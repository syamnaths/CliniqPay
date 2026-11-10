# {{name}} — working agreement

This project uses **Loop** (atlas-first). These rules apply to every session, agent and contributor.

- **Platform:** {{platform}} (chosen at the start; details in `.loop/platform.md`)
- **Stack:** {{stack}}

## Automatic pickup

At the start of a session, after context compaction or when resuming:

1. Read the `CURRENT RESUME` block at the top of `HANDOFF.md`. It is the active checkpoint; older entries are history.
2. Read `.loop/platform.md`, `Loop/loop.md`, `Loop/ATLAS-FIRST.md`, `Loop/OWNER-COMMUNICATION.md` and `Loop/EFFICIENT-WORKFLOW.md`. Load other Loop files only when relevant.
3. Run `{{cmdStatus}}`. It shows delivered / building / planned maps, the next map to build and any drift.
4. Verify the branch, working tree and relevant source before trusting recorded status.
5. Continue the recorded next action within the owner's authorisation, unless the newest request changes it. Do not restart finished work or ask the owner to repeat known requirements.
6. Before handing off, update the same `CURRENT RESUME` block. Do not create competing status files.

## Build from the atlas

`docs/app-map/` is the shared picture of the product. Every feature addition, removal or behaviour change updates its map in the same change.

- Pick work with `{{cmdNext}}`. Make the map exact before coding; set it to `building`.
- Build to the map. Add behaviour tests. Then add `source` references (`file:line`) and set the map to `delivered`.
- Run `{{cmdAtlas}}` after every map change (it refuses broken edges and missing source) and `{{cmdCheck}}` before each commit. Run `{{cmdVerify}}` for structural or visual atlas changes.
- Product tests: `{{projectTest}}`. Prove each feature at the strongest level listed in `.loop/platform.md` and say which level you reached.
- Plans go to `planned` maps or `docs/app-map/FIX-QUEUE.md`, never into delivered maps.
- Each feature has a track in `.loop/tracks/<map-id>/spec.md`. Keep its checklist current.

{{templateRule}}## Talk to the owner

{{ownerStyle}}

Give approve-style options (A recommended / B / C) only for decisions that change the result. Do routine work yourself. Show proof the owner can judge: {{visualProof}}. Say what is verified and what is not.

## Product rules

- All user-facing text in every supported language at once ({{languages}}) in {{textHome}}, with placeholder checks in tests. Gender-neutral wording.
- {{versionRule}}
{{platformRules}}
- No raw developer text for users; calm translated messages, quiet technical logs.
- Measure before claiming sizes, speed or savings. Device feel and sound need a device check.
- Consent, privacy and safety first for sensitive features; never store private choices.

## Release boundary

Commit validated checkpoints locally. The owner approves every push to production, every deploy and every store release (see the `release` map). If the agent cannot push, give one copy-paste command and confirm the remote afterwards.
