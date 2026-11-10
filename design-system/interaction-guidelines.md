# Interaction and accessibility guidelines

Status: design requirements for the prototype and future implementation, not a claim that these components already exist. Apply patterns where relevant to each workflow; they do not imply that every screen needs every component. Use the visual tokens and recipes in `README.md`. Validate actual behavior and contrast in the built interface.

## Forms and data entry

- Provide persistent, programmatically associated labels; placeholders are optional format hints, never replacements for labels. Mark required and optional fields consistently and explain the convention. Make controls visually distinct with a border and a touch target of at least 44 × 44 CSS px; aim for 48 × 48 on touch-oriented screens.
- Validate on blur or completion, and on submission; avoid errors on the first keystroke. Retain entered values on failure. Explain errors in text next to each field and link them via `aria-describedby` / `aria-invalid`; for multiple errors, show an accessible summary with links and move focus appropriately. Revalidate as the user corrects an error.
- Where useful for complex requirements, show clear positive feedback in text or an icon as well as color. Do not imply payment or identity verification from a form checkmark.
- Use appropriate `type`, `inputmode` and `autocomplete` attributes. For phone numbers and identifiers such as PAN or GST, prefer text with suitable input mode over numeric controls that lose leading zeros. Provide an accessible show/hide password button with a descriptive label and keyboard support.
- Format phone numbers, dates or identifiers only where helpful; preserve paste, editing, cursor position, autofill and screen-reader usability, and validate on the server. Do not collect card details unless a provider and compliant flow have been explicitly chosen; use provider-hosted fields if required.
- Show character counts for bounded text areas when useful, identify the actual maximum and announce limits without overwhelming assistive technology. Focus the first field only where it helps; avoid unexpected jumps or opening a mobile keyboard automatically.

## Loading and progress

- Use layout-matched skeletons for meaningful waiting periods and reserve space to reduce layout shifts. Use reduced-motion-safe animations and accessible loading text; decorative skeletons should not create noisy announcements.
- For submissions, preserve the button's dimensions, show progress and guard against repeated activation. The server must also handle duplicate requests safely; a disabled button alone is insufficient.
- Show determinate progress only when actual progress is measurable, such as supported uploads; otherwise use an indeterminate indicator with a descriptive label. Use step labels and “Step X of Y” for genuine multistep flows, with current and completed states accessible to screen readers.
- Use image placeholders and explicit dimensions when beneficial. Do not add a loading bar to every server-rendered navigation by default.
- Optimistic updates may be used for reversible, low-risk preferences with a visible pending state and rollback on failure. Do **not** optimistically mark bills paid, financial records saved, hospital approvals complete or WhatsApp messages delivered. Show pending until server/provider confirmation; do not automatically repeat a financial mutation merely because a connection returns.

## Empty, restricted and error states

- First-use views explain the absence of data and offer an appropriate action when the user has permission. Completed work can have a calm completion message; illustration or celebration is optional.
- Distinguish no data, no search results and filtered-out results; offer clear search or filter reset where relevant. Echo user queries as text, never unescaped HTML, and avoid exposing sensitive search text unnecessarily.
- Restricted views explain the next step, such as contacting an administrator, without revealing whether protected records exist. Design 404 and 500 pages with plain language and a safe route back; a search bar is optional. Show a non-sensitive support reference only when one actually exists; never expose stack traces or internal identifiers.
- Show lost connectivity and reconnection state without promising offline operation. Retry safe reads when appropriate; reconcile uncertain writes before offering another attempt. Show a 429 retry interval only when supplied by the server, honor `Retry-After`, and avoid inventing a countdown.
- Design session-expiry warnings and renewal only when the authentication implementation supports them. Preserve unsaved work safely where feasible; never persist sensitive drafts on shared devices without a security and retention decision. Clearly explain an expired session.
- For permanent destructive actions, use a confirmation proportional to the risk, state consequences, and default focus to a safe option; typed confirmation is reserved for especially consequential actions. Financial records need traceable corrections or reversals, not routine permanent deletion. Warn about unsaved changes for internal navigation and use `beforeunload` only while dirty; browser-controlled wording and mobile limitations apply.

## Feedback and navigation

- Use consistent, non-blocking toasts in a predictable position. Short informational or success messages may dismiss after 4–6 seconds if the information remains available elsewhere. Persistent errors and actionable messages must remain available until dismissed or resolved; do not time out an Undo action without an accessible alternative. Announce status changes politely and urgent errors assertively as appropriate.
- Use success, error, warning and informational colors consistently, with text or icons as well as color. Banners may be dismissible if appropriate; never conceal a critical unresolved system condition. Hide zero-count badges unless zero is meaningful and supply an accessible name for counts.
- Provide visible keyboard focus (normally a 2px outline with sufficient contrast); do not remove focus indicators globally. Give hover and pressed states where supported, and respect reduced motion. Do not rely on a disabled control's tooltip: native disabled controls may not receive keyboard focus. Explain the reason in visible nearby text or use an accessible pattern with server-side enforcement.
- Modal dialogs need an accessible name, appropriate initial focus, focus containment, inert background and focus return to the invoking control. Provide a visible close or cancel action and support Escape where dismissal is safe. For unsaved or critical operations, preserve state or ask before discarding; do not allow an accidental backdrop click to lose data. Lock background scrolling when appropriate without breaking mobile or assistive navigation.
- Breadcrumbs are useful for deeper hierarchies; link ancestors and mark the current page with `aria-current="page"`. Tooltips are supplementary, appear on hover and focus with a short delay where useful, can be dismissed with Escape, and never hold essential information inaccessible on touch.

## Search and tables

- For server-backed typeahead, start with a roughly 300ms debounce when useful, cancel or ignore stale responses, and test with assistive technology. Offer a labeled clear button when populated.
- Show active filters as individually removable chips and offer clear all when useful. Announce changes to result counts without excessive live-region updates.
- Prefer pagination and an item range for structured administrative and financial tables; an infinite list is appropriate only when its interaction and accessibility fit a browsing use case. Make sorting controls keyboard-operable and expose the active direction using `aria-sort` on the appropriate header.
- For bulk actions, show the selected count and available actions; recheck authorization and confirm consequential actions, including partial failures. Preserve context across pagination only if selection behavior is explicit.
- Use sticky table headers or columns where they improve a constrained table; check zoom, responsive overflow, overlapping content and keyboard access. Avoid fixing columns by default if they obscure data.

## Accessibility and performance

- Target WCAG 2.2 AA; verify normal text at least 4.5:1 and large text at least 3:1, and meaningful interface boundaries and icons at least 3:1 against adjacent colors where applicable. Disabled and decorative elements have specific exceptions; test actual states instead of assuming the palette passes.
- Give icon-only buttons accessible names; use semantic controls and labels before adding ARIA. Ensure sufficient touch targets and visible focus. Test keyboard and screen-reader paths, zoom, long text and mobile widths.
- Respect `prefers-reduced-motion`; stop or reduce shimmer, pulsing and movement. Specify image and embed dimensions or aspect ratios, reserve loading space and avoid content jumping.
- Respect device safe-area insets where content or sticky bottom controls can overlap a notch or home indicator, and ensure controls remain reachable.

Reference: [W3C modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) and [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
