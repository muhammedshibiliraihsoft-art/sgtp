# Handoff

## Current phase

Phase 0 — SGTP target product definition and starter alignment. No implementation has started.

## Current task

Task F1-04 (PostgreSQL and migration strategy) is completed. We validated that the database configuration correctly applies migrations on a fresh PostgreSQL instance, tests run cleanly against a separate test database, and the forward-only migration policy is documented in `docs/DATABASE.md`. Waiting for confirmation of task F1-05 (Authentication foundation and simplejwt).

## Repository and workspace

- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- `docs/`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- HEAD: `0a78d8f` (`Initial commit`)
- Branch: `main` tracking `origin/main`
- Starter source files preserved.
- Existing SGTP `.git` metadata and history preserved.
- No second repository initialized and no push performed.

## Target final product

SGTP is now defined as the Supplier-Centric Garment & Tailor Platform, with Tailor Management as the core V1 module. The hierarchy is Supplier/Main Admin → Supplier Back Office → isolated Shop workspaces → Clients, Designs, Measurements, Fabric/Materials, Work, Billing, and Reports.

The required persisted flow is:

`Client Request → Design → Measurement → Fabric/Material → Cutting → Stitching → Check → Finishing → QC → Completed → Billing → Reports/History`

The full product definition and Definition of Done are in `docs/PRODUCT_DEFINITION.md`.

## Inspection summary

The starter is a Django 5.1.4 / DRF 3.15.2 PostgreSQL project with Docker, devcontainer, JWT authentication, a custom email user, tenants, UUID/audit/soft-delete base models, OpenAPI/Swagger, and tests. It contains `core/`, `apps/accounts/`, `apps/tenants/`, `apps/common/`, templates, dependency/tooling files, Docker infrastructure, and editor configuration.

## Reusable

- Django project wiring and environment-loading pattern.
- Custom user model, user manager, admin, JWT endpoints, serializers, and initial tests.
- Tenant model/admin/API/migrations/tests as a starting point only.
- UUID, timestamps, audit fields, and soft-delete base model.
- PostgreSQL, Docker, devcontainer, Gunicorn, WhiteNoise, Makefile, and tooling setup.

## Missing or conflicting items

- `AGENTS.md` and `docs/PRODUCT_DEFINITION.md` now contain the approved V1 target; the starter remains incomplete against that target.
- Tenant membership and isolation are incomplete: users are not related to tenants; `user_set` is not backed by a relation; no tenant filtering mixin exists despite README references.
- `BaseModelWithTenant.tenant` is nullable and no active-tenant/request authorization mechanism exists.
- JWT logout calls `blacklist()` without installing the SimpleJWT blacklist app.
- Settings do not define `ALLOWED_HOSTS` or CORS policy; container environment variable names do not match settings expectations.
- The host lacks installed Django/pytest/psycopg dependencies, so runtime checks remain pending.
- The starter is not yet the target product: supplier back office, isolated shop workspaces, clients, related persons, designs, measurements, materials, production stages, billing, reports/PDFs, frontend, storage, jobs, audit, CI, monitoring, and end-to-end validation are not implemented.
- The target requires React/Vite/Tailwind, but the starter has only an empty `frontend/` placeholder.
- The current generic tenant foundation does not yet provide the shop membership, active-shop context, tenant isolation, or object-level permissions required by the target.
- Tenant context is approved as URL-path based (`/shops/{shop_id}/...`) and must be implemented/tested in T3-03.
- Related Person billing ownership is approved as Primary Client ownership and must be implemented/tested in R5-01.
- Cookie-authenticated state-changing requests require an approved CSRF strategy; HttpOnly/Secure cookies alone are not sufficient.

## Tests and checks

- Repository access: passed with `git ls-remote`.
- Clone: passed.
- Starter Git status: clean.
- `python sgtp/manage.py check`: blocked by `ModuleNotFoundError: No module named 'django'`.
- Tests: not run because dependencies are not installed.

## Reorganization verification

- `git rev-parse --show-toplevel` returns `C:/Users/Admin/Documents/ChatGPT/django 2/sgtp`.
- `git remote -v` still points to `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`.
- `AGENTS.md` and `docs/` exist inside the SGTP root.
- The starter source remains preserved; documentation is maintained in the SGTP repository.
- `backend/` and `frontend/` exist as empty layout placeholders only; no business modules were created.

## Target contradiction record

- Previous planning treated the repository as an uninitialized generic Django foundation and deferred V1 requirements.
- The target is now explicit and broader: an integrated supplier/shop Tailor Management product with an end-to-end production-to-billing workflow and operational capabilities.
- The development plan has been realigned to this target, but the starter implementation remains unchanged. Phase 1 foundation gaps belong to Phase 1; later-phase decisions remain scoped to their respective phases.

## Decisions and constraints

- Do not create a replacement Django project.
- Do not create new business modules.
- Do not modify business architecture during this inspection.
- Do not push to GitHub.
- Keep all work local.
- Preserve the approved supplier → back office → isolated shop hierarchy and V1 workflow.
- Treat `docs/PRODUCT_DEFINITION.md` as the target product reference.
- Phase confirmation activates only the named phase; it does not authorize all tasks in that phase.
- Every task requires a separate `CONFIRM TASK <TASK-ID>` after the task brief is presented.
- After one task is validated and documented, stop. Do not start the next task or phase automatically.

## Phase playbook audit status

- Confirmation-flow wording was aligned across all ten phase playbooks, `AGENTS.md`, `docs/DEVELOPMENT_PLAN.md`, and this handoff.
- The ten phase playbooks exist and require separate task confirmation after phase activation.
- No application source, architecture, scope, task ID, dependency, or implementation-order changes were made.

## Phase playbook completion

- `docs/phases/07_FRONTEND.md` created with tasks F7-01 through F7-05.
- `docs/phases/08_TESTING_HARDENING.md` created with tasks H8-01 through H8-04.
- `docs/phases/09_STAGING.md` created with tasks S9-01 through S9-04.
- `docs/phases/10_PRODUCTION.md` created with tasks P10-01 through P10-04.
- All ten playbooks use phase activation followed by separate task confirmation, validation, documentation, report, and stop boundaries.

## Canonicalization audit status

- Target implementation paths are explicit in `docs/ARCHITECTURE.md` and the affected phase playbooks.
- Current starter paths remain documented only as transition inputs.
- Domain responsibilities map to `accounts`, `shops`, `clients`, `catalog`, `works`, `billing`, `reports`, `ai_agents`, `integrations`, and shared `core` primitives.
- Deployment phases explicitly use Cloudflare Pages, Render, Render PostgreSQL, and Cloudflare R2/S3-compatible storage; worker selection remains Django-Q or Celery + Redis.
- Refresh-token planning explicitly requires an HttpOnly/Secure cookie, rotation, and reuse detection.

## Phase 1 status

Phase 1 implementation has started. Tasks F1-01 through F1-04 are complete. We established the virtual environment, split settings into base/dev/test/prod, refactored the User model away from soft-deletes, established base models, and documented the PostgreSQL forward-only migration strategy after verifying clean execution on a fresh database. `manage.py check` and tests pass cleanly. No business logic was modified.

## Recommended next action

Next, await explicit confirmation `CONFIRM TASK F1-05` to proceed with Authentication foundation and simplejwt.
