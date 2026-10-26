# Changelog

## 2026-10-26 — Phase 5 local migrations applied (unpublished)

- User authorized local `devdb` migrations after inspecting the nine-operation
  plan: `catalog.0025`/`0026`, `works.0003`, `billing.0001`–`0006`. All applied;
  no migrations remain pending.
- Backed up `devdb`, validated the archive, restored it into a disposable DB,
  and compared pre-existing business/catalog/work table row counts after the
  migration. Counts matched; expected content-type/permission/migration rows
  and 12 new Phase 5 tables were added. The comparison database was removed;
  the ignored backup remains available for recovery.
- Focused backend billing/pricing tests passed 21/21 on a disposable DB.
  Django system check, migration drift, Project State Validator passed. Local
  frontend and backend readiness returned HTTP 200. Earlier supported frontend
  233/233, typecheck/build, and authenticated synthetic Billing E2E remain valid.
- Staging remains deferred; no commit/deploy. Local DB setup is complete;
  production operational gates remain open.

## 2026-10-26 — Phase 5 local closure validation (unpublished)

- Staging is deferred per the user's latest direction; no commit or deployment
  occurred.
- The guarded disposable PostgreSQL migration and backup/restore script passed,
  verifying financial totals, Shop ownership, and private A5 PDF checksum.
  Its exact databases/media were removed; persistent `devdb` was not modified.
- Focused backend billing/pricing tests passed 21/21 on an isolated disposable
  Django test database, verified absent after the run.
- Local frontend `/` and backend readiness returned HTTP 200. A read-only
  migration-ledger check found `devdb` has not applied catalog 0025/0026,
  works 0003, or billing migrations. Authenticated local Phase 5 E2E was not
  rerun; Phase 5 remains partial until the local database migration scope is
  explicitly resolved.
- The Project State Validator passed and discovered 593 tests; the full suite
  was not run in this refresh, and remote verification was unavailable.

## 2026-10-26 — Phase 5 verification refresh (local, unpublished)

- Re-ran the Project State Validator: PASS; Phase 5 remains active and the
  working tree is dirty. The validator could not independently discover tests
  or verify the remote.
- Initial staging liveness/readiness requests timed out, but a later documented
  smoke returned HTTP 200 for both. Unauthenticated `/api/schema/` returned
  Admin login HTML; deployed API contracts, provider SHA, and migration state
  remain unverified. No staging or persistent database write/deployment occurred.
- Inspected local release refs: the staging worktree and separate sync
  candidate do not contain the committed Phase 5 Billing feature; the candidate
  is not merged into the local staging branch. This is not a live Render SHA
  check.
- Recorded that Docker Desktop was not running and no new live local visual
  validation was made. Existing 2026-10-25 test and responsive/E2E evidence is
  unchanged; Phase 5 remains partial.
- Fresh supported-sibling checks: Billing/purge focused UI tests 13/13,
  full frontend suite 233/233, TypeScript project build, and Vite production build passed. Backend suites
  were not rerun without a verified disposable PostgreSQL target; `devdb` was
  left untouched.
- Database-independent backend checks: Django system check PASS and Billing
  calculation/PDF tests 5/5 PASS. Migration drift reported no model changes
  but could not reach PostgreSQL for history consistency. Read-only remote refs
  confirmed staging at `4db6d9fe` and the sync candidate at `cab810bb`; neither
  committed tree includes Phase 5 Billing code. User authorized commit/staging
  deployment after closure; neither action has occurred.
- Read-only remote Git query confirmed `origin/staging=4db6d9fe` at this check;
  this branch ref is not proof of the live Render deploy SHA.
- A fresh isolated PostgreSQL start attempt failed because both bundled PG15
  executables could not initialize on Windows (`-1073741502`), Docker engine
  pipe was absent, and port 5432 was unavailable. The empty scratch directory
  was removed; no database was created or written.

## 2026-10-25 — Manual Super Admin financial purge (local, unpublished)

- Added a Main Supplier Super Admin-only Back Office flow to review a selected
  Shop's invoice history and manually purge a confirmed issued invoice bundle.
- Requires reason, exact invoice-number confirmation, and idempotency key;
  private files are removed before financial rows. Failed storage deletion
  leaves the financial bundle available for retry.
- Retains existing audit/idempotency entries and Shop number sequences; adds a
  purge tombstone and completion audit. No automatic purge path was added.
- Added additive `billing.0006`, focused backend/UI tests, and synchronized all
  four local OpenAPI snapshots. Persistent DB migration/deployment not done;
  Phase 5 remains partial pending retention/production reliability gates.
- Corrected purge-page Retry semantics: Shop-list errors retry Shop loading,
  invoice-history errors retry history, and purge/storage failures retry the
  same confirmed purge. Added loading/disabled, error/retry, empty, draft guard,
  exact-confirmation, and storage-failure coverage.
- Validation: focused backend purge suite 3/3; FinancialPurgePage tests 8/8;
  full supported frontend suite 233/233; typecheck/build passed. Targeted lint
  exited 0 with two `react(set-state-in-effect)` warnings in the page; OpenAPI
  generation 0 errors / 29 existing warnings. See `docs/PROJECT_STATE.md`.

## 2026-10-25 — Phase 5 final local verification refresh (unpublished)

- Full backend validation passed: Django test runner 486/486 and pytest
  593/593 (392 warnings) on unique disposable PostgreSQL test databases.
  Supported sibling frontend passed 233/233 with typecheck/build; lint exited
  0 with existing warnings. Django system check and migration drift passed.
- Fresh disposable migration plus PostgreSQL dump/restore verified financial
  totals, Shop ownership, and a private A5 invoice PDF checksum. The app's
  `PrivateReferenceStorage` adapter passed synthetic R2 upload/read/checksum/
  delete; a synthetic presigned PUT also returned HTTP 200 and passed metadata,
  private-read/checksum, and exact-key cleanup checks. The exact synthetic
  objects and disposable DBs were absent afterward.
  Mocked viewport checks subsequently covered Work Billing, Billing History,
  Design price, and Financial Purge without overflow. Authenticated headless
  Chrome E2E then purged one synthetic issued invoice via the real UI/API on
  disposable PostgreSQL; the invoice bundle was absent while completion
  tombstone/idempotency remained. Exact disposable DB and temporary browser/test
  resources were removed; `devdb` was untouched. The separate Catalog
  upload-ticket/browser flow remains unverified. Receipt/credit-note file
  restore, production backup/restore/monitoring,
  deployed parity and backup/object-retention alignment remain unverified.
- No application `devdb` migration/write, staging/production change, commit,
  push, or deployment. Phase 5 remains partial; automatic retention/deletion
  is not implemented.

## 2026-10-25 — Phase 5 local verification refresh (unpublished)

- Reconciled current-state Phase 5 verification with the 2026-10-22 clean
  disposable runs: Django 483/483 and pytest 590/590 (389 warnings); migration
  drift and Project State Validator passed. On 2026-10-25, Django check and
  migration drift were rerun; the Project State Validator passed with 590 tests
  discovered. Supported sibling frontend Vitest passed 225/225, build/typecheck
  passed, and lint exited 0 with existing warnings.
- Reconfirmed the disposable A5 invoice restore smoke artifacts were absent by
  read-only PostgreSQL/container checks; `devdb` remained without Billing
  migrations. No application DB, external R2, staging, or production write was
  made. Phase 5 remains partial because operational/production gates and the
  retention/anonymization decision remain unresolved.
- Audited remaining storage/observability gates: required R2 setting assignments
  are non-empty in ignored local configuration, but no external request was
  authorized or made. No Sentry/error-tracking SDK or DSN configuration was
  found in this checkout/local environment. Provider/configuration choice,
  production alerting/restore evidence, and retention policy remain blockers.

## 2026-10-22 — Portrait A5 PDF layout (local, unpublished)

- Reflowed Measurement worksheet and financial invoice/receipt/credit-note PDFs
  to portrait A5; long content remains intact and continues across A5 pages.
- Added immutable financial PDF layout versions so new exports use A5 while
  existing A4 files remain unchanged. No PDF route, authorization, locale, or
  financial calculation changed.
- Focused renderer tests, migration/API checks, and schema validation results
  are recorded in the current task handoff.

## 2026-10-22 — PHASE-5-INTEGRATED-CLOSURE-01 verification update (local, unpublished)

- Authenticated browser E2E passed on synthetic data in disposable PostgreSQL: Shop currency context, AUTO and MANUAL invoices, fixed/percentage discounts, optional tax, sequential issue, partial payment, credit note, linked refund, unpaid void, Billing History and Outstanding. Work production status remained unchanged.
- Added finance-only nullable `billing_currency` to Shop request context; non-finance staff remain excluded. Corrected the synthetic backup fixture to seed financial sequence high-water marks; no runtime numbering change was needed.
- Full backend suite passed 587/587 before the narrow context-contract addition; focused post-change Shop-context/Work/Billing tests passed 54/54. Frontend Vitest 225/225, typecheck/build, Django check and migration-drift check passed. Four generated schemas validate with 0 errors / 29 existing warnings.
- Fresh disposable migration replay and PostgreSQL dump/restore verified totals, Shop ownership, and one invoice PDF file/checksum across restore; receipt/credit-note files were not claimed as restore-tested. Their protected download and cross-Shop behavior are separately API-tested. Persistent `devdb` was not written or migrated. External R2, production alerting/monitoring, retention/anonymization and production restore remain open. Phase 5 remains partial; no staging/production action, commit, push, or deploy.

## 2026-10-21 — R5-01 Shop Design pricing and Billing backend (local, unpublished)

- Added Shop-specific Design prices, Shop currency/minor-unit validation, and
  Work-time Design price/currency snapshots.
- Added Shop-scoped invoice, invoice-line, payment and outstanding APIs with
  ADMIN/CASHIER STAFF permission; draft edits, immutable issue, and
  invoice-bound append-only partial payments.
- Added additive catalog/works/billing migrations and focused backend tests.
  30 focused tests passed on disposable PostgreSQL; app devdb was not migrated.
- No frontend, price catalog, idempotency/audit, report, commit, push, or deploy.

## 2026-10-21 — T4-06 Domain integration validation (local, unpublished)

- Added a focused Work API integration regression for create → assignment/stage progression → Completed, preserving selected Client/DesignVersion/MeasurementSet references and checking foreign-Shop list/detail isolation.
- Backend Work tests passed 22/22 on isolated PostgreSQL 15 after fresh migration replay through `works.0002`; sibling Orders tests passed 36/36; typecheck/build, Django model check, and migration drift passed. Persistent `devdb`/`testdb` were not used.
- Updated the repository-state gate to recognize explicitly confirmed T4-06 integration-test scope; validator tests passed 35/35.
- No runtime behavior, API contract, schema, or migration changed. Browser-to-API E2E, staging, production, commit, push, and deployment were not performed. Phase 5 remains separately gated.

## 2026-10-20 — CREATE-ORDER-FINAL-CLOSURE-01 (local, unpublished)

- New Work is blocked when either parent Family or Design is archived; create locks Shop → Family → Design, while prior Work remains readable. Design responses add `family_status` for the Order picker to omit archived-Family Designs.
- Preserve URL-preselected Material IDs until verified, replaced or explicitly cleared; a failed optional-material lookup only blocks when a preselection is unresolved. No schema migration.
- Work API tests 15/15 on disposable PostgreSQL; supported frontend Orders/Measurement suites 34/34 and typecheck passed. Django check/migration drift pass; OpenAPI validates with 0 errors / 29 existing warnings. Browser E2E unverified; no shared DB, commit, push or deployment.

## 2026-10-19 — CREATE-ORDER-ARCHIVE-ELIGIBILITY-AND-E2E-CLOSURE-01 (local, unpublished)

- New Work now requires its parent Design to be active as well as the selected version to be published; the transaction locks Shop then Design to coordinate with archive. Existing Work history stays readable. No schema/migration change.
- Added backend API and frontend regression coverage for archived Design rejection, stale UI errors, duplicate in-flight submit, and cross-Shop wearer/Design/Measurement checks. Regenerated both OpenAPI snapshots with Work routes/create contract (0 errors, 29 warnings).
- Focused backend tests passed 12/12; supported frontend Orders + Measurement Review tests 15/15; typecheck and Django check passed. Full Client Measurements tests were 16/18 with two existing expectation/accessibility-contract mismatches. Browser E2E remains unverified; archived Family eligibility remains a business decision. No dev/staging/production DB, commit, push, or deployment.

## 2026-10-19 — FIX-VARIANT-RETIREMENT-RELEASE-BLOCKERS-SAFELY (local, unpublished)

- Added `catalog.0025_reconcile_family_design_defaults` after `0024`. It reuses the approved `0018` preset definitions and additively repairs missing global Family option groups/options and published Family-linked Designs without requiring active Variants; existing same-name Designs, versions, selections, and Shop-owned rows are left untouched.
- Re-verified Variant mutation APIs: current Global/Shop views restrict HTTP methods to read-only or OPTIONS, and focused API tests assert write rejection. Updated the stale Measurement regression to expect 405 and set an inactive legacy Variant only as test setup before verifying legacy-profile reads and new Family-level records.
- Added focused migration reconciliation/bootstrap tests. Both new tests are discovered and scoped Flake8 passes, but DB execution and fresh/upgrade replay remain **UNVERIFIED** because the configured disposable PostgreSQL host is unavailable (Docker is unavailable and localhost port 5432 is closed); no application DB was used. Corrected stale architecture/database text claiming Work still matched Variant IDs. No commit, push, or deployment.

## 2026-10-18 — VARIANT-RETIREMENT-STAGING-RELEASE-PREFLIGHT-01 (local, unpublished)

- Verified Render's staging backend source repository, `staging` branch, live deploy SHA, Docker root, and auto-deploy-on-commit setting. The exact artifact source still contains Variant mutation methods and has no `catalog.0024`; it is not the current Family-based release candidate.
- Render lists no frontend service; Pages source/settings, live HTTP health/API, actual provider environment-variable values, and staging DB migration/data state remain unverified or inaccessible. The read-only SQL attempt was blocked by the empty DB IP allowlist; no allowlist or Render setting was changed.
- Fresh local migration replay (including `catalog.0024`) passed on disposable `test_devdb`, which was removed after the tests. Targeted suites ran with 2 backend and 3 frontend failures; frontend typecheck, Django check, and migration drift check passed. No application code, application DB, staging DB, commit, push, or deployment was changed.

## 2026-10-18 — VARIANT-CROSS-CHECKOUT-DRIFT-RESOLUTION-01 (local, unpublished)

- Verified the active local pairing from process/container metadata: sibling `frontend/parallel-foundation` UI proxies to canonical `main` backend.
- Classified `main/frontend` (Variant UI) and sibling `apps/` backend (Variant-required Design serializer) as deprecated, runnable, unsupported copies under current worktree ownership rules. Marked the main frontend README and canonical environment/current-state docs accordingly.
- No source implementation, schema, migration, legacy data, or database was changed. Focused contract checks are recorded in the handoff; no commit, push, or deployment.

## 2026-10-18 — VARIANT-MIDDLE-LAYER-RETIREMENT-IMPLEMENTATION-02 (local, unpublished)

- Retired writable Global/Shop Variant API operations while preserving legacy list/detail reads; Work source compatibility now requires the same Family rather than exact Variant equality.
- Active sibling frontend Order/Measurement profile resolution is Family-based and does not extend a legacy Variant-linked profile. Legacy Design/Profile references remain readable; historical seed migrations were not rewritten. The already-dirty checkout contains `catalog.0024_retire_variant_measurement_mappings` for Family-only definition mappings; this task neither changed nor applied it.
- Updated the two checked-in OpenAPI snapshots and verified-current architecture/API/data/compatibility maps, plus project-state and handoff records. No database migration or application DB write was performed.
- Validation: narrow backend Variant/catalog/Work regression set 12/12 PASS; Django check and migration drift check pass; OpenAPI generation 0 errors; focused frontend tests and typecheck pass. A broader 63-test backend run was stopped after tests attempted remote R2 media fixtures unavailable by DNS; it is not counted as passing. Broader frontend suites retain remaining failures recorded in the handoff. No commit, push, or deployment.

## 2026-10-18 — VARIANT-RETIREMENT-DEPENDENCY-AUDIT-01 (local, unpublished)

- Recorded the user's resolved policy that active Variant workflows are retired and Global/Shop bootstrap must not require active Variant materialization; legacy rows/FKs are allowed only for compatibility, immutable history, or migration safety.
- Verified incomplete retirement in source: local `main` still has writable Variant APIs and management/Design-selection UI, Work requires Design/Profile Variant equality, model-level Profile creation permits Variant, and migrations `0002`/`0012`/`0018` seed/use active Variants. The sibling backend still requires `variant_id` for Design creation and sibling Orders UI matches Profiles by Variant. Shop initialization itself is Family-level and copies no Variants.
- Aligned current business, product, API, database, data-flow, architecture, dependency-map, project-state, and handoff documentation. Added a preflight-first correction/migration plan. Historical changelog entries remain historical.
- Documentation-only change. No code, migration, schema snapshot, database, runtime/deployment, or product-test changes/checks were performed. No database ledger/data inventory was queried. Repository validator and `git diff --check` exited PASS; test-discovery/dirty-tree warnings and line-ending notices are recorded in the handoff. Runtime/deployed status remains unverified; no commit, push, or deployment.

## 2026-10-18 — DEPENDENCY-ONE-VIEW-MAP-VERIFY-ALIGN-AND-SYSTEM-CORRECTNESS-01 (local, unpublished)

- Corrected only §1 of the dependency impact map to distinguish Shop request context, direct required Work dependencies, optional references, measurement version links, action-level authorization, inventory ledger behavior, and the actual frontend/API consumers.
- Recorded the unresolved conflict between the catalog bootstrap implementation and the business-rule/documentation claim that default Variants are copied. No business rule was inferred; no product code, API, schema, migration, or database changed. No product tests were run.
- Repository state validator and `git diff --check` exited PASS; the validator warned that test discovery was unavailable and the working tree is dirty. Diff check emitted existing line-ending notices.

## 2026-10-16 — T4-04 Work aggregate (local, unpublished)

- Added one-garment Work/Order backend model, Shop-scoped API, fixed production
  stages, assignment policy, due indicators, and per-Shop stable Work numbers.
- Added approved `CHECK` Work Function and additive migrations `tenants.0010`
  and `works.0001`. No existing application database was migrated.
- Targeted disposable PostgreSQL Work/Function tests 23/23 PASS; Django check,
  migration drift, OpenAPI generation (0 errors), project-state validator and
  its 33/33 tests PASS. T4-05/T4-06, frontend and publication remain separate.

## 2026-10-13 — GARMENT-SETUP-PARTS-AND-MEASUREMENTS-IMPLEMENT-01 (local, unpublished)

- Extended Shop Catalog garment setup with the existing FamilyOptionGroup editor and a measurement setup area that maps Shop-owned definitions at family or variant scope, or creates and maps a new Shop-owned definition. Added a Design-draft return path after garment configuration.
- Added the Shop-scoped measurement-definition mapping endpoint and updated OpenAPI snapshots. Global definitions and immutable measurement history remain unchanged; no database migration.
- Validation: backend focused tests 4/4 PASS; frontend focused tests 32/32 PASS; typecheck/build, Django check, migration drift PASS. OpenAPI validation: 0 errors, 29 warnings / 13 unique. Tests used disposable `test_devdb`; configured app DB `devdb` was not written. No commit, push, or deployment.

## 2026-10-12 — MEASUREMENT-PROFILE-SAVE-AND-RECOVERY-01 (local, unpublished)

- Fixed the mismatch between the filtered Measurement definitions response and save-time mapping validation for Shop-materialized garments. Saves now recognize inherited global family/variant mappings without copying catalog data.
- On a duplicate profile-create response, the client reloads the person's profiles and opens the matching existing profile; failed stale-family requests also refresh active families and clear an unavailable selection. The backend's unique-profile guard remains authoritative, while a different garment can still create a separate profile.
- Validation: backend Measurement/Materials API 34/34 PASS; frontend Measurement page 15/15 PASS, typecheck and production build PASS; changed Python Flake8 and scoped diff checks PASS. Tests used only disposable `test_testdb`; current application DB `devdb` was not queried or changed. No schema/data migration, commit, push, or deployment.

## 2026-10-12 — GARMENT-FAMILY-DEFAULT-MEASUREMENTS-01 (local, unpublished)

- Completed the family-level measurement baseline for all four seeded garment families. Existing Men's Shirt and Kuwaiti Dishdasha defaults are preserved; additive migration `catalog.0023` adds Abaya and Darraa / Long Dress field definitions, with Hem Width additionally available for Darraa.
- Defaults are mapped at family level and therefore appear for every variant. The Shop `Add measurement` UI now submits a family-level mapping (`variant_id: null`) so added fields are available for every variant of that garment family.
- Validation: Measurement/Materials API 34/34 before the final mapping-scope change; focused fresh-DB tests 2/2 and frontend Measurement/API 28/28 after it; approved defaults/concurrency 8/8. Django check, migration drift, migration Flake8/compile, and scoped diff checks PASS. Migration `0023` was applied and verified on local `devdb`; staging/production were not changed. No commit, push, or deploy.

## 2026-10-11 — GARMENT-DEFAULT-MEASUREMENT-STRUCTURE-RESTORE-01 (local, unpublished)

- Restored generic approved Measurement structure for Shop-materialized Families by resolving mappings from the Shop Family and its linked global `template_source`; linked Shop Variants also resolve source-Variant-specific mappings. No per-garment frontend hardcoding, mapping cloning, schema migration, or historical-value rewrite.
- Family-filtered API results now use the applicable mapping order, preserving garment-specific structure even when one reusable definition has different order values across families. Supplemental Shop measurement mappings inherit the supplemental definition's configured order.
- Regression coverage proves Men's Shirt defaults, another source family, local and source-variant behavior, deduplication, ordering, supplemental fields, Shop isolation, and existing immutable measurement history. Backend API 33/33 and approved-default/concurrency 8/8 pass; frontend Measurement page/form tests 25/25 pass; Django check, Flake8, and scoped diff check pass. Migration drift: no changes; history check unavailable because configured test base DB `testdb` is absent.
- Tests ran only against disposable local `test_testdb` (created and removed); configured `devdb` was not written. No staging/production, commit, push, or deployment.

## 2026-10-11 — STYLE-OPTION-SNAPSHOT-LEAK-FIX-01 (local, unpublished)

- Fixed duplicate Design chooser options: reusable Shop Catalog list queries now exclude per-Design snapshot StyleOptions (`source_style_option` set), while existing Designs retain those copies and their images. The same availability rule applies to Design create/add/replace and Shop style-option edit endpoints.
- Confirmed in read-only `devdb`: screenshot Shop had 4 reusable Sleeve choices and 12 active snapshots. Regression plus existing independent-copy tests 2/2 PASS; Django check PASS; migration drift reports no changes; project-state validator PASS with existing warnings. Full Catalog API module: 47/50 PASS; unrelated outstanding results are a global Design publish role expectation mismatch (403 vs expected 200) and two Arabic translation tests blocked by WIN1252 encoding in the ephemeral test DB. Tests ran in disposable `test_devdb`; no migration or application-data edit. No commit, push, or deploy.

## 2026-10-11 — DESIGN-EDITOR-ACTION-BUTTON-STYLING-01 (local, unpublished)

- Fixed the Design editor's unstyled `Edit name`, `Add selection`, and reference-image `Upload` actions by defining the missing page-scoped secondary-button presentation. Icons and labels align horizontally; controls have visible button surfaces, consistent sizing, and interaction/focus states. No behavior or backend/data changes.
- Validation: frontend Design tests 13/13 PASS; typecheck/build PASS; `git diff --check` PASS (only pre-existing line-ending notices). No commit, push, or deployment.

## 2026-10-11 — SHOP-DESIGN-CATALOG-SOURCE-AND-EDIT-01 (local, unpublished)

- Root cause: Shop Design editor fetched global-only Option Groups, so Shop-owned Family mappings appeared absent even though Catalog/Measurements had the configured garment parts. The Design editor now reads the same Shop-scoped Family → Option Group configuration and active Style Options used by Measurements; no duplicate option catalog is introduced.
- Added Draft-only Design-name editing and per-selection replacement, backed by existing Draft name PATCH plus a new Shop/version/selection-scoped PATCH endpoint. Selection edits retain version immutability and tenant boundaries, and refresh the style snapshot/translation/image links transactionally.
- The exact local design shown in the user screenshot exists in `devdb` and its Family currently has 8 configured option-group mappings. Validation: Design frontend tests 13/13 PASS, typecheck/build PASS; three focused backend Design API tests PASS; Django check PASS; OpenAPI reports 0 errors with 29 existing warnings; both schema snapshots parse and match; project-state validator PASS (540 tests discovered). Temp schema-file writing was denied by Windows, so snapshots were updated explicitly. No migration/data change or write to `devdb`, no commit/push/deploy.

## 2026-10-11 — BACKOFFICE-GLOBAL-DESIGN-CREATION-IO-ROOT-CAUSE-01 (local, unpublished)

- Reused the existing Main-Supplier-protected global family and family-filtered global variant reads, then connected the Back Office Create action to the existing Global Design create endpoint and draft editor lifecycle. Removed the stale “API missing” warning.
- Explicitly loaded the existing Designs stylesheet on Back Office Global Design list/editor routes so direct route loads render with the intended page styling.
- No backend, API contract, permission, catalog ownership, lifecycle, tenant data, or schema change. Validation: frontend focused tests 4/4 PASS; typecheck/build PASS; backend focused tests 55/55 PASS; Django check PASS; migration drift clean; OpenAPI 0 errors / 29 existing warnings. No commit, push, staging, or production action.

## 2026-10-11 — BACKOFFICE-MINIMAL-CLIENT-SCOPE-CORRECTION-01 (local, unpublished)

- Removed the operational Measurements surface from Back Office while keeping Shop Measurement routes and selected-Shop measurement-definition configuration intact. Added a read-only selected-Shop Client contact directory with neutral fallbacks for missing contact values.
- Backend authorization now prevents Main Supplier access to operational Client/Related Person measurement profiles/history while preserving measurement-definition configuration. Existing Shop scoping remains authoritative; no schema, migration, data rewrite, or Catalog behavior changed.
- Validation: focused frontend tests 28/28 PASS, typecheck/build PASS; focused backend Client + Measurement/Materials tests 42/42 PASS; Django check PASS; migration drift NOT REQUIRED; project-state validator PASS (test discovery unavailable); `git diff --check` PASS with existing CRLF notices. No commit, push, staging, or production action.

## 2026-10-11 — GLOBAL-CATALOG-ATOMIC-SAVE-02 (local, unpublished)

- Global Catalog family Save now sends translations and ordered group IDs together in one PATCH. The backend locks the global family and applies both through one transaction; the standalone group endpoint remains compatible and shares the same mapping replacement service.
- Added successful combined-save coverage, a controlled second-write failure proving transaction rollback, and a legacy split-request reproduction proving the previous partial-save risk. Updated frontend/API contract tests and API documentation. No migration, bulk rewrite, Shop data change, or Design-history rewrite.
- Validation: backend Catalog API + concurrency + approved-default suite 51/51 PASS; atomic/isolation-focused backend tests 7/7 PASS; focused frontend Global Catalog/API/Shop Catalog/Variants tests 42/42 PASS; frontend typecheck/build PASS; Django system check PASS; OpenAPI 0 errors with 29 warnings (13 unique, existing); generated schema copies byte-identical; migration model drift reports no changes, while history consistency could not be checked because configured local base DB `testdb` is absent; project-state validator PASS (532 discovered tests); `git diff --check` PASS (line-ending notices only). No commit, push, Render/staging/production access, or deployment.

## 2026-10-10 — CATALOG-SHOP-GLOBAL-FAMILY-READONLY-UX-ALIGN-01 (local, unpublished)

- Aligned Shop Catalog controls with the existing ownership contract: global family/group configuration remains visible but read-only, while matching Shop-owned families remain editable. Added focused UI coverage for loading/error states and retained behavior; backend/API/Design behavior unchanged.
- Validation: CatalogPage + VariantsPanel tests 21/21, typecheck/build, and three focused local PostgreSQL backend regressions PASS. No commit, push, or deployment.

## 2026-10-10 — CATALOG-SHOP-FAMILY-GROUP-ISOLATION-FIX-01 (local, unpublished)

- Restricted Shop Catalog family-option-group PUT to Shop-owned families; global family defaults remain readable in Shop context but writable only through Global Catalog. Added a row lock for the Shop-owned family during replacement and documented the 403 contract in OpenAPI/API docs.
- Added multi-Shop tests for global data preservation, Shop B/new-Shop default visibility, Shop A-owned mapping isolation, and Design required/SINGLE/MULTI enforcement. Validation: Catalog API + approved defaults 42/42 PASS; focused Shop/global authorization tests 3/3 PASS; Django check, migration drift, OpenAPI (0 errors), `git diff --check`, and project-state validator (529 discovered tests) PASS. OpenAPI reports existing unrelated warnings. No migration, staging/production DB access, commit, push, or deployment.

## 2026-10-10 — SHOP-ADMIN-USER-ID-AND-PIN-01 (local, unpublished)

- Treat the exact entered `login_id` as the user-facing User ID, preserve letter casing, and retain case-insensitive login/uniqueness. Keep generated `user_code` only as internal identity/legacy alias; Edit Shop and Team do not present it as the user's chosen ID.
- New account onboarding continues to issue a one-time six-digit PIN. Confirmed password changes require exactly six digits and invalidate the old credential/session. Added migration `accounts.0008_login_id_preserve_case` and backend/frontend regression coverage.
- Validation: backend focused 32/32 PASS; full frontend 170/170 PASS (one Catalog pagination assertion failed once, then passed isolated and in full rerun); typecheck/build, Django check, migration drift, diff check, and project-state validator (525 discovered) PASS. Full backend suite: 420 tests, 417 passed, 3 errors. Two captured errors concern a missing admin static manifest entry (`core/api_browser.css`) and a legacy migration test using a schema without `accounts_user.login_id`; the third error detail was truncated and remains unidentified. Black check reports eight backend files would be reformatted; because they contain broader existing changes, no full-file reformat was applied. No commit, push, staging change, or deployment.

## Historical checkpoint — BACKOFFICE-SHOP-ADMIN-USER-ID (superseded)

- The initial version displayed generated `user_code`; the confirmed follow-up now displays the entered User ID stored in `login_id`.
- Validation: focused Back Office tests 6/6, frontend typecheck/build, project-state validator, and diff check pass. No commit, push, or deployment.

## 2026-10-10 — CLOUDFLARE-FRONTEND-ENV-READINESS-09B (local, unpublished)

- Made the Pages API proxy environment-neutral with fail-closed runtime `API_ORIGIN` and exact `FRONTEND_ORIGIN`; added tests for synthetic production routing, no staging fallback, and invalid/missing configuration.
- Documented the same-build/per-environment-runtime model, staging API binding, intentionally unset production target, frontend Pages root/build/output/SPA fallback, and secret boundary. No Cloudflare/Render mutation, deployment, commit, or push.
- Validation: Pages proxy tests 4/4, typecheck and two synthetic environment builds pass with identical bundle hashes, no runtime origins/R2 credential markers in output, diff check and repository validator pass (dirty tree/test discovery warnings). Cloudflare configuration is not externally verified.

## 2026-10-09 — STAGING-AUTH-INTEGRATION-AND-HARDENING-02 (local partial, unpublished)

- Replaced unconditional client-supplied `CF-Connecting-IP` trust with an environment-selected, allowlisted trusted proxy header and a safe `REMOTE_ADDR` default. Render and future native VPS templates select their respective proxy-overwritten single-IP headers; added spoof/fallback tests.
- Local Django check and pure IP-source tests (6/6) pass; `arabic-reshaper==3.0.1` was already declared and imports from `.venv`. Database-backed auth tests are blocked by unavailable local PostgreSQL. Per user direction local DB testing stopped; Render's read-only SQL connector could not reach staging because its source IP is not allowlisted and TLS is required. No allowlist change, staging DB test, staging deploy, commit or push occurred. Render staging is confirmed to auto-deploy commits from `main`, so publication remains withheld pending an approved separate test DB and safe exact-file closure.

## 2026-10-09 — AUTH-DOCS-OPENAPI-RECONCILIATION-01 (local, unpublished)

- Supersedes the earlier email self-service recovery and Shop Admin → VIEWER reset claims without deleting their historical implementation records. Current policy: shared legacy-password + PIN compatibility; active same-Shop STAFF-only reset by Shop Admin; Shop Admin recovery by phone request and Back Office approval; VIEWER has no login.
- Corrected current authentication guidance and the reset endpoint's OpenAPI source description; regenerated both schema copies. Documentation/schema reconciliation only; no runtime authorization or credential behavior changed.

## 2026-10-09 — FRONTEND-MAIN-RECONCILIATION-01 (local, unpublished)

- Added a separate email password-reset request/confirmation flow on main, backed by existing endpoints, while retaining the Shop Admin PIN-reset route. Successful reset clears the current AuthProvider session; generic request success and retryable field-preserving errors are maintained.
- Removed the redundant CSRF bootstrap after successful login. Decoupled Users capacity stats from search/filter/page requests and refresh stats only for Shop/permission or membership-count changes.
- Frontend tests 166/166 across 33 files on final rerun, typecheck/build, project-state validator, and diff check passed. Lint exits 0 with React effect warnings. One unrelated Catalog pagination assertion was intermittent once, then passed isolated and in the final rerun. No backend/schema changes, commit, push, or deployment.

## 2026-10-08 — AUTH-LOGIN-PIN-RESET-IMPLEMENTATION-01 (local, unpublished)

- Added nullable global Login ID and case-insensitive DB uniqueness, six-digit PIN generation/change, shared DB-backed attempt limits, Shop ADMIN phone reset requests with Main Supplier review, Team reset action, Back Office review, and a separate public reset page. Preserved legacy login aliases and the Login page visual structure.
- Added migration `accounts.0006`, focused tests, and regenerated both OpenAPI copies. Django check, migration drift, pure PIN tests, frontend 154/154, typecheck/build, and schema validation passed. PostgreSQL-backed tests and staging verification remain pending; no commit/push/deploy/migration on shared systems.

## 2026-10-08 — EXISTING-AUTH-REQUEST-FLOWS-01 (local, unpublished)

- Added frontend password recovery request/confirmation using existing backend endpoints; maintained generic responses and current auth/session protections.
- Removed the redundant post-login CSRF bootstrap; debounced Users/Clients search and protected results from stale responses; separated Users stats from search/filter/page changes; deferred Design list fetching until picker interaction.
- Frontend tests 135/135 across 29 files, typecheck and build passed. Lint exits 0 with `set-state-in-effect` warnings. No backend/API/schema changes, authenticated email-flow verification, commit, merge, push, or deployment.

## 2026-10-08 — CURRENT-STATE-MIGRATION-INTEGRITY-01 (local, unpublished)

- Hardened `catalog.0018` reverse validation to compare every DesignSelection row, preventing duplicate option-group rows from being collapsed and incorrectly treated as an unchanged seed.
- Added a regression test proving rollback refuses to remove a seed Design with an extra selection in an existing group. No schema operation or new migration was added.
- Fresh disposable UTF-8 PostgreSQL migration replay and full backend suite passed (471/471); frontend full suite 142/142 on final rerun, typecheck/build and Django/migration-drift checks passed. No commit, push, staging/production migration, or cloud write.

## 2026-10-07 — OPT-02 safe baseline remediation (local, unpublished)

- Fixed cached production-settings test isolation while preserving the fail-closed R2 requirement and assertions.
- Restricted unpublished catalog `0018` seed rollback to deterministic seed IDs with guards against changed Designs; added two data-safety regression tests.
- Verified live staging auto-deploy follows `main` pushes. Local backend 470/470 and frontend 142/142 pass; no commit, push, deployment or production setup.

## 2026-10-07 — OPT-01 baseline (local, audit-only)

- Recorded current repository/test/build preflight evidence, one backend test-isolation failure, deployment-trigger uncertainty, and measured-versus-unmeasured performance boundaries in `docs/OPT_01_BASELINE.md`.
- Indexed the user's locked production engineering standard for future risk-based task gates and placed DigitalOcean production as the final separately authorized task. No application behavior, commit, push or deployment change.

## 2026-10-07 — FRONTEND-GARMENT-SYSTEM-INTEGRATION-01 (local, unpublished)

- Connected Shop-owned garment families and option groups to the existing Catalog UI, including family group configuration for ordering, single/multiple selection, and required groups.
- Added Family-level Design support without requiring a Variant, while retaining existing Variant-specific Design flows.
- Integrated Shop-specific family/group rules into Measurements; added inline custom measurement-definition creation and optional association of saved measurement sets with the selected published Design version.
- Added frontend API/UI regression coverage for Shop catalog contracts, family/group configuration, family-level Designs, custom measurement definitions, and Design-version linkage.
- Validation: frontend suite 142/142 across 30 files; typecheck, production build, repository-state validator, and diff checks passed. Lint exits 0 with React `set-state-in-effect` warnings, including several in ClientMeasurementsPage. Authenticated browser verification was not performed. No commit, push, or deployment.

## 2026-10-07 — MEASUREMENT-HISTORY-DESIGN-DEFAULTS-01 (local, unpublished)

- Added audited measurement-version deactivation through the existing set detail route, with explicit confirmation in both measurement-history UIs. Values, snapshots, copy provenance, and version high-water marks are retained; concurrent deletes are serialized and the final active version is protected.
- Made Design creation atomic and retry-safe: style selections are submitted with the draft in one transaction and a client idempotency key prevents duplicate designs after an uncertain network response. Empty style catalogs can still save a named Shop design; a failed style-catalog request cannot be mistaken for an empty catalog.
- Added deterministic, style-only defaults for the existing Kuwaiti Dishdasha, Abaya, and Darraa / Long Dress families. No customer measurements, finished-garment dimensions, ease values, or regional numeric ranges are seeded.
- Documented the ISO 8559 and active ASTM D13.55 evidence boundary in `docs/MEASUREMENT_DESIGN_RESEARCH.md`; body measurements remain distinct from style and finished-garment/ease decisions.
- Added backend API/concurrency/preset coverage and frontend delete/atomic-save/failure/retry coverage. No commit, push, deployment, staging database write, or demo/customer measurement seed was performed.
- Validation: backend 456/456 on clean local UTF-8 PostgreSQL with external storage disabled; focused backend 70/70 plus catalog concurrency 6/6; frontend 133/133 across 29 files with typecheck/build passing and lint exiting 0 with existing effect warnings; repository validator PASS with 456 discovered and validator tests 31/31; Django, deploy, migration drift, OpenAPI, Black, Flake8, schema parity, and diff checks passed.

## 2026-10-06 — CLIENT-WORKSPACE-HISTORY-01 (local, unpublished)

- Reworked Client detail into a responsive workspace with compact contact summary, accessible action hierarchy, isolated loading/errors for Client and Related Persons, and a measurement profile/version history panel.
- Connected history to existing APIs only: lazy profile expansion and paginated versions, exact immutable set detail, confirmed immutable copy, compare, and per-version worksheet PDF. Kept measurement values read-only in this view and left backend contracts/schema, application shell, Design, and Orders unchanged.
- Follow-up from the local screenshot: imported the base Client stylesheet in the detail route (it had only been pulled in by the separate ClientsPage route), and replaced the premature “Unavailable garment” collapsed-card fallback with “Measurement profile” while names resolve lazily.
- Hid the root viewport scrollbar visually at the user's request while retaining native scrolling for older versions.
- Matched Related Persons to the Measurements workspace card structure and refined its count, Add action, and empty/loading states without changing form or API behavior.
- The Client detail Measurements action now opens the existing measurement-entry workflow in-place, retaining client/shop/person context and avoiding duplicate client-context requests; direct measurement routes remain supported.
- Replaced the legacy flat Measurements workflow presentation with distinct, consistently bordered step/review cards matching the Clients workspace, with visible step badges on desktop and mobile; behavior is unchanged.
- Combined workflow steps 01 Client and 02 Garment into one bordered panel: side-by-side with a central divider on laptop/large tablet widths, stacked with one shared border on smaller screens.
- Kept Add Related Person on the Client overview only; the measurement view retains existing people for wearer selection without offering management there.
- Moved Measurement profile into the preceding Style card and hid the Related Persons side panel in Measurement view; client overview and backend remain unchanged.
- Body Measurement entry now defaults new fields to `INCH`. The main unit switcher applies the selected unit to every field; each field remains independently editable afterward. Numeric values are never converted, and the backend payload still carries an explicit unit per saved value.
- The separately requested backend-persisted demo Fabric records were not created: the local database contains no Shop, so no valid Shop-context API target exists. No mock data, direct ORM insert, opening-stock movement, or frontend-only fallback was added.
- Validation: frontend tests 125 passed (29 files), typecheck/build passed; lint exited 0 with React effect warnings. Focused inventory API regression suite passed 16 tests on a disposable PostgreSQL database. Authenticated browser verification, commit, push, deployment, and Fabric data creation were not performed.

## 2026-10-06 — STAGING-STYLE-IMAGE-MIGRATION-FIX-01

- Corrected PostgreSQL migration ordering after the staging startup failed because migration `0015` attempted to create the primary-image unique index while its backfill still had pending trigger events. `0015` now ends after the deterministic primary-image backfill; additive migration `0016_styleoptionimage_one_primary` creates the partial unique constraint in the next transaction.
- Added a PostgreSQL migration regression test that exercises pre-existing StyleOptionImage rows, both migrations, and deterministic primary selection. Published implementation commit `5e17a4dc973efb2eee371dec8de01cefcdb56dc3` to `main` and `staging`; exact-SHA Project State Validation run `37445684348` passed. Render staging deploy `dep-db2c8jm7bikc73dr7800` is live, both migrations logged `OK`, and live/ready health checks returned 200. Full PostgreSQL suite 448 passed; focused migration test 1 passed; Django check, migration drift, OpenAPI validation, Black, and Flake8 passed. Production was not deployed.

## 2026-10-05 — STARTUP-PRIVATE-IMAGE-01 one-image-per-Style-Option

- A Style Option (for example, a specific Collar or Cuff) now has exactly one current reusable image. Shop and Main Supplier upload forms accept a single file; uploading another image atomically makes it current. API serialization and new Design snapshots expose/capture only that current image.
- Existing image rows and private objects are retained; prior DesignSelectionImage source links are not rewritten or deleted. Migration `catalog.0015_styleoptionimage_primary` marks one deterministic current image per option and enforces at most one current image at the database level. DesignVersion reference galleries remain multi-image.
- Local validation: backend focused tests 3 passed; frontend tests 99 passed; typecheck and production build passed. No remote publication or deployment verified in this change.

## 2026-10-05 — STARTUP-PRIVATE-IMAGE-01 Shop upload transaction fix

- Render logs for the authenticated upload attempt showed `TransactionManagementError`: `ShopPrivateMediaUploadView` called `_lock_shop_write_context()` (`select_for_update`) without a transaction. Wrapped the write endpoint in `transaction.atomic` and added a `TransactionTestCase` regression proving the upload authorization runs inside a transaction. No storage credentials, schema, migration, or business-rule change. The source image has not yet completed an authenticated upload/visual verification.

## 2026-10-05 — STARTUP-PRIVATE-IMAGE-01 image failure diagnosis and staging R2 preparation

- Render traceback confirmed `FileNotFoundError` for a private image under `/app/private-assets`; read-only R2 `HeadObject` for the logged key returned 404. Added fail-fast staging R2 requirement and an explicit opt-in gate for legacy frontend multipart fallback, with regression tests. No model, migration, auth, permission, or business-rule change. R2 settings were merged into the existing staging service without exposing their values; its environment-only deployment is live on the previously published SHA `a873884eb6a96470a368154a3ea2162bb73b42de`. The R2-aware code is still local and awaits publication. The user saved the bucket CORS policy; the browser preflight for `http://localhost:5173` + `PUT` + `content-type` returned 204. The verified original image is present locally and needs upload through the app after the R2-aware code is live.

## 2026-10-05 — Local frontend performance audit (unpublished)

- Audited request flows without an authenticated browser session. Prepared frontend-only reductions for redundant Global Catalog, Shop context, Measurement design, Inventory, and Back Office Shop search requests, with regression tests on the isolated frontend branch. No business/backend contract or permission change, local `main` merge, push, or deployment is claimed. Warm staging-proxy health timing remains nonzero; the exact final validation and remaining browser-verification limit are recorded in `docs/HANDOFF.md`.

## 2026-10-05 — Local backend/frontend integration checkpoint

- Committed the previously validated private-media/measurement worksheet and Shop Style Option API backend work locally, then merged `frontend/parallel-foundation` into local `main` without conflicts. The frontend branch was pushed first; the integrated `main` has not yet been pushed, and no exact-SHA CI or staging migration/deployment is claimed.
- `main` publication requires an explicit staging side-effect decision: checked-in Render configuration requests automatic staging deploys on commit, while live auto-deploy and required R2 secret provisioning are not independently verified. The local integrated validation results and remaining remote latency limit are recorded in the current handoff.

## 2026-10-05 — Frontend integration and local loading optimization checkpoint

- Committed and pushed the existing Measurement/R2 UI and Shop Style Option preview/editor on `frontend/parallel-foundation` at `9ff32bc30d94744cfa0c432e4bb1c57d4182a20c`; the branch is not yet merged into `main`. The editor supports Shop-owned English-name PATCH, additive private reference-image upload and preview, progress/retry feedback, and read-only global options.
- Reduced unnecessary client work with route-level lazy loading, one viewport-appropriate login illustration, concurrent Styles-tab requests without unrelated Family fetches, and in-flight deduplication of identical default GET requests (no persistent cache). Frontend checks: 99 tests, typecheck, and build passed; lint exits 0 with existing React effect warnings. The initial built JavaScript entry fell from about 591 KB to 399 KB raw; local API calls still traverse the staging proxy and measured roughly 0.4–0.7 seconds for health/CSRF.
- Local backend regression suite: 445 PostgreSQL-backed tests passed with test settings and local DB host; validator tests 37 passed; Django check PASS; migration drift reports no model changes with base `testdb` history unavailable; changed Python Black/Flake8 PASS. Backend commit/`main` merge/push, exact-SHA CI, and shared-environment migrations were not completed at this checkpoint. The checked-in Render config requests staging auto-deploy on `main` commits, but the live provider setting is unverified.

## 2026-10-05 — CATALOG-STYLE-OPTION-EDIT-API-01

- Added Shop-scoped `PATCH` translation editing for Shop-owned Style Options while preserving the existing `is_active` lifecycle update. Updates merge only supplied locales; code, group, owner, and omitted translations are preserved. Existing Shop write authorization and foreign-Shop 404 behavior remain in force.
- No image replacement/deletion, model, migration, dependency, frontend, commit, push, or deployment change. Existing private reference-image upload remains additive.
- Validation: focused Catalog API 32 passed; full PostgreSQL-backed suite 445 passed; repository validator PASS (445 discovered); validator tests 37 passed; Django check PASS; no migration generated (local migration-history consistency could not be checked because base `testdb` is absent); OpenAPI validation 0 errors/29 warnings (13 unique); changed-file Black/Flake8 PASS; frontend suite 95 passed, typecheck/build PASS, lint exits 0 with existing React effect warnings; schema copies and `git diff --check` PASS.

## 2026-10-04 — MEASUREMENT-R2-UI-01 local validation

- Added local/R2 private catalog-media storage integration, short-lived actor/Shop/target-bound upload tickets, and private A4 Measurement/Design worksheet PDF export. Added Unicode font shaping/rendering support for Arabic/Urdu, Bangla, and Malayalam names; no billing record or persisted Design↔Measurement relation is created.
- Corrected Windows private-media key separator/length handling; added additive migration `catalog.0014_private_reference_path_length`. `catalog.0013_privatemediaupload` and `0014` passed disposable UTF-8 PostgreSQL tests. No shared/staging/production database was migrated.
- Validation: focused Catalog/Measurement tests 54 passed; full PostgreSQL-backed suite 442 passed; repository validator PASS (442 tests discovered); validator tests 37 passed; Django system check PASS; production deploy check 0 errors/13 warnings; migration drift PASS; OpenAPI 0 errors/29 warnings (13 unique); changed Python Black/Flake8 PASS. Frontend 89 tests passed; typecheck/build PASS; lint exits 0 with React effect warnings; build has a large-chunk advisory.
- R2 bucket verification/listing succeeded. The three compressed sample JPEGs were uploaded to the existing private `birky-desgin-test/` prefix and individually verified by size/content type; no Shop/StyleOption business records were created. No commit, push, CI run, or deployment occurred.

## 2026-10-03 — MEASUREMENT-E2E-01 remediation and publication

- Integrated the existing Client, Garment Family/Variant, grouped Style Options, Shop Design, Client/Related Person Measurement Profile, localized measurement definitions, explicit CM/INCH entry, immutable version history, copy, compare, and final review APIs into the local frontend Measurements workflow. Fabric selection reads ACTIVE stock availability for display only and does not reserve or deduct inventory. No fake Work record or workflow stage was introduced.
- Added the deterministic Men’s Shirt style seed: Sleeve, Collar, Cuff, Pocket, Placket, Embroidery, and Color are mapped to Men’s Shirt, and Classic Formal Shirt, Smart Casual Shirt, and Modern Evening Shirt are published global Standard Shirt templates. The data migration is reversible for historical migration tests without changing schema.
- Cleared stale unsaved measurements whenever client, Family, Variant, or saved Profile context changes; removed the implicit CM default; selected the adjacent latest versions for compare; guarded duplicate profile/design/measurement/copy mutations; and render every available private option image. API origins are now supplied only by server-side environment configuration rather than a compiled staging URL.
- Extended the read-only Shop context response with the current membership's assigned Work Function codes so the UI can honor the existing `MEASUREMENT` STAFF gate. Main Supplier has no membership assignment and receives an empty list. Updated API/OpenAPI artifacts and architecture/API documentation. No model migration.
- Validation: PostgreSQL-backed full application suite 433 passed; focused Measurement API/concurrency/default-template and Shop context suite 40 passed. Frontend tests 84 passed; typecheck/build passed; lint exits 0 with existing React state-in-effect warnings. Django system check passed; production deploy check had 13 drf-spectacular warnings; OpenAPI had 0 errors and 29 warnings (13 unique). No model changes detected; local migration-history consistency could not be verified because configured base database `testdb` is absent. Backend/frontend `git diff --check` and schema artifact parity passed.
- Backend remediation and the merged frontend integration are published to `main` at `a619ca6cd395cf47f85bc09b75ee34dc977dfb6c`; local and remote SHA parity was verified. GitHub Actions Project State Validation run `37114613711` passed for that exact SHA. Render staging deployment and authenticated browser verification remain pending because Render account access is unavailable in this workspace.

## 2026-10-03 — GARMENT-VARIANTS-01 (frontend phase)

- Added the Catalog Variants second tab using real paginated backend APIs: debounced server-side search, Family/status/source filters, backend count, pagination, compact responsive cards, and the existing Family → View Variants continuation. The existing Shop context API supplies role-aware Shop controls.
- Added Shop Variant detail/edit/archive/reactivate and create flows, read-only Global Variants in Shop Catalog, and Main Supplier global Variant create/edit/archive/reactivate/set-default management under the existing Back Office Global Catalog.
- Connected Variant detail “View Designs” to the exact backend `?family=<uuid>&variant=<uuid>` filter. Kept translation editing progressive, preserved RTL/theme tokens and drawer keyboard handling. No thumbnails were added.
- Validation on `frontend/parallel-foundation`: typecheck PASS; seventy frontend test cases across 13 files PASS; lint exits 0 with six existing warnings in unchanged shared files; production build PASS with a bundle-size advisory; `git diff --check` PASS. Authenticated viewport verification remains pending user login. No commit, push, merge, or deployment.

## 2026-10-03 — GARMENT-VARIANTS-01 (backend phase)

- Completed the additive Variant backend contract: active/archive lifecycle and migration `catalog.0011_garmentvariant_is_active`; authoritative list/detail DTOs; Shop and Main Supplier detail, translation, lifecycle and default routes; paginated server-side search/family/status/source filters; exact Variant Design filters; and archived Variant rejection for new dependent records.
- Preserved historical references and the existing Family/Measurement implementation. Variant thumbnail is deferred; no inventory/cost semantics were introduced.
- Validation: full PostgreSQL application suite 430 passed; focused Catalog/Measurement/Variant API/concurrency suite 56 passed; validator tests 30 passed; repository state validator PASS (430 tests discovered); Django checks, migration drift, OpenAPI, Black/Flake8, schema parity and diff check PASS. OpenAPI reported 0 errors/28 warnings (12 unique). Before the later staging authorization, migration was tested only in disposable UTF-8 PostgreSQL databases; the staging application is recorded below.

## 2026-10-03 — GARMENT-VARIANTS-01 staging deployment

- Published implementation commit `ca1285cd73814139350c076ce426c2273f4ca81a` to `main` after exact-SHA Project State Validation run `37099853077` passed. Manually deployed Render staging service `birky-staging-api` as deploy `dep-db095b0u01pc739cl4n0` (live; auto-deploy remains off).
- Startup applied the Family image/status migration and Variant active-state migration successfully. `/api/health/live/` and `/api/health/ready/` returned 200. Unauthenticated requests to Family detail and Shop Variant detail returned 401, confirming both routes are registered; authenticated browser verification remains pending. Production was not deployed or migrated.

## 2026-10-03 — GARMENT-FAMILIES-01 (backend phase)

- Completed backend Phase A for global Garment Families: reversible ACTIVE/ARCHIVED lifecycle, immutable code and safe Main Supplier translation editing, detail response, database-wide case-insensitive code/translated-name search before pagination, and a single optional private optimized Family thumbnail with authenticated content delivery.
- Archived Families are hidden from ordinary browse and rejected for new Shop Variant/Design, Global Design Template, Measurement Profile, and Measurement Definition mapping creation. Existing records and Measurement history remain available. The existing ordered global Family → Option Group mapping contract is preserved.
- Added migration `catalog.0010_garmentfamily_image_garmentfamily_image_byte_size_and_more`; validated by disposable UTF-8 PostgreSQL tests only. Updated OpenAPI/schema and canonical API/database/state docs. Expanded the repository validator for the explicitly authorized Family Catalog scope.
- Validation: full PostgreSQL application suite 419 passed; Catalog API suite 27 passed; Catalog/Measurement API and concurrency regressions 23 passed; validator tests 35 passed; repository validator PASS (419 tests discovered); Django check and production deploy check passed (12 existing OpenAPI warnings); migration drift clean; OpenAPI 0 errors/28 warnings (12 unique); Black, Flake8, schema parity, and `git diff --check` passed. No commit, push, merge, or deployment.

## 2026-10-03 — GARMENT-FAMILIES-01 (frontend phase)

- Integrated Shop Garment Families browsing with authenticated list/detail/image APIs, debounced server search, API pagination count, a compact responsive card and detail sheet, applicable Style Groups, and existing Family-filtered Shop Variants/Design routes. Shop users receive no Family management controls.
- Added Main Supplier Back Office Family creation/editing with stable read-only code, optional localized names/descriptions, ACTIVE/ARCHIVED filter, reversible lifecycle controls, authenticated private image upload/replace/remove, and ordered Family → Option Group mapping. Existing Style Group and Global Style Option surfaces remain available.
- Frontend validation on `frontend/parallel-foundation`: typecheck PASS; 59 tests PASS; build PASS; diff check PASS; lint exits 0 with six warnings in unchanged shared files. Unit/component tests cover API contracts and lifecycle, Family image, mapping, search, pagination, detail, and Shop view behavior.
- Authenticated visual checks at 1440–320 viewport sizes were not performed because the local browser is at sign-in and credentials remain for the user to enter. No commit, push, merge, deployment, or shared/staging/production database migration.

## 2026-10-03 — T4-02 Catalog and Design API completion endpoints

- Added authenticated, password-change-complete API routes for Main Supplier-only Family and Option Group creation with atomic translated records, a paginated Main Supplier-only global variant selector, and visibility-safe Global Design Template detail retrieval.
- Added authorization, translation validation, variant filtering/isolation, and draft/published visibility tests. No schema migration or business-rule changes. Regenerated and synchronized both OpenAPI artifacts.
- Validation: 5 focused endpoint tests passed; Catalog API regression suite had 22 passes and one pre-existing Arabic-data test excluded because the local PostgreSQL cluster is WIN1252 encoded. Django system check passed; deployment check had no errors and 18 environment/schema warnings; migration drift was clean; OpenAPI had zero errors and 28 warnings (12 unique); schema artifact parity, Black, Flake8, `git diff --check`, repository validator, and its 28 tests passed. No deployment or migration occurred.

## 2026-10-03 — Catalog and Designs frontend integration

- Connected the existing Catalog and Designs frontend modules to the current `apps/catalog` API contracts, corrected request/response field and upload/query parameter mismatches, and removed mock-data success fallbacks so API failures are visible.
- Implemented the supported catalog and design actions, pagination, reference-image uploads, and API contract tests. Backend API gaps (Family/Option Group creation and the global variant list needed for Global Template creation) remain explicitly unavailable in the UI; no guessed endpoint or mock behavior was added.
- Updated the repository state validator to recognize the previously approved and completed T4-03A Catalog backend during a later frontend-only handoff, with regression coverage.
- Validation on frontend commit `fa9e84b55fe8d5f9b62aee12459138edf790233d`: typecheck PASS; 47 tests PASS; production build PASS; lint PASS with six pre-existing warnings; repository state validator PASS with its documented test-discovery warning; `git diff --check` PASS. No authenticated staging browser E2E or deployment was performed.
- The feature branch was merged locally into `main` and published to GitHub `main` with the T4-02 API work in commit `3d17271dae879f5f26ceba5b46c413bf2d501310`. The remote SHA was verified. No deployment occurred.

## 2026-10-02 — DJANGO-ADMIN-UX-01 local implementation

- Added a native Django Admin index organized by Business, Garments & Designs, Measurements, Materials, Users & Access, and System; applied the requested BiRKy Admin branding and minimal responsive/dark-mode-compatible status styling.
- Explicitly gated internal Admin models to persisted active Main Supplier superusers. Added read-only catalog/design/measurement/material inspections, Shop client history views, clear list/search/filter layouts, and selected relations to avoid N+1 lookups. Private FileFields are excluded from Admin forms and displays.
- Preserved the existing safe Shop update/lifecycle path and User creation/deletion/password protections. Added 18 focused Admin tests. No model/schema/API/business-rule/dependency/frontend/deployment changes. Implementation commit `608362d6509b286ba0daa9ede4e33d39d2888a6c` passed exact-SHA GitHub Actions Project State Validation run `37017703294`.

## 2026-10-02 — T4-03 Measurements and Materials implementation

- Added Shop-scoped measurement definitions, localized labels, approved Men's Shirt and Kuwaiti Dishdasha seed templates, Client/Related Person measurement profiles, immutable versioned measurement sets and values, copy/compare operations, and minimal Shop-owned Material references.
- Added explicit Shop-path APIs with role/function checks, cross-Shop non-disclosure, PostgreSQL locking/constraints, regression and concurrency tests, and refreshed the generated OpenAPI artifacts. No frontend, inventory, Work/Order, billing, Phase 5, or deployment work was included.
- Published as implementation commit `d9ca27bbab8587c2da5ceb8c1f61f913087fdc48`; exact-SHA Project State Validation run `37006408609` completed successfully. No deployment occurred.

## 2026-10-02 — T4-02 Catalog and Designs local implementation

- Added the Shop-scoped `apps/catalog` foundation: locked global garment/style defaults, translations, Shop custom catalog records, reusable private image references, versioned designs, immutable published snapshots, independent design/template copies, and Main Supplier global-template controls.
- Shop-local design publication is allowed to an active Shop ADMIN or active STAFF assigned `STITCHING`; “Tailor” is this STAFF function, not an access role. No Work, measurement, material, billing, frontend, deployment, or production storage provider was added.
- Local validation: catalog/docs/browser focused suite 30 passed; full PostgreSQL-backed application suite 350 passed; migration drift and Django checks passed; OpenAPI had zero errors (23 existing warnings). GitHub Actions validation is tracked against the exact publication commit SHA.

## 2026-10-01 — STAGING-MAIN-ADMIN-BOOTSTRAP-01 implementation

- Added a staging-only, one-time Main Supplier Admin bootstrap management command and disabled-by-default Render entrypoint switch. It guards the exact staging environment/database, requires explicit confirmation and strong temporary credentials, creates no Shop, forces password change, and treats existing email/phone collisions as safe no-ops without changing accounts.
- Added focused tests for account creation, role/password-change flags, environment/database/confirmation/secret guards, duplicate protection, and repeat-run immutability. No migration or frontend changes.
- Validation: focused tests 9 passed; Django system check and no-migration-drift check passed; repository validator passed; Black, Flake8, Git Bash syntax check, and `git diff --check` passed. The broader local 330-test run did not complete because the local PostgreSQL server exited during the run; a retry then failed after that server was unavailable. Exact-SHA Project State Validation run `36887320909` passed for `9b8fbc94741d85e018be10fdee41b34bd283af52`.
- Pushed to `main` as `9b8fbc94741d85e018be10fdee41b34bd283af52`. Render deploy `dep-dav83hhsrm7s73e9llsg` created the requested staging Main Supplier Admin, with no Shop created. A duplicate same-SHA deploy was a safe no-op. Cleanup deploy `dep-dav84r3bc2fs738dghi0` is live after disabling the bootstrap switch and blanking all four temporary inputs; `/api/health/ready/` returned 200. No secret values are recorded here.

## 2026-10-01 — BACKOFFICE-01 local implementation

- Added a Main Supplier-only Back Office shell that reuses the current frontend sidebar, header, theme, color palette, and responsive layout. The Work page mock data is not reused.
- Connected Shop listing, search/filter/order/pagination, create, detail/update, and activation lifecycle to the existing `/api/v1/tenants/` API. Shop creation atomically creates its first ADMIN; the returned User ID and temporary password are shown once in memory and are not persisted by the frontend.
- Added `is_main_supplier_admin` to the auth user profile so the frontend can route Main Supplier users into Back Office; server permissions remain authoritative. No model migration or environment-variable change was needed.
- Local evidence: frontend 31 tests passed, typecheck and production build passed, lint has one existing `react(set-state-in-effect)` warning in `src/App.tsx`; backend full suite passed 257 tests before adding one focused first-admin login/password-change test, which also passed separately. OpenAPI refreshed with zero errors and 23 warnings (7 unique). Django check, no-migration-drift check, Project State validator, and `git diff --check` passed.
- Backend implementation commit `a0bd06ec272440f687fef68a157568466821a664` is published on `main` and live on the existing Render staging service as deploy `dep-dav6emo473hc73dqm7t0`. The readiness and CSRF bootstrap endpoints returned 200 after deployment. Render auto-deploy remains disabled.
- Frontend feature commit `def2c60d` is local on `frontend/parallel-foundation`, with canonical `main` merged normally. It is not pushed: this branch is configured as the Cloudflare Pages client-preview source, and pushing triggers a deployment. Explicit approval for that preview publish is still needed.

## 2026-10-01 — API-BROWSABLE-PORTAL-01

- Added a Main Supplier-only, DRF-style API browser at `/api/browse/`; root now opens it, while Swagger remains at `/api/docs/`.
- The browser builds its endpoint list from the protected OpenAPI schema, restricts requests to same-origin `/api/v1/`, requires Bearer JWT where the API requires it, and keeps access tokens in page memory only. Existing Django-session exclusion, API permissions, CSRF bootstrap, and refresh/logout protection remain unchanged.
- No business endpoint, model, migration, dependency, or React frontend was added.
- Validation: 10 focused documentation/browser tests and all 319 PostgreSQL-backed application tests passed. Published at implementation commit `304c9666f680e3e32aa05e4545b44aa049963e19`; exact-SHA Project State Validation run `36862739900` succeeded. No deployment occurred.

## 2026-10-01 — API-DOC-REFRESH-01

- Protected `/api/docs/` and `/api/schema/` with the existing Django Admin/Main Supplier session and forced-password-change policy; responses are private and no-store.
- Root now redirects to the protected docs portal. Removed the stale starter API test page, unused `/api-auth/` route, and development-only DRF session authentication so docs sessions do not authenticate business API calls.
- Refreshed the committed OpenAPI schema from the current `v1` implementation and clarified authentication, CSRF, pagination, Shop scope, and Client/Related Person contracts. No business API behavior, models, or migrations were changed.
- The repository is public and `schema.yml` remains committed; live route protection does not make this file confidential. No repository-visibility change or deployment was performed.
- Local verification before publication: focused tests 62 passed; full PostgreSQL-backed suite 315 passed; repository validator and validator tests 27 passed; Django checks and migration drift check passed; schema validation had zero errors (23 warnings); Black, Flake8, and `git diff --check` passed. Published at implementation checkpoint `9e93a77754ac03839d038e5e3a32458208bc02e9`; exact-SHA Project State Validation run `36850074419` succeeded.

## 2026-10-01 — T4-01 published

- T4-01 Clients and Related Persons is complete and published at `e4e5e4126d60bfb563fbd25fbf0baab9e85963f9`; exact-SHA Project State Validation run `36796609814` succeeded.
- T4-02 remains unstarted and unauthorized. No frontend source or deployment was included.

## 2026-09-30 — Phase 4 activation and T4-01 implementation

- Phase 4 was explicitly activated and only T4-01 Clients/Related Persons was authorized. Canonical BR-CLIENT-002 records the approved role-access matrix. T4-01 work began under that authorization; its later completion/publication is recorded above. Do not infer that future tasks are authorized.
- The runtime app follows the current Django `apps.*` layout at `apps/clients`; frontend source remains isolated and unchanged.

## 2026-09-30 — PHASE4-PARALLEL-UNBLOCK-01 roadmap dependency clarification

- Clarified that backend Phase 4/5/6 delivery may progress independently of frontend completion; each frontend domain slice remains contract-first and follows its accepted backend contract.
- Preserved the historical `PHASE4-RESEQUENCE-01` and `FRONTEND-DELIVERY-LOCK-01` entries; the UI Reference Gate, Dashboard Last Rule, phase boundaries, and separate confirmation gates remain unchanged.
- Documentation/roadmap only. No application or frontend source changes. This entry records the approved roadmap correction, not a Phase 4 activation or T4-01 implementation.

## 2026-09-30 — PHASE4-RESEQUENCE-01 roadmap dependency update

- Parked the existing parallel frontend foundation without touching, deleting, resetting, or merging its branch/worktree. Formal frontend work remains gated until the later sequence and individual confirmations.
- Documentation/roadmap only. Phase 4 was not activated; T4-01, F7-01, F7-01A, application code, and frontend source were not started or changed.

## 2026-09-30 — T3-05A final staging verification and closure

- Added a fail-closed command for rotating credentials of only the already-existing deterministic staging smoke identities, with staging/database/explicit-confirmation guards and fixture integrity checks. The fixture itself was preserved; no Users/Shops/memberships/Work Functions were recreated or changed.
- Local PostgreSQL suite: 294 passed; focused rotation/bootstrap tests: 39 passed. Repository validator and validator tests passed; Django/deploy/migration/OpenAPI/format/lint/shell/diff checks passed. Implementation commit `b29a897897d35ec9163c510456bd9197b8a4f6e1` passed exact-SHA Project State Validation run `36667104952` (294 application tests).
- Render final deployment `dep-dau9ptlg1s2s73c2foig` is live on the same application SHA. Live login, cookie, refresh/logout/revocation, CORS, health, Main Supplier access, and bidirectional Shop endpoint/object isolation checks passed. Migration, static collection, and Gunicorn startup were confirmed; no secret exposure was found. Temporary credential variables are blank, bootstrap/rotation flags are false, and the existing synthetic fixture remains.
- T3-05A is complete. The Render provider hostname remains active; custom-domain DNS/TLS and real frontend browser integration remain deferred. No frontend, Production, worker, Redis/Celery, or Phase 4 work was performed.

## 2026-09-30 — T3-05A partial live staging verification

- Added a guarded synthetic Main Supplier/Shop A/Shop B fixture using staging-only secrets; live provider-hostname login, refresh CSRF rejection/success and rotation, Secure/HttpOnly/SameSite=Lax refresh-cookie attributes, authenticated logout CSRF rejection/success, and Shop-context isolation were observed. Main Supplier context access to both Shops succeeded; each Shop's foreign context returned 404.
- Bootstrap flag was set false and the three credential variables were blanked after fixture creation; cleanup deploy is live and health checks return HTTP 200. No real customer data or credentials were committed/documented. T3-05A remains in progress because broader membership/User-ID/stats/Work-Function/direct-object isolation and definitive cookie-clear/old-token revocation checks remain outstanding. Custom-domain DNS/TLS and real frontend browser integration remain deferred.

## 2026-09-30 — T3-05A custom-domain deferment and live staging state

- Recorded the approved operational decision that BiRKy does not currently control `birky.com`: `https://birky-staging-api.onrender.com` is the active T3-05A backend; `https://api-staging.birky.com` and `https://staging.birky.com` are reserved/planned targets only. Removed the unowned custom API domain from the repository's Render Blueprint configuration without changing host validation, CORS/CSRF policy, resource plans, or deployment behavior.
- At this earlier checkpoint, recorded Render resources and the initial live deployment in the environment, project-state, handoff, architecture, security, Phase 3 playbook, and staging runbook; authenticated lifecycle and Shop-isolation evidence had not yet been collected. T3-05A remained in progress.

## 2026-09-30 — T3-05A Staging Backend Foundation (published; CI green)

- Prepared an explicit secure staging settings profile, PostgreSQL URL support, Render Blueprint with manual deployment and isolated Free PostgreSQL, bounded database startup readiness, provider PORT/Gunicorn configuration, CSRF bootstrap, guarded staging reset command, smoke checker, and staging runbook.
- Local PostgreSQL-backed application suite: 255 passed; staging-focused tests: 28 passed; auth/CSRF lifecycle regressions: 7 passed; validator tests: 23 passed. Staging Django/deploy checks, migration drift, OpenAPI (zero errors), Black, Flake8, and `git diff --check` passed. Docker build and disposable local PostgreSQL-backed container smoke passed.
- Black/Flake8 passed for new staging and validator Python modules; whole-file checks of touched legacy files report existing style findings and no broad reformat was applied. Published as `9af6424116ebba12896d90d032c36bd25328a4d0`; Project State Validation run `36652187336` succeeded for that exact SHA. No application business models or migrations, dependency changes, frontend, worker, storage, or Production resources were added. At that repository-publication checkpoint, no Render account/resource, DNS/TLS, or live staging deployment had been verified or performed.

## 2026-09-30 — T3-05 Back-office / Shop API and Admin hardening (published; CI green)

- Implemented membership-scoped Shop discovery/profile reads, role-limited statistics, Main Supplier-only Shop settings and lifecycle operations, exact User-ID member lookup, capacity lower-bound enforcement, and hardened Django Admin paths without changing the approved business rules.
- Added API/Admin, authorization, regression, and PostgreSQL concurrency coverage. Full PostgreSQL-backed suite: 231 passed; repository validator and 14 validator tests passed; Django check, production deployment check, migration drift check, OpenAPI validation (zero errors), Black, Flake8, and `git diff --check` passed. OpenAPI/deployment checks report nonfatal serializer type-hint and role-enum warnings.
- No migration or dependency changes. Published as commit `3d21a0943006cd866bc19bc728cbec05daae1630`; exact-SHA Project State Validation run `36614638187` succeeded. T3-05A, Phase 4, frontend, and deployment work have not started.

## 2026-09-29 — T3-04C Work-Function foundation (published; CI green)

- Added normalized membership-scoped persistence for the approved seven-code catalog, additive migration with no backfill, Shop ADMIN-only GET/PUT management, Shop isolation, actor attribution, transactional set replacement, and soft-deleted assignment history.
- Added model/API/lifecycle/migration and PostgreSQL concurrency regression coverage. Focused tests: 19 passed; full PostgreSQL-backed suite: 211 passed (172 warnings). Repository validator, validator tests, Django/migration/OpenAPI checks, Black, Flake8, and diff check passed. Published implementation commit `dfbf6eecdbcd36c014a45a5d297c26e4e27a4113`; GitHub Actions Project State Validation run `36605653294` succeeded for that exact SHA.
- Updated current product-definition, decision, API, architecture, database, security, business-rule, phase, development-plan, project-state, and handoff descriptions. Phase 4 stage/function mapping remains deferred; T3-05 and later tasks have not started.

## 2026-09-29 — Parallel Frontend Foundation Track governance

- Documented a separate same-repository frontend branch/worktree strategy while retaining `main` as the backend/integration source and canonical cross-project documentation owner.
- Approved early frontend foundation preparation as distinct from Phase 7/F7-01 completion; F7-01/F7-01A retain their existing T3-05A sequencing. Frontend work must be mock-first for unfinished APIs, backend-authorized, and respect the single-owning-Shop ordinary-account model.

## 2026-09-29 — T3-04B User-Scope remediation (published)

- Replaced the superseded one-global-User/multi-Shop assumption with one immutable owning Shop per ordinary account; separate Shops require distinct accounts even for the same real-world person.
- Added Shop-owned account creation and reset authority, atomic Shop/first-ADMIN account creation, same-Shop membership enforcement, and guarded ownership backfill/database consistency protections.
- Added/updated account-scope, membership, Shop creation, reset, and migration-preflight regression tests. Pre-publication local validation: focused User-Scope suite: 9 passed; PostgreSQL-backed full application suite: 192 passed. Validator, validator tests, Django check, migration drift and OpenAPI pass; OpenAPI/deploy checks report two nonfatal role-enum naming warnings. New Python files pass Black/Flake8; broad lint/format checks on touched legacy files still show existing style findings.
- Updated current architecture, business rules, API, database, security, phase plan, project state, and handoff docs. Published as commit `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c`; GitHub Actions Project State Validation run `36591864481` completed SUCCESS for that exact SHA. T3-04C and later tasks remain unstarted.

## 2026-09-29 — T3-04B Remediation publication checkpoint

- Restored the T3-04B transactional membership and global User-lifecycle services on the verified post-revert `main` baseline. Shop creation commits with exactly one active first ADMIN; membership User/Shop identity is immutable; ADMIN hierarchy/cardinality, locked User validation, global deactivation invariants, undo ordering, and approved capacity/reactivation rules are enforced in services.
- Disabled direct Django Admin Shop creation and membership writes; routed User Admin deactivation through the global lifecycle service. Updated inactive-Shop Shop Admin denial to 403, corrected exact normalized undo error assertions, and updated reactivation-at-capacity expectations.
- Added Shop creation, ADMIN/User lifecycle, Django Admin, multi-Shop, and PostgreSQL separate-connection race regression tests. No migration, dependency change, T3-04C, T3-05, or later-phase implementation.
- Local validation before publication: focused remediation 77 passed; T3-04A/T3-03/membership/migration regressions 39 passed; full PostgreSQL-backed suite 183 passed (113 warnings); validator 183 discovered and 14 validator tests passed; Django/deployment checks, OpenAPI, Black, Flake8, and diff check passed. Require Project State Validation SUCCESS for the exact publication SHA before T3-04C.

## 2026-09-29 — T3-04A Global Identity / User-ID / Authentication

- Implemented the confirmed global identity foundation locally: generated permanent User ID, canonical optional email/phone identity for normal users, required trimmed first name, alias-based authentication, contact safeguards, controlled credential reset, and hard-delete denial.
- Added a preflight/backfill migration that refuses unsafe legacy rows rather than fabricating names or contacts; added identity, authentication, API, and migration-preservation regression coverage. Existing UUID primary keys, JWT UUID identity, memberships, and audit references are preserved.
- Read-only local database preflight found no existing User/superuser/Shop rows or email/name issues. After preflight, the local PostgreSQL database successfully applied required tenant migrations and `accounts.0004_t304a_global_identity`; no production database was accessed.
- Focused identity/authentication suite: 29 passed; T3-02A compatibility regression: 10 passed. Full PostgreSQL-backed application suite: 167 passed (155 warnings); repository validator PASS; 14 validator tests passed; Django system/deployment checks, migration drift, OpenAPI validation, Black and Flake8 for newly added Python modules, and `git diff --check` passed. A broader Flake8 run over touched legacy files still reports findings and is not reported as clean.
- At the original T3-04A task-time checkpoint, changes were local-only and GitHub CI had not run; they were subsequently published. T3-04B and later tasks were unstarted at that historical checkpoint.

## 2026-09-28 — T3-04 Scoped Querysets and Object Permissions

- Updated `TenantScopedMixin` to require authorized T3-03 context, verify actor/URL/compatibility alias consistency, filter by the trusted Shop, and force Shop ownership on create/update.
- Bound `IsTenantMember` object checks to the selected Shop for ordinary members and Main Supplier; added temporary UUID/FK/soft-delete test proof for direct IDs, lists/counts, Main Supplier scope, writes, and fail-closed mismatches.
- No business models/endpoints, migrations, dependencies, global Tenant/member API changes, or T3-05 work. Future business endpoints must adopt and prove the shared boundary.
- Initial task-completion validation (before publication): focused tests 28 passed; full application suite 152 passed (144 warnings); repository validator PASS (152 discovered); validator tests 14 passed; Django check, migration drift, OpenAPI, Black, Flake8, and `git diff --check` passed. The implementation was subsequently committed/pushed; current publication and CI evidence is recorded in the 2026-09-29 entry below.

## 2026-09-29 — T3-REBASELINE-01 Phase 3 business architecture and state sync

- Reconciled approved global User/User ID, optional normal-user contacts, admin-grade contacts, multi-Shop membership, ADMIN cardinality/authority, Shop visibility/lifecycle, capacity, and membership-scoped Work Function rules. Marked them as confirmed target policy, not implemented code; assigned prerequisite work to T3-04A–T3-04C before T3-05.
- Updated product, architecture, API/security/database, Phase 3/4/7/8 plans, project state, handoff, and decision/business-rule records. Preserved T3-03/T3-04 path-context and isolation contracts and the fixed V1 workflow.
- Corrected current T3-04 repository state: live verification showed `main`/`origin/main`/remote main in parity (derive current SHA from Git); GitHub Actions Project State Validation run #36511111586 succeeded for the published baseline. Current documentation changes are local/uncommitted and are not covered by that CI result.
- Validation: repository validator PASS (152 discovered); validator tests 14 passed; Django check PASS; migration drift reports no changes with local PostgreSQL unavailable; full pytest collected 152 but was blocked by unavailable PostgreSQL; `git diff --check` PASS. Documentation audit found 52 unique Business Rule IDs and consistent task sequencing. No application source or migration changes.
- Documentation/planning only. No application code, migrations, dependencies, tests, frontend, staging, commit, or push.

## 2026-09-28 — T3-03 Tenant / Shop Request Context

- Added a request-local Shop context resolver and reusable DRF context base that authenticates before Shop authorization and preserves the mandatory password-change gate.
- Added `GET /api/v1/shops/{shop_id}/context/` with UUID path selection, selected-Shop membership role, and explicit Main Supplier context; no Shop defaults are returned.
- Added the approved uniform non-disclosing 404 contract for foreign, unauthorized, inactive, soft-deleted, unavailable, and nonexistent Shops; authentication failures retain 401.
- Updated `IsTenantMember` to require the resolved request context and added focused context/security regressions. T3-04 query/object isolation remains out of scope; no business model, migration, dependency, or global Shop-visibility policy changed.
- T3-02A current-state documentation was reconciled while updating task handoff; dated historical decision/audit records were retained and labelled historical where needed.
- T3-03 was committed and pushed; GitHub Actions Project State Validation Run #19 passed for the implementation commit.

## 2026-09-28 — T3-02A Account and preference foundation

- Implemented the confirmed account/authentication foundation: unique optional E.164 phone and email-or-phone login, Main Supplier Admin-only account creation/phone management, one-time no-store initial credentials with forced password change, and email reset with refresh-session revocation.
- Added nullable User locale, `system|light|dark` appearance, and nullable Shop default locale/timezone/currency; ordinary authenticated global Shop reads omit the new defaults.
- Added additive accounts/tenants migrations and regression tests; preserved UUID identity, existing memberships, email login, JWT/CSRF/refresh rotation/blacklist protections, and production throttle rates.
- Updated current API, architecture, database, security, phase plan, project state, and handoff descriptions. No T3-03 or later-phase implementation, CI push, or GitHub push was performed.

## 2026-09-28 — T3-02A-BUSINESS-DECISION-LOCK

- Recorded human-approved account creation, email/phone identity and management, credential lifecycle, Shop timezone/currency/settings authority, nullable locale, and appearance rules in `docs/BUSINESS_RULES.md` and `docs/DECISIONS.md`.
- Reconciled architecture, product definition, API, database, security, phase plan, project state, handoff, and agent instructions. Explicitly recorded that public User creation remains enabled in current code and email-only login remains implemented; T3-02A must reconcile these behaviors.
- Repaired the identified Windows-1252 em-dash encoding bytes in `BUSINESS_RULES.md` and `DECISIONS.md` without changing their business meaning; strict UTF-8 validation now passes.
- Documentation/business-rule reconciliation only. No application source, migrations, dependencies, deployment, commit, or push; T3-02A and T3-03 remain unimplemented and unauthorized.

## 2026-09-28 — V1-ENVIRONMENT-LOCK

- Locked the V1 environment model as LOCAL → STAGING → PRODUCTION. Removed the separate Preview tier from the approved architecture.
- Recorded company name BiRKy and staging domains `staging.birky.com` / `api-staging.birky.com`. Production domains `app.birky.com` / `api.birky.com` are reserved but not provisioned.
- Renamed T3-05A from "Backend Preview" to "Staging Backend Foundation" and F7-01A from "Client Preview Frontend" to "Staging Frontend & Client Review Checkpoint".
- Moved F7-01/F7-01A earlier in the dependency sequence (immediately after T3-05A) to enable early client staging and auth/i18n/theme browser validation.
- Updated Phase 9 to reuse the same Staging environment for formal release-candidate validation after reset/reconfiguration.
- Added BR-ENV-001 and BR-ENV-002 environment/deployment business rules.
- Documentation/roadmap only: no application code, migrations, or deployment was changed.

## 2026-09-28

- Completed and committed the T3-02-REMEDIATION implementation with security and integrity fixes; subsequent closure review identified CI PostgreSQL connectivity and test throttle-cache isolation issues.
- Restricted User API targeting, aligned Shop writes with Main Supplier policy, protected membership lifecycle state, verified real authentication throttling, restored duplicate CORS test coverage, expanded CI health checks, and wired production CORS environment propagation.
- Added regression coverage; 120 application tests are collected. The initial CI result and full-suite details were corrected during the closure follow-up below; no migrations were created.
- Left global User administration ownership, ordinary-user Shop read visibility, Shop DELETE semantics, and T3-03 work unresolved/deferred.

## 2026-09-28 — T3-02-REMEDIATION validation closure

- Mapped the PostgreSQL service port to the GitHub Actions runner so the PostgreSQL-backed application suite can connect to its service.
- Isolated auth-throttle cache state in the API tests that expect baseline login responses; production throttle rates and behavior were not changed.
- Corrected current-state claims in project state, handoff, architecture, security, and README documentation.
- Local validation: 120/120 application tests passed; 69 focused tests passed; 11 repository-validator tests passed; repository validator and Django system check passed; migration check reported no changes.
- Historical note: the earlier run failed on PostgreSQL connectivity. This was superseded by the later verified green GitHub Actions run 36415017163 on `0ac45e1e80606539210ff8f7ad5a653eb4ba5215`; that run does not validate subsequent local documentation changes.

## 2026-09-28 — V1 roadmap update

- Updated the approved V1 requirement-to-task map while preserving the ten-phase architecture and task-level confirmation gate.
- Added planned Phase 3 tasks T3-02A and T3-05A, and Phase 7 task F7-01A; assigned localization, RTL/LTR, Light/Dark/System, tailoring, billing, documents, audit, observability, preview, testing, staging, production, and Post-V1 requirements to their owning plans.
- Created `docs/POST_V1_ROADMAP.md` and `docs/ENVIRONMENTS.md`.
- Documentation/roadmap only: no application code, migrations, or deployment was authorized or changed.

## 2026-09-27

- Completed PRE-P3-02 documentation-only governance correction.
- Locked the V1 model as exactly one Main Supplier / Main Admin above multiple isolated Shops.
- Clarified that External Suppliers are Shop-owned non-user records with no login, tenant role, or global/shared directory.
- Hardened the Phase 3 T3-01 brief and preserved the legacy Tenant compatibility decision gate.
- No Phase 3 business implementation, models, migrations, APIs, or application source changes were made.

## 2026-09-25

- Bootstrapped repository continuity documentation and agent instructions.
- Recorded the verified baseline: empty Git repository with no Django implementation.
- Established the SGTP V1 Target Final Product / Definition of Done, including the supplier/shop hierarchy, Tailor Management workflow, technical capabilities, boundaries, and end-to-end validation requirements.
- Realigned the architecture, development plan, project state, handoff, and agent instructions to the approved target without changing application code.
- Clarified the project-wide confirmation gate: phase confirmation activates scope only; each task requires a separate explicit task confirmation and ends with a stop boundary.
- Added the missing Phase 7–10 Antigravity implementation playbooks without changing the approved architecture, scope, order, or implementation decisions.
- Canonicalized target implementation paths, domain boundaries, deployment direction, and refresh-token handling across the phase plan while preserving current-starter descriptions.
- Documented the required CSRF strategy decision point for cookie-based refresh; the concrete mechanism remains a Phase 2 selection, implementation, and validation task.
- Corrected project state to distinguish the existing starter foundation from unimplemented Phase 1 work; recorded Phase 1 as independently audited and ready, but inactive and unconfirmed.
- Recorded approved URL-path tenant context (`/shops/{shop_id}/...`) and Primary Client ownership for Related Person billing; retained Phase 2 CSRF mechanism selection and validation as an explicit task.

## 2026-09-27

- Added the dependency-light `scripts/verify_project_state.py` validator, focused validator tests, and a GitHub Actions state-validation gate.
- Added an evidence-backed repository-state completion rule to `AGENTS.md` and synchronized current Phase 2/B2-05, 47-test, and Phase 3-not-started documentation claims.
- Activated Phase 1 and completed Task F1-01 (Repository and dependency baseline). Established virtual environment and verified manage.py check. Documented validation limitations: existing starter lint violations remain and pytest is blocked by unavailable PostgreSQL; no application source cleanup was performed.
- Completed Task F1-02 (Environment management and settings split) by modularizing core/settings.py into ackend/config/settings/{base,dev,prod,test}.py, updating .env.example, and ensuring safe failure on missing secrets.

## 2026-09-28 — T3-02-REMEDIATION final documentation closure

- Confirmed that the GitHub Actions run for the closure commit successfully passed the application suite, Django system checks, and PostgreSQL integration.
- Confirmed T3-02-REMEDIATION is now fully CLOSED.
- Added agent transition note regarding the shift to Codex for upcoming engineering work, maintaining all established governance and architectural rules.
## 2026-10-02 — T4-03A Inventory & Stock Foundation (completed locally)

- Added additive Shop-scoped inventory classification, explicit legacy-Material enablement, zero-start materialized balances, immutable stock ledger, explicit opening/stock-in/adjustment APIs, inventory selector/history, and archive stock protection. Existing T4-03 measurement history remains separate; no Work, costing, procurement, frontend, or deployment behavior is included.
- Validation: focused inventory plus T4-03 measurement regressions 41 passed; full PostgreSQL-backed suite 409 passed; repository validator PASS (409 tests discovered); validator tests 32 passed; Django system check PASS; production `check --deploy` has no errors and reports 12 warnings; migration drift: no changes; OpenAPI: zero errors, 28 warnings (12 unique); Black, Flake8, schema artifact parity, and `git diff --check` PASS. Migrations were exercised on the disposable PostgreSQL test DB. At the time this implementation entry was recorded, publication was still pending; no deployment occurred.

## 2026-10-02 — T4-03A publication and exact-SHA CI

- Published implementation commit `1e6e79a60a7337a43e6bb73c47aacf0c947c6570` to `main` with message `feat: add shop inventory and stock ledger foundation`.
- GitHub Actions Project State Validation run `37045373602` completed successfully for that exact SHA. Local `main`, `origin/main`, and GitHub `main` matched after push; no deployment or shared/staging/production migration occurred.

## 2026-10-07 — GARMENT-SYSTEM-BACKEND-01 (local implementation)

- Added tenant-owned garment families and option groups, scoped APIs, explicit family/group selection policy, nullable Design variant, and optional published DesignVersion association on immutable measurement snapshots. Existing global catalog rows and legacy option-group ID input are retained.
- Validation: migration 0019 applied in the disposable PostgreSQL test DB; focused 65 catalog/measurement tests PASS; full `apps/` suite PASS (390 tests); Django check PASS; migration drift check PASS; OpenAPI generation zero errors/29 warnings (13 unique), both schema artifacts identical; Black/Flake8/diff check PASS; Project State Validator PASS (459 tests discovered). No commit, push, deployment, or frontend edits.
# Unreleased — staged Garment Variant retirement

- Made active Design creation/listing Garment Family based.
- Made measurement mappings and new profiles Garment Family based.
- Removed Variant configuration and selection from active frontend workflows.
- Preserved legacy Variant data and historical Design/Measurement references.
- Added guarded migration `0024_retire_variant_measurement_mappings`.
