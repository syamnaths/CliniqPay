# Current app (to map)

Status: planned · release 1 · map `current-app` in `docs/app-map/atlas-data.mjs`

## Goal

Map what already exists as delivered maps with source references.

## Steps (from the map)

1. Entry points
2. Main screens or endpoints
3. Data and storage
4. Background work

## Acceptance

Map what already exists as delivered maps with source references.

## Boundaries

- **Always:** build to the map; add behaviour tests; text in every language (en).
- **Ask first:** new packages, data deletion or migration, publishing, anything that changes the product brief.
- **Never:** invent requirements the owner did not give.

## Done checklist

- [ ] Map made exact before coding (guards, defaults, exits, failure paths); status `building`
- [ ] Built to the map; smallest coherent change
- [ ] TDD evidence: expected RED before implementation, GREEN and refactor (or documented exception)
- [ ] Unit tests for changed logic and integration tests for changed boundaries, with applicable failure paths; existing coverage reused
- [ ] Feature security review complete: findings evidenced, discussed with owner before remediation, agreed fixes tested and re-reviewed (Loop/SECURITY.md); no unresolved blocking findings
- [ ] Behaviour tests added and passing (`npm test (or the test command of the chosen web stack)`)
- [ ] Professional design reviewed for user-facing work: agreed visual system, complete states, responsive layout, accessibility and rendered evidence (or explicit blocker)
- [ ] Proved at the strongest level in `.loop/platform.md` (say which level)
- [ ] User text in every language: en
- [ ] Version bumped as `.loop/platform.md` says
- [ ] Legal rows this feature touches updated in `.loop/legal-checklist.md` (data, cookies, APIs, packages, assets, AI content, payments, advice, claims); none left `todo`
- [ ] Map `delivered` with `source` refs; `npm run atlas` passes
- [ ] Doc or notes updated; FIX-QUEUE and HANDOFF current
- [ ] Owner shown the result (phone-width and desktop screenshots in a real browser); verified vs not verified stated

## Decisions

- (record owner decisions here with the date)
