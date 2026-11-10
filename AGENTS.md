# CliniqPay — working agreement

This project uses **Loop** (atlas-first). These rules apply to every session, agent and contributor.

- **Platform:** Web application (desktop and tablet browsers) (chosen at the start; details in `.loop/platform.md`)
- **Stack:** Python, Django, Django templates, Tailwind CSS v4, PostgreSQL; Celery and Redis when background work is implemented

## Automatic pickup

At the start of a session, after context compaction or when resuming:

1. Read the `CURRENT RESUME` block at the top of `HANDOFF.md`. It is the active checkpoint; older entries are history.
2. Read `.loop/platform.md`, `Loop/loop.md`, `Loop/ATLAS-FIRST.md`, `Loop/OWNER-COMMUNICATION.md` and `Loop/EFFICIENT-WORKFLOW.md`. Load other Loop files only when relevant.
3. Run `npm run atlas:status`. It shows delivered / building / planned maps, the next map to build and any drift.
4. Verify the branch, working tree and relevant source before trusting recorded status.
5. Continue the recorded next action within the owner's authorisation, unless the newest request changes it. Do not restart finished work or ask the owner to repeat known requirements.
6. Before handing off, update the same `CURRENT RESUME` block. Do not create competing status files.

## Goal continuity

**Goal pauses belong to the owner.** Keep the goal active until it is complete. Never set it to paused unless the owner explicitly asks. Take necessary temporary rests (for example cooldowns, rate-limit waits or required recovery) without pausing the goal; record the reason and restart condition, then continue automatically when checks pass and the host permits. Continue other authorised work when safe. A rest never bypasses resource guards, approval gates or host limits. The owner may pause while riding or travelling and resume on arrival; do not infer a pause from absence or travel, and do not resume an owner-paused goal until the owner asks.

## Prioritise before starting work

Keep one active delivery map (the current big rock). Finish its supporting fixes, tests and docs before unrelated work. Dependencies come first; then the smallest valuable outcome and risk reduction. `meta.buildOrder` is the agreed order; the Eisenhower matrix is triage, not an automatic override. Record blockers and reasons for reordering. Before switching from a blocked active map, checkpoint its restart step in the track and handoff and return it to `planned` with `blockedBy` retained. Multiple building maps are invalid; priority never bypasses dependencies or release boundaries. See `Loop/ATLAS-FIRST.md` → Priorities and one active big rock.

## Build from the atlas

`docs/app-map/` is the shared picture of the product. Every feature addition, removal or behaviour change updates its map in the same change.

- Pick work with `npm run atlas:next`. Make the map exact before coding; set it to `building`.
- Build to the map. Add behaviour tests. Then add `source` references (`file:line`) and set the map to `delivered`.
- Run `npm run atlas` after every map change (it refuses broken edges and missing source) and `npm run atlas:check` before each commit. Run `npm run atlas:verify` for structural or visual atlas changes.
- Product tests: Django tests or pytest (configure when application exists). Prove each feature at the strongest level listed in `.loop/platform.md` and say which level you reached.
- Plans go to `planned` maps or `docs/app-map/FIX-QUEUE.md`, never into delivered maps.
- Each feature has a track in `.loop/tracks/<map-id>/spec.md`. Keep its checklist current.

## Talk to the owner

Simple, plain words and short lines. Lead with the result. Decision-ready work with no placeholders.

**Verification link rule:** After each run or delivered slice, always provide the exact live URL (e.g., http://127.0.0.1:8000/...) for the owner to inspect and verify before proceeding.

Give approve-style options (A recommended / B / C) only for decisions that change the result. Do routine work yourself. Show proof the owner can judge: phone-width and desktop screenshots in a real browser. Say what is verified and what is not.

## Professional design before delivery

**Design-system selection.** The owner's approved reference or existing product system takes precedence. Otherwise use [Material Design 3](https://m3.material.io/) as the default for web, Android and cross-platform interfaces, customised with the product's brand tokens. For native iOS/macOS use [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) and native components. Other native platforms follow their platform conventions. These defaults authorise an initial representative screen, not a silent redesign of an existing product. Record the chosen system and tokens in the project design notes; obtain the owner's decision before a major new visual commitment. A design system is not a package: reuse the existing stack and check current supported implementations before proposing any new dependency. Avoid mixing competing component styles; verify accessibility and visual quality in the actual implementation.

Every user-facing feature must look and behave like a coherent finished product. Follow the owner's reference and the existing design system; reuse established components. Without a reference, propose a concise direction suited to the audience and platform, show one representative screen, and obtain the owner's decision on a major new visual direction before spreading it across the product. Routine polish within the agreed direction needs no repeated approval.

- Establish consistent typography, spacing, alignment, colour, iconography and component states. Use clear information hierarchy, readable content widths and restrained decoration; avoid generic ornament that distracts from the task.
- Design the full experience: loading, empty, success, error, validation, disabled and permission states where applicable. Use real approved content; do not ship placeholder copy, broken assets or dead controls.
- Adapt to the platform and relevant screen sizes, including long translated text. Check keyboard navigation, visible focus, labels, contrast, touch targets and reduced-motion preferences where relevant.
- Before delivery, inspect the rendered feature at representative sizes and exercise the key interactions. Correct clipping, overflow, inconsistent spacing and unclear actions; show the owner representative screenshots with any remaining limits. Source inspection alone is not visual proof. If rendering tools are unavailable, record visual review as blocked rather than claiming polish is verified.

## Product rules

- All user-facing text in every supported language at once (en) in locale files (for example `locales/<lang>.json`), with placeholder checks in tests. Gender-neutral wording.
- Bump `?v=` pins, the service-worker cache name and pinned tests together when a served file changes.
- Works at phone width without horizontal scroll; keyboard and screen-reader basics.
- Offline and slow-network behaviour stated when the app is a PWA.
- No raw developer text for users; calm translated messages, quiet technical logs.
- Measure before claiming sizes, speed or savings. Device feel and sound need a device check.
- Consent, privacy and safety first for sensitive features; never store private choices.

## Tests and security before delivery

Follow TDD for testable behavior: confirm a meaningful failing test before implementation, then GREEN and refactor. Reuse existing coverage; add unit tests for changed logic and integration tests for changed component boundaries, with failure paths where applicable. Record skipped or blocked levels honestly (details in Loop/DELIVERY-WORKFLOW.md). Before marking a feature delivered, perform the focused security review in Loop/SECURITY.md, list evidenced vulnerabilities and discuss them with the owner before remediation. Fix agreed findings, rerun tests and re-review. No findings means report limits and continue; no empty approval gate.

## Legal checklist

`.loop/legal-checklist.md` holds the 20 legal checks (rules in `Loop/LEGAL-CHECKLIST.md`). When a map collects personal data, adds cookies or trackers, a third-party API, a package, assets, AI content, payments, advice or marketing text, update those rows in the same change. The release needs check 20 (final legal audit) done. Loop drafts legal pages and flags lawyer items; the owner approves legal text before it is published. Never claim the product is legally compliant.

## Release boundary

Commit validated checkpoints locally. The owner approves every push to production, every deploy, every store release (see the `release` map) and every published legal page. If the agent cannot push, give one copy-paste command and confirm the remote afterwards.
