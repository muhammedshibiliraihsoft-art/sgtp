# Architecture

## Target product architecture

SGTP V1 has exactly one top-level Supplier / Main Admin. That operator runs the Supplier Back Office and manages multiple isolated Shop workspaces. V1 is not a multi-supplier SaaS platform. Each Shop owns or accesses only its permitted clients, designs, measurements, materials, production work, billing, reports, history, and External Supplier records.

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

## V1 Supplier / Shop / External Supplier Model

The following business model is locked for V1:

- There is exactly one top-level **Supplier / Main Admin**.
- The approved hierarchy is **one Main Supplier / Main Admin → Supplier Back Office → multiple Shops**.
- **Shop** is the actual business workspace and the tenant/isolation boundary.
- An **External Supplier** is a normal business record owned by exactly one Shop. It is distinct from the Main Supplier / Main Admin.
- External Suppliers are not users, tenants, members, roles, administrators, API accounts, or authentication participants. They do not log in or receive a dashboard.
- External Supplier records are not global or shared between Shops. Shop A and Shop B may each have separate records with the same real-world supplier name.
- Backend enforcement must prevent cross-Shop discovery or access through direct IDs, list/detail endpoints, search, filters, ordering, pagination, counts, aggregates, autocomplete, nested relations, foreign-key traversal, or manipulated URL paths.
- Main Supplier cross-Shop visibility is an explicitly authorized operational capability; it does not make Shop data globally visible to Shop users.
- The starter `Tenant` model is the V1 technical implementation for `Shop`. T3-01 confirmed it is safe to map Tenant = Shop structurally, while a new `Main Supplier` singleton model enforces exactly one top-level platform owner.

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
- `tenants` contains the retained `Tenant` model mapped to the V1 Shop, the singleton Main Supplier, membership, policy and administration endpoints.
- `common` owns shared model abstractions.
- No service layer, domain modules, background worker, event bus, or external integration layer exists.
- Target modules for V1 are not yet implemented: supplier/back office, shop workspace, clients, related persons, designs, measurements, materials, production workflow, billing, reports/PDFs, storage, jobs, and monitoring.
- `backend/` contains settings and shared model foundation code; `frontend/` is an empty placeholder. Django project wiring and apps remain at the repository root under `core/` and `apps/`.
- Target boundaries are `accounts` for identity/auth, `shops` for supplier/shop/membership/workspace tenancy, `clients` for clients/related persons, `catalog` for designs/measurements/materials, `works` for orders and production workflow, `billing` for invoices/payments/accounts, `reports` for reports/history/PDFs, `ai_agents` for controlled AI services, `integrations` for external adapters/webhooks, and `core` for shared primitives only.

## Authentication

- `AUTH_USER_MODEL = accounts.User`.
- Email is the login identifier.
- Base DRF configuration uses JWT authentication; development settings also enable session authentication and the browsable API.
- Login and refresh routes use SimpleJWT.
- The JWT blacklist application is installed and configured.
- Access token is returned in JSON.
- Refresh token is stored in an HttpOnly cookie.
- Refresh cookie uses SameSite=Lax.
- Refresh cookie Secure flag is environment-specific.
- Django CSRF protection is required for refresh/logout.
- csrftoken is issued explicitly at login.
- Frontend sends X-CSRFToken for cookie-authenticated refresh/logout.
- Refresh tokens rotate.
- Old rotated refresh tokens are blacklisted.
- Reuse of a blacklisted rotated token is rejected.
- Logout blacklists the current refresh token and clears both refresh and csrftoken cookies.
- No custom token-family revocation architecture is used in B2-02.

## Permissions and Scoping

- Object-level permission primitives are established: `IsOwner` (verifies ownership), `IsTenantMember` (Phase 3 deny-by-default contract), and `DenyAll` (explicit denial).
- Reusable tenant queryset scoping is provided by `TenantScopedMixin`, which enforces the `/shops/{shop_id}/...` path contract by filtering querysets and preventing cross-tenant IDOR access.
- Actual User-Shop membership logic is modeled via `TenantMember` and `ShopRolePolicy`. Shop write authority uses the existing Main Supplier policy, while business tenant isolation context implementation remains pending for Phase 3 (T3-03, T3-04).

## API Security and Reliability

- Centralized custom exception handling enforces a predictable `{"errors": ...}` envelope for all API errors.
- Unhandled 500 exceptions are trapped and returned as a generic dictionary to prevent leaking stack traces or sensitive internal details.
- Scoped authentication throttling (`AuthRateThrottle`) protects login, refresh, and logout endpoints from brute-force attacks.
- An environment-driven CORS allowlist strictly controls cross-origin access.
- Credentialed CORS is enabled, providing compatibility with the existing B2-02 `HttpOnly` token-refresh and CSRF cookie flow.
- A lightweight `/api/health/live/` probe returns unconditionally.
- A `/api/health/ready/` probe verifies database connectivity and returns 503 on dependency failure.

## Data architecture

- `BaseModel` provides UUID IDs, created/updated timestamps, created/updated user references, and `SOFT_DELETE_CASCADE`.
- `BaseModelWithTenant` adds an optional foreign key to the legacy `tenants.Tenant` input.
- `Tenant` is the current technical representation of the approved Shop entity, with a Main Supplier foreign key and profile/contact/address fields. `TenantMember` links Users to Shops; T3-03 request context and end-to-end isolation remain pending.
- `User` has no tenant foreign key directly. Instead, TenantMember links User and Tenant.  The approved target tenant-context mechanism is URL-path based: `/shops/{shop_id}/...`.
- The target Shop boundary and External Supplier ownership rules are defined above; they are not implemented by the current starter Tenant CRUD/API.

## API surface

- `/admin/`
- `/api/v1/auth/users/`, `/login/`, `/logout/`, `/token/refresh/`
- `/api/v1/tenants/` and tenant actions `activate`, `deactivate`, `stats`
- User API ordinary-user access is restricted to the authenticated user's own record; self-profile activation state is read-only.
- Target shop-scoped API paths use `/shops/{shop_id}/...` for tenant context.
- `/api/schema/` and `/api/docs/`
- `/` serves a static API test/reference page.

## Infrastructure

- PostgreSQL 15 in Docker Compose.
- Python 3.13 slim production/development images.
- Production startup waits for PostgreSQL, runs migrations, collects static files, and starts Gunicorn.
- WhiteNoise serves collected static files.
- VS Code Dev Container installs development dependencies and applies migrations.

## Architecture gaps and conflicts

1. `Tenant.user_count` counts ACTIVE and INACTIVE memberships via the `memberships` reverse relation.
2. Business tenant isolation (context, URL resolution, and cross-module scoped querysets) remains pending for Phase 3 (T3-03, T3-04), although the membership foundation and base `TenantScopedMixin` were introduced.
3. The tenant field is nullable, so tenant-scoped records can be unscoped by default.
4. The README references missing `apps.common.views.base_model_view` and `apps.tenants.mixins` components.
5. Local settings use `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` and `DB_*`; verify each deployment environment supplies those documented names.
6. JWT blacklist is installed/configured; runtime refresh rotation and reuse behavior is covered by authentication lifecycle tests, while deployment-specific database behavior still requires CI/runtime verification.
7. The foundation includes the single Supplier, Tenant-as-Shop mapping and membership/role policy, but does not yet implement External Supplier records, URL-path context, complete business-record isolation, or the end-to-end tailoring workflow.
8. The target React/Vite/Tailwind frontend is absent; persistent object storage, background workers, monitoring and complete release operations are also pending.

## Recommended foundation changes

- Make the V1 architecture authoritative in repository documentation before coding.
- T3-01 selected and implemented the Tenant-as-Shop mapping and singleton Supplier; preserve that approved mapping in subsequent migrations and APIs.
- Implement tenant isolation at queryset and permission boundaries, with tests proving cross-tenant access is denied.
- Decide whether tenant-scoped foreign keys are mandatory and enforce that decision in models/serializers.
- Align settings with container environment variables and explicitly configure allowed hosts/CORS.
- Ensure all JWT revocation checks are tested explicitly.
- Add the missing shared view/mixin abstractions only if the approved architecture needs them.
- Design domain entities and relationships around the supplier → shop → client/work hierarchy before implementing modules.
- Make the complete production workflow a persisted state machine with transition authorization and audit history.
- Define a service layer so billing, reports, jobs, and integrations cannot bypass core business rules.
- Define secure object storage, asynchronous job boundaries, monitoring, CI, and end-to-end acceptance tests.

## Phase 1 status and current V1 readiness

Phase 1 foundation implementation is complete. SGTP V1 is not ready for production: business modules and end-to-end workflows remain unimplemented, and Phase 3 URL-path Shop context/isolation is pending T3-03. T3-02 remediation closure changes are local and verified; confirmation from a GitHub Actions run remains pending.

## Membership Lifecycle and Rules

### State Transitions
The Shop Membership lifecycle follows these strict rules:

- **ACTIVE** -> Deactivate -> **INACTIVE**
- **INACTIVE** -> Reactivate -> **ACTIVE**
- **INACTIVE** -> Remove -> **REMOVED** (Soft Delete)
- **REMOVED** -> Undo (within 5 seconds) -> **Previous State**

*Note: There is NO direct ACTIVE -> REMOVED transition. Memberships must be deactivated before they can be removed.*

### Max Users Logic
The max_users limit is configured per-Shop (not hard-coded).
- **ACTIVE** and **INACTIVE** memberships both consume a max_users slot.
- **REMOVED** (soft-deleted) memberships do NOT consume a slot.
