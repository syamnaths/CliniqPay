# Loop efficiency workflow

Purpose: reduce repeated context, investigation and rework while preserving correctness, approvals and evidence. This is a required companion to `loop.md`, `DELIVERY-WORKFLOW.md` and `MODEL-ROUTING.md`, not permission to skip their safety gates.

## Default task loop

1. Capture objective, relevant context, constraints and acceptance criteria. Infer clear details; ask only about material ambiguity. Separate requested work from optional improvements.
2. Read current instructions and the active handoff first; find relevant source/tests through targeted search and the existing map. Confirm baseline and preserve unrelated work.
3. Classify the bounded task once. Choose direct execution, deterministic tooling or one justified model dispatch. Reuse that decision until scope/capability changes.
4. For a bug, collect evidence and test one hypothesis. Add a regression test when practical, then implement the smallest fix. After three failed hypotheses, reassess rather than stack speculative changes.
5. Run fresh targeted checks after edits and the complete applicable release checks before publication. Inspect failures/stderr, review spec compliance and then quality/risk.
6. Update affected maps and the active handoff. Report result, evidence level, unresolved risks and the exact next action briefly. External publication still needs explicit approval.

## Context and continuity

- Use one coherent outcome per task. Recommend a fresh task at a natural boundary when old context obscures the current work; do not create one without the user's request. Preserve a compact resume packet first. Do not fork merely to reduce context: a fork retains history.
- Keep `HANDOFF.md` as the active `START` / `MID` / `NOW` snapshot. `NOW` holds current revision/version, approved objective, active files, decisions, fresh evidence, open risks and next action. Do not create a second competing current-state document.
- When shortening history, preserve original content in the append-only archive and index/corrections scheme from `loop.md`. Never discard unresolved risks, approvals, failures or recovery references. Do not read all archived history for routine tasks.
- Load required instruction files fully when activated. Context optimization applies to optional source/history, never to bypassing mandatory instructions. Within an unchanged task, reuse already-read instructions as permitted by the host.
- Retrieve source ranges, not entire large files. Use maps as navigation hints and verify current source. Limit tool output to relevant excerpts and failure summaries; never feed a full source file back merely because an assertion printed it.
- Keep required flow-atlas changes in the same implementation checkpoint. Regenerate machine-produced references; do not manually maintain duplicate diagrams.

## Routing economics and honesty

- Preserve an explicit user-selected model/reasoning setting. Use the least-cost capable route from the current local policy; never claim live availability or exact savings from a static model list.
- A recommendation or adapter result `PLANNED` means **not executed**. It is not a model switch and is not evidence of cost savings. An `--execute` dispatch needs a recorded successful child result and supervisor validation before it counts as routed work; the parent model remains unchanged.
- Direct work is appropriate when the current model meets requirements and another run would add no value. Record `executionMode: direct` separately from the adapter's route state; do not invent an adapter `SUCCESS` result. A plan-only call is optional once classification is already clear, not a ritual before every lookup.
- Use a self-contained `new` child when a compact packet suffices; fork only when retained history is necessary. Delegate before the parent does the same work. Never concurrently resume an active session. Use only the approved adapter for model-specific child runs, with bounded fallback and no recursive dispatch.
- If a different capability is necessary but dispatch is unavailable, use the existing human-switch checkpoint. Do not silently continue capability-sensitive work under an unsuitable route.
- Parallelize only independent work with distinct ownership and a clear benefit. No automatic fleet of agents for a one-file change. Count parent work, child work, retries and rework when evaluating savings.

## Deterministic automation first

- Reuse tested local commands for test selection, version checks, atlas generation, diff checks and release preparation. If a procedure repeatedly needs reconstruction, propose a small script with explicit inputs, bounded output and failure exit codes.
- A release-preparation command must not push, deploy, fetch, install dependencies, rewrite user files or use credentials as a hidden side effect. Keep preparation, local commit and externally approved publication separate.
- Do not create scripts or reorganize the app merely because this policy mentions them. Implement them as bounded follow-up tasks when requested and validate their failure paths.
- Prefer compact summaries plus task-local redacted logs on failure. Report nonzero exits, warnings, exclusions and missing prerequisites; do not label an incomplete suite as fully green.

## Quality that prevents repeat work

- Prefer tests of behavior over regexes tied to internal function signatures, arbitrary source text or release versions. Source contracts are appropriate for static invariants, not proof of timing, audio, rendering or lifecycle behavior.
- Use targeted tests during iteration, then fresh complete applicable checks for the checkpoint/release. Avoid repeating an unchanged full suite solely to produce another summary. Do not reuse stale evidence after relevant code changes.
- Classify known failures with reason, affected coverage, owner/next action and revision. Expected-error allowlists must be narrow and asserted; missing fixtures are limitations, not passing checks. New/untriaged failures block the checkpoint.
- Browser/layout and device audio/thermal claims require matching evidence. Browser use remains opt-in; if unavailable, report source/mock evidence and the exact user verification needed.
- For intermittent failures, prefer optional, bounded diagnostics: timestamps, stage transitions, synthesis duration, buffer waits, error counts. No secrets, narration payloads, persistent background polling or unrelated telemetry. Require separate scope before adding diagnostics.
- Split oversized modules incrementally when repeated cross-coupling/search costs justify it. Preserve public contracts and behavior with tests; no unapproved wholesale rewrite.

## Measurement and concise handoff

Record only material changes and available telemetry, not invented budgets or savings percentages:

```text
Checkpoint / objective / acceptance criteria
Source revision and relevant files
Execution: direct | dispatched | human-selected; recommendation vs actual evidence
Validation: command, result, evidence level, exclusions/warnings
Usage: input/cached/output/reasoning tokens and elapsed time if available; otherwise unavailable
Quality: retries, regressions, user corrections and open risks
Next action / required approval
```

Compare similar completed tasks before claiming a cost improvement. Shorter replies alone do not establish lower total usage. Account limits are not increased by workflow changes.

Installation boundary: a project-local policy edit affects that project copy. Updating the installed reusable plugin requires its source/reinstall workflow and appropriate authorization; never edit the plugin cache or global settings as a shortcut.
