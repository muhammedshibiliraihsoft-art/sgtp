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

- T3-02A, T3-03 URL-path context, T3-04 reusable query/object isolation primitives, T3-04A, T3-04B remediation, T3-04B-USER-SCOPE, T3-04C, and T3-05 are published. T3-04C exact-SHA Project State Validation succeeded. T3-05 exact-SHA Project State Validation succeeded in run `36614638187`; T3-05A is the current confirmed task. See the Phase 3 playbook and staging runbook.

## Phase 4 — core tailor business

- After Phase 3 identity/membership/Work-Function prerequisites, implement Clients/Related Persons and searchable duplicate-warning flow, Catalog/Designs and private reference metadata, extensible measurement templates with immutable history/compare, Materials, Work/Orders with approved priorities and derived date indicators, workflow, service layer, constraints and concurrency safeguards. Workflow remains canonical and fixed; staffing uses `Access Role + authorized Shop context + Work Function eligibility + specific assignment + explicit service policy`, not tailoring-job access roles. Work Function eligibility alone is not authorization. Stage/function mapping (including whether Check needs a distinct function) belongs to its Phase 4 task; no per-Shop workflow builder.

## Phase 5 — billing + reports + reliability

- Implement Decimal-safe advance/partial/final Billing, Outstanding, Primary Client ownership for Related Person billing, idempotency, audit/alert foundation, multilingual PDFs/reports with per-document locale override, private object storage, observable background jobs, backup and restore verification, and financial safety.

## Phase 6 — AI + integrations

- Implement isolated `ai_agents`, controlled tools, service interfaces, locale/authorized Shop and actor context, timeout/fallback/output validation and original-text preservation, adapters/webhook validation/retries/idempotency/failure isolation. Full AI Assistant and Smart Translation Assist remain Post-V1.

## Phase 7 — frontend

- Implement React + Vite + Tailwind, English/ar-KW/Bangla/Urdu i18n, RTL/LTR, Light/Dark/System, authenticated API client, Staging checkpoint, role/Shop routing and authorized settings, V1 business screens, and approved AI interfaces; remain desktop-usable, tablet-ready and mobile-safe for essential flows.

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
- No Post-V1 work starts before Phase 10 and the complete V1 Definition of Done pass. Environment progression and the constrained Small Enhancement Lane are documented in `docs/ENVIRONMENTS.md` and `docs/POST_V1_ROADMAP.md`.

## Out of scope for V1 unless explicitly added

- Unapproved business modules or changes to the supplier/shop hierarchy.
- AI or third-party integrations that can directly control or break core business workflows.
- Technology-stack replacement.

## Approved V1 roadmap amendment

This amendment adds requirements and checkpoints without changing the ten-phase architecture, order, or task-confirmation gate above. V1 is a strict release target: no post-V1 work may begin until Phase 10 acceptance and the complete product Definition of Done pass. The controlled Small Enhancement Lane may be used only during an already confirmed task and only within its documented limits in `docs/POST_V1_ROADMAP.md`.

### Phase 3 task sequence

`T3-01 (complete) → T3-02 (complete) → T3-02-REMEDIATION (closed) → T3-02A (complete) → T3-03 (complete) → T3-04 (complete) → T3-04A (published) → T3-04B-REMEDIATION-01 (published) → T3-04B-USER-SCOPE (published; exact-SHA CI green) → T3-04C (published; exact-SHA CI green) → T3-05 → T3-05A`.

- **T3-04A — Global identity/User-ID/authentication remediation (published):** permanent role-/Shop-neutral User ID; optional normal-user email/phone; first-name display rule; admin-grade contact safeguards; identifier login; generated Main Supplier recovery; guarded compatibility/backfill. Preserve UUID, password hashes, existing email, memberships, and JWT/CSRF/refresh protections. No OTP/provider work.
- **T3-04B — Membership/Admin-invariant remediation (published):** one-to-two active ADMIN invariant; Main Supplier-controlled ADMIN hierarchy; atomic first-ADMIN Shop creation; User deactivation guard; membership lifecycle/capacity integration. Its earlier one-global-User/multi-Shop account assumption is superseded by the separately confirmed T3-04B-USER-SCOPE task. Preserve T3-03/T3-04 context and isolation. Broader Shop visibility/lifecycle API scope remains T3-05.
- **T3-04B-USER-SCOPE (published):** each ordinary account is permanently owned by one Shop; different Shops use distinct accounts even for the same person. Shop creation atomically creates the first ADMIN account/membership; Main Supplier creates any role; Shop ADMIN creates only same-Shop STAFF/VIEWER and resets only current same-Shop STAFF/VIEWER. Migration preflight stops for multi-Shop or unowned ordinary accounts. Commit `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c`; Project State Validation run `36591864481` succeeded.
- **T3-04C — Work-Function foundation (published):** depends on published T3-04B safeguards and T3-04B-USER-SCOPE. Zero-to-many controlled Work Functions per Shop-owned membership, Shop-local ADMIN management, isolation and lifecycle preservation; functions are not permissions. No Phase 4 workflow or assignment implementation. Exact-SHA Project State Validation succeeded.
- **T3-02A — Account, phone, locale, and preference foundation (complete; historical contract):** implemented UUID/email-compatible E.164 phone login, Main Supplier Admin-only account creation/phone administration, one-time no-store generated credentials and forced first-login change, email reset and session revocation, persisted nullable User locale/appearance and Shop defaults. Email was required at T3-02A completion; T3-04A later made normal-user email optional. Do not add OTP/SMS/WhatsApp/2FA providers. Shop Admin settings authority is not granted; currency change after financial history remains `BUSINESS DECISION REQUIRED`. See Phase 3 playbook and current handoff for validation evidence.
- **T3-03 (complete):** establish authenticated request-local context at `/api/v1/shops/{shop_id}/...`; deny foreign or unavailable Shops with a uniform non-disclosing 404 and preserve 401 authentication failures. Preferences and Shop defaults never authorize access. This does not implement query/object isolation.
- **T3-04 (foundation complete):** `TenantScopedMixin` requires authorized T3-03 context, verifies URL/actor/compatibility-alias consistency, scopes reads/detail lookups, and assigns the selected Shop on create/update. `IsTenantMember` binds objects to the selected Shop for ordinary members and Main Supplier. Test-only UUID/FK proof coverage verifies lists/counts, direct IDs, Main Supplier scope, ownership, update protection, mismatch/missing context, and soft delete. No business modules, migrations, or dependencies were added; each future business endpoint must adopt and test this boundary.
- **T3-05 (published; exact-SHA CI green):** authorized Shop/profile/stats and membership APIs/actions, exact User-ID member lookup, Main Supplier-only settings and Shop lifecycle, Django Admin/API parity, `max_users >= user_count` validation, actor attribution, concurrency/undo safety, and accurate OpenAPI contracts. Ordinary Shop DELETE is disabled; deactivation preserves data/memberships. Shop Admin settings authority remains not granted; currency changes after financial history remain a separate financial-policy decision. Published implementation commit: `3d21a0943006cd866bc19bc728cbec05daae1630`; Project State Validation run `36614638187` succeeded.
- **T3-05A — Staging Backend Foundation:** after T3-05 and verified isolation, establish the first shared non-production staging backend environment at `api-staging.birky.com` with isolated PostgreSQL, health/readiness, CORS/CSRF configuration, staging logs, synthetic/demo data, and safe data reset. Staging is not Production.
  - Execution status: task confirmed; repository implementation is published and exact-SHA Project State Validation run `36652187336` succeeded. External Render account, resource creation, DNS/TLS, and live deployment remain unverified until provider access is available.

### Later-phase requirement placement

#### Parallel Frontend Foundation Track (pre-Phase-7 preparation)

Frontend preparation may proceed in parallel with Phase 3 backend work on `frontend/parallel-foundation` in a dedicated worktree, using the same SGTP repository. This isolated track may establish React/Vite/Tailwind/TypeScript tooling, application and layout shells, reusable UI foundations, responsive/accessibility defaults, locale and RTL/LTR infrastructure, Light/Dark/System theme infrastructure, and mock-first API/service boundaries based only on published contracts. It must not implement unimplemented business workflows or invent backend APIs, permissions, Shop selection rules, or business behavior.

This track is explicitly not F7-01, does not complete Phase 7, and does not change the formal task/dependency order below: F7-01 and F7-01A remain sequenced after T3-05A as already approved. Canonical cross-project documentation remains main-owned; frontend-specific working guidance belongs under `frontend/`. Sync backend changes from `main` into the frontend branch using reviewed, normal merges; do not routinely merge unfinished frontend work back to `main`.

- **Phase 4:** Shop-scoped Client quick search by name/normalized phone/stable ID (Work number when available); duplicate warning without silent merge; measurement templates, immutable history and comparison; private design-reference gallery; Normal/Urgent/Very Urgent Work priority; derived delivery-date indicators. No Client tags in V1. Date thresholds/cutoffs remain unresolved. Staffing/authorization context uses access role, authorized Shop context, eligible Work Function, optional specific membership/User assignment, and explicit service policy. No per-Shop workflow builder; stage/function mapping is decided in its Phase 4 task, with no new function invented in advance.
- **Phase 5:** advance/deposit, partial and final payments; Decimal-safe, idempotent financial services; outstanding balances; Primary Client billing ownership for Related Person work; linked receipts/invoices/reports with per-document language override; English, Arabic RTL, Bangla and Urdu PDF validation; private object storage, observable jobs, audit events, backup and actual restore verification. Refund, overpayment, allocation and retention choices remain unresolved unless already approved.
- **Phase 6:** preserve controlled AI/integration scope; propagate requested locale, authorized Shop/actor context, timeout/fallback, output validation and original-text preservation. AI cannot alter canonical data or bypass workflow, billing, or isolation.
- **Phase 7:** React/Vite/Tailwind foundation includes English/ar-KW/Bangla/Urdu localization, correct RTL/LTR and mixed-direction handling, Light/Dark/System semantic theme, preference synchronization, international phone UX, normalized API errors and request IDs. Insert F7-01A Staging Frontend & Client Review Checkpoint after F7-01 acceptance and before F7-02. F7-02–F7-05 cover preferences/routing, authorized settings, business screens, responsiveness/accessibility and failure handling.
- **Phase 8:** integrated authentication, localization, RTL, theme, business, PDF, privacy, security and cross-Shop test matrix. Shop A must never discover Shop B through search, duplicate checks, IDs, gallery, measurements, billing, reports, settings or notifications.
- **Phase 9:** formal release-grade Staging reuses the existing staging environment after appropriate reset/reconfiguration; verify full deployment, auth/CSRF, locale/theme, business flows, files/jobs/PDFs, isolation, backup and restore.
- **Phase 10:** sole Production/V1 release gate; accept only a Phase 9-approved candidate after full integrated workflow, security, observability, backups/restore and documentation evidence.

Environment progression is `LOCAL → STAGING → PRODUCTION`. Do not deploy unfinished commits automatically or treat client feedback as implementation authorization. See `docs/ENVIRONMENTS.md`.

### Frontend timing adjustment

F7-01 and F7-01A are allowed to execute immediately after T3-05A in the overall dependency sequence:

`T3-01 (complete) → T3-02 (complete) → T3-02-REMEDIATION (closed) → T3-02A → T3-03 → T3-04 → T3-04A → T3-04B → T3-04C → T3-05 → T3-05A → F7-01 → F7-01A → Phase 4 → Phase 5 → Phase 6 → F7-02 → F7-03 → F7-04 → F7-05 → Phase 8 → Phase 9 → Phase 10`.

This gives the client a usable staging shell earlier, validates authentication/i18n/theme integration early, and reduces frontend/backend contract surprises. F7-02–F7-05 remain later frontend implementation tasks unless separately re-planned.
