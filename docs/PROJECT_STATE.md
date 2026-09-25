# Project State

## Status

- Phase: 0 — starter verification and inspection complete
- Current task: verify and inspect the original SGTP starter before development
- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Starter commit: `0a78d8fd32013c729c7f17dde8c218a8d8900c17` (`Initial commit`)
- Starter branch: `main`, clean and tracking `origin/main`
- Phase 1: **not yet safe to begin** until the V1 requirements and target architecture are made explicit and the foundation gaps below are resolved or accepted

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

## Missing or incomplete foundation

- No V1 requirements or SGTP-specific architecture are present in the outer `AGENTS.md`; it currently contains only continuity and engineering rules. A trustworthy requirements comparison is therefore not possible yet.
- User-to-tenant membership/ownership is not modeled: `User` has no tenant relation, while `Tenant.user_count` calls `user_set`.
- Tenant isolation is not enforced. The README references `TenantFilterMixin` and `apps.common.views.base_model_view`, but those files do not exist.
- Tenant-aware base model permits `tenant = NULL`, and no request/context policy establishes the active tenant.
- JWT token blacklisting is configured in code, but `rest_framework_simplejwt.token_blacklist` is absent from `INSTALLED_APPS`.
- `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` are not configured despite production/CORS claims.
- Devcontainer sets `DEBUG` and `DATABASE_URL`, while settings read `DJANGO_DEBUG` and discrete `DB_*` variables; those paths do not align.
- Local dependencies are not installed in the current host, so `manage.py check` and tests could not run (`ModuleNotFoundError: django`).
- No domain/business modules beyond accounts and generic tenants exist.

## Recommended foundation changes before Phase 1

1. Obtain or add the authoritative SGTP V1 requirements and architecture to repository documentation, then reconcile them with this inspection.
2. Define the tenant membership model and isolation policy before adding domain modules.
3. Align environment variable names, database configuration, `DEBUG`, allowed hosts, CORS, and production security settings.
4. Add the required SimpleJWT blacklist app or remove blacklist behavior, based on the approved auth contract.
5. Establish a dependency environment and run migrations, checks, linting, and tests before extending the starter.
6. Replace README claims for missing mixins/components with verified implementation or corrected documentation.

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
