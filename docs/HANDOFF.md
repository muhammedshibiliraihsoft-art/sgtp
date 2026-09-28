# Handoff

## Current phase

Phase 3 (Shop / Tenant) implementation is active.
## Current task

Task T3-02 (User-Shop membership and roles) remediation is complete and verified (Identity, Lifecycle, Undo, Capacity).

- **Changed areas:** `apps/tenants/models/membership.py`, `apps/tenants/policy.py`, `apps/tenants/tests/test_membership.py`, `apps/tenants/tests/test_membership_api.py`, `apps/tenants/views/membership.py`, `apps/tenants/serializers/membership.py`, `core/permissions.py`, `docs/PROJECT_STATE.md`, and `docs/HANDOFF.md`.
- **Validation performed:** Verified local tests running clean. `pytest` successful (65 tests pass). `manage.py check` passes with zero issues.
- **Next authorized task:** T3-03 is NOT YET AUTHORIZED. It requires a separate explicit `CONFIRM TASK T3-03` after presenting its task plan. Do not infer authorization.
- **Current blockers/deferred items:** None.
## Repository state evidence
- Verify current HEAD with `git rev-parse HEAD`
- Verify remote parity with `git status -sb`
- Do not treat a stored commit hash in documentation as authoritative.

## Repository and workspace

- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- `docs/`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Phase 1 corrective implementation was completed and published to `origin/main`.
- Branch: `main` tracking `origin/main`
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
- The starter is not yet the target product: supplier back office, isolated shop workspaces, clients, related persons, designs, measurements, materials, production stages, billing, reports/PDFs, frontend, storage, jobs, audit, CI, monitoring, and end-to-end validation are not implemented.
- The target requires React/Vite/Tailwind, but the starter has only an empty `frontend/` placeholder.
- Tenant context is approved as URL-path based (`/shops/{shop_id}/...`) and must be implemented/tested in Phase 3.
- Related Person billing ownership is approved as Primary Client ownership and must be implemented/tested in Phase 5.

## Historical Status

Phase 1 and Phase 2 are complete. 
Phase 3 is active:
- **T3-01 Supplier and Shop Entities**: Complete. The repository has a reproducible database baseline, Shop mapping, and Supplier singleton constraint.
- **T3-02 User-Shop membership and roles**: Complete. `TenantMember` and `ShopRolePolicy` firmly establish user roles and Main Supplier cross-shop authority.

## Recommended next action

Next, present the T3-03 task plan and await explicit `CONFIRM TASK T3-03`. Phase 3 activation does not authorize T3-03 or any other Phase 3 task automatically.
