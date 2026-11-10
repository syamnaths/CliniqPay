# CliniqPay master administration

Status: delivered. Source: requirement.md, platform_admin/views.py.

## Flow

- Sign in as an authorized platform administrator
- Review enrolled hospitals and enrollment requests
- View and manage hospital account status
- Triage and resolve hospital support incidents (`/platform/support/`)
- Inspect technical client dossiers, play voice memo audio explanations, view full-size screenshots, and assign engineers
- Transition ticket status (`open`, `in_progress`, `waiting_hospital`, `resolved`, `closed`), log resolution notes, and post public replies or private internal notes
- Quick reporter contact actions (1-click phone dialer, WhatsApp chat, direct pre-filled email)

## Validation & Business Rules

1. Master console access restricted to platform staff / superusers (`is_platform_admin`).
2. Dual-mode communication: public responses trigger hospital notification; private internal engineering notes remain shielded from hospital views.
3. Live status and engineer assignments reflect instantly across support queues and ticket workspaces.
