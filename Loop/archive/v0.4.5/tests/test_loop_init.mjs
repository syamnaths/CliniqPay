// Loop starter tests: run with  node --test tests/test_loop_init.mjs
// Creates throwaway projects in the OS temp folder and removes them.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const LOOP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const INIT = path.join(LOOP, 'scripts/loop-init.mjs');
const BRIEF = path.join(LOOP, 'examples/brief.example.json');
const temp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'loop-init-'));
const node = (args, cwd) => spawnSync(process.execPath, args, { cwd, encoding: 'utf8' });

test('a new project is born from its atlas plan', () => {
    const dir = path.join(temp(), 'calm');
    const result = node([INIT, dir, '--brief', BRIEF]);
    assert.equal(result.status, 0, result.stderr);
    for (const file of ['AGENTS.md', 'HANDOFF.md', '.loop/workflow.md', 'docs/project-brief.md', 'docs/app-map/atlas-data.mjs', 'docs/app-map/index.html', 'docs/app-map/FLOW-REFERENCE.md', 'docs/app-map/CONTROL-INVENTORY.md', 'docs/app-map/atlas-contract.test.mjs', '.loop/platform.md', '.loop/tracks/release/spec.md', 'Loop/loop.md', 'Loop/ATLAS-FIRST.md', 'Loop/OWNER-COMMUNICATION.md', 'package.json']) {
        assert.ok(fs.existsSync(path.join(dir, file)), `${file} exists`);
    }
    for (const id of ['first-open', 'write-today', 'streak', 'daily-reminder']) assert.ok(fs.existsSync(path.join(dir, '.loop/tracks', id, 'spec.md')), `track ${id}`);
    assert.match(result.stdout, /Next: First open \(first-open\)/, 'prints the first feature to build');
    const atlas = JSON.parse(fs.readFileSync(path.join(dir, 'docs/app-map/atlas.json'), 'utf8'));
    assert.deepEqual(atlas.graphs.map(g => g.id).sort(), ['daily-reminder', 'first-open', 'overview', 'quality-gates', 'release', 'roadmap', 'streak', 'write-today']);
    assert.deepEqual(atlas.meta.buildOrder, ['first-open', 'write-today', 'streak', 'daily-reminder', 'release'], 'release 2 features come last, then the release map');
    assert.deepEqual(atlas.meta.platforms, ['web']);
    assert.match(atlas.graphs.find(g => g.id === 'release').rows.flat().map(n => n[1]).join(' '), /Deploy/);
    const pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
    assert.equal(pkg.scripts['atlas:check'], 'node --test docs/app-map/atlas-contract.test.mjs');
    assert.ok(atlas.graphs.filter(g => g.group === 'Features').every(g => g.status === 'planned'));
    const writeToday = atlas.graphs.find(g => g.id === 'write-today');
    assert.ok(writeToday.rows.flat().some(n => n[0] === 'fail'), 'failure path from the brief becomes a branch');
    const handoff = fs.readFileSync(path.join(dir, 'HANDOFF.md'), 'utf8');
    assert.equal((handoff.match(/^## CURRENT RESUME/gm) || []).length, 1);
    assert.match(handoff, /build \*\*First open\*\*/);
    assert.doesNotMatch(fs.readFileSync(path.join(dir, 'AGENTS.md'), 'utf8') + handoff, /\{\{\w+\}\}/, 'no placeholders left');
    // The generated project's own checks pass.
    const tests = node(['--test'], dir);
    assert.equal(tests.status, 0, tests.stdout + tests.stderr);
});

test('the platform is chosen at the start: an Android project gets no npm and Android rules', () => {
    const dir = path.join(temp(), 'bus');
    const result = node([INIT, dir, '--brief', path.join(LOOP, 'examples/brief.android.example.json')]);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /Platform: Android app \(native\)/);
    assert.ok(!fs.existsSync(path.join(dir, 'package.json')), 'no package.json for a non-JavaScript project');
    const agents = fs.readFileSync(path.join(dir, 'AGENTS.md'), 'utf8');
    assert.match(agents, /node docs\/app-map\/atlas-status\.mjs --next/);
    assert.match(agents, /versionCode/);
    assert.match(agents, /strings\.xml/);
    assert.match(agents, /\.\/gradlew test/);
    assert.doesNotMatch(agents, /npm |\?v=|service-worker/);
    const platformDoc = fs.readFileSync(path.join(dir, '.loop/platform.md'), 'utf8');
    assert.match(platformDoc, /emulator/);
    assert.match(fs.readFileSync(path.join(dir, '.gitignore'), 'utf8'), /\*\.keystore/);
    const atlas = JSON.parse(fs.readFileSync(path.join(dir, 'docs/app-map/atlas.json'), 'utf8'));
    assert.match(atlas.graphs.find(g => g.id === 'release').rows.flat().map(n => n[1]).join(' '), /Google Play/);
    assert.match(atlas.graphs.find(g => g.id === 'overview').rows[0][0][1], /^Launch the app/);
    for (const file of ['AGENTS.md', 'HANDOFF.md', '.loop/workflow.md', '.loop/platform.md', 'docs/app-map/README.md']) {
        assert.doesNotMatch(fs.readFileSync(path.join(dir, file), 'utf8'), /\{\{\w+\}\}/, `${file} has no placeholders`);
    }
    const check = node(['--test', 'docs/app-map/atlas-contract.test.mjs'], dir);
    assert.equal(check.status, 0, check.stdout + check.stderr);
});

test('several platforms can be chosen together, and a brief without a platform is refused', async () => {
    const { normaliseBrief } = await import(INIT);
    assert.throws(() => normaliseBrief({ name: 'X', features: ['a'] }), /needs a platform/);
    assert.throws(() => normaliseBrief({ name: 'X', platform: 'toaster', features: ['a'] }), /Unknown platform/);
    const dir = path.join(temp(), 'both');
    const brief = JSON.parse(fs.readFileSync(BRIEF, 'utf8'));
    const briefPath = path.join(path.dirname(dir), 'b.json');
    fs.writeFileSync(briefPath, JSON.stringify(brief));
    const result = node([INIT, dir, '--brief', briefPath, '--platform', 'web,iphone']);
    assert.equal(result.status, 0, result.stderr);
    const atlas = JSON.parse(fs.readFileSync(path.join(dir, 'docs/app-map/atlas.json'), 'utf8'));
    assert.deepEqual(atlas.meta.platforms, ['web', 'ios']);
    const steps = atlas.graphs.find(g => g.id === 'release').rows.flat().map(n => n[1]).join(' | ');
    assert.match(steps, /Web: /);
    assert.match(steps, /iOS: .*TestFlight/);
});

test('START.md in an empty folder: answers are read, the template page is used, and building can start', () => {
    const dir = path.join(temp(), 'shop');
    fs.mkdirSync(path.join(dir, 'template-page'), { recursive: true });
    const start = fs.readFileSync(path.join(LOOP, 'start/START.md'), 'utf8')
        .replace('Name:\n', 'Name: Tiny Shop\n').replace('For:\n', 'For: local bakers\n')
        .replace('First release must:\n', 'First release must: take cake orders\n').replace('Platform:\n', 'Platform: web\n')
        .replace('Languages: en', 'Languages: en, ml')
        .replace('## Features\n> One line per feature: Title: step > step > step\n> Optional lines under a feature: fails: ..., done when: ..., release: 2\n> Release 1 is built first; release 2 and later come after.\n\n- ',
                 '## Features\n- Browse cakes: Open shop > See cakes\n- Order: Choose size > Confirm\n  - fails: No network: keep the form\n  - done when: baker gets the order\n- Reviews: Read > Write\n  - release: 2');
    fs.writeFileSync(path.join(dir, 'START.md'), start);
    fs.writeFileSync(path.join(dir, 'template-page/index.html'), '<!doctype html><h1>Bakery</h1>');
    fs.writeFileSync(path.join(dir, 'template-page/style.css'), 'h1{color:brown}');
    const result = spawnSync(process.execPath, [INIT, dir, '--start'], { encoding: 'utf8', env: { ...process.env, LOOP_AGENT: 'echo' } });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /Platform: Web app/);
    assert.match(result.stdout, /Use Loop for this project\. Build the next atlas map\.\n/, 'hands over to the agent with the kickoff prompt');
    assert.ok(fs.existsSync(path.join(dir, 'design/template-page/index.html')));
    assert.ok(fs.existsSync(path.join(dir, 'design/template-page/style.css')));
    assert.ok(!fs.existsSync(path.join(dir, 'template-page')), 'template folder moved into design/');
    assert.ok(fs.existsSync(path.join(dir, 'docs/START.md')) && !fs.existsSync(path.join(dir, 'START.md')), 'answers kept with the docs');
    assert.match(fs.readFileSync(path.join(dir, 'AGENTS.md'), 'utf8'), /## Template page[\s\S]*design\/template-page\/index\.html/);
    assert.match(fs.readFileSync(path.join(dir, '.loop/tracks/browse-cakes/spec.md'), 'utf8'), /follow the template page/);
    const brief = JSON.parse(fs.readFileSync(path.join(dir, 'docs/project-brief.json'), 'utf8'));
    assert.deepEqual(brief.languages, ['en', 'ml']);
    assert.equal(brief.features.find(f => f.id === 'order').failure, 'No network: keep the form');
    assert.equal(brief.features.find(f => f.id === 'reviews').release, 2);
    const atlas = JSON.parse(fs.readFileSync(path.join(dir, 'docs/app-map/atlas.json'), 'utf8'));
    assert.equal(atlas.meta.templatePage, 'design/template-page/index.html');
    assert.equal(node(['--test'], dir).status, 0);
});

test('an unfilled START.md says exactly what is missing', async () => {
    const { parseStartMd } = await import(INIT);
    assert.throws(() => parseStartMd(fs.readFileSync(path.join(LOOP, 'start/START.md'), 'utf8')), /missing: Name, Platform, Features/);
    const dir = temp();
    fs.copyFileSync(path.join(LOOP, 'start/START.md'), path.join(dir, 'START.md'));
    const result = node([INIT, dir]);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /START\.md is missing/);
});

test('a non-empty folder is refused unless adopting, and nothing is overwritten', () => {
    const dir = temp();
    fs.writeFileSync(path.join(dir, 'index.html'), '<p>existing</p>');
    fs.writeFileSync(path.join(dir, 'package.json'), JSON.stringify({ name: 'old', scripts: { test: 'echo mine' } }));
    const refused = node([INIT, dir, '--brief', BRIEF]);
    assert.equal(refused.status, 2);
    assert.match(refused.stderr, /not empty/);
    const adopted = node([INIT, dir, '--adopt', '--name', 'Old App']);
    assert.equal(adopted.status, 0, adopted.stderr);
    assert.equal(fs.readFileSync(path.join(dir, 'index.html'), 'utf8'), '<p>existing</p>');
    const pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
    assert.equal(pkg.scripts.test, 'echo mine', 'existing scripts are kept');
    assert.equal(pkg.scripts.atlas, 'node docs/app-map/build-atlas.mjs', 'atlas scripts are added');
    assert.ok(fs.existsSync(path.join(dir, '.loop/tracks/current-app/spec.md')));
    assert.match(adopted.stdout, /Platform: Web app .*detected/);
});

test('the atlas refuses a delivered map without real source, and accepts it with source', () => {
    const dir = path.join(temp(), 'p');
    assert.equal(node([INIT, dir, '--brief', BRIEF]).status, 0);
    const dataPath = path.join(dir, 'docs/app-map/atlas-data.mjs');
    const original = fs.readFileSync(dataPath, 'utf8');
    const flip = source => fs.writeFileSync(dataPath, original.replace(/("id": "first-open",[\s\S]*?"status": )"planned"([\s\S]*?"source": )""/, `$1"delivered"$2${JSON.stringify(source)}`));
    flip('');
    let build = node([path.join(dir, 'docs/app-map/build-atlas.mjs')]);
    assert.notEqual(build.status, 0);
    assert.match(build.stderr, /first-open.*needs source references/);
    flip('src/missing.js:1');
    build = node([path.join(dir, 'docs/app-map/build-atlas.mjs')]);
    assert.match(build.stderr, /source not found src\/missing\.js:1/);
    fs.mkdirSync(path.join(dir, 'src'));
    fs.writeFileSync(path.join(dir, 'src/first-open.js'), 'export const ready = true;\n');
    flip('src/first-open.js:1');
    build = node([path.join(dir, 'docs/app-map/build-atlas.mjs')]);
    assert.equal(build.status, 0, build.stderr);
    const next = node([path.join(dir, 'docs/app-map/atlas-status.mjs'), '--next']);
    assert.match(next.stdout, /Next: Write today \(write-today\)/, 'the next map moves on after delivery');
    const status = JSON.parse(node([path.join(dir, 'docs/app-map/atlas-status.mjs'), '--json']).stdout);
    assert.ok(status.delivered.includes('first-open'));
});

test('a broken edge stops the build with a clear message', () => {
    const dir = path.join(temp(), 'q');
    assert.equal(node([INIT, dir, '--brief', BRIEF]).status, 0);
    const dataPath = path.join(dir, 'docs/app-map/atlas-data.mjs');
    fs.writeFileSync(dataPath, fs.readFileSync(dataPath, 'utf8').replace('"Choose"', '"Choose"], ["open", "ghost", "Nowhere"'));
    const build = node([path.join(dir, 'docs/app-map/build-atlas.mjs')]);
    assert.notEqual(build.status, 0);
    assert.match(build.stderr, /broken edge open → ghost/);
});

test('brief rules: a name and at least one feature are required', async () => {
    const { normaliseBrief } = await import(INIT);
    assert.throws(() => normaliseBrief({ features: ['x'] }), /needs a name/);
    assert.throws(() => normaliseBrief({ name: 'X', platform: 'web' }), /at least one feature/);
    const brief = normaliseBrief({ name: 'Shop App', platform: 'web', features: ['Overview', 'Roadmap', 'Cart', 'Release'] });
    assert.deepEqual(brief.features.map(f => f.id), ['overview-1', 'roadmap-2', 'cart', 'release-4'], 'feature ids never clash with the overview or roadmap maps');
    assert.equal(brief.slug, 'shop-app');
});

test('every new project carries the 20-point legal checklist, wired into features and release', () => {
    const dir = path.join(temp(), 'legal');
    assert.equal(node([INIT, dir, '--brief', BRIEF]).status, 0);
    const list = fs.readFileSync(path.join(dir, '.loop/legal-checklist.md'), 'utf8');
    const rows = list.match(/^\| (\d+) \| .+ \| todo \|/gm) || [];
    assert.equal(rows.length, 20, 'twenty checks, all todo at the start');
    for (const text of ['Privacy Policy', 'Terms & Conditions', 'Cookie Policy', 'Cookie consent', 'request deletion', 'third-party API', 'AI-generated content', 'Open-source', 'copyrighted assets', 'Attribution', 'UI assets', 'Age restrictions', 'high-risk advice', 'Refund', 'Marketing claims', 'Final legal audit']) assert.match(list, new RegExp(text), text);
    assert.doesNotMatch(list, /\{\{\w+\}\}/, 'no placeholders left');
    assert.ok(fs.existsSync(path.join(dir, 'Loop/LEGAL-CHECKLIST.md')), 'project copy of the rules');
    assert.match(fs.readFileSync(path.join(dir, 'AGENTS.md'), 'utf8'), /## Legal checklist/);
    assert.match(fs.readFileSync(path.join(dir, '.loop/tracks/first-open/spec.md'), 'utf8'), /legal-checklist\.md/);
    assert.match(fs.readFileSync(path.join(dir, '.loop/tracks/release/spec.md'), 'utf8'), /Legal check 20/);
    const atlas = JSON.parse(fs.readFileSync(path.join(dir, 'docs/app-map/atlas.json'), 'utf8'));
    assert.equal(atlas.graphs.find(g => g.id === 'release').rows[0][0][0], 'legal-audit', 'release starts with the final legal audit');
    assert.ok(atlas.graphs.find(g => g.id === 'quality-gates').rows.flat().some(n => n[0] === 'legal'), 'every feature passes the legal rows gate');
    assert.equal(node(['--test'], dir).status, 0);
});

test('tracks carry boundaries, and atlas status reports weak or out-of-range source references', () => {
    const dir = path.join(temp(), 'bounds');
    assert.equal(node([INIT, dir, '--brief', BRIEF]).status, 0);
    const spec = fs.readFileSync(path.join(dir, '.loop/tracks/first-open/spec.md'), 'utf8');
    assert.match(spec, /## Boundaries\n\n- \*\*Always:\*\*[\s\S]*- \*\*Ask first:\*\*[\s\S]*- \*\*Never:\*\*/);
    fs.writeFileSync(path.join(dir, 'probe.txt'), 'real code\n\n}\n');
    fs.appendFileSync(path.join(dir, 'docs/app-map/atlas-data.mjs'), "\ngraphs[0].status = 'delivered'; graphs[0].source = 'probe.txt:1; probe.txt:2; probe.txt:3; probe.txt:9';\n");
    const out = node([path.join(dir, 'docs/app-map/atlas-status.mjs')], dir);
    assert.equal(out.status, 1);
    assert.match(out.stdout, /weak reference probe\.txt:2/);
    assert.match(out.stdout, /weak reference probe\.txt:3/);
    assert.match(out.stdout, /line out of range probe\.txt:9/);
    assert.doesNotMatch(out.stdout, /probe\.txt:1\b/);
});
