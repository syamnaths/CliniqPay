# CliniqPay project brief

Source: `requirement.md`. The product is a lightweight browser-based billing and cashier desk for small healthcare providers in India, intended for desktop and Android tablets. Planned capabilities include service-based billing, cash and exact-amount UPI collection, payment verification, WhatsApp receipts, and daily collection, doctor-share and outstanding-balance summaries. Configure hospital, service, doctor and payment details before use.

The supplied reference image guides visual character; `design-system/` and `Brand assets/BRAND-STYLE-GUIDE.md` adapt it to the CliniqPay identity. The logo SVG and official color values remain outstanding.

The agreed stack is Python and Django, Django templates, Tailwind CSS v4, PostgreSQL, and Celery with Redis when background work is implemented. See `docs/architecture.md`. Hosting, storage, provider selection, tax rules, payment verification, doctor-share calculation, scheduling and delivery behavior remain to be decided. Pricing and sales claims in the requirements are proposed product assumptions. No implementation or integration is currently verified.

## Enrollment and platform administration

Hospitals enroll through the CliniqPay landing page with selected plan tier (Starter, Standard Hospital, Enterprise Chain) and bed count. An authorized CliniqPay platform administrator acts as the master administrator for enrolled hospital accounts, reviewing enrollments filtered by plan tier, verifying bed scale, and activating tenant workspaces with credentials. Hospital staff work within their own hospital workspace with departmental counter scopes (OPD, Pharmacy, Lab, IPD). Define approval versus automatic activation, account controls, administrator roles and permissions, any access to hospital operational data, and detailed audit and security rules before implementation. Enforce tenant isolation and record administrative actions.

## Database architecture

The agreed first-release design is one modular Django application with a shared, tenant-aware PostgreSQL database; independently deployed microservices are not planned. Hospital isolation, access boundaries, audit and recovery requirements are detailed in [database architecture](database-architecture.md). Exact roles, schema and row-level security implementation remain open.

## Delivery approach

Map the full product and critical user journeys, create a connected simulated prototype for review, then develop and verify dependency-ready atlas slices. See [delivery plan](delivery-plan.md).
