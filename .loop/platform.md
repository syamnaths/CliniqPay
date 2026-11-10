# Platform

**Platform:** Browser-based web application for desktop and Android tablets. No PWA or offline capability is assumed.

**Agreed stack:** Python and Django; Django templates with Tailwind CSS v4 and targeted JavaScript; PostgreSQL; Celery and Redis when background messaging and reporting are implemented. Use one shared, tenant-aware PostgreSQL database and a modular Django application; microservices are not planned for the first release. See `docs/database-architecture.md`. Hosting and integration providers remain undecided. See `docs/architecture.md`.

## Validation

- Product test runner: Django tests or pytest, to be configured when the application is created. No product test command exists yet; `npm test` currently runs Node tests and is not product verification.
- Browser: Playwright, to be configured when the application is created. Inspect desktop and phone/tablet layouts and critical interactions; record console errors.
- Atlas: `npm run atlas`, `npm run atlas:status`, `npm run atlas:next`, `npm run atlas:check`, `npm run atlas:verify`. Node is for atlas and frontend tooling.
- Proof ladder: static review → unit/integration tests → local runtime → browser → representative device. State what was actually verified.

## Platform rules

Responsive layout, keyboard and screen-reader basics. Use Django's localization system for user-facing text; English is the current working language. No service worker or offline behavior is promised. If those are added, define cache/version behavior and offline expectations. Design and build from the atlas, the landing concept and `design-system/`.

## Release path

1. Configure isolated environments and secrets; choose hosting, data location and providers.
2. Build Tailwind and static assets, apply migrations, deploy web and any required worker/scheduler.
3. Run product, integration, access-control and browser checks; verify backups and operational alerts.
4. Obtain owner approval for production deployment and publishable legal content.
5. Deploy and verify live health, version and critical flows.
