---
name: Clinical FinTech Precision
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#3d4947'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#6d7a77'
  outline-variant: '#bcc9c6'
  surface-tint: '#006a61'
  primary: '#00685f'
  on-primary: '#ffffff'
  primary-container: '#008378'
  on-primary-container: '#f4fffc'
  inverse-primary: '#6bd8cb'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#006947'
  on-tertiary: '#ffffff'
  tertiary-container: '#00855b'
  on-tertiary-container: '#f5fff6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  title-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
  metric-mono:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system targets clinic owners, hospital financial officers, medical billing administrators, and patients completing high-stakes medical transactions. The interface projects unimpeachable enterprise security, institutional calm, and fluid digital efficiency. It bridges the empathy of medical care with the rigor of cryptographic financial infrastructure.

The aesthetic fuses **Corporate / Modern** structure with **Tonal Glassmorphism** accents:
- **Crisp Structural Discipline:** Deep slate infrastructure, surgical borders, and unambiguous information hierarchy minimize cognitive strain during complex ledger and reconciliation tasks.
- **Biomedical Luminescence:** Dual teal and cyan accents directly echo the logo identity, utilizing soft gradients and subtle glows to designate verified states, action anchors, and transactional confidence.
- **Operational Clarity:** High contrast typography with zero ornamental distraction, paired with specialized semantic statuses for claims, copays, settlements, and conversational billing channels (e.g., WhatsApp payment links).

## Colors

The palette establishes a distinct healthcare-fintech balance:

- **Primary (`#0D9488` with `#00A88F` gradient shift):** The vibrant clinical teal extracted from the logo marks primary interactive states, primary conversion actions, active ledger rows, and verified billing pathways.
- **Secondary (`#0F172A`):** Deep Slate Navy anchors high-tier navigation, executive dashboard toolbars, high-contrast modal headers, and definitive body text. It projects enterprise solidity and banking-grade security.
- **Tertiary (`#10B981`):** WhatsApp Emerald communicates successful payment transactions, live instant-payment messaging flows, automated patient reminders, and positive balance settlements.
- **Neutral (`#F8FAFC` to `#0F172A` range):** The foundation relies on cool slate canvas tones (`#F8FAFC`), crisp pure-white surface cards (`#FFFFFF`), subtle border dividers (`#E2E8F0`), and muted technical captions (`#64748B`).
- **Semantic Accents:** 
  - Overdue / Denied Claim: Crimson (`#EF4444`)
  - Pending Review / Insurance Pre-auth: Amber (`#F59E0B`)
  - Encrypted / Telehealth Sync: Light Trust Mint (`#CCFBF1`)

## Typography

The type system implements a dual-font architecture:

- **Display & Section Headers (`Plus Jakarta Sans`):** Provides approachable, modern geometric clarity with refined terminal shapes that mirror the rounded cross and heart emblem of the logo. Used across page titles, stat rollouts, and primary invoice summaries.
- **Data, Navigation, and Functional Body (`Inter`):** Delivers neutral legibility, tall x-height, and tabular figure support indispensable for complex ledger tables, copay calculations, claims status lists, and audit timestamps.
- **Monospace/Tabular Attributes:** For all currency, transaction hashes, and invoice numbers, utilize `font-variant-numeric: tabular-nums` within `Inter` to maintain strict column alignment across high-density financial spreadsheets.

## Layout & Spacing

The layout model is anchored on an 8pt base grid for dense, information-rich healthcare operations:

- **Desktop (12 Columns):** Fixed fluid containers with a maximum width of 1440px. Gutters set to 24px (`1.5rem`) with 32px outer canvas margins. Sidebars for administrative navigation remain fixed at 260px width, while patient ledger grids dynamically adjust column count.
- **Tablet (8 Columns):** Standardized 16px gutters and 24px canvas margins. Split-view claims adjudication collapses into stacked collapsible panels.
- **Mobile (4 Columns):** Rapid payment links, WhatsApp billing receipts, and patient checkout views drop to 12px gutters (`0.75rem`) and 16px margins (`1rem`), prioritizing edge-to-edge summary cards and thumb-accessible payment CTAs.

## Elevation & Depth

Visual hierarchy uses crisp slate borders, ambient teal tints, and functional white elevations:

- **Base Canvas (Level 0):** Cool Slate (`#F8FAFC`), entirely matte, serving as the backdrop for billing workspaces.
- **Container Panels (Level 1):** Solid `#FFFFFF` surfaces bounded by a hairline border (`1px solid #E2E8F0`) with a diffuse, near-imperceptible shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.05)`.
- **Interactive & Dropdown Cards (Level 2):** Subtle elevation with a tinted ambient spread: `0 10px 15px -3px rgba(15, 23, 42, 0.06), 0 4px 6px -4px rgba(13, 148, 136, 0.05)`.
- **Payment Modals & Overlays (Level 3):** Clean modal scrim using `#0F172A` at 40% opacity with backdrop blur (4px). The modal surface utilizes `0 25px 50px -12px rgba(15, 23, 42, 0.22)` with a crisp top-border accent of 2px clinical teal.

## Shapes

The shape system adopts a roundedness level of `2` (8px standard radius) to balance enterprise rigor with the friendly, rounded aesthetic of the logo mark:

- **Buttons, Inputs, and Form Controls:** Formatted with `0.5rem` (8px) radius, preventing harsh clinical severity while maintaining reliable data-entry alignment.
- **Data Cards and Module Containers:** Use `rounded-lg` (`1rem` / 16px) for softened, contemporary SaaS card silhouettes.
- **Status Tags, Verification Pills, and Avatar Badges:** Full pill radius (`9999px`) to immediately denote metadata, status states, and patient flags.
- **Modals and Patient Payment Sheets:** `rounded-xl` (`1.5rem` / 24px) on top edges for mobile bottom-sheets and dialog containers.

## Components

### Buttons
- **Primary:** Gradient fill transitioning from `#0D9488` to `#00A88F`, crisp white text (`#FFFFFF`), font weight 600, 8px border radius, subtle teal glow shadow on hover (`0 4px 14px 0 rgba(13, 148, 136, 0.35)`).
- **Secondary Enterprise:** Slate Navy outline (`#0F172A`) or surface (`#F1F5F9`) with `#0F172A` text, 1px border (`#E2E8F0`), flat elevation.
- **WhatsApp Direct Action:** Solid emerald fill (`#10B981`) with integrated chat icon, white text, designated specifically for dispatching payment links or patient billing conversations.

### Inputs & Form Fields
- Height 44px for high touch accuracy. Neutral state: `#FFFFFF` surface with `1px solid #CBD5E1`.
- Focused state: Border transitions to `#0D9488` with a 3px outer ring of `#0D9488` at 15% opacity (`ring-teal-100`).
- Integrated currency prefix and format masks with tabular monospace numerals.

### Data Cards & Billing Widgets
- Crisp white background, 16px rounded corners, 1px border `#E2E8F0`.
- KPI summary cards feature a 3px horizontal status indicator along the top edge or an icon badge set in a 10% tint container (e.g., `#CCFBF1` background with `#0D9488` icon).

### Chips & Badges
- **Paid / Settled:** `#ECFDF5` background, `#047857` text, pill shape, subtle emerald dot indicator.
- **Pending / Insurance Claim:** `#FFFBEB` background, `#B45309` text.
- **Overdue / Failed:** `#FEF2F2` background, `#B91C1C` text.
- **WhatsApp Verified:** `#D1FAE5` background, `#065F46` text.

### Tables & Ledgers
- Sticky header in `#F8FAFC` with uppercase 11px slate typography (`#64748B`).
- Clean alternating hover states using `#F8FAFC`.
- Action cell aligns right with subtle secondary icon buttons (`#64748B` transitioning to `#0D9488`).
## Implementation clarification

The concept's actual Tailwind v3 configuration uses `rounded-lg` = 8px and `rounded-xl` = 12px. The earlier shape prose describes 16px and 24px instead; use the actual preview values until the visual direction is revised. The shared Tailwind v4 tokens and product guidance are in `../design-system/`. The concept is a visual prototype; its claims, testimonials and interactive flows are not evidence of implemented capabilities or certifications.
