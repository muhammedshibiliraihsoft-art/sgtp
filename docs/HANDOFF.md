# Handoff

## Current phase

Phase 0 — SGTP starter verification and inspection complete. No implementation has started.

## Current task

Make the existing cloned SGTP repository the project root without creating a replacement or nested repository, then stop before Phase 1.

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

## Inspection summary

The starter is a Django 5.1.4 / DRF 3.15.2 PostgreSQL project with Docker, devcontainer, JWT authentication, a custom email user, tenants, UUID/audit/soft-delete base models, OpenAPI/Swagger, and tests. It contains `core/`, `apps/accounts/`, `apps/tenants/`, `apps/common/`, templates, dependency/tooling files, Docker infrastructure, and editor configuration.

## Reusable

- Django project wiring and environment-loading pattern.
- Custom user model, user manager, admin, JWT endpoints, serializers, and initial tests.
- Tenant model/admin/API/migrations/tests as a starting point only.
- UUID, timestamps, audit fields, and soft-delete base model.
- PostgreSQL, Docker, devcontainer, Gunicorn, WhiteNoise, Makefile, and tooling setup.

## Missing or conflicting items

- `AGENTS.md` contains continuity rules but no V1 requirements or target SGTP architecture, so the requested requirements comparison is currently limited to the documented starter intent and cannot be treated as final.
- Tenant membership and isolation are incomplete: users are not related to tenants; `user_set` is not backed by a relation; no tenant filtering mixin exists despite README references.
- `BaseModelWithTenant.tenant` is nullable and no active-tenant/request authorization mechanism exists.
- JWT logout calls `blacklist()` without installing the SimpleJWT blacklist app.
- Settings do not define `ALLOWED_HOSTS` or CORS policy; container environment variable names do not match settings expectations.
- The host lacks installed Django/pytest/psycopg dependencies, so runtime checks remain pending.

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
- The starter repository remains clean; the moved continuity files appear as local uncommitted additions in the SGTP repository.
- `backend/` and `frontend/` exist as empty layout placeholders only; no business modules were created.

## Decisions and constraints

- Do not create a replacement Django project.
- Do not create new business modules.
- Do not modify business architecture during this inspection.
- Do not push to GitHub.
- Keep all work local.

## Phase 1 decision

Phase 1 should **not begin yet**. First add or locate the authoritative V1 requirements/architecture, resolve the tenant/auth/configuration foundation decisions, install dependencies in an isolated environment, and run the starter checks.

## Recommended next action

Provide the V1 requirements and target architecture in repository documentation or `AGENTS.md`. Then review the proposed foundation changes with the actual requirements before making code changes.
