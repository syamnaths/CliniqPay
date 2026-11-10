// Loop atlas status: what is planned, building and delivered, what to build
// next, and whether any map has drifted from the source.
// Run: node docs/app-map/atlas-status.mjs            (summary)
//      node docs/app-map/atlas-status.mjs --next     (next map to build + its track)
//      node docs/app-map/atlas-status.mjs --json     (machine-readable)
import { priorityPlan } from './priority-plan.mjs';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { graphs, meta } from './atlas-data.mjs';

const directory = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(directory, '../..');
const args = new Set(process.argv.slice(2));
const order = meta.buildOrder || graphs.map(g => g.id);
const byId = Object.fromEntries(graphs.map(g => [g.id, g]));
const status = g => g.status || 'delivered';

const issues = [];
for (const g of graphs) {
    if (status(g) !== 'planned' && !g.source) issues.push(`${g.id}: ${status(g)} but has no source references`);
    for (const ref of g.source ? g.source.split('; ') : []) {
        const [file, line = '1'] = ref.split(':');
        const full = path.resolve(root, file);
        if (!fs.existsSync(full)) { issues.push(`${g.id}: source missing ${ref}`); continue; }
        const lines = fs.readFileSync(full, 'utf8').split('\n');
        const text = (lines[+line - 1] ?? '').replace(/[\s{}()\[\];,]/g, '');
        if (+line > lines.length) issues.push(`${g.id}: line out of range ${ref}`);
        else if (+line > 1 && text.length < 3) issues.push(`${g.id}: weak reference ${ref} (blank or closing line; re-point it to the code it describes)`);
    }
    const track = path.resolve(root, '.loop/tracks', g.id);
    if (status(g) !== 'delivered' && g.group === (meta.featureGroup || 'Features') && !fs.existsSync(track)) issues.push(`${g.id}: no track folder at .loop/tracks/${g.id}`);
}

const priorities = priorityPlan(graphs, meta);
issues.push(...priorities.issues);
const next = byId[priorities.next] || null;
const summary = {
    project: meta.title,
    snapshot: `${meta.commit} · ${meta.date}`,
    total: graphs.length,
    delivered: graphs.filter(g => status(g) === 'delivered').map(g => g.id),
    building: graphs.filter(g => status(g) === 'building').map(g => g.id),
    planned: graphs.filter(g => status(g) === 'planned').map(g => g.id),
    next: next ? { id: next.id, title: next.title, status: status(next), track: `.loop/tracks/${next.id}/spec.md` } : null,
    priorities,
    issues
};

if (args.has('--json')) {
    console.log(JSON.stringify(summary, null, 2));
} else if (args.has('--next')) {
    if (issues.length) console.log(`Invalid atlas plan:\n- ${issues.join('\n- ')}`);
    else if (!next) console.log(priorities.queue.length ? 'No ready map. Resolve blockers or checkpoint the blocked active map before switching work.' : 'Every map is delivered. Add the next feature to the atlas as a planned map.');
    else {
        console.log(`Next: ${next.title} (${next.id}) · ${status(next)}`);
        console.log(`Track: ${summary.next.track}`);
        console.log('Steps to build:');
        for (const [id, label, detail] of next.rows.flat()) console.log(`  - ${label} [${id}]: ${detail}`);
    }
} else {
    const pct = summary.total ? Math.round((summary.delivered.length / summary.total) * 100) : 0;
    console.log(`${summary.project} — ${summary.snapshot}`);
    console.log(`Maps: ${summary.total} · delivered ${summary.delivered.length} · building ${summary.building.length} · planned ${summary.planned.length} (${pct}% of maps delivered)`);
    if (next) console.log(`Next to build: ${next.title} (${next.id}) → ${summary.next.track}`);
    for (const warning of priorities.warnings) console.log(`Warning: ${warning}`);
    for (const item of priorities.queue.filter(g => g.blockers.length)) console.log(`Blocked: ${item.title} — ${item.blockers.join('; ')}`);
    console.log(issues.length ? `Issues:\n- ${issues.join('\n- ')}` : 'Issues: none');
}
process.exit(issues.length ? 1 : 0);
