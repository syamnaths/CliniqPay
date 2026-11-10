#!/usr/bin/env node
// Loop project starter (atlas-first). Creates a new project whose first
// artefact is its flow atlas: an overview, a roadmap, a quality-gates map and
// one planned map per feature, a release map for the chosen platform(s), plus
// tracks, AGENTS.md, HANDOFF.md and an atlas check. Then it builds the atlas
// and prints the first feature to build.
//
// Platform is chosen at the start (web, android, ios, mobile, desktop, backend,
// cli, other, or several). Loop never fixes the platform or the stack itself.
//
//   node scripts/loop-init.mjs <target> --brief START.md|brief.json [--platform web,android] [--git] [--start]
//   node scripts/loop-init.mjs <target>                      (uses <target>/START.md, else asks questions)
//
// --start hands over to the coding agent right away (LOOP_AGENT, default
// "codex") with: Use Loop for this project. Build the next atlas map.
// A template page (brief "templatePage", or a template-page/ folder next to
// START.md) is moved to design/template-page/ and every screen follows it.
//   node scripts/loop-init.mjs <existing-project> --adopt [--platform ...] [--name ...]
//
// Safety: never overwrites an existing file; refuses a non-empty target unless
// --adopt is given. No network, no package installs. Node 18+ is needed only
// for the atlas tools; the product itself can use any stack.
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { execFileSync, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { PLATFORMS, PLATFORM_IDS, parsePlatforms, detectPlatforms, platformProfile } from '../starter/platforms.mjs';

const LOOP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const STARTER = path.join(LOOP_ROOT, 'starter');
const LOOP_VERSION = JSON.parse(fs.readFileSync(path.join(LOOP_ROOT, '.codex-plugin/plugin.json'), 'utf8')).version;
const START_FILES = ['START.md', 'template-page', '.DS_Store', '.git'];
export const KICKOFF = 'Use Loop for this project. Build the next atlas map.';
const LOOP_DOCS = ['loop.md', 'ATLAS-FIRST.md', 'OWNER-COMMUNICATION.md', 'EFFICIENT-WORKFLOW.md', 'DELIVERY-WORKFLOW.md', 'SECURITY.md', 'LEGAL-CHECKLIST.md'];

// ── arguments (read in main) ────────────────────────────────────────────────
let argv = [];
let target = '';
let adopt = false;
const flag = name => argv.includes(name);
const option = name => { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : undefined; };
const today = new Date().toISOString().slice(0, 10);

// ── helpers ─────────────────────────────────────────────────────────────────
export const slugify = value => String(value).toLowerCase().normalize('NFKD').replace(/[^\w\s-]/g, '').trim().replace(/[\s_]+/g, '-').replace(/-+/g, '-').slice(0, 40) || 'item';
const fill = (template, values) => template.replace(/\{\{(\w+)\}\}/g, (_, key) => values[key] ?? '');
const written = [], skipped = [];
function write(relative, content) {
    const full = path.join(target, relative);
    if (fs.existsSync(full)) { skipped.push(relative); return false; }
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, content);
    written.push(relative);
    return true;
}
const copy = (from, to) => write(to, fs.readFileSync(from, 'utf8'));
const run = (cmd, args, opts = {}) => execFileSync(cmd, args, { cwd: target, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...opts });

// ── brief ───────────────────────────────────────────────────────────────────
async function askBrief() {
    // Line queue: works for a person typing and for piped answers.
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: process.stdin.isTTY });
    const lines = [], waiters = [];
    let closed = false;
    rl.on('line', line => (waiters.length ? waiters.shift()(line) : lines.push(line)));
    rl.on('close', () => { closed = true; while (waiters.length) waiters.shift()(null); });
    const readLine = prompt => {
        process.stdout.write(prompt);
        if (lines.length) return Promise.resolve(lines.shift());
        if (closed) return Promise.resolve(null);
        return new Promise(resolve => waiters.push(resolve));
    };
    rl.question = async prompt => {
        const line = await readLine(prompt);
        if (line === null) throw new Error('Input ended before the brief was complete.');
        if (!process.stdin.isTTY) process.stdout.write(line + '\n');
        return line;
    };
    const ask = async (q, d = '') => (await rl.question(d ? `${q} [${d}]: ` : `${q}: `)).trim() || d;
    console.log('Loop starter. Answer in plain words; press Enter to accept a default.\n');
    const brief = {
        name: await ask('Project name'),
        audience: await ask('Who is it for'),
        outcome: await ask('What must the first release do')
    };
    console.log('\nWhich platform will you build for? Pick one or more numbers (for example 1 or 1,2).');
    PLATFORM_IDS.forEach((id, i) => console.log(`  ${i + 1}. ${PLATFORMS[id].label}`));
    for (;;) {
        const answer = await ask('Platform');
        try {
            brief.platforms = parsePlatforms(answer.split(/[,\s]+/).filter(Boolean).map(v => (/^\d+$/.test(v) ? PLATFORM_IDS[+v - 1] || v : v)));
            if (brief.platforms.length) break;
        } catch (error) { console.log(`  ${error.message}`); }
    }
    console.log(`Common stacks: ${brief.platforms.map(id => PLATFORMS[id].stacks).join(' | ')}`);
    Object.assign(brief, {
        stack: await ask('Stack (or "to decide")', 'to decide'),
        languages: (await ask('Languages (comma separated)', 'en')).split(',').map(s => s.trim()).filter(Boolean),
        templatePage: await ask('Template page to build on (path to an HTML page, image or folder; Enter to skip)', ''),
        features: []
    });
    if (!brief.templatePage) delete brief.templatePage;
    console.log('\nFeatures for the first release. Format: Title: step > step > step   (empty line to finish)');
    for (;;) {
        const raw = await readLine('  feature: ');
        if (raw !== null && !process.stdin.isTTY) process.stdout.write(raw + '\n');
        const line = (raw || '').trim();
        if (!line) break;
        const [title, steps = ''] = line.split(':');
        brief.features.push({ title: title.trim(), steps: steps.split('>').map(s => s.trim()).filter(Boolean) });
    }
    rl.close();
    return brief;
}

// ── START.md (plain fill-in form) ───────────────────────────────────────────
const START_KEYS = { 'name': 'name', 'project name': 'name', 'for': 'audience', 'who is it for': 'audience', 'audience': 'audience', 'first release must': 'outcome', 'first release': 'outcome', 'outcome': 'outcome', 'platform': 'platforms', 'platforms': 'platforms', 'stack': 'stack', 'languages': 'languages', 'language': 'languages', 'test command': 'testCommand', 'template page': 'templatePage', 'template': 'templatePage' };
export function parseStartMd(text) {
    const raw = { features: [], constraints: [], mustNot: [] };
    let section = '';
    for (const line of text.split(/\r?\n/)) {
        if (/^\s*>/.test(line) || /^#\s/.test(line)) continue;
        const heading = /^##\s+(.+)/.exec(line);
        if (heading) { section = heading[1].trim().toLowerCase(); continue; }
        if (!section) {
            const field = /^([A-Za-z ]+):\s*(.*)$/.exec(line.trim());
            if (field && START_KEYS[field[1].trim().toLowerCase()] && field[2].trim()) raw[START_KEYS[field[1].trim().toLowerCase()]] = field[2].trim();
            continue;
        }
        const item = /^(\s*)[-*]\s+(.*)$/.exec(line);
        if (!item || !item[2].trim()) continue;
        const value = item[2].trim();
        if (section.startsWith('feature')) {
            const sub = /^(fails|if it fails|failure|done when|acceptance|release|goal):\s*(.+)$/i.exec(value);
            if (item[1].length && sub && raw.features.length) {
                const key = sub[1].toLowerCase();
                const feature = raw.features[raw.features.length - 1];
                if (key === 'release') feature.release = Number(sub[2]) || 1;
                else if (key === 'goal') feature.goal = sub[2].trim();
                else if (key.startsWith('done') || key === 'acceptance') feature.acceptance = sub[2].trim();
                else feature.failure = sub[2].trim();
            } else {
                const at = value.indexOf(':');
                const title = (at >= 0 ? value.slice(0, at) : value).trim();
                const steps = at >= 0 ? value.slice(at + 1).split('>').map(x => x.trim()).filter(Boolean) : [];
                raw.features.push({ title, steps });
            }
        } else if (section.startsWith('constraint')) raw.constraints.push(value);
        else if (section.startsWith('must')) raw.mustNot.push(value);
    }
    if (typeof raw.languages === 'string') raw.languages = raw.languages.split(',').map(x => x.trim()).filter(Boolean);
    for (const key of ['constraints', 'mustNot']) if (!raw[key].length) delete raw[key];
    const missing = [['name', 'Name'], ['platforms', 'Platform']].filter(([k]) => !raw[k]).map(([, label]) => label);
    if (!raw.features.length) missing.push('Features (at least one)');
    if (missing.length) throw new Error(`START.md is missing: ${missing.join(', ')}. Fill these in (or let Loop ask you) and run again.`);
    return raw;
}

export function readBrief(file) {
    const text = fs.readFileSync(file, 'utf8');
    const raw = file.toLowerCase().endsWith('.md') ? parseStartMd(text) : JSON.parse(text);
    raw._from = path.dirname(path.resolve(file));
    return raw;
}

// Find the template page: brief.templatePage (path), or a template-page/ folder
// next to the brief or inside the target. Only real files count (README.md in
// Loop's own empty template-page folder is ignored).
function findTemplatePage(raw, targetDir) {
    const candidates = [];
    if (raw.templatePage) candidates.push(path.resolve(raw._from || process.cwd(), raw.templatePage.replace(/^~(?=\/)/, process.env.HOME || '~')));
    if (raw._from) candidates.push(path.join(raw._from, 'template-page'));
    candidates.push(path.join(targetDir, 'template-page'));
    for (const candidate of candidates) {
        if (!fs.existsSync(candidate)) { if (candidate === candidates[0] && raw.templatePage) throw new Error(`Template page not found: ${raw.templatePage}`); continue; }
        if (fs.statSync(candidate).isFile()) return candidate;
        const files = fs.readdirSync(candidate).filter(n => n !== 'README.md' && n !== '.DS_Store');
        if (files.length) return candidate;
    }
    return '';
}

export function normaliseBrief(raw) {
    const brief = { ...raw };
    delete brief._from;
    if (!brief.name) throw new Error('The brief needs a name.');
    brief.slug = brief.slug || slugify(brief.name);
    brief.audience = brief.audience || brief.for || 'to confirm with the owner';
    brief.outcome = brief.outcome || 'to confirm with the owner';
    brief.platforms = parsePlatforms(brief.platforms ?? brief.platform);
    if (!brief.platforms.length) throw new Error(`The brief needs a platform. Choose one or more: ${PLATFORM_IDS.join(', ')}.`);
    delete brief.platform;
    const profile = platformProfile(brief.platforms);
    brief.stack = brief.stack || 'to decide';
    brief.languages = Array.isArray(brief.languages) && brief.languages.length ? brief.languages : ['en'];
    brief.ownerStyle = brief.ownerStyle || 'Simple, plain words and short lines. Lead with the result. Decision-ready work with no placeholders.';
    const used = new Set(['overview', 'roadmap', 'quality-gates', 'release']);
    brief.features = (brief.features || []).map((feature, index) => {
        const base = typeof feature === 'string' ? { title: feature } : { ...feature };
        let id = slugify(base.id || base.title || `feature-${index + 1}`);
        while (used.has(id)) id = `${id}-${index + 1}`;
        used.add(id);
        const steps = (base.steps && base.steps.length ? base.steps : ['Start', 'Main action', 'Result']).map(String);
        return { id, title: base.title || id, goal: base.goal || `Deliver ${base.title || id} for ${brief.audience}.`, steps, acceptance: base.acceptance || '', failure: base.failure || '', release: Number(base.release) || 1 };
    });
    if (!brief.features.length) throw new Error('The brief needs at least one feature for the first release.');
    brief.buildOrder = [...brief.features].sort((a, b) => a.release - b.release).map(f => f.id);
    brief.openQuestions = brief.openQuestions || [...(brief.stack === 'to decide' ? ['Which stack to use'] : []), ...profile.questions, 'Where user data is stored (if any)', 'Accessibility targets', 'Analytics and privacy rules'];
    return brief;
}

// ── commands ────────────────────────────────────────────────────────────────
// npm scripts when the project is JavaScript-based; plain node commands otherwise.
export function commandsFor(brief, hasPackageJson = false) {
    const js = hasPackageJson || platformProfile(brief.platforms).node || /\b(node|react|vue|svelte|next|nuxt|astro|vite|electron|javascript|typescript|js|ts)\b/i.test(brief.stack);
    const profile = platformProfile(brief.platforms);
    const base = js
        ? { atlas: 'npm run atlas', status: 'npm run atlas:status', next: 'npm run atlas:next', verify: 'npm run atlas:verify', check: 'npm run atlas:check' }
        : { atlas: 'node docs/app-map/build-atlas.mjs', status: 'node docs/app-map/atlas-status.mjs', next: 'node docs/app-map/atlas-status.mjs --next', verify: 'node docs/app-map/verify-atlas.mjs', check: 'node --test docs/app-map/atlas-contract.test.mjs' };
    return { npm: js, ...base, test: brief.testCommand || (profile.tests.length === 1 ? profile.tests[0].replace(/^[^:]+: /, '') : profile.tests.join('; ')) };
}

// ── atlas plan ──────────────────────────────────────────────────────────────
export function atlasPlan(brief, cmd = commandsFor(brief)) {
    const profile = platformProfile(brief.platforms);
    const chunk = (list, size) => list.reduce((rows, item, i) => { if (i % size === 0) rows.push([]); rows[rows.length - 1].push(item); return rows; }, []);
    const short = (text, max = 58) => (text.length > max ? text.slice(0, max - 1).trimEnd() + '…' : text);
    const overview = {
        id: 'overview', group: 'Start here', title: 'The whole product', status: 'planned',
        subtitle: `${brief.name} for ${brief.audience}, on ${profile.label}. Each feature opens its own map.`,
        source: '',
        rows: [
            [['open', `${profile.entry}: ${brief.name}`, `Entry point on ${profile.label}. Design how a new user starts.${brief.templatePage ? ` Look and layout follow ${brief.templatePage}.` : ''}`]],
            ...chunk(brief.features.map(f => [`f-${f.id}`, f.title, f.goal]), 3),
            [['outcome', 'First release outcome', brief.outcome]]
        ],
        edges: [...brief.features.map(f => ['open', `f-${f.id}`, 'Choose']), ...brief.features.map(f => [`f-${f.id}`, 'outcome', 'Delivers'])],
        drilldowns: Object.fromEntries(brief.features.map(f => [`f-${f.id}`, f.id])),
        notes: ['Planned from the approved brief. Switch to delivered when the features exist.']
    };
    const releases = [...new Set(brief.features.map(f => f.release))].sort((a, b) => a - b);
    const roadmap = {
        id: 'roadmap', group: 'Start here', title: 'Build order', status: 'planned',
        subtitle: 'The order Loop builds the features in (meta.buildOrder).',
        source: '',
        rows: releases.flatMap(r => chunk(brief.buildOrder.map(id => brief.features.find(f => f.id === id)).filter(f => f.release === r).map(f => [`r-${f.id}`, f.title, `Release ${r}. Track: .loop/tracks/${f.id}/spec.md`]), 3)),
        edges: brief.buildOrder.slice(1).map((id, i) => [`r-${brief.buildOrder[i]}`, `r-${id}`, 'Then']),
        drilldowns: Object.fromEntries(brief.features.map(f => [`r-${f.id}`, f.id])),
        notes: [`${cmd.next} always names the first map in this order that is not delivered. The release map comes last.`]
    };
    const quality = {
        id: 'quality-gates', group: 'Systems', title: 'How every feature is built', status: 'delivered',
        subtitle: 'The atlas-first checkpoint loop this project follows.',
        source: 'AGENTS.md:1; .loop/workflow.md:1; .loop/platform.md:1',
        rows: [
            [['next', 'Pick next map', `${cmd.next} names the next planned map and its track.`]],
            [['map', 'Make the map exact', 'Steps, branches, defaults, failure paths. Status: building.']],
            [['build', 'Build to the map', `Smallest coherent change, all languages, version bump. Platform: ${profile.label}.`]],
            [['check', 'Prove it', `Behaviour tests (${cmd.test}), ${cmd.atlas}, ${profile.visual.join('; ')}. Proof ladder in .loop/platform.md.`]],
            [['legal', 'Legal rows', 'Update .loop/legal-checklist.md rows this change touches (data, cookies, APIs, packages, assets, AI content, payments, advice, claims). Rules: Loop/LEGAL-CHECKLIST.md.']],
            [['flip', 'Flip to delivered', 'Add source refs (file:line). The build refuses delivered without source.']],
            [['record', 'Record and report', 'Track, fix queue, HANDOFF CURRENT RESUME, commit, plain-words report.']]
        ],
        edges: [['next', 'map', 'Read'], ['map', 'build', 'Exact'], ['build', 'check', 'Done'], ['check', 'build', 'Fails'], ['check', 'legal', 'Passes'], ['legal', 'build', 'Gap'], ['legal', 'flip', 'Clear'], ['flip', 'record', 'Built'], ['record', 'next', 'Repeat']],
        notes: ['Defined by AGENTS.md, .loop/workflow.md and .loop/platform.md (generated by Loop).']
    };
    const releaseSteps = [['legal-audit', 'Final legal audit', 'Legal check 20: recheck all 20 rows in .loop/legal-checklist.md, flag lawyer items, owner approves legal pages. Rules: Loop/LEGAL-CHECKLIST.md.'],
        ...profile.release.map((step, i) => [`p${i + 1}`, short(step), `Release step: ${step}. Owner approval gates in Loop/loop.md apply.`])];
    const release = {
        id: 'release', group: 'Systems', title: 'Release', status: 'planned',
        subtitle: `How ${brief.name} reaches users on ${profile.label}.`,
        source: '',
        rows: releaseSteps.map(step => [step]),
        edges: releaseSteps.slice(1).map((step, i) => [releaseSteps[i][0], step[0], 'Then']),
        notes: ['Built last, after the first-release features. Track: .loop/tracks/release/spec.md']
    };
    const features = brief.features.map(f => {
        const steps = f.steps.map((step, i) => [`s${i + 1}`, short(step), `To build: ${step}. Define the guard, default, exit and failure path before coding.`]);
        const rows = steps.map(step => [step]);
        const edges = steps.slice(1).map((step, i) => [steps[i][0], step[0], 'Next']);
        if (f.failure) { rows[rows.length - 1].push(['fail', 'If it fails', f.failure]); edges.push([steps[steps.length - 1][0], 'fail', 'Error'], ['fail', steps[0][0], 'Retry']); }
        rows.push([['done', 'Works end to end', `Acceptance: ${f.acceptance || f.goal}`]]);
        edges.push([steps[steps.length - 1][0], 'done', 'Complete']);
        return { id: f.id, group: 'Features', title: f.title, status: 'planned', subtitle: f.goal, source: '', rows, edges, notes: [`Planned · release ${f.release} · track .loop/tracks/${f.id}/spec.md`] };
    });
    const meta = {
        title: `${brief.name} · Flow Atlas`, slug: brief.slug, date: today,
        commit: 'initial plan (nothing built yet)',
        scope: `Atlas-first plan for ${brief.name}. First release: ${brief.outcome}`,
        groups: ['Start here', 'Features', 'Systems', 'Supporting pages'],
        featureGroup: 'Features',
        buildOrder: [...brief.buildOrder, 'release'],
        ...(brief.templatePage ? { templatePage: brief.templatePage } : {}),
        platforms: brief.platforms
    };
    return { meta, graphs: [overview, roadmap, ...features, quality, release] };
}

function atlasModule({ meta, graphs }) {
    return `// ${meta.title}. Edit this file; run node docs/app-map/build-atlas.mjs to rebuild.\n// Status per map: planned → building → delivered (delivered needs source: 'file:line; ...').\n// Method: Loop/ATLAS-FIRST.md\nexport const meta = ${JSON.stringify(meta, null, 2)};\n\nexport const graphs = ${JSON.stringify(graphs, null, 2)};\n`;
}

function trackSpec(brief, f, cmd) {
    return `# ${f.title}\n\nStatus: planned · release ${f.release} · map \`${f.id}\` in \`docs/app-map/atlas-data.mjs\`\n\n## Goal\n\n${f.goal}\n\n## Steps (from the map)\n\n${f.steps.map((s, i) => `${i + 1}. ${s}`).join('\n')}${f.failure ? `\n\nIf it fails: ${f.failure}` : ''}\n\n## Acceptance\n\n${f.acceptance || f.goal}\n\n## Done checklist\n\n- [ ] Map made exact before coding (guards, defaults, exits, failure paths); status \`building\`\n- [ ] Built to the map; smallest coherent change\n${brief.templatePage ? `- [ ] Screens follow the template page (\`${brief.templatePage}\`): layout, colours, fonts, spacing\n` : ''}- [ ] Behaviour tests added and passing (\`${cmd.test}\`)\n- [ ] Proved at the strongest level in \`.loop/platform.md\` (say which level)\n- [ ] User text in every language: ${brief.languages.join(', ')}\n- [ ] Version bumped as \`.loop/platform.md\` says\n- [ ] Legal rows this feature touches updated in \`.loop/legal-checklist.md\` (data, cookies, APIs, packages, assets, AI content, payments, advice, claims); none left \`todo\`\n- [ ] Map \`delivered\` with \`source\` refs; \`${cmd.atlas}\` passes\n- [ ] Doc or notes updated; FIX-QUEUE and HANDOFF current\n- [ ] Owner shown the result (${platformProfile(brief.platforms).visual.join('; ')}); verified vs not verified stated\n\n## Decisions\n\n- (record owner decisions here with the date)\n`;
}

function releaseSpec(brief, cmd) {
    const profile = platformProfile(brief.platforms);
    return `# Release\n\nStatus: planned · map \`release\` in \`docs/app-map/atlas-data.mjs\` · platform: ${profile.label}\n\n## Steps\n\n${profile.release.map((s, i) => `${i + 1}. ${s}`).join('\n')}\n\n## Done checklist\n\n- [ ] Every first-release feature map is \`delivered\` (\`${cmd.status}\`)\n- [ ] Release steps above made exact for the chosen stack and accounts\n- [ ] Secrets, signing keys and store credentials kept out of the repository\n- [ ] Legal check 20 (final audit) done in \`.loop/legal-checklist.md\`: no \`todo\` or \`blocked\` rows, every \`n/a\` has a reason, owner decision on every \`lawyer\` row\n- [ ] Owner approved the final legal pages (privacy, terms, cookies, refunds, disclaimers) that apply\n- [ ] Owner approved the release in writing (date recorded below)\n- [ ] Live version confirmed after release; map \`delivered\` with source refs\n\n## Decisions\n\n- (record owner decisions here with the date)\n`;
}

function platformDoc(brief, cmd) {
    const p = platformProfile(brief.platforms);
    const list = items => items.map(x => `- ${x}`).join('\n');
    return `# Platform\n\nChosen at the start: **${p.label}**. Stack: **${brief.stack}**.\nChange this file (and the release map) if the owner changes the platform. Do not change the platform without the owner's decision.\n\n## Stack options considered\n\n${list(p.stacks)}\n\n## Test commands\n\n${list(p.tests)}${brief.testCommand ? `\n- Agreed for this project: \`${brief.testCommand}\`` : ''}\n\nAtlas commands (Node 18+, development only): \`${cmd.atlas}\`, \`${cmd.status}\`, \`${cmd.next}\`, \`${cmd.check}\`, \`${cmd.verify}\`.\n\n## Proof ladder (strongest level reached is reported)\n\n${list(p.proof)}\n\nVisual proof: ${p.visual.join('; ')}.\n\n## Platform rules\n\n${list([...p.version, ...p.rules, `User text lives in ${p.text.join(' / ')}, in every language: ${brief.languages.join(', ')}.`])}\n\n## Shared hotspots (one owner at a time)\n\n${p.hotspots}\n\n## Release path\n\n${p.release.map((s, i) => `${i + 1}. ${s}`).join('\n')}\n`;
}

function briefDoc(brief) {
    return `# ${brief.name} — project brief\n\nApproved ${today}. Source of truth for scope; the atlas shows behaviour.\n\n| | |\n| --- | --- |\n| For | ${brief.audience} |\n| First release must | ${brief.outcome} |\n| Platform | ${platformProfile(brief.platforms).label} |\n| Stack | ${brief.stack} |\n| Languages | ${brief.languages.join(', ')} |\n| Template page | ${brief.templatePage ? `\`${brief.templatePage}\`` : 'none (Loop designs the first screen)'} |\n\n## Features (build order)\n\n${brief.buildOrder.map((id, i) => { const f = brief.features.find(x => x.id === id); return `${i + 1}. **${f.title}** (release ${f.release}) — ${f.goal}`; }).join('\n')}\n\n## Constraints\n\n${(brief.constraints || ['(none recorded)']).map(c => `- ${c}`).join('\n')}\n\n## Must not do\n\n${(brief.mustNot || ['(none recorded)']).map(c => `- ${c}`).join('\n')}\n\n## Open questions (ask the owner before they matter)\n\n${brief.openQuestions.map(q => `- ${q}`).join('\n')}\n`;
}

// ── main ────────────────────────────────────────────────────────────────────
async function main() {
    argv = process.argv.slice(2);
    const positional = argv.filter((arg, i) => !arg.startsWith('--') && !['--brief', '--name', '--platform'].includes(argv[i - 1]));
    if (!positional[0] || flag('--help')) {
        console.log(`Usage: node scripts/loop-init.mjs <target> [--brief START.md|brief.json] [--platform ${PLATFORM_IDS.join('|')}[,...]] [--git] [--start] [--adopt [--name "Name"]]`);
        process.exit(positional[0] ? 0 : 2);
    }
    target = path.resolve(positional[0]);
    adopt = flag('--adopt');
    if (fs.existsSync(target) && fs.readdirSync(target).filter(n => !START_FILES.includes(n)).length && !adopt) {
        console.error(`Target is not empty: ${target}\nUse --adopt to add the atlas tools to an existing project (nothing is overwritten).`);
        process.exit(2);
    }
    fs.mkdirSync(target, { recursive: true });

    let brief, platformNote = '';
    if (adopt) {
        const name = option('--name') || path.basename(target);
        const platforms = option('--platform') ? parsePlatforms(option('--platform')) : detectPlatforms(fs.readdirSync(target));
        if (!option('--platform')) platformNote = ` (detected; pass --platform to change)`;
        brief = normaliseBrief({ name, platforms, outcome: 'map the current behaviour, then plan new features', features: [{ id: 'current-app', title: 'Current app (to map)', steps: ['Entry points', 'Main screens or endpoints', 'Data and storage', 'Background work'], goal: 'Map what already exists as delivered maps with source references.' }] });
    } else {
        const startFile = path.join(target, 'START.md');
        const usingStart = !option('--brief') && fs.existsSync(startFile);
        const raw = option('--brief') ? readBrief(path.resolve(option('--brief'))) : usingStart ? readBrief(startFile) : await askBrief();
        if (option('--platform')) raw.platforms = option('--platform');
        const templateSource = findTemplatePage(raw, target);
        brief = normaliseBrief(raw);
        if (templateSource) {
            // Move it when it already sits inside the project; copy it when it lives elsewhere.
            const destination = path.join(target, 'design/template-page');
            const inside = templateSource.startsWith(target + path.sep);
            fs.mkdirSync(destination, { recursive: true });
            const name = path.basename(templateSource);
            if (fs.statSync(templateSource).isFile()) {
                const to = path.join(destination, name);
                if (!fs.existsSync(to)) inside ? fs.renameSync(templateSource, to) : fs.copyFileSync(templateSource, to);
            } else {
                for (const entry of fs.readdirSync(templateSource).filter(n => n !== 'README.md' && n !== '.DS_Store')) {
                    const to = path.join(destination, entry);
                    if (fs.existsSync(to)) continue;
                    inside ? fs.renameSync(path.join(templateSource, entry), to) : fs.cpSync(path.join(templateSource, entry), to, { recursive: true });
                }
                if (inside && !fs.readdirSync(templateSource).filter(n => n !== '.DS_Store').length) fs.rmSync(templateSource, { recursive: true, force: true });
            }
            written.push('design/template-page/ (your template page)');
            const files = fs.readdirSync(destination);
            const entry = files.find(n => /^index\.html?$/i.test(n)) || files.find(n => /\.html?$/i.test(n)) || files[0];
            brief.templatePage = `design/template-page/${entry || ''}`.replace(/\/$/, '');
        }
    }
    if (!adopt && !option('--brief') && fs.existsSync(path.join(target, 'START.md')) && !fs.existsSync(path.join(target, 'docs/START.md'))) {
        // Keep the owner's answers with the project docs.
        fs.mkdirSync(path.join(target, 'docs'), { recursive: true });
        fs.renameSync(path.join(target, 'START.md'), path.join(target, 'docs/START.md'));
        written.push('docs/START.md (your answers)');
    }
    const profile = platformProfile(brief.platforms);
    const cmd = commandsFor(brief, fs.existsSync(path.join(target, 'package.json')));

    // Loop policy copy (project-local, like Lite's Loop/ folder)
    for (const doc of LOOP_DOCS) if (fs.existsSync(path.join(LOOP_ROOT, doc))) copy(path.join(LOOP_ROOT, doc), path.join('Loop', doc));
    write('Loop/README.md', `# Loop (project copy)\n\nCopied from Loop ${LOOP_VERSION} on ${today}. Start with \`../AGENTS.md\`, then \`loop.md\` and \`ATLAS-FIRST.md\`. This copy may be newer or older than the installed Loop plugin; it governs this project.\n`);

    // Atlas tools
    for (const file of ['atlas-template.html', 'build-atlas.mjs', 'atlas-status.mjs', 'verify-atlas.mjs']) copy(path.join(STARTER, 'docs/app-map', file), path.join('docs/app-map', file));
    const plan = atlasPlan(brief, cmd);
    write('docs/app-map/atlas-data.mjs', atlasModule(plan));

    const values = {
        name: brief.name, date: today, loopVersion: LOOP_VERSION, outcome: brief.outcome, audience: brief.audience, stack: brief.stack,
        platform: profile.label, cmdAtlas: cmd.atlas, cmdStatus: cmd.status, cmdNext: cmd.next, cmdVerify: cmd.verify, cmdCheck: cmd.check, projectTest: cmd.test,
        versionRule: profile.version.join(' '), textHome: profile.text.join(' / '), visualProof: profile.visual.join('; '), hotspots: profile.hotspots,
        platformRules: profile.rules.map(r => `- ${r}`).join('\n'),
        templateRule: brief.templatePage ? `## Template page\n\nThe owner's basic template page is \`${brief.templatePage}\` (folder \`design/template-page/\`). Every screen follows its layout, colours, fonts and spacing. Reuse its markup and styles where the platform allows; otherwise match it closely. Change the look only when the owner decides.\n\n` : '',
        languages: brief.languages.join(', '), ownerStyle: brief.ownerStyle, mapCount: String(plan.graphs.length),
        firstFeature: brief.features.find(f => f.id === brief.buildOrder[0]).title, firstFeatureId: brief.buildOrder[0],
        gitLine: flag('--git') ? 'Local Git repository initialised with the first commit.' : 'Git not initialised by the starter.'
    };
    const tpl = name => fs.readFileSync(path.join(STARTER, 'templates', name), 'utf8');
    write('AGENTS.md', fill(tpl('AGENTS.md'), values));
    write('HANDOFF.md', fill(tpl('HANDOFF.md'), values));
    write('.loop/workflow.md', fill(tpl('workflow.md'), values));
    write('docs/app-map/FIX-QUEUE.md', fill(tpl('FIX-QUEUE.md'), values));
    write('docs/app-map/README.md', fill(tpl('app-map-README.md'), values));
    write('.loop/platform.md', platformDoc(brief, cmd));
    write('.loop/legal-checklist.md', fill(tpl('legal-checklist.md'), values));
    write('.gitignore', tpl('gitignore') + (profile.gitignore.length ? `\n# ${profile.label}\n${profile.gitignore.join('\n')}\n` : ''));
    if (!adopt) { write('docs/project-brief.md', briefDoc(brief)); write('docs/project-brief.json', JSON.stringify(brief, null, 2) + '\n'); }
    for (const f of brief.features) write(`.loop/tracks/${f.id}/spec.md`, trackSpec(brief, f, cmd));
    write('.loop/tracks/release/spec.md', releaseSpec(brief, cmd));
    copy(path.join(STARTER, 'docs/app-map/atlas-contract.test.mjs'), 'docs/app-map/atlas-contract.test.mjs');

    // npm scripts only for JavaScript-based projects. Others run the node commands directly.
    const scripts = { atlas: 'node docs/app-map/build-atlas.mjs', 'atlas:status': 'node docs/app-map/atlas-status.mjs', 'atlas:next': 'node docs/app-map/atlas-status.mjs --next', 'atlas:verify': 'node docs/app-map/verify-atlas.mjs', 'atlas:check': 'node --test docs/app-map/atlas-contract.test.mjs', test: 'node --test' };
    const pkgPath = path.join(target, 'package.json');
    if (!cmd.npm) {
        // nothing to add: AGENTS.md lists the plain commands
    } else if (fs.existsSync(pkgPath)) {
        const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
        pkg.scripts = pkg.scripts || {};
        const added = Object.entries(scripts).filter(([k]) => !(k in pkg.scripts));
        for (const [k, v] of added) pkg.scripts[k] = v;
        if (added.length) { fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n'); written.push(`package.json (added scripts: ${added.map(([k]) => k).join(', ')})`); }
    } else {
        write('package.json', JSON.stringify({ name: brief.slug, version: '0.1.0', private: true, type: 'module', scripts }, null, 2) + '\n');
    }

    // Build and check the atlas right away: the project starts from its map.
    const build = run(process.execPath, ['docs/app-map/build-atlas.mjs']).trim().split('\n').pop();
    let status = '';
    try { status = run(process.execPath, ['docs/app-map/atlas-status.mjs', '--next']); } catch (error) { status = error.stdout || ''; }

    if (flag('--git')) {
        try {
            if (!fs.existsSync(path.join(target, '.git'))) run('git', ['init', '-q']);
            run('git', ['add', '-A']);
            run('git', ['commit', '-q', '-m', `[CP-000] Loop atlas-first project start\n\nCreated by Loop ${LOOP_VERSION} loop-init.mjs from the approved brief.`]);
        } catch (error) {
            console.warn(`Git step skipped: ${(error.stderr || error.message).toString().trim().split('\n')[0]}`);
        }
    }

    console.log(`\nLoop ${LOOP_VERSION} · ${adopt ? 'adopted' : 'created'} ${brief.name} at ${target}`);
    console.log(`Platform: ${profile.label}${platformNote} · stack: ${brief.stack}`);
    console.log(`Atlas: ${build}`);
    console.log(`Files written: ${written.length}${skipped.length ? ` · kept existing: ${skipped.join(', ')}` : ''}`);
    console.log('\n' + status.trim());
    if (brief.templatePage) console.log(`Template page: ${brief.templatePage}`);
    console.log('\nOpen docs/app-map/index.html to see the plan.');
    if (flag('--start')) {
        // Hand over to the coding agent so building starts straight away.
        const agent = process.env.LOOP_AGENT || 'codex';
        console.log(`\nStarting ${agent} in ${target}: "${KICKOFF}"`);
        const started = spawnSync(agent, [KICKOFF], { cwd: target, stdio: 'inherit' });
        if (started.error) console.log(`Could not start ${agent} (${started.error.code || started.error.message}). Open the project in your agent and say: ${KICKOFF}`);
    } else {
        console.log(`Start building: open the project in your agent and say: ${KICKOFF}\n(Or run again next time with --start to hand over automatically.)`);
    }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
    main().catch(error => { console.error(error.message); process.exit(1); });
}
