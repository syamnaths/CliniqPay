# CliniqPay brand style guide

**Version 1.0 · Working guide**

This guide interprets the existing CliniqPay logo and the product brief. The logo artwork and colors are provisional until the replacement SVG is supplied. The color values below are approximations sampled from the current raster master, not original brand specifications.

## Brand foundation

**What we do:** CliniqPay is a simple digital billing and cashier desk for small healthcare providers. It helps staff prepare bills, record collections, share receipts and understand daily cash flow.

**Who we serve:** Owners, doctors and front-desk staff at small hospitals, nursing homes, clinics and diagnostic centres in India.

**Positioning:** A clear, approachable money desk for healthcare teams that need to get on with patient care.

**Brand promise:** Make everyday billing and collections easier to understand and manage.

**Personality:** Calm, clear, dependable, practical and welcoming. The brand should feel at home at a busy hospital counter, without looking clinical or intimidating.

**Suggested short description:** “Simple billing and collections for healthcare.”

## Logo

The current identity combines a healthcare cross, a heart-shaped negative space and a rounded lowercase wordmark. Dark teal carries the main identity; turquoise adds energy and highlights “pay.”

- Use the full logo where space permits. Use the icon alone for compact navigation, favicons and app icons where the brand is already clear.
- Preserve the original proportions, spelling and relationship between the icon and wordmark. Do not stretch, rotate, add effects or recreate the wordmark with a substitute font.
- Leave clear space around the logo. As a starting rule, keep at least the height of the wordmark’s lowercase “i” clear on every side.
- Place the logo on a plain surface with enough contrast. Avoid busy photographs and colors that obscure the mark. Use an approved light or dark variant once the SVG versions are available.
- Set minimum sizes after testing the new SVG in the actual interface and in print; the wordmark must remain legible.
- The heart and internal gaps should remain transparent if that is how the final SVG is constructed. Check them on both light and dark backgrounds.

**Source:** [Current master logo](logo/Cliniqpay%20healthcare%20heart-plus%20logo.png). Existing small raster exports are reference assets; replace them with exports from the approved SVG when available.

## Color

The first two colors are approximate samples of the existing master. The supporting colors are proposed for a calm, legible product interface.

| Role | Color | Hex | Use |
| --- | --- | --- | --- |
| Primary | Deep teal | `#006058` | Brand anchor, headings, primary buttons |
| Accent | Turquoise | `#00B8A0` | Highlights, active indicators, illustrations |
| Background | Soft white | `#F7FAF9` | Main application background |
| Surface | White | `#FFFFFF` | Cards, forms and dialogs |
| Main text | Ink | `#17332F` | Body text and key figures |
| Secondary text | Muted slate | `#506A66` | Labels and supporting information |
| Border | Pale teal-gray | `#D9E6E3` | Dividers and input borders |
| Success | Green | `#16734A` | Confirmed or completed states |
| Warning | Amber | `#8A5900` | Pending items and cautions |
| Error | Red | `#B3261E` | Errors and failed actions |

**Use:** Let soft white and white dominate the workspace. Use deep teal for hierarchy and key actions, and turquoise sparingly for emphasis. Status colors communicate meaning; pair them with a label or icon rather than relying on color alone.

**Accessibility:** Check actual foreground and background combinations at implementation time. Aim for WCAG AA contrast: 4.5:1 for normal text, 3:1 for large text and meaningful interface boundaries. Turquoise is best used as an accent rather than small text on white. Test focus, hover and disabled states separately.

## Typography

**Recommended interface family:** Inter, with `system-ui, sans-serif` as fallback. It is a practical proposal, not a claim about the logo’s typeface. Keep the logo wordmark as artwork.

| Level | Suggested size / line height | Weight | Use |
| --- | --- | --- | --- |
| Page title | 28 / 36 px | 700 | Main screen heading |
| Section heading | 20 / 28 px | 600 | Groups and panels |
| Card heading | 16 / 24 px | 600 | Card titles and prominent labels |
| Body | 16 / 24 px | 400 | Instructions and content |
| Supporting text | 14 / 20 px | 400–500 | Metadata and helper text |
| Small label | 12 / 16 px | 500–600 | Compact labels; use sparingly |

Use sentence case for headings, labels and buttons. Display amounts with the rupee symbol and Indian digit grouping, for example `₹12,500.00`. Align columns of amounts consistently; use tabular numerals where available.

## Visual language

- **Layout:** Open, orderly and task-focused. Show the next action and the most important amount clearly. Keep frequently used billing actions within easy reach on desktop and tablet.
- **Spacing:** Use a consistent 4 px spacing scale, with 16–24 px inside common cards and between related groups.
- **Shapes:** Use softly rounded corners, around 8–12 px for controls and cards. Echo the logo’s friendly curves without turning the interface into a decorative experience.
- **Icons:** Use a consistent, simple outlined icon set with clear labels for important actions. Avoid mixing stroke weights or decorative medical symbols into operational screens.
- **Imagery:** When photography is useful, choose real, respectful healthcare settings and diverse Indian healthcare teams. Avoid staged emergencies, distressing imagery and identifiable patient information without permission.
- **Data:** Give totals, payment state and outstanding balances visual priority. Keep tables quiet and readable, with clear column labels and adequate spacing.

## Voice and writing

Speak like a helpful, competent colleague at the counter: direct, calm and respectful. Use familiar words, short instructions and concrete outcomes. Avoid hype, jargon, fear-based sales language and unsupported claims about preventing leakage or guaranteeing payment.

| Situation | Prefer | Avoid |
| --- | --- | --- |
| Primary action | “Create bill” | “Initiate billing workflow” |
| Payment waiting | “Waiting for payment” | “Transaction processing pending” |
| Receipt action | “Send receipt on WhatsApp” | “Dispatch digital artefact” |
| Error | “Couldn’t send the receipt. Check the number and try again.” | “Something went wrong!” |
| Empty state | “No bills yet. Create your first bill to get started.” | “Nothing to see here.” |

Use “patient” when referring to the person receiving care and “cashier” or “staff” for the person using the desk. Use “bill” for charges, “payment” for money received, and “receipt” for proof of payment. Do not show a payment as received until the system has verified it.

## Product application

- **Billing:** Make patient details, line items, totals and the final action easy to scan. Keep tax labels clear and use the tax treatment configured for the service.
- **Payments:** Distinguish pending, confirmed, failed and manually recorded states in both text and appearance. Show the amount and payment method together.
- **WhatsApp:** Explain what will be sent and to which number. Show whether a message is queued, sent or failed when that information is available.
- **Daily summary:** Lead with collections and outstanding balances; show cash and UPI separately and explain doctor-share figures clearly.
- **Marketing:** Emphasize simplicity, clarity and suitability for small healthcare teams. Describe automatic payment matching, WhatsApp delivery and scheduled summaries as capabilities only when the actual integrations and workflows support them.

## Handoff checklist

1. Replace the raster master with an approved SVG and confirm the official colors and wordmark.
2. Export full-color, single-color and reversed versions as needed, plus appropriately sized transparent PNGs and app icons.
3. Verify logo legibility and contrast in actual light and dark placements.
4. Validate typography, color contrast and touch targets in the built product.
5. Confirm product and integration claims against the implemented experience before publishing marketing copy.
