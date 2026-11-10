// Loop atlas browser check (needs Playwright; optional). Opens the built
// atlas and checks every map: step and connection counts, step selection,
// labels inside their boxes, keyboard use, phone width without sideways
// scroll, print-all and SVG export. Run after node docs/app-map/build-atlas.mjs.
import assert from 'node:assert/strict';
import { graphs, meta } from './atlas-data.mjs';

let chromium;
try { ({ chromium } = await import('playwright')); }
catch (error) {
    console.log(JSON.stringify({ skipped: true, reason: 'playwright is not installed; run npm i -D playwright to enable the browser check' }));
    process.exit(0);
}

const browser = await chromium.launch({ headless: true });
try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(new URL('./index.html', import.meta.url).href);
    await page.waitForFunction(count => window.atlasQA?.graphs.length === count, graphs.length);
    const checked = await page.evaluate(() => {
        const done = [];
        for (const graph of window.atlasQA.graphs) {
            window.atlasQA.navigate(graph.id);
            if (document.querySelectorAll('#graph .node').length !== graph.rows.flat().length) throw new Error('Step count: ' + graph.id);
            if (document.querySelectorAll('#graph .edge').length !== graph.edges.length) throw new Error('Connection count: ' + graph.id);
            for (const node of graph.rows.flat()) {
                window.atlasQA.selectNode(node[0]);
                if (document.getElementById('node-title').textContent !== node[1]) throw new Error('Selection: ' + graph.id + '/' + node[0]);
            }
            for (const el of document.querySelectorAll('#graph .node')) {
                const box = el.querySelector('rect').getBBox();
                for (const text of el.querySelectorAll('text')) {
                    const b = text.getBBox();
                    if (b.x < box.x || b.x + b.width > box.x + box.width || b.y + b.height > box.y + box.height) throw new Error('Label outside box: ' + graph.id + '/' + text.textContent);
                }
            }
            done.push(graph.id);
        }
        return done;
    });
    const first = graphs[0];
    await page.evaluate(id => window.atlasQA.navigate(id), first.id);
    await page.locator('#graph .node').first().focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#node-title').innerText(), first.rows.flat()[0][1], 'keyboard selects a step');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.selectOption('#map-select', graphs[graphs.length - 1].id);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false, 'no sideways page scroll on a phone');
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.evaluate(() => { window.print = () => { window.printRequested = true; }; });
    await page.click('#print-all');
    assert.equal(await page.locator('.print-page').count(), graphs.length);
    const download = page.waitForEvent('download');
    await page.click('#export-svg');
    assert.match((await download).suggestedFilename(), /\.svg$/);
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ project: meta.title, mapsChecked: checked.length, selections: true, labelBounds: true, keyboard: true, mobileOverflow: false, printMaps: graphs.length, svgDownload: true, pageErrors: errors }));
} finally {
    await browser.close();
}
