# Production engineering standard — project adoption

The user's **Production Engineering, Performance, Reliability & Safety Standards, Version 1.0 FINAL** are the locked engineering source of truth for current and future implementation. This project adoption is an operational index, not a replacement for the full user-supplied standard or for approved business rules. Apply only relevant checks to each confirmed task; do not weaken correctness, security, tenant isolation, data integrity, or image quality to save cost.

## Risk gates

- **Always:** correctness, permissions/security, data safety, visible error handling, regression and performance impact.
- **When touched:** media and image delivery, caching/pagination, jobs, public APIs, mobile forms, third-party services, heavy JavaScript.
- **High risk:** deeper proof for auth, tenant boundaries, finance, payments and migrations (transactions, idempotency, race safety, audit and recovery as relevant).
- **Milestone/release:** integrated architecture, security, performance, scaling, deployment, backup/restore and observability audit. A task-level pass is not a release sign-off.

## Cross-cutting acceptance

- Test meaningful UI at ~360px and larger widths; avoid horizontal overflow, hidden keyboard-open actions, tiny touch controls and inaccessible keyboard paths. Preserve input on failure and avoid false success, endless spinner, silent catch and whole-page failure from one image.
- Use bounded timeouts/retries; never blindly retry writes. Keep duplicate writes safe through suitable UI guards, operation IDs and database constraints/transactions.
- Preserve original uploads where the media contract requires it; deliver suitably sized, clear image variants with reserved dimensions, lazy loading and localized failure/retry. Avoid full originals in list cards and unbounded gallery loads.
- Fetch only needed data/code, prevent N+1 and unnecessary API calls, measure real route/API/image costs where possible, and keep optional dependency failures local. Avoid adding services or libraries without a measured need.
- Validate uploads and inputs server-side; enforce auth, object/Shop authorization, secret hygiene and rate policy. Use structured safe errors/logging and request correlation.
- Treat `LOCAL → STAGING → PRODUCTION`, exact candidate identity, migrations, backups and a tested restore procedure as release gates. Keep infrastructure scalable beyond the initial low-cost size; never encode a $6/$7 machine as a product limit.

Project-specific vehicle wording in the source document is illustrative, not a SGTP business requirement. The general slow-image/local-failure rule applies to garment and design imagery. Existing workflow and UI behavior must not regress during optimization.
