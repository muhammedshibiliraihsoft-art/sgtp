# Handoff

## LOCAL-TO-STAGING-SYNC-01 (2026-10-12; candidate in progress)

- Source is local `main` at `d6560c7c5457df11820686c6b6f3f204338c530a` plus unpublished user work; live Render API runs `staging` at `e1a4aafe85308b96d329d963c91e4ccac17a9c26`, with commit auto-deploy. A separate worktree/branch `codex/local-to-staging-sync-01` holds the selected release candidate; neither source worktree was reset or merged.
- Corrected three stale release-gate tests: Global Design publish authenticates as Main Supplier, staging bootstrap checks the defined PIN variable, and historical Membership migration test uses an explicit compatible accounts migration state and historical User model. Full isolated PostgreSQL suite: 546/546 PASS. Upgrade rehearsal from staging migrations through catalog 0017–0023: PASS; migration drift: clean. Candidate frontend: 189/189 tests, build, and lint pass; lint warnings remain. Runtime-only dependency audit: zero vulnerabilities.
- Live staging DB contents/ledger and recovery path remain unverified because the Render read-only SQL connector cannot reach the DB through its TLS/IP allow-list. The database is Free with no managed backup. Cloudflare Pages staging frontend and exact origin are not provisioned/verified. No candidate push, staging deploy, account creation, or staging DB write occurred.
- Next: inspect staged candidate for secrets/config drift, publish a review PR and obtain exact-SHA CI, then establish staging DB recovery and frontend origin before merging into auto-deployed `staging`. Use the guarded one-time account bootstrap only after the target is verified, and clear its temporary environment variables immediately afterward.

## MEASUREMENT-PROFILE-SAVE-AND-RECOVERY-01 (2026-10-12; local, unpublished)

- Root cause: the filtered definitions API resolves effective mappings from both a Shop-materialized family/variant and their global `template_source`; `_allowed_definitions()` during save validated only direct mappings on the Shop-owned family. This made inherited default fields display correctly but fail with “Definition is not available for this garment.”
- Fix: save validation now accepts generic mappings for the local/source family and variant-specific mappings for the selected local/source variant. No mapping rows are copied and no schema change is needed. Frontend profile-create failures refresh the current person's profiles and active family catalog: a concurrently/already-existing matching profile is selected and its measurement history loads; a family ID absent from the refreshed catalog is cleared. Backend duplicate protection remains in place, and another garment remains independently selectable.
- Validation: Measurement/Materials API 34/34 PASS, including materialized Shop family profile creation, measurement save, and history GET; frontend Measurement page 15/15 PASS, typecheck PASS, production build PASS; changed Python Flake8 and scoped `git diff --check` PASS. `black --check` stalled without output and was stopped.
- Database safety: tests created/destroyed only disposable `test_testdb` using `DJANGO_SETTINGS_MODULE=backend.config.settings.test` and local PostgreSQL host. `.env` identifies application DB `devdb`, which was not queried or changed. No migration, production/staging access, commit, push, or deployment.
- Next: refresh the local Measurement flow and test a Shop-materialized garment: create/select its profile, save one inherited default value, then confirm the new version and value appear in history. If a stale-family response occurs, refresh the page once if the active family catalog itself has changed.

## GARMENT-FAMILY-DEFAULT-MEASUREMENTS-01 (2026-10-12; local, unpublished)

- Added additive data migration `catalog.0023_seed_abaya_darraa_measurement_defaults`. It leaves the existing Men's Shirt and Kuwaiti Dishdasha baselines unchanged and adds family-level Abaya fields (Full Length, Shoulder Width, Bust/Chest, Waist, Hip/Seat, Sleeve Length, Upper Arm/Bicep, Armhole, Sleeve Opening, Neck Opening) plus the same Darraa / Long Dress baseline with Hem Width.
- These are field definitions only: no customer values, size tables, ease allowances, grading values, or historical measurement records are generated or rewritten. Defaults are family-level and returned for every variant. The Shop `Add measurement` UI now sends `variant_id: null`, so added measurements also belong to the garment family.
- Validation: Measurement/Materials API 34/34 PASS before the final mapping-scope adjustment; focused tests on a fresh disposable DB 2/2 PASS after it; approved-default/concurrency 8/8 PASS; frontend Measurement page/API 28/28 PASS after the UI update. Django check and migration drift PASS; migration Flake8/compile and scoped diff checks PASS. `black --check` stalled without output and was stopped.
- Database safety: configured application DB was verified as `devdb`, user `devuser`, local PostgreSQL `127.0.0.1:5432`. Tests used only disposable `test_devdb`. After the user requested the defaults be available in the local app, migration `0023` was applied to `devdb`; applied migration and resulting family mappings were verified. Staging/production were not accessed. No commit, push, or deployment.
- Next: refresh the local BMS Measurement page and verify defaults appear for each family and stay the same across variants. A measurement added from the page should be available to the whole family.

## GARMENT-DEFAULT-MEASUREMENT-STRUCTURE-RESTORE-01 (2026-10-11; local, unpublished)

- Root cause: seeded global Measurement definitions/mappings existed, but Shop default catalog materialization creates Shop-owned Families/Variants linked by `template_source` and did not copy Measurement mappings. The definitions endpoint filtered mappings only by the selected local `family_id`, so the approved source defaults disappeared. A regression test also exposed that shared `MeasurementDefinition.sort_order` may differ from a family's approved mapping order; the API now returns the effective mapping order for family-filtered results.
- Fix: the endpoint resolves active Family and Variant in the explicit Shop/global scope, and looks up applicable mappings for the local Family plus its source Family; for a linked local Variant it also includes mappings for that source Variant. The global/same-Shop definition queryset remains enforced. No mapping rows are copied, no schema migration or frontend change is needed, and new Shop-local definitions receive their declared order on their mapping.
- Validation: Measurement/Materials API tests 33/33 PASS (includes defaults, family/variant selection, source-variant additions, supplemental custom field, deduplication/order, two-Shop isolation, and immutable saved-measurement history); approved default + concurrency tests 8/8 PASS; existing frontend Measurement page/form tests 25/25 PASS, typecheck/build PASS. Django check PASS; `makemigrations --check --dry-run` reports no changes, but the configured base DB `testdb` is absent so migration-history consistency could not be queried. Flake8 PASS, scoped `git diff --check` PASS, and project-state validator PASS (545 discovered tests; dirty-tree warning). Black was not fully verified: test file has one pre-existing formatting discrepancy outside this task; a later Black process stalled and was stopped. No schema migration or frontend work.
- Test settings were configured with `DB_NAME=testdb`, `DB_HOST=db`; `db` is the local Docker PostgreSQL service. The test run explicitly used local `127.0.0.1` and only created/destroyed disposable `test_testdb`. Configured application DB `devdb` was not written. No staging/production access, commit, push, or deployment. Existing dirty worktree changes were preserved.
- Next: no further implementation is authorized by this task; user may refresh the local Measurement flow to manually confirm the approved garment fields render.

## STYLE-OPTION-SNAPSHOT-LEAK-FIX-01 (2026-10-11; local, unpublished)

- Root cause: the local `devdb` Shop `sleeve` group had 4 reusable global options and 12 active Shop-owned Design snapshots. `copy_design_version()` intentionally stores independent StyleOption/image snapshots linked by `source_style_option`; the Shop options list did not distinguish those internal snapshots from reusable Catalog entries, so repeated names/copy codes appeared in the Design chooser (and other consumers of that list).
- Fix: shared `_shop_catalog_style_options()` now exposes only global and Shop-owned reusable options with `source_style_option IS NULL`. The Shop style-option list, Design create/add/replace selection inputs, and Shop option edit route use this queryset. Existing Design snapshot rows and links are retained; no bulk cleanup or schema change.
- Tests: new regression checks picker omission and rejects snapshot IDs through Design creation, add, and replace. New regression + existing independent-copy test: 2/2 PASS. Full Catalog API module: 47/50 PASS; one unrelated permission expectation mismatch (global Design publish returned 403 while the test expects 200), and two Arabic translation tests fail because the ephemeral test database is WIN1252 rather than UTF-8. Django system check PASS; migration drift reports no changes; project-state validator PASS with existing dirty-tree/test-discovery warnings. Initial global-Python test attempt could not import `arabic_reshaper`; rerun passed under project `.venv`. Test runner created/destroyed only `test_devdb`; configured app DB `devdb` was queried read-only.
- No migration, application-data edit, commit, push, staging, or production action. Local Design page may be refreshed to confirm the Sleeve chooser now shows only four reusable options; snapshot rows remain in existing Design records.

## DESIGN-EDITOR-ACTION-BUTTON-STYLING-01 (2026-10-11; local, unpublished)

- Root cause: the Design editor used the shared class `secondary-button`, but the frontend had no base CSS rule for it. As a result, `Edit name`, `Add selection`, and image `Upload` rendered as unframed/misaligned controls while `Publish version` looked correct because it uses the separately styled `primary-button`.
- Fix: added scoped Design-page secondary button styles for inline icon/label alignment, border/surface, minimum height, hover/disabled/focus states; upload label shares the same treatment. No behavior, API, backend, or database changes.
- Validation: frontend Design tests 13/13 PASS; typecheck/build PASS; `git diff --check` PASS (only pre-existing line-ending notices). No commit, push, staging, or deployment.
- Next: refresh the local Design editor and visually confirm all three controls now read as proper buttons.

## SHOP-DESIGN-CATALOG-SOURCE-AND-EDIT-01 (2026-10-11; local, unpublished)

- Root cause verified against the screenshot’s exact Design UUID: its Shop Family has 8 configured FamilyOptionGroup rows in local `devdb`, but the Design editor queried the global-only option-group list. `getOptionGroups()` omitted Shop-owned Family mappings; Measurements already used the correct `getShopFamilyOptionGroups(shopId, familyId)` contract.
- Design editor now reads those same Family mappings and active Shop-visible Style Options, avoiding duplicate garment-part definitions. Draft Design name is editable; each Draft selection has an Edit action to replace its option within the same configured group. Published versions remain immutable.
- Backend added a Shop-context, version-scoped selection PATCH. It validates active option, same Shop/global visibility, same configured option group and Draft status, then updates the captured label/translations/reference-image links transactionally while retaining soft-delete recovery records.
- Validation: frontend Design suite 13/13 PASS, typecheck/build PASS; focused backend Design API tests 3/3 PASS; backend test runner system check clean. The failed earlier iteration ran only against disposable `test_devdb`; it was destroyed. Local `devdb` was queried read-only and not changed. No migration, deployment, commit, or push.
- Next: user can refresh local `/designs/<id>` and confirm the Catalog-configured garment parts appear; then use Edit on the Design name or any Draft selection. If this test Family truly lacks a required part, configure it once in Catalog and both Measurements and Designs will read it.

## BACKOFFICE-GLOBAL-DESIGN-CREATION-IO-ROOT-CAUSE-01 (2026-10-11; local, unpublished)

- Root cause: the UI warning incorrectly asserted no global-variant list API existed. `/api/v1/catalog/variants/` already provides the authorized Main Supplier global-only list, and `getAllGlobalVariants(family)` already consumes it. The Create UI was absent. Separately, Back Office Design list/editor did not import `Designs.css`, so direct navigation showed unstyled content.
- Fix: Global Design page now loads active global families, fetches only active global variants for the selected family, submits to the existing `POST /api/v1/catalog/design-templates/` contract (including explicit family-level `variant_id: null`), and opens the existing editor for the returned draft. Added direct stylesheet imports on both Back Office Design routes. No backend/API/schema/permission/lifecycle change; no migration or Shop data changes.
- Tests/checks: new page tests and existing editor suite 4/4 PASS; frontend typecheck/build PASS. Backend Catalog variant + Design API tests 55/55 PASS; Django check PASS; migration drift `No changes detected`; OpenAPI validation 0 errors / 29 existing warnings. `git diff --check` PASS (line-ending notices only); project-state validator PASS (539 tests discovered; worktree dirty, remote unavailable warning).
- No staging/production access, commit, push, or deploy. Existing broadly dirty `main` worktree preserved.
- Next: user may manually check `/backoffice/designs` locally.

## BACKOFFICE-MINIMAL-CLIENT-SCOPE-CORRECTION-01 (2026-10-11; local, unpublished)

- Root cause: Back Office had a Measurements nav item and route rendering the Shop's operational `ClientMeasurementsPage`; `MeasurementAccess` relied on a shared service that intentionally admitted Main Supplier requests without Shop membership. The existing selected-Shop Clients API returns only contact identity plus normalization/timestamps, not measurement history, values, garment, variant, Design, or style selections.
- Fix: removed only Back Office Measurements nav/route; added a read-only basic Client directory linked from the selected Shop detail. It reuses the existing Shop-scoped client endpoint and renders missing name as Guest, missing phone/email as em dash. Backend now denies Main Supplier on Client/Related Person measurement profile/history endpoints while preserving the existing explicit-Shop measurement-definition configuration permission and Shop role behavior. No data/model/API migration or Catalog changes.
- Focused frontend tests: 28/28 PASS; typecheck/build PASS. Backend Client + Measurement/Materials suite: 42/42 PASS; Django check PASS; migration drift NOT REQUIRED. Project-state validator PASS (test discovery unavailable; documented test count not independently checked). `git diff --check` PASS (existing CRLF notices only). No staging/production, commit, push, or deploy. Worktree was already broadly dirty; unrelated local changes were preserved.
- Next: record the focused backend test and validator outcomes; no further implementation is authorized by this task.

## GLOBAL-CATALOG-ATOMIC-SAVE-02 (2026-10-11; local, unpublished; implementation complete)

- Re-verified the Global Catalog's former two-write flow: `GlobalCatalogPage.submitFamily` called family PATCH, then group PUT. Changed the UI to send translations plus ordered `option_group_ids` in one PATCH; it uses the returned detail and keeps the edit state recoverable on failure.
- Backend now validates the combined payload, locks only a global family, and applies translations plus mappings under one outer transaction. The legacy standalone group PUT remains supported and reuses the same mapping write service. Shop-owned families and Shop endpoints are not changed; authorization stays Main Supplier-only.
- Added tests for successful one-request save, controlled second-write rollback, a reproduction of the former split-request partial state, and unauthorized actor rejection. Updated API docs and generated schema artifacts. Validation: backend Catalog API/concurrency/approved-default suite 51/51 PASS; atomic/isolation/authorization selection 7/7 PASS; focused frontend Global Catalog/API/Shop Catalog/Variants suite 42/42 PASS; typecheck/build PASS; Django system check PASS; OpenAPI 0 errors / 29 warnings (13 unique) and schema copies byte-identical; project-state validator PASS (532 tests discovered); `git diff --check` PASS (line-ending notices only). Migration drift reported no model changes; the migration-history check warns because local base DB `testdb` is missing. Local Docker Postgres was used only for Django's disposable test database; Render/staging/production DBs untouched. No migration, commit, push, or deployment.

## CATALOG-SHOP-GLOBAL-FAMILY-READONLY-UX-ALIGN-01 (2026-10-10; local, unpublished)

- Shop Catalog family/group editing now requires the API-provided `tenant` owner to match the current Shop; VIEWER remains read-only. Global family configuration stays visible, with disabled controls, a small Main Supplier ownership hint, and no Save action. The save handler also guards ownership; backend 403 enforcement remains unchanged.
- Changed `frontend/src/features/catalog/CatalogPage.tsx` and its focused tests. No API/type/backend/schema/Design changes. Tests cover visible/read-only global configuration, preserved Shop-owned save, family-detail loading/error states, and existing Design navigation behavior.
- Validation: Shop Catalog + VariantsPanel tests 21/21 PASS; frontend typecheck and production build PASS; three local PostgreSQL backend isolation/authorization/design regressions PASS; `git diff --check` PASS. No commit, push, Render access, or deployment. Main worktree contains extensive pre-existing unrelated modifications; all were preserved.

## CATALOG-SHOP-FAMILY-GROUP-ISOLATION-FIX-01 (2026-10-10; local, unpublished)

- Root cause: the Shop Catalog family/group PUT accepted a global family and replaced shared `FamilyOptionGroup` rows, even though those mappings have no Shop owner. Shop GET still needs to read global defaults; Shop writes are now allowed only for a family owned by the selected Shop, under a row lock. Global management remains available on the Main Supplier Global Catalog route.
- Added multi-Shop regression coverage for Shop A global-write denial/data preservation, Shop B and new-Shop global defaults, Shop A-owned family isolation, and Design required/SINGLE/MULTI validation. Existing unmapped-selection and Main Supplier global-update tests remain in the Catalog batch.
- Local PostgreSQL validation: focused 3/3 PASS; Catalog API + approved defaults 42/42 PASS. Django check PASS; migration drift reports `No changes detected`; OpenAPI validation has 0 errors and existing unrelated warnings; `git diff --check` PASS; project-state validator PASS with 529 discovered tests. No model changes/migration. Schema/API docs were reconciled; no staging/production access, commit, push, or deployment.
- Frontend source was not changed in this main-worktree task. A Shop Catalog attempt to save a global-family mapping is rejected server-side with 403; the frontend's current error path remains responsible for displaying that denial. No shared/global mapping can be changed through the Shop route.

## SHOP-ADMIN-USER-ID-AND-PIN-01 (2026-10-10; local, unpublished)

- User-facing User ID now means the Shop Admin/Staff ID entered at provisioning (API/model `login_id`), not generated `user_code`. Preserve its letter casing after trimming outer whitespace; allow only 3–32 ASCII letters/digits/underscore, beginning with a letter. Case-insensitive uniqueness/login matching remains to prevent duplicate identities; `user_code` stays an immutable internal legacy alias.
- Edit Shop fetches memberships on edit entry and shows only entered ADMIN User ID(s). Shop create uses “First Admin User ID” and the success panel returns that exact value. Team user creation/list/reset/promotion labels say User ID and do not display generated `user_code` as a human ID when no entered ID exists.
- New account PIN generation was already six digits. First-login PIN change already validates exactly six ASCII digits and atomically changes the credential, advances auth version, and blacklists refresh sessions; regression tests now check the old PIN cannot log in and the new PIN can.
- Added `accounts.0008_login_id_preserve_case` to widen the DB format constraint; no existing data rewrite. Backend auth/Shop creation tests 32/32 PASS; full frontend 170/170 PASS after the Catalog pagination assertion initially failed once and then passed isolated and in the full rerun. Frontend typecheck/build, Django check, migration drift, `git diff --check`, and project-state validator PASS (525 tests discovered; existing dirty-tree warning). Full backend suite: 420 tests, 417 passed, 3 errors. Captured errors: `apps.common.tests.test_admin_ux.DjangoAdminUXTests.test_admin_index_is_available_to_main_supplier_and_groups_sections` fails because the staticfiles manifest lacks `core/api_browser.css`; `apps.tenants.tests.test_work_functions.MembershipWorkFunctionMigrationTests.test_existing_membership_is_preserved_with_zero_functions` queries `accounts_user.login_id` on a historical test schema without that column. A third error was present but its detail was truncated in tool output and remains unidentified. Black `--check` reports eight backend files would be reformatted; because those files contain broader existing changes, no full-file formatting rewrite was applied.
- No commit, push, staging DB access, or deployment. Local `main` remains broadly dirty with unrelated existing work; preserve all of it.

## Historical checkpoint — BACKOFFICE-SHOP-ADMIN-USER-ID (2026-10-10; superseded)

- The earlier checkpoint displayed generated `user_code` in Edit Shop; the current task replaces that user-facing display with the entered `login_id` User ID.
- Validation: focused Back Office tests 6/6 PASS; frontend typecheck/build PASS; `python scripts/verify_project_state.py` PASS (dirty-tree and test-discovery warnings); `git diff --check` PASS (existing CRLF normalization warnings only). No commit, push, or deploy.

## CLOUDFLARE-FRONTEND-ENV-READINESS-09B (2026-10-10; local repository wiring only)

- Replaced the staging-only Pages proxy binding with `API_ORIGIN`; each Pages environment supplies its own runtime API origin plus exact `FRONTEND_ORIGIN`. The proxy has no staging fallback, validates HTTPS origin configuration, and returns a safe error when required bindings are absent/invalid. Added synthetic-production-routing and missing-binding tests.
- The staging sample uses the active Render staging API. Production values remain unset until the production API and frontend origin are provisioned. No API URL is placed in frontend build variables; R2/private credentials remain backend-only.
- Frontend Pages root is `frontend`, build command is `npm run build`, output is `dist`, and SPA fallback remains `public/_redirects`. The Node version remains specified by `frontend/.node-version`; use a Vite 8-compatible Node release (20.19+ or 22.12+). Provider settings/live bindings were not inspected or changed.
- Validation: Pages proxy tests 4/4; frontend typecheck PASS; synthetic staging- and production-profile `npm run build` outputs matched exactly; output scan found no staging/production runtime origins or R2 credential markers; `git diff --check` PASS; `python scripts/verify_project_state.py` PASS with expected dirty-worktree and unavailable-test-discovery warnings. The build ran on local Node 24.18.0, not the Cloudflare build image. Cloudflare project root/build settings and live runtime bindings remain unverified. No deploy, provider mutation, commit, or push.

## STAGING-AUTH-INTEGRATION-AND-HARDENING-02 (2026-10-09; partial, blocked before deploy)

- Changed auth rate-limit identity selection from unconditional `CF-Connecting-IP` trust to allowlisted `AUTH_TRUSTED_CLIENT_IP_HEADER` configuration, safe `REMOTE_ADDR` default, and socket-peer fallback for missing/invalid configured proxy IPs. Render blueprint uses the Cloudflare edge header; future native VPS uses Nginx-overwritten `X-Real-IP` with loopback Gunicorn. Added spoofed-header and provider-mode source tests.
- `arabic-reshaper==3.0.1` is already pinned in `requirements.txt`; project `.venv` import succeeds. `manage.py check` passes; pure source tests pass 6/6. The focused DB-backed auth test run collected 38 and stopped at its first setup error: PostgreSQL at `127.0.0.1:5432` is unavailable. Local DB testing was stopped per user direction. Render's read-only SQL connector also cannot reach the staging DB because its source IP is not allowlisted and TLS is required; no allowlist change was made and no test used the active application DB.
- Render read-only check: `birky-staging-api` uses branch `main`, auto-deploy trigger `commit`, and currently runs the prior published `main` revision. No commit/push/deploy or Render environment change was made. The dirty main tree contains broad unrelated feature work; staging dependency closure is not yet safe to publish.
- Next: provide a disposable local PostgreSQL test server/database; rerun focused auth lifecycle, PIN-reset, abuse/rate-limit, and concurrency tests; then re-evaluate exact commit closure before any staging push. Actual staging CSRF, pending PIN endpoint, recovery permissions, and UI smoke checks remain unverified.

## Native VPS production wiring (local, unpublished)

`PRE-PUSH-NATIVE-VPS-PRODUCTION-WIRING-08` defines the planned native Linux VPS runtime (initial provider DigitalOcean Droplet; portable to another Linux VPS) in `deploy/` and `docs/runbooks/PRODUCTION_NATIVE_VPS.md`. Nginx proxies HTTPS to loopback Gunicorn; a root-owned external env file supplies production CSRF, database TLS, and private R2 configuration. Production is not provisioned or deployed, and migrations are not automatic. Render staging is unchanged.

## Current authentication source of truth (local, unpublished)

Use the approved rules in `docs/task-plans/AUTH-RESET-MODEL-CORRECTION-01.md`: legacy passwords and new six-digit PINs share the existing credential field; Login ID and approved legacy aliases are supported; Shop Admin resets only active same-Shop STAFF; Shop Admin recovery requires a phone request and Back Office approval; VIEWER cannot sign in; email self-service reset is removed. The email-reset statements in the historical task records below describe prior implementation only and are superseded. Main Supplier/Back Office authority is unchanged.

## Historical handoff — FRONTEND-MAIN-RECONCILIATION-01 (2026-10-09; email reset superseded)

- Historical implementation record: this task added an email password-reset request/confirm screen on `/reset-password`, backed by endpoints available at that time. AUTH-RESET-MODEL-CORRECTION-01 later removed the email self-service flow; it is not current behavior. The separate Shop Admin PIN-reset request flow remains the approved path.
- Removed the redundant post-login CSRF bootstrap. Split Users capacity stats from membership list fetching; stats no longer refetch on search, filters, or pagination and refresh after membership-count changes.
- Existing debounced Users/Clients/Inventory search, stale-response guards, keyboard support, image retry, Shop context and bounded family design lookup were verified and kept.
- Checks: frontend 166/166 tests across 33 files on final rerun; typecheck/build PASS; lint exit 0 with React `set-state-in-effect` warnings; state validator and `git diff --check` PASS. One unrelated Catalog pagination assertion was intermittent once, then passed isolated and in the final full rerun. Backend/email delivery and authenticated browser flow were not verified. Main remains dirty with prior user changes; this task adds no backend/schema work and does not commit, push, deploy, or touch the separate frontend worktree.
- Follow-up: existing login background images emitted by build are 1.57–1.83 MB each. Optimize only after visual-quality review and with an explicit media scope; no asset was rewritten here.

## Historical handoff — AUTH-LOGIN-PIN-RESET-IMPLEMENTATION-01 (2026-10-08; later auth policy applies)

This records the implementation checkpoint before AUTH-RESET-MODEL-CORRECTION-01. Its role/reset descriptions are historical where they conflict with the current policy above.

- Backend: `accounts.0006` adds nullable case-insensitive unique `login_id`, an atomic database-backed auth-attempt bucket, and persistent Shop ADMIN PIN reset requests. Existing UUID/user_code/JWT/auth_version/refresh cookie architecture remains. New account and scoped/global reset credentials are generated six-digit PINs; selected PINs use dedicated validation and Django hashing. Public phone submission creates a generic request only; Main Supplier approval/rejection is server-authorized and approval returns the PIN once.
- Frontend: Login visual markup/CSS is preserved; only Forgot password navigation changed. New reset page, Team Reset PIN, first Shop ADMIN and Team Login ID inputs, one-time PIN results, and Back Office request review were added. Credential result is displayed before optional Work Function assignment can fail.
- Checks: Django system check, `makemigrations --check --dry-run`, 2 pure PIN tests, frontend 154/154 tests, typecheck/build, and generated OpenAPI validation (0 errors; 29 existing warnings) passed. PostgreSQL-backed tests/migration replay are **not verified**: local PostgreSQL and Docker are unavailable, and shared staging DB is excluded from test DB operations. Staging still runs the published older code; no deploy/migration was performed.
- Next: use a disposable PostgreSQL test database to run new and existing backend auth/tenant tests, verify migration/index/approval concurrency and rate limits, then obtain separate publication authorization and verify the new flow against staging. No commit, push, or deploy in this task.

## Historical handoff — EXISTING-AUTH-REQUEST-FLOWS-01 (2026-10-08; email reset superseded)

This task's frontend email recovery work was historical and was later removed by AUTH-RESET-MODEL-CORRECTION-01. Its search, request-efficiency and other non-auth results remain historical records; use current code/state rather than this earlier task as auth guidance.

- Password recovery now has a public frontend request/confirmation flow backed by the existing generic, anonymous reset endpoints. Login no longer performs the redundant second CSRF bootstrap; the security-required CSRF-before-login and CSRF → refresh → `/users/me` restore order are unchanged.
- Users and Clients search are debounced with stale-response protection. Users summary statistics are isolated from search/filter/page changes. Design lists load only when the user opens the Design picker; loading/error/retry and stale-selection handling are included.
- Implementation is in `sgtp-frontend` on `frontend/parallel-foundation`; main application code and backend were not changed for this task. Frontend tests 135/135 across 29 files; typecheck and build passed. Lint exits 0 with React `set-state-in-effect` warnings. Diff check passed.
- Email delivery/authenticated browser reset verification was not performed. No commit, merge, push, deployment, or cloud write. Existing dirty worktree changes were preserved.
- Next: `EXISTING-DOMAIN-PERFORMANCE-MEDIA-01` remains planned and requires explicit confirmation.

## Current handoff — CURRENT-STATE-MIGRATION-INTEGRITY-01 (2026-10-08; local only)

- Reviewed Catalog migrations `0017–0019`, current model state, migration graph/reverse behavior, and Shop-ownership constraints. Fixed the `0018` reverse guard so repeated option-group keys cannot hide extra selection rows; rollback now compares all sorted `(group_code, selected_code)` pairs and preserves changed seed Designs. Added a regression test for an extra selection in an existing group.
- Validation: fresh disposable UTF-8 PostgreSQL database replayed the migration chain. The focused rollback tests passed 3/3; the full backend suite passed 471/471. `django check`, `makemigrations --check --dry-run`, and database verification of migration records plus five partial unique indexes passed. Frontend: full suite 142/142 on final rerun (one earlier run had a transient Catalog pagination failure; isolated test and full rerun passed), typecheck and production build passed.
- Only the task-scoped `0018` migration reverse and its existing regression-test file were edited in code; no schema operation or new migration was added. Other dirty user files were preserved. No commit, push, deploy, staging/production migration, or cloud write. The disposable test PostgreSQL cluster is stopped/removed after validation.
- At that task's checkpoint, Tasks 2 and 3 were separately planned; Task 2 is now complete locally (see handoff above), while Task 3 still requires its own explicit confirmation.

## Tests and checks

- Current AUTH-LOGIN-PIN-RESET-IMPLEMENTATION-01: 476 backend tests discovered; DB-backed suite not run. Two pure PIN tests, Django check, migration drift, frontend 154/154, typecheck/build, and OpenAPI generation/validation passed. PostgreSQL migration replay and staging verification remain pending.
- Historical CURRENT-STATE-MIGRATION-INTEGRITY-01: full suite passed 471/471; fresh disposable UTF-8 PostgreSQL migration replay; focused seed reverse tests 3 passed; Django system check and `makemigrations --check --dry-run` passed at that checkpoint. Catalog migration ledger and expected partial unique indexes were verified then.
- Frontend: 142/142 passed on full rerun after one intermittent Catalog pagination failure (isolated file passed 10/10); typecheck and production build passed.

## Current handoff — OPT-02 (2026-10-07; local only)

- Changed `core/tests/test_settings.py` to import production settings in a subprocess with fake isolated R2 values; assertions for production flags and R2 remain. Production settings source/guard was not changed in OPT-02. Targeted settings tests 14/14 and full backend suite 470/470 pass.
- Changed the uncommitted `catalog.0018` seed migration to give its own global default Designs deterministic IDs; reverse removes only verified seed IDs and refuses changed seeds. Added two historical-model-state regression tests. Older-schema migration rollback tests pass. No migration was applied to staging/production; only disposable local test databases were used.
- Frontend 142/142, typecheck/build pass; lint exits 0 with existing effect warnings. Django check, `makemigrations --check --dry-run`, repository validator (470 discovered), changed-file Black/Flake8, and `git diff --check` pass. Full evidence is in `docs/OPT_02_RESULT.md`.
- Live Render read-only check: `birky-staging-api` follows `main` with `autoDeployTrigger=commit`; startup entrypoint applies migrations. OPT-02 did not alter trigger, commit, push, deploy or cloud data. Other feature work remains dirty and unpublished. Next separately confirmed task is OPT-03 measured hardening; before any publication, explicitly review the candidate and staging deploy effects.

## Current handoff — OPT-01 (2026-10-07; audit-only)

- Confirmed task ended at baseline/preflight. Added `docs/OPT_01_BASELINE.md` and `docs/PRODUCTION_ENGINEERING_STANDARD.md`, plus governance references; no application code, database business data, cloud resources, commit, push or deploy changed in OPT-01.
- At the OPT-01 inspection checkpoint, local `main` HEAD matched `origin/main`; derive the current SHA from Git. The current feature work and three migrations are uncommitted. Full local PostgreSQL backend run: 467 passed, one failed (`test_prod_settings_security_flags`), due to cached base settings despite fake R2 values in the test. Isolated rerun failed the same way. Fix the test isolation without weakening the production R2 guard, then rerun the suite.
- Frontend 142/142, typecheck/build pass; lint exits 0 with React effect warnings. Django check, migration drift, repository-state validator and diff check pass. Authenticated browser performance and low-end/mobile media delivery remain unmeasured.
- Before any `main` push, verify Render's live auto-deploy setting (`render.yaml` says `commit`) and migration/R2 readiness. The proposed low-cost DigitalOcean production setup remains **last**, after safe candidate and restore/operations decisions; no new production environment was created. Next action is present OPT-02 for separate confirmation. Do not begin it automatically.

## Current handoff — FRONTEND-GARMENT-SYSTEM-INTEGRATION-01 (2026-10-07; local only)

- Implemented on the user-selected local `main` checkout. Reused existing Catalog, Designs, and Measurements routes and Shop-scoped backend contracts; no parallel workflow, mock data, commit, push, or deployment.
- Catalog now supports creating Shop-owned garment families and option groups, and configuring each family’s applicable groups, order, single/multiple selection mode, and required status. Measurements consumes those Shop-specific family/group rules and can create a custom measurement definition inline for a selected family/optional Variant.
- Designs now supports Family-level designs without a Variant as well as existing Variant-linked designs. Measurement profiles can display applicable Family-level and Variant-level designs and persist an optional selected published Design-version reference with a saved measurement set.
- Tests cover Shop API contracts, Catalog create/configuration and local pagination, Family-level Design creation, inline measurement definitions, and optional Design-version payload linking. Existing Client workspace/backend changes in the dirty checkout were not altered as part of this task.
- Validation: full frontend suite 142/142 across 30 files; `npm run typecheck`, production build, `python scripts/verify_project_state.py`, and `git diff --check` passed. Lint exited 0 with React `set-state-in-effect` warnings (several in ClientMeasurementsPage). One full-suite run had an intermittent Catalog pagination assertion; the isolated test and subsequent full-suite rerun passed. Authenticated browser verification was not performed. No commit, push, or deployment; no remote publication or end-to-end image/storage validation is claimed.

## Current handoff — MEASUREMENT-HISTORY-DESIGN-DEFAULTS-01 (2026-10-07; local only)

- Measurement-set DELETE is a protected soft deactivation: the Shop/profile/set rows are locked in the established order, the last active version is rejected, and values, localized snapshots, audit fields, `copied_from`, and the monotonically increasing version sequence remain intact. Inactive versions are unavailable to normal list/detail/copy/compare/PDF paths.
- Design creation now accepts selections and an idempotency key in the initial request. Draft, translations, and selections commit together or roll back together; a matching retry returns the original design. Shop-created variants/families remain valid without global defaults, and the UI distinguishes a genuinely empty style catalog from an API failure.
- Migration `0018_seed_remaining_family_design_defaults` adds style-only presets to the resolved active default/fallback global variants for Kuwaiti Dishdasha, Abaya, and Darraa / Long Dress. It creates no measurement profiles, sets, or values. Research sources and unfilled numeric-data gaps are recorded in `docs/MEASUREMENT_DESIGN_RESEARCH.md`.
- Validation used local PostgreSQL with UTF-8 and all R2 variables forced empty. The clean full backend suite passed 456 tests; focused backend measurement/catalog coverage passed 70 tests and catalog concurrency passed 6 tests. Frontend passed 133 tests across 29 files, typecheck, and production build; lint exits 0 with existing React effect warnings. Repository validator passed with 456 tests discovered and its own 31 tests passed. Django check, production deploy check (13 existing drf-spectacular warnings), migration drift, OpenAPI validation (0 errors, 29 warnings / 13 unique), schema parity, Black, Flake8, and `git diff --check` passed.
- Safety note: an earlier broad test invocation inherited staging R2 credentials before they were explicitly disabled. One style-image upload returned success before a subsequent read failed, so one orphaned test object may exist at `shops/e0dcb9cd-8a29-4d25-a877-39209997a20c/style-options/fc66896e-acdb-491c-acb1-2274af1a91f9/references/5c440d58160843c7921b8c65cfc70ea1.webp`. No external cleanup was attempted because this task forbids external mutation.
- The work remains uncommitted and unpublished. No push, deployment, staging database write, or customer/demo measurement data creation was performed.

## Current handoff — CLIENT-WORKSPACE-HISTORY-01 (2026-10-06; local only)

- User explicitly selected the existing `main` branch for this task. Verified starting `main` was clean at `db67725e47b21ef8033f46fb7cecf5a4d600d1a2`, equal to `origin/main`. The sibling `sgtp-frontend` worktree was not changed.
- Client detail now presents a desktop-first responsive workspace: contact summary, primary Measurements action, Edit action, destructive Remove under an accessible More actions disclosure, measurement history, and an adjacent Related Persons panel. Client and Related Persons requests/errors/loading states are independent. Existing client and related-person forms/API behavior remains in place.
- Measurement profiles are fetched only when the authorized Shop Client detail view is available. Profile histories are fetched one backend page (20 records) at a time, only on expansion; exact set details are fetched only when opened. Profile garment labels are resolved lazily and cached per family/locale; variant browsing is requested only for variant-bearing profiles. Copy confirms then calls the existing immutable copy endpoint and refreshes page 1; compare and PDF export use the backend endpoints with exact selected set IDs. Version values are read-only here. No Related Person history, fake Design/Order links, backend change, migration, shell/navigation change, or new API was introduced.
- Changed areas: `frontend/src/features/clients/ClientDetailPage.tsx`, new `ClientMeasurementHistory.tsx` and workspace stylesheet/tests, `frontend/src/features/measurements/api.ts` plus contract test, localized English fallback keys, and the optional locale query support for `getFamilyDetail`.
- Validation: `npm run typecheck` PASS; full frontend suite PASS (124 tests / 29 files); production build PASS; `npm run lint` exits 0 with React effect warnings (including pre-existing warnings in other frontend files); focused Client/Measurement/API tests PASS (10). The initially observed single full-suite measurement test failure passed in isolation and on full-suite rerun. Authenticated browser/RTL visual verification was not performed because the active local browser was at `/login` and the user owns the login session.
- Screenshot follow-up: the Client detail route had omitted its base `clients.css` import, so build output split the base stylesheet into the ClientsPage asset and left detail styles missing. Added the explicit import on ClientDetailPage; collapsed profile cards now use the neutral “Measurement profile” label until lazy garment-name resolution completes, instead of incorrectly displaying “Unavailable garment”. Focused client tests (5), typecheck, and production build pass after this correction.
- Dropdown/history scrollbar polish: hid the root viewport scrollbar visually at the user's request while retaining native scrolling for long histories. Authenticated browser visual verification remains unavailable while the browser is at `/login`.
- Related Persons panel polish: brought the panel into the same card/header structure as Measurements, aligned the count and Add action, and unified loading, error, empty, and populated content within the panel. Existing API and form behavior is unchanged.
- In-page Measurements workflow: the Client detail Measurements action now lazily mounts the existing measurement-entry workflow in the same client workspace, preserving the client detail URL and keeping Related Persons alongside it. Client/shop/Related Person data is passed from the already-loaded parent to avoid repeat context requests; direct `/clients/:id/measurements` and `/measurements` routes remain intact. No measurement business logic or backend contract changed.
- Measurements visual structure: removed the legacy flat/unified treatment that stripped section borders and hid step badges. Each measurement workflow step and final review now renders as an individual bordered surface with the same radius, spacing, and subtle shadow as the Client workspace panels, including mobile widths. Workflow sequence and behavior are unchanged.
- Measurement context row: steps 01 Client and 02 Garment now share a single outer border. At viewport widths 900px and above they render in a two-column row with a central divider; below that they stack vertically with one outer border and a horizontal divider. Other steps retain their individual cards.
- Related Person creation remains available from the Client overview only; its Add button is hidden while the in-place Measurements workflow is open. Existing Related Person records remain visible and selectable as the wearer.
- Follow-up layout: Step 04 Measurement profile was moved into the preceding Step 03 Style card as an internally divided subsection. The Related Persons side panel is now omitted from Measurement view, letting the workflow use the full workspace width; Client overview remains unchanged. Backend/API untouched.
- Body Measurement unit follow-up: new fields initialize to `INCH`; the main unit switcher applies its selected unit to every field, and each field can then be changed independently. Unit changes never convert numeric values, and saved API values remain explicitly unit-tagged. Updated focused and full frontend tests cover the semantics.
- Fabric follow-up: the requested 2–3 demo items must use the real Shop-context inventory endpoint and persistence. The existing API/model/permission path is sufficient and its focused 16-test regression suite passes, but the local database currently has no Shop and therefore no valid Shop ID or authorized Shop context. No Fabric record, mock, direct ORM insert, or opening-stock movement was created. Resume only after the user identifies an authorized target Shop/environment.
- Validation after the unit follow-up: frontend suite 125 tests / 29 files PASS; typecheck and production build PASS; lint exits 0 with existing React effect warnings; focused inventory API tests 16/16 PASS on a disposable PostgreSQL database. Local `main` remains uncommitted and unpushed. No commit, push, merge, deployment, or business-data change occurred. Continue only after the user reviews the local implementation; do not publish as part of this handoff.

## Current handoff — STAGING-STYLE-IMAGE-MIGRATION-FIX-01 (2026-10-06; published and staging-verified)

- Baseline `main`, `staging`, `origin/main`, and `origin/staging` were all `47c67b5b9a5cccd87f531d6ff02a1850d385d9a3`. Exact-SHA Project State Validation run `37439777893` passed. The Render staging auto-deploy for that SHA failed during migration `catalog.0015_styleoptionimage_primary` with PostgreSQL `cannot CREATE INDEX ... because it has pending trigger events`. The previous staging revision remained live and both health endpoints were HTTP 200. No production deployment occurred.
- Corrective change: migration `0015` now adds `is_primary` and backfills existing image rows only; new `0016_styleoptionimage_one_primary` adds the conditional unique constraint after the backfill migration transaction completes. Added a PostgreSQL `TransactionTestCase` that migrates legacy images through 0015/0016 and asserts the lowest-sort-order image becomes the sole primary. Existing image records and objects are not removed.
- Implementation commit `5e17a4dc973efb2eee371dec8de01cefcdb56dc3` was pushed fast-forward to both `main` and `staging`; both remote refs and local refs matched at verification. Exact-SHA GitHub Project State Validation run `37445684348` passed all jobs, including the full 448-test application suite, validator, Django system check, and migration check.
- Render staging deploy `dep-db2c8jm7bikc73dr7800` completed `live`. Its logs show both `catalog.0015_styleoptionimage_primary... OK` and `catalog.0016_styleoptionimage_one_primary... OK`; Gunicorn started; `/api/health/live/` and `/api/health/ready/` returned `{"status":"alive"}` and `{"status":"ready"}`. No manual deploy was triggered. Production was not deployed or migrated.
- Local focused migration regression: 1 passed; full PostgreSQL suite: 448 passed (305 warnings); repository validator: PASS (448 discovered); validator tests: 31 passed; Django check and migration drift: PASS; OpenAPI validation exit 0; Black/Flake8 and `git diff --check`: PASS. Local PostgreSQL cluster was stopped after validation. The sibling frontend worktree was not modified.
- Canonical docs were updated after publication; any follow-up documentation commit must preserve these verified implementation/deploy facts. No further feature/task is authorized by this handoff.

## Historical handoff — STARTUP-PRIVATE-IMAGE-01 (2026-10-05; staging R2 configured, code unpublished)

- Baseline: local `main` is ahead of GitHub `main`; the sibling frontend worktree is on `frontend/parallel-foundation`. Derive current SHAs from Git. Preserve the pre-existing dirty performance-audit changes in both worktrees.
- New task edits: frontend `usePrivateImage` retries only transient network/5xx failures twice with a bound, aborts on unmount, rejects empty/non-image responses, and exposes manual retry; Shop Style Option previews display a visible error/retry when retrieval or image decoding fails. Frontend regression tests cover transient recovery, terminal 404, invalid HTML, and Catalog retry UI. Backend Catalog API test now checks uploaded image metadata/content URL after a fresh Shop list request. No application API, model, migration, auth, permission, or business rule changed.
- Verified image failure: at 2026-10-05 09:36:10 UTC the authorized reference-image GET raised `FileNotFoundError` for a private image under `/app/private-assets/catalog/references/`. A read-only R2 `HeadObject` for the logged key in `birkos-staging-private` returned 404. This GET is API-to-storage, so CORS does not explain its 500; CORS is required for browser-to-R2 presigned PUT. Never copy a guessed sample into the missing key or expose private URLs.
- Staging R2 configuration and R2-aware code are live; the deploy applied `catalog.0013_privatemediaupload` and `catalog.0014_private_reference_path_length`, collected static files, and started Gunicorn. Health live/ready both returned 200, and exact-SHA GitHub Project State Validation passed. The user's subsequent authenticated upload attempt exposed a separate missing transaction on `ShopPrivateMediaUploadView`: `_lock_shop_write_context()` uses `select_for_update()`. Local fix adds `transaction.atomic` and a real `TransactionTestCase`; it is awaiting publication/redeploy. R2 bucket CORS preflight for origin `http://localhost:5173`, method `PUT`, and header `content-type` returned 204. The verified original `C:\Users\Admin\Downloads\Untitled design (10).png` still needs upload through the authenticated app after this fix is live; do not create a substitute image.
- Startup: `authService.restore` must run CSRF bootstrap → cookie refresh → `/users/me/`; its remote RTT and possible Render Free cold start are not eliminated by this frontend patch. Do not claim zero startup lag or authenticated browser timing. A future backend response-shape/security change or deployment needs separate review/authorization. Direct R2 presigned GET could reduce Django byte-serving but requires Shop authorization, private-bucket CORS, short expiry, and bearer-link risk review; it was studied, not implemented.
- Validation for the R2 publication: backend suite 446 passed; frontend suite 117 passed with typecheck/build; staging health and migration logs were verified; exact-SHA CI passed. Transaction fix tests: 2 passed; final validator/diff and CI for the transaction-fix SHA remain pending. No authenticated image upload/display success is claimed. Next: publish the transaction fix, then upload the verified original through the authenticated UI and confirm it renders.

## Previous handoff — local performance/workflow audit (2026-10-05; local checkpoint)

- Frontend-only edits are uncommitted in the sibling `sgtp-frontend` worktree on `frontend/parallel-foundation`; local `main` has not been pushed or deployed. The frontend branch is not yet merged back into local `main` for this pass. Preserve both worktrees and do not infer remote CI or staging deployment from local tests.
- Verified request-count defects and fixes: Main Supplier Global Catalog previously loaded families, groups, all style options, and all families on every tab/search; it now loads active-tab data and ignores stale tab responses. Measurement variant changes now filter the already-loaded family design lists instead of refetching both lists. Shop context is shared across Shop route navigation instead of repeating Shop list + context calls on every page. Back Office Shop and Inventory searches are debounced; Inventory reuses its material list until explicit refresh or a write.
- Changed frontend files: `frontend/src/App.tsx`, `frontend/src/hooks/useCurrentShop.ts` and its new test, `frontend/src/backoffice/BackOfficePages.tsx` and new Shop-list test, `frontend/src/backoffice/catalog/GlobalCatalogPage.tsx` and its test, `frontend/src/features/measurements/ClientMeasurementsPage.tsx` and its test, `frontend/src/features/materials/MaterialsInventoryPage.tsx` and its new test, and `frontend/README.md`. Canonical docs changed in local `main`: `docs/PROJECT_STATE.md`, `docs/HANDOFF.md`, and `docs/CHANGELOG.md` only.
- Repeated unauthenticated warm health checks through local Vite proxy measured about 0.31–0.75 seconds, and direct Render calls about 0.33–0.60 seconds in the same sample. This does not measure authenticated workflow timing. The user could not provide an authenticated browser session during this audit; do not claim zero lag or end-to-end visual verification. The frontend still depends on staging API data and latency. Billing/pricing screens are not implemented in this local frontend baseline; do not present them as optimized or complete.
- Final local validation after the last code edit: frontend 105/105 tests passed, typecheck/build passed, lint exit 0 with existing React effect warnings; backend PostgreSQL-backed 445/445 tests passed, validator tests 37/37 passed, Django check passed, and `makemigrations --check --dry-run` found no model changes (base `testdb` is absent, so migration-history consistency was not checked). No backend source, migration, dependency, API, business rule, frontend merge, commit, push, or deployment change was made in this audit. Next action: when a user-owned login is available, measure authenticated Back Office/Shop routes before claiming experiential smoothness. This local request-count pass is not Phase 4 or Phase 7 completion.

## Current handoff — frontend integration and loading optimization (2026-10-05; in progress)

- The authorized frontend Measurement/R2 UI, Shop Style Option preview/editor, private image uploads, and loading optimizations are committed and pushed on `frontend/parallel-foundation` at `9ff32bc30d94744cfa0c432e4bb1c57d4182a20c`; that branch is clean. Its integration into local `main` completed with a conflict-free merge, but local `main` is not yet pushed. Frontend validation: 99 tests passed, typecheck/build passed, lint exits 0 with existing React effect warnings.
- The backend Measurement/R2 and Shop Style Option PATCH work is committed locally on `main`. Latest full UTF-8 PostgreSQL test run: 445 passed using `DJANGO_ENV=test` and local PostgreSQL host. Validator tests: 37 passed; repository validator PASS; Django check PASS; migration drift reports no model changes but cannot verify history against the absent configured base `testdb`. Changed Python Black and Flake8 PASS.
- Local Vite `/api` still proxies to Render staging to preserve the existing Shop/login data. Measured health/CSRF requests took approximately 0.4–0.7 seconds; route splitting, responsive login imagery, concurrent Catalog loading, and in-flight duplicate GET suppression reduce local work but do not remove remote network/service latency. Do not switch to the empty local Shop database without a data plan.
- `render.yaml` currently specifies `autoDeployTrigger: "commit"` for staging. The live Render service setting and staging R2 secret provisioning could not be independently confirmed from this workspace. `main` publication is paused pending a decision about the possible staging deploy and verification of R2 configuration; no `main` push, exact-SHA CI result, or staging/production migration is claimed. Local backend and merge commits exist. The next business task and Phase 5 remain unstarted.

## Previous handoff — CATALOG-STYLE-OPTION-EDIT-API-01 (2026-10-05; complete locally at that checkpoint)

- Added an additive translation-edit path to the existing Shop Style Option `PATCH` endpoint. A request updates only supplied locale rows; omitted translations and descriptions remain unchanged. Existing `is_active` update remains compatible; option code, group, and Shop owner are immutable.
- The endpoint uses the authorized URL-path Shop context and existing Shop ADMIN/STAFF/Main Supplier write policy. VIEWER is denied; foreign-Shop and global Style Options are not editable through this Shop route and return non-disclosing 404. No image removal/replacement API was added; uploads remain additive to protect Design references.
- Validation after implementation: Catalog API suite 32 passed; full UTF-8 PostgreSQL-backed suite 445 passed; repository validator PASS (445 discovered); validator tests 37 passed; Django system check PASS; no migration generated; OpenAPI 0 errors/29 warnings (13 unique); Black/Flake8 PASS; frontend baseline 95 tests, typecheck/build PASS, lint exits 0 with existing effect warnings; schema copies and `git diff --check` PASS. Migration-history inspection warns because configured base database `testdb` is absent; the disposable PostgreSQL test database was created and used successfully.
- No frontend changes, commit, push, CI run, deployment, shared/staging/production migration, or image/business-record deletion occurred. The `MEASUREMENT-R2-UI-01` sample JPEGs are standalone private R2 objects and are not associated with a Shop or Style Option.
- No next task is authorized. The separate frontend editor requires its own explicit task confirmation.

## Previous handoff — MEASUREMENT-R2-UI-01 (2026-10-04; local validation)

- Local Measurement/R2 implementation and validation were completed before the Style Option API task. Backend changes remain uncommitted on `main`; frontend changes remain isolated in `sgtp-frontend` on `frontend/parallel-foundation`. No commit, push, merge, or deployment has occurred.
- Local `.env` contains the required R2 configuration. Values were not printed. Endpoint format passed and read-only bucket `HeadBucket` returned HTTP 200. No shared/staging/production database was changed.
- Three distinct generated garment reference samples (dishdasha collar, shirt cuff, embroidered placket) are optimized JPEGs in the workspace `reference-samples/` folder (512×512; approximately 17–33 KB each) and have been uploaded to the existing private R2 prefix `birky-desgin-test/`. Each object was verified with `HeadObject` for exact size and `image/jpeg` content type. No Shop/StyleOption association or application business record was created; the images are standalone assets in the requested folder.
- Backend additions include a private-media upload ticket/migration and authorized Measurement Worksheet PDF endpoint. Frontend adds private-media API helpers, explicit unit controls, duplicate-save protection, and PDF download. A PDF Design association is request-time only; no billing model/data or persisted Measurement↔Design relation is added.
- Latest final validation: focused Catalog/Measurement API suite 54 passed; full PostgreSQL-backed suite 442 passed using project `DJANGO_ENV=test` settings, UTF-8 `template0` disposable test DB, and R2 disabled in the test process; repository validator PASS (442 discovered); validator tests 37 passed; Django system check PASS; production `check --deploy` has 0 errors and 13 drf-spectacular warnings; `makemigrations --check --dry-run` reports no changes; OpenAPI has 0 errors and 29 warnings (13 unique); changed/new backend Python passes Black and Flake8. Frontend suite 89 passed, typecheck/build pass; lint exits 0 with React effect warnings and the build reports the existing large-chunk advisory. Schema artifacts match. The initial full-suite attempt under `DJANGO_ENV=dev` exposed a Windows file-name-length/path-separator defect, a WIN1252 test database, and ManifestStaticFilesStorage test setup; the upload defect was fixed with normalized storage keys and migration `catalog.0014_private_reference_path_length`, and the correct test settings verified the complete suite green.
- R2 `HeadBucket`, object listing, upload, and post-upload `HeadObject` verification succeeded. The three requested sample objects are stored under `birky-desgin-test/` with private/no-store cache metadata. No staging/production database or deployment was accessed, and no Shop/StyleOption records were created. No commit or push has occurred.
- The sample images remain standalone R2 objects; no Shop/StyleOption target was identified and no business records were created. T4-04, Phase 5, and later business work remain unauthorized.

## Previous handoff — MEASUREMENT-E2E-01 (2026-10-03)

- Explicitly authorized by the pasted MEASUREMENT-E2E-01 task. Implemented the local Client → Family/Variant → grouped style options → persisted Shop Design → Client/Related Person Measurement Profile → localized definitions and explicit CM/INCH values → immutable version/history/copy/compare flow. Fabric selection uses the existing inventory read endpoint for display only; it creates no reservation or stock movement. No fake Work entity, Work ID, Cutting stage, measurement-owned inventory, or new role/function was added.
- The deterministic `catalog.0012_seed_mens_shirt_design_defaults` migration maps Men’s Shirt to Sleeve, Collar, Cuff, Pocket, Placket, Embroidery, and Color. It creates Classic Formal Shirt, Smart Casual Shirt, and Modern Evening Shirt as published global Standard Shirt templates. The reverse operation removes only seed template rows so historical migration tests remain valid.
- Remediation clears stale measurement drafts on owner/garment/profile changes, requires explicitly selected CM/INCH units, defaults comparison to the latest adjacent versions, blocks duplicate in-flight mutations, and shows every available private option image. Local/Pages API targets now come only from server-side environment variables.
- Main Supplier must choose an active Shop explicitly. Shop ADMIN can manage measurement records; STAFF access is granted only when selected-Shop context reports the active `MEASUREMENT` assignment; VIEWER and unassigned STAFF are denied. Added read-only `work_functions` to `GET /api/v1/shops/{shop_id}/context/`, scoped to the selected active membership and returned in canonical order; Main Supplier receives an empty list. No migration.
- Backend remediation is committed locally on `main`; frontend integration is committed on `frontend/parallel-foundation` and merged locally into `main`. Local `main` is ahead of `origin/main` pending publication. Do not reset, discard, stash, or overwrite this integrated work.
- Validation: full PostgreSQL-backed application suite with `DJANGO_ENV=test` and the disposable UTF-8 test DB: 433 passed. Focused Measurement API, concurrency, default-template, and Shop context tests: 40 passed. Frontend suite: 84 passed; typecheck/build pass. Lint exits 0 with React set-state-in-effect warnings, including async loading effects in the Measurements page. Django system check passes; production deploy check has 13 drf-spectacular warnings; OpenAPI generation/validation has 0 errors and 29 warnings (13 unique). `makemigrations --check --dry-run` reports no model changes but could not verify migration-history consistency because the configured base database `testdb` does not exist. Backend/frontend diff checks pass and schema artifact copies match.
- No manual authenticated local-browser session was performed because the local browser is at the user-owned login page. Local commits and the integration merge are complete; no push, deployment, shared/staging/production migration, or external API mutation occurred.

## Previous handoff — GARMENT-VARIANTS-01 (2026-10-03)

- Explicitly authorized with `CONFIRM TASK GARMENT-VARIANTS-01`. Backend Phase A and frontend Phase B are implemented and locally validated in their separate worktrees. The repository state validator passed with 430 backend tests discovered after the task docs were updated.
- Backend worktree: `main`; implementation commit `ca1285cd73814139350c076ce426c2273f4ca81a` was pushed and deployed to Render staging as `dep-db095b0u01pc739cl4n0`. Exact-SHA GitHub Project State Validation run `37099853077` passed. Render startup applied `catalog.0010_garmentfamily_image_garmentfamily_image_byte_size_and_more` and `catalog.0011_garmentvariant_is_active`; health live/ready endpoints returned 200. Protected Family and Shop Variant detail endpoints returned 401 without authentication, confirming the routes resolve. Production was not deployed or migrated.
- Frontend worktree: `frontend/parallel-foundation`, baseline `fa9e84b55fe8d5f9b62aee12459138edf790233d`, with the GARMENT-FAMILIES-01 local changes preserved plus this task's local Variants integration. Do not reset, discard, overwrite, or stash those changes.
- Implemented backend contract: active/archive lifecycle; paginated search/family/status/source Shop listing; Main Supplier global create/detail/edit/archive/reactivate/default; Shop detail/edit/archive/reactivate; exact Variant filters for Shop Designs and Global Design Templates; archived-Variant rejection for new Design and Measurement records; family-row serialization for lifecycle/default races. Variant thumbnail is deferred because Family image storage/service wiring is not yet a reusable abstraction. No cost/stock/supplier/warehouse/BOM semantics were added.
- The user authorized publishing the backend changes to the existing Render staging API. The backend `main` changes were pushed after validation, then manually deployed because the `birky-staging-api` service has auto-deploy disabled. The deployed migrations and health checks succeeded. Production remains out of scope. Manual authenticated browser checks remain pending because the user owns login in the open localhost tab.
- Frontend implementation: paginated Shop Variant browsing with debounced server search, Family/source/status filters, count and pagination; compact cards and accessible responsive details; Shop Variant create/edit/archive/reactivate; Main Supplier global create/edit/archive/reactivate/set-default; Family → filtered Variants continuation; and exact Variant filtering in Designs. The existing Shop context endpoint supplies the current membership role, so read-only users do not see Shop mutation or archived-list controls. No frontend-side mock fallback or invented Variant identity fields were added. Thumbnail remains deferred because the Family private-image implementation is not a reusable single-image abstraction.

## Tests and checks

- Backend: full PostgreSQL-backed app suite 430 passed; focused Catalog/Measurement/Variant API and concurrency suite 56 passed; repository validator unit tests 30 passed; repository state validator PASS (430 tests discovered); Django/system and production deploy checks PASS (12 existing OpenAPI warnings); migration drift clean; OpenAPI 0 errors/28 warnings (12 unique); Black, Flake8 and `git diff --check` PASS. Migration `catalog.0011_garmentvariant_is_active` ran only on disposable UTF-8 PostgreSQL test databases.
- Frontend: `npm run typecheck` PASS; all frontend test cases across 13 files PASS; `npm run build` PASS; lint exits 0 with six existing warnings in unchanged shared files; frontend `git diff --check` PASS. Production build reports the existing >500 kB bundle-size advisory. Authenticated manual responsive/RTL/theme checks are pending user login.
- Both worktrees remain local and uncommitted; no commit, push, merge, deployment, or shared/staging/production migration occurred.

## Previous handoff — GARMENT-FAMILIES-01 (2026-10-03)

- Explicitly authorized with `CONFIRM TASK GARMENT-FAMILIES-01`. Backend Phase A and frontend Phase B are implemented and locally validated in their separate worktrees: backend `main` at baseline `f440db032073d183c639a47c9b83597a7efd2a9b`, frontend `frontend/parallel-foundation` at baseline `fa9e84b55fe8d5f9b62aee12459138edf790233d`. Both worktrees contain uncommitted task changes. No commit, push, merge, or deployment was performed.
- Backend adds ACTIVE/ARCHIVED global Family lifecycle, immutable Family code with Main Supplier translation editing, Family detail, global server-side search before pagination, one optional private optimized thumbnail, and Main Supplier-only archive/reactivate/image writes. Ordinary Shop users browse active Families only. Existing ordered Family → Option Group GET/PUT remains intact.
- Archived Families are excluded from normal Shop browse and cannot be selected for new Shop Variants, Shop Designs, Global Design Templates, Measurement Profiles, or Measurement Definition mappings. Existing Variants/Designs and measurement history remain intact and readable. Measurement creation locks the Family row to serialize against archive.
- Migration `catalog.0010_garmentfamily_image_garmentfamily_image_byte_size_and_more` adds only lifecycle/image metadata and was validated on disposable UTF-8 test databases. Local development, staging, and production databases were not migrated.
- Backend tests: full PostgreSQL-backed application suite: 419 tests passed; Catalog API suite 27 passed; Catalog/Measurement API and concurrency regressions 23 passed; validator tests 35 passed. Django check PASS; production deploy check exit 0 with 12 existing OpenAPI warnings; migration drift clean; OpenAPI 0 errors/28 warnings (12 unique); Black, Flake8, schema artifact parity, repository state validator (PASS; 419 discovered), and `git diff --check` PASS.
- API and database documentation, generated schema artifacts, Project State, and Changelog describe the Family contract. Backend checks remain green. Frontend uses real authenticated APIs and covers Shop browse/search/pagination/detail, family-filtered Variants/Design navigation, and Main Supplier management for create/edit/archive/reactivate/images/group ordering. Frontend typecheck, 59 tests, production build, and diff check pass; lint exits 0 with six existing warnings in unchanged shared files. Manual authenticated visual checks at each requested viewport were not done because the local browser tab is at `/login` and the user handles login. No staging/production database migration, deployment, commit, push, or merge occurred.

## Current handoff — T4-02-API-ENDPOINTS-01 (2026-10-03)

- Explicitly authorized with `CONFIRM TASK T4-02-API-ENDPOINTS-01`. Additive Catalog/Design API work is implemented and validated on local `main`. The API work and preceding Catalog/Design frontend integration were published to GitHub `main` at commit `3d17271dae879f5f26ceba5b46c413bf2d501310`; remote SHA was verified. No deployment occurred.
- Implemented routes: Main Supplier-only `POST /api/v1/catalog/families/` and `POST /api/v1/catalog/option-groups/` (atomic creation with required unique English translations); Main Supplier-only paginated `GET /api/v1/catalog/variants/` (global variants only, optional validated `family` UUID); and `GET /api/v1/catalog/design-templates/{design_id}/` (Main Supplier can see drafts; Shop users see published versions only; hidden/archived templates return 404). No model change or migration.
- Focused endpoint coverage passed (5 tests); Catalog API regression suite: 22 passed with one pre-existing test excluded because the local PostgreSQL cluster uses `WIN1252`; that test inserts Arabic text and fails on database encoding. The first run also showed the new non-English fixtures hit the same environment limit; fixtures were made English-only, after which all new endpoint tests passed. Do not alter database encoding or rewrite unrelated regression tests as part of this task.
- Django system check passed; `check --deploy` had no errors and 18 warnings (12 OpenAPI warnings plus local security-setting warnings); migration drift check found no changes. OpenAPI regenerated with 0 errors and 28 warnings (12 unique); `schema.yml` and `docs/schema.yml` match. Flake8, Black, `git diff --check`, Project State validator, and all 28 validator tests passed. Validator warns that it cannot discover the project test count in this environment.
- No staging/production request was made. Existing frontend lacks create forms for Family/Option Group and a Global Template create form; this backend task does not implement those UI forms.

## Current handoff — Catalog and Designs frontend integration (2026-10-03)

- User authorized integrating the existing Catalog and Designs frontend modules against the current backend contract, fixing small UI issues, and bringing the result to `main` only if safe. The implementation commit `feat(frontend): integrate catalog and designs APIs` is on `frontend/parallel-foundation` and has been merged locally into `main` using a normal merge. Validation passed. A push was attempted but could not authenticate: `gh auth status` reports no GitHub session and Git Credential Manager could not obtain credentials. Remote `main` remains at the pre-merge revision; rerun a normal `git push origin main` after GitHub authentication is available. No force-push is needed.
- The pages now consume live API shapes and pagination, show request errors instead of mock fallback data, and implement supported Shop/global catalog and design actions, including Shop design creation, supported draft selections, publish/archive, and reference-image uploads. API contract tests were added. No backend files or deployment settings were changed.
- Local frontend validation on that commit: typecheck PASS; 47 tests PASS; production build PASS; lint exits successfully with six pre-existing warnings in `useCurrentShop.ts`, `usePrivateImage.ts` (two), `ClientForm.tsx`, `UsersPage.tsx`, and `App.tsx`; no new warnings from changed files. `git diff --check` passed. Repository state validator passed, with its documented test-discovery warning. Its scope check was updated to recognize the previously approved and completed T4-03A Catalog backend when a later frontend task is current; all 28 validator tests pass.
- Known API-driven limits: there is no backend create endpoint for Families or Option Groups, so those create actions are not offered. Global design-template creation cannot be safely completed from the current API because there is no global variant-list endpoint; no fake endpoint or mock fallback was introduced. The backend has no Global Design Template detail route, so the frontend resolves a selected template from the paginated list. These gaps are documented in the frontend README.
- No authenticated staging browser E2E was performed, and no deployment occurred. The feature branch push is known to trigger the Cloudflare client-preview; the `main` production Pages branch setting is not independently verified. Before publishing, derive current refs/worktree state again and report separately whether any hosting provider deployed the pushed commit. Never force-push.
- Broader frontend work and T4-04 remain outside this integration task.

## Current handoff — T4-03A Inventory & Stock Foundation (2026-10-02)

- T4-03A is explicitly authorized (`CONFIRM TASK T4-03A`), implemented in commit `1e6e79a60a7337a43e6bb73c47aacf0c947c6570`, pushed to `main`, and exact-SHA CI-verified by Project State Validation run `37045373602` (SUCCESS). It adds inventory to the existing `apps/catalog` Material identity; T4-03 remains historically complete with its original reference-only scope. T4-04 has not started and is not authorized.
- Local `main`, `origin/main`, and GitHub `main` matched after publication; working tree was clean. No frontend, Work aggregate, billing/costing, Phase 5, staging/production migration, or deployment was included. Current branch/HEAD/worktree must be derived from Git.
- Implemented so far: controlled categories/units; explicit enablement for legacy Materials without inferred values/opening stock; zero-initialized Shop-scoped balance; atomic opening/stock-in/adjustment ledger services; immutable movement history; active inventory selector and management APIs; archive blocked while on-hand/reserved quantities remain; archived history stays readable to authorized managers. Work-linked reserve/release/consume/return remains future integration with the real Work model.
- Final validation: focused inventory + T4-03 measurement regressions 41 passed; full PostgreSQL-backed suite 409 passed; repository validator PASS (409 discovered); validator tests 32 passed; Django check PASS; production deploy check has 0 errors (12 warnings); migration drift PASS; OpenAPI 0 errors/28 warnings (12 unique); Black, Flake8, schema parity, and `git diff --check` PASS. Exact-SHA GitHub Actions run `37045373602` succeeded for `1e6e79a60a7337a43e6bb73c47aacf0c947c6570`.
- PostgreSQL 15 was started locally from the existing initialized `pgdata` cluster after read-only verification; no reinitialization occurred. Testing uses disposable `test_devdb`; no staging or production database was accessed.
- Preserve UUID Material identities and Measurement history. Existing Materials migrate with blank inventory classification and no fabricated stock. Inventory classification must be explicitly enabled before selector visibility. Every mutation uses Shop→Material→Balance lock order.
- Next task: none authorized. Do not start T4-04, Phase 5, frontend, or deployment.

## Historical handoff — T4-03 Measurements + Materials (2026-10-02)

- Latest separately authorized maintenance task `DJANGO-ADMIN-UX-01` is implemented, published to `main`, and exact-SHA CI-verified. The task only changes native Django Admin registration, permissions, templates, local Admin CSS, docs, and focused tests. It does not change models, migrations, APIs, business rules, dependencies, frontend source, or deployment state.
- Django Admin UX tests: 18 passed; full PostgreSQL-backed application suite: 388 passed; validator test suite: 30 passed; Django system check PASS; production `check --deploy` exits 0 with 12 existing nonfatal OpenAPI warnings; migration drift: no changes; OpenAPI: zero errors and existing warnings; Black/Flake8/`git diff --check` PASS. Implementation SHA `608362d6509b286ba0daa9ede4e33d39d2888a6c` passed GitHub Actions Project State Validation run `37017703294`. No deployment occurred.

- Phase 4 remains ACTIVE. T4-01, T4-02, and T4-03 are complete and published. T4-03 was confirmed with `CONFIRM TASK T4-03`; T4-04, Phase 5, frontend, and deployment remain separately gated.
- T4-03 implementation was added to the existing `apps/catalog` runtime app: Shop-context measurement/material models, services, APIs, migrations, PostgreSQL tests, and synchronized docs/schema. No Work/Order, inventory, billing, frontend, Phase 5, or deployment work was included.
- Validation: focused T4-03 API/concurrency tests 20 passed; full PostgreSQL-backed application suite 370 passed; repository validator PASS (370 tests discovered); validator tests 30 passed. Django system check PASS; production `check --deploy` had no errors (12 nonfatal drf-spectacular warnings); migration drift clean; OpenAPI zero errors and 28 warnings (12 unique); Black/Flake8 and `git diff --check` PASS. Implementation commit `d9ca27bbab8587c2da5ceb8c1f61f913087fdc48` passed exact-SHA Project State Validation run `37006408609`.
- Local development migration `catalog.0006_measurement_material_foundation` and deterministic seed migration `catalog.0007_seed_measurement_definitions` have been applied to the local development/test database only. No staging or production migration/deployment was performed.
- Expected implementation policy: only Men's Shirt and Kuwaiti Dishdasha are seeded; sets/values/label snapshots are immutable; units must be explicit INCH/CM and are never converted; material is only an archive-first Shop reference record. See the T4-03 section in the Phase 4 playbook and API/database docs.
- Next task: none authorized. T4-04 requires a separate explicit task confirmation. Do not begin T4-04, Phase 5, frontend work, or deployment.

## Historical handoff — STAGING-MAIN-ADMIN-BOOTSTRAP-01 (2026-10-01)

- Task `STAGING-MAIN-ADMIN-BOOTSTRAP-01` is complete on `main` at `9b8fbc94741d85e018be10fdee41b34bd283af52`; exact-SHA Project State Validation run `36887320909` passed. The staging account was created in deploy `dep-dav83hhsrm7s73e9llsg`; cleanup deploy `dep-dav84r3bc2fs738dghi0` is live with the bootstrap switch disabled and all four temporary input values blank. The requested Main Supplier Admin has a forced password change on first login. No Shop, migration, or Production deploy was made.
- Local verification: focused bootstrap tests 9 passed; `manage.py check`, no-migration-drift check, repository validator (PASS), its 21 tests, Black, Flake8, shell syntax, and `git diff --check` passed. The broader local suite did not complete because the local PostgreSQL process exited; exact-SHA CI passed.
- User identity: Shibili, `mshibilin06@gmail.com`, phone normalized to `+916282911854`. The one-time password is held only for delivery in the final response; it is not in the repository or Render environment after cleanup. Ask the user to change it immediately after first login.
- User identity requested: Shibili, `mshibilin06@gmail.com`, phone `6282911854` normalized to E.164 as `+916282911854`. Any generated temporary password must remain out of repository, logs, commands, and tool text output; communicate it only once after successful creation so the user can change it immediately.

## Previous handoff — BACKOFFICE-01 (2026-10-01)

- Task `BACKOFFICE-01` backend commit `a0bd06ec272440f687fef68a157568466821a664` is committed and pushed to `main`; Render staging deploy `dep-dav6emo473hc73dqm7t0` is live. Frontend feature commit `def2c60d` is committed locally on `frontend/parallel-foundation` and `main` has been merged into that branch; it is not pushed yet.
- Main Supplier-only frontend pages provide Back Office dashboard, Shop list/search/filter/order/pagination, create, detail/edit, and activate/deactivate. The pages reuse the established shell/theme and use the real `/api/v1/tenants/` contract. Work page mock data remains untouched.
- Backend exposes a derived `is_main_supplier_admin` boolean in login/profile responses. A focused backend integration test verifies the created first Shop ADMIN can log in using the returned permanent User ID and initial password, is correctly forced through password change, and succeeds at changing that password.
- Validation: complete backend PostgreSQL suite passed 257 tests, then the added first-admin login/password-change test passed separately; frontend 31 tests, typecheck, and build passed; lint reported one existing warning in `src/App.tsx`; Django check, migration drift, schema validation, Project State validator, and `git diff --check` passed. Render readiness and CSRF bootstrap endpoints returned 200 after the deployment.
- The existing `birky-staging-api` is on `main` with `autoDeploy=off`; staging now runs the backend implementation commit. Do not deploy Production.
- The frontend branch is configured as the Cloudflare Pages client-preview source; a push automatically triggers a preview deployment. Current approval covers Render staging, not automatic Cloudflare preview publication. Prepare the frontend branch locally and request approval for that preview push after changes are reviewable.
- Next: obtain the user's approval to push `frontend/parallel-foundation`, because that push triggers the Cloudflare Pages client-preview deployment. After approval, push and verify the preview; do not deploy Production.

## Current phase

Phase 3 is COMPLETE; it was activated with `CONFIRM PHASE 3`, and T3-05A is complete with custom-domain DNS/TLS explicitly deferred. Phase 4 is ACTIVE; Core Tailor Business activation was explicitly confirmed with `CONFIRM PHASE 4`.

Completed foundation tasks include T3-01–T3-04B-USER-SCOPE, T3-04C, and T3-05. T3-05 is published and its exact-SHA Project State Validation succeeded for the implementation commit. Derive current `HEAD`/`main` from Git.

## Historical task state before T4-03

Previous completed task: Clients and Related Persons is published.
Historical T4-02 — Catalog and Designs — was explicitly confirmed with `CONFIRM TASK T4-02`. Its implementation and validation were completed and published at `1287d61a1406bbdd3edddc778b91f59c9cca52df`; exact-SHA Project State Validation run `36970391503` succeeded. T4-03 was subsequently authorized as the current task.
The separate API-DOC-REFRESH-01 maintenance task is committed and published at checkpoint `9e93a77754ac03839d038e5e3a32458208bc02e9`; exact-SHA Project State Validation run `36850074419` succeeded. This maintenance task does not activate T4-02 or frontend work.
API-BROWSABLE-PORTAL-01 is a published historical maintenance task; it did not authorize or implement T4-02.
T3-05A — Staging Backend Foundation — remains complete, committed, pushed, exact-SHA CI-green, and live-verified. Staging remains on the verified provider hostname; custom-domain DNS/TLS and frontend browser integration are deferred. Derive current `HEAD` from Git. The T4-01 implementation SHA and exact-CI run are recorded in `docs/PROJECT_STATE.md` and `docs/CHANGELOG.md`.

`FRONTEND-DELIVERY-LOCK-01` established Contract-First Paired Delivery and the UI Reference Gate. The later-approved `PHASE4-PARALLEL-UNBLOCK-01` clarification allows backend Phase 4/5/6 and frontend integration to progress in parallel: frontend completion is not a backend prerequisite, while each frontend business slice still follows acceptance of its backend contract. The frontend foundation branch remains isolated and must not be modified from this worktree. Phase 4 is active; T4-01/T4-02/T4-03 are published, and T4-03A is the current separately authorized inventory task. T4-04, Phase 5, and frontend tasks remain separately gated.

Derive current `HEAD`/`main` from Git rather than storing a current SHA in this handoff. Do not begin T4-04, Phase 5, or frontend work without separate authorization. Do not modify/merge frontend work. No deployment is allowed for T4-03.

## Current state and next gate

- Parallel development rule: `main` remains the backend/current integration source and canonical documentation owner. Frontend foundation work uses `frontend/parallel-foundation` in sibling worktree `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp-frontend`, with application source only under `/frontend`. Do not edit frontend source in the main worktree or repeatedly edit canonical docs from the frontend branch.
- The Parallel Frontend Foundation Track (`frontend/parallel-foundation`) is active. The existing Work page serves as the authenticated visual/layout reference but its data remains mocked until the T4-04 API exists. No final UI may be implemented without an approved visual reference (UI REFERENCE GATE).
- Ordinary accounts are Shop-owned and must not receive a post-login multi-Shop selector. Main Supplier cross-Shop UX must rely on an authorized backend contract.

- T3-04A's published generated `user_code`, optional normal-user email/phone, required trimmed `first_name`, alias login, controlled credential reset, contact safeguards, and User hard-delete denial remain in place; UUID remains the database/JWT `user_id` identity.
- T3-04B remediation routes membership changes through transactional services; enforces immutable membership User/Shop identity, atomic Shop + first ADMIN creation, ADMIN 1–2 cardinality, global User-deactivation authority/invariants, lifecycle rules, safe Django Admin paths, and approved capacity semantics. No migration was added.
- Approved ordinary-Shop visibility, Shop deactivation/no-delete, and max_users lower-bound rules are implemented and published under T3-05; its exact-SHA CI gate succeeded.
- T3-05A repository changes include explicit staging settings, a manually deployed Render Blueprint, isolated Free PostgreSQL, bounded DB startup wait, provider PORT/Gunicorn tuning, host-only CSRF bootstrap, guarded synthetic-data reset, smoke script, and runbook. Actual Render resources and deployment are now verified; see current evidence below. Application auto-deploy is off.
- Local verification on the guarded-bootstrap commit: full PostgreSQL-backed application suite 270 passed; repository validator PASS (270 discovered), validator tests 23 passed. The previously recorded staging Django/deploy checks, migration drift, OpenAPI, Black/Flake8, Docker smoke, and exact-SHA CI evidence remain as stated for their respective checkpoints; exact-SHA run `36661313651` passed for commit `b53c897cff193eebeebf664b01fb8a55b335a718`.
- Historical checkpoint: after initial fixture creation, only context-level A↔B isolation and core authenticated flows had been checked. The subsequent final verification completed the Shop endpoint matrix and logout/revocation checks; see the current status and staging runbook. No customer data was used. Never use Production credentials/data.
- Free plan is temporary/non-durable: Web Service sleeps on idle and has an ephemeral filesystem; Free PostgreSQL is limited to 1 GB, expires after 30 days, and has no backups. Excess bandwidth/build usage may be billed. Do not upgrade/add paid resources without explicit billing approval. See `docs/runbooks/STAGING_BACKEND.md`.
- The approved T3-04B User-Scope decision supersedes the older one-global-User/multiple-Shops target: each ordinary account has one immutable owning Shop; same-real-world people in different Shops use independent accounts. Main Supplier accounts remain global.
- Published implementation adds `User.owning_shop`, migration `accounts.0005_user_shop_ownership` with historical-membership preflight and database guards, atomic Shop-owned account creation, `/api/v1/shops/{shop_id}/users/`, same-Shop account reset authorization, and regression fixtures/tests.
- Pre-publication local preflight found zero Users and memberships in the development DB. GitHub CI migration/application validation passed on its disposable PostgreSQL database. Neither establishes shared/staging/production data status; the migration aborts on ordinary Users with multiple or no determinable Shop. Shared/staging/production ownership preflight was NOT PERFORMED; no shared/staging/production migration was applied.
- Pre-publication local validation: focused account/membership/auth regressions 138 passed; PostgreSQL-backed full suite 192 passed, including four concurrency cases; validator tests 14 passed; Django and migration checks passed; OpenAPI passed with two nonfatal role-enum naming warnings; Black/Flake8 passed on new Python files. GitHub Actions Project State Validation passed for the published exact SHA. Broad lint checks on touched legacy files still report existing style findings; they were not mass-formatted.
- Historical Phase 3 checkpoint: T3-04C, T3-05, and T3-05A are complete and published with exact-SHA CI green. At that checkpoint T4-01 was complete and T4-02 had not started; current T4-02 status is recorded above.
- T3-05 local validation: focused Shop/API/Admin/regression/concurrency tests 30 passed; complete PostgreSQL-backed application suite 231 passed (186 warnings); repository validator PASS (231 discovered); validator tests 14 passed; Django system/deploy checks and migration drift check passed; OpenAPI validation reported zero errors with nonfatal warnings; Black, Flake8, and `git diff --check` passed. The exact commit's GitHub Actions run `36614638187` passed all steps, including the PostgreSQL-backed application suite and migration check.

## Tests and checks

- **T4-01 final validation:** focused Clients/Related Persons API and PostgreSQL concurrency tests: 15 passed; full PostgreSQL 15-backed application suite: 309 passed; repository validator PASS (309 discovered); validator tests: 27 passed. Django system check and production `check --deploy`: PASS; migration drift: no changes; OpenAPI: zero errors, 23 warnings (7 unique, existing serializer type-hint/role-enum warnings); Black, Flake8, and `git diff --check`: PASS. Exact-SHA Project State Validation run `36796609814` succeeded for `e4e5e4126d60bfb563fbd25fbf0baab9e85963f9`; no deployment occurred.
- Final T3-05A application suite: 294 passed; repository validator PASS (294 discovered); validator tests 23 passed. Focused credential rotation/bootstrap tests: 39 passed; staging tests: 28 passed; auth/CSRF lifecycle regressions: 7 passed.
- Staging Django checks, deploy check, migration drift, OpenAPI (zero errors), Black/Flake8 for new staging Python, Git Bash shell syntax, and `git diff --check` passed. GitHub Actions run `36667104952` succeeded for exact implementation SHA `b29a897897d35ec9163c510456bd9197b8a4f6e1`. Render final cleanup deploy `dep-dau9ptlg1s2s73c2foig` is live on that SHA; migrations/static collection/Gunicorn and health checks succeeded. No secret exposure was found. Full live token and Shop isolation matrix passed. Free-plan limitations and remaining DNS/TLS/browser deferrals are documented in the staging runbook.

## T3-04C execution (historical)

- Scope: membership-scoped seven-code Work Function catalog and Shop ADMIN-only same-Shop GET/PUT management. Functions remain eligibility descriptions, not roles or permissions. No Phase 4 mapping, T3-05, frontend, or deployment work is included.
- Implementation: additive `tenants.0009_membership_work_functions`, normalized relation with current-assignment uniqueness/catalog check, transactional set replacement and soft-deleted history, Shop-first authorization/locking, audit actor attribution, API/OpenAPI contract, and regression tests. Existing membership lifecycle keeps assignments through inactive/reactivated states and valid removal undo; expired undo does not restore membership/function assignments.
- Tests: focused Work Function model/API/lifecycle/migration/concurrency tests: 19 passed. Full PostgreSQL-backed suite: 211 passed, 172 warnings. The suite includes the PostgreSQL concurrency tests.
- Checks: repository validator PASS (211 discovered; one earlier invocation could not reach the remote, then a final invocation verified `origin/main` parity); validator tests 14 passed; Django check PASS; `DJANGO_ENV=prod check --deploy` exit 0 with two nonfatal OpenAPI role-enum warnings; migration drift PASS; OpenAPI validation PASS with the same two warnings; Black/Flake8 PASS; `git diff --check` PASS.
- Publication and exact-SHA CI were verified for T3-04C. At that checkpoint T3-05 had not started; current T3-05 status is recorded at the top of this handoff.

## T3-04B remediation — task-time local validation record

- Focused remediation suite: 77 passed; T3-04A identity/authentication, T3-03 context, membership, and migration regressions: 39 passed.
- Full PostgreSQL-backed pytest suite: 183 passed (113 warnings). Separate-connection PostgreSQL races for dual promotion, demotion/global deactivation, and first-ADMIN creation/global User deactivation all passed.
- Repository validator: PASS (183 discovered); validator tests: 14 passed. Django system/deployment checks, OpenAPI schema validation, Black, Flake8, and `git diff --check`: PASS.
- `makemigrations --check --dry-run`: no model changes detected. The statements above describe validation at that task-time checkpoint; publication/current status is recorded at the top of this handoff.

## T3-04B-USER-SCOPE execution (historical)

- Task is explicitly confirmed, implemented, validated, committed, and published; T3-04C is not started and must not be begun without its own task plan and confirmation.
- Confirmed design: one immutable owning Shop per ordinary account; different Shops use distinct accounts even for the same real-world person. Main Supplier accounts remain global with no owning Shop. Existing account attachment/movement is rejected.
- Published source adds the ownership field/migration and database guards, Shop-scoped account creation/reset, atomic Shop + first ADMIN account creation, same-Shop membership enforcement, and regression tests. The old one-global-User/multi-Shop rule remains marked superseded/history.
- Local preflight before applying the migration found an empty development DB (zero Users/memberships); this does not establish shared/production data status. Migration preflight tests now cover multi-Shop and unowned history refusal.
- Exact-SHA GitHub Actions run `36591864481` completed SUCCESS for commit `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c`.
- Next planned task: T3-04C Work Functions. It is NOT STARTED and requires its own plan and explicit confirmation. Do not begin automatically.

## Historical T3-04A tests and checks

- Focused identity/authentication suite: 29 passed; T3-02A compatibility regressions: 10 passed. Full pytest suite: 167 passed (155 warnings) against the local PostgreSQL test database. One earlier run was interrupted by the stopped local PostgreSQL process; the existing service was restarted without resetting its data, and a clean complete rerun passed.
- Repository validator: PASS (167 tests discovered); validator tests: 14 passed. `manage.py check` and `DJANGO_ENV=prod manage.py check --deploy`: PASS; `makemigrations --check --dry-run`: no changes detected; OpenAPI validation: PASS; `git diff --check`: PASS.
- Read-only local PostgreSQL preflight found 0 Users, 0 superusers, and 0 Shops, with no unusable names, blank emails, or case-insensitive duplicate email groups. Then the normal local migration command applied T3-04A and its tenant prerequisites successfully. The migration regression test separately verifies preservation of representative legacy identity, password, membership, and audit references.
- Black and Flake8 pass for all six newly added Python modules. A broader Flake8 run over touched legacy files still reports style/unused-import findings, so whole touched-file lint is not clean. GitHub CI has not run for this local diff.
- T3-04A changes remain uncommitted and unpushed. No commit or push has been made.

## T3-REBASELINE-01 validation

- Repository validator: PASS (152 tests discovered; expected dirty-tree warning). Validator unit tests: 14 passed.
- `manage.py check`: PASS. `makemigrations --check --dry-run`: no changes detected; PostgreSQL at `127.0.0.1:5432` was unavailable, so migration-history consistency was not verified locally.
- Full pytest: 152 collected but not completed; database-backed setup errored because PostgreSQL was unavailable. Do not report a local full-suite pass. The published checkpoint's GitHub Actions validation succeeded; local PostgreSQL-backed full-suite execution remains unverified here.
- `git diff --check`: PASS. 52 Business Rule IDs checked, no duplicates; Phase 3 task sequence consistent across the development plan and playbook.
- Application code/migrations/dependencies/tests: unchanged. Documentation checkpoint committed and pushed; no deployment occurred.

## T3-04 verification record (historical task evidence)

- **Implemented:** `TenantScopedMixin` requires T3-03 authorized request context, checks actor/URL/compatibility alias, scopes reads, and assigns selected-Shop ownership on create/update. `IsTenantMember` now requires object-to-context Shop equality for members and Main Supplier.
- **Security:** missing context/configuration fails closed; URL, alias, and actor mismatches are non-disclosing 404s. Foreign direct IDs are excluded by scoped lookup. T3-03 uniform Shop-context 404 and authentication 401 behavior are preserved.
- **Database/API scope:** no production business models, API routes, migrations, or dependencies added. Test-only UUID/FK/soft-delete proof model validates the reusable boundary. At T3-04 completion, Tenant/member APIs were unchanged; later-approved visibility/deactivation rules are now recorded as target behavior for T3-04B/T3-05.
- **Validation:** 28 focused scope/context tests passed; full suite 152 passed (144 warnings); repository validator PASS (152 discovered); 14 validator tests passed; Django check PASS; migration check reports no changes; OpenAPI validation, Black, Flake8, and `git diff --check` PASS. T3-04 was subsequently pushed and its current CI evidence is stated above.
- **Next task at that historical point:** T3-05 was the proposed next task; the 2026-09-29 rebaseline supersedes that order with T3-04A–C prerequisites.
- **Known warning baseline:** Django tests emit existing test-key-length, local staticfiles, and DRF format-converter warnings; these are not T3-03 failures.

## T3-04 verification record (historical)

- T3-03 context/membership tests remain covered by the validation matrix. Focused T3-04 permission/scope plus T3-03 context tests: 28 passed.
- Full suite: 152 passed (144 warnings). Repository validator: PASS, 152 discovered, dirty-tree warning expected. Validator tests: 14 passed. Django system check: PASS. Migration drift: no changes. OpenAPI validation: PASS. Black and Flake8: PASS. `git diff --check`: PASS.
- No production schema/dependency changes or business modules. T3-05 remains not started and unauthorized.

### Historical: T3-02A verification record

- **Implemented:** optional unique E.164 User phone and compatible email/phone login; anonymous account creation denied; Main Supplier Admin account/phone administration; one-time random initial password with no-store response and forced first-login change; email password reset with generic response, expiry/single use, and refresh-session revocation; nullable user locale, `system|light|dark` appearance; nullable Shop locale/timezone/currency with Main Supplier Admin-only serialization; versioned JWT access/refresh revocation.
- **Database:** additive migrations `accounts.0003_alter_user_options_user_appearance_preference_and_more` and `tenants.0008_tenant_default_currency_tenant_default_locale_and_more`; UUID identity/memberships preserved; no fabricated phones or inferred Shop defaults.
- **Tests added/updated:** T3-02A account/auth/Shop settings regressions; existing account-creation tests aligned to the confirmed deny-anonymous/admin-create contract; auth lifecycle test cache is cleared between tests without changing runtime throttling; historical tenant migration test now uses historical models and restores the latest schema.
- **Files/areas:** accounts models/auth/serializers/views/URLs/settings/dependency and tests; tenant settings model/serializers/permissions/view/migration/tests; docs/API, ARCHITECTURE, DATABASE, SECURITY, Phase 3 plan, DEVELOPMENT_PLAN, PROJECT_STATE, HANDOFF, CHANGELOG, `.env.example`.
- **Validation:** final test/check results are recorded in the T3-02A verification section below.
- **Known limitations:** no front-end localization/theme UI, no Shop URL context or tenant isolation, no later-phase business modules. Shop defaults must not be read by ordinary users. Credential recovery follows the phone request → Back Office approval model; email self-service reset is not exposed.
- **Unresolved decisions at T3-02A completion (historical):** ordinary-user Shop read visibility and Shop deletion semantics were later resolved as target policy by the 2026-09-29 rebaseline. Shop Admin settings authority remains not granted; currency changes after financial history remain deferred.
- **Next task:** T3-03, but NOT AUTHORIZED; prepare its task plan and wait for exact `CONFIRM TASK T3-03`. Do not implement it automatically.
- **Git/CI:** T3-02A is complete. Commit is on `origin/main`. CI is green (GitHub Actions Project State Validation Run #17 SUCCESS).

### T3-02A verification record

Final verification outcomes are recorded in the `Tests and checks` section below.

## Historical tests and checks — T3-02A

- Application suite: 130 collected, 130 passed (`python -m pytest -q -p no:cacheprovider --no-cov`).
- Dedicated T3-02A module: 10 passed; the complete 130-test run also covers existing auth lifecycle, migration, and API error tests.
- Historical T3-02A validation: repository validator PASS; validator tests: 11 passed; detected 130 application tests and expected dirty working tree.
- `manage.py check`: PASS. `manage.py check --deploy` with `DJANGO_ENV=prod`: PASS. Default development `check --deploy`: exit 0 with six expected local dev security warnings (DEBUG, development secret, SSL redirect/HSTS, secure session/CSRF cookies).
- `manage.py makemigrations --check --dry-run`: PASS, no changes. Both T3-02A migrations are applied locally. API schema validation: PASS.
- Black check for new/rewritten account implementation: PASS. Black and Flake8 for `scripts/`: PASS. Flake8 for account implementation: PASS. `git diff --check`: PASS.
- GitHub Actions: the GitHub Actions workflow passed successfully for T3-02A.
- Git status: local working tree is clean. Branch `main` is up to date with `origin/main`.
- **Historical Changed areas:** User API authorization/serializer, Main Supplier Shop-write permission, membership serializer lifecycle protection, real throttle wiring/tests, duplicate CORS tests, production CORS environment propagation, CI validation, remediation regression tests, and documentation.
- **Validation:** remote CI is green: the latest GitHub Actions workflow passed successfully.
- **Historical next implementation candidate:** T3-03 was then unconfirmed; it has since been completed as recorded above.
- **Policies as of T3-03 completion (historical):** ordinary-user global Shop read visibility and Shop delete/archive/deactivate semantics were then unresolved; the 2026-09-29 rebaseline approved membership-authorized Shop visibility and deactivate/no-ordinary-DELETE. Shop Admin scoped settings authority remains not granted; currency changes after financial history remain deferred.
- **Agent Transition Note:** Upcoming engineering work may be executed through Codex; repository governance and explicit task-confirmation rules remain authoritative regardless of implementation agent.
## Repository state evidence
- Verify current HEAD with `git rev-parse HEAD`
- Verify remote parity with `git status -sb`
- Do not treat a stored commit hash in documentation as authoritative.

## Repository and workspace

- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- `docs/`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Historical Phase 1 corrective implementation was completed and published to `origin/main`.
- At the reviewed baseline, branch `main`, HEAD and `origin/main` matched; T3-02 remediation is committed and GitHub Actions was green. Recheck Git and CI after documentation updates; prior evidence does not validate this diff.
- Starter source files were modified for Phase 1.
- Existing SGTP `.git` metadata and history preserved.

## Target final product

SGTP is now defined as the Supplier-Centric Garment & Tailor Platform, with Tailor Management as the core V1 module. The hierarchy is Supplier/Main Admin -> Supplier Back Office -> isolated Shop workspaces -> Clients, Designs, Measurements, Fabric/Materials, Work, Billing, and Reports.

The required persisted flow is:

`Client Request -> Design -> Measurement -> Fabric/Material -> Cutting -> Stitching -> Check -> Finishing -> QC -> Completed -> Billing -> Reports/History`

The full product definition and Definition of Done are in `docs/PRODUCT_DEFINITION.md`.

## Locked V1 tenancy model

- V1 has exactly one top-level Supplier / Main Admin and no multi-supplier SaaS model.
- The hierarchy is Main Supplier / Main Admin → Supplier Back Office → multiple isolated Shops.
- Shop is the tenant/workspace boundary.
- External Supplier records are owned by exactly one Shop and are not users, tenants, members, roles, or authentication participants. They do not log in.
- External Supplier records are not global/shared; Shop isolation applies to all access and discovery paths.
- The starter `Tenant` model has been retained and structurally mapped as the V1 technical implementation for `Shop`. T3-01 verified this structural mapping was safe. A `Supplier` singleton model was created to enforce exactly one top-level platform owner.

## Inspection summary

The starter is a Django 5.1.4 / DRF 3.15.2 PostgreSQL project with Docker, devcontainer, JWT authentication, a custom email user, tenants, UUID/audit/soft-delete base models, OpenAPI/Swagger, and tests. It contains `core/`, `apps/accounts/`, `apps/tenants/`, `apps/common/`, templates, dependency/tooling files, Docker infrastructure, and editor configuration.

## Reusable

- Django project wiring and environment-loading pattern.
- Custom user model, user manager, admin, JWT endpoints, serializers, and initial tests.
- Tenant model/admin/API/migrations/tests as a starting point only.
- UUID, timestamps, audit fields, and soft-delete base model.
- PostgreSQL, Docker, devcontainer, Gunicorn, WhiteNoise, Makefile, and tooling setup.

## Phase 3+ Deferred Implementations

- `BaseModelWithTenant.tenant` remains nullable. T3-03 establishes request context and T3-04 provides reusable query/object isolation primitives; future concrete Shop-owned endpoints must adopt and verify those primitives.
- The starter is not yet the target product: Clients/Related Persons, Catalog/Designs, and Measurements/Materials foundations now exist in the local implementation; Work/production stages, billing, reports/PDFs, frontend, persistent storage, workers, complete audit capture, monitoring, and full end-to-end validation remain incomplete. T3-03's pushed baseline passed GitHub Actions run #19. T3-04, T3-04A, T3-04B remediation, T3-04C, T3-05, and the T3-05A staging backend foundation are published; remaining work is individually gated.
- The target requires React/Vite/Tailwind, but the starter has only an empty `frontend/` placeholder. English/ar-KW/Bangla/Urdu localization, RTL/LTR, and Light/Dark/System are planned V1 requirements, not implemented.
- Tenant context is implemented as URL-path based (`/api/v1/shops/{shop_id}/...`); T3-04 primitives are available, and each future Shop-owned endpoint must apply them to queries and objects.
- Related Person billing ownership is approved as Primary Client ownership and must be implemented/tested in Phase 5.

## Historical Phase Status

Phase 1 and Phase 2 are complete. 
Historical Phase 3 task outcomes:
- **T3-01 Supplier and Shop Entities**: Complete. The repository has a reproducible database baseline, Shop mapping, and Supplier singleton constraint.
- **T3-02 User-Shop membership and roles**: Complete. `TenantMember` and `ShopRolePolicy` firmly establish user roles and Main Supplier cross-shop authority.

## T3-02 remediation status

- Ordinary users cannot enumerate or target other User records through the User API; self-profile updates remain supported.
- Shop write and activate/deactivate permissions now use `ShopRolePolicy.is_main_supplier_admin`, so `is_staff` alone is insufficient.
- Membership `is_active` is read-only in generic PATCH/PUT; lifecycle actions remain the only state-transition API.
- Real authentication throttling is verified by an integration-style repeated-login test; duplicate CORS tests are independently collected.
- CI now includes the full application suite, Django check, and migration check in addition to project-state validation.
- Production CORS configuration receives `DJANGO_CORS_ALLOWED_ORIGINS` from deployment environment variables.
- No migrations were created.
- At that historical checkpoint T3-03 request context, External Supplier records, and future business modules remained unimplemented; T3-03 has since been completed as recorded above.

## Historical roadmap handoff (superseded by the current T3-04 status above)

T3-02A-BUSINESS-DECISION-LOCK authorized documentation/business-rule reconciliation only. Do not implement T3-02A, T3-03, T3-05A (Staging Backend Foundation), F7-01A (Staging Frontend & Client Review Checkpoint), any application feature, or deploy any environment under this task. T3-02A remains the next candidate and requires its own task plan and exact explicit confirmation. Newly approved account/authentication policies are targets, not implemented behavior; remaining policy items stay `BUSINESS DECISION REQUIRED` in the canonical decision record.

## Historical tests and checks — V1-ROADMAP-UPDATE

- Repository validator: PASS (dirty working tree warning is expected until documentation changes are committed).
- Validator tests: 11 passed.
- Application suite: 120 passed; collection was 120.
- Django system check: PASS.
- Migration check: no changes detected.
- `git diff --check`: PASS (Git emitted only CRLF-to-LF normalization warnings).
- GitHub Actions: the previously verified baseline run was green; this local documentation diff has not been pushed and has no new CI run.
- Scope: documentation only; no application source, migrations, deployment, commit, or push.

## Historical: T3-02A-BUSINESS-DECISION-LOCK (superseded by the current T3-02A status above)

- Decision: approved T3-02A account/authentication, phone, credential lifecycle, Shop settings, locale, and appearance rules are now recorded in the canonical business-rule and decision documents.
- Code status: unchanged. Anonymous User creation is still available in the current endpoint, and login remains email-only; T3-02A must reconcile these approved policy targets.
- Validation: repository validator PASS (dirty-tree warning expected); validator tests 11 passed; full pytest 120 passed; Django check PASS; migration drift check no changes; `git diff --check` PASS. Business Rule IDs are unique and `BUSINESS_RULES.md`/`DECISIONS.md` pass strict UTF-8 decoding. Current local diff has no new CI run.
- Next task: T3-02A remains unauthorized; obtain its exact task confirmation before implementation. T3-03 also remains unauthorized.

## Current handoff — GARMENT-SYSTEM-BACKEND-01 (2026-10-07)

- Confirmed and implementing backend only in existing `main` worktree. Preserve unrelated dirty files, especially prior measurement/client frontend and backend changes; do not commit, push, deploy, or run frontend.
- Implemented in working tree: Shop-owned GarmentFamily/OptionGroup, Shop-scoped family/group list/create/config APIs, per-family explicit selection mode/required flags, optional Design.variant, publish-time configuration validation, optional exact published DesignVersion association on MeasurementSet, and copy preservation. New migration: `apps/catalog/migrations/0019_shop_owned_garment_systems.py`.
- Added catalog API tests for manual Shop garment system creation/ownership, configured required single group, family-level design publishing, cross-Shop privacy, and measurement snapshot link/copy preservation.
- Already verified: `.venv` compileall PASS; Django system check PASS; migration drift check PASS (no changes); migration 0019 applied by tests; OpenAPI artifacts regenerated with zero errors and identical hashes; focused 65 catalog/measurement API tests PASS; full `apps/` suite PASS (390 tests). The uniquely named disposable test database ran with R2 process vars empty; no staging object storage was touched.
- Final validation: Black PASS, Flake8 PASS, `git diff --check` PASS (line-ending normalization warnings only), Project State Validator PASS (459 tests discovered). Temporary PostgreSQL instance was cleanly stopped; no database files were deleted. Existing worktree remains dirty and no commit/push/frontend/deploy occurred.
- For continuation: inspect `git status` and the GARMENT-SYSTEM-BACKEND-01 diff before any further change. No frontend implementation is included; use these documented APIs for separately authorized frontend integration.
