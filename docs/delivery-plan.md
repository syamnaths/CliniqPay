# CliniqPay product and delivery plan

**Status:** Agreed delivery direction; planning and prototyping remain to be completed. This document records the conversation and links to the source of truth for each area. It does not assert that product features, integrations or security controls exist.

## Objective and scope

Build the complete agreed first-release workflow in `requirement.md` for small Indian hospitals, nursing homes, clinics and diagnostic centres, on desktop and Android tablet browsers. The planned areas are landing-page enrollment, CliniqPay master administration, hospital setup, billing, payment tracking, WhatsApp receipts and daily summaries. The requirements express desired outcomes; implementation details and integrations still require validation. Future changes to scope must update the brief and atlas.

Read with `docs/project-brief.md`, `docs/architecture.md`, `docs/database-architecture.md`, `design-system/README.md`, and the atlas at `docs/app-map/index.html`. The atlas is the shared map of product flows and delivery status. `HANDOFF.md` contains the current checkpoint.

## Delivery model

1. **Map the full product and user journeys.** Review and expand the planned atlas for each role, including entry points, permissions, normal paths, errors and recovery. Record dependencies and open decisions. The current high-level maps are a starting point, not a completed detailed design.
2. **Prototype critical connected journeys.** Create a coherent, reviewable prototype that covers each user and the transitions between them. Prioritize the critical path and decision-heavy screens; do not wait for every minor screen to be polished. Use the landing page concept and the design system as visual references; apply `design-system/interaction-guidelines.md` to relevant prototype and implementation states.
3. **Review the prototype and decisions.** Walk through each role, document corrections and agree on decisions affecting access, billing and integrations. Update the atlas and track specs to match. Prototype approval is a design and workflow checkpoint, not evidence of implemented functionality.
4. **Build one complete slice at a time.** Take the next dependency-ready atlas map, confirm its acceptance criteria, implement it with meaningful behavior and boundary tests, inspect representative responsive views, review security and record evidence. Update the map and handoff as specified by Loop. Follow the order in the atlas unless dependencies or an owner-approved change require a documented reorder.
5. **Verify the complete release.** Test the connected workflows, real integration behavior and operational recovery before seeking approval to deploy or publish. No feature or release is delivered solely because the prototype exists.

Design continues during implementation for states and details discovered by testing. Update the map and prototype when a material workflow changes; do not silently diverge from the agreed reference. No timeframe, staffing commitment, price or budget is established by this plan.

## Roles and prototype journeys

| Role | Critical journey to map and prototype | Decisions or checks |
| --- | --- | --- |
| Hospital applicant | Open landing page → select plan tier (Starter, Standard, Enterprise) & declare bed count → enter clinic & administrator details → submit → see status | Plan-tier fit, bed capacity, validation, duplicate submissions, confirmation and activation policy |
| CliniqPay platform administrator | Sign in → filter requests by plan tier and status → review hospital capacity & bed count → approve/activate → inspect audit trail & copy welcome credentials | Plan allocation, approval vs automatic activation, rejection and suspension, privileges and access to hospital data |
| Hospital administrator | Enter an authorized hospital workspace → configure hospital details (beds, closing time, default tax, WhatsApp API) → organize tariffs by Department → configure doctor roster with courtesy titles & cuts → manage staff with departmental counter scope | Departmental tariff grouping, counter assignment, roles and credentials, tax treatment, doctor-share rules and provider setup |
| Cashier / billing staff | Identify patient → view departmentally scoped tariffs & consultant → add services → review bill → record cash or present UPI QR (with live patient counter display) → complete receipt | Counter department scope, validation, corrections, pending and failed payments, customer display sync |
| Owner / authorized report recipient | Review daily cash, UPI, doctor shares, departmental splits, and outstanding amounts → receive 8:00 PM WhatsApp summary | Departmental collections, schedule, timezone, corrections and failed delivery |
| Patient | View billing details on secondary counter display → scan exact dynamic QR → receive itemized WhatsApp receipt | Live bill inspection, message consent, delivery failure, minimum necessary information |

These are working role descriptions, not a final permissions matrix. A person may hold more than one role; access must be explicitly assigned and tested. Provider and workflow behavior must be confirmed before it is described as operational.

## Prototype boundaries

- Clearly label the experience as a prototype. Use fictional hospitals, patients, phone numbers and transactions; do not collect or transmit real patient data.
- Simulate enrollment, approvals, QR payment, callbacks and WhatsApp delivery. Never describe a simulated payment as real or a simulated message as delivered. Use non-scannable illustrative payment graphics and clearly label them.
- No live provider credentials, real payment collection, production integrations or actual messages are needed for the prototype. Keep it isolated from production resources.
- Show key empty, loading, validation, success, pending, failure and permission states where they affect decisions. Include cancellation and recovery paths.
- Check the prototype on representative desktop and tablet sizes, plus phone widths where relevant; inspect navigation, readability, keyboard use and visible focus. Record what was reviewed and any blockers.
- Existing `Landing page concept/` is a visual reference, not an approved production page. Its sample claims, testimonials, certifications, prices and placeholder actions require verification before use.

## Implementation slices and proof

The current atlas puts enrollment first, followed by platform administration, hospital setup, billing, payment, receipts and daily summary; release comes last. The exact order and dependency details remain subject to mapping the connected prototype and approval of material decisions. Where two user roles share a journey, deliver the smallest coherent end-to-end behavior permitted by the dependencies; record interim limitations without calling an incomplete flow delivered.

For each slice:

1. Refine its atlas map and track: inputs, authorization, defaults, transitions, failure paths and observable acceptance criteria.
2. Implement with tenant-aware access controls, traceable financial changes and provider boundaries appropriate to the slice. Avoid claiming unimplemented integrations.
3. Run meaningful unit and integration tests, including cross-hospital denial and relevant failure and duplicate-event paths. Verify the interface in a browser when visual; inspect console and page errors and record skipped checks.
4. Perform the Loop design, security and applicable legal review; fix agreed findings and verify again. Record evidence and limits, update source references and mark only the verified map delivered.
5. Update the handoff and proceed to the next dependency-ready map. No production deploy or publication is implied.

## Release readiness

Before real hospital use, verify the complete journey from enrollment through daily reports with representative roles and two hospital accounts. Test authorization and tenant isolation across requests, jobs, reports and downloads; payment callback authenticity, idempotency and reconciliation; messaging consent, delivery and retry behavior; financial calculations and corrections; responsive access and failure recovery. Confirm provider onboarding and costs, privacy and legal review, production secrets, monitoring, backups and tested restores. Record remaining issues, their owner and impact; obtain owner approval for production deployment and any publication requiring it. These are planned checks, not claims of compliance.

## Decisions to resolve

- Hospital enrollment approval, activation, rejection and suspension.
- Role permissions, administrator access to hospital data, staff onboarding and audit visibility.
- Patient and billing data collected; retention, deletion, hosting region and recovery objectives.
- Payment provider, hospital onboarding, settlement model and verification behavior.
- WhatsApp provider, consent, templates, charges and message delivery states.
- Tax treatment, doctor-share calculations, bill corrections and outstanding balances.
- Daily summary recipients, timezone, scheduling and retry policy.
- Hosting, production plan and cost; logo SVG and final brand colors.

Resolve each at the relevant design checkpoint; do not invent approval or claim a provider capability before it is verified.
