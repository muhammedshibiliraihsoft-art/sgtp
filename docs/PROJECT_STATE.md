# Project State

## Status

- Phase 1 and Phase 2 are complete.
- Phase 3 is ACTIVE; activation was explicitly confirmed with `CONFIRM PHASE 3`.
- Completed Phase 3 tasks: T3-01, T3-02, T3-02-REMEDIATION, T3-02A, and T3-03.
- Remaining tasks T3-04 onward are not started and remain individually gated.
- Latest implementation task: T3-03 — Tenant / Shop Request Context = COMPLETE / COMMITTED / PUSHED / CI GREEN. T3-03 was explicitly confirmed. T3-04 is NOT STARTED / NOT AUTHORIZED.
- Current application test discovery: 145 tests. The T3-03 commit passed GitHub Actions Project State Validation Run #19; its result covers the current pushed baseline.

- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Phase 1 corrective implementation was completed and published to `origin/main`.
- Current branch: `main`
- Target status: SGTP V1 is explicitly defined in `docs/PRODUCT_DEFINITION.md`
- Starter foundation: exists in the cloned SGTP repository.
- Phase 1 implementation: **Historical - Complete.**
- Confirmation status: T3-03 was explicitly confirmed and completed. T3-04 has not been confirmed and must not start without its own task plan and confirmation.
- Detailed phase playbooks: 01-10 present.
- Later-phase decisions: Tenant context is approved as URL-path based (`/shops/{shop_id}/...`), and Related Person billing is owned by the Primary Client.
- T3-05A (Staging Backend Foundation) and F7-01A (Staging Frontend & Client Review Checkpoint) remain planned only. T3-02A implemented the account/preference data and API foundation; frontend localization, RTL/LTR layout, and full Light/Dark/System UI remain Phase 7 work.
- T3-02A confirmed policy is now implemented: anonymous self-registration denied; Main Supplier Admin controls global account creation/phone lifecycle and Shop defaults; email and optional unique E.164 phone authenticate one UUID account; generated initial password is returned once/no-store and must be changed; email reset is single-use and revokes sessions; nullable locale and `system|light|dark` preferences and nullable Shop defaults persist.
- T3-02A verification: the pushed baseline CI passed in GitHub Actions run #17. T3-03 is committed and pushed; GitHub Actions run #19 passed for it.

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
- Full queryset/object isolation remains T3-04 scope. Global Shop visibility, Shop deletion semantics, Shop Admin settings authority, and currency-change policy remain unresolved and unchanged.
- Focused context/membership/permission suite: 76 passed; the dedicated Shop-context module contains 15 tests.
- Full application suite: 145 passed (144 warnings). Django check, migration drift check, OpenAPI schema validation, validator unit tests (14 passed), Black, Flake8, and `git diff --check` passed.
- Repository validator: PASS; Phase 3 is recorded as active with explicit activation in both current-state documents. It discovered 145 application tests.
- No database schema or dependency changes. T3-03 is committed and pushed; GitHub Actions Project State Validation Run #19 passed.

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
- The required end-to-end workflow is documented, but no production-domain modules for clients, designs, measurements, materials, production stages, billing, or reports exist yet.
- The target requires React/Vite/Tailwind, but the starter contains no frontend implementation; `frontend/` is only an empty placeholder.
- The target requires a service layer, object-level permissions, persistent object storage, background jobs, audit logging, CI, monitoring, and automatic documentation; the starter does not implement these as complete capabilities.
- T3-03 request-local active-Shop context is implemented; complete queryset/object isolation remains pending T3-04.

## Phase 3+ Missing or incomplete business logic

- Tenant-aware base model still permits `tenant = NULL`; T3-03 now establishes the active Shop per request, but T3-04 must apply the trusted context to every Shop-owned queryset/object.
- Tenant-context resolution is implemented at `/api/v1/shops/{shop_id}/...`; T3-04 full isolation remains pending.
- Billing ownership for work belonging to a Related Person is approved as Primary Client ownership and must be enforced in Phase 5.
- No domain/business modules beyond accounts, tenants, and membership exist.

### PRE-P3-02 result

- The V1 Supplier / Shop / External Supplier business meaning is now explicit across the governing documentation.
- Phase 3 task outcomes: T3-01, T3-02, T3-02-REMEDIATION, T3-02A, and T3-03 are complete. T3-04 and subsequent tasks remain individually gated.

### T3-02 remediation result

- User API access is restricted so ordinary authenticated users cannot enumerate, modify, or delete other users; self-profile updates remain available and account activation state is read-only through the serializer.
- Shop write actions and activation/deactivation use the existing `ShopRolePolicy` Main Supplier authority instead of Django `is_staff` alone.
- Generic membership updates cannot change `is_active`; lifecycle actions remain authoritative.
- Authentication throttling is explicitly wired to the `auth` scope and verified with a non-mocked repeated-login test.
- Duplicate CORS test method names were corrected so all intended tests are collected.
- CI retains project-state validation and is configured to run the application suite, Django system checks, and migration checks with PostgreSQL. The GitHub Actions run for the reviewed baseline successfully passed all checks, including the application suite, Django system checks, and PostgreSQL integration. Remote CI confirmation is fully green and the PostgreSQL connectivity issue is resolved.
- Production compose now propagates `DJANGO_CORS_ALLOWED_ORIGINS` without inventing a deployment origin.
- No migrations were required or changed.
- Remaining unresolved decisions include ordinary-user Shop read visibility, Shop DELETE semantics, Shop Admin scoped settings authority, currency changes after financial history, and the other later-phase items in `docs/DECISIONS.md`. Global User administration/public signup, phone rules, credential lifecycle, and current Main Supplier Shop-settings authority are now confirmed.

### Phase 3+ Deferred Implementations

- Actual business tenant isolation is not fully enforced; T3-04 queryset/object enforcement is pending.
- Tenant-aware base model permits `tenant = NULL`; T3-03 establishes trusted request context, but does not change model nullability or scope business queries.
- Tenant-context resolution is implemented as URL-path based (`/api/v1/shops/{shop_id}/...`).
- Billing ownership for work belonging to a Related Person is approved as Primary Client ownership and must be enforced in Phase 5.
- No domain/business modules beyond accounts, tenants, and membership exist.

## Historical Phase 1 Verification results

- Repository access: passed.
- Clone: passed.
- Phase 1 corrective changes were committed and published to `origin/main`.
- File inventory and source/configuration inspection: completed.
- Django check: passes without issues.
- Application tests: full project suite passes .

## Current root verification

- Repository root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- Documentation: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- `backend/` contains settings and shared model foundation code; `frontend/` is a layout placeholder. No client, catalog, works, billing, or reports business modules exist yet.

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

- V1-ROADMAP-UPDATE and V1-ENVIRONMENT-LOCK were documentation/roadmap work only. T3-02A and T3-03 are implemented. T3-04 onward, T3-05A (Staging Backend Foundation), F7-01A (Staging Frontend & Client Review Checkpoint), and deployments remain unimplemented; each requires its own confirmation. Environment model is locked as LOCAL → STAGING → PRODUCTION.
- Post-V1 work is gated until Phase 10 and the complete V1 Definition of Done are accepted.
- GitHub Actions run 36415017163 passed on repository HEAD before this documentation-only change. This historical CI result does not validate the current documentation diff.
- Historical local validation for the roadmap documentation update: repository validator PASS; validator tests 11 passed; application suite 120 passed; Django system check PASS; migration drift check PASS; `git diff --check` PASS. This does not describe the current T3-03 diff.
