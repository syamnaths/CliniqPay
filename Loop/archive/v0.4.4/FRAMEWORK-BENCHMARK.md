# Loop Framework Benchmark

Reviewed against primary project materials on 2026-08-20:

- [Superpowers](https://github.com/obra/superpowers)
- [Gemini CLI Conductor](https://github.com/gemini-cli-extensions/conductor)
- [Google’s Conductor introduction](https://developers.googleblog.com/en/conductor-introducing-context-driven-development-for-gemini-cli/)

## Capabilities adopted or strengthened

| Capability | Superpowers | Conductor | Loop 0.2 |
| --- | --- | --- | --- |
| Collaborative discovery before code | Strong | Spec/setup driven | Client-and-engineering discovery with proportional approval gate |
| Durable specification and plan | Design and detailed plans | Per-track spec/plan/metadata | Proportional `.loop/tracks/` artifacts linked to handoff checkpoints |
| Existing-project activation | Supported | Explicit brownfield setup | Baseline, targeted mapping, doc/source reconciliation, change preservation |
| Systematic debugging | Explicit root-cause workflow | Review/correction flow | Reproduce, hypothesis, minimal experiment, regression, three-failure architecture stop |
| Test-first work | Mandatory TDD methodology | Workflow configurable | Test-first for stable behavior/defects, with documented exceptions and evidence |
| Isolated implementation | Git worktrees | Git-aware tracks/revert | Risk-proportional branch/worktree isolation with overlap safeguards |
| Review | Spec and code-quality stages | Track review | Ordered spec-compliance then quality/risk review with blocking severities |
| Completion evidence | Explicit fresh-verification gate | Plan/status synchronization | Fresh evidence gate tied to acceptance criteria and evidence levels |
| Corrections and recovery | Branch finishing/review | Logical track/phase/task revert | Review-fix phase plus approval-gated logical-unit recovery |
| Natural-language activation | Skill triggered | Natural-language and commands | Host-integrated natural-language intents; commands optional |
| Workflow behavior tests | Skill pressure/eval scenarios | Repository workflows | Scenario acceptance suite defined; execution harness still required |

## Loop-specific scope

Loop additionally defines local-first context routing, handoff compaction and archives, project graph tiers, provider-neutral per-task model routing, offline llamafile eligibility, protocol/security standards, evidence classifications, dynamic project activation, and explicit source-versus-deployment boundaries.

## Remaining operational gaps

- Model routing is a validated contract but still requires a host/API/local adapter for dispatch and automatic fallback.
- Workflow behavior scenarios are specified but have not yet been executed through a dedicated eval harness.
- This local plugin is valid but is not automatically installed or published through a marketplace by the repository alone.
- Host-native dialogs, hooks, commands, and session-start activation depend on capabilities exposed by the installing host.

Do not claim Loop is categorically better from feature coverage alone. Compare representative project outcomes: requirement accuracy, task success, defects, review findings, rework, context/tokens, latency, cost, recovery quality, and user corrections.

## Review 2026-10-08 (Loop 0.4.4)

Four popular agent plugins were checked against Loop. Only ideas Loop did not already have were added.

| Source | Already in Loop | Added in 0.4.4 | Not adopted, and why |
| --- | --- | --- | --- |
| [Superpowers](https://skills.sh/obra/superpowers) | Discovery before code, plans, test-first, root-cause debugging, worktrees, two-stage review, fresh verification before claims, parallel agents for independent work | Receiving review: check each comment before applying it (`DELIVERY-WORKFLOW.md`) | One-question-at-a-time brainstorming: Loop asks all start questions in one message on purpose |
| Karpathy guidelines ([summary](https://pasqualepillitteri.it/en/news/1872/karpathy-claude-md-trending-github-llm-coding)) | Ask when unclear, smallest coherent change, preserve unrelated work | Craft rules: say your assumption, simplest thing that works, surgical edits, done means a check passes (`loop.md` §3) | — |
| i-have-adhd ([summary](https://chudi.dev/blog/claude-adhd-plugin)) | Result first, plain words, no padding, honest errors | Focus-friendly replies: answer first, one topic, status line, numbered steps with minutes, lists of five or fewer, show the win, one next step (`OWNER-COMMUNICATION.md`) | — |
| Claude Octopus ([docs](https://www.mintlify.com/nyldn/claude-octopus)) | Phase gates (spec → plan → build → review), evidence gates, model routing | Second opinion for high-risk changes: fresh independent reviewer with one lens, disagreements to the owner (`DELIVERY-WORKFLOW.md`) | Three models on every task (about 3x cost); numeric "quality scores" (Loop reports evidence levels, not invented percentages); dozens of fixed personas |

