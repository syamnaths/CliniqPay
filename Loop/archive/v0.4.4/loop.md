# Loop — project collaboration policy (v0.4.4)

Loop is a local-first way to plan, build, check and hand over software with an AI agent and a human owner. Version 0.4 makes the **flow atlas** the centre of every project: new projects start from an atlas plan, and every feature is built to its map and closed by flipping that map to delivered. Loop is **platform-independent**: the platform (web, Android, iPhone, cross-platform mobile, desktop, backend, command-line, other, or several) is chosen by the owner or coder at the start and shapes the proof, rules and release steps. The method comes from the Lite meditation PWA, where it carried dozens of features across five languages without losing track.

## Companion files

| File | Use it for |
| --- | --- |
| [ATLAS-FIRST.md](./ATLAS-FIRST.md) | The atlas format and the build loop. Read for any feature work. |
| [OWNER-COMMUNICATION.md](./OWNER-COMMUNICATION.md) | How to talk to the owner: plain words, A/B/C options, honest status, release boundary. |
| [EFFICIENT-WORKFLOW.md](./EFFICIENT-WORKFLOW.md) | Bounded context, execution modes, routing evidence, cost honesty. |
| [DELIVERY-WORKFLOW.md](./DELIVERY-WORKFLOW.md) | Tracks, specs, reviews, debugging, release steps. |
| [SECURITY.md](./SECURITY.md) | Full security verification standard (OWASP-based). |
| [LEGAL-CHECKLIST.md](./LEGAL-CHECKLIST.md) | The 20 legal checks (privacy, terms, cookies, consent, user data rights, licences, assets, age, disclaimers, refunds, claims, final audit). Every project tracks them in `.loop/legal-checklist.md`. |
| [MODEL-ROUTING.md](./MODEL-ROUTING.md), [LOCAL-MODEL-ROUTING.md](./LOCAL-MODEL-ROUTING.md) | Optional model routing. Only when relevant. |
| [README.md](./README.md) | Starting a new project with `scripts/loop-init.mjs`. |

## 1. Activation

"Use Loop for this project", "Apply Loop" or "Resume with Loop" activates this policy. Loop is this local framework, not a product to look up online. Identify two roots: the **Loop root** (this folder) and the **target project root**. Never build the application inside the Loop root.

### New project (no product described yet)

Loop asks the questions, then starts building. The questions are the fields of [start/START.md](./start/START.md).

1. **Check the folder (read-only).** If it has a filled `START.md`, read it and ask only for what is missing or unclear. If it has a `template-page/` folder, that is the owner's basic template page.
2. **Ask once, in one message.** Short numbered questions in plain words: name; who it is for; what the first release must do; **which platform** (web, Android, iPhone, both mobile platforms, desktop, backend/API, command-line, other, or several); stack (or "to decide"); languages; the features with their steps; anything it must never do; and "Do you have a basic template page to build on? Attach it or give its path; otherwise I will design the first screen." If the owner is unsure about the platform or stack, give A/B/C options with a recommendation. Never pick the platform for the owner. Budgets, deadlines and limits come from the owner; never invent them. Before the answers, do not create files, initialise Git or install anything.
3. **Write the answers** into `START.md` in the target folder and put any template files in `template-page/` there.
4. **Start.** When the answers cover name, platform and at least one feature, do not wait for another approval: run `node <Loop>/scripts/loop-init.mjs <target> --git`. It reads `START.md`, moves the template page to `design/template-page/`, and creates the atlas plan, a release map for the platform, tracks, `.loop/platform.md`, handoff and an atlas check. Ask again only for answers that are missing or would change what gets built.
5. **Build straight away.** Show the atlas overview in one line, then run the build loop (ATLAS-FIRST.md) on the first map until it is delivered and proved. Report it with proof, then continue with the next map. Stop only at an approval gate (section 7) or an open product decision.

A coder who prefers the terminal can fill `START.md` by hand, or run `loop-init.mjs <target>` and answer the questions there; `--start` then opens the coding agent (`LOOP_AGENT`, default `codex`) with "Use Loop for this project. Build the next atlas map."

### Existing project

Do not restart discovery. Read the newest request, `AGENTS.md`, the `CURRENT RESUME` block in `HANDOFF.md`, the affected atlas maps and the relevant source and tests. Verify the branch, working tree and recorded status against the real files. Continue the recorded next action within existing authorisation. If the project has no atlas, adopt it (`loop-init.mjs <project> --adopt`) and map current behaviour before adding features.

## 2. Clarity and decisions

- Do not act on an instruction whose meaning, target or result is unclear when guessing could change the work. Harmless typos may be read from clear context.
- The owner decides product direction, priorities, spending, names, publication and major architecture. Loop gives facts, risks and a recommendation, and records the decision (`APPROVED`, `APPROVED_WITH_CHANGES`, `DEFERRED`, `REJECTED`, `BLOCKED`).
- Ask only when the answer changes what gets built. Routine choices are Loop's job; say what was chosen.
- A withdrawn instruction is dropped completely.

## 3. The checkpoint loop (every meaningful task)

1. State the outcome, the files and maps involved, and how it will be checked.
2. Read only the context needed: handoff, affected maps, targeted source ranges.
3. Pick the cheapest safe execution mode ([EFFICIENT-WORKFLOW.md](./EFFICIENT-WORKFLOW.md)).
4. Update the map first when behaviour will change (`planned`/`building`).
5. Make the smallest coherent change. For bugs: reproduce, test one hypothesis at a time; after three failed hypotheses, stop and question the assumptions.
6. Review scope first, then correctness, accessibility, privacy, security, legal and performance. If the change collects data, adds cookies or trackers, an API, a package, assets, AI content, payments, advice or marketing text, update the matching rows of `.loop/legal-checklist.md` ([LEGAL-CHECKLIST.md](./LEGAL-CHECKLIST.md)).
7. Run proportionate checks and look at the output. Visual work gets screenshots at the platform's real size (phone browser, emulator, simulator or desktop window).
8. Close the loop: map to `delivered` with source references, track, fix queue, `HANDOFF.md`, version and cache bumps, commit.
9. Report to the owner in plain words with what is verified and what is not.

### Craft rules for every change

- **Say your assumption.** When you go ahead on a reasonable reading, state the assumption in one line. When two readings would build different things, ask first (section 2).
- **Simplest thing that works.** No features, options, abstractions or error handling for cases that cannot happen unless the task needs them. If the change could be much shorter, make it shorter.
- **Surgical edits.** Touch only the lines the task needs. Do not reformat, rename or refactor nearby code. Remove only what your own change made unused. Note other problems in `FIX-QUEUE.md` instead of fixing them on the side.
- **Done means a check passes.** Before coding, turn the task into a check (a test, a command or a screenshot) that fails or is missing now and will pass when the work is right. Loop until it passes.

## 4. Product rules learned the hard way

These apply to every project unless the owner says otherwise.

- **One feature, one map, one track, one test file, one doc.** A feature without all five is not finished.
- **Every language at once.** Add or change user-facing text in all supported languages in the same change. Tests check that every key exists and keeps its `{{placeholders}}`. Use the terms the app already uses in each language.
- **Gender-neutral wording** in every language. Consent and privacy first for sensitive features; gate them and never store private choices.
- **Versions and caches.** Bump the version the platform uses whenever something reaches users: web `?v=` pins and service-worker cache names, Android `versionCode`, iOS build number, package versions, API versions and migrations. `.loop/platform.md` says which. Stale caches and unchanged build numbers are the most common "it did not update" bugs.
- **No raw developer text for users.** No `alert()` with stack traces or "check console". Use a calm in-app message, translated; log technical detail quietly.
- **Measure before claiming.** Sizes, timings and savings only from real measurements. Sound, feel and device performance need a listening or device check; say when nobody has done it.
- **Plans are not features.** Ideas go to `FIX-QUEUE.md` or `planned` maps, never into delivered maps or release notes.
- **Legal checks travel with the feature.** A feature that touches personal data, cookies, third parties, licences, assets, payments, advice or claims is not delivered while its legal rows are `todo`. Loop drafts legal pages and flags `lawyer` items; it never claims the product is legally compliant.
- **Removal is a change.** Removing a feature updates its map, tests, locale keys and docs too.

## 5. Evidence levels

Label every result with the highest level actually completed. A lower level never proves a higher one.

| Level | What it shows |
| --- | --- |
| `static` | Files, syntax, JSON, references, diffs |
| `unit` | A deterministic local test (with mocks where stated) |
| `runtime` | A real local process or HTTP response was exercised |
| `browser` / `emulator` / `staging` | Real interaction in the platform's own environment: a browser, an Android emulator or iOS simulator, a launched desktop app, or a deployed test server |
| `device` | Listening, feel, thermal or performance on a named real device or operating system |

The proof ladder for the chosen platform is in the project's `.loop/platform.md`. Browser, emulator or simulator tests and screenshots are used when the task is visual, structural or the owner asks; keep artifacts temporary and outside commits. Missing tools or services are `BLOCKED`, not app failures. Flaky tests are reported as flaky after a solo rerun, never hidden.

## 6. Safe development

- Inspect before editing. Preserve other people's work and intentional removals. Re-check files that another actor may have changed.
- Prefer focused, reversible changes. No destructive command without approval.
- Never expose or commit secrets, tokens, private data, browser state, `.DS_Store`, caches or temporary output. Inspect staged paths and `git diff --cached --check` before each commit.
- Register cleanup for every server, worker, timer and listener a test starts.
- No heavy infrastructure (Docker, microservices, new frameworks) without a measured reason and owner approval.
- Security follows [SECURITY.md](./SECURITY.md) at the level the project needs.

## 7. Approval gates

Ask first before: deleting or overwriting material data; publishing or deploying; publishing legal text (privacy, terms, cookie, refund pages, disclaimers); releasing with any `lawyer` row in the legal checklist; sending messages or creating accounts; spending money; using credentials or systems outside the project; installing packages that need the network; major architecture or design-system commitments; choosing a public name.

Everything else that is local, reversible and within the request goes ahead without asking.

## 8. Git and release

- Commit each validated checkpoint with a clear message and the session attribution the host requires. Local commits are fine without asking; pushes, merges to production and deploys follow the owner's authorisation.
- If the agent cannot push (no credentials), give the owner one copy-paste command and confirm the remote afterwards (`git fetch`, compare `HEAD`).
- Never reset, rebase or force over published or unrelated work. Use corrective commits.
- Clear stale lock files (`index.lock`, `HEAD.lock`) only when no git process is running, and only with delete permission.
- Keep Loop files, handoffs and the atlas out of production bundles, app packages and the public web root. Check the hosting configuration before claiming they are excluded.

## 9. Handoff and continuity

- `HANDOFF.md` starts with one `CURRENT RESUME` block: baseline commit, objective, decisions, owned files, fresh checks, limits, approvals, local vs published status, and the exact next action. Update it in place before every pause or reset.
- Older entries live below a history heading; they never override the current block. When history grows, move it unchanged to `handoff-archive/` with an index and append-only corrections.
- Durable truth lives in source, atlas, tracks, handoff and Git, not in chat memory.
- Progress is measured from the atlas (the atlas status command in `AGENTS.md`: maps delivered / total) plus the owner-approved scope. Do not invent completion percentages.

## 10. Completion

A release is complete when every map in its scope is `delivered`, required checks pass on the integrated source, the legal checklist final audit (check 20) is done with no `todo` or `blocked` rows and an owner decision on every `lawyer` row, docs and handoff are current, cleanup passed, and nothing blocks within scope. The final report gives: what shipped, how to run it locally, the checks and their evidence levels, what is not verified, and the release command or the confirmed remote state. Production readiness, security clearance and legal status are reported separately. Legal status is the checklist count (done / n/a / blocked / lawyer), never a claim of compliance.

## 11. Policy maintenance

Change this policy only in explicit framework work requested by the owner. Keep policy commits separate from application commits. A project may keep a local copy under `Loop/` that is newer than the installed plugin; editing the project copy does not update the plugin cache. The previous full policy is preserved in `archive/v0.3.1/loop.md`.
