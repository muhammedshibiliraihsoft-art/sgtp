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

## Parallel frontend foundation and ownership

`main` remains the backend/current integration source of truth and the primary owner of canonical project and business documentation. Parallel visual and frontend-foundation work uses the same repository on `frontend/parallel-foundation` in the sibling worktree `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp-frontend`; frontend implementation lives under `/frontend` and must not be developed in the main worktree. Frontend-specific instructions and handoff belong under `frontend/`.

This early Parallel Frontend Foundation Track is not Phase 7 completion and does not move or waive F7-01 dependencies. It may establish tooling, application/layout shells, design tokens/components, accessibility/responsive/i18n/RTL/LTR/theme foundations, and mock-first API adapters. Unimplemented backend features remain interfaces/mocks, not live contracts. Backend/main is synchronized into the frontend branch through deliberate normal merges; unfinished frontend work is not routinely merged into main. Frontend navigation and role presentation are UX only; all authorization remains backend-enforced.

Ordinary Users have one immutable owning Shop and do not select among multiple Shop memberships after login. Main Supplier is the global authority; any cross-Shop navigation depends on a real authorized backend contract and does not imply ordinary-user multi-Shop identity.

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

### T3-05A staging backend foundation (implementation in progress)

The repository now defines an explicit `DJANGO_ENV=staging` settings module, a Render Blueprint for a manually deployed, isolated staging API/PostgreSQL pair, bounded startup readiness/migration behavior, and safe health/CSRF bootstrap support. Render resources, DNS/TLS, and an operational deployment are not claimed until verified through the provider. The Free plan is temporary and non-durable; see `docs/runbooks/STAGING_BACKEND.md` for its current limitations and gates. No Production or business module is part of this work.

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

- Current implementation after local T3-04A: UUID primary key, immutable generated `user_code`, optional unique canonical email and E.164 phone for normal Users, and identifier login by User ID/email/phone. `USERNAME_FIELD=email` is retained for Django Admin/CLI compatibility; API auth uses the explicit identifier resolver.
- Persist nullable User preferred locale and `system|light|dark` appearance, defaulting appearance to `system`; locale selection is `User preference → authorized Shop default → English`.
- Shop default locale/timezone/currency are configuration only and must be resolved only after authorization. None of these preferences or settings may determine role, membership, access, or Shop selection.
- Public self-registration is prohibited; Main Supplier Admin retains global User creation/credential-reset authority, while Shop ADMINs have only the published same-Shop STAFF/VIEWER creation/reset scope. Normal Users may omit both contacts; superusers and active Shop ADMIN contact-removal paths require email and phone. No phone verification is required.
- Generated initial passwords are cryptographically random, hash-only at rest, emitted once with no-store, and changed at first login. Current recovery is email-based with secure, expiring, single-use behavior; password change/reset revokes refresh-token sessions.
- Shop timezone/currency are explicit and are never inferred; they may remain unset until configured. Main Supplier Admin manages Shop-level settings in the current foundation. Shop Admin settings authority is not granted by T3-02A.
- Generated account credentials are one-time response data with `Cache-Control: no-store`; first-login password change gates normal authenticated API operations. Password recovery is generic to the caller and uses expiring single-use Django reset tokens delivered by configured email. Plaintext passwords/reset tokens are not written to application storage or audit records.
- Shop default settings are serialized only on Main Supplier Admin reads/writes. Existing broad authenticated Shop reads retain their previous scope but omit the new settings fields; this does not implement T3-03 context or change Shop visibility policy.

### Identity and staffing architecture

- Each ordinary User has one immutable `owning_shop`; its membership role and lifecycle belong to that Shop. The same real-world person may have independent accounts in different Shops, but an account cannot be shared or reassigned. Main Supplier accounts remain global with no owning Shop.
- `TenantMember` references the ordinary account's owning Shop, and the database guards ownership/membership consistency. Shop creation atomically creates a new first ADMIN account and membership. Main Supplier may create any Shop role; a Shop ADMIN may create STAFF/VIEWER and reset current same-Shop STAFF/VIEWER credentials only.
- Existing T3-04B membership/Admin safeguards remain in force. T3-04B-USER-SCOPE is published at `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c` with exact-SHA CI success in run `36591864481`.
- Every User receives permanent `user_code` (human User ID); UUID remains the internal key/JWT `user_id`. Normal-user email/phone are optional; active Shop ADMIN/Main Supplier accounts require both. T3-04A and the T3-04B remediation are published; the latter enforces membership promotion/lifecycle/cardinality safeguards.
- Access Role (`ADMIN`, `STAFF`, `VIEWER`) is distinct from membership-scoped Work Functions. Each Shop permits one to two active ADMIN memberships; Main Supplier manages this hierarchy. Shop creation establishes its first ADMIN, and global deactivation must preserve at least one active ADMIN in every affected Shop.
- Work Functions are normalized zero-to-many assignments on a Shop membership, from the approved controlled V1 catalog. They describe work eligibility, not authorization. Shop ADMINs manage functions only within their own Shop through the Shop-path API. T3-04C implements persistence, transactional set management, and lifecycle history; Phase 4 owns workflow-stage mapping and work assignment.
- Approved Shop rules are implemented in T3-05: ordinary Users see only authorized Shops; Main Supplier controls Shop activation/deactivation and settings; deactivation preserves Shop data/memberships; no ordinary Shop DELETE; max_users cannot be lowered below current user_count. T3-05 is published and its exact-SHA CI succeeded.
- Preserve the existing explicit `/shops/{shop_id}/...` context, authentication ordering, uniform non-disclosing unavailable-Shop 404, 401 authentication behavior, and T3-04 trusted-context/query/object boundary. A person with accounts in different Shops uses distinct independent accounts; each request still requires explicit authorized Shop context, and no preference/default guess replaces the path context.

### Current code boundary and approved target

The current `User` model uses email as Django's `USERNAME_FIELD` for Admin/CLI compatibility, but email may be null; `user_code` is the permanent human identifier, `first_name` is required, and ordinary Users have one immutable `owning_shop`. `TenantMember` is constrained to that owning Shop and has a per-membership role. Published T3-04B safeguards enforce the one-to-two active-ADMIN invariant and lifecycle authority. Membership-scoped Work Functions are implemented by T3-04C; T3-05 Shop management is published with exact-SHA CI green.

## Planned cross-cutting V1 presentation and operations

- Supported UI locales are English (`en`), Arabic Kuwait (`ar-KW`), Bangla (`bn`) and Urdu (`ur`); Arabic/Urdu are RTL, English/Bangla LTR, with explicit mixed-direction handling. Preserve Unicode and canonical source text.
- Theme is Light/Dark/System, persisted per User; semantic tokens and system preference may change presentation only. No theme-specific business logic or dual component trees.
- Work priority is Normal/Urgent/Very Urgent. Upcoming/due-soon/today/overdue are derived date indicators, not workflow states; threshold and date cutoff remain business decisions.
- V1 observability includes approved error tracking, environment tags, request correlation, failed-job visibility, critical alerts and secret-safe logs. Audit captures actor/Shop/action/object/safe change/timestamp/correlation, never credentials or tokens.
- Environment lifecycle is LOCAL → STAGING → PRODUCTION. Staging is isolated, demo-data-only, visibly non-production and requires browser verification of cookie/CSRF/CORS at `staging.birky.com` / `api-staging.birky.com`. Phase 9 reuses the same Staging environment for formal release-candidate validation. Phase 10 remains the sole Production gate. Details: `docs/ENVIRONMENTS.md`.
- No Post-V1 work begins before Phase 10 and full V1 acceptance; see `docs/POST_V1_ROADMAP.md` for deferred scope and the constrained enhancement lane.

## Permissions and Scoping

- Object-level permission primitives include `IsOwner`, `IsTenantMember`, and `DenyAll`. `IsTenantMember` requires trusted T3-03 context and binds an object to the selected Shop, including for Main Supplier requests.
- `TenantScopedMixin` now requires authenticated `request.shop_context`, checks actor, URL Shop ID, and the derived `request.tenant_id` alias for consistency, and filters by the trusted Shop. Missing required context/configuration fails closed; create/update ownership is saved from the authorized Shop.
- Actual User-Shop account ownership and membership logic is modeled via `User.owning_shop`, `TenantMember`, and `ShopRolePolicy`. Each ordinary account has one immutable owning Shop; same-Shop membership consistency and scoped account operations are implemented by the published T3-04B-USER-SCOPE task. Each later Shop-owned endpoint must still adopt reusable isolation primitives and prove its own isolation.

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
- `Tenant` is the current technical representation of the approved Shop entity, with a Main Supplier foreign key and profile/contact/address fields. `TenantMember` links Users to Shops. T3-03 request context and T3-04 reusable scope/permission primitives are implemented. `BaseModelWithTenant.tenant` remains nullable; no concrete business subclass currently needs a migration.
- `User` has no tenant foreign key directly. Instead, TenantMember links User and Tenant.  The approved target tenant-context mechanism is URL-path based: `/shops/{shop_id}/...`.
- The target Shop boundary and External Supplier ownership rules are defined above; they are not implemented by the current starter Tenant CRUD/API.

## API surface

- `/admin/`
- `/api/v1/auth/users/`, `/login/`, `/logout/`, `/token/refresh/`
- `/api/v1/tenants/` and tenant actions `activate`, `deactivate`, `stats`
- `GET /api/v1/shops/{shop_id}/context/` authenticates first, resolves one active Shop, and returns only the selected Shop UUID, the actor's selected-Shop role (null for Main Supplier), and Main Supplier context flag. Denied/unavailable Shop cases share a uniform 404; invalid/unauthenticated authentication remains 401.
- User API ordinary-user access is restricted to the authenticated user's own record; self-profile activation state is read-only.
- Shop-scoped APIs use `/shops/{shop_id}/...`; T3-03 establishes request-local context and T3-04 supplies the reusable trusted-context queryset/object boundary. Business modules/endpoints must adopt it when introduced.
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
2. T3-03 URL-path request context and T3-04 trusted-context query/object primitives are implemented. No production business-resource endpoints exist yet; their adoption and end-to-end isolation remain future verification requirements. `TenantScopedMixin` is an isolation primitive, not a substitute for endpoint/action authorization.
3. The tenant field is nullable, so tenant-scoped records can be unscoped by default.
4. The README references missing `apps.common.views.base_model_view` and `apps.tenants.mixins` components.
5. Local settings use `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` and `DB_*`; verify each deployment environment supplies those documented names.
6. JWT blacklist is installed/configured; runtime refresh rotation and reuse behavior is covered by authentication lifecycle tests, while deployment-specific database behavior still requires CI/runtime verification.
7. The foundation includes the single Supplier, Tenant-as-Shop mapping, membership/role policy, T3-03 URL-path context, and T3-04 scoped query/object primitives, but does not yet implement External Supplier records, business-resource endpoints, or the end-to-end tailoring workflow.
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

Phase 1 foundation implementation is complete. T3-02A, T3-03, T3-04, T3-04A, T3-04B remediation, T3-04B-USER-SCOPE, T3-04C, and T3-05 are published; Project State Validation passed for the exact T3-05 commit. SGTP V1 is not ready for production. Business modules and end-to-end workflows remain unimplemented; future endpoints must adopt and verify the T3-04 boundary.

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
