# Local and Offline Model Routing

This document extends [`MODEL-ROUTING.md`](./MODEL-ROUTING.md) with an optional local inference route. It keeps the Loop usable when network access, provider access, or remote model capacity is unavailable.

The host-integrated Loop capability refreshes the machine and local-model profile at activation. The profile check is read-only and advisory until a verified model adapter is configured; it does not start a model or make a routing decision on behalf of an unconfigured project.

The reference pattern is a local [llamafile](https://github.com/Mozilla-Ocho/llamafile) executable paired with a compatible GGUF model. The supplied reference document, [Run Offline AI from a USB Pendrive](https://docs.google.com/document/d/1tWyQ5ZonKTR8kLBL3E06Y9t1CWQIGy5ZHN1QXPjpCYI/edit), describes the portable executable/model arrangement. Its Windows and USB commands are examples, not universal project requirements.

## Local route boundary

Local routing is allowed only when the model and runtime are already available locally or the user has approved their installation. The route must not download models, contact a provider, expose project data, or install dependencies silently.

The local model is a capability option, not an automatic quality guarantee. Before selecting it, verify its local manifest:

```text
provider: llamafile | other-local-runtime
modelFile: <local GGUF path or approved local model identifier>
runtimeVersion: <verified version>
contextWindow: <verified tokens>
maxOutputTokens: <verified tokens>
reasoningCapability: none | low | medium | high | unknown
tools: shell | file | patch | none | <declared set>
modalities: text | image | other
memoryRequired: <estimated RAM/VRAM>
networkRequired: false
health: GREEN | YELLOW | RED | UNKNOWN
verifiedAt: <local timestamp>
```

If the manifest, context capacity, or health is unknown, do not claim that the local model is suitable. Use `UNKNOWN`, reduce the task scope, ask the user, or return `BLOCKED`.

## When the local model may be used

Route to a local model when all required capabilities fit and at least one of these conditions applies:

- The task is simple or focused: classification, extraction, formatting, summarization, local documentation drafting, deterministic transformation, or small isolated edits.
- The task contains private or sensitive project context that should not leave the machine.
- The user is offline, provider access is unavailable, or the user explicitly prefers local processing.
- The task needs only local files and declared local tools, with no current external facts or remote service.
- A local model is sufficient for a bounded subtask inside a larger feature, such as indexing files, preparing a test matrix, generating a first-pass map, or compressing a handoff.
- Local execution is being used for a low-risk first pass that will be validated by the required stronger route.

Do not route solely because a local model exists. The selected model must fit the task’s context, output, tool, modality, quality, and safety requirements.

## When the local model must not be the sole route

Keep the task on a stronger verified route, or require explicit review and escalation, for:

- Security decisions, secrets, authentication, authorization, privacy, incident response, or threat-model conclusions.
- Production migrations, destructive recovery, concurrency correctness, financial or legal decisions, or other high-risk work.
- Complex algorithms, architecture decisions, broad refactors, or diagnosis where the local model’s reasoning capability is not verified.
- Tasks requiring current external facts, provider-specific behavior, web research, or a tool the local runtime cannot provide.
- Work whose context exceeds the local model’s verified window or would require sending private context to an unapproved service.
- Browser or Playwright execution unless the local environment separately provides the requested browser capability. Playwright remains opt-in under `loop.md`.

A local model may still perform a bounded supporting subtask in these cases, but a stronger route must own the decision and final validation.

## Local-first context handling

Use local context artifacts before loading broad source material:

1. Read the active handoff `NOW` section, context index, project map, and relevant architecture sections.
2. Retrieve only the files and ranges required for the bounded task.
3. Pass a compact objective, constraints, evidence requirements, and output schema to the local model.
4. Keep the source of truth in project files and handoff records; do not treat model memory as durable context.
5. Record uncertainty, omissions, and the exact local model/runtime used.

Do not use a smaller context window as permission to omit required safety rules, approvals, validation layers, or recovery instructions. If the relevant context does not fit, use a larger-context route or ask for direction.

## Offline fallback sequence

```text
classify task
  -> check local manifest and health
  -> check context/tools/safety fit
  -> local llamafile route when eligible
  -> validate output locally
  -> escalate to a verified remote/stronger route when required
  -> if no safe route exists, BLOCKED with reason
```

If remote routing fails and the local route is eligible, continue locally and record `offlineFallback: true`. If the local route fails validation, do not silently retry indefinitely or claim completion; escalate or report `BLOCKED`.

If neither the remote nor local adapter can switch automatically but a safe selectable model exists in the host, use the human-in-the-loop fallback from `MODEL-ROUTING.md`. Recommend whether the engineer should select the verified local model or a remote capability tier, preserve the local context packet and resume reference, and wait for the selection. Offline mode must never recommend an unavailable remote route as immediately executable.

## Local decision record

Add these fields to the normal routing record when local execution is selected:

```text
provider: llamafile
local: true
offlineFallback: true | false
modelFile: <local identifier, not a secret>
runtimeVersion: <verified version>
contextUsed: <estimate>
health: GREEN | YELLOW | RED | UNKNOWN
networkAccess: none
validation: <checks and result>
escalated: true | false
```

Never record private prompts, secrets, tokens, full sensitive payloads, or raw confidential model output in the routing log.

## Current Loop status

This folder defines the local routing contract, dynamic preflight, interactive recommendation path, and llamafile reference path. Loop now includes a Codex child-launch adapter for selectable Codex models, but it still does not contain a llamafile binary, GGUF model, project-specific hardware manifest, or local-model health probe. Therefore local inference remains unavailable until a consuming project supplies and verifies those components; the Codex adapter must not misrepresent remote Codex execution as local inference.
