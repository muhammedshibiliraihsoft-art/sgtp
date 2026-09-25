# Project State

## Status

- Phase: 0 — target product definition and starter alignment
- Current task: prepare for Phase 1 implementation after independent plan audit
- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Starter commit: `0a78d8fd32013c729c7f17dde8c218a8d8900c17` (`Initial commit`)
- Starter branch: `main`, with local documentation checkpoints ahead of `origin/main`; application source remains unchanged
- Target status: SGTP V1 is now explicitly defined in `docs/PRODUCT_DEFINITION.md`
- Starter foundation: exists in the cloned SGTP repository and remains unchanged.
- Phase 1 implementation: **not yet performed**.
- Phase 1 plan/readiness: independently audited, clear, and ready to begin when explicitly activated.
- Phase 1 activation: not active.
- Confirmation status: no phase or task is currently confirmed.
- Detailed phase playbooks: 01–10 present; planning only, no phase activated
- Later-phase decisions: tenant-context resolution and Related Person billing ownership remain unresolved and must be handled in their respective phases; they do not by themselves block Phase 1.

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

- User-to-tenant membership/ownership is not modeled: `User` has no tenant relation, while `Tenant.user_count` calls `user_set`.
- Tenant isolation is not enforced. The README references `TenantFilterMixin` and `apps.common.views.base_model_view`, but those files do not exist.
- Tenant-aware base model permits `tenant = NULL`, and no request/context policy establishes the active tenant.
- Tenant-context resolution mechanism is intentionally undecided; no header, URL path, subdomain, session, or alternative may be selected silently.
- Billing ownership for work belonging to a Related Person is intentionally undecided; billing must not infer primary-Client versus Related-Person ownership.
- JWT token blacklisting is configured in code, but `rest_framework_simplejwt.token_blacklist` is absent from `INSTALLED_APPS`.
- `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` are not configured despite production/CORS claims.
- Devcontainer sets `DEBUG` and `DATABASE_URL`, while settings read `DJANGO_DEBUG` and discrete `DB_*` variables; those paths do not align.
- Local dependencies are not installed in the current host, so `manage.py check` and tests could not run (`ModuleNotFoundError: django`).
- No domain/business modules beyond accounts and generic tenants exist.

## Recommended foundation changes before Phase 1

1. Translate the approved product definition into an entity/relationship and authorization design for suppliers, shops, users, and shop-scoped records.
2. Define the tenant membership model, active-shop context, and object-level isolation policy before adding business modules.
3. Align environment variables, database configuration, `DEBUG`, allowed hosts, CORS, and production security settings.
4. Add the required SimpleJWT blacklist app or remove blacklist behavior, based on the approved auth contract.
5. Establish the frontend foundation and backend service/API boundaries without changing the approved business hierarchy.
6. Establish storage, background job, audit, CI, monitoring, and documentation foundations.
7. Establish a dependency environment and run migrations, checks, linting, and tests before extending the starter.
8. Replace README claims for missing mixins/components with verified implementation or corrected documentation.

## Verification results

- Repository access: passed.
- Clone: passed.
- Starter Git status: clean.
- File inventory and source/configuration inspection: completed.
- Django check: not runnable because Django is not installed in the current host environment.
- Application tests: not run for the same dependency reason.

## Current root verification

- Repository root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- Documentation: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- `backend/` and `frontend/` now exist as empty layout placeholders only; no business modules were created.

## Phase playbook confirmation audit

- All ten phase implementation prompts use the mandatory phase-level activation plus task-level confirmation model.
- Phase confirmation activates scope only; it does not authorize all tasks.
- Each task requires a separate task brief and explicit `CONFIRM TASK <TASK-ID>` before implementation.
- After one task, the agent must validate, document, report, and stop; next-task and next-phase activation are never automatic.
- Phase playbooks 07–10 have now been added with task IDs, validation, handoff, rollback, Definition of Done, and Antigravity prompts.

## Planning-only status

- No phase is active.
- No task is confirmed.
- No application source, models, APIs, frontend screens, deployment, or infrastructure implementation was performed while creating the playbooks.

## Canonicalization audit

- The approved target Django structure is documented separately from the current starter paths: `backend/config/settings`, `backend/apps/{accounts,shops,clients,catalog,works,billing,reports,ai_agents,integrations}`, and `backend/core/{models,tenancy,permissions,exceptions,services}`.
- Current root-level `core/`, `apps/accounts/`, `apps/tenants/`, and `apps/common/` references are explicitly labeled as starter transition inputs, not target implementation boundaries.
- Infrastructure direction is documented as Cloudflare Pages, Render, Render PostgreSQL, Cloudflare R2/S3-compatible storage, and an open Django-Q or Celery+Redis worker choice.
- Auth planning now explicitly includes an HttpOnly/Secure refresh cookie, rotation, and reuse detection.
- Cookie-authenticated state-changing requests require an approved CSRF defense; HttpOnly/Secure cookies alone are insufficient.
