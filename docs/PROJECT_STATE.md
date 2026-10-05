# Project State

## Status

- **Current task: `STARTUP-PRIVATE-IMAGE-01` (2026-10-05; staging R2 live, upload transaction fix pending).** The existing Render service now has R2 configuration and R2-aware code; the deploy applied private-media migrations, collected static files, started Gunicorn, and returned 200 for live/ready health checks. The user saved bucket CORS and localhost upload preflight returned 204. An authenticated upload attempt uncovered `TransactionManagementError` because the Shop media authorization view called `select_for_update()` outside a transaction; the local `transaction.atomic` fix and regression test are pending publication. The existing source image still needs authenticated upload/display verification.
- **Previous local frontend performance audit (2026-10-05; historical checkpoint).** In the separate `frontend/parallel-foundation` worktree, changes reduced redundant Main Supplier Catalog, Shop-context, Measurement-design, Inventory-search, and Back Office Shop-search requests without changing backend contracts or business rules. Repeated warm health checks measured about 0.31–0.75 seconds through the local proxy. Authenticated Back Office/Shop browser timing was not verified. Billing/pricing UI remains outside the implemented local frontend scope.
- **Current integration checkpoint (2026-10-05; publication in progress).** Local `main` contains the Measurement-R2/Style Option backend APIs and migrations `catalog.0013`/`0014`, plus the integrated frontend baseline. R2 variables have been merged into the existing Render staging API and its environment-only deployment is live on the previously published SHA; the R2-aware code and its fail-fast staging guard are in local unpublished commits. Local tests recorded before this final publication pass: backend suite 446 passed, focused staging tests 20 passed, frontend suite 117 passed with typecheck/build; details in `docs/HANDOFF.md`. Do not claim image upload/display verification until performed through the authenticated app.
- **Previous local backend task: `CATALOG-STYLE-OPTION-EDIT-API-01`.** Shop-owned Style Option translation editing is implemented through the existing Shop-context PATCH route. Partial locale updates preserve omitted translations; code/group/Shop ownership remain immutable, and existing `is_active` updates are supported. Shop isolation and existing ADMIN/STAFF/Main Supplier Shop-context authorization are preserved. Focused Catalog API tests: 32 passed; full PostgreSQL-backed suite: 445 passed; repository validator PASS (445 discovered); validator tests: 37 passed; Django check PASS; OpenAPI: 0 errors/29 warnings (13 unique); no migration generated; changed-file Black/Flake8 PASS. At that task's validation checkpoint the frontend editor had not yet started.
- **Previous authorized task: `MEASUREMENT-R2-UI-01`.** Local implementation and validation completed; at that point full PostgreSQL-backed suite: 442 passed; focused Catalog/Measurement suite: 54 passed; validator: PASS (442 discovered); validator tests: 37 passed; Django check and migration drift: PASS; production deploy check: 0 errors (13 existing warnings); OpenAPI: 0 errors, 29 warnings (13 unique); changed-file Black/Flake8 and backend/frontend diff checks: PASS. Frontend: 89 tests passed, typecheck/build passed; lint exits 0 with React effect warnings and an existing large-chunk advisory. Three compressed samples are standalone private objects under `birky-desgin-test/`; they are not attached to a Shop/StyleOption and no business records were created. No commit, push, or deployment occurred.
- **Previous authorized task: `MEASUREMENT-E2E-01`.** Frontend/backend remediation is implemented, merged into `main`, published to the canonical remote branch, and its GitHub Actions Project State Validation passed. Render staging deployment and authenticated manual-browser verification remain pending because Render account access is unavailable in this workspace. The full test and check record is in the handoff history.

- **Previous authorized task: `T4-02-API-ENDPOINTS-01`.** Added Main Supplier-only global Family/Option Group creation, paginated Main Supplier-only global variant listing, and visibility-safe Global Design Template detail retrieval. No model or migration change. Catalog API tests: 22 passed; one existing Arabic-data test was excluded because the local PostgreSQL cluster uses WIN1252. Django checks passed with environment/schema warnings; OpenAPI had zero errors. Repository validator passed. Published to GitHub `main` on 2026-10-03 at implementation commit `3d17271dae879f5f26ceba5b46c413bf2d501310`; remote SHA was verified. No deployment occurred.

- **Previous authorized task: Catalog and Designs frontend integration.** Its implementation was committed on `frontend/parallel-foundation`, merged locally into `main`, and published with T4-02 API commit `3d17271dae879f5f26ceba5b46c413bf2d501310`. Frontend checks and the repository state validator passed. It connects existing Catalog and Designs pages to T4-02 APIs, replaces mock fallbacks with visible errors, and fills supported create/select/publish/archive/image-upload flows. No deployment occurred, and authenticated staging browser E2E was not performed. Remaining frontend UI gaps are recorded in `docs/HANDOFF.md`.

- **Historical task: STAGING-MAIN-ADMIN-BOOTSTRAP-01 is complete, pushed, and live on Render staging.** The implementation passed exact-SHA Project State Validation. One Main Supplier Admin was created through the guarded one-time command, with first-login password change required. The bootstrap switch is off, all four temporary inputs are blank, and the cleanup deploy is live with readiness HTTP 200. No Shop or migration was added.

- **Previously authorized maintenance: DJANGO-ADMIN-UX-01 is implemented, published to `main`, and CI-verified.** Native Django Admin now groups the existing account, Shop, client, catalog, measurement, and material models, with an explicit Main Supplier-only permission boundary. Catalog/business records are inspection-only unless an existing safe Shop service already supports an operation. Focused tests: 18 passed; full PostgreSQL-backed suite: 388 passed; validator tests: 30 passed; migration drift: no changes. No schema, migration, dependency, frontend, or deployment changes.

- **Historical task: BACKOFFICE-01 backend implementation is published to `main` and live on Render staging.** Readiness and CSRF bootstrap endpoints returned 200 after deploy. Its frontend implementation reused the existing shell and live Shop APIs; the Work page mock content was not reused. At that task's completion its feature branch had not yet been published. Backend adds a derived read-only `is_main_supplier_admin` profile field and no migration. Exact deployment evidence is in the historical changelog and handoff entries.
- Phase 1 and Phase 2 are complete.
- Phase 3 is COMPLETE; it was activated with `CONFIRM PHASE 3` and the approved T3-05A staging foundation is complete (custom-domain DNS/TLS remains explicitly deferred).
- Phase 4 is ACTIVE; Core Tailor Business activation was explicitly confirmed with `CONFIRM PHASE 4`. T4-01, T4-02, and T4-03 are COMPLETE, committed, published, and CI-verified. T4-03A — Inventory & Stock Foundation was explicitly confirmed with `CONFIRM TASK T4-03A` and is COMPLETE, COMMITTED, PUBLISHED, and exact-SHA CI-VERIFIED. Catalog/Design frontend integration is authorized as a separate integration task. T4-04 and Phase 5 remain unauthorized; this does not authorize other frontend business modules.
- T4-03A is an additive extension to completed T4-03. Focused T4-03A/T4-03 tests: 41 passed; full PostgreSQL-backed suite: 409 passed; validator: PASS with 409 tests discovered; validator tests: 32 passed; Django check: PASS; production deploy check: 0 errors with 12 warnings; migration drift: clean; OpenAPI: 0 errors, 28 warnings (12 unique); Black/Flake8/schema parity/diff check: PASS. GitHub Actions Project State Validation succeeded for the T4-03A implementation commit. Migrations were applied only to the disposable PostgreSQL test database. No deployment or shared/staging/production migration occurred.
- Historical T4-02 baseline `1287d61a1406bbdd3edddc778b91f59c9cca52df` passed Project State Validation run `36970391503`.
- T4-03 implementation checkpoint `d9ca27bbab8587c2da5ceb8c1f61f913087fdc48` passed Project State Validation run `37006408609`.
- API-DOC-REFRESH-01 and API-BROWSABLE-PORTAL-01 are completed historical maintenance tasks; neither changed Phase 4 authorization.
- Completed Phase 3 tasks include T3-01, T3-02, T3-02-REMEDIATION, T3-02A, T3-03, T3-04, T3-04A, T3-04B-REMEDIATION-01, T3-04B-USER-SCOPE, and T3-04C. T3-04C implementation commit `dfbf6eecdbcd36c014a45a5d297c26e4e27a4113` is published; exact-SHA Project State Validation run `36605653294` succeeded.
- T3-04B-USER-SCOPE is COMPLETE, COMMITTED, and PUBLISHED on `main` at `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c`; GitHub Actions Project State Validation run `36591864481` completed successfully for that exact SHA.
- T3-04 is COMPLETE, COMMITTED, and PUSHED on `main`. Live verification on 2026-09-29: local `HEAD`, `origin/main`, and remote `refs/heads/main` matched; derive the current SHA from Git.
- T3-04A is published at `304e6ec4a6811b0153db4dea1417d24affa11bec`; its GitHub CI passed.
- Initial T3-04B publication `5e3b1714289e7b5660e1a54d6cb2752b64d54683` failed GitHub Actions Run #36545855022 and was reverted. T3-04B-REMEDIATION-01 was published as the corrective checkpoint; T3-04B-USER-SCOPE is now published with its exact-SHA CI gate green.
- Historical Phase 3 publication record: T3-04B-REMEDIATION-01, T3-04B-USER-SCOPE, T3-04C, and T3-05 were implemented, validated, and published. T3-04C exact-SHA CI passed in run `36605653294`; T3-05 implementation commit `3d21a0943006cd866bc19bc728cbec05daae1630` passed Project State Validation run `36614638187`. T3-05A repository implementation and local validation were published; implementation checkpoint CI run `36652187336` succeeded.
- Current staging state: T3-05A is COMPLETE, published, and exact-SHA CI-green. Live provider-hostname checks verified login/cookie behavior, refresh rotation/reuse rejection/logout clearing, membership/User-ID/stats/Work-Function/direct-object isolation in both Shop directions, and Main Supplier access to approved Shop surfaces. The synthetic fixture remains; temporary credential variables are blank and bootstrap/rotation flags are false. Final cleanup deploy `dep-dau9ptlg1s2s73c2foig` is live on the published implementation checkpoint and both health endpoints return 200. Reserved custom-domain DNS/TLS and real frontend browser integration remain deferred.
- Historical T3-05A implementation checkpoint (not current HEAD): commit `9af6424116ebba12896d90d032c36bd25328a4d0`.
- The Parallel Frontend Foundation Track is an approved pre-Phase-7 preparation lane, separate from Phase 7/F7-01 completion and its formal dependencies. Its frontend source belongs in an isolated frontend branch/worktree; `main` remains the canonical backend/integration branch and owner of cross-project documentation. Unimplemented APIs/business workflows must remain behind mock adapters.
- The PHASE4-PARALLEL-UNBLOCK-01 roadmap correction makes backend Phase 4/5/6 delivery non-blocking with respect to frontend completion. Existing backend feature integration may continue independently on `frontend/parallel-foundation`; each new frontend domain slice remains contract-first and follows acceptance of its backend API. The UI Reference Gate and Dashboard Last Rule remain in force. Phase 4 activation and each task retain separate confirmation gates.

- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Phase 1 corrective implementation was completed and published to `origin/main`.
- Current branch: `main`
- Target status: SGTP V1 is explicitly defined in `docs/PRODUCT_DEFINITION.md`
- Starter foundation: exists in the cloned SGTP repository.
- Phase 1 implementation: **Historical - Complete.**
- Confirmation status: Phase 4 and T4-01/T4-02/T4-03/T4-03A were explicitly authorized. T4-01/T4-02/T4-03/T4-03A are complete and published; T4-03A exact-SHA CI is green. Catalog/Design frontend integration, T4-02 API endpoints, and GARMENT-FAMILIES-01 are separately authorized. T4-04, Phase 5, and other frontend business modules remain unauthorized.
- Current task: `STARTUP-PRIVATE-IMAGE-01` R2 reliability and existing image recovery. R2 variables are configured on the existing Render staging API, and its environment-only deployment is live on the previously published revision; publication of local R2-aware code is in progress. The original object key was absent from R2, so use only the verified original image. Do not claim upload/display until checked. The next business task and Phase 5 remain unauthorized.
- Detailed phase playbooks: 01-10 present.
- Later-phase decisions: Tenant context is approved as URL-path based (`/shops/{shop_id}/...`), and Related Person billing is owned by the Primary Client.
- T3-05A (Staging Backend Foundation) is complete. Active backend: `https://birky-staging-api.onrender.com`; reserved future API hostname: `https://api-staging.birky.com` (not owned/controlled, configured, DNS-verified, or TLS-verified). On 2026-09-30, live checks with synthetic Main Supplier and Shop A/B accounts verified login without refresh-token JSON exposure; Secure/HttpOnly/SameSite=Lax refresh cookie; CSRF-required refresh/logout; rotation, old-token reuse rejection, cookie clearing, and post-logout refresh rejection. Membership list/detail, exact User-ID, stats, Work Function, and direct-object isolation were verified for Shop A→B and B→A; Main Supplier access to approved surfaces in both Shops was verified. Temporary credentials are blank and bootstrap/rotation flags are false. Final cleanup deploy is live and both health endpoints return 200. No real customer data was used. F7-01A remains planned only; frontend browser integration and custom-domain DNS/TLS are deferred. T3-02A implemented the account/preference data and API foundation; frontend localization, RTL/LTR layout, and full Light/Dark/System UI remain Phase 7 work.
- At T3-02A completion, email was required and optional unique E.164 phone could authenticate the same UUID account. T3-04A subsequently made normal-user email and phone optional while retaining Main Supplier-controlled global account creation, no-store initial credentials, email reset, session revocation, locale/appearance preferences, and Shop defaults.
- T3-04A implements the published permanent User ID, optional normal-user email/phone, required first name, admin-grade contact safeguards, alias login, controlled reset, and User hard-delete denial. Published T3-04B remediation enforces membership/Admin lifecycle and cardinality invariants. Published T3-04B-USER-SCOPE adds one immutable owning Shop per ordinary account, same-Shop membership enforcement, scoped creation/reset, and a guarded migration. Published T3-04C adds normalized membership-scoped Work Functions and Shop-ADMIN-only set management without permission escalation. T3-05 Shop visibility/lifecycle/API/Admin hardening is published at `3d21a0943006cd866bc19bc728cbec05daae1630`; exact-SHA Project State Validation run `36614638187` succeeded.
- T3-02A and T3-03 historical CI records remain below. The published T3-04 baseline and the later T3-REBASELINE-01 documentation checkpoint passed GitHub Actions Project State Validation (runs #36511111586 and #36524789793 respectively).

## Current Verification Results

- **MEASUREMENT-E2E-01 local validation:** Backend full PostgreSQL suite 433 passed; focused Measurement API/concurrency/default-template and Shop-context tests 40 passed. Frontend tests 84 passed, typecheck and production build passed, lint exited 0 with React state-in-effect warnings. Django system check passed; production deploy check had 13 drf-spectacular warnings; OpenAPI generated/validated with 0 errors and 29 warnings (13 unique). No model changes detected. Migration-history consistency check could not connect because configured base database `testdb` does not exist. The frontend integration is merged and published to `main`; local and `origin/main` both resolve to `a619ca6cd395cf47f85bc09b75ee34dc977dfb6c`, and GitHub Actions Project State Validation run `37114613711` passed for that SHA. Backend/frontend diff checks pass and schema copies match. No authenticated browser test, Render deployment, or shared/staging/production migration occurred because Render account access is unavailable in this workspace.


- **Previous GARMENT-VARIANTS-01 backend and frontend checkpoint:** Full PostgreSQL-backed backend suite: 430 passed; focused Catalog/Measurement/Variant API and concurrency suite: 56 passed; validator tests: 30 passed; repository state validator PASS (430 discovered). Django system and production deploy checks PASS (12 existing OpenAPI warnings); migration drift clean; OpenAPI 0 errors/28 warnings (12 unique); Black/Flake8/schema generation/diff check PASS. Frontend typecheck PASS; seventy frontend test cases across 13 files PASS; lint exits 0 with six existing warnings in unchanged shared files; build PASS with an existing bundle-size advisory; diff check PASS. Backend branch `main` and frontend branch `frontend/parallel-foundation` remain local/uncommitted with Family changes preserved. Only disposable UTF-8 PostgreSQL test databases were migrated. No push, merge, deployment, or shared/staging/production migration. Authenticated manual browser check remains pending user login.

- **GARMENT-FAMILIES-01 frontend checkpoint:** Shop Family browse/search/pagination/detail and filtered Variant/Design navigation; Main Supplier create/edit/archive/reactivate, private image management, and ordered Option Group mapping. Typecheck PASS; frontend tests 59 passed; build PASS; diff check PASS; lint exits 0 with six existing warnings in unchanged files. Authenticated visual responsive verification is pending user login. Frontend changes are local/uncommitted on `frontend/parallel-foundation`.

- **DJANGO-ADMIN-UX-01 validation:** focused Admin/security suite 18 passed; full PostgreSQL-backed application suite 388 passed; repository validator PASS (388 tests discovered); validator tests 30 passed. Django system check PASS; production deployment check PASS with 12 existing nonfatal OpenAPI warnings; migration drift: no changes; OpenAPI: zero errors with existing warnings; Black, Flake8, and `git diff --check` PASS. Implementation commit `608362d6509b286ba0daa9ede4e33d39d2888a6c` passed exact-SHA Project State Validation run `37017703294`. No schema/migration/frontend/deployment changes.

- **T4-03 complete and published:** focused measurement/material API and PostgreSQL concurrency tests: 20 passed; full PostgreSQL-backed application suite: 370 passed using project test settings with a UTF-8 disposable database. Repository validator: PASS (370 application tests discovered); validator suite: 30 passed. Django system check: PASS; `DJANGO_ENV=prod check --deploy`: no errors (12 nonfatal drf-spectacular warnings); migration drift: no changes. OpenAPI: zero errors, 28 warnings (12 unique, including type-hint/enum warnings and automatically disambiguated measurement operation IDs). Black, Flake8, schema artifact parity, and `git diff --check` passed. Implementation commit `d9ca27bbab8587c2da5ceb8c1f61f913087fdc48` passed exact-SHA Project State Validation run `37006408609`. No deployment occurred.

- **API-DOC-REFRESH-01:** Internal `/api/docs/` and `/api/schema/` access is restricted to authenticated Main Supplier users via Django Admin session; anonymous access redirects to Admin login and other authenticated users receive a non-disclosing 404. Root redirects to docs; session auth is excluded from business APIs; Swagger authorization persistence is disabled. The stale public test page and unused `/api-auth/` route were removed. Live anonymous checks: root/docs/schema redirects verified; both health probes returned 200. Focused PostgreSQL-backed tests: 62 passed; full suite: 315 passed. Repository validator PASS (315 tests discovered); validator tests 27 passed; Django system and production deployment checks PASS; migration drift: no changes; OpenAPI: zero errors, 23 warnings (7 unique); Black, Flake8 and `git diff --check` PASS. Published at checkpoint `9e93a77754ac03839d038e5e3a32458208bc02e9`; exact-SHA CI run `36850074419` succeeded. No deployment occurred.
- **API-BROWSABLE-PORTAL-01:** Added Main Supplier-only `/api/browse/` endpoint explorer from protected OpenAPI schema; root points to this page and Swagger remains at `/api/docs/`. Requests stay same-origin under `/api/v1/`; required API calls use Bearer JWT in page memory only, while Django Admin session alone still returns 401 from business APIs. CSRF bootstrap is used on unsafe requests; refresh/logout continue using their existing protected cookie lifecycle. Browser smoke showed 50 operations, static assets returned 200, and no console errors. Focused docs/browser tests: 10 passed; full PostgreSQL-backed suite: 319 passed. Repository validator PASS (319 application tests discovered); validator tests: 27 passed; Django system and production deployment checks PASS; migration drift: no changes; collectstatic dry-run PASS (166 assets discovered); OpenAPI: zero errors, 23 warnings (7 unique); Black, Flake8, JavaScript syntax check and `git diff --check` PASS. Published at implementation commit `304c9666f680e3e32aa05e4545b44aa049963e19`; exact-SHA GitHub Actions Project State Validation run `36862739900` succeeded. No model/API behavior, migration, dependency, React frontend, or deployment changes.

- T4-01 validation: focused Clients/Related Persons API and PostgreSQL concurrency tests: 15 passed; full PostgreSQL 15-backed application suite: 309 passed. Repository validator: PASS (309 application tests discovered); validator tests: 27 passed. GitHub Actions Project State Validation run `36796609814` succeeded for exact commit `e4e5e4126d60bfb563fbd25fbf0baab9e85963f9`.
- Django system check and production `check --deploy`: PASS; `makemigrations --check --dry-run`: no changes detected. OpenAPI validation: zero errors, 23 warnings (7 unique, existing serializer type-hint/role-enum warnings). Black and Flake8 checks for the changed/new Python files and `git diff --check` passed.
- The full-suite run used local PostgreSQL 15; GitHub Actions separately completed successfully for the exact published T4-01 SHA. No deployment occurred.
- T3-05A live staging security/isolation verification passed using only the existing synthetic fixture. Staging-focused tests: 28 passed; authentication/CSRF lifecycle regressions: 7 passed. Docker image build and disposable local Docker/PostgreSQL smoke passed: migrations and static collection completed; liveness/readiness/CSRF bootstrap returned HTTP 200.
- Historical staging bootstrap evidence and deploy IDs below remain checkpoint records. Final T3-05A evidence: implementation commit `b29a897897d35ec9163c510456bd9197b8a4f6e1`; Project State Validation run `36667104952` succeeded for that exact SHA with 294 application tests. Render was verified as Free/Frankfurt Docker service plus Free/Frankfurt PostgreSQL 15, auto-deploy off and DB IP allow-list unchanged. Final application deploy `dep-dau9ptlg1s2s73c2foig` runs that SHA; logs confirmed migrations, collectstatic, and Gunicorn startup, with no secret exposure found. Credential variables were blanked and both bootstrap/rotation flags false; both health routes return 200. Complete authenticated endpoint isolation and token lifecycle checks passed. Custom DNS/TLS and frontend browser integration remain deferred.

## Verification history

- **T3-05 — published (task-time record):** commit `3d21a0943006cd866bc19bc728cbec05daae1630`; GitHub Actions Project State Validation run `36614638187` completed SUCCESS for that exact SHA. Local focused tests: 30 passed. Full PostgreSQL-backed application suite: 231 passed (186 warnings). Repository validator PASS (231 discovered); validator tests 14 passed; Django system/deployment checks, migration drift, OpenAPI (zero errors), Black, Flake8, and `git diff --check` passed. No migration/dependency changes. At that T3-05 checkpoint, T3-05A, Phase 4, frontend, and deployment were unstarted.

- T3-04B remediation focused suite: 77 passed, including exact immutable-identity/error-envelope assertions and Shop/Admin lifecycle cases.
- PostgreSQL-backed full application suite: 183 passed (113 warnings), including separate-connection tests for concurrent promotions, demotion versus global deactivation, and first-ADMIN creation versus User deactivation.
- Regression suite for T3-04A identity/authentication, T3-03 Shop context, membership and migration behavior: 39 passed.
- Repository validator: PASS (183 tests discovered); validator tests: 14 passed. Django system check and `DJANGO_ENV=prod` deployment check: PASS. OpenAPI schema validation: PASS. Black and Flake8 for changed Python files: PASS; `git diff --check`: PASS.
- `makemigrations --check --dry-run`: PASS against the available local PostgreSQL `devdb`; no model changes or migration-history warnings.
- The initial T3-04B commit remains historical failed evidence and was reverted before this correction. Confirm the Project State Validation result for the exact T3-04B publication SHA before proceeding.

### Latest T3-02A Verification

- Full application suite: 130 collected, 130 passed (`pytest -q -p no:cacheprovider --no-cov`).
- Repository validator: PASS; validator tests: 11 passed. Validator confirms 130 discovered application tests and reports only the expected dirty-worktree warning.
- Django system check: PASS. Production deployment check (`DJANGO_ENV=prod`): PASS with no issues. The default local development `check --deploy` emits six expected development-environment security warnings; the production settings check is clean.
- Migration status: both new migrations applied locally; `makemigrations --check --dry-run`: no changes detected.
- API schema validation: PASS. Black check for new/rewritten account implementation: PASS; Black and Flake8 checks for `scripts/`: PASS; Flake8 for account implementation: PASS.
- `git diff --check`: PASS. GitHub Actions Project State Validation Run #17 reported SUCCESS for the pushed commit.

### Latest T3-03 Verification

- T3-03 uses DRF request-local context at `/api/v1/shops/{shop_id}/context/`; authentication and the password-change gate precede Shop resolution.
- Shop context requires an active, non-deleted Shop and either an active, non-deleted membership or explicit Main Supplier authority. ADMIN, STAFF, and VIEWER memberships may enter context; selected-Shop role is attached to the request.
- Foreign, unauthorized, inactive, deleted, unavailable, and nonexistent Shop requests return the same non-disclosing 404 (`shop_context_unavailable`). Unauthenticated, invalid, and revoked credentials preserve 401 behavior.
- T3-04 reusable queryset/object isolation primitives are complete; actual business-resource endpoints must adopt and verify them. This T3-03 verification entry is historical: ordinary Shop visibility and Shop deletion were unresolved at that task's completion, then resolved as target rules by the 2026-09-29 rebaseline. Shop Admin settings authority remains not granted; currency changes after financial history remain deferred for a financial-policy decision.
- Focused context/membership/permission suite: 76 passed; the dedicated Shop-context module contains 15 tests.
- Full application suite: 145 passed (144 warnings). Django check, migration drift check, OpenAPI schema validation, validator unit tests (14 passed), Black, Flake8, and `git diff --check` passed.
- Repository validator: PASS; Phase 3 is recorded as active with explicit activation in both current-state documents. It discovered 145 application tests.
- No database schema or dependency changes. T3-03 is committed and pushed; GitHub Actions Project State Validation Run #19 passed.

### T3-04 Verification Record (initial local completion; later published)

- Added trusted-context queryset scoping and server-controlled Shop ownership in `TenantScopedMixin`; bound `IsTenantMember` object authorization to the selected Shop, including Main Supplier requests.
- Updated the temporary proof model to use a UUID Shop foreign key and soft-delete base; added tests for selected-Shop lists/counts, foreign direct IDs, Main Supplier one-Shop scope, create ownership, update/reparenting, absent/mismatched context, and deleted rows.
- Focused scope/context tests: 28 passed. Full application suite: 152 passed (144 warnings). Repository validator: PASS (152 discovered; dirty-tree warning expected); validator tests: 14 passed. Django system check: PASS; migration drift check: no changes; OpenAPI schema validation: PASS; Black check: PASS; Flake8: PASS; `git diff --check`: PASS.
- No business models/APIs, migrations, or dependencies were added. `BaseModelWithTenant.tenant` remains nullable because no concrete business subclass exists. No production schema, dependency, API-route, or business-module changes were made.
- The local validation figures above are task-completion evidence. T3-04 was subsequently committed/pushed on `main`; the verified published commit and CI status are recorded in the current Status section. T3-REBASELINE-01 was later published as a documentation-only checkpoint and passed GitHub Actions Project State Validation.

## Locked V1 business tenancy model

- Exactly one top-level Supplier / Main Admin exists in V1; there is no multi-supplier SaaS model. Enforced via `Supplier` singleton model.
- The hierarchy is one Main Supplier / Main Admin → Supplier Back Office → multiple Shops.
- Shop is the actual business workspace and tenant/isolation boundary.
- External Supplier records belong to exactly one Shop and are non-user, non-tenant business records with no login or system permissions.
- External Supplier data is never global/shared and is isolated by Shop.
- **Tenant mapping:** The legacy starter `Tenant` model has been retained and structurally mapped as the implementation of the `Shop` entity. T3-01 verified this structural safety and created the `Supplier` owning entity.

## Repository verification

- `git ls-remote` succeeded against the corrected URL.
- The existing cloned SGTP repository is now the project root.
- `AGENTS.md` and `docs/` were moved into the SGTP repository without overwriting starter files.
- Phase 1 corrective changes have been committed and pushed.

## Starter structure

- `core/`: Django settings, URL configuration, ASGI, and WSGI.
- `apps/accounts/`: custom email-based user, manager, JWT/login/logout endpoints, admin, migration, and tests.
- `apps/tenants/`: tenant model, admin, CRUD/action API, migration, and tests.
- `apps/common/`: abstract UUID/audit/soft-delete base models, including a tenant-aware base model.
- `templates/api_test.html`: simple endpoint reference page.
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `setup.cfg`: runtime and development dependencies/tooling.
- `Dockerfile`, `Dockerfile.dev`, `docker-compose.prod.yml`, `.devcontainer/`: container and PostgreSQL infrastructure.
- `.vscode/launch.json`, `Makefile`, `.env.example`, `.gitignore`, `README.md`, `LICENSE`: local development and project documentation.

## Existing technologies

- Python 3.13 container target; local inspection interpreter was Python 3.12.10.
- Django 5.1.4 and Django REST Framework 3.15.2.
- PostgreSQL 15 through psycopg 3.2.3.
- SimpleJWT, drf-spectacular, django-filter, django-cors-headers, django-safedelete, WhiteNoise, Gunicorn, Pillow, and python-dotenv.
- Docker Compose and VS Code Dev Container workflows.
- pytest configuration plus Django TestCase-based tests; Black, Flake8, isort, and coverage tooling.

## Existing reusable components

- Custom `User` model using email as `USERNAME_FIELD`.
- User manager with password hashing and superuser validation.
- JWT access/refresh login, refresh, logout, and user profile endpoints.
- `BaseModel` with UUID primary key, timestamps, audit-user fields, and cascade soft delete.
- `BaseModelWithTenant` with an optional tenant foreign key.
- Tenant CRUD/action API, admin, serializers, migrations, and initial tests.
- API schema/Swagger routes and DRF pagination/filter/search/order configuration.
- PostgreSQL/Docker/devcontainer setup and production Gunicorn entrypoint.

## Target alignment and contradictions

- The project target is now a complete Supplier-Centric Garment & Tailor Platform, not merely a generic Django/DRF starter.
- Tailor Management is the core V1 business module, with isolated shop workspaces under a supplier back office.
- The required end-to-end workflow is documented. T4-01 provides Clients/Related Persons, T4-02 provides Catalog/Designs, T4-03 provides Measurements/Materials, and T4-03A provides Shop inventory. Work/production stages, billing, and reports remain unimplemented.
- At this main-branch baseline, the target requires React/Vite/Tailwind but the repository has no tracked frontend application yet. Parallel frontend foundation work is isolated from `main`; the empty-directory/branch implementation state is verified separately by Git.
- The target requires a service layer, object-level permissions, persistent object storage, background jobs, audit logging, CI, monitoring, and automatic documentation; the starter does not implement these as complete capabilities.
- T3-03 request-local active-Shop context and T3-04 reusable queryset/object isolation primitives are implemented. T4-01 is the first business-resource API and adopts/tests them; later endpoints must do likewise.

## Phase 3+ Missing or incomplete business logic

- `BaseModelWithTenant.tenant` remains nullable, but T4-01 Client/RelatedPerson models use required Shop FKs and endpoint isolation tests. Other future Shop-owned models/endpoints must enforce and test their own scope.
- Tenant-context resolution is implemented at `/api/v1/shops/{shop_id}/...`; T4-01 adopts T3-04 shared query/object primitives. Remaining endpoint-specific isolation work is future work.
- Billing ownership for work belonging to a Related Person is approved as Primary Client ownership and must be enforced in Phase 5.
- Implemented Phase 4 business modules are Clients/Related Persons, Catalog/Designs, and the T4-03 Measurements/Materials foundation, alongside accounts, tenants, and membership. Work/production workflow and Phase 5 billing/reporting remain unimplemented.

### PRE-P3-02 result

- The V1 Supplier / Shop / External Supplier business meaning is now explicit across the governing documentation.
- Historical PRE-P3-02 task-time outcomes: T3-01, T3-02, T3-02-REMEDIATION, T3-02A, T3-03, and T3-04 were complete; T3-05 and subsequent tasks then remained individually gated.

### T3-02 remediation result

- User API access is restricted so ordinary authenticated users cannot enumerate, modify, or delete other users; self-profile updates remain available and account activation state is read-only through the serializer.
- Shop write actions and activation/deactivation use the existing `ShopRolePolicy` Main Supplier authority instead of Django `is_staff` alone.
- Generic membership updates cannot change `is_active`; lifecycle actions remain authoritative.
- Authentication throttling is explicitly wired to the `auth` scope and verified with a non-mocked repeated-login test.
- Duplicate CORS test method names were corrected so all intended tests are collected.
- CI retains project-state validation and is configured to run the application suite, Django system checks, and migration checks with PostgreSQL. The GitHub Actions run for the reviewed baseline successfully passed all checks, including the application suite, Django system checks, and PostgreSQL integration. Remote CI confirmation is fully green and the PostgreSQL connectivity issue is resolved.
- Production compose now propagates `DJANGO_CORS_ALLOWED_ORIGINS` without inventing a deployment origin.
- No migrations were required or changed.
- Remaining decisions include Shop Admin settings authority (not granted), currency changes after financial history, and later items listed in `docs/DECISIONS.md`. T3-04A identity, T3-04B membership/Admin invariants, T3-04B-USER-SCOPE, and T3-04C Work Functions are published; broader Shop API visibility/lifecycle enforcement remains T3-05.

### Phase 3+ Deferred Implementations

- T4-01 Client/Related Person endpoints have Shop A/B direct-ID, search, relationship, and duplicate non-disclosure tests. End-to-end isolation across the complete V1 business workflow is not yet demonstrated; all later business endpoints must adopt/test T3-04 primitives.
- Tenant-aware base model permits `tenant = NULL`; T3-03 establishes trusted request context and T3-04 provides reusable query/object scoping, but neither changes model nullability nor creates domain queries.
- Tenant-context resolution is implemented as URL-path based (`/api/v1/shops/{shop_id}/...`).
- Billing ownership for work belonging to a Related Person is approved as Primary Client ownership and must be enforced in Phase 5.
- Clients/Related Persons, Catalog/Designs, and Measurements/Materials are implemented and published through T4-03; Work, billing, and reports remain unimplemented.

## Historical Phase 1 Verification results

- Repository access: passed.
- Clone: passed.
- Phase 1 corrective changes were committed and published to `origin/main`.
- File inventory and source/configuration inspection: completed.
- Django check: passes without issues.
- Application tests: the then-current full project suite passed (historical; see Current Verification Results above for the present verified result).

## Current root verification

- Repository root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- Documentation: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- `backend/` contains settings and shared model foundation code; runtime Django apps remain under root `apps/`. `apps/clients` and `apps/catalog` are implemented and published through T4-03. `frontend/` is maintained in the isolated frontend worktree; Work, billing, and reports remain unimplemented.

## Historical completed task — T3-04B-USER-SCOPE

- Status: COMPLETE, COMMITTED, and PUBLISHED on `main`; commit `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c`; GitHub Actions Project State Validation run `36591864481` SUCCESS for the exact commit.
- Approved rule: each ordinary User is permanently owned by one Shop. The same person in another Shop has a separate account. Main Supplier accounts remain global. Existing accounts cannot be moved or attached to another Shop.
- Implemented and published: `User.owning_shop`, guarded migration `accounts.0005_user_shop_ownership`, database membership/ownership consistency and immutability checks, atomic Shop-owned account creation, Main Supplier and Shop ADMIN account authority, Shop Admin STAFF/VIEWER reset scope, and regression tests/docs.
- Preflight evidence: local development PostgreSQL database contained zero Users and zero memberships before this migration was applied locally; GitHub CI migration/application validation ran against its disposable PostgreSQL database and passed. No shared/staging/production ownership preflight was performed and no such migration was applied; migration stops with affected UUIDs if it encounters ordinary accounts spanning multiple Shops or with no determinable Shop.
- Pre-publication local validation: focused account/membership/auth regressions 138 passed; PostgreSQL-backed full suite 192 passed, including four concurrency cases; validator tests 14 passed; Django and migration checks passed; OpenAPI passed with two nonfatal role-enum naming warnings; Black/Flake8 passed on new Python files. GitHub Actions Project State Validation passed for the published exact SHA. Shared/staging/production ownership preflight was NOT PERFORMED, and no shared/staging/production migration was applied.
- At the T3-04B-USER-SCOPE checkpoint, T3-04C was awaiting its own authorization. It has since been completed and published. T3-05, T3-05A and Phase 4 have not been started by this task.

## Phase playbook confirmation audit

- All ten phase implementation prompts use the mandatory phase-level activation plus task-level confirmation model.
- Phase confirmation activates scope only; it does not authorize all tasks.
- Each task requires a separate task brief and explicit `CONFIRM TASK <TASK-ID>` before implementation.
- After one task, the agent must validate, document, report, and stop; next-task and next-phase activation are never automatic.
- Phase playbooks 07-10 have now been added with task IDs, validation, handoff, rollback, Definition of Done, and implementation prompts.

## Completed Implementation Record (Phase 2 Complete)

- Phase 1 is complete. F1-01 through F1-05 are all complete.
- Phase 2 is complete.
- B2-01 DRF API Baseline is complete.
- B2-02 JWT Lifecycle implementation is completed and verified.
  - Standard Django CSRF mechanism is implemented.
  - Refresh token cookie lifecycle is implemented.
  - Rotation and blacklist/reuse behavior are implemented.
  - Relevant validation results are recorded accurately .
- B2-03 Permission and tenant-scope interfaces implementation is completed and verified.
  - Reusable tenant queryset scoping is implemented via `TenantScopedMixin`.
  - `IsTenantMember` is intentionally a deny-by-default Phase 3 contract.
  - Actual Shop/User membership is implemented (T3-02), but business tenant isolation (URL context) remains Phase 3.
  - 403/404 boundaries strictly enforced and validated .
- B2-04 is complete and audit-cleared.
  - Custom API exception handler normalizes errors.
  - Throttling configured for auth scopes.
  - `CORS_ALLOWED_ORIGINS` explicitly restricted.
  - Lightweight `/api/health/live/` and DB-connected `/api/health/ready/` probes are operational.
- B2-05 is complete. Schema generation fixed, throttling and CORS tests added. F-01, C-01, C-02, and C-03 resolved. Phase 2 is now complete.
- Python virtual environment `.venv` created, and dependency baseline established. `manage.py check` passed.
- Historical at Phase 2 completion: lint tools ran with existing starter violations; the application suite passed against the devcontainer PostgreSQL database. Current remediation closure validation is recorded above and supersedes old test claims.
- Environment settings are now split into base, dev, test, and prod. `core/settings.py` acts as a backward-compatible router rejecting unknown environments. Missing secrets fail safely.
- The `User` model was decoupled from `django-safedelete` (replaced with `TimeStampedUUIDModel`) to fix identity uniqueness issues with soft-deletion, and base models were refactored to `backend/core/models/base.py`.
- The database migration strategy has been established and documented in `docs/DATABASE.md`. A fresh PostgreSQL migration from an empty database applies perfectly, and the forward-only migration policy is in place.
- JWT configuration hardened with explicit algorithm, UUID claims, signing key, UPDATE_LAST_LOGIN, and 30-min access tokens. Security cookie flags are explicit per environment (dev: disabled, prod: HttpOnly + Secure). Logout view no longer leaks exception details. `.env.example` documents all required variables including `DJANGO_ENV`.
- The JWT blacklist app is installed and configured.

## Canonicalization audit

- The approved target Django structure is documented separately from the current starter paths: `backend/config/settings`, `backend/apps/{accounts,shops,clients,catalog,works,billing,reports,ai_agents,integrations}`, and `backend/core/{models,tenancy,permissions,exceptions,services}`.
- Current root-level `core/`, `apps/accounts/`, `apps/tenants/`, and `apps/common/` references are explicitly labeled as starter transition inputs, not target implementation boundaries.
- Infrastructure direction is documented as Cloudflare Pages, Render, Render PostgreSQL, Cloudflare R2/S3-compatible storage, and an open Django-Q or Celery+Redis worker choice.
- Auth planning now explicitly includes an HttpOnly/Secure refresh cookie, rotation, and reuse detection.

## Historical roadmap update status (2026-09-28; current task status is recorded above)

- V1-ROADMAP-UPDATE and V1-ENVIRONMENT-LOCK were documentation/roadmap work only. T3-02A through T3-04 are implemented. T3-05 onward, T3-05A (Staging Backend Foundation), F7-01A (Staging Frontend & Client Review Checkpoint), and deployments remain unimplemented; each requires its own confirmation. Environment model is locked as LOCAL → STAGING → PRODUCTION.
- Post-V1 work is gated until Phase 10 and the complete V1 Definition of Done are accepted.
- GitHub Actions run 36415017163 passed on repository HEAD before this documentation-only change. This historical CI result does not validate the current documentation diff.
- Historical local validation for the roadmap documentation update: repository validator PASS; validator tests 11 passed; application suite 120 passed; Django system check PASS; migration drift check PASS; `git diff --check` PASS. This does not describe the current T3-03 diff.
