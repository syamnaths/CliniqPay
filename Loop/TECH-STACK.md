# NexaForge Generic Technology and Implementation Architecture

This document defines a language-neutral technology-selection policy for applications built under the NexaForge collaboration loop. It is the implementation companion to [`communication-architecture.md`](./communication-architecture.md); it is not the architecture of `loop.md`.

The communication model, safety rules, local-first process, evidence levels, and testing standards are reusable across programming languages, frameworks, transports, databases, deployment models, and application domains. A project selects a concrete implementation profile during preflight and records the choice in `HANDOFF.md`.

## Core decision

Do not treat the technology choices in this document as mandatory products. Treat them as capability requirements and selection criteria.

```text
Generic architecture and invariants
  -> project constraints and product needs
  -> implementation profile
  -> dependency preparation
  -> local proof and validation
  -> measured production decision
```

Every implementation must preserve the generic communication contracts, security controls, local-first validation model, checkpoint process, and evidence classifications even when its tools differ.

## Technology decision matrix

| Capability | Required decision | Selection rule |
|---|---|---|
| Primary language | Project-selected | Choose a maintained language with suitable libraries, tooling, security support, and local compatibility. |
| Application framework | Project-selected or minimal runtime | Use a framework when it reduces risk; avoid adopting one without a measured need. |
| Public transport | Project-selected adapter | Choose HTTP, WebSocket, SSE, QUIC, messaging, native IPC, or another transport according to client and delivery needs. |
| Protocol format | Project-selected | JSON is the default interoperable format; use a typed or binary format when measured requirements justify it. |
| Route/message model | Required | Use versioned envelopes, schemas, owners, policies, correlation, idempotency, and observability. |
| Durable data store | Project-selected | Choose a transactional database or equivalent durable store appropriate to consistency, query, scale, and retention needs. |
| Queue/cache/coordination | Conditional | Add only when required for asynchronous work, rate limits, locks, pub/sub, or short-lived state. |
| Background execution | Project-selected | Use processes, workers, jobs, actors, functions, containers, or platform tasks as appropriate. |
| Frontend | Project-selected | Use the smallest client technology that satisfies the product and accessibility requirements. |
| Styling/design system | Project-selected | Define semantic tokens, responsive behavior, focus states, and component states before feature UI. |
| Ingress and transport security | Project-selected | Use a maintained proxy, gateway, platform ingress, or direct secure runtime with documented TLS and origin controls. |
| Testing | Required layers | Use static, unit, protocol, runtime, browser, security, load, and manual evidence only where applicable. |
| Dependency management | Project-selected | Use a lockfile, trusted package source, reproducible install, audit, and documented versions. |
| Source history | Local Git preferred | Initialize local Git in the target project when possible; continue with file snapshots if unavailable. |

## Implementation profile

Before implementation, record one concrete profile. The profile may be a monolith, modular monolith, service-based system, serverless system, desktop application, mobile application, CLI, library, embedded application, or another justified shape.

```text
profileName: <name>
scope: production-shaped | protocol-proof | technical-spike
language: <language and version>
framework: <framework and version, or none>
client: <browser | native | CLI | service | none>
publicTransport: <HTTP | WebSocket | SSE | QUIC | IPC | none | other>
protocolFormat: <JSON | MessagePack | Protobuf | other>
durableStore: <database or none>
queueOrCoordination: <technology or none>
backgroundExecution: <worker/process/function/actor/none>
frontend: <technology or none>
styling: <technology or none>
ingressAndTLS: <proxy/platform/direct/none>
testRunner: <tool>
browserRunner: Playwright | not-applicable
modelRouting: optional | unavailable | active
localModelRouting: optional | unavailable | configured | active
activeComponents: <list>
deferredComponents: <list>
notApplicableComponents: <list with reasons>
fallbacks: <list>
```

The profile must explain why each major choice fits the product, machine, delivery target, security model, and proof scope. It must identify installed, missing, incompatible, cached, and deferred dependencies.

### Loop deployment boundary

Loop policy and internal context belong in the private source repository when the project needs them, but are excluded from production deployment artifacts and public web roots by default. A project must record any intentional internal deployment copy and its access controls. Secrets and private runtime data never belong in Loop documents.

## Generic application structure

Use boundaries that fit the selected language and framework. Names may change, but responsibilities remain clear:

```text
application/
├── protocol/          # envelopes, schemas, codecs, transport adapters
├── routes/            # versioned route registry and policy metadata
├── domain/            # business rules and domain modules
├── application/       # commands, queries, workflows, use cases
├── infrastructure/   # persistence, queues, external systems, telemetry
├── tasks/             # asynchronous task contracts and workers
├── client/            # optional browser, native, CLI, or service client
└── tests/             # static, unit, protocol, runtime, browser, and load tests
```

The transport layer routes messages and enforces boundary controls. Domain modules own business decisions. Long-running, resource-sensitive, or resumable work uses the project’s selected worker model while preserving the Ghost task invariants defined in `communication-architecture.md`.

## Protocol and transport implementation

The protocol is transport-neutral. A project may expose it through one or more adapters:

```text
Client
  -> transport adapter
  -> frame/message decoder
  -> version and schema validation
  -> authentication/session checks
  -> route policy and rate limits
  -> route handler or task scheduler
  -> response/event/progress adapter
```

WebSocket is supported but not required for every project. If WebSocket is selected, apply the WebSocket security controls in `loop.md` and `communication-architecture.md`. If another transport is selected, document its equivalent origin, authentication, authorization, framing, replay, backpressure, and connection controls.

The selected transport must support the required application behaviors or document a safe fallback for:

- Request/response
- Commands and queries
- Events and subscriptions
- Progress and completion
- Cancellation and expiry
- Reconnect and resume where applicable
- Correlation and tracing
- Idempotency and duplicate delivery
- Payload limits and backpressure
- Binary or large-payload transfer where applicable

## Data, persistence, and consistency

Choose durable storage according to the application’s consistency, query, scale, privacy, retention, and recovery needs.

Required rules:

- Use migrations or an equivalent repeatable schema process.
- Use transactions or equivalent atomic operations for related state changes.
- Use unique constraints or equivalent invariant enforcement for idempotency.
- Persist durable task state before starting asynchronous execution.
- Persist results before publishing completion.
- Use an outbox or equivalent consistency pattern when state changes and event publication must be coordinated.
- Do not use caches, browser storage, queues, or process memory as the only source of durable business truth.
- Define backup, restore, retention, deletion, and recovery expectations.

## Queues, workers, and Ghost execution

Queues, workers, actors, scheduled jobs, functions, and other execution systems are implementation choices. Their behavior must satisfy the generic Ghost contract:

```text
accepted task
  -> durable task record
  -> bounded execution
  -> lease/heartbeat/deadline where applicable
  -> checkpointing where required
  -> result persistence
  -> response/event publication
  -> acknowledgement and release
```

Every asynchronous task must define:

- Task identity and correlation fields
- Execution mode and capability limits
- Deadline, timeout, lease, or cancellation behavior
- Retry and idempotency policy
- Progress and checkpoint behavior
- Failure and dead-letter behavior
- Completion persistence and publication order
- Cleanup and worker-release behavior

Do not introduce a queue, cache, container, service, or worker pool solely because it is conventional. Add infrastructure when the product behavior, isolation, reliability, or measured load requires it.

## Client and frontend

The client may be a browser, native application, CLI, service, or no client at all. Client SDKs should own transport concerns rather than business rules:

- Connection or request lifecycle
- Authentication refresh where applicable
- Correlation and timeout handling
- Retry and reconnect behavior
- Subscription restoration and event sequencing
- Typed payload conversion
- Safe public error conversion
- Local test instrumentation

For browser applications, define responsive design tokens and component states before feature screens. The `.screen-brand-logo` rule is reusable where that component exists: use a maximum dimension of `80px` in horizontal flex rows, center standalone logos with a maximum width of `125px`, preserve aspect ratio, shrink inside narrow containers, and prevent horizontal overflow.

## Ingress, deployment, and scaling

Use the simplest local and deployment topology that meets the proof scope. Possible components include a development server, reverse proxy, platform ingress, TLS terminator, gateway, worker supervisor, scheduler, or direct application process.

Production or shared environments must document:

- Secure transport and certificate/trust mode
- Origin and host allowlists where relevant
- Process ownership and graceful shutdown
- Health/readiness checks
- Port and socket exposure
- Scaling boundaries and shared state
- Logs, metrics, traces, alerts, and redaction
- Backup, rollback, and recovery

Scale from measured connections, requests, messages, bytes, latency, CPU, memory, queue depth, storage, error rate, and reconnect behavior. Do not claim capacity without representative load evidence.

## Testing and quality

Required validation is proportional to the application profile:

- Static checks: syntax, types, configuration, formatting, dependency and schema checks.
- Unit checks: isolated domain rules, handlers, policies, codecs, and utilities.
- Protocol checks: envelope, framing, route, schema, correlation, error, idempotency, replay, and duplicate-delivery contracts.
- Runtime checks: real local processes, readiness, routes, persistence, workers, queues, timers, and cleanup.
- Security checks: threat model, secrets, authentication, authorization, injection, origin, rate limits, replay, safe errors, and auditability.
- Load checks: representative connections, requests, messages, payloads, latency, throughput, memory, queues, and failure recovery.
- Browser checks: headless Playwright for browser behavior whenever the application has a browser interface or browser evidence is relevant.
- Manual checks: optional human visual or exploratory review; never silently substitute for required automated evidence.

### Local-first headless Playwright standard

Codex may invoke Playwright automatically whenever browser behavior, browser protocol behavior, accessibility behavior, responsive behavior, or a browser release gate is relevant. A separate manual trigger is not required. Tests run against the local target application and local supporting services with disposable local data.

Use:

- Isolated browser contexts and deterministic fixtures
- Stable user-facing locators and web-first assertions
- No arbitrary sleeps or implementation-detail selectors
- Local mocks or controlled fixtures for third-party services
- Chromium headless as the default browser project
- Firefox/WebKit headless compatibility projects when required
- Zero local retries; CI retries only for diagnosis, with retry-passing tests reported as `FLAKY`
- Traces on first retry or failure
- Temporary screenshots only when page-design or responsive checks are in scope

Minimum responsive viewports when applicable:

```text
mobile:  390x844
tablet:  768x1024
desktop: 1440x900
```

Screenshots, traces, videos, browser contexts, cookies, local/session storage, reports, and temporary test data remain local to the task. Remove disposable artifacts and close browser contexts and processes after evaluation. Do not commit them or place secrets/private data in them. Missing browsers or unhealthy local services are `BLOCKED`, not application failures. Browser dependency installation that requires network access remains approval-gated.

Equivalent project commands should be documented when applicable, for example:

```text
<package-manager> run test:e2e
<package-manager> run test:e2e:critical
<package-manager> run test:e2e:report
```

## Dependency and source management

Before implementation:

- Inspect manifests, lockfiles, runtime versions, and package sources.
- Prefer reproducible lockfile installation.
- Record dependency status as available, cached, missing, incompatible, or blocked.
- Run dependency health, audit, type, lint, build, test-discovery, and local-start checks as applicable.
- Request one consolidated approval before network package, browser, toolchain, or system dependency installation.
- Never commit secrets, generated noise, browser artifacts, credentials, or unapproved files.

## Optional reference implementation profile: PHP/Laravel

The following is an example, not the generic default. Use it only when the project’s constraints and product needs justify it:

```text
language: PHP 8.5, with PHP 8.4 compatibility where required
framework: Laravel 13 modular monolith
public transport: Workerman-based secure WebSocket gateway
data format: JSON
durable store: PostgreSQL
queue/coordination: Redis or Valkey when required
background execution: Laravel queue workers implementing Ghost contracts
browser client: TypeScript SDK around the native WebSocket API
styling: Tailwind CSS v4
ingress: Nginx or Caddy
tests: PHPUnit/Pest, PHPStan, Pint or PHP CS Fixer, Playwright, protocol and load tests
```

This reference profile must not override a project’s declared language, framework, transport, database, or deployment requirements. Any substitution must be recorded with its effect on confidence and validation.

## Decisions still required from each project

- Product domain and route list
- Client types and supported platforms
- Language, framework, and version policy
- Transport and protocol format
- Authentication, session, and authorization model
- Durable entities, consistency, privacy, and retention
- File/media and payload limits
- Queue, worker, and task requirements
- Browser support and required Playwright projects
- Accessibility and responsive targets
- Concurrency, latency, availability, and recovery targets
- Deployment environment and operating system
- External services and managed infrastructure
- Selected security level and exclusions

## Confidence assessment

Confidence must be reported by capability, not assumed from the selected tools:

- Language/framework fit: <high | medium | low>
- Protocol and transport fit: <high | medium | low>
- Persistence and consistency fit: <high | medium | low>
- Worker/task fit: <high | medium | low>
- Browser and Playwright fit: <high | medium | low | not-applicable>
- Security evidence: <tested scope and remaining gaps>
- Production capacity: <measured | unmeasured>
- Overall architecture confidence: <high | medium | low>

No implementation profile is production-approved solely because its tools are popular or its tests pass. Report tested controls, untested controls, evidence level, open risks, and next validation step.
