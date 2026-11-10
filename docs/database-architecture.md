# Database and application architecture

**Decision:** For the first release, use one modular Django application and one shared, tenant-aware PostgreSQL database. The owner accepted this direction on 2026-11-08. This is a design decision; no database, isolation policy or application is implemented yet.

## Why this approach

Billing, hospital accounts, payments and messaging have clear module boundaries within one codebase. A single database permits related billing changes to be committed together and keeps initial deployments and operations manageable. Do not introduce independently deployed microservices for the first release. A Celery worker and scheduler, introduced when needed, are separate processes using the same application code; they are not separate services with independent data ownership.

## Hospital tenancy

Each enrolled hospital is a tenant. Hospital-owned records carry a hospital identifier. Application authorization must confirm the authenticated user's active membership, role and hospital on every access, including queries, updates, background jobs, reports, exports and private file downloads. Do not accept an arbitrary hospital ID from the client as proof of access. Apply tenant-aware database constraints to prevent relationships across hospitals.

Platform administrators manage hospital accounts through explicitly assigned permissions. Access to a hospital's operational or patient information requires a separately defined permission and an audit record; master administration does not automatically imply unrestricted data access. Hospital roles, platform permissions, enrollment activation and exceptional access remain product decisions.

PostgreSQL row-level security is a proposed additional safeguard, subject to designing database roles, connection pooling, worker context, privileged access and migration operations. It complements rather than replaces application authorization. Table owners and roles with bypass privileges can bypass policies unless configured appropriately; test real runtime roles and ensure tenant context cannot leak between requests or jobs. The exact policy implementation is not yet approved or implemented.

## Planned data groups

| Group | Examples | Scope |
| --- | --- | --- |
| Platform | Enrollment requests (with plan tier and bed count), hospital account status, platform administrators | Platform-wide, restricted |
| Identity & Access | Users, hospital memberships, role (`admin`, `cashier`, `front_desk`), multi-department scope (`department_scope`: opd, pharmacy, lab, radiology, ipd, emergency, ot_surgery, all) | Identity may span hospitals; membership and permissions are scoped |
| Setup | Services/Tariff catalog (`name`, `department`, `billing_unit` [hour, day, session, test, visit, strip, count], `price`, `tax_percent`), physical ward cadres (`HospitalWardCadre`: name, prefix, number_from, number_to, service_item), doctor roster (courtesy titles & cut rules), payment & WhatsApp settings | Hospital |
| Front Desk & Patients | Patient directory (`name`, `phone`, `patient_id` / UHID e.g. `P1001`, `age`, `gender`, `is_inpatient`, `admission_date`, `discharge_date`, `room_bed_number`), patient search index | Hospital |
| Billing & Inpatient (IPD) | Inpatient (`ipd`) & OPD (`opd`) bills (`bill_type`, serial number `unique_hospital_bill_number`), line items (`billing_unit`, `quantity`, `formatted_quantity`, bed/room charges), attending doctor share calculation | Hospital |
| Payments | Payment attempts, verified provider events, cash records, customer display token, reconciliation | Hospital |
| Messaging and reports | Receipt delivery attempts, 8 PM summaries, scheduled job results | Hospital |
| Audit | Actor, action, affected hospital or record, time and outcome | Restricted; may be platform-wide or hospital-scoped |

These are conceptual groups, not a final schema. Collect only data required for the workflow. Use private object storage for persisted receipt files if needed; authorize downloads against hospital membership and permissions.

## Integrity and operations

- Use database transactions for related financial writes; represent money as decimal or integer minor units. Preserve bill-time pricing, tax and doctor-share inputs.
- Record corrections, reversals and financial actions in a traceable history. Define exact ledger, retention and deletion rules before implementation.
- Verify payment callbacks using the chosen provider's documented method; validate hospital merchant account, amount and identifiers. Store provider events idempotently and reconcile delayed or missing events. Creating a QR does not establish payment.
- Record message and scheduled-job state. Design retries and idempotency to avoid duplicate payment updates and messages; show only delivery states supported by provider evidence.
- Protect secrets and data in transit, restrict database and file access, redact sensitive data from logs, monitor access and failures, and test backup restoration.
- A shared database shares capacity and backup/restore boundaries. One hospital's workload may affect others, and recovering one hospital independently requires additional procedures. Define and test those procedures before production.

## Validation and evolution

Before production, test allowed and denied operations for at least two hospitals, including cross-hospital object references, background work, reports and downloads; test admin privileges, audit events, duplicate callbacks, financial transaction failure and backup restoration. Verify the runtime database role cannot bypass intended safeguards.

Revisit separate databases if a customer or regulation requires stronger isolation, independent recovery or a different data location, or when measured load warrants it. Extract a microservice only when a specific boundary has a demonstrated independent scaling, deployment or ownership need. Migration between tenancy models has cost and should be planned, not assumed to be automatic.

Open decisions: exact schema and constraints, database role and row-level security design, admin permissions and auditing details, retention, hosting provider and region, backup/recovery objectives, tax and doctor-share rules, payment and WhatsApp providers, and enrollment activation.
