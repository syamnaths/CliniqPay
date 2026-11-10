# Project start

Name: CliniqPay
For: Small hospitals, nursing homes, clinics and diagnostic centres in India
First release must: Provide a lightweight billing and cashier desk for bills, payment tracking, WhatsApp receipts and daily summaries.
Platform: web
Stack: Python, Django, Django templates, Tailwind CSS v4, PostgreSQL; Celery and Redis for background work
Languages: en
Template page: reference/hospital-management-2048w.webp

## Features
- Quick billing: Select patient and services > review taxes and total > create bill
- Payment collection: Select bill > display exact-amount UPI QR or record cash > verify payment > show status
- WhatsApp receipts: Select receipt > confirm patient number > send receipt > track delivery status
- Daily summary: Review cash and UPI collections > review doctor shares and outstanding balances > send daily summary
- Setup: Configure hospital details, services, tariffs, doctors and payment settings > review setup

## Constraints
- Support desktop and Android tablet browsers; use the brand guide and design system.
- Payment verification, WhatsApp delivery, tax rules and scheduled reports require appropriate integrations and validation.

## Must not
- Mark a payment confirmed without verification or clearly identified manual recording.
