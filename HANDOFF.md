# CliniqPay — handoff

## CURRENT RESUME

- **Objective:** Build a browser-based billing and cashier desk for small healthcare providers in India, based on `requirement.md`.
- **Baseline:** Django project with SQLite dev DB. Delivered maps: `workflow`, `enrollment`, `platform-admin`, `setup`, `billing`, `payment`, `summary`, `receipts`.
- **Platform:** Web, intended for desktop and Android tablet browsers. Agreed stack: Python/Django, Django templates, Tailwind CSS v4 and PostgreSQL; Celery and Redis when background work is implemented. One shared, tenant-aware PostgreSQL database with a modular Django application.
- **Atlas:** `docs/app-map/index.html`; source `docs/app-map/atlas-data.mjs`. 11 maps: 8 delivered, 0 building, 3 planned. Next map to build is `release` (Store & production readiness checklist).
- **Checks:** Django unit tests for all apps passed (40/40 tests). Atlas build and contract tests passed with zero errors (`npm run atlas:check`).
  - Landing Page Hero & Social Proof Enhancements:
    1. Connected **"Start Your Free Setup"** Hero Form directly to live trial registration (`/enrollment/submit/`) with plan tier dropdown (Starter ₹1,999/mo, Standard ₹3,999/mo, Enterprise ₹6,999/mo) and automated reference token issuance.
    2. Replaced the static side-by-side POS mockup with an interactive 3-slide **Real-World Deployment Hero Carousel** showcasing:
       - **Slide 1 (Starter Clinic):** Arogya Daycare Clinic (Solo practice, OPD quick tokens, zero-fee dynamic UPI, WhatsApp bills).
       - **Slide 2 (Standard Hospital):** City Care Hospital (20 beds, room turnover lifecycle Occupied/Cleaning/Available, dedicated pharmacy dispensing terminal).
       - **Slide 3 (Enterprise Chain):** Apex Multi-Specialty Hospital (50 beds, cardiology diagnostics, department-scoped cashiering, platform triage).
    3. Replaced "Trusted by Medical Administrators" with **"What Founders Have to Say" Interactive Carousel** featuring:
       - **Aravind** (Forward Deployed Engineer · Co-Founder) on eliminating receptionist cashier discrepancies.
       - **Syam** (Forward Deployed Designer · Co-Founder) on emergency-optimized typography, contrast, and cognitive load reduction.
       - **Jithin James** (Technical Architect · Co-Founder) on sovereign zero-fee direct-to-bank settlements and ABDM longitudinal tenant isolation.
    4. Removed the "Watch 60-Sec Demo Video" button. Atlas build and contract tests passed with zero errors (`npm run atlas:check`).
  - Landing Page Full Interconnection & Supplementary Pages:
    1. Audited and eliminated all 24 dead `href="#"` links across the SaaS landing page (`enrollment/templates/enrollment/landing.html`).
    2. Wired primary header navigation and footer quick links directly to active landing sections (`#features`, `#comparison`, `#workflow`, `#roi-calculator`, `#pricing`, `#faqs`, `#enrollment-form`).
    3. Created and routed **Statutory Terms of Service & ABDM Compliance** (`/terms/` → `legal_terms.html`).
    4. Created and routed **Enterprise Security, Encryption & DPDP Standards Whitepaper** (`/security/` → `security_whitepaper.html`).
    5. Created and routed **Live System Status & Infrastructure Health** (`/status/` → `system_status.html`).
    6. Wired floating and inline "Chat with Billing Expert" CTAs directly to official WhatsApp integration. Atlas build and contract tests passed with zero errors (`npm run atlas:check`).
  - Configured project for 1-click **Render** cloud deployment:
    1. Added `render.yaml` defining web service (`gunicorn cliniqpay.wsgi:application`) and PostgreSQL database in the Singapore region (low latency to India).
    2. Added `build.sh` build script handling dependency installation, WhiteNoise static assets collection (`collectstatic`), database migrations, and automatic initial demo seeding via `python manage.py seed_demo_data`.
    3. Updated `cliniqpay/settings.py` with dynamic `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `dj-database-url` PostgreSQL database configuration, and WhiteNoise compressed static storage.
    4. Updated `requirements.txt` with `gunicorn`, `whitenoise`, and `dj-database-url`. Atlas build and contract tests passed with zero errors (`npm run atlas:check`).
  - Database Cleaned & Reset for Showcase: Removed all extraneous test accounts, mock patients, and test invoices while preserving the master platform administration account (`admin`).
  - Provisioned 3 clean showcase accounts covering all three subscription tiers with realistic sample data:
    1. **Starter Plan:** Arogya Daycare Clinic (`arogya-daycare`) — OPD Quick Billing, Doctor consultation queue, active diagnosis notes.
    2. **Standard Plan:** City Care Hospital (`city-care`) — Inpatient bed tracking, Room turnover lifecycle (Occupied/Cleaning/Available), Dedicated Registered Pharmacist Terminal with Batch & Expiry tracking, Doctor e-prescriptions.
    3. **Enterprise Plan:** Apex Multi-Specialty Hospital (`apex-hospital`) — High-volume multi-department clinical care, Cardiology & Neurology consultants, executive suites, and Platform Admin support incident ticket. Atlas build and contract tests passed with zero errors (`npm run atlas:check`).
  - Integrated **YouPI-PG** (self-hosted, zero-fee sovereign UPI gateway) with complete test/sandbox version:
    1. Built `YoupiPaymentGateway` service (`payments/services/youpi.py`) supporting live YouPI Core API session creation with automatic zero-dependency high-fidelity Sandbox fallback.
    2. Implemented HMAC-SHA256 authenticated webhook receiver (`/payments/<slug>/youpi/webhook/`) verifying signatures against `X-Gateway-Signature` and deduplicating deliveries with `X-Gateway-Delivery-Id`.
    3. Added 1-click test observer simulator (`/payments/<slug>/<bill_number>/youpi/test-simulate/`) for instant developer/sandbox verification directly from the checkout desk.
    4. Added gateway provider configuration in Hospital Settings allowing clinics to toggle between Direct VPA and YouPI-PG with custom API URL, merchant UUID, and webhook secret. Atlas build and contract tests passed with zero errors (`npm run atlas:check`).
  - Remediated critical security and integrity findings from `doubts.md`:
    1. Tenant Isolation & Least Privilege: Limited super-admin rights in `get_staff_role` strictly to `is_superuser`; standard `is_staff` users no longer receive blanket cross-tenant admin access. Added server-side role restrictions on Pharmacy Dispensing (`PHARMACIST` or `ADMIN`) and Doctor Portal (`DOCTOR` or `ADMIN`).
    2. Plaintext Credentials Elimination: Removed `raw_password` field from `HospitalStaff` database model and views; eliminated predictable fallback password (`doctor123`) using cryptographically secure tokens; replaced plaintext Credentials modal with an administrative `Reset Password` modal (`reset_staff_password`) backed by Django's PBKDF2 hashing.
    3. Payment Integrity & Idempotency: Protected `record_cash` and `confirm_upi` against duplicate submissions and state overwriting (`bill.status == PAID` redirects immediately to receipt). Added strict cash validation rejecting tendered amounts below bill total (`cash_tendered < bill.total_amount`).
    4. Inpatient Discharge Multi-Bill Safety: Hardened inpatient discharge check during payment settlement; patients are only discharged and their rooms released to housekeeping once all outstanding stay charges are settled in full (`patient.bills.filter(status=UNPAID).exclude(id=bill.id)`).
    5. Clean Tax Receipts: Removed hardcoded dummy GSTIN fallback (`29ABCDE1234F1Z5`) from receipts; invoices render GSTIN only when configured by the hospital. Atlas build and contract tests passed with zero errors (`npm run atlas:check`). Implemented Duplicate Bill Warning confirmation modal when exact previous invoice amount matches; added `Housekeeping` staff user role with direct redirect to dedicated Housekeeping Dashboard (`/hospital/<slug>/housekeeping/`); added real-time room cleaning and sanitization turnover lifecycle (`RoomBedStatus`: available, occupied, cleaning) triggered automatically on inpatient discharge or room transfer; locked cleaning beds from cashier admission until marked clean by housekeeping; provided 1-click room sanitization with instant AJAX feedback. Implemented discharge workflow safeguard where confirming discharge generates the final stay invoice, keeps the patient admitted until payment is completed, and only confirms discharge and bed turnover once the final bill is settled in full. Upgraded "Service & Tariff Catalog" UX with a responsive modern flex-card CSS layout replacing the flat table layout; added dedicated "Miscellaneous & Ad-Hoc Charges" (`misc`) tariff category in Service Catalog and Quick Billing Counter with custom inputs (Description, Amount, Qty, Tax) for unknown/unforeseen fees; implemented official Hospital Brand Logo upload section with interactive 1:1 square ratio icon mark cropper with matching pixel coordinates between dashed viewport and live canvas preview, rounded borders for inner logo images across dark mode containers and header navigation (`rounded-lg` on image, `rounded-xl` on outer pill), dual-mode preview (Light/Receipt & Dark POS), media serving, and elevated branding across header navigation, POS counter, patient counter tablet, and printed tax receipts with a "Verified Provider" brand badge. Delivered full end-to-end Hospital Support Desk & Platform Admin Incident Tracking and Resolution system:
  1. Hospital Helpdesk (`/hospital/<slug>/support/` & `/hospital/<slug>/support/<ticket_number>/`) with ticket status tracking, category & priority selector, client environment auto-capture (URL, user-agent, screen resolution), screenshot image attachment, in-browser HTML5 voice memo audio recorder with live waveform and playback, and threaded conversation updates.
  2. Platform Admin Support Center (`/platform/support/` & `/platform/support/<ticket_number>/`) with high-level triage metrics (Open, Urgent, Waiting Hospital, Resolved), multi-facet filtering (status, priority, category, hospital, keyword search), technical diagnostic dossier inspection, voice note audio player, screenshot lightbox viewer, assignment of engineers, status transitions, official resolution notes recording, public hospital replies, and private internal engineering notes.
  3. Dedicated Pharmacist Role & Pharmacy Dispensing Terminal (`/billing/<slug>/pharmacy/`):
     - Added `PHARMACIST` staff user role restricted to Standard & Enterprise tiers; automatically hides/bypasses Counter / Dept Scope checkboxes in staff modals with scope locked to pharmacy only.
     - Starter Plan retains general reception quick dispensing renamed distinctly to `Pharmacy-Lite (OTC)` across the catalog and cashier counter.
     - Dedicated Pharmacy Dispensing Terminal featuring real-time patient phone search, reserved Doctor Prescription Link space for upcoming Schedule H/H1 regulatory lookup, mandatory line-item **Batch Number** and **Expiry Date (MM/YY)** validation, dynamic invoice total, and right-column live dispensing ledger.
     - Medicine Storage / Rack Coordinates: added `storage_location` and `is_pharmacy_lite` fields to `ServiceItem` and created `MedicineBatch` model with stock quantity, expiry date, and batch number tracking.
     - Dual-Context CSV Bulk Upload & Downloadable Sample CSVs:
       - In Service & Tariff Catalog (Admin Only): `Download Catalog CSV Template` and `Bulk Import Services & Medications` modal restricted strictly to Hospital Administrators.
       - In Dedicated Pharmacy Terminal (Pharmacist & Admin): `Download Inward Batch Template` and `Bulk Inward Medicine Batches` modal for inward batch shipments and stock tracking restricted specifically to Registered Pharmacists and Administrators.
     - Header user role indicators (`admin`, `cashier`, `pharmacist`, `housekeeping`, `doctor`) across POS Cashier, Pharmacy Terminal, Hospital Settings, and Housekeeping headers.
     - Updated Landing page pricing matrix (Starter ₹1,999/mo, Standard ₹3,999/mo, Enterprise ₹6,999/mo) with annual 20% discount toggle; updated feature matrices reflecting Doctor E-Prescription Suite, Inpatient Bed Lifecycle, Pharmacy Terminal, and Patient WhatsApp Dispatch.
     - WhatsApp Message Templates & Notifications Suite: Verified and structured across all 3 key touchpoints:
       1. Patient Tax Invoices & Payment Receipts (`generate_whatsapp_receipt_text`) with bill number, timestamp, amount paid, and direct PDF download link.
       2. Doctor E-Prescriptions (`dispatch_prescription_whatsapp`) with attending consultant, diagnosis, medication breakdown, and pharmacy pickup link.
       3. Daily 8 PM Hospital Revenue & Doctor Payout Reconciliations (`summary_text`) detailing UPI vs Cash totals, outstanding dues, and doctor share breakdowns.
     - In-App Knowledge Base (`/hospital/<slug>/help/` with Section 9 & statutory compliance FAQ), and Flow Atlas track.
  4. Medical Staff & Clinical Tariff Agreements, Doctor Workspace & Clinical Consultation Journey (`/hospital/<slug>/doctor/`):
     - Renamed "Doctor Roster & Share Rules" to "Medical Staff & Clinical Tariff Agreements" across all views, templates, navigation headers, and specs.
     - Added `registration_number` (MCI/SMC council reg) and optional User account binding (`doctor_username`, `doctor_password`) to `Doctor` and added `DOCTOR` to `HospitalStaff.Role`.
     - Built Doctor Portal (`/hospital/<slug>/doctor/`) accessible directly by consultant physicians upon login via `/hospital/<slug>/login/`.
     - Frontdesk Live OPD Token & Queueing Engine:
       - Every outpatient bill assigns a sequential daily token number (`#Tk-01`, `#Tk-02`) per consultant with estimated wait time (`estimated_wait_minutes`).
       - Token call board with real-time status transitions: `Waiting`, `In Consultation / Active`, `Completed`.
       - Automatic real-time background queue polling (`doctor_queue_poll_ajax`) refreshing `OPD Tokens (N)` count, `IPD Rounds (N)` count, and token cards every 4 seconds without reloading the page or disturbing active clinical write pad canvas inputs.
       - 1-click "Call & Attend" immediately engages the patient, loads demographics, and opens the clinical workspace.
       - Token number and estimated wait times printed prominently on patient receipts and checkout slips.
     - Digital Freehand Write Pad Canvas (Touch / Stylus / Mouse):
       - Converted from full-page space consuming card to a focused, responsive pop-up modal dialog (`#writePadModal`) with high-DPI retina scaling, ink palettes (Black, Blue, Red anomaly, Green), stroke thicknesses (Fine, Medium, Bold), eraser, and quick clear controls.
       - Elevated **Typed Clinical Observations & Case Notes** as the primary high-priority clinical workspace on the main page with a spacious, multi-row expandable textarea (`#padTypedNotes`, `rows="6"`), instant sketch attachment badges, and direct 1-click persistence to the patient's permanent longitudinal timeline.
       - 1-click "Save Note to History" serializes typed notes together with attached canvas drawings as base64 images into the patient's permanent clinical timeline.
     - Date-Ordered Patient Case History Timeline:
       - Automatically defaults to Today's history upon login.
       - Dedicated filter toolbar: "Today", "All Dates", "IPD Rounds", plus a custom date picker for retrospective review.
       - Chronological historical feed displaying patient demographics, attending doctor, provisional diagnosis, typed observation notes, and embedded freehand scribbles.
     - Computerized E-Prescription authoring suite: diagnosis, vitals (BP, pulse, temp, weight), chief complaints, optional medication rows (dosage 1-0-1, timing, duration, qty), and clinical advice with interactive "Are you sure about this?" confirmation modal for dietary/advice-only records without pharmaceutical medications.
     - Direct Doctor Prescription bridge to Pharmacy Terminal (`/billing/<slug>/pharmacy/`): Pharmacists see pending doctor prescriptions and click "Load to Dispense" to instantly populate patient demographics, referring consultant, and auto-select all prescribed medications into the line-item table with quantities and batch inputs.
     - Updated Tariff & Catalog labels to generic "Item / Service / Medicine Name *" in dashboard forms so services, lab tests, and medications fit seamlessly.
  5. Dedicated Patient Counter Display Tablet QR for Pharmacy (`/payments/<slug>/display/?counter=pharmacy`) with real-time dynamic QR generation, medicine breakdown, and URL copy banner.
  6. Header navigation integration across Hospital Settings Dashboard, Cashier Counter, Doctor Portal, and Platform Admin Console.
  7. Hospital Platform Knowledge Base & Searchable User Manual (`/hospital/<slug>/help/`): complete onboarding guides for all features (OPD quick billing, IPD discharge safeguards, Housekeeping 1-click room sanitization, Counter display dynamic UPI QR, Tariff catalog & miscellaneous ad-hoc fees, 8 PM daily revenue summaries & doctor payout percentages, hospital branding cropper, support ticket submission), visual operational lifecycle flowcharts, interactive expandable FAQs, and instant client-side search filtering.
  8. UI Polish & Layout Enhancements: Two-row responsive mobile and tablet layout across Hospital Dashboard, Doctor Portal, Cashier Counter, and Pharmacy Terminal headers with clean `lg:` breakpoint split; prevents cramped single-row wrapping on tablet widths (768px-1024px); provides smooth horizontal scroll for navigation actions and quick access controls; global sleek thin 6px scrollbar across all dark and light themes.
- **Next action:** Build `release` (Store & production readiness checklist). Run `node docs/app-map/atlas-status.mjs` for current status.

- **Design update:** `Landing page concept/` is the current visual reference; `design-system/` documents its tokens and v3/v4 distinction. Interaction requirements are documented in `design-system/interaction-guidelines.md`; they are not implemented or verified. Browser visual verification remains outstanding.

## History

- 2026-11-08 — Reviewed and documented interaction, accessibility and financial-state guidance for the prototype and future implementation.

- 2026-11-08 — Documented the agreed atlas-first, prototype-then-incremental delivery approach. No prototype or product implementation was created by this documentation update.

- 2026-11-08 — Owner accepted the modular application and shared tenant-aware database direction; isolation and operational details documented.

- 2026-11-08 — Owner confirmed the Python/Django stack; architecture and platform documentation updated. No application implementation yet.

- 2026-11-08 — Added landing-page enrollment and master administration to the planned atlas.
- 2026-11-08 — Adopted the existing materials into Loop and replaced the generic current-app placeholder with requirement-based planned flows. No product implementation or release performed.
