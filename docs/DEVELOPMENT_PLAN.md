# Development Plan

This plan is subordinate to `docs/PRODUCT_DEFINITION.md`. It preserves the approved SGTP supplier → back office → isolated shop hierarchy and the complete persisted production-to-billing workflow.

## Execution gate

Phase confirmation activates only the named phase. It does not authorize all tasks listed under that phase. Before every task, the implementing agent must present the task objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for `CONFIRM TASK <TASK-ID>`. It may implement only that task, must validate and document it, and must stop. The next task and next phase each require a new explicit confirmation.

## Phase 0 — repository and product definition

- Preserve and inspect the original SGTP starter repository.
- Define the target final product, V1 boundaries, business hierarchy, workflow, and Definition of Done.
- Record starter reuse, contradictions, risks, and unresolved decisions.

## Phase 1 — foundation

- Verify repository/dependency/virtual-environment baseline.
- Establish environment management, django-environ or approved equivalent, settings split, custom User/core/shared model interfaces, PostgreSQL, migrations, secure defaults, and baseline documentation.
- Do not create business modules.

## Phase 2 — backend core + security

- Establish DRF/API versioning, CORS, JWT access/refresh lifecycle, rotation/reuse detection, object-permission and tenant-scoping interfaces, rate limiting, exceptions, API documentation, health, and security validation.

## Phase 3 — shop / tenant

- Implement the approved URL-path tenant context `/shops/{shop_id}/...`, then implement Supplier/Main Admin, Supplier Back Office, Shop, User-Shop membership, roles, scoped queries, supplier cross-shop visibility, shop isolation, and object-level access tests.

## Phase 4 — core tailor business

- Implement Clients, Family/Related Persons, Catalog, Designs, Measurements, Materials, Works/Orders, the approved production workflow, service layer, business rules, indexes, constraints, and concurrency safeguards.

## Phase 5 — billing + reports + reliability

- Implement Billing, Accounts, Transactions, Outstanding, Primary Client ownership for Related Person billing, billing idempotency, audit logging, soft delete, PDF generation, Reports, object storage, background jobs, backup strategy, restore verification, and financial safety.

## Phase 6 — AI + integrations

- Implement isolated `ai_agents`, controlled tools, service interfaces, AI permissions/tenant awareness, timeout/fallback/output validation, integration adapters, webhook validation, retries, idempotency, and failure isolation.

## Phase 7 — frontend

- Implement React + Vite + Tailwind foundation, authentication/API client, role-aware routing, tenant context, Supplier Back Office, Shop workspace, Clients, Designs, Measurements, Materials, Works, Billing, Reports, and approved AI interfaces.

## Phase 8 — testing + hardening

- Complete unit/API/integration/authentication/permission/tenant-isolation/workflow/billing/file/failure/regression/security/performance validation.
- Prove the critical invariant: Shop A must never access Shop B data.

## Phase 9 — staging

- Establish staging environment/database/configuration/deployment, migrations, object storage, workers, monitoring, smoke/E2E testing, backup restore drill, and production readiness evidence.

## Phase 10 — production

- Complete production configuration/secrets, PostgreSQL/object storage/workers, migrations, monitoring, backups, deployment validation, final security review, acceptance, documentation, and handoff.

## Phase boundaries

- Future phase files may be read for context but must not be implemented early.
- A phase is not complete merely because its code runs; its own validation checklist, documentation, and handoff must pass.
- V1 is complete only after the integrated end-to-end journey and Definition of Done in `docs/PRODUCT_DEFINITION.md` pass.

## Out of scope for V1 unless explicitly added

- Unapproved business modules or changes to the supplier/shop hierarchy.
- AI or third-party integrations that can directly control or break core business workflows.
- Technology-stack replacement.
