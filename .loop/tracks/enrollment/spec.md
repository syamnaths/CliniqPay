# Hospital enrollment

Status: planned. Source: requirement.md and owner request.

## Flow

- Visit the CliniqPay landing page
- Enter hospital and administrator details
- Submit enrollment and receive confirmation (status: `pending_review`)
- Track review or activation status
- Platform administrator reviews application, approves, and activates 7-day trial

## Implementation Details

- **Model:** Hospital enrollment request records hospital name, address, contact person, phone, email, and proposed admin credentials.
- **Access & Isolation:** Submissions are public; platform admin review requires master authentication. Enrolled hospital accounts are created as isolated tenants.
- **Audit:** Record applicant IP, submission timestamp, review decision, reviewer ID, and activation event.
