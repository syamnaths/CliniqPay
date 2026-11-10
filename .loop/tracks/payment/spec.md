# Payment collection

Status: delivered. Source: payments/views.py:12.

## Flow

- Open an outstanding bill
- Choose cash or exact-amount UPI QR
- Display dynamic UPI QR generated via merchant integration (Razorpay/Cashfree direct-to-hospital account)
- Receive automated webhook notification and update status to confirmed
- Fallback: Cashier explicitly marks Cash or External UPI with reference/UTR, flagged as manually recorded
- Show confirmed, pending or failed status
- Token-secured live patient-facing counter QR display screen (`payments:counter_display`) for dual-screen/tablet counters with auto-sync and 100dvh responsiveness.

## Implementation Details

- **Settlement Architecture:** Direct hospital merchant account model. CliniqPay does not custody patient funds.
- **Verification:** Only verified PG webhook callbacks transition UPI bills to `confirmed`. Manual cash/UTR entries are recorded with cashier identity and marked unverified settlement.
- **Audit:** All payment attempts, webhook payloads, and manual cashier actions are logged idempotently.
- **Counter Display Security:** Token-authorized (`display_token`) unprivileged read-only view. No settlement or database modifications can be triggered from the tablet screen. Prevents enumeration and session snooping.
