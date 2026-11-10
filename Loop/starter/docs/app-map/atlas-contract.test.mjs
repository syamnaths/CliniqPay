// Atlas contract: the atlas builds, every feature map has a track, delivered
// maps point at real source, and the build order covers every feature.
// Run: node --test docs/app-map/atlas-contract.test.mjs  (any platform; Node 18+)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const { graphs, meta } = await import(path.join(root, 'docs/app-map/atlas-data.mjs'));
const featureGroup = meta.featureGroup || 'Features';

test('the atlas builds without errors', () => {
    const output = execFileSync(process.execPath, [path.join(root, 'docs/app-map/build-atlas.mjs')], { encoding: 'utf8' });
    const summary = JSON.parse(output.trim().split('\n').pop());
    assert.equal(summary.maps, graphs.length);
    assert.ok(fs.existsSync(path.join(root, 'docs/app-map/index.html')));
});

test('every feature map (and the release map) has a track with a spec', () => {
    for (const graph of graphs.filter(g => g.group === featureGroup || g.id === 'release')) {
        assert.ok(fs.existsSync(path.join(root, '.loop/tracks', graph.id, 'spec.md')), `missing .loop/tracks/${graph.id}/spec.md`);
    }
});

test('delivered and building maps point at real source', () => {
    for (const graph of graphs.filter(g => (g.status || 'delivered') !== 'planned')) {
        assert.ok(graph.source, `${graph.id} needs source references`);
        for (const ref of graph.source.split('; ')) assert.ok(fs.existsSync(path.join(root, ref.split(':')[0])), `${graph.id}: ${ref} not found`);
    }
});

test('the build order lists every feature map exactly once', () => {
    const features = graphs.filter(g => g.group === featureGroup).map(g => g.id).sort();
    const order = (meta.buildOrder || []).filter(id => features.includes(id));
    assert.deepEqual([...order].sort(), features);
    assert.equal(new Set(order).size, order.length);
});

test('the handoff has exactly one CURRENT RESUME block', () => {
    const handoff = fs.readFileSync(path.join(root, 'HANDOFF.md'), 'utf8');
    assert.equal((handoff.match(/^## CURRENT RESUME/gm) || []).length, 1);
});

test('the platform is recorded', () => {
    assert.ok(Array.isArray(meta.platforms) && meta.platforms.length, 'meta.platforms lists the chosen platform(s)');
    assert.ok(fs.existsSync(path.join(root, '.loop/platform.md')), '.loop/platform.md exists');
});
