# Architecture

## Target product architecture

SGTP V1 is a supplier-centric, multi-shop business system. The supplier/main admin operates the supplier back office, which manages isolated shop workspaces. Each shop owns or accesses only its permitted clients, designs, measurements, materials, production work, billing, reports, and history.

```text
Supplier / Main Admin
        ↓
Supplier Back Office
        ↓
Isolated Shop Workspace(s)
        ↓
Client → Design → Measurement → Fabric/Material → Production Workflow
                                                   ↓
                                      Completion → Billing → Reports/History
```

The target production workflow is:

`Client Request → Design → Measurement → Fabric/Material → Cutting → Stitching → Check → Finishing → QC → Completed → Billing → Reports/History`

The final system is intended to have a React/Vite/Tailwind frontend, Django/DRF backend, PostgreSQL/Django ORM persistence, secure token authentication, tenant isolation, object-level permissions, service-layer business logic, persistent object storage, background jobs, audit logging, tests, CI, monitoring, and automatic API/documentation updates. AI and external integrations must remain isolated from core business workflows.

## Canonical target repository structure

The target implementation path is:

```text
backend/
├── config/settings/{base.py,dev.py,prod.py}
├── apps/{accounts,shops,clients,catalog,works,billing,reports,ai_agents,integrations}/
├── core/{models,tenancy,permissions,exceptions,services}/
└── manage.py
```

This is the approved target structure. The root-level `core/`, `apps/accounts/`, `apps/tenants/`, and `apps/common/` paths described below are current starter-repository paths only; they must not be mistaken for target module boundaries.

## Approved infrastructure direction

- Frontend: React + Vite + Tailwind, hosted on Cloudflare Pages for staging/production delivery.
- Backend: Django + DRF, hosted on Render.
- Database: Render PostgreSQL.
- Object storage: Cloudflare R2 or another approved S3-compatible private object store.
- Background jobs: Django-Q or Celery + Redis; the choice remains open until the reliability phase selects and documents one.
- Authentication: access token plus refresh token, with the refresh token handled through an HttpOnly/Secure cookie, rotation, and reuse detection; cookie-authenticated state-changing requests also require an approved CSRF protection strategy.

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

## Current versus target boundaries

- `core` owns global configuration and URL entry points.
- `accounts` owns authentication identity and user-facing auth endpoints.
- `tenants` owns organization records and tenant administration endpoints.
- `common` owns shared model abstractions.
- No service layer, domain modules, background worker, event bus, or external integration layer exists.
- Target modules for V1 are not yet implemented: supplier/back office, shop workspace, clients, related persons, designs, measurements, materials, production workflow, billing, reports/PDFs, storage, jobs, and monitoring.
- `backend/` and `frontend/` are currently empty placeholders; the existing Django code remains at the repository root under `core/` and `apps/`.
- Target boundaries are `accounts` for identity/auth, `shops` for supplier/shop/membership/workspace tenancy, `clients` for clients/related persons, `catalog` for designs/measurements/materials, `works` for orders and production workflow, `billing` for invoices/payments/accounts, `reports` for reports/history/PDFs, `ai_agents` for controlled AI services, `integrations` for external adapters/webhooks, and `core` for shared primitives only.

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
7. The starter is a generic foundation and does not yet implement the approved SGTP V1 business hierarchy or end-to-end workflow.
8. The target requires a frontend and supporting infrastructure that are absent from the starter.

## Recommended foundation changes

- Make the V1 architecture authoritative in repository documentation before coding.
- Select and document the tenant membership model and active-tenant resolution strategy.
- Implement tenant isolation at queryset and permission boundaries, with tests proving cross-tenant access is denied.
- Decide whether tenant-scoped foreign keys are mandatory and enforce that decision in models/serializers.
- Align settings with container environment variables and explicitly configure allowed hosts/CORS.
- Enable and test JWT refresh-token blacklist support if logout requires revocation.
- Add the missing shared view/mixin abstractions only if the approved architecture needs them.
- Design domain entities and relationships around the supplier → shop → client/work hierarchy before implementing modules.
- Make the complete production workflow a persisted state machine with transition authorization and audit history.
- Define a service layer so billing, reports, jobs, and integrations cannot bypass core business rules.
- Define secure object storage, asynchronous job boundaries, monitoring, CI, and end-to-end acceptance tests.

## Phase 1 readiness

Not ready. The target is now documented, but the starter lacks the business modules and several required security, tenancy, infrastructure, and frontend foundations.
