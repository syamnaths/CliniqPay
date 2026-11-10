# Quick billing & Pharmacy Dispensing

Status: delivered. Source: requirement.md.

## Flow

- Find or enter patient details
- Select services, consultation, procedures, or pharmacy medications
- Dedicated Pharmacist Terminal (`/billing/<slug>/pharmacy/`) for Standard/Enterprise tiers with mandatory Batch Number and Expiry Date (MM/YY) per line item
- Review itemized charges, batch numbers, and applicable tax
- Create bill, auto-assign next serial invoice number, and present amount due

## Verification & Architecture

- `HospitalStaff.Role.PHARMACIST` with department scope restricted solely to `['pharmacy']`
- Counter scope UI auto-hides for Pharmacist and Housekeeping roles
- Mandatory `batch_number` and `expiry_date` validation on pharmacy dispensing line items
- Starter tier retains `Pharmacy-Lite (OTC)` direct counter dispensing; Standard and Enterprise tiers enable dedicated Pharmacist user accounts and regulatory batch/expiry tracking.
- Dedicated `MedicineBatch` model with manufacturer batch number, expiry date (`MM/YY`), stock quantity, and physical rack coordinates (`rack_location`).
- Bulk inward medicine CSV import (`/billing/<slug>/pharmacy/csv/upload/`) with downloadable sample template (`/billing/<slug>/pharmacy/csv/download/`).
- Active staff role display badge indicators across all desktop/tablet headers (`admin`, `cashier`, `pharmacist`, `housekeeping`).
