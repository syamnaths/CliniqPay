---
name: loop
description: "Use when the user says 'Use Loop for this project', 'Apply Loop', 'Resume with Loop', or asks for Loop project orchestration. Handles greenfield discovery, existing-project activation, local-first context, bounded model routing, validation, recovery, and handoff continuity."
---

# Loop orchestration

Apply the authoritative policy in `loop.md`, the delivery lifecycle in `DELIVERY-WORKFLOW.md`, and the routing contracts in `MODEL-ROUTING.md` and `LOCAL-MODEL-ROUTING.md` from the plugin root.

## Invocation behavior

Read and apply `EFFICIENT-WORKFLOW.md` from the project-local Loop root when present, otherwise from the reusable instructions root. It defines the compact context, nonduplicative routing, deterministic automation and evidence-quality routine. Project policy may be newer than the installed plugin; do not edit the installed cache to synchronize it.

An explicit request to use or resume **Loop** selects this skill immediately. Treat Loop as this installed/local project workflow—not as an OpenAI product term. Do not invoke the OpenAI Docs skill, browse the web, or search product documentation to identify Loop when this skill or a local Loop installation is available. Resolve the target project and reusable-instructions roots from the current workspace and local files.

Loop is host-integrated. Do not ask the user to choose a task class. Read the user’s task, infer complexity and required capabilities, decompose a feature into bounded subtasks when needed, and route each subtask independently.

For a new idea or empty project with no stated product intent, do only enough read-only inspection to confirm the target and that it is empty, then ask one concise opening question covering what the client is building, who it is for, and the required first-release outcome. Before that answer, do not initialize Git, run a full environment preflight, install dependencies, select an architecture, create project maps, or write a detailed `HANDOFF.md`. After sufficient discovery, run the relevant engineering review, present options and risks, obtain the client’s decision at the approval checkpoint, and document the agreed project brief, architecture baseline, constraints, and next action before implementation. Never silently turn an engineering recommendation into a client decision.

Never invent an execution budget, deadline, team constraint, usage limit, or cost ceiling. Use values supplied or approved by the client. Any engineering estimate offered after discovery must be clearly labeled as an estimate with assumptions and must not be recorded as an approved constraint until the client accepts it.

For an existing project, use existing-project activation instead: inspect the target root, instructions, handoff, map, source, tests, Git or non-Git baseline, dependencies, and runtime health; reconcile documentation with actual code; load only the relevant context; preserve unrelated work; and route each bounded task after context inspection. Do not restart discovery unless the request introduces a new product decision or the existing intent is unclear.

Use a durable track for a meaningful feature, bug, migration, or review. Create a proportional spec and plan, obtain approval for material design choices, implement bounded tasks, perform spec-compliance review before quality/risk review, append review-fix tasks when needed, and require fresh verification evidence before completion. For bug fixes, reproduce and test one hypothesis at a time; after three failed attempts, stop and question the assumptions or architecture. Use branches/worktrees only when their isolation value exceeds their setup risk.

Use the local context index, project map, handoff, architecture documents, and actual source files before loading broad context. Keep local context primary and pass only the relevant bounded context to a model adapter.

If the current prompt contains `[LOOP_ROUTED_CHILD]`, this is already a model-routed bounded execution. Do not classify or dispatch it again. Complete only its supplied task, validate proportionately, and return the result to the supervising Loop session.

## Routing behavior

1. Inspect the target project and current runtime profile.
2. Classify the request internally.
3. Select the least-cost healthy model that meets context, tool, modality, quality, and safety requirements.
4. Prefer a verified local model for eligible offline, private, or bounded work.
5. When Codex CLI 0.148.0 or later is available, prefer the bundled internal adapter at `scripts/codex_model_router.py`. Pass the internally inferred task class and bounded task over stdin; use `fork` to preserve source-session context without competing with the active session, `resume` only after the source session has stopped, or `new` for an independent bounded task.
6. The adapter applies `--model` and `model_reasoning_effort` as per-run overrides and must not rewrite the engineer's global `config.toml`. It records only local routing metadata and a prompt hash, never the private prompt.
7. Validate the result and escalate through a bounded fallback when required.
8. If automatic switching is unavailable or every safe automatic route fails, enter the human-in-the-loop fallback: recommend the best currently selectable model and reasoning level, explain why, preserve a resumable routing checkpoint, and ask the engineer to change the model through the host model selector (for example `/model` in Codex).
9. After the engineer switches or chooses an alternative, re-check capability fit, resume the same bounded task from the checkpoint, validate the result, and record the selected route, fallback, validation result, and next action in the handoff.

If no adapter can dispatch or switch models, report automatic routing as unavailable—not all routing as failed—and activate the human fallback. Do not pretend that a recommendation or `/model` instruction changed the active model. Wait for host evidence or the engineer’s confirmation, and never ask the engineer to classify the task; Loop supplies the recommendation.

## Browser behavior

Playwright and screenshots remain opt-in under `loop.md`. Do not launch them merely because a browser project exists.

## Continuity

Preserve `START`, `MID`, `NOW`, checkpoints, corrections, local context, project maps, and resume identifiers according to the root Loop policy. The host skill is an orchestration layer, not a replacement for the project’s source, tests, or handoff records.

Natural-language intents such as “start this feature,” “implement the approved track,” “show status,” “review this track,” and “recover this checkpoint” activate the corresponding delivery protocol. Do not require command memorization. Destructive or history-changing recovery remains approval-gated.
