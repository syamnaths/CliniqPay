# Codex Model Routing Policy

This document defines the model-router architecture for Loop-based work. The router analyzes each bounded task request, selects the least-cost model that can satisfy its requirements, dispatches the request, validates the result, and applies a bounded fallback when necessary. It is provider-neutral: a remote model gateway, an OpenAI-compatible client, a local llamafile runtime, or another model adapter may implement the dispatch boundary.

For local or offline execution, apply [`LOCAL-MODEL-ROUTING.md`](./LOCAL-MODEL-ROUTING.md). A local model is selected only when its verified capabilities fit the bounded task and the local-first safety rules remain satisfied.

## Boundary

The routing layer may classify a task, select a compatible model, check current availability and usage signals, record the decision, and launch or resume a separate Codex session with the selected model when the environment supports it.

The routing unit is the smallest meaningful bounded task, not the entire feature. A complex feature may be decomposed into simple, standard, reasoning, browser, and high-risk subtasks, each routed independently. If a new session is required, preserve the project root, task scope, approvals, and handoff context. A user-selected model or explicit model request takes precedence over automatic routing.

The router cannot silently replace the model inside the currently executing Codex turn. Loop therefore includes an internal launch adapter, `scripts/codex_model_router.py`, that starts a model-specific bounded child with `codex exec`, `codex exec fork`, or `codex exec resume`. The supervising turn remains on its original model and integrates the child result. Automatic routing is proven only when the adapter returns a successful child result and the local decision record names the actual selected model.

Human-in-the-loop selection is the required final fallback when automatic switching is unsupported or exhausted. Loop performs the analysis and recommendation; the engineer performs only the host-controlled model change. This preserves useful routing even when the host does not expose a programmable model-switch adapter.

## Routing objectives

Apply [`EFFICIENT-WORKFLOW.md`](./EFFICIENT-WORKFLOW.md) for dispatch economics and reporting. `PLANNED` is not execution. When the current model is capable and child overhead adds no value, direct execution is valid; classify once and do not rerun the advisory adapter for every small tool call. Preserve human fallback when a necessary capability is unavailable. Prefer a bounded new child over copying unrelated history; use fork when history is actually required. This companion does not change adapter result schemas or override explicit model choices.

Choose the least expensive and lowest-latency model that can reliably satisfy the task. Escalate when reasoning, context, tools, safety, or validation requirements exceed the selected model’s capability.

Do not hard-code a model name as a permanent default. Model names, availability, context windows, capabilities, pricing, and deprecation status can change. Use stable capability classes and refresh the model registry from the available official catalog or provider integration.

## Task classes

```text
simple                deterministic calculation, formatting, extraction, classification
focused               short explanation, small documentation edit, isolated code change
standard              normal implementation, debugging, tests, or project analysis
reasoning             algorithm design, multi-file refactor, architecture, complex diagnosis
high-risk             security, privacy, migration, concurrency, production, or recovery work
large-context         repository mapping, broad review, or work near context limits
browser               browser, Playwright, responsive, accessibility, or visual behavior
local-offline         bounded work using a verified local model/runtime without network access
```

## Per-request routing lifecycle

```text
feature request
  -> decompose into bounded tasks
  -> load only relevant local context
  -> classify complexity and required capabilities
  -> inspect local and remote model candidates
  -> select least-cost capable healthy model
  -> dispatch one request/session through a model adapter
  -> validate output and required evidence
  -> accept, bounded-fallback, or BLOCKED
  -> record route, result, and resource signals
```

The feature name must not force every subtask onto the strongest model. For example, architecture planning may use a reasoning model, routine file discovery may use a cost-sensitive model, and security review may require the strongest compatible route. The supervisor remains responsible for integration and final validation.

## Capability requirements

Each routing decision should derive these requirements before choosing a model:

```text
reasoning: none | low | medium | high | xhigh | max
contextRequired: estimated input and retained context size
maxOutputRequired: expected response/output size
tools: shell | patch | browser | web | file | MCP | other
modalities: text | image | audio | other
latencyTarget: low | normal | flexible
qualityTarget: normal | high | critical
```

## Default routing policy

```text
simple       -> small/fast model, no or low reasoning
focused      -> small or balanced model, low reasoning
standard     -> balanced coding model, low or medium reasoning
reasoning    -> stronger coding/reasoning model, medium/high reasoning
high-risk    -> strongest compatible model, high reasoning and explicit review
large-context-> model whose context window safely fits the task, then choose quality/cost
browser      -> model with required tool and modality support; use Playwright for browser evidence
local-offline-> verified local model when context, tools, safety, and quality requirements fit
```

Use the current provider catalog to fill the classes. The policy should use capability classes rather than assuming older model names remain available.

## Candidate selection and cost optimization

The router evaluates local candidates first when the local-first policy permits them, then remote candidates when local capability, health, context, latency, or quality is insufficient. “Cost” includes provider cost, latency, local CPU/RAM/battery cost, context expansion, retries, and expected rework—not only token price.

Select the lowest-cost candidate that passes every hard requirement. Do not choose a cheaper model when it lacks a required tool, context window, modality, safety level, or quality threshold. Do not choose a stronger model merely because the parent feature is complex.

## Model registry

The router should maintain or obtain a current registry with:

```text
modelId
status: available | unavailable | deprecated | unknown
reasoningLevels
contextWindow
maxOutputTokens
tools
modalities
latencyClass
costClass
provider
catalogCheckedAt
```

For API-backed integrations, query the provider’s model catalog when permitted. The OpenAI Models API lists currently available model objects; model documentation supplies capability and context details.

## Model adapter boundary

The router must depend on an adapter, not on one provider or one gateway:

```text
ModelAdapter
  listCandidates() -> capability and availability records
  checkHealth(candidate) -> current health and limits
  dispatch(candidate, task, context) -> response and usage
  resumeOrLaunch(candidate, handoff) -> session reference when supported
```

A gateway such as OpenRouter may implement the remote adapter and route among remote providers. A llamafile process implements the local adapter. The Loop router still owns task classification, local-first preference, safety requirements, fallback limits, validation, and decision records; the adapter only supplies model access and provider-specific telemetry.

## Bundled Codex launch adapter

Loop ships a dependency-free internal adapter at `scripts/codex_model_router.py` and its capability mapping at `config/model-routing.json`. The user does not manually choose a task class or run this script. The workspace default is `--task-class auto`: the adapter reads the bounded task prompt, infers the smallest capable task class, and then applies the configured model and reasoning effort. A supervising Loop session may still pass an explicit task class when it has already decomposed and classified a bounded task.

The adapter uses the Codex CLI's per-run configuration surface:

```text
codex exec --model <model> -c model_reasoning_effort="<effort>"
codex exec fork --model <model> -c model_reasoning_effort="<effort>" <session>
codex exec resume --model <model> -c model_reasoning_effort="<effort>" <session>
```

- Use `--task-class auto` unless the supervising workflow has an explicit, evidence-backed class for the bounded task.
- Prefer `fork` for automatic task delegation from an active supervisor session. It preserves source context while preventing two processes from mutating the same active session.
- Use `resume` only after the source interactive session has stopped or when the host guarantees exclusive session ownership.
- Use `new` for a self-contained task whose bounded local context packet is sufficient.
- Send the task over stdin so private prompt content is absent from process arguments.
- Prefix child work with `[LOOP_ROUTED_CHILD]` to prevent recursive routing.
- Keep the global `~/.codex/config.toml` unchanged. Per-run `--model` and `-c` values override its defaults only for the child invocation.
- Store compact decisions under `<target>/.codex/loop-routing/`. Records contain a prompt hash, inferred or explicit route, model, effort, attempts, and resume reference—not prompt text or model output.
- Treat a zero exit status as child dispatch success, not final feature validation. The supervisor still validates and integrates the result.

The default mapping is versioned and dated because model availability changes. Refresh `config/model-routing.json` against the current host-selectable catalog before relying on stale entries. Optional profile templates under `config/codex-profiles/` support human-launched sessions; they are not the live automatic router and must not be copied into `$CODEX_HOME` without approval.

## Health and usage signals

Health is separate from static capability. Track, without storing secrets:

```text
lastSuccessAt
lastFailureAt
rollingSuccessRate
rollingErrorRate
p50LatencyMs
p95LatencyMs
recent429Count
remainingRequests
remainingTokens
resetRequestsAt
resetTokensAt
lastRequestId
```

For OpenAI API integrations, capture rate-limit response headers such as `x-ratelimit-remaining-requests`, `x-ratelimit-remaining-tokens`, and their reset values, plus request IDs. Account limits are dynamic and must not be copied from model documentation into project configuration.

Use health states:

```text
GREEN  compatible, available, recent success, sufficient remaining budget
YELLOW elevated latency/errors, low remaining budget, or recent throttling
RED    unavailable, deprecated, repeated failures, or no usable quota
```

Do not treat a static catalog as proof that a particular account/model request will succeed. Request telemetry and account-specific rate-limit signals are the operational evidence.

## Selection algorithm

```text
1. Classify the task from the user request and project context.
2. Honor an explicit user-selected model or quality requirement.
3. Estimate context size, output size, tools, modalities, and reasoning need.
4. Filter models that cannot satisfy those requirements.
5. Remove RED models and penalize YELLOW models.
6. Prefer the lowest cost/latency GREEN model that meets the quality threshold.
7. Use the stronger model when the task is high-risk or the smaller model fails validation.
8. If no model qualifies, return BLOCKED or request user direction; do not silently lower a safety or quality requirement.
9. Record the decision and fallback plan in the handoff or task log.
```

## Fallback and escalation

- A fallback must preserve required tools, context capacity, modality, and safety level.
- Rate-limit failures may use a compatible fallback or wait until the recorded reset time.
- Capability failures require escalation, not blind retries.
- A model that produces an incomplete, uncertain, or validation-failing result may be escalated once to the next suitable class.
- Do not endlessly retry or cycle models.
- High-risk tasks require explicit review even when the strongest model succeeds.

Automatic fallback is bounded and capability-preserving:

```text
dispatch failure or unavailable candidate
  -> classify failure: capability | health | rate-limit | validation | context
  -> choose the next compatible candidate
  -> retry at most the configured limit
  -> revalidate the complete result
  -> accept, escalate, human-selection fallback, or BLOCKED
```

Health or rate-limit failure may use another compatible candidate. Capability or validation failure must escalate to a stronger or better-suited candidate. Never downgrade a safety, privacy, context, or quality requirement merely to avoid blocking. Never cycle indefinitely.

Local/offline routing rules are defined in `LOCAL-MODEL-ROUTING.md`. A local model may handle a bounded supporting subtask inside a high-risk feature, but must not silently become the sole decision-maker when the task requires stronger reasoning, current external facts, unavailable tools, or explicit review.

## Human-in-the-loop model selection

If automatic routing is unavailable, cannot verify model health, or exhausts its safe launch/fallback attempts, Loop must enter `AWAITING_HUMAN_MODEL_SWITCH`. Present a recommendation before asking the engineer to select a model with the host model selector, such as `/model` in Codex. The recommendation must be based on the bounded task class and capability requirements, not on the parent feature name alone.

When the accessible live catalog is available, recommend a specific selectable model and reasoning level. Otherwise recommend a capability tier and clearly mark the exact model as unresolved. Include one safe alternative when possible. Do not ask the engineer to choose a task class or perform the routing analysis.

Use this compact format:

```text
Automatic model switch failed or is unavailable.
Routing state: AWAITING_HUMAN_MODEL_SWITCH
Task class: <simple | focused | standard | reasoning | high-risk | large-context | browser>
Recommended: <exact selectable model, or capability/cost tier> with <reasoning level>
Why: <one sentence tied to the task requirements>
Alternative: <compatible model/tier, if safe>
Checkpoint: <routing checkpoint and resume reference>
Action: change the model with the host selector (for example /model), then confirm or continue from this checkpoint.
```

The human fallback lifecycle is:

```text
automatic dispatch/switch fails or is unsupported
  -> exhaust bounded compatible automatic alternatives
  -> write a compact routing checkpoint without private prompt content
  -> recommend exact model + reasoning level when knowable
  -> engineer changes model using the host UI/command
  -> Loop verifies the active/selected route when evidence is available
  -> resume the same bounded task and local context packet
  -> validate normally and record the outcome
```

Do not continue capability-sensitive work under the old model while waiting for the switch. If the engineer deliberately selects another model, respect that choice after warning only when it fails a hard context, tool, modality, privacy, or safety requirement. If no selectable model can satisfy a hard requirement, report `BLOCKED` rather than recommending an unsafe downgrade.

Recommendation guidance:

```text
simple        -> cost-sensitive / fast model, none or low reasoning
focused       -> cost-sensitive or balanced model, low reasoning
standard      -> balanced coding model, low or medium reasoning
reasoning     -> stronger reasoning/coding model, high reasoning when justified
high-risk     -> strongest compatible model, high or max reasoning, explicit review
large-context -> model with a sufficient context window before optimizing cost
browser       -> model with the required browser/tool capability; Playwright remains opt-in
```

Use the current provider catalog to translate these capability tiers into model names. Never claim that the recommended model is healthy or within quota unless live account-specific evidence is available. A user-selected model takes precedence and must be recorded as an explicit choice.

## Decision record

Record a compact routing record:

```text
taskClass: reasoning
selectedModel: <actual provider model ID>
reasoning: high
contextRequired: <estimate>
requiredTools: <tools>
health: GREEN | YELLOW | RED
usageSignal: <remaining/reset summary or unavailable>
fallback: <compatible model or none>
reason: <why this model met the task requirements>
session: <current or newly launched session reference>
routeState: AUTO_SELECTED | AWAITING_HUMAN_MODEL_SWITCH | HUMAN_SELECTED | BLOCKED
recommendedModel: <model/tier or none>
humanSelection: <confirmed model or none>
resumeReference: <checkpoint/session/task reference>
```

Never record API keys, tokens, private prompts, private user data, or full request payloads.

## Local-first operation

Routing decisions are local metadata. The project remains usable without a provider API, health endpoint, or network access. If live model health cannot be checked, mark it `UNKNOWN`, use the configured safe model policy, and report the limitation. Do not claim live availability from stale metadata.

Model routing does not replace the Loop’s context routing. The context index and project map reduce what is loaded; model routing selects the capability needed for the remaining task.

## Measurement

Evaluate routing using representative tasks and compare:

- Task success rate
- Required validation pass rate
- Escalation rate
- Latency
- Input, cached, output, and reasoning tokens where available
- Rate-limit incidents
- Cost or quota consumption
- User correction and rework rate

The routing policy is successful only if it reduces cost or latency without increasing failed work, unsafe decisions, or rework.
