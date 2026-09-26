# Project State

## Status

- Phase 1 — corrective work complete
- Current task: Phase 1 is complete
- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Current HEAD: cec6340a (pre-correction committed state)
- Current branch: `main` with Phase 1 application and documentation modifications
- Target status: SGTP V1 is now explicitly defined in `docs/PRODUCT_DEFINITION.md`
- Starter foundation: exists in the cloned SGTP repository.
- Phase 1 implementation: **Complete.**
- Confirmation status: Phase 1 tasks completed.
- Detailed phase playbooks: 01–10 present; planning only, no phase activated
- Later-phase decisions: tenant context is approved as URL-path based (`/shops/{shop_id}/...`), Related Person billing is owned by the Primary Client, and CSRF mechanism selection/validation remains a Phase 2 task.

## Repository verification

- `git ls-remote` succeeded against the corrected URL.
- The existing cloned SGTP repository is now the project root.
- `AGENTS.md` and `docs/` were moved into the SGTP repository without overwriting starter files.
- The SGTP repository's existing `.git` metadata and history were preserved; no second repository was initialized.
- No GitHub push was performed.

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
- Existing tenant support is insufficient for isolated shop workspaces: user membership, active-shop context, queryset isolation, and object-level authorization are missing.

## Missing or incomplete foundation

- User-to-tenant membership/ownership is not modeled: `User` has no tenant relation. `Tenant.user_count` intentionally returns a placeholder 0 for Phase 1.
- Tenant isolation is not enforced. Stale mixin references were removed from the README.
- Tenant-aware base model permits `tenant = NULL`, and no request/context policy establishes the active tenant.
- Tenant-context resolution is approved as URL-path based (`/shops/{shop_id}/...`) and must be enforced in Phase 3.
- Billing ownership for work belonging to a Related Person is approved as Primary Client ownership and must be enforced in Phase 5.
- No domain/business modules beyond accounts and generic tenants exist.

### Phase 2/3 Deferred Implementations

- User-to-tenant membership is not modeled: `User` has no tenant relation, and tenant isolation is not enforced.
- Tenant-aware base model permits `tenant = NULL`, and no request/context policy establishes the active tenant.
- Tenant-context resolution is approved as URL-path based (`/shops/{shop_id}/...`) and must be enforced in Phase 3.
- Billing ownership for work belonging to a Related Person is approved as Primary Client ownership and must be enforced in Phase 5.
- No domain/business modules beyond accounts and generic tenants exist.
- Cookie-authenticated state-changing requests require an approved CSRF defense. HttpOnly/Secure cookies alone are insufficient. Rotation and reuse detection are pending.

## Verification results

- Repository access: passed.
- Clone: passed.
- Working tree: contains uncommitted Phase-1 corrective changes.
- File inventory and source/configuration inspection: completed.
- Django check: passes without issues.
- Application tests: full project suite passes (21 tests).

## Current root verification

- Repository root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- Documentation: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- `backend/` and `frontend/` exist as layout placeholders only; no business modules were created yet.

## Phase playbook confirmation audit

- All ten phase implementation prompts use the mandatory phase-level activation plus task-level confirmation model.
- Phase confirmation activates scope only; it does not authorize all tasks.
- Each task requires a separate task brief and explicit `CONFIRM TASK <TASK-ID>` before implementation.
- After one task, the agent must validate, document, report, and stop; next-task and next-phase activation are never automatic.
- Phase playbooks 07-10 have now been added with task IDs, validation, handoff, rollback, Definition of Done, and Antigravity prompts.

## Implementation Status (Phase 1 Complete)

- Phase 1 is complete.
- F1-01 through F1-05 are all complete.
- Python virtual environment `.venv` created, and dependency baseline established. `manage.py check` passed.
- Lint tools can run, but existing starter lint violations remain. `pytest` is passing against the new devcontainer PostgreSQL database with all project tests collected.
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
