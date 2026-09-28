# Handoff

## Current phase

Phase 3 (Shop / Tenant) implementation is active.
## Current task

Task T3-02-REMEDIATION is COMPLETE and fully closed. The security/integrity implementation and validation fixes are committed and verified remotely.

- **Changed areas:** User API authorization/serializer, Main Supplier Shop-write permission, membership serializer lifecycle protection, real throttle wiring/tests, duplicate CORS tests, production CORS environment propagation, CI validation, remediation regression tests, and documentation.
- **Validation:** Repository validator PASS; Django check PASS; migration drift check PASS; local application test suite PASS. Remote CI is green: the latest GitHub Actions workflow passed successfully, confirming the PostgreSQL CI connectivity and throttle cache isolation fixes. No migrations were required for closure. Production authentication throttling behavior was not weakened to make tests pass.
- **Next authorized task:** T3-03 is NOT YET AUTHORIZED. It requires a separate explicit CONFIRM TASK T3-03 after presenting its task plan. Do not infer authorization.
- **Current blockers:** Business decisions remain required for global User administration ownership, ordinary-user Shop read visibility, and Shop DELETE semantics. T3-03 remains unauthorized.
- **Agent Transition Note:** Upcoming engineering work may be executed through Codex; repository governance and explicit task-confirmation rules remain authoritative regardless of implementation agent.
## Repository state evidence
- Verify current HEAD with `git rev-parse HEAD`
- Verify remote parity with `git status -sb`
- Do not treat a stored commit hash in documentation as authoritative.

## Repository and workspace

- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- `docs/`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Historical Phase 1 corrective implementation was completed and published to `origin/main`.
- At the reviewed baseline, branch `main`, HEAD and `origin/main` matched; closure changes remain local.
- Starter source files were modified for Phase 1.
- Existing SGTP `.git` metadata and history preserved.

## Target final product

SGTP is now defined as the Supplier-Centric Garment & Tailor Platform, with Tailor Management as the core V1 module. The hierarchy is Supplier/Main Admin -> Supplier Back Office -> isolated Shop workspaces -> Clients, Designs, Measurements, Fabric/Materials, Work, Billing, and Reports.

The required persisted flow is:

`Client Request -> Design -> Measurement -> Fabric/Material -> Cutting -> Stitching -> Check -> Finishing -> QC -> Completed -> Billing -> Reports/History`

The full product definition and Definition of Done are in `docs/PRODUCT_DEFINITION.md`.

## Locked V1 tenancy model

- V1 has exactly one top-level Supplier / Main Admin and no multi-supplier SaaS model.
- The hierarchy is Main Supplier / Main Admin → Supplier Back Office → multiple isolated Shops.
- Shop is the tenant/workspace boundary.
- External Supplier records are owned by exactly one Shop and are not users, tenants, members, roles, or authentication participants. They do not log in.
- External Supplier records are not global/shared; Shop isolation applies to all access and discovery paths.
- The starter `Tenant` model has been retained and structurally mapped as the V1 technical implementation for `Shop`. T3-01 verified this structural mapping was safe. A `Supplier` singleton model was created to enforce exactly one top-level platform owner.

## Inspection summary

The starter is a Django 5.1.4 / DRF 3.15.2 PostgreSQL project with Docker, devcontainer, JWT authentication, a custom email user, tenants, UUID/audit/soft-delete base models, OpenAPI/Swagger, and tests. It contains `core/`, `apps/accounts/`, `apps/tenants/`, `apps/common/`, templates, dependency/tooling files, Docker infrastructure, and editor configuration.

## Reusable

- Django project wiring and environment-loading pattern.
- Custom user model, user manager, admin, JWT endpoints, serializers, and initial tests.
- Tenant model/admin/API/migrations/tests as a starting point only.
- UUID, timestamps, audit fields, and soft-delete base model.
- PostgreSQL, Docker, devcontainer, Gunicorn, WhiteNoise, Makefile, and tooling setup.

## Phase 3+ Deferred Implementations

- `BaseModelWithTenant.tenant` is nullable and no active-tenant/request authorization mechanism exists.
- The starter is not yet the target product: complete request-scoped Shop isolation, clients, related persons, designs, measurements, materials, production stages, billing, reports/PDFs, frontend, persistent storage, workers, complete audit capture, monitoring, and end-to-end validation remain unimplemented. CI currently validates repository state, runs tests, and performs Django/migration checks, subject to the pending GitHub workflow confirmation recorded above.
- The target requires React/Vite/Tailwind, but the starter has only an empty `frontend/` placeholder.
- Tenant context is approved as URL-path based (`/shops/{shop_id}/...`) and must be implemented/tested in Phase 3.
- Related Person billing ownership is approved as Primary Client ownership and must be implemented/tested in Phase 5.

## Historical Phase Status

Phase 1 and Phase 2 are complete. 
Phase 3 is active:
- **T3-01 Supplier and Shop Entities**: Complete. The repository has a reproducible database baseline, Shop mapping, and Supplier singleton constraint.
- **T3-02 User-Shop membership and roles**: Complete. `TenantMember` and `ShopRolePolicy` firmly establish user roles and Main Supplier cross-shop authority.

## T3-02 remediation status

- Ordinary users cannot enumerate or target other User records through the User API; self-profile updates remain supported.
- Shop write and activate/deactivate permissions now use `ShopRolePolicy.is_main_supplier_admin`, so `is_staff` alone is insufficient.
- Membership `is_active` is read-only in generic PATCH/PUT; lifecycle actions remain the only state-transition API.
- Real authentication throttling is verified by an integration-style repeated-login test; duplicate CORS tests are independently collected.
- CI now includes the full application suite, Django check, and migration check in addition to project-state validation.
- Production CORS configuration receives `DJANGO_CORS_ALLOWED_ORIGINS` from deployment environment variables.
- No migrations were created.
- T3-03, external suppliers, and future business modules remain unimplemented.

## Recommended next action

After closure is verified and reported, stop. T3-03 remains unauthorized and requires its own task plan and explicit `CONFIRM TASK T3-03`. Phase 3 activation does not authorize T3-03 or any other Phase 3 task automatically.
