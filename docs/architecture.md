# CliniqPay technical architecture

Status: agreed stack, planned implementation. The owner confirmed the Python stack on 2026-11-08. No application services, integrations or security controls are implemented yet.

## Stack

| Layer | Choice | Role |
| --- | --- | --- |
| Application | Python and Django, one modular project | Server-rendered web pages, business rules, authentication, internal administration and integration endpoints |
| Interface | Django templates, Tailwind CSS v4 and targeted JavaScript | Public landing page, hospital desk and platform administration; reuse `design-system/theme.css` in a compiled Tailwind build |
| Data | Managed PostgreSQL | Hospital, billing, payment and audit records; Django migrations version the schema |
| Background processing | Celery and Redis | Add when messaging, scheduled reports and retries are implemented; deploy a worker and a single scheduler |
| Documents | Private object storage, provider to be chosen | Receipt PDFs if persistent storage is needed; never expose private files publicly by default |
| Tests | Django test framework or pytest, plus Playwright for browser flows | Choose and configure test runner during implementation; test access controls, calculations and integrations |
| Hosting | Managed Python hosting, managed PostgreSQL and Redis | Provider and region remain undecided; confirm actual cost, operations and data handling before selection |

Use supported stable versions and pin dependencies at implementation time. Node is a build/development dependency for Tailwind and Loop atlas tooling, not the application backend. The landing concept's Tailwind v3 CDN is for preview only; compile Tailwind v4 for the application.

## Application boundaries

- **Public:** Landing page with plan tier selection (Starter, Standard Hospital, Enterprise Chain), hospital enrollment submission, and ROI estimator. Submission creates an `EnrollmentRequest` tagged with the requested plan tier and declared bed capacity.
- **Platform administration:** Authorized CliniqPay staff review enrollment requests filtered by plan tier and status, review requested capacity, and activate tenant workspaces with auto-generated welcome credentials.
- **Hospital workspace:** Tenant-isolated clinic environment (`/hospital/<slug>/`). Hospital administrators configure hospital profile, bed count, closing time, default tax, WhatsApp Cloud API keys, role-based staff members, departmental counters, tariffs, and doctors:
  - **Departmental Tagging:** Services/Tariffs are organized by Department (`OPD / General Consultation`, `Pharmacy`, `Diagnostic Lab`, `Radiology`, `IPD / Nursing Procedures`).
  - **Staff Role & Counter Scope:** Staff members are assigned a role (`Hospital Admin` or `Cashier / Receptionist`) and optionally scoped to specific departmental counters (e.g., `All Counters`, `OPD Desk`, `Pharmacy Counter`, `Lab Desk`).
  - **Medical Staff & Clinical Tariff Agreements:** Doctors are configured with separate courtesy titles (`Dr.`, `Prof. Dr.`, `Surgeon`, etc.), specialties, and % or fixed consultation share splits.
- **Integrations:** Server-side payment (dynamic UPI QR and simulated webhooks) and WhatsApp Cloud API adapters (Meta Cloud API, WABA ID, Phone ID) isolate provider-specific code.
- **Workers:** A worker processes durable, retryable jobs; a scheduler triggers summaries at the agreed cutoff time (e.g. 8:00 PM). Store job state and outcomes so failures can be reviewed and retried.

Suggested Django app boundaries: `accounts`, `setup_hospital`, `enrollment`, `billing`, `payments`, `receipts`, `summary`, and `platform_admin`. Use one deployable application initially; separate services only when justified by actual needs. All styling bundles self-hosted Tailwind 3.4.17 (`static/vendor/tailwind.min.js`) eliminating external CDN runtime dependencies.

### Medical Billing Units & Multi-Counter Scope

1. **Intelligent Tariff Units:** Services configured in `setup_hospital.models.ServiceItem` support domain-specific healthcare units:
   - `count`: Standard units / counts (procedures, consumables)
   - `hour`: Hourly tariffs (e.g. Daycare rooms, Observation bed hours, Oxygen hood hourly rates)
   - `day`: Daily tariffs (e.g. ICU bed per day, General ward room per day)
   - `session`: Per session tariffs (e.g. Dialysis session, Physiotherapy session, OT block)
   - `test`: Per test (e.g. CBC, Lipid Profile, USG Abdomen)
   - `visit`: Consultation visits (e.g. Follow-up visit, Specialist consultation)
   - `strip`: Pharmacy strips / blister packs

   `billing.models.BillItem` persists the unit at checkout (`formatted_quantity` provides human-readable context e.g. `2 days`, `3 hrs`, `1 visit`), ensuring itemized tax receipts and WhatsApp PDFs render intelligible medical line items.

### Front Desk Operations, Inpatient (IPD) Admission & Seamless Plan Upgrade

### Clinical Operations & Doctor Portal (Medical Staff & E-Prescriptions)

1. **Doctor Credentials & Medical Staff Agreements:**
   - Doctors maintain professional titles (`Dr.`, `Prof. Dr.`, `Surgeon`), medical registration numbers, and clinical fee splits (% or fixed honorarium).
   - Dedicated user authentication allows doctors to log in and be routed straight to their **Clinical Portal** (`/doctor/<slug>/`).
2. **Clinical Queues (OPD & IPD Ward Rounds):**
   - **Outpatient Consultation Queue:** Shows registered walk-ins and consultation appointments assigned to the doctor today.
   - **Inpatient Ward Rounds:** Live census of admitted patients occupying ward beds under this consultant's care, displaying admission duration and bed numbers.
3. **Clinical Dossier & Digital E-Prescriptions:**
   - Recording vitals (BP, Pulse, Temp, SpO2, Weight), chief complaints, and clinical diagnosis.
   - Prescribing medications with dosage frequency (e.g. `1-0-1`, `1-1-1`), timing (Before/After food), and duration.
   - Prescribing diagnostic investigations (Lab / Imaging).
   - Active prescriptions flow seamlessly into the **Pharmacy Terminal** for 1-click batch dispensing and the **Reception Counter** for billing.

#### 1. Plan-Tiered Inpatient (IPD) Capability
- **Plan 1 (Starter Clinic):** Strictly Outpatient (OPD) and Pharmacy quick-cashiering. Inpatient enrollment, admission checkboxes, bed tracking, and IPD history summaries are **completely removed/hidden** from the Starter interface to keep day-clinic operations fast and zero-clutter.
- **Plan 2 (Standard Hospital):** Unlocks Front Desk Receptionist role, Patient UHID Generation (`P1001`), Inpatient (IPD) Admission checkbox with confirmation, Room/Bed assignment, running inpatient visit ledger, and Discharge action with confirmation.
- **Plan 3 (Enterprise Chain):** All Standard IPD features plus Multi-Branch patient registry, Emergency Casualty triage desk, and Operation Theatre & Surgery (OT) billing.

#### 2. Upgrade-Friendly Architecture (Starter $\rightarrow$ Standard $\rightarrow$ Enterprise)
- **Zero Data Loss / Zero Schema Migration on Upgrade:** All patients, bills, and payments created while a clinic was on the Starter plan are stored in the same unified schema. When the hospital upgrades to Standard or Enterprise:
  1. The hospital’s existing patients immediately acquire full Inpatient admission capability, running summaries, and history search without any data conversion.
  2. Prior bills retain their original OPD status while future bills can be tagged as Inpatient (`ipd`).
  3. Patient IDs (UHIDs) that were assigned automatically during Starter continue sequentially without gaps.
  4. New departments (`ipd`, and later `emergency`, `ot_surgery`) instantly appear in the catalog and billing counter.

#### 3. Inpatient Admission & Discharge Lifecycle
- **Physical Ward Cadres & Room Number Ranges (`HospitalWardCadre`):**
  - Standard and Enterprise hospitals configure their bed layout once in Hospital Settings (e.g., *Deluxe Rooms: Room 201–208*, *ICU: Bed 1–6*, *General Ward: Bed 101–115*), directly linked to the respective daily tariff item.
  - **Room Types & Range Config Integrity & Gap Validation:**
    - Detects all catalog services billed per Day or Hour (e.g., Deluxe Room, General Ward, ICU).
    - Validates that no room number is assigned more than once (zero overlap or duplicate room numbers across room categories).
    - Enforces positive integer numbers with `From <= To`.
    - Checks against hospital room capacity ceiling (`starting_room_number` to `starting_room_number + bed_count - 1`).
    - Detects and alerts on unassigned room gaps between categories (e.g. 101–130 and 140–199 flags gap 131–139).
    - Checks whether all hospital rooms are assigned if all beds are active.
    - Features real-time client-side interactive feedback (green for complete allocation, amber for gaps/incomplete allocation, red for overlaps) plus server-side validation.
  - On the Billing Counter, selecting a cadre displays an interactive visual bed grid:
    - **Green Badges:** Available physical beds.
    - **Red Badges:** Currently occupied by an active inpatient (`[OCCUPIED]` with disabled selection to prevent duplicate bed assignment).
  - Clicking an available bed automatically pre-selects the linked IPD tariff rate and populates the room identifier without manual typing or service catalog searching.
- **Discharge Action with Confirmation:**
  - Front desk can click **"Discharge Patient"** which opens a safety confirmation modal showing final bill status and unbilled balance warnings.
  - Once confirmed, `patient.is_inpatient` is set to `False`, `discharge_date` is recorded, and the bed is released, closing the running admission ledger cleanly.

#### 4. Patient Registry & Visit History (Replacing "Recent Bills")
- The right-hand column replaces "Recent Bills Generated" with a dynamic **"Patient Registry & Visit History"**:
  - Live search input filters patients instantly by **Name**, **Phone**, or **Patient ID (UHID)**.
  - Patient cards display status pills: **Active Inpatient (Room #)** vs **Outpatient (OPD)**.
  - 1-click on any patient selects them in the billing desk, loads their running summary, and reveals their historical visits.

## Data and access

The agreed first-release tenancy and deployment decision is documented in [database architecture](database-architecture.md): one modular Django application and one shared, tenant-aware PostgreSQL database. Microservices are not planned for the first release.


Associate hospital-owned records with a hospital, and verify membership and permission on every read and write, including APIs, background jobs, exports and file downloads. Database constraints should prevent cross-hospital references. Consider PostgreSQL row-level security as defense in depth once connection roles and bypass rules are designed; it does not replace application authorization. Test both allowed and denied access across two hospitals.

Keep platform-admin privileges separate from hospital roles, require strong authentication for privileged accounts, and audit sensitive actions with actor, hospital, action, time and outcome. Define break-glass access and retention with the owner. Avoid storing clinical details that billing does not need. Encrypt in transit, restrict secrets and use private storage. Determine backup retention, restore testing, data location and legal requirements before production.

Use decimal or integer minor units for money, never floating-point calculations. Persist the tax, tariff and doctor-share inputs used at billing time; corrections and reversals should remain traceable. Final tax and share rules require product and professional review.

## Integration flows

**Payment:** Create a provider-supported exact-amount QR tied to a bill and hospital's configured merchant account. QR creation does not confirm payment. Verify provider callbacks with the provider's documented mechanism, validate account, amount and identifiers, record events idempotently, and reconcile missing or delayed notifications. Distinguish pending, confirmed, failed and explicitly recorded cash; handle duplicates, expiry, reversals and disputes. Provider capabilities and settlement model must be confirmed.

**WhatsApp:** Queue an approved message or receipt for the intended number; record provider message ID and known delivery state. Apply retries carefully and avoid duplicate sends. Define consent, template approval, failed delivery and opt-out behavior with the selected provider. Do not report a message delivered without an appropriate provider event.

**Daily summary:** Aggregate by hospital and reporting period in the hospital's configured timezone; default timezone and 8 PM schedule are proposed by the brief. Record scheduled execution and send outcomes, make retries idempotent, and show what data is included. Doctor-share calculation rules remain open.

## Deployment and operations

Separate development, staging and production configuration and credentials. Use environment-based secret injection; never commit credentials. Run migrations as a controlled deploy step, collect static assets and build Tailwind for release. Deploy web, worker and scheduler processes appropriate to the hosting provider. Configure HTTPS, secure cookies, allowed hosts, CSRF protection, least-privilege database access, logs with sensitive data redacted, monitoring and alerts. Verify backups and restore procedures. Payment webhooks must be reachable over HTTPS and authenticated as specified by the provider. No deployment or purchasing is authorized by this document.

## Decisions still needed

Enrollment review and activation; roles and platform-admin access; exact schema and retention; hosting/provider/region and budget; payment merchant and settlement model; WhatsApp provider and consent; tax and doctor-share rules; reporting schedule and retry policy; backups and recovery objectives. Implementation must validate each decision and provider behavior before presenting it as a working feature.
