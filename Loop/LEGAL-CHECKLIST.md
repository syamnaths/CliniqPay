# Loop legal checklist (20 checks)

Every Loop project carries these 20 checks in `.loop/legal-checklist.md`. They catch the usual legal gaps in AI-built software before users see the product. Loop is not a lawyer: it drafts, checks and flags. The owner decides, and anything marked `lawyer` goes to a real lawyer.

## Status values

| Status | Meaning |
| --- | --- |
| `todo` | Not checked yet |
| `done` | Done, with proof (file, page or link) in the Proof column |
| `n/a` | Does not apply, with the reason (for example "no payments") |
| `lawyer` | Needs a lawyer's review; Loop has written what the question is |
| `blocked` | Waiting for the owner (a fact, an account, a decision) |

## The 20 checks

### A. Legal pages

1. **Privacy Policy.** Add one when the product collects any personal data (accounts, forms, analytics, logs with IP addresses).
2. **Terms & Conditions.** Rules of use, limits of liability, who runs the product, how disputes work.
3. **Cookie Policy.** List every cookie and similar storage (local storage, SDK identifiers), what it does and how long it stays.
4. **Cookie consent.** Check whether a consent banner is required for the users' countries (for example EU/UK GDPR and ePrivacy, India's DPDP Act, US state laws). Non-essential cookies and trackers wait for consent where required.

### B. Personal data

5. **Consent on forms.** Every form that collects personal data says why, links to the Privacy Policy and asks for clear consent where the law needs it. No pre-ticked boxes.
6. **What data we collect.** A plain list of every piece of user data, where it is stored and who else receives it.
7. **Why we collect each piece.** One purpose per data item. Data without a purpose is not collected.
8. **Deletion requests.** A working way for users to ask for their data to be deleted, and a known process to do it.
9. **Access and correction requests.** A working way for users to see or correct their data.

### C. Third parties and licences

10. **Third-party API terms.** Read the terms of every API and SDK used (rate limits, allowed use, data sharing, attribution, commercial use, AI training rules).
11. **AI-generated content.** Check that AI-made text, images, code, music or voices do not copy protected work, real people or brands, and that the AI tool's terms allow the use.
12. **Open-source licences.** List every dependency with its licence. Flag copyleft (GPL, AGPL, LGPL) and "unknown" licences.
13. **No copyrighted assets without permission.** Images, fonts, icons, videos, sounds and text must be owned, licensed or free to use.
14. **Attribution.** Add credits where a licence requires them (credits page, about screen, `NOTICE` file).
15. **UI asset licences.** Check templates, UI kits, icon sets and font licences cover this use (commercial, app embedding, web serving).

### D. Users and selling

16. **Age limits.** If the product needs a minimum age, or children may use it, add age gating and follow child-privacy rules.
17. **High-risk advice disclaimers.** Health, money, legal, safety or emergency content gets a clear disclaimer and a "get professional help" path.
18. **Refund and cancellation policy.** Required if users are charged. Must match the payment provider's and app store's rules.
19. **Honest marketing claims.** Every claim on the site, store listing or app (numbers, "secure", "AI-powered", "certified", reviews) is true and can be shown with proof.

### E. Final audit

20. **Final legal audit.** Before release, recheck items 1–19 against the real product, and mark anything that needs a lawyer as `lawyer` with a one-line question for the lawyer.

## When Loop runs the checks

- **At project start.** `loop-init.mjs` writes `.loop/legal-checklist.md`. On the first map, Loop marks each check `todo` or `n/a` (with a reason) from the brief. Items that depend on unknown facts become `blocked` with one plain question to the owner.
- **During each feature (checkpoint step 6).** If a feature touches a trigger below, Loop updates those rows in the same change. The feature is not delivered while a touched row is `todo`.

  | The feature… | Recheck |
  | --- | --- |
  | collects, stores or shares personal data | 1, 5, 6, 7, 8, 9 |
  | adds cookies, analytics, ads or tracking SDKs | 3, 4 |
  | adds a third-party API or SDK | 10 |
  | uses AI-generated content | 11 |
  | adds a package or library | 12 |
  | adds images, fonts, icons, sounds or a UI kit | 13, 14, 15 |
  | has sign-up, children or adult content | 16 |
  | gives health, money, legal or safety guidance | 17 |
  | takes payments or subscriptions | 18 |
  | adds marketing text, store listing or landing copy | 19 |

- **Before release.** The `release` track needs check 20 done: no row is `todo` or `blocked`, every `n/a` has a reason, and every `lawyer` row has an owner decision (A: wait for the lawyer, B: release with the risk recorded, C: remove the feature).

## Rules

- **Drafts, not legal advice.** Loop may draft Privacy, Terms, Cookie and Refund pages from the real data list (checks 6 and 7). Every draft is labelled as a draft for owner review. Loop never says the product is "legally compliant".
- **Publishing legal pages is an approval gate.** The owner approves the final text before it is published, like any user-visible content.
- **Facts come from the code.** The data list, cookie list, API list and dependency list are built from the real source, config and lock files, not from memory. Proof is a file path or a command output.
- **Every language.** Legal pages and consent text appear in every supported language, like all user text.
- **No dark patterns.** Consent is as easy to refuse as to accept; deletion is as easy to find as sign-up.
- **Laws depend on country.** Record the countries where users will be (ask the owner once). If unsure which law applies, mark the row `lawyer`.

## Report to the owner

Show the checklist as one short line per group, for example: "Legal: 14 done, 4 n/a, 1 needs your answer, 1 for a lawyer." Then list only the `blocked` and `lawyer` rows with A/B/C options.
