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

## Automatic execution modes

| Mode | When | How |
|---|---|---|
| Caveman | Tiny, clear, low-risk edit with a deterministic check | One agent, minimal files, no branch, smallest check. |
| Focused | Small bounded change or bug | One agent, targeted source and tests. |
| Isolated | Feature, refactor, performance, persistence, localisation, broad visual work | Branch/worktree, checkpoint loop, two-stage review, atlas + handoff update. |
| Specialists | Two or more truly independent subtasks | Smallest number of short-lived helpers; one owner integrates. |
| High-risk gate | Publish, migration, auth/secrets, destructive recovery | Prepare and validate, then stop for owner approval. |

Escalate when scope grows; de-escalate only at a clean checkpoint.

## Shared hotspots (one owner at a time)

`docs/app-map/`, {{hotspots}}.

## Done means

- Map `delivered` with real `source` refs; `{{cmdAtlas}}` and `{{cmdCheck}}` pass.
- Behaviour tests added and passing (`{{projectTest}}`); proof level stated.
- All languages updated; {{versionRule}}
- Track checklist ticked; `FIX-QUEUE.md` and `HANDOFF.md` current.
- Owner shown the result ({{visualProof}}) with verified vs not verified stated.
