# Changelog

## Unreleased

- Name design defaults: Material Design 3 for web/Android/cross-platform, Apple HIG/native components for native iOS/macOS and platform conventions elsewhere. Preserve existing approved designs and avoid automatic package installs.

- Add an explicit professional design gate: agreed visual direction, consistent components, complete interaction states, responsive/accessibility checks and rendered visual evidence. Include it in feature tracks and the cloud instruction.

- Make TDD explicit for testable behavior, unit coverage for logic and integration coverage for changed boundaries. Reuse existing tests. Feature closure now includes a focused security/pentest review, evidenced vulnerability discussion before remediation, regression-tested fixes and re-review; awaiting discussion never pauses the goal.

- Resolve prioritisation conflicts: stable dependency ordering inside releases, explicit cross-release conflict errors, one active map enforced, blocked-work checkpoints before switching, implicit release dependencies validated, and no next recommendation for invalid plans.

- Prioritise one active big rock, dependencies and valuable outcomes. Atlas dashboard adds focus, ordered queue and Eisenhower triage, sharing its next recommendation with the CLI. Unclassified priorities remain explicit; no speed gains are claimed without measurement.

- Goal pauses belong to the owner. Necessary rests keep the goal active and work continues when checks pass and the host permits. Owner-requested pauses (including while riding or travelling) wait for the owner to resume. Core policy, skill, communication, workflow and starter handoff instructions agree.

## 0.4.6 — honest guards and pauses

Lessons from a resource-guard fix (thermal rules that differed between the guard and the goal).

- `loop.md` §6 new "Resource guards and pauses": rules by task profile (approved light work may run when its checks pass; unknown blocks heavy work; a known warning blocks both); unknown is never "safe"; a clear state needs a numeric reading ("has not been recorded" stays unknown); guard tests cover light and heavy for clear, warning and unknown; five-part pause report with measured or "unknown" ETA.
- `loop.md` §9: one rule, one wording everywhere (goal, `AGENTS.md`, `.loop/`, tracks, handoff); a copy that cannot be edited, such as a stored goal, is its own sync blocker, and the goal is not reported as resumed.
- `OWNER-COMMUNICATION.md`: five-line pause message. `EFFICIENT-WORKFLOW.md` and the skill point to the new rules. `HANDOFF.md` template has a "Pause / blockers" line.
- Four new behaviour scenarios and a policy test. Stale atlas references were already covered in 0.4.5 (`atlas-status.mjs` reports weak references).
- Proper `.gitignore`: the project template now covers secrets and keys (keeps `.env.example`), dependencies, build output, test and browser output, logs, OS and editor files, and local databases, while keeping the Loop record (`.loop/`, `docs/app-map/`, `design/`, `Loop/`, `HANDOFF.md`, `AGENTS.md`). The Loop folder has its own `.gitignore` (caches, `*.tgz`, `_to_delete/`, `.DS_Store`). New starter test.
- Previous versions of changed files are kept in `archive/v0.4.5/`.

## 0.4.5 — reuse first, honest atlas

Ideas from Ponytail, OmniRoute, Graphify and agent-skills; only what Loop lacked. Details and what was skipped: `FRAMEWORK-BENCHMARK.md`.

- `loop.md` §3 craft rules: reuse-first ladder before new code, never trim the safety net, `Known limit:` markers listed in `FIX-QUEUE.md`, find out why odd code exists before removing it, check the real docs.
- `DELIVERY-WORKFLOW.md`: approve a change that clearly improves the code; polish goes to the fix queue.
- `MODEL-ROUTING.md`: gateway safety (loopback, keys, no body logging, fail-closed checks, short fallback with cooldown, risky modes off).
- `ATLAS-FIRST.md`: fact vs guess `(inferred)` label, atlas before file search, keep references pointing at real code. `atlas-status.mjs` now reports out-of-range and weak (blank or closing-line) references.
- New tracks get a Boundaries section (Always / Ask first / Never, using the brief's must-not list).
- New test: tracks carry boundaries and atlas status reports weak references. Five more behaviour scenarios. Previous versions of changed files are kept in `archive/v0.4.4/`.

## 0.4.4 — focus and craft

Ideas from four agent plugins (Superpowers, Karpathy guidelines, i-have-adhd, Claude Octopus); only what Loop lacked. Details and what was skipped: `FRAMEWORK-BENCHMARK.md`.

- `loop.md` §3: craft rules for every change — say your assumption, simplest thing that works, surgical edits, done means a check passes.
- `OWNER-COMMUNICATION.md`: focus-friendly replies — answer first, one topic, status line, numbered steps with minutes, lists of five or fewer, show the win, flat errors, one next step.
- `DELIVERY-WORKFLOW.md`: receiving review (check each comment before applying it) and an opt-in second opinion for high-risk changes (fresh reviewer, one lens, disagreements to the owner).
- `tests/loop-skill-scenarios.md`: five new behaviour scenarios for these rules.
- Previous versions of changed files are kept in `archive/v0.4.3/`.

## 0.4.3 — legal checklist

- New `LEGAL-CHECKLIST.md`: 20 legal checks in five groups (legal pages, personal data, third parties and licences, users and selling, final audit), with status values `todo` / `done` / `n/a` / `lawyer` / `blocked`, a trigger table and plain rules.
- Every new or adopted project gets `.loop/legal-checklist.md` (20 rows, a data list, a third-party list, lawyer questions, owner decisions) and a project copy of the rules.
- Each feature track has a legal line; the quality-gates map has a "Legal rows" step; a feature is not delivered while a legal row it touches is `todo`.
- The release map starts with "Final legal audit" (check 20); the release track needs it done and the owner's OK on legal pages.
- `loop.md`: legal added to review, product rules, approval gates (publishing legal text, releasing with `lawyer` rows) and completion. Loop drafts and flags; it never claims legal compliance.
- Previous versions of changed files are kept in `archive/v0.4.2/`.

## 0.4.2 — ask, then build

- Loop asks the start questions itself (one message) and starts building the first map right away when name, platform and a feature are known. No separate approval step; it still stops at approval gates.
- New fill-in form `start/START.md`. `loop-init.mjs` reads a `START.md` in the target folder (or `--brief START.md`), says exactly which answers are missing, and keeps the answers in `docs/START.md`.
- Template page: put your basic page, screenshot, Figma export or folder in `template-page/` (or give its path). It moves to `design/template-page/`, and `AGENTS.md`, the atlas overview, tracks and brief tell every screen to follow it. `start/template-page/` is the empty folder to copy.
- `--start` hands over to the coding agent (`LOOP_AGENT`, default `codex`) with "Use Loop for this project. Build the next atlas map."

## 0.4.1 — platform choice

- Loop no longer assumes a web app. The platform is chosen at the start (web, android, ios, mobile, desktop, backend, cli, other, or several) in the opening question, the brief (`platforms`), the terminal menu or `--platform`.
- `starter/platforms.mjs` holds a profile per platform: common stacks, test commands, proof ladder, platform rules, version rule, text location, hotspots, release steps, open questions and `.gitignore` lines.
- New projects get `.loop/platform.md` and a `release` map + track for the chosen platform(s), built last.
- npm scripts only for JavaScript projects; others use `node docs/app-map/...` commands. The atlas check moved to `docs/app-map/atlas-contract.test.mjs` so it never mixes with the product's own tests.
- `--adopt` guesses the platform from the files and says so.
- Policy, skill and docs reworded for any platform (evidence: browser / emulator / simulator / staging / device). New Android example brief.
- The terminal questions now also work with piped answers.

## 0.4.0 — atlas-first

- New project starter `scripts/loop-init.mjs` and `starter/`: a project is born from its brief as an atlas plan (overview, roadmap, one map per feature, quality gates), with `AGENTS.md`, a single CURRENT RESUME `HANDOFF.md`, `.loop/workflow.md`, a track per feature, atlas contract tests and npm scripts. `--adopt` adds Loop to an existing project without overwriting anything.
- Atlas tools: `build-atlas.mjs` (validates maps, edges, drilldowns, statuses and real `file:line` sources), `atlas-status.mjs` (`--next`, `--json`), `verify-atlas.mjs` (optional Playwright check), and a generic interactive atlas template.
- `loop.md` rewritten as a short policy with the product rules learned on Lite: one feature = one map + track + test + doc; every language; gender-neutral content; version and cache bumps; measure before claiming; plans are not features; owner-approved pushes.
- New docs: `ATLAS-FIRST.md`, `OWNER-COMMUNICATION.md`, `SECURITY.md` (moved out of `loop.md`), `README.md`.
- `EFFICIENT-WORKFLOW.md` generalised; `DELIVERY-WORKFLOW.md` ties tracks to atlas maps.
- Codex router: `[LOOP_CLASSIFY]` slice so only the relevant part of a long prompt is classified.
- Previous versions of changed files are kept in `archive/v0.3.1/`.
