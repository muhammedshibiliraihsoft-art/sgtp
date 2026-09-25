# Architecture

## Verified starter architecture

The cloned starter is a conventional Django monolith:

```text
core.settings -> installed Django/DRF/local apps
core.urls     -> admin, browsable API, auth API, tenant API, schema/docs
apps.accounts -> User model, JWT auth, profile endpoints, admin, tests
apps.tenants  -> Tenant model, tenant CRUD/actions, admin, tests
apps.common   -> abstract UUID/audit/soft-delete base models
PostgreSQL    -> configured default database
Docker        -> development container and production web/db services
```

## Project and application boundaries

- `core` owns global configuration and URL entry points.
- `accounts` owns authentication identity and user-facing auth endpoints.
- `tenants` owns organization records and tenant administration endpoints.
- `common` owns shared model abstractions.
- No service layer, domain modules, background worker, event bus, or external integration layer exists.

## Authentication

- `AUTH_USER_MODEL = accounts.User`.
- Email is the login identifier.
- DRF uses JWT authentication first and session authentication second.
- Login and refresh routes use SimpleJWT; logout attempts to blacklist refresh tokens.
- The blacklist application is not installed, so logout behavior requires verification/fix before being considered complete.

## Data architecture

- `BaseModel` provides UUID IDs, created/updated timestamps, created/updated user references, and `SOFT_DELETE_CASCADE`.
- `BaseModelWithTenant` adds an optional foreign key to `tenants.Tenant`.
- `Tenant` is an organization record with profile/contact/address fields and a user limit.
- `User` has no tenant foreign key or membership model. Consequently, tenant ownership and isolation are not implemented.

## API surface

- `/admin/`
- `/api/v1/auth/users/`, `/login/`, `/logout/`, `/token/refresh/`
- `/api/v1/tenants/` and tenant actions `activate`, `deactivate`, `stats`
- `/api/schema/` and `/api/docs/`
- `/` serves a static API test/reference page.

## Infrastructure

- PostgreSQL 15 in Docker Compose.
- Python 3.13 slim production/development images.
- Production startup waits for PostgreSQL, runs migrations, collects static files, and starts Gunicorn.
- WhiteNoise serves collected static files.
- VS Code Dev Container installs development dependencies and applies migrations.

## Architecture gaps and conflicts

1. Tenant membership is absent. `Tenant.user_count` assumes a reverse `user_set`, but `User` does not reference `Tenant`.
2. Tenant isolation is absent. No middleware, permission, queryset policy, or existing `TenantFilterMixin` is present.
3. The tenant field is nullable, so tenant-scoped records can be unscoped by default.
4. The README references missing `apps.common.views.base_model_view` and `apps.tenants.mixins` components.
5. Settings and infrastructure disagree: settings read `DJANGO_DEBUG` and `DB_*`, while devcontainer configuration supplies `DEBUG` and `DATABASE_URL`.
6. Production settings do not define `ALLOWED_HOSTS` or a CORS allowlist.
7. The stated architecture is generic starter architecture, not yet verified against SGTP V1 because V1 requirements are absent from `AGENTS.md`.

## Recommended foundation changes

- Make the V1 architecture authoritative in repository documentation before coding.
- Select and document the tenant membership model and active-tenant resolution strategy.
- Implement tenant isolation at queryset and permission boundaries, with tests proving cross-tenant access is denied.
- Decide whether tenant-scoped foreign keys are mandatory and enforce that decision in models/serializers.
- Align settings with container environment variables and explicitly configure allowed hosts/CORS.
- Enable and test JWT refresh-token blacklist support if logout requires revocation.
- Add the missing shared view/mixin abstractions only if the approved architecture needs them.

## Phase 1 readiness

Not ready. The repository is cloned and understood at starter level, but the authoritative V1 requirements are not present and several security/data-boundary foundations are incomplete.
