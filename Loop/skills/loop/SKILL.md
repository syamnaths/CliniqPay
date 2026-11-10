---
name: loop
description: "Use when the user says 'Use Loop for this project', 'Apply Loop', 'Resume with Loop', 'Build the next atlas map', or asks for Loop project orchestration. Asks which platform to build for at the start, then starts new projects atlas-first with loop-init.mjs, adopts existing projects, builds one atlas map at a time with proof, and keeps a single CURRENT RESUME handoff."
---

# Loop orchestration (v0.4.5, atlas-first)

Apply `loop.md` from the project-local `Loop/` folder when present, otherwise from the plugin root. Companion files: `ATLAS-FIRST.md` (atlas format and build loop), `OWNER-COMMUNICATION.md`, `EFFICIENT-WORKFLOW.md`, `DELIVERY-WORKFLOW.md`, `SECURITY.md`, `LEGAL-CHECKLIST.md` (20 legal checks), `MODEL-ROUTING.md`. The project copy may be newer than the installed plugin; do not edit the installed cache.

## Invocation

An explicit request to use or resume **Loop** selects this skill immediately. Loop is this local workflow, not an OpenAI product term: do not open OpenAI Docs or search the web to identify it. Never ask the user to pick a task class; infer it.

If the prompt contains `[LOOP_ROUTED_CHILD]`, this is already a routed bounded task: do not classify or dispatch again. Do only that task, validate it, and return.

## New project (empty folder or new idea)

Loop asks the questions and then starts building. Do not wait for a separate approval once the answers are enough.

1. Read-only check of the target. A filled `START.md` there means: read it, ask only what is missing. A `template-page/` folder there is the owner's basic template page.
2. Otherwise ask the questions from `start/START.md` (Loop root) in **one** message, numbered, plain words: name; for whom; what the first release must do; **which platform** (web, Android, iPhone, both mobile, desktop, backend/API, command-line, other, or several); stack or "to decide"; languages; features with steps; must-not-do; and whether they have a basic template page (attach or give a path). If unsure about platform or stack, give A/B/C options with a recommendation; never choose for them. No files, Git or installs before the answers.
3. Write the answers into `<target>/START.md` and any template files into `<target>/template-page/`.
4. When name, platform and at least one feature are known, run from the Loop root:

   ```
   node scripts/loop-init.mjs <target-folder> --git
   ```

   It reads `START.md` (moved to `docs/START.md`), moves the template page to `design/template-page/`, and creates `AGENTS.md`, `HANDOFF.md` (one CURRENT RESUME block), `.loop/workflow.md`, `.loop/platform.md` (stack, test commands, proof ladder, platform rules, release path), one track per map and `docs/app-map/` (atlas data, builder, status, atlas check, `index.html`). Feature maps and the `release` map start `planned`. JavaScript projects also get `npm run atlas*` scripts; others use the plain `node docs/app-map/...` commands listed in `AGENTS.md`.
5. Build straight away: one line on the atlas overview, then the build loop below on the first map. Every screen follows `design/template-page/` when it exists. Report each delivered map with proof and carry on to the next. Stop only at approval gates or real product decisions.

## Existing project

Read `AGENTS.md`, `HANDOFF.md` (CURRENT RESUME only), `.loop/platform.md`, then the atlas status command from `AGENTS.md`. If the project has no atlas yet, run `node scripts/loop-init.mjs <project> --adopt --name "<Name>" [--platform <id>]` (it never overwrites files and reports the detected platform), then map current behaviour as `delivered` maps with real `file:line` sources before planning new work. Preserve unrelated changes; reconcile docs with code.

## Build loop (one map at a time)

1. The atlas next command → the single ready active map, or the first dependency-ready map in `meta.buildOrder`, and its track. Resolve invalid plans or checkpoint blocked active work before choosing another map.
2. Confirm the map's steps are still right; edit the map first if not (`planned` → `building`).
3. Follow TDD for that map's testable behaviour: confirm RED, implement GREEN, then refactor. Reuse coverage; unit-test changed logic and integration-test changed boundaries, including applicable failure paths (DELIVERY-WORKFLOW.md). Record mocks, blocked checks and not-applicable levels.
4. Apply the professional design gate in `loop.md`: preserve the agreed reference/system; otherwise default to Material Design 3 for web/Android/cross-platform or Apple HIG/native components for native iOS/macOS, following other native platform conventions where applicable. Reuse the stack, record the design choice, include relevant interaction states, inspect rendered screens at representative sizes, and correct layout/accessibility defects. Show visual evidence or state that review is blocked. Prove at the strongest level in `.loop/platform.md` (for example browser, emulator, simulator, staging, device). Say which level you reached.
   Legal: if the map collects data, adds cookies or trackers, an API, a package, assets, AI content, payments, advice or marketing text, update those rows in `.loop/legal-checklist.md` (trigger table in `LEGAL-CHECKLIST.md`). No touched row may stay `todo`.
5. Before delivery, perform the feature security review in `SECURITY.md`: list evidenced vulnerabilities, discuss them with the owner before remediation, fix agreed findings and rerun tests/review. While awaiting discussion keep the goal active, checkpoint and mark the feature `planned` with `blockedBy` before selecting other ready work. No confirmed findings means report checks and limits and continue. Then flip the map to `delivered` with real `file:line` sources. The atlas build refuses fake or missing sources.
6. Run the product tests and the atlas check, update the CURRENT RESUME block (progress from the atlas status), commit with a checkpoint id.
7. Report to the owner in plain words with a screenshot when visual, then repeat.

On the first map, mark every legal check `todo` or `n/a` (with reason) from the brief, and ask the owner once which countries the users are in. Before release, run check 20 (final legal audit): no `todo` or `blocked` rows, and an owner A/B/C decision on every `lawyer` row. Loop drafts legal pages; it never claims legal compliance.

**Goal pauses belong to the owner.** Keep the goal active until it is complete. Never set it to paused unless the owner explicitly asks. Take necessary temporary rests (for example cooldowns, rate-limit waits or required recovery) without pausing the goal; record the reason and restart condition, then continue automatically when checks pass and the host permits. Continue other authorised work when safe. A rest never bypasses resource guards, approval gates or host limits. The owner may pause while riding or travelling and resume on arrival; do not infer a pause from absence or travel, and do not resume an owner-paused goal until the owner asks.

Resource guards (CPU, memory, disk, thermal): rules by task profile — approved light work may run when its checks pass; unknown readings block heavy work; a known warning blocks both. Unknown is never "safe", and a clear state needs a numeric reading. Every necessary rest or owner-requested pause reports blocker, latest reading and time, what is still allowed, restart condition and ETA (measured, or "unknown"). When a rule changes, update every copy (goal, `AGENTS.md`, `.loop/`, tracks, handoff); a copy that cannot be edited is its own `BLOCKED` item, and the goal is not reported as resumed.

Release, push, spending, data deletion, publishing legal text and user-visible content changes stay behind the approval gates in `loop.md`. When the owner must push, give one copy-paste command and confirm with `git fetch` afterwards.

## Prioritise before starting work

Keep one active delivery map (the current big rock). Finish its supporting fixes, tests and docs before unrelated work. Dependencies come first; then the smallest valuable outcome and risk reduction. `meta.buildOrder` is the agreed order; the Eisenhower matrix is triage, not an automatic override. Record blockers and reasons for reordering. Before switching from a blocked active map, checkpoint its restart step in the track and handoff and return it to `planned` with `blockedBy` retained. Multiple building maps are invalid; priority never bypasses dependencies or release boundaries. See `ATLAS-FIRST.md` → Priorities and one active big rock.

## Routing

Use local context first (handoff, atlas, the track, the real source). Route bounded subtasks to the least-cost healthy model that meets the need. With Codex CLI 0.148.0+, use `scripts/codex_model_router.py`; it reads only the `[LOOP_CLASSIFY]` … `[/LOOP_CLASSIFY]` slice for classification when present, applies per-run model overrides, and never rewrites global config. If automatic switching is unavailable, recommend a model, keep a resumable checkpoint, and ask the engineer to switch with the host selector (for example `/model`). Never claim a switch you did not see.

## Boundaries

Browser, emulator or simulator checks and screenshots are used when the change is visual or the owner asks, through the project's tests or the atlas verify command. Destructive or history-changing recovery needs approval. The skill orchestrates; the project's source, tests, atlas and handoff are the record.
