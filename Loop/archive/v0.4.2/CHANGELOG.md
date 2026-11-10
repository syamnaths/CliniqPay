# Changelog

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
