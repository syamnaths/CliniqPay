// Loop atlas builder. Reads atlas-data.mjs, validates every map, and writes
// index.html (interactive atlas), FLOW-REFERENCE.md (text + Mermaid),
// atlas.json and, when meta.inventoryPages is set, CONTROL-INVENTORY.md.
// No dependencies. Run: node docs/app-map/build-atlas.mjs
import { priorityPlan } from './priority-plan.mjs';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { graphs, meta } from './atlas-data.mjs';

const directory = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(directory, '../..');
const STATUSES = ['planned', 'building', 'delivered'];
const groupOrder = meta.groups || ['Start here', 'Features', 'Systems', 'Supporting pages'];
const problems = [];

graphs.sort((a, b) => {
    const ga = groupOrder.indexOf(a.group), gb = groupOrder.indexOf(b.group);
    return (ga < 0 ? 99 : ga) - (gb < 0 ? 99 : gb);
});

const seen = new Set();
for (const graph of graphs) {
    const where = `map "${graph.id}"`;
    for (const key of ['id', 'group', 'title', 'subtitle']) if (!graph[key]) problems.push(`${where}: missing ${key}`);
    if (seen.has(graph.id)) problems.push(`${where}: duplicate map id`);
    seen.add(graph.id);
    graph.status = graph.status || 'delivered';
    if (!STATUSES.includes(graph.status)) problems.push(`${where}: status must be ${STATUSES.join(' / ')}`);
    graph.source = graph.source || '';
    graph.notes = graph.notes || [];
    const nodes = (graph.rows || []).flat();
    if (!nodes.length) problems.push(`${where}: has no steps`);
    const ids = new Set(nodes.map(node => node[0]));
    if (ids.size !== nodes.length) problems.push(`${where}: duplicate step id`);
    for (const node of nodes) if (node.length < 3 || !node[1] || !node[2]) problems.push(`${where}: step ${node[0]} needs [id, label, detail]`);
    for (const edge of graph.edges || []) {
        if (!ids.has(edge[0]) || !ids.has(edge[1])) problems.push(`${where}: broken edge ${edge.join(' → ')}`);
    }
    for (const [node, target] of Object.entries(graph.drilldowns || {})) {
        if (!ids.has(node)) problems.push(`${where}: drilldown from unknown step ${node}`);
        if (!graphs.some(other => other.id === target)) problems.push(`${where}: drilldown to unknown map ${target}`);
    }
    // Delivered or building maps must point at real source. Planned maps may not have any yet.
    if (graph.status !== 'planned' && !graph.source) problems.push(`${where}: ${graph.status} map needs source references (file:line)`);
    for (const reference of graph.source ? graph.source.split('; ') : []) {
        const [file, line = '1'] = reference.split(':');
        const full = path.resolve(root, file);
        if (!fs.existsSync(full)) { problems.push(`${where}: source not found ${reference}`); continue; }
        if (+line > fs.readFileSync(full, 'utf8').split('\n').length) problems.push(`${where}: line out of range ${reference}`);
    }
}
const priorities = priorityPlan(graphs, meta);
problems.push(...priorities.issues);
if (problems.length) {
    console.error('Atlas build stopped:\n- ' + problems.join('\n- '));
    process.exit(1);
}

const data = JSON.stringify({ meta, graphs, priorities }).replaceAll('<', '\\u003c');
const template = fs.readFileSync(path.join(directory, 'atlas-template.html'), 'utf8');
fs.writeFileSync(path.join(directory, 'index.html'), template.replace('/* ATLAS_DATA */', `const atlas = ${data};`));

const clean = value => String(value).replaceAll('|', '/').replaceAll('\n', ' ');
let markdown = `# ${meta.title}\n\nSource snapshot: ${meta.commit} · ${meta.date}.\n\n${meta.scope}\n\nOpen [the interactive atlas](./index.html) for diagrams, step details, source references, SVG export and printing.\n\n`;
markdown += '## Index\n\n' + graphs.map((g, i) => `${i + 1}. [${g.title}](#${g.id}) — ${g.status}`).join('\n') + '\n\n';
for (const g of graphs) {
    const refs = g.source ? g.source.split('; ').map(ref => `[${ref}](../../${ref.split(':')[0]})`).join(', ') : 'none yet (planned)';
    markdown += `<a id="${g.id}"></a>\n\n## ${g.title}\n\nStatus: **${g.status}** · ${g.subtitle}\n\nSources: ${refs}.\n\n`;
    markdown += '```mermaid\nflowchart TD\n';
    for (const [id, label] of g.rows.flat()) markdown += `  ${id}["${label.replaceAll('"', "'")}"]\n`;
    for (const [from, to, label] of g.edges) markdown += `  ${from} -->|"${label.replaceAll('"', "'")}"| ${to}\n`;
    markdown += '```\n\n| Step | Behaviour |\n| --- | --- |\n';
    for (const [, label, detail] of g.rows.flat()) markdown += `| ${clean(label)} | ${clean(detail)} |\n`;
    markdown += '\n' + g.notes.map(n => `- ${n}`).join('\n') + '\n\n';
}
markdown += '## Coverage and limitations\n\nPlanned maps describe intended behaviour and are not delivered. Delivered maps are source-reviewed; they are not proof of runtime, device or performance behaviour unless the notes say which evidence exists.\n';
fs.writeFileSync(path.join(directory, 'FLOW-REFERENCE.md'), markdown);
fs.writeFileSync(path.join(directory, 'atlas.json'), JSON.stringify({ meta, graphs }, null, 2) + '\n');

if (!Array.isArray(meta.inventoryPages) || !meta.inventoryPages.length) {
    fs.writeFileSync(path.join(directory, 'CONTROL-INVENTORY.md'), `# Screen and control inventory\n\nNo pages listed yet. Add HTML entry pages to \`meta.inventoryPages\` in atlas-data.mjs (for example ['index.html']) and run npm run atlas to list every button, link, input and select.\n`);
} else {
    let inventory = `# Screen and control inventory\n\nSource snapshot: ${meta.commit} · ${meta.date}.\n\n`;
    for (const file of meta.inventoryPages) {
        const full = path.resolve(root, file);
        if (!fs.existsSync(full)) continue;
        const html = fs.readFileSync(full, 'utf8');
        inventory += `## ${file}\n\n| Line | Element | Identifier / label | Details |\n| --- | --- | --- | --- |\n`;
        for (const match of html.matchAll(/<(input|select|button|a|summary)\b([^>]*?)(?:>([\s\S]*?)<\/\1\s*>|\/?>)/g)) {
            const [, tag, attrs, inner = ''] = match;
            const attr = name => new RegExp('(?:^|\\s)' + name + '="([^"]*)"').exec(attrs)?.[1] || '';
            const line = html.slice(0, match.index).split('\n').length;
            const text = inner.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
            const label = attr('id') || attr('name') || attr('aria-label') || text.slice(0, 80) || '(unlabeled)';
            const extra = [attr('type') && 'type=' + attr('type'), attr('href') && 'href=' + attr('href'), attr('data-i18n') && 'label=' + attr('data-i18n')].filter(Boolean).join(' · ');
            inventory += `| ${line} | ${tag} | ${clean(label).replaceAll('<', '&lt;')} | ${clean(extra)} |\n`;
        }
        inventory += '\n';
    }
    fs.writeFileSync(path.join(directory, 'CONTROL-INVENTORY.md'), inventory);
}

const count = status => graphs.filter(g => g.status === status).length;
console.log(JSON.stringify({
    maps: graphs.length, planned: count('planned'), building: count('building'), delivered: count('delivered'),
    steps: graphs.reduce((n, g) => n + g.rows.flat().length, 0), connections: graphs.reduce((n, g) => n + g.edges.length, 0),
    output: path.relative(root, path.join(directory, 'index.html'))
}));
