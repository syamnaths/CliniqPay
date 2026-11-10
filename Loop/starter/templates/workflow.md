# {{name}} — delivery workflow

Status: default for all work in this project. Platform: {{platform}} (`.loop/platform.md`). Policy: `Loop/loop.md`; method: `Loop/ATLAS-FIRST.md`.

## Delivery path

```text
next planned map ({{cmdNext}})
  -> make the map exact, status: building
  -> compact task packet (objective, files, map, acceptance checks)
  -> branch or worktree when the change is substantial or risky
  -> build to the map with behaviour tests ({{projectTest}})
  -> prove it at the strongest level in .loop/platform.md
  -> scope review, then quality / risk review
  -> map delivered with source refs, track + fix queue + handoff updated
  -> validated checkpoint commit
  -> owner-approved push / release (release map)
```

## Goal continuity

**Goal pauses belong to the owner.** Keep the goal active until it is complete. Never set it to paused unless the owner explicitly asks. Take necessary temporary rests (for example cooldowns, rate-limit waits or required recovery) without pausing the goal; record the reason and restart condition, then continue automatically when checks pass and the host permits. Continue other authorised work when safe. A rest never bypasses resource guards, approval gates or host limits. The owner may pause while riding or travelling and resume on arrival; do not infer a pause from absence or travel, and do not resume an owner-paused goal until the owner asks.

## Prioritise before starting work

Keep one active delivery map (the current big rock). Finish its supporting fixes, tests and docs before unrelated work. Dependencies come first; then the smallest valuable outcome and risk reduction. `meta.buildOrder` is the agreed order; the Eisenhower matrix is triage, not an automatic override. Record blockers and reasons for reordering. Before switching from a blocked active map, checkpoint its restart step in the track and handoff and return it to `planned` with `blockedBy` retained. Multiple building maps are invalid; priority never bypasses dependencies or release boundaries. See `Loop/ATLAS-FIRST.md` → Priorities and one active big rock.

## Automatic execution modes

| Mode | When | How |
|---|---|---|
| Caveman | Tiny, clear, low-risk edit with a deterministic check | One agent, minimal files, no branch, smallest check. |
| Focused | Small bounded change or bug | One agent, targeted source and tests. |
| Isolated | Feature, refactor, performance, persistence, localisation, broad visual work | Branch/worktree, checkpoint loop, two-stage review, atlas + handoff update. |
| Specialists | Two or more truly independent subtasks | Smallest number of short-lived helpers; one owner integrates. |
| High-risk gate | Publish, migration, auth/secrets, destructive recovery | Prepare and validate, then stop for owner approval. |

Escalate when scope grows; de-escalate only at a clean checkpoint.

## Tests and security before delivery

Follow TDD for testable behavior: confirm a meaningful failing test before implementation, then GREEN and refactor. Reuse existing coverage; add unit tests for changed logic and integration tests for changed component boundaries, with failure paths where applicable. Record skipped or blocked levels honestly (details in Loop/DELIVERY-WORKFLOW.md). Before marking a feature delivered, perform the focused security review in Loop/SECURITY.md, list evidenced vulnerabilities and discuss them with the owner before remediation. Fix agreed findings, rerun tests and re-review. No findings means report limits and continue; no empty approval gate.

## Shared hotspots (one owner at a time)

`docs/app-map/`, {{hotspots}}.

## Done means

- Map `delivered` with real `source` refs; `{{cmdAtlas}}` and `{{cmdCheck}}` pass.
- Behaviour tests added and passing (`{{projectTest}}`); proof level stated.
- All languages updated; {{versionRule}}
- Legal rows touched by the change updated in `.loop/legal-checklist.md` (none left `todo`).
- Track checklist ticked; `FIX-QUEUE.md` and `HANDOFF.md` current.
- Owner shown the result ({{visualProof}}) with verified vs not verified stated.
