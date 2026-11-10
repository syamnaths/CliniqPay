# Hospital setup

Status: delivered. Source: requirement.md.

## Flow

- Enter hospital details, room ranges and billing preferences
- Configure services, tariffs and applicable tax
- Configure doctors and payment settings (Medical Staff & Clinical Tariff Agreements)
- Review and save settings

## Validation & Business Rules

1. **Room Types & Range Config Integrity:**
   - Detects all catalog services billed per Day/Hour (e.g. Deluxe Room, General Ward, ICU).
   - Validates that no room number is assigned more than once (zero overlap/duplicates across room categories).
   - Enforces positive integer room numbers where `From <= To`.
   - Checks against hospital room capacity ceiling (`starting_room_number` to `starting_room_number + bed_count - 1`).
   - Detects and reports unassigned room gaps between categories (e.g. 101–130 and 140–199 flags gap 131–139).
   - Reports incomplete capacity coverage if total allocated rooms are fewer than total hospital bed capacity.
   - Dual-layer validation: Real-time interactive client-side status box (green for complete, amber for gaps/incomplete, red for overlaps) + strict server-side POST validation with Django flash messages.

2. **Hospital Logo & Brand Identity:**
   - Interactive 1:1 square canvas cropper with matching pixel viewport coordinates between dashed container and live canvas preview.
   - Dual preview modes: Light mode (for paper receipts) and Dark mode (for digital POS interfaces).
   - Serves verified brand badges across POS Counter, patient tablet displays, and tax receipts.

3. **Hospital Helpdesk & Knowledge Base:**
   - Complete hospital user guide (`/hospital/<slug>/help/`) with instant live search, interactive FAQs, and Section 9 dedicated to Pharmacy Dispensing & Pharmacist role isolation.
   - In-app support incident ticket portal (`/hospital/<slug>/support/`) with voice memo recording, screenshot attachments, and automated technical client environment capture.

4. **Service & Tariff Catalog Bulk CSV & Storage Rack Management:**
   - Bulk CSV Import (`/hospital/<slug>/services/csv/upload/`) and downloadable CSV template (`/hospital/<slug>/services/csv/download/`).
   - Fields supported: `name, department, code, price, tax_percent, billing_unit, storage_location, is_pharmacy_lite`.
   - Distinct Pharmacy-Lite flag separates reception OTC medications from prescription-only hospital drugs.
   - Physical rack coordinates (`storage_location`, e.g., "Rack A-02 / Shelf 1") for fast physical item locating.

5. **Medical Staff & Clinical Tariff Agreements (Doctor Portal & Credentials):**
   - Configures attending physicians with professional courtesy titles (`Dr.`, `Prof. Dr.`, `Surgeon`), medical registration numbers, and percentage or fixed consultation honorarium splits.
   - Dedicated credentials allow doctors to access their own clinical dashboard, managing today's OPD consultation queue and admitted IPD ward rounds.
   - Clinical E-Prescriptions: diagnosis, vitals, dosage frequency (`1-0-1`), and diagnostic lab orders that bridge directly to Pharmacy dispensing and reception billing.
