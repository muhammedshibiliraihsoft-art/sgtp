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
- T3-02A authentication accepts the compatible `email` field or an `identifier` containing email/E.164 phone; both resolve to the same UUID User and password-authentication path. Anonymous account creation is denied; Main Supplier Admin may create accounts and manage login phones.
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
- T3-02A adds `auth_version` to access/refresh tokens and increments it on password change/reset. Credential changes also blacklist outstanding refresh tokens; no custom token-family architecture is introduced.

### Implemented V1 identity and preferences (Phase 3 T3-02A)

- Preserve the User UUID primary key and required unique email. Add country-aware phone normalization to E.164 without fabricating values for existing users; login may use email or phone through one deterministic authentication path.
- Persist nullable User preferred locale and `system|light|dark` appearance, defaulting appearance to `system`; locale selection is `User preference → authorized Shop default → English`.
- Shop default locale/timezone/currency are configuration only and must be resolved only after authorization. None of these preferences or settings may determine role, membership, access, or Shop selection.
- Public self-registration is prohibited; Main Supplier Admin is the current authority for global User creation/management. Email is required, phone is optional, and a registered unique E.164 User phone or email authenticates the same UUID account. Phone add/change/remove follows authorized account management; no V1 phone verification is required.
- Generated initial passwords must be cryptographically random, hash-only at rest, never logged or repeatedly exposed, and changed at first login. Recovery is email-based with secure, expiring, single-use behavior; password change/reset revokes refresh-token sessions.
- Shop timezone/currency are explicit and are never inferred; they may remain unset until configured. Main Supplier Admin manages Shop-level settings in the current foundation. Shop Admin settings authority is not granted by T3-02A.
- Generated account credentials are one-time response data with `Cache-Control: no-store`; first-login password change gates normal authenticated API operations. Password recovery is generic to the caller and uses expiring single-use Django reset tokens delivered by configured email. Plaintext passwords/reset tokens are not written to application storage or audit records.
- Shop default settings are serialized only on Main Supplier Admin reads/writes. Existing broad authenticated Shop reads retain their previous scope but omit the new settings fields; this does not implement T3-03 context or change Shop visibility policy.

## Planned cross-cutting V1 presentation and operations

- Supported UI locales are English (`en`), Arabic Kuwait (`ar-KW`), Bangla (`bn`) and Urdu (`ur`); Arabic/Urdu are RTL, English/Bangla LTR, with explicit mixed-direction handling. Preserve Unicode and canonical source text.
- Theme is Light/Dark/System, persisted per User; semantic tokens and system preference may change presentation only. No theme-specific business logic or dual component trees.
- Work priority is Normal/Urgent/Very Urgent. Upcoming/due-soon/today/overdue are derived date indicators, not workflow states; threshold and date cutoff remain business decisions.
- V1 observability includes approved error tracking, environment tags, request correlation, failed-job visibility, critical alerts and secret-safe logs. Audit captures actor/Shop/action/object/safe change/timestamp/correlation, never credentials or tokens.
- Environment lifecycle is LOCAL → STAGING → PRODUCTION. Staging is isolated, demo-data-only, visibly non-production and requires browser verification of cookie/CSRF/CORS at `staging.birky.com` / `api-staging.birky.com`. Phase 9 reuses the same Staging environment for formal release-candidate validation. Phase 10 remains the sole Production gate. Details: `docs/ENVIRONMENTS.md`.
- No Post-V1 work begins before Phase 10 and full V1 acceptance; see `docs/POST_V1_ROADMAP.md` for deferred scope and the constrained enhancement lane.

## Permissions and Scoping

- Object-level permission primitives include `IsOwner`, `IsTenantMember`, and `DenyAll`. `IsTenantMember` now requires the trusted T3-03 request context for endpoint-level Shop entry; complete object authorization remains T3-04 scope.
- `TenantScopedMixin` is legacy URL-based queryset filtering only. A raw `shop_id` filter is not authorization and does not prove cross-tenant IDOR safety; T3-04 must consume the trusted context.
- Actual User-Shop membership logic is modeled via `TenantMember` and `ShopRolePolicy`. T3-03 now resolves request-local Shop context after DRF authentication; T3-04 full queryset/object isolation remains pending.

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
- `Tenant` is the current technical representation of the approved Shop entity, with a Main Supplier foreign key and profile/contact/address fields. `TenantMember` links Users to Shops. T3-03 request context is implemented; end-to-end isolation remains pending in T3-04.
- `User` has no tenant foreign key directly. Instead, TenantMember links User and Tenant.  The approved target tenant-context mechanism is URL-path based: `/shops/{shop_id}/...`.
- The target Shop boundary and External Supplier ownership rules are defined above; they are not implemented by the current starter Tenant CRUD/API.

## API surface

- `/admin/`
- `/api/v1/auth/users/`, `/login/`, `/logout/`, `/token/refresh/`
- `/api/v1/tenants/` and tenant actions `activate`, `deactivate`, `stats`
- `GET /api/v1/shops/{shop_id}/context/` authenticates first, resolves one active Shop, and returns only the selected Shop UUID, the actor's selected-Shop role (null for Main Supplier), and Main Supplier context flag. Denied/unavailable Shop cases share a uniform 404; invalid/unauthenticated authentication remains 401.
- User API ordinary-user access is restricted to the authenticated user's own record; self-profile activation state is read-only.
- Shop-scoped APIs use `/shops/{shop_id}/...`; T3-03 establishes request-local context, while T3-04 remains responsible for all business-data queryset/object isolation.
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
2. T3-03 URL-path request context is implemented. Cross-module queryset/object isolation remains pending for T3-04; the existing `TenantScopedMixin` is not an authorization mechanism.
3. The tenant field is nullable, so tenant-scoped records can be unscoped by default.
4. The README references missing `apps.common.views.base_model_view` and `apps.tenants.mixins` components.
5. Local settings use `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` and `DB_*`; verify each deployment environment supplies those documented names.
6. JWT blacklist is installed/configured; runtime refresh rotation and reuse behavior is covered by authentication lifecycle tests, while deployment-specific database behavior still requires CI/runtime verification.
7. The foundation includes the single Supplier, Tenant-as-Shop mapping, membership/role policy, and T3-03 URL-path context, but does not yet implement External Supplier records, complete business-record isolation, or the end-to-end tailoring workflow.
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

Phase 1 foundation implementation is complete. Phase 3 T3-02A is implemented and pushed; remote CI is green. T3-03 request-local URL-path Shop context is implemented and locally verified. SGTP V1 is not ready for production. Business modules and end-to-end workflows remain unimplemented. Full data isolation is pending T3-04.

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
