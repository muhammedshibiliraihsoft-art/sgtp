# Handoff

## Current handoff — FRONTEND-RECONCILIATION-01 / STARTUP-PRIVATE-IMAGE-01 (2026-10-06; local validation complete, publication not authorized)

- Main's pre-work baseline was `643e598940cbae9c289d79866f77ace76a033e81`, matching `origin/main`. Preserve the user's existing work; current implementation is local-only. A recovery snapshot of the tracked diff and all then-untracked files is at `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp-main-cleanup-recovery-20261006`. The sibling `sgtp-frontend` worktree remains on `frontend/parallel-foundation` at `9ff32bc30d94744cfa0c432e4bb1c57d4182a20c`, with its 48 frontend dirty items unchanged.
- Frontend foundation and existing workflow UX were reconciled into this main worktree. Five same-path Catalog conflicts retained main's implementation, which enforces the approved single-current-image contract; two additional dirty `GlobalTemplateEditor` files were already main-only and were preserved. Shop context now hides stale user context during account changes; inventory request results are guarded by Shop/request scope. No frontend behavior was manually verified in an authenticated browser.
- Backend work retained and validated: `catalog.0015_styleoptionimage_primary` picks one deterministic current image per Style Option, enforces at most one primary, and leaves old image records/objects and Design source relationships intact. Upload accepts exactly one file and atomically replaces the current pointer. Missing private objects return 404; Shop upload authorization is wrapped in a transaction.
- Validation: full PostgreSQL-backed suite 447 passed; focused Catalog + private upload transaction tests 33 passed; repository validator discovered 447 tests and passed (at the pre-commit checkpoint it correctly warned the worktree was dirty); validator tests 31 passed; Django system check passed; migration drift reported no model changes; OpenAPI had 0 errors / 29 warnings (13 unique); changed backend files passed Black/Flake8. Frontend: 121 tests passed, typecheck/build passed, lint exited 0 with 15 `react(set-state-in-effect)` warnings; `git diff --check` passed.
- Local PostgreSQL was started from the existing `pgdata` cluster only for disposable test databases and stopped after testing. No staging/production database was touched. The existing Render staging deployment remains on its previous SHA. No push, deployment, or remote merge occurred. The previously verified original image still requires authenticated upload/display verification.
- Follow-up: re-run the repository validator after local commits and verify `main` is Git-clean while `origin/main` remains unchanged. Do not push or deploy without separate authorization.

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
- **Known limitations:** no front-end localization/theme UI, no Shop URL context or tenant isolation, no later-phase business modules. Shop defaults must not be read by ordinary users. Email reset delivery requires deployment email configuration and `PASSWORD_RESET_URL`.
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
