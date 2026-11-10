# Generic Application Communication Architecture

This document defines the communication architecture for applications built under the NexaForge collaboration loop. It describes the application being built, not the architecture of `loop.md` itself.

## Architectural intent

The architecture defines a generic, centralized communication plane for applications that need request/response operations, commands, queries, events, subscriptions, streaming, or long-running tasks. WebSocket is the initial public transport for browser clients. The protocol core remains domain-neutral and does not own business logic.

```text
Client
    |
    | Secure WebSocket (wss://)
    v
Central WebSocket hub layer
    |
    v
Route registry and task classifier
    |
    +--> Fast application handlers
    +--> Warm Ghost workers
    +--> Cold Ghost workers
    +--> Durable Ghost workers
    |
    v
Database, queues, workers, and internal modules
```

## Scope and boundaries

- A browser is the initial client, but the protocol may also be used by CLI, native, service, or worker clients through an appropriate adapter.
- Request/response operations, live events, notifications, status updates, subscriptions, and task progress use the WebSocket communication plane.
- JSON is the primary payload format.
- Binary data uses a separate logical layer and, where useful, a separate WebSocket channel.
- The hub is the only public application entry point for browser communication. Other client types may use approved protocol adapters.
- Internal modules remain private and are reached through the hub or internal application mechanisms.
- The hub routes communication; domain modules own business logic.
- The protocol does not assume any business concepts. Authentication, authorization, ownership, tenant, and capability rules are supplied by the application profile when applicable; connection and route security always apply.

## Public communication rule

Clients must not call application modules directly.

```text
Client -> protocol transport -> communication hub -> route owner -> application logic
```

The client knows the transport endpoint and versioned message protocol. It does not need to know the internal module topology.

Internal function calls, queues, HTTP, or other protocols may be used behind the hub when technically appropriate. The requirement is centralized browser communication, not forced WebSocket usage for every internal operation.

## Hub responsibilities

The hub is responsible for:

- Connection lifecycle
- Secure handshake and session establishment
- Authentication and connection validation
- Message envelope validation
- Route lookup
- Per-message authorization and policy checks
- Rate limiting and quotas
- Request/response correlation
- Subscription management
- Event delivery
- Task acceptance and status delivery
- Reconnection and resume support
- Backpressure and bounded queues
- Tracing, metrics, audit events, and safe errors

The hub must not become a monolithic business-logic server. It must not own complex domain workflows, long-running computation, large file processing, or permanent business state.

## Protocol core

The protocol core is reusable across application domains. It defines envelopes, message types, identifiers, schemas, errors, correlation, idempotency, sequencing, subscriptions, task progress, cancellation, security policy hooks, and observability fields. An application profile supplies domain routes, payload schemas, policies, handlers, workflows, retention rules, and performance targets.

The core must not assume a particular domain, database schema, authentication mechanism, frontend framework, or business vocabulary. Unused capabilities are declared `DEFERRED` or `NOT_APPLICABLE` in the project handoff rather than silently omitted.

## Message protocol

Every message uses a versioned envelope:

```json
{
  "version": "1.0",
  "id": "req_123",
  "type": "request",
  "route": "<module>.<resource>.<operation>",
  "timestamp": "2026-08-02T10:00:00Z",
  "traceId": "trace_456",
  "parentId": "req_100",
  "idempotencyKey": "idem_789",
  "payload": {}
}
```

Supported message types:

- `request` — client requests an operation.
- `response` — hub or handler returns a result.
- `event` — server publishes an event.
- `subscribe` — client subscribes to a stream.
- `unsubscribe` — client ends a subscription.
- `ack` — client or server confirms delivery or processing.
- `error` — structured failure response.
- `progress` — task progress update.

Required fields are `version`, `id`, `type`, `route`, and `traceId`. Every side-effecting operation also requires an `idempotencyKey`; read-only operations may omit it when repetition has no side effect.

## Route framework

Routes use the structure:

```text
<domain>.<resource>.<operation>
```

Examples are application-profile examples only:

```text
auth.session.create
users.profile.get
orders.create
orders.status.subscribe
notifications.subscribe
files.upload.start
```

Every route must have one owner and a registry entry containing:

```text
Route
Owner
Version
Message type
Input schema
Output schema
Authentication requirement
Authorization rule
Rate limit
Timeout
Idempotency requirement
Priority
Execution mode
Retry policy
Audit requirement
```

Route rules:

- One route has one owning module.
- The hub does not implement domain decisions.
- Routes are versioned.
- Schemas are explicit and validated at the boundary.
- Permissions and limits are declared per route.
- Cross-domain workflows use an application service or task workflow.
- Deprecated routes have a documented migration period.
- Route changes require a checkpoint and validation.

The generic system routes are transport and task capabilities, not business routes. Application-profile routes must be added only when their owner, schema, policy, validation, and checkpoint are defined.

## Request pipeline

Every incoming message follows the same pipeline for every transport adapter. The WebSocket path is:

```text
WebSocket ingress
  -> frame decoding
  -> envelope validation
  -> authentication
  -> client/session checks
  -> route policy checks
  -> rate limiting
  -> route registry lookup
  -> task classification
  -> handler or Ghost execution
  -> response/event publication
  -> tracing and audit
```

No handler may bypass envelope validation, route policy, or tracing.

## Execution modes

The hub uses a Ghost Hybrid Protocol and selects an execution mode per task.

```text
Short and simple       -> fast in-process handler
Medium and repeatable  -> warm Ghost
Heavy or isolated      -> cold Ghost
Long or resumable      -> durable Ghost
```

### Fast path

Use for small reads, simple validation, and low-risk operations. The hub routes directly to an application handler without creating a Ghost.

### Warm Ghost

Use a limited warm worker pool for frequent or medium-duration work. A warm Ghost may process multiple bounded tasks for a short lifetime and then terminate after an idle timeout.

### Cold Ghost

Create an isolated worker for heavy, infrequent, untrusted, or resource-sensitive work. The Ghost terminates after publishing and persisting the result.

### Durable Ghost

Use for long-running or resumable tasks. The Ghost saves progress checkpoints so a replacement worker can resume after failure.

## Ghost task lifecycle

```text
RECEIVED
  -> VALIDATED
  -> CLASSIFIED
  -> QUEUED
  -> LEASED
  -> RUNNING
  -> CHECKPOINTED       optional
  -> RESULT_PERSISTED
  -> RESULT_PUBLISHED
  -> ACKNOWLEDGED
  -> COMPLETED
  -> GHOST_RELEASED
```

Failure states are `FAILED_RETRYABLE`, `FAILED_FINAL`, `CANCEL_REQUESTED`, `CANCELLED`, `EXPIRED`, and `DEAD_LETTERED`.

Ghost rules:

- A task is durably recorded before a Ghost starts.
- A Ghost receives one bounded task packet.
- A Ghost has a lease, heartbeat, deadline, and capability-limited access.
- A Ghost cannot communicate directly with the browser.
- Results are persisted before completion is reported.
- Retries use idempotency keys and must be safe for at-least-once execution.
- Every state transition is observable.
- A Ghost may terminate only after its task state is resolved or safely recoverable.

## Reconnection and resume

Clients use a connection state machine:

```text
DISCONNECTED -> CONNECTING -> AUTHENTICATING -> READY -> RECONNECTING
```

The client must use exponential backoff with jitter, request timeouts, authentication refresh, subscription restoration, and cancellation support.

Event streams use sequence numbers. After reconnecting, a client can request events after its last received sequence. If replay is unavailable, the hub sends a resynchronization instruction.

Commands that may be retried require idempotency keys. The system assumes at-least-once execution and prevents duplicate side effects through idempotency storage and database constraints.

## Idempotency and duplicate delivery

WebSocket delivery is at-least-once. The protocol must not assume that a command, event, subscription, or completion notification is received exactly once.

Use separate identifiers for separate purposes:

```text
messageId       -> identifies one message
idempotencyKey  -> prevents duplicate command effects
eventId         -> identifies one published event
sequence        -> orders events within one stream
subscriptionId  -> identifies one active subscription
taskId          -> identifies one durable task
```

### Duplicate commands

- Every side-effecting route requires an idempotency key.
- Store the key, request fingerprint, outcome, and result durably.
- A repeated key with the same request returns the original logical result without repeating the side effect.
- A repeated key with a different request is rejected as an idempotency conflict.
- Read-only routes may omit an idempotency key when repetition has no side effect.

### Duplicate events and replay

- Every event requires an `eventId`, stream identifier, and sequence number.
- The client tracks the last accepted sequence per stream and a bounded set of recently seen event IDs.
- A replayed event whose ID was already processed is ignored at the client surface.
- An event with a gap triggers replay or an explicit resynchronization through durable state.
- The server may publish an event more than once internally, but the client-visible state must be deduplicated.

### Duplicate subscriptions

- Every subscription has a `subscriptionId` and stream key.
- Repeating the same subscription request returns the existing subscription or explicitly replaces it.
- The server must not silently create duplicate subscription pipelines for the same client and stream.

### Duplicate task completion

- Durable task results are keyed by `taskId` and written once as the authoritative business result.
- Completion events include both `taskId` and `eventId`.
- Replayed completion events must not create another business side effect or another client-visible completion state.
- The client reconciles completion with `task.status.get` when delivery history is unavailable.

Acknowledgement confirms receipt or processing at a particular layer; it does not by itself guarantee exactly-once delivery.

## Backpressure and overload control

Backpressure occurs when a producer sends data faster than a client, hub, or handler can process it.

The system must use:

- Per-connection and global queue limits
- Maximum message sizes
- Per-route concurrency limits
- Client and route rate limits
- Priority levels
- Acknowledgements for important streams
- Coalescing for replaceable updates
- Sampling or batching for telemetry
- Stale-event dropping for low-value live updates
- Explicit throttling or rejection when capacity is exhausted

Critical command results must not be silently dropped. Low-value presence, typing, or telemetry events may be coalesced, sampled, or dropped according to route policy.

## Text and binary communication

JSON is the primary control and application-data layer. Binary traffic receives separate policies for size, queueing, rate limits, timeout, and observability.

Preferred layout:

```text
wss://application.example/control  -> JSON commands, events, subscriptions
wss://application.example/binary   -> binary or large-payload transfer
```

Large files should preferably use a negotiated transfer channel while progress and completion remain WebSocket events. If binary data must remain on WebSockets, use chunk IDs, checksums, acknowledgements, resumability, and an independent binary queue.

## Scaling architecture

The hub is logically centralized but may run as multiple instances:

```text
Browser connections
        -> WebSocket-aware load balancer
        -> Hub instance 1..N
        -> shared session/event coordination when required
        -> private application modules and Ghost scheduler
```

Scale based on sustained active connections, messages per second, inbound/outbound bytes, CPU, memory, event-loop latency, queue depth, request latency, and reconnect rate.

Existing connections remain attached to their current hub instance. New connections are distributed to available instances. Business state must not depend on one hub instance’s memory.

Start with the simplest deployment that meets measured demand. Add shared coordination, additional hub instances, or separate services only when traffic, isolation, or reliability requirements justify them.

## Local-first protocol and browser validation

Protocol development and validation are local-first. The project root is the source of truth, and tests run against local application processes, local databases, local queues/caches, and disposable local data. External services are not required for the default proof; controlled local fixtures or mocks are used where an external dependency is not in scope.

When an application profile defines a `.screen-brand-logo` UI component, its responsive behavior is part of the browser validation profile: verify the flex-row `80px` maximum, standalone centered `125px` maximum width, aspect-ratio preservation, narrow-container shrink behavior, and absence of horizontal overflow at mobile, tablet, and desktop viewports.

The validation order is:

```text
local static checks
  -> local unit tests
  -> local protocol/WebSocket tests
  -> local runtime tests
  -> local headless Playwright tests
```

Headless Playwright is the required browser-level test standard for browser-facing applications. Codex may invoke it automatically whenever browser evidence is relevant; a separate manual trigger is not required. It validates user-visible behavior, browser WebSocket behavior, authentication/session flows, subscriptions, progress, completion, reconnect/resume, error states, keyboard behavior, and responsive behavior. Responsive page-design checks use at least mobile `390x844`, tablet `768x1024`, and desktop `1440x900` local viewports unless the application declares more appropriate target dimensions. Manual visual review is optional and is not a release or completion gate.

Playwright tests must use isolated local contexts and disposable data, stable user-facing locators, web-first assertions, deterministic fixtures, and explicit cleanup. Page-design checks may capture screenshots, but screenshots are temporary evaluation artifacts stored in a task-scoped local directory and removed after evaluation. Browser contexts, cookies, storage, traces, screenshots, videos, and reports must be closed or removed after the run and must not be committed. Tests must not use production credentials, real private data, arbitrary sleeps, or direct assertions against implementation details. Third-party services are mocked or controlled rather than tested directly.

Chromium headless is the default on-demand local browser project. Firefox and WebKit headless projects are added to compatibility or release gates when applicable. Browser binaries, local services, and test dependencies are checked during preflight. Missing browsers or unhealthy local services are reported as `BLOCKED`, not as application failures.

Required browser-test evidence includes the Playwright version, browser project, local target URL, test command, pass/fail/flaky result, and retained failure artifacts. Traces are enabled on the first retry or failure; screenshots and videos are diagnostic artifacts only. Local runs use zero retries by default. CI may use one retry, but a test that passes only after retry is reported as `FLAKY`. Browser dependency installation that requires network access remains subject to the project approval gate.

## Security standards

- Use `wss://` in production.
- Validate the connection origin using an allowlist.
- Authenticate the connection and authorize every sensitive message.
- Validate every message against its route schema.
- Enforce tenant, resource, and capability boundaries when applicable.
- Apply per-connection, per-client, and per-route limits.
- Limit frame and payload sizes.
- Protect sensitive commands with idempotency and replay controls.
- Never expose secrets through messages, logs, or Ghost capabilities.
- Audit sensitive route execution.
- Return safe error messages without leaking internal details.
- Test for Cross-Site WebSocket Hijacking and malformed-message attacks.

The implementation should follow the WebSocket protocol defined by [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455/) and the security practices in the [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html).

## Observability

Every operation should be traceable using:

```text
requestId
traceId
parentId
connectionId
taskId
ghostId
route
attempt
hubInstance
status
latency
errorCode
```

Record connection events, route decisions, task state transitions, retries, backpressure actions, Ghost heartbeats, and result publication. Do not log credentials, tokens, private payloads, or secrets.

## Architectural choices

### Initial recommendation: modular monolith

Use one deployable backend containing the hub, application modules, database access, and a small worker interface. This is the simplest starting point and keeps module boundaries clear.

### Add Ghost workers when needed

Use the Ghost Hybrid Protocol for long-running, bursty, CPU-heavy, isolated, or resumable tasks.

### Extract services only when justified

Separate services may be introduced later for independently scaling, isolating, or deploying modules. They are not required at the beginning.

## Non-negotiable invariants

1. The browser communicates through the public WebSocket hub.
2. The hub routes communication but does not own domain business logic.
3. Every message is versioned, validated, correlated, and policy-checked.
4. Every route has one owner and an explicit contract.
5. Every Ghost task is durable, bounded, observable, and recoverable.
6. Side-effecting commands are idempotent and safe under retry.
7. Events, subscriptions, and task completions are deduplicated by protocol identifiers.
8. Queues are bounded and overload is deliberate.
9. Results are persisted before completion is reported.
10. Sensitive actions are authorized at message level.
11. Scaling is based on measured demand, not assumptions.

## Change control

Any change to the hub protocol, route registry, message envelope, execution modes, retry semantics, security controls, or scaling assumptions requires:

- Architecture review
- Updated route or protocol documentation
- Proportionate implementation and validation
- A checkpoint in `HANDOFF.md`
- A local Git checkpoint when Git is available
