# WhatsApp receipts

Status: delivered. Source: receipts/views.py:10.

## Flow

- Open bill and payment receipt
- Confirm recipient phone number and receipt details
- Dispatch itemized GST receipt PDF via WhatsApp Cloud API / BSP
- Display delivery status (queued, sent, delivered, failed) with retry option

## Implementation Details

- **Sender & Identity:** Central CliniqPay verified business number clearly identifying the issuing hospital.
- **PDF Delivery:** Rendered PDF / printable view uploaded or served via time-limited secure link (`receipts:view`).
- **Privacy & DPDP:** Patient phone number sanitized with 10-digit Indian mobile validation; delivery logs retained in `WhatsAppReceiptLog`.
