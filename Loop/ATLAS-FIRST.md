# Atlas-first delivery

Loop builds every project from a **flow atlas**: a set of small, connected maps that show how the product behaves. The atlas is written **before** code, updated **with** every change, and checked **by machine**. This method was proven on the Lite meditation PWA (51 maps, 435 steps, 5 languages, dozens of features) and is now the default for every Loop project, on any platform. The atlas tools need Node 18+ on the developer's machine only; the product can be web, Android, iOS, desktop, backend, command-line or anything else.

## Why

- The owner can see the whole product on one page, without reading code.
- Every session starts from the same picture, so nothing is rebuilt by mistake and nothing is forgotten.
- A feature is not "done" until its map says so, and the map cannot say so without real source references.
- Plans and delivered behaviour never mix: plans live as `planned` maps or in `FIX-QUEUE.md`.

## The atlas files (in every project)

| File | Purpose |
| --- | --- |
| `docs/app-map/atlas-data.mjs` | The only file people edit. Exports `meta` and `graphs`. |
| `docs/app-map/build-atlas.mjs` | Validates every map and writes the outputs below. Fails on broken edges, unknown drilldowns, missing source files or out-of-range lines. |
| `docs/app-map/atlas-status.mjs` | Shows planned / building / delivered, the next map to build and drift issues. `--next` prints the steps to build. |
| `docs/app-map/atlas-contract.test.mjs` | Atlas contract: it builds, every feature and the release map has a track, delivered maps have real source, the build order is complete, the platform is recorded. |
| `docs/app-map/verify-atlas.mjs` | Optional browser check of the atlas page itself (Playwright): counts, selection, label fit, keyboard, phone width, print, SVG export. |
| `docs/app-map/index.html` | Generated interactive atlas. Open it in a browser. |
| `docs/app-map/FLOW-REFERENCE.md`, `atlas.json` | Generated text + Mermaid reference and machine copy. |
| `docs/app-map/FIX-QUEUE.md` | Proposed and completed fixes. Plans never go into delivered maps. |
| `.loop/platform.md` | The platform chosen at the start: stack, test commands, proof ladder, platform rules, release path. |

Commands: JavaScript projects get `npm run atlas`, `atlas:status`, `atlas:next`, `atlas:check`, `atlas:verify`. Other projects run the same tools directly, for example `node docs/app-map/atlas-status.mjs --next`. `AGENTS.md` lists the exact commands for each project.

## Map format

```js
graphs.push({
  id: 'checkout',                 // unique, also the track folder name
  group: 'Features',              // Start here | Features | Systems | Supporting pages (meta.groups can change this)
  title: 'Checkout',
  subtitle: 'From cart to paid order.',
  status: 'planned',              // planned → building → delivered
  source: 'src/checkout.js:1; tests/checkout.test.mjs:1', // required unless planned
  rows: [                         // each row is drawn left-to-right, rows top-to-bottom
    [['cart', 'Review cart', 'Items, totals and edit links.']],
    [['pay', 'Pay', 'Card form; errors shown in plain words.'], ['fail', 'Payment fails', 'Keep the cart; offer retry.']],
    [['done', 'Order placed', 'Receipt screen and email.']]
  ],
  edges: [['cart', 'pay', 'Continue'], ['pay', 'done', 'Approved'], ['pay', 'fail', 'Declined'], ['fail', 'pay', 'Retry']],
  drilldowns: { pay: 'payments' },// optional: open another map from a step
  notes: ['Prices come from the server; the client never sets them.']
});
```

Write every step as the user experiences it, with the real guard, default, exit and failure path. Short labels, specific details.

## The build loop

1. **Init.** Loop asks the start questions (or reads a filled `START.md`; the platform is chosen there), then `node <Loop>/scripts/loop-init.mjs <project>` creates the project, the atlas (an overview, a roadmap, one `planned` map per feature, a quality-gates map and a `release` map for the platform), a track per map, `.loop/platform.md`, `AGENTS.md`, `HANDOFF.md` and the atlas check. It moves a template page into `design/template-page/` when given, builds the atlas and prints the first feature. Building starts right away.
2. **Pick.** The atlas next command continues the single active map if ready; otherwise names the first ready map in `meta.buildOrder`, with its steps and track. A blocked active map needs a recorded checkpoint and a return to `planned` before switching. Invalid plans have no next recommendation.
3. **Plan the map first.** Before code, make the map exact: steps, branches, failure paths, defaults. Show it to the owner when a product decision is open. Set `status: 'building'`.
4. **Build to the map.** Follow TDD for testable behaviour: confirm RED before implementation, implement GREEN and refactor. Reuse unit coverage for logic and integration coverage for changed boundaries (DELIVERY-WORKFLOW.md).
5. **Prove it.** Run the product tests, rebuild the atlas and run the atlas check. Prove behaviour at the strongest level in `.loop/platform.md` (browser, emulator, simulator, staging or device) and say which level you reached. Take screenshots or examples when the owner will judge by eye.
6. **Security review, then flip the map.** Follow the feature review in `SECURITY.md`: list evidenced vulnerabilities, discuss findings with the owner before remediation, fix agreed findings and rerun tests/review. Pending discussion keeps the feature undelivered and the goal active. No confirmed findings means report the limits and continue. Add `source` references (`file:line`), set `status: 'delivered'`, update notes with the evidence you actually have. The build refuses a delivered map without real source.
7. **Record.** Update the track, `FIX-QUEUE.md` (if a tracked fix), `meta.commit`/`meta.date`/`meta.scope`, and the `CURRENT RESUME` block in `HANDOFF.md`.
8. **Repeat** from step 2. The `release` map comes last in the build order. When every map is delivered, add the next feature as a new `planned` map.

## Rules that keep the atlas honest

- A behaviour change and its map change land in the **same** commit.
- If source and map disagree, read the source, fix whichever is wrong, and say so.
- Never mark `delivered` from a plan, a mock or a passing wording test. Notes must say which evidence exists: source review, unit test, browser / emulator / simulator test, staging, device check.
- Do not invent flows to have something to draw. A non-flow change only needs a check that the atlas is still accurate.
- When a feature is removed, remove or rewrite its map, and say "removed (owner: reason)" in notes so history is clear.
- Separate fact from guess. A step taken straight from the source needs no label; a step you inferred (not yet read in code) ends with `(inferred)` until it is checked.
- Look in the atlas and the track before searching files. Read source only for the map steps the task touches.
- Keep source references pointing at the code they describe. The atlas status command reports a reference that is out of range or lands on a blank or closing line; re-point it when code moves.
- Keep the atlas a development tool: never precache or ship it inside the product bundle or app package.

## Existing projects

For a project that has no atlas, start with `loop-init.mjs <project> --adopt [--platform ...]`: it guesses the platform from the files (and says so), adds the atlas tools and a starter `atlas-data.mjs` without touching other files. Then map the current behaviour as `delivered` maps (with source references) before planning new features as `planned` maps.

## Priorities and one active big rock

Use big rocks for delivery and the Eisenhower matrix for triage. A big rock is a small end-to-end outcome, not an entire subsystem. Small rocks are supporting fixes, tests and documentation inside that outcome. Keep one delivery map `building` at a time by default; finish and verify it before starting another. Do not open unrelated work just because it is easy. Parallel work is optional only for independent work with separate ownership and an integration check; never required.

Keep `meta.buildOrder` as the single agreed execution order. Order dependencies before dependants, then prioritise the smallest valuable first-release outcome, blockers and risk-reducing proof. Use effort only as a tie-breaker; avoid invented numerical scores. Record the reason when changing order. Continue the active map before picking another. If it is blocked, record why and the exact restart step in its track and handoff, return it to `planned` while retaining `blockedBy`, then deliberately select the next ready map; do not pretend the blocked work is complete.

Each delivery map may carry `priority: { rock: 'big' | 'small', important: boolean, urgent: boolean, reason: string }`, `dependsOn: [mapId]` and `blockedBy: 'reason'`. Missing priority means unclassified, not unimportant. Urgent requires an actual deadline or immediate impact in the reason. Important + urgent means triage now; important + not urgent means protect focus; urgent + not important means timebox or delegate only if authorised; neither means defer for owner review, never silently delete scope. The matrix does not override dependencies, approval gates or an active map. Reorder the source build order deliberately when triage warrants it.

The atlas dashboard shows current focus, ordered ready/blocked work, big/small rocks and the four matrix quadrants. Its next recommendation must match `atlas-status --next`. Reassess after a delivered map or a material blocker, not after every small task. Track elapsed delivery time, blocked time and reopened work when available; do not promise faster development or a percentage improvement without comparable measurements.


Dependency precedence is mandatory: all unfinished prerequisites must be in the build order, before their dependants. The starter uses a stable dependency order within each release; dependencies on later releases require a scope decision instead of an automatic release change. Cycles, missing dependencies, multiple building maps and delivered maps with unfinished prerequisites are invalid. Release depends on every feature in the current atlas and must come after them; adding future scope requires updating the release plan explicitly. Urgency does not override any of these constraints.
