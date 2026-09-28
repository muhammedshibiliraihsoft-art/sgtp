# Handoff

## Current phase

Phase 3 NOT STARTED for new implementation activation. Previously confirmed Phase 3 task outcomes are historical; latest work is the documentation-only T3-02A-BUSINESS-DECISION-LOCK.
## Current task

T3-02A-BUSINESS-DECISION-LOCK documentation task is COMPLETE. Latest implementation task T3-02-REMEDIATION remains COMPLETE and fully closed. This task recorded approved business rules only; it did not authorize or implement application work.

- **Changed areas:** User API authorization/serializer, Main Supplier Shop-write permission, membership serializer lifecycle protection, real throttle wiring/tests, duplicate CORS tests, production CORS environment propagation, CI validation, remediation regression tests, and documentation.
- **Validation:** Repository validator PASS; Django check PASS; migration drift check PASS; local application test suite PASS. Remote CI is green: the latest GitHub Actions workflow passed successfully, confirming the PostgreSQL CI connectivity and throttle cache isolation fixes. No migrations were required for closure. Production authentication throttling behavior was not weakened to make tests pass.
- **Next implementation candidate:** T3-02A remains NOT authorized. Present its bounded task plan and wait for exact `CONFIRM TASK T3-02A`. T3-03 and later tasks require their own confirmations.
- **Current blockers:** Ordinary-user Shop read visibility, Shop DELETE semantics, Shop Admin scoped settings authority, currency changes after financial history, and other later-phase decisions remain unresolved. Global User authority, public signup prohibition, phone rules, credential lifecycle, and Main Supplier Shop-settings authority are now confirmed in `docs/BUSINESS_RULES.md` and `docs/DECISIONS.md`. T3-03 remains unauthorized.
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
- At the reviewed baseline, branch `main`, HEAD and `origin/main` matched; T3-02 remediation is committed and GitHub Actions was green. Recheck Git and CI after documentation updates; prior evidence does not validate this diff.
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
- The starter is not yet the target product: complete request-scoped Shop isolation, clients, related persons, designs, measurements, materials, production stages, billing, reports/PDFs, frontend, persistent storage, workers, complete audit capture, monitoring, and end-to-end validation remain unimplemented. The latest verified baseline GitHub Actions run passed repository validation, application tests, Django checks, and migration checks; this local documentation diff has not been pushed and has no CI result.
- The target requires React/Vite/Tailwind, but the starter has only an empty `frontend/` placeholder. English/ar-KW/Bangla/Urdu localization, RTL/LTR, and Light/Dark/System are planned V1 requirements, not implemented.
- Tenant context is approved as URL-path based (`/shops/{shop_id}/...`) and must be implemented/tested in Phase 3.
- Related Person billing ownership is approved as Primary Client ownership and must be implemented/tested in Phase 5.

## Historical Phase Status

Phase 1 and Phase 2 are complete. 
Historical Phase 3 task outcomes:
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

## Roadmap handoff

T3-02A-BUSINESS-DECISION-LOCK authorized documentation/business-rule reconciliation only. Do not implement T3-02A, T3-03, T3-05A (Staging Backend Foundation), F7-01A (Staging Frontend & Client Review Checkpoint), any application feature, or deploy any environment under this task. T3-02A remains the next candidate and requires its own task plan and exact explicit confirmation. Newly approved account/authentication policies are targets, not implemented behavior; remaining policy items stay `BUSINESS DECISION REQUIRED` in the canonical decision record.

## Tests and checks — V1-ROADMAP-UPDATE

- Repository validator: PASS (dirty working tree warning is expected until documentation changes are committed).
- Validator tests: 11 passed.
- Application suite: 120 passed; collection was 120.
- Django system check: PASS.
- Migration check: no changes detected.
- `git diff --check`: PASS (Git emitted only CRLF-to-LF normalization warnings).
- GitHub Actions: the previously verified baseline run was green; this local documentation diff has not been pushed and has no new CI run.
- Scope: documentation only; no application source, migrations, deployment, commit, or push.

## T3-02A-BUSINESS-DECISION-LOCK — current session

- Decision: approved T3-02A account/authentication, phone, credential lifecycle, Shop settings, locale, and appearance rules are now recorded in the canonical business-rule and decision documents.
- Code status: unchanged. Anonymous User creation is still available in the current endpoint, and login remains email-only; T3-02A must reconcile these approved policy targets.
- Validation: repository validator PASS (dirty-tree warning expected); validator tests 11 passed; full pytest 120 passed; Django check PASS; migration drift check no changes; `git diff --check` PASS. Business Rule IDs are unique and `BUSINESS_RULES.md`/`DECISIONS.md` pass strict UTF-8 decoding. Current local diff has no new CI run.
- Next task: T3-02A remains unauthorized; obtain its exact task confirmation before implementation. T3-03 also remains unauthorized.
