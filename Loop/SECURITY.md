# Security verification standard

Use the latest stable [OWASP Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard/) as the application security baseline. Use ASVS Level 1 for every application, Level 2 for applications handling meaningful private or business data, and Level 3 only when the threat model or risk requires it. Record the selected level and exclusions in the project handoff.

For WebSocket applications, also apply the [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html), [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), and [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

### Required security checks

Every applicable application must verify and report:

- Threat model, trust boundaries, sensitive data, abuse cases, and security assumptions.
- Dependency provenance, lockfiles, vulnerability audit, and approved package sources.
- Secret absence from source, commits, logs, artifacts, browser output, and error messages.
- TLS/WSS configuration, certificate trust mode, secure transport, and proxy behavior.
- Explicit WebSocket origin allowlist and Cross-Site WebSocket Hijacking resistance.
- Authentication at connection/session level and authorization at message/route level.
- Session expiry, refresh rotation, logout invalidation, replay resistance, and reconnect behavior.
- No authentication tokens in URLs, local storage, session storage, logs, or page output unless a documented threat review approves the mechanism.
- Strict message envelope and payload schema validation with allowlists and bounded sizes.
- Injection resistance for SQL, command, template, HTML, JSON, and downstream service inputs.
- Per-connection, per-client, and per-route rate limits; connection exhaustion and message-flood protection.
- Idempotency and duplicate/replay protection for side-effecting commands and event streams.
- Safe error responses that do not disclose credentials, stack traces, internal paths, queries, or private data.
- Security event logging for connection, authentication, authorization, validation, rate-limit, replay, abnormal-close, and administrative events, with sensitive data redacted.
- Secure binary/file handling when applicable: type validation, size limits, safe names, storage isolation, and malware scanning where required.
- Access control and resource ownership checks where users or private records exist.
- Auditability of sensitive actions and retention rules for security logs.
- Backup, recovery, dependency rollback, and incident-response expectations appropriate to the project.

### Secret, password, salt, and environment-variable controls

Apply the [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html), and [Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html).

- Never store plaintext passwords, reversible password encryption, API keys, tokens, database passwords, private keys, or signing secrets in source code, committed configuration, fixtures, screenshots, logs, browser output, or test artifacts.
- Use the framework’s maintained password hashing facility with Argon2id where available; use an approved fallback only when the environment requires it. Never use plain SHA-256 or another fast general-purpose hash for passwords.
- Generate a unique cryptographically random salt per password through the password-hashing library. Do not invent, reuse, hide, or manually compare salts; salts are stored with the password hash and do not need to be secret.
- Use a pepper only as documented defense-in-depth, store it separately from the database, and define rotation and compromise procedures.
- Generate session secrets, encryption keys, signing keys, nonces, and idempotency secrets with a cryptographically secure random source. Never derive them from names, timestamps, predictable text, or source-controlled defaults.
- Prefer an operating-system, cloud, or dedicated secrets manager for production secrets. Environment variables are an acceptable fallback only when their exposure, permissions, process visibility, rotation, and logging risks are documented.
- Keep local `.env` files ignored and disposable. Commit only a safe `.env.example` containing placeholder names and non-secret example values.
- Do not use production secrets in local development or tests. Generate isolated test credentials and disposable keys for each environment.
- Use least-privilege credentials per service, worker, database, queue, and deployment target. Do not share one unrestricted secret across all components.
- Define secret ownership, source, scope, expiry, rotation, revocation, and emergency replacement. Key and secret rotation must be tested before an incident occurs.
- Redact secrets from exceptions, structured logs, tracing attributes, command output, `phpinfo()`, debug pages, crash dumps, and process diagnostics.
- Scan the staged diff and repository history for secrets before every checkpoint commit. If a secret is exposed, treat it as compromised: revoke or rotate it, remove access, preserve safe evidence, and document the incident.
- Fail closed when a required production secret is missing, malformed, expired, or invalid. Do not silently use a development default in a production-shaped run.
- Verify that browser-delivered code never contains server secrets, database credentials, private keys, or unrestricted service tokens.

Required secret-handling tests include plaintext-password rejection, unique-salt/hash verification, expired and rotated credential rejection, missing-secret fail-closed behavior, log redaction, repository scanning, `.env` ignore verification, and secret absence from browser artifacts.

## Feature security review and owner discussion

After functional implementation and applicable unit/integration checks pass, but before the map is marked `delivered`, adopt a security reviewer and pentester mindset in a separate review pass. Use the existing required checks above for the changed attack surface and its affected trust boundaries; do not repeat an unchanged, evidenced review without a reason. This is a review role, not a requirement to spawn another agent or run every security tool. Existing high-risk independent review requirements still apply.

1. Review the actual diff and affected data flows, then attempt focused negative/abuse tests relevant to the feature (for example unauthorised access, cross-user access, injection, replay or unsafe error disclosure). Active testing stays within explicitly authorised local or isolated test environments with synthetic data. Production or third-party targets, destructive tests and load/denial-of-service testing need specific authorisation. Missing tooling is `BLOCKED` or `INCOMPLETE`, never a clean pentest result.
2. Record findings once in the track review (or its spec for a small track): stable ID, severity with rationale, affected file/line, preconditions, safe reproduction or test evidence, user/data impact, proposed fix and verification. Distinguish confirmed vulnerabilities from suspected risks and untested controls; do not invent findings to fill a list. Redact sensitive evidence.
3. List the findings for the owner in plain language, discuss impact and recommended fixes, and wait for their response before implementing security-review remediation. If there are no confirmed findings, report the checks and limits and continue without an empty approval gate. Previously discussed and authorised fixes do not require repeated approval unless scope changes. Do not treat silence as acceptance.
4. Keep the goal active during that discussion. Record the feature as awaiting security discussion using `blockedBy`, checkpoint its restart step and return its map to `planned` before taking other dependency-ready work. Never mark it delivered while required checks or the discussion remain unresolved. Critical/high findings block delivery; medium/low findings require a recorded fix or explicit owner disposition. Release gates in `loop.md` still apply.
5. After discussion, fix the agreed findings with a failing regression/security test first where practical, rerun that test plus affected unit/integration checks, then repeat the focused security review. Update each finding with evidence and its final disposition; unresolved findings remain visible in the fix queue and handoff. Report the tested controls and remaining risk, never claim the feature is vulnerability-free.

### Security verdicts

Report each security check as:

```text
PASS          control implemented and tested with evidence
FAIL          executable security assertion failed
BLOCKED       required security tool, environment, credential, or fixture unavailable
INCOMPLETE    control is designed but not fully tested
NOT_APPLICABLE documented threat-model exclusion
UNSET         required risk level or threshold was not declared
```

Never describe an application as “secure,” “cleared,” or production-approved solely because no security test failed. Report the selected ASVS level, tested controls, untested controls, evidence level, and remaining risk.

### Minimum security test set for the WebSocket gateway

- Untrusted-origin handshake rejection.
- Missing, expired, rotated, and revoked credential rejection.
- Message-level authorization failure.
- Unknown route and message-type mismatch rejection.
- Malformed JSON/schema, oversized message, and injection-payload handling.
- Rate-limit and connection-limit behavior.
- Replay of a side-effecting command and replay of an event.
- Safe error and redacted-log inspection.
- Logout/session-expiry connection closure.
- TLS/WSS verification using the declared trust mode.

## Protocol contract minimum

For every WebSocket or message-protocol proof, test at minimum:

- Valid request
- Valid subscription
- Malformed envelope
- Unknown route
- Route/message-type mismatch
- Correlation fields
- Safe error response
- Progress event
- Completion event and persistence
- Idempotency or retry behavior where applicable
- Duplicate side-effecting command with the same idempotency key
- Idempotency conflict using the same key with different input
- Duplicate subscription request
- Replayed event deduplication using event ID and sequence
- Duplicate task-completion observation
- Reconnect and resynchronization behavior

Use a known protocol client library or a shared, tested framing helper. Invalid envelopes may receive generated error IDs and must not require echoing untrusted fields.

## Asynchronous task invariants

For every progress-producing task or worker, validate:

- At least two intermediate progress transitions
- Final completion persistence
- Completion publication
- Idempotency behavior
- Retry or failure behavior
- Timer or worker release
- Post-completion silence
- Cancellation or expiry behavior when supported

Runtime warnings, orphaned workers, unhandled exceptions, and continuing timers are validation failures even when the final response appears correct.

This file holds the full security standard moved out of `loop.md` in Loop 0.4. Apply the parts that fit the project (for example, the WebSocket checks only for WebSocket apps).
