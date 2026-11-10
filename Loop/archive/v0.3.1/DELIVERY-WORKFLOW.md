# Loop Delivery Workflow

This document defines the durable specification, implementation, review, debugging, and recovery lifecycle used by the Loop plugin. It applies to new and existing projects and complements `loop.md` rather than replacing its safety, context, testing, routing, and handoff rules.

## Durable work tracks

Use [`EFFICIENT-WORKFLOW.md`](./EFFICIENT-WORKFLOW.md) throughout this lifecycle. A policy-only change can use one combined spec/plan/review record; do not create redundant artifacts. Automation mentioned in a plan is not delivered until implemented and tested.

Every feature, bug, migration, or meaningful review may use a track. Tiny one-step changes may remain a handoff checkpoint when a separate track would add no value.

```text
.loop/
├── project.md                 # product goals and user context
├── product-guidelines.md      # UX, writing, accessibility, and brand rules
├── workflow.md                # project-specific delivery and approval choices
├── tracks.md                  # active/completed track index
└── tracks/
    └── <track-id>/
        ├── spec.md            # problem, scope, behavior, constraints, acceptance criteria
        ├── plan.md            # phases, bounded tasks, files, validation, dependencies
        ├── metadata.json      # ID, type, state, owner, timestamps, checkpoint references
        └── review.md          # spec review, quality review, findings, fixes, verdict
```

Loop creates only the artifacts justified by project and task size. `HANDOFF.md` remains the active continuity surface; tracks preserve durable task-specific detail without making the handoff grow indefinitely.

Track states:

```text
PROPOSED -> SPECIFIED -> APPROVED -> ACTIVE -> REVIEW -> COMPLETE
                         |            |          |
                         v            v          v
                       DEFERRED     BLOCKED   FIXES_REQUIRED
                                                   |
                                                   v
                                                 REVIEW

Any validated checkpoint may become REVERTED through the recovery protocol.
```

## Track lifecycle

1. Understand the request and existing project context.
2. Create a concise specification with explicit acceptance criteria and exclusions.
3. Present material design decisions in readable sections and obtain approval.
4. Create a bounded implementation plan with dependencies, affected files, validation, and rollback considerations.
5. Route each bounded task independently under `MODEL-ROUTING.md`.
6. Implement with test-first behavior where appropriate and checkpoint after fresh validation.
7. Run spec-compliance review before code-quality/security review.
8. Add a `Review Fixes` phase for unresolved findings and re-review after fixes.
9. Synchronize track status, project context, handoff, and checkpoint history.
10. Claim completion only from fresh evidence that covers tests and acceptance criteria.

The user may express these intents naturally: start or plan a feature, implement the approved track, show status, review the active track, or recover/revert a checkpoint. Loop maps the intent internally; users do not need to memorize commands.

## Specification and plan gates

- Creative or behavior-changing work requires a design/specification proportionate to its impact before implementation.
- Ask one focused question at a time when discovery is needed; do not conduct a long generic interview.
- Present alternatives only when they are viable and materially different.
- Approval applies to the documented scope, not to unstated adjacent work.
- Plans identify exact affected surfaces, dependencies, risks, validation, and stopping conditions.
- Plan steps should be independently checkable and small enough to review without losing feature context.

## Systematic debugging

Bug work follows evidence before editing:

```text
reproduce and capture evidence
  -> trace the failure to its source
  -> compare with a working path or contract
  -> state one falsifiable hypothesis
  -> test the hypothesis with the smallest safe experiment
  -> add a failing regression test when practical
  -> implement one root-cause fix
  -> rerun the regression and relevant suite
```

Do not stack speculative fixes. After three failed materially different attempts, stop and review the architecture, assumptions, or reproduction evidence before trying again. Environmental or external failures must be documented with the investigation, handling, and monitoring required.

## Test-first implementation

For defects and stable behavioral requirements, prefer RED-GREEN-REFACTOR:

1. Add or identify the smallest test that expresses the required behavior.
2. Run it and confirm it fails for the expected reason.
3. Implement the smallest sufficient change.
4. Run the targeted test and confirm it passes.
5. Refactor without changing behavior.
6. Run the relevant broader checks.

Do not force test-first work when no safe deterministic test surface exists. Record the alternative evidence and residual risk. Playwright and screenshots remain opt-in under `loop.md`.

## Isolated implementation

Use a Git branch or worktree when the task is substantial, parallel, experimental, or likely to overlap active work. Before using one:

- Confirm Git availability and the current dirty state.
- Choose a task-specific branch/worktree path without moving or overwriting user changes.
- Run setup and a clean baseline test in the isolated workspace.
- Keep generated dependencies and secrets out of commits.

Do not force worktrees for tiny changes or environments where they increase risk. Merging, publishing, deleting a branch/worktree, or modifying remote state remains approval-gated.

## Two-stage review

Review in this order:

1. `SPEC_COMPLIANCE` — required behavior, acceptance criteria, scope, exclusions, and evidence.
2. `QUALITY_AND_RISK` — correctness, maintainability, security, privacy, performance, accessibility, operations, and tests.

Critical or high-severity findings block completion. Record medium and low findings with disposition. A model or sub-agent report is advisory evidence; the supervisor verifies the actual diff, files, and test output.

## Verification before completion

No success claim may rely only on confidence, an earlier run, static inspection, or another agent’s statement. Immediately before completion:

1. Identify the commands and evidence that prove the acceptance criteria.
2. Run the complete applicable checks freshly.
3. Read the result and exit status.
4. Reconcile the result against the specification and plan.
5. Report what passed, failed, was skipped, or remains unavailable.

Passing lint does not prove compilation, passing unit tests does not prove runtime behavior, and a passing retry is reported as flaky where the project policy requires it.

## Review fixes and recovery

When review finds a gap, append a `Review Fixes` phase to the active plan. Each finding receives severity, owner, fix task, validation, and final disposition. Reopen the track until blocking findings are resolved or explicitly deferred by the decision-maker.

Recovery operates on logical units—track, phase, task, or checkpoint—not vague time ranges. Before any revert:

- Resolve the exact commits and affected files with read-only inspection.
- Detect unrelated or overlapping changes.
- Explain what will be reversed and what will remain.
- Require approval for destructive or history-changing actions.
- Prefer a new inverse commit or another recoverable mechanism over reset.
- Update track, handoff, and checkpoint state after validation.

## Adaptive host interaction

Use native host dialogs or structured choices when the host supports them. Otherwise use concise plain text. Interaction style must not change the underlying decision, approval, or evidence requirements. Natural-language triggering is the default; slash commands are optional aliases supplied by a host, not a dependency of Loop.

## Workflow behavior validation

Changes to the Loop skill should be tested against representative pressure scenarios before release:

- A user asks to skip design and implement an ambiguous feature immediately.
- A simple-looking bug invites a speculative fix before reproduction.
- A model reports success without fresh test evidence.
- A complex feature contains simple subtasks that should not inherit the strongest route.
- A local model is available but lacks sufficient context or safety capability.
- A dirty worktree overlaps the requested change.
- Review finds a blocking spec gap after implementation.
- A user requests rollback while unrelated changes are present.

The expected behavior is documented in `tests/loop-skill-scenarios.md`. Plugin schema validation alone does not prove workflow compliance.
