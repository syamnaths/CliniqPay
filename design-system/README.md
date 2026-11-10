# CliniqPay design system

The current visual reference is the [landing page concept](../Landing%20page%20concept/code.html) and its [design notes](../Landing%20page%20concept/DESIGN.md). It uses a cool, light canvas, white cards, teal actions, dark text, soft elevation and restrained tinted accents. Apply the same visual language to the billing desk without importing the concept's unverified product claims. The earlier [brand guide](../Brand%20assets/BRAND-STYLE-GUIDE.md) remains useful for voice and logo handling; its original palette and Inter-only typography are superseded for interface design by this working system. Brand colors remain provisional until the SVG is approved.

## Tailwind resources

The concept is a **standalone Tailwind v3 CDN prototype** with an inline theme. It requires network access for the CDN, Google Fonts and icons and is not a production build. `theme.css` is the equivalent **Tailwind v4** token resource for a future built application. Do not load it directly in the v3 prototype. The two configurations must be kept in sync when the visual direction changes; the agreed app stack uses Django templates with a Tailwind v4 build.

For a Tailwind v4 build, import the theme after Tailwind in the application's CSS, adjusting the relative path:

```css
@import "tailwindcss";
@import "../design-system/theme.css";
```

Ensure Tailwind scans the application's templates. Load Plus Jakarta Sans and Inter via an appropriate font resource or locally hosted files; system fallbacks are provided. Material Symbols are an external icon font in the concept. Use a consistent icon set and provide accessible labels for icon-only controls.

## Foundations

- **Color:** `primary` #00685f and `primary-container` #008378 lead actions; `surface` #f7f9fb is the canvas, `surface-container-lowest` #fff the card, and `on-surface` #191c1e the main text. Use `on-surface-variant` #3d4947 for supporting text. Use semantic text and background pairings and verify contrast at actual sizes; do not put white text on a light accent without checking it.
- **Type:** Plus Jakarta Sans for headings and titles; Inter for body, labels and numeric data. Use `font-headline-xl text-headline-xl-mobile sm:text-headline-xl` for a responsive hero and `font-body-md text-body-md` for compact copy. Use `tabular-nums` for currency and ledgers.
- **Spacing:** The shared theme supplies `space-xs` through `space-xl`, `gutter`, `gutter-mobile`, `margin` and `margin-mobile`; use responsive margins such as `px-margin-mobile sm:px-margin`. Use the standard Tailwind spacing scale elsewhere.
- **Shape:** The actual concept configuration uses `rounded-lg` 8px and `rounded-xl` 12px; this differs from the prose in its DESIGN.md. Those rendered values are the reference for now. Use `rounded-card` (16px) and `rounded-control` (8px) for new components when suitable. Avoid relying on an unqualified `rounded` when moving between Tailwind versions.
- **Depth:** Use subtle neutral shadows for cards and a restrained teal accent for prominent actions. Keep content legible without blur or glow.
- **Layout:** Use a centered maximum width of 1440px for marketing; adapt dense operational pages to available desktop and tablet width. Stack content on small screens, use readable columns and avoid horizontal page overflow.

## Component recipes

| Component | Tailwind classes / guidance |
| --- | --- |
| Page | `min-h-screen bg-surface font-body-md text-body-md text-on-surface` |
| Container | `mx-auto w-full max-w-[1440px] px-margin-mobile sm:px-margin` |
| Card | `rounded-card bg-surface-container-lowest p-4 shadow-card sm:p-6` |
| Primary button | `inline-flex min-h-11 items-center justify-center rounded-control bg-primary px-4 py-2 font-title-md text-title-md text-on-primary hover:bg-primary-container focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50` |
| Secondary button | `inline-flex min-h-11 items-center justify-center rounded-control border border-outline-variant bg-surface-container-lowest px-4 py-2 font-semibold text-on-surface focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary` |
| Input | `min-h-11 w-full rounded-control border border-outline-variant bg-surface-container-lowest px-3 py-2 text-on-surface focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary` |
| Icon tile | `flex size-10 shrink-0 items-center justify-center rounded-control bg-primary-fixed text-on-primary-fixed` |
| Status | Use a text label plus color or icon; distinguish pending, confirmed, failed and manually recorded states. Verify each color pairing. |
| Table | Use semantic headers, `tabular-nums`, right-aligned amounts and an `overflow-x-auto` wrapper on narrow screens. |

## Product and accessibility rules

Use [interaction and accessibility guidelines](interaction-guidelines.md) for forms, loading, errors, navigation, tables, motion and role-specific financial safeguards. These are planned requirements, not implemented components.


Use semantic buttons, associated form labels, visible keyboard focus, 44px minimum touch targets and responsive typography. Respect reduced motion and avoid relying on color alone. Target WCAG AA contrast and test rendered states. Show verified payment and message statuses only when supported by the integration. The concept contains illustrative numbers, testimonials, prices, certifications and functional claims that require validation; it is not approved production copy or a working enrollment flow.

The concept and the v4 token resource have not yet been tested in a compiled application. Verify rendered desktop and phone layouts, external resource loading and interactions when an app build is available.
