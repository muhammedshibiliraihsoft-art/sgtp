# Phase 4 — Core Tailor Business

## 1. Phase Overview
Implement the shop-scoped Tailor Management domain.
## 2. Phase Objective
Connect clients, related persons, catalog/designs, measurements, materials, and work through the approved workflow.
## 3. Business Purpose
Give shops an operational record from client request to completed garment work.
## 4. Technical Purpose
Create normalized entities, service-layer rules, state transitions, constraints, indexes, and concurrency protection.
## 5. Preconditions
Phase 3 T3-04A–T3-04C identity/membership/Work-Function prerequisites and T3-05 Shop/API/Admin hardening accepted; T3-04 isolation DoD passed; T3-05A staging foundation accepted; explicit `CONFIRM PHASE 4`; all required documents read. Frontend integration completion is not a Phase 4 prerequisite. Phase 4 backend tasks follow their own dependency graph; after each backend contract is accepted, its corresponding frontend slice may follow independently under the Contract-First and UI Reference Gates.
## 6. Dependencies
Shop context/membership, permissions, shared models, PostgreSQL.
## 7. Current Repository Assumptions
Accounts, Supplier/Shop (legacy Tenant), memberships, T3-03 Shop context, and T3-04 reusable isolation primitives exist. T3-04A identity/User-ID remediation, T3-04B membership/Admin safeguards, T3-04B-USER-SCOPE, and T3-04C Work Functions are published; exact-SHA CI passed for T3-04C. T4-01 Clients/Related Persons is the first Phase 4 module and is published; T4-02 and later Phase 4 business modules/services are not implemented and require their own task authorization.
## 8. Exact Scope
Clients, family/related persons, catalog/designs, measurements, materials, works/orders, workflow services, indexes, constraints, concurrency.
## 9. Out of Scope
Billing, PDF/report generation, AI integrations, frontend screens, production deployment.
## 10. Architecture Context
Every record is shop-scoped; service methods are the business boundary; transitions are explicit and audited. Staffing/authorization combines Access Role, authorized Shop context, Work-Function eligibility, optional specific assignment, and explicit service policy. Work Functions do not authorize actions. The workflow is fixed across Shops; no per-Shop builder.

When a membership becomes inactive or loses a Work Function while assigned work is open, preserve historical actor records; do not silently transfer ownership or block urgent security deactivation. Clearly mark affected open work for reassignment or route it through an explicitly approved reassignment service. The exact operational behavior belongs to the relevant Phase 4 task; do not rewrite workflow history.
## 11. Implementation Sequence
Clients → related persons → catalog/designs → measurements → materials → work aggregate → workflow services → APIs/tests.
## 12. Detailed Task List

### T4-01 Clients and related persons
Objective: implement Shop-scoped Clients and Related Persons, preserving Primary Client billing ownership for future Work. Dependencies: accepted Phase 3 identity/membership/Shop context/isolation foundations and Phase 4 activation. Expected runtime app: `apps/clients/` because the current Django project loads apps from `apps.*`; do not create a shadow `backend/apps` package or relocate existing apps. Steps: add UUID Client and RelatedPerson models, required Shop ownership, required RelatedPerson→Primary Client, optional contact fields, soft deletion, same-Shop relationship validation, and deterministic contact normalization. Use UUID identity only; no client_code. Search Unicode names, normalized phone, exact UUID, paginated deterministically; exclude deleted records. Do not add Work-number search before T4-04 exists. Duplicate phone/email matches in the same Shop and same record type return machine-readable warning only, allow creation/update, and never merge; warnings expose only same-Shop matches. Serialize duplicate-sensitive writes by locking the Shop before checking and writing. No Client tags. API: `/api/v1/shops/{shop_id}/clients/` plus nested `/clients/{client_id}/related-persons/`, CRUD with role permissions and soft-delete DELETE. Permissions: Main Supplier and active same-Shop ADMIN full CRUD; STAFF read/create/update; VIEWER read-only; inactive/removed none; Work Functions do not alter permission. DB: UUIDs, Shop/parent FKs, search indexes; no contact uniqueness. Tests cover access matrix, isolation/non-disclosure, relationship validation, normalization/search, warnings, pagination, deleted rows, and PostgreSQL concurrency. Do not implement billing, other Phase 4 domains, or frontend. DoD: only when the above behavior, tests, migration and docs validate.

### T4-02 Catalog and designs
Objective: model reusable catalog/design defaults and Shop-owned design records. Dependencies: T4-01. Runtime files: `apps/catalog/{models,migrations,serializers,views,services,storage,tests}`. Implement locked family/variant/style defaults, translations, Shop custom variants/styles, private reusable StyleOption references, Design drafts/immutable published versions, selection/reference snapshots, independent copies, and pagination. Shop publication is limited to active ADMIN or active STAFF assigned `STITCHING` (Tailor is not a role); global templates publish only through Main Supplier authority. DB: ownership, status, uniqueness, translation, image/source and index constraints. API: scoped catalog/design CRUD, publish/copy/archive/reference endpoints. Security: uniform Shop scoping/private authorized streams; no public media URLs. Tests: ownership, non-disclosure, publication, immutable history, image handling and PostgreSQL publish/selection races. Out of scope: Work linkage, measurements/materials, billing and frontend. DoD: only after migration, full test suite, docs and publication validation.

### T4-03 Measurements and materials
Objective: add Shop-scoped person measurement profiles and immutable history, plus a minimal Shop-owned Material/Fabric reference catalog. Dependencies: T4-01 Clients/Related Persons, T4-02 GarmentFamily/Variant, active Phase 3 Shop context/isolation and Work Function foundation. Runtime files are under `apps/catalog/`; do not create `backend/apps/catalog/`.

Measurement entities: global or Shop-owned `MeasurementDefinition`; locale translations; family and optional variant mappings; `MeasurementProfile` owned by exactly one Client XOR RelatedPerson; immutable, versioned `MeasurementSet`; Decimal `MeasurementValue`; immutable localized label snapshots. Profiles and histories for a Related Person remain independent of the Primary Client's profile; the existing RelatedPerson→Primary Client relationship remains the future billing-owner link. Do not add a display-name, billing, Work, or order snapshot field.

Seed only these approved mappings: Men's Shirt — Full Length, Shoulder Width, Chest, Waist, Sleeve Length, Neck, Hip/Seat, Bicep, Armhole, Cuff/Wrist; Kuwaiti Dishdasha — Full Length, Shoulder, Chest, Sleeve Length, Neck, Waist, Hip/Seat, Upper Arm/Bicep, Cuff/Sleeve Opening, Armhole, Shoulder Slope/Posture, Placket Length, Side Slit Height. Use stable codes and English canonical labels; locale support is en, ar-KW, bn, ur with English fallback. Do not seed guessed Abaya/Darraa templates or Pant/Thobe aliases.

Values may be partial. Each value requires an explicit Decimal and `INCH` or `CM`; no default, conversion, or BODY/GARMENT/FINISHED distinction. Sets/values/snapshot labels cannot be edited or deleted; corrections create a new version. Copying creates independent value rows and records `copied_from`. Compare only within the same profile; return a difference only when units match, and return both raw values/units without conversion when they differ. Historical labels stay stable if reusable definition translations later change. Shop custom definitions are reusable only inside the Shop and mapped family/optional variant; require an English canonical label; archive rather than delete or restore.

Materials in T4-03: only UUID, required Shop, name, optional Shop-local code, description, ACTIVE/ARCHIVED state, audit fields and timestamps. T4-03A is a later additive task and does not rewrite this completed contract.

MEASUREMENT-E2E-01 adds a frontend integration slice under separate authorization. It uses backend Family/Variant data, the actual ordered Family → Option Group mapping, Shop/global Design APIs, and the immutable measurement APIs. It does not introduce a Work aggregate, material reservation, or production workflow. The additive `catalog.0012_seed_mens_shirt_design_defaults` data migration maps the approved Men’s Shirt sections (Sleeve, Collar, Cuff, Pocket, Placket, Embroidery, Color) and supplies Classic Formal Shirt, Smart Casual Shirt, and Modern Evening Shirt as published global defaults for Standard Shirt.

API: `/api/v1/shops/{shop_id}/measurement-definitions/` (GET/POST), definition detail (GET/PATCH), and `/archive/`; client-nested `/clients/{client_id}/measurement-profiles/`, profile detail, `/sets/` GET/POST, set detail GET, set `/copy/` POST, and profile `/compare/` GET; Related Person equivalents nested under `/clients/{client_id}/related-persons/{related_person_id}/measurement-profiles/`; `/materials/` (GET/POST), material detail (GET/PATCH), and `/archive/` POST. No hard-delete or Work-specific route. Use page-number pagination, stable ordering, selected-Shop filtering, and uniform non-disclosing 404 for foreign/missing nested records.

Permissions: Main Supplier must select a Shop path and is scoped to that Shop's private records; may read/manage where the rule allows. ADMIN has full measurement and custom-definition management and material read/write/archive. Active STAFF with `MEASUREMENT` may read/create profiles/sets, copy/compare, create definitions and edit only own safe custom-definition metadata, but may not archive definitions. STAFF without the function and VIEWER have no measurement PII/history access. For Materials, STAFF and VIEWER are read-only and require no Work Function. Inactive/removed memberships are denied; function eligibility never replaces role/context authorization.

DB: additive `apps/catalog/migrations/` migrations only. Check owner XOR, one value per definition/set, unique profile identity, unique profile version, mapping and translation uniqueness, valid unit/status, code uniqueness, same-family variant and same-Shop/global links, and protected historical FKs. Cross-table Shop invariants are revalidated in services. Lock order is Shop → measured person/profile → set; serialize profile, version/copy, and custom-code creation and retain PostgreSQL uniqueness as final guard. Seed migration is deterministic/repeatable. Tests cover exact seeds/no guessed families, translation fallback/snapshot, partial Decimal values/units, immutable history/copy/compare, permissions, nested-owner checks, both Shop-isolation directions, materials and independent-connection concurrency.

Validation: focused PostgreSQL tests, full PostgreSQL suite, repository validator and validator tests, Django system and production deploy checks, migration drift, OpenAPI, Black, Flake8, and `git diff --check`. Update API/database/security/business/architecture/state/handoff/schema/changelog documentation. Do not modify frontend, implement T4-04 or Phase 5, or deploy. DoD: only after the above constraints, tests, generated schema and exact-SHA CI pass; then stop without starting another task.

### T4-04 Work aggregate and workflow state
Objective: create work/order aggregate and approved states. Dependencies: T4-01–03 and completed Phase 3 T3-04A–T3-04C/T3-05 prerequisites. Files: `backend/apps/works/{models,migrations,serializers,views,tests}`. Steps: model client/design/measurement/material links, stable searchable Work number, status, due dates, and priority `Normal|Urgent|Very Urgent`; implement only Request, Cutting, Stitching, Check, Finishing, QC, Completed transitions. Do not model TAILOR/SALESMAN/CASHIER as access roles. Workflow eligibility/assignment must use authorized Shop context + membership Access Role + applicable Work Function + explicit service policy. A Work Function alone never authorizes a transition. Specify stage-to-function mapping in this task; if Check requires an additional catalog function, record BUSINESS DECISION REQUIRED rather than inventing one. Keep workflow fixed and do not add a per-Shop workflow builder. Expose upcoming/due-soon/today/overdue as derived date indicators, not workflow states. DB: state/index/constraints. API: work CRUD/transition/search endpoints. Security: shop scope/transition permissions. Tests: valid/invalid transitions, role/function/assignment matrix, denial when membership/function/context is absent or foreign, priority, due-date derivation/cutoff decision gate, Work search and cross-Shop denial. DoD: persisted workflow and priority without unapproved workflow states or function-based permission escalation.

### T4-05 Service layer and concurrency
Objective: enforce domain rules outside views. Dependencies: T4-04. Steps: transactional services, select-for-update/version checks, idempotent transitions, audit events, validation and conflict errors. DB: transactions/unique constraints. API: service error mapping. Tests: races, retries, duplicate transitions, rollback. DoD: views cannot bypass rules.

### T4-06 Domain integration validation
Objective: verify the complete shop workflow before billing. Dependencies: T4-05. Steps: API integration scenario from request to completed; verify data links and isolation. DoD: documented evidence.

## T4-03A — Inventory & Stock Foundation (separately approved)

Objective: extend canonical Shop-owned Material records with explicit inventory classification, safe balance, and immutable stock ledger. Existing Materials keep UUID and receive no inferred category/unit or opening stock; inventory enablement is explicit and initializes zero balance. Categories: FABRIC/BUTTON/ZIP/THREAD/HOOK/INTERLINING/OTHER. Units: METRE/YARD/PIECE/ROLL; no conversions, fractional PIECE/ROLL, or negative stock. Main Supplier must select a Shop; ADMIN manages and adjusts; STAFF/VIEWER read active inventory only. Opening, stock-in, and reasoned adjustments append ledger entries atomically with balance changes. Archive requires zero on-hand and reserved and preserves readable history. No measurement-history change, Work, reservation/consumption API, procurement, costing, frontend, or deployment.

Files: additive code/migration/tests under `apps/catalog/`, API and generated schema artifacts, validator allowance gated on explicit T4-03A confirmation in current state/handoff, and canonical inventory documentation. Validation: focused API/model tests, PostgreSQL concurrency (oversell, stock-in, adjustment, enablement, archive race), T4-03 measurement regressions, full PostgreSQL suite, project validator/tests, Django/deploy checks, migration drift, OpenAPI/schema parity, Black/Flake8, `git diff --check`. DoD requires verified results and state/handoff update; stop afterward without T4-04.

## 13. Task Dependency Graph
`T4-01 → T4-02 → T4-03 → T4-03A → T4-04 → T4-05 → T4-06`.
## 14. Expected Files / Folders
For T4-01, use runtime `apps/clients/`, `backend/config/settings/base.py`, and `core/urls.py`, with migrations, serializers/views/URLs, tests, and domain docs. Do not create a shadow `backend/apps/clients` package or relocate existing apps. Later task paths are planned separately and must follow the live repository's Django import structure when each task is activated.
## 15. Expected New Files
Clients, related persons, catalog/designs, measurements, materials, works, workflow services and tests.
## 16. Expected Modified Files
Settings/apps/URLs, shared audit/storage interfaces, API/docs.
## 17. Database Changes
All domain tables, FKs, indexes, status/quantity constraints, versions, and audit references.
## 18. Migration Requirements
Review every migration, test empty and representative databases, preserve shop scope, document data backfills.
## 19. API Changes
CRUD and transition APIs with serializer validation, pagination, filtering, schema, and authorization.
## 20. Backend Changes
Models, services, transactions, permissions, querysets, API, audit hooks.
## 21. Frontend Changes
None.
## 22. Security Requirements
PII minimization, shop isolation, transition authorization, safe file references, IDOR tests.
## 23. Tenant / Permission Requirements
Every query and service receives/derives authorized shop context; supplier visibility follows policy.
## 24. Validation Requirements
End-to-end workflow, invalid links, invalid transitions, concurrency, duplicate requests, cross-shop attacks.
## 25. Testing Requirements
Unit, API, integration, transaction, workflow, permission, isolation, regression tests.
## 26. Error / Failure Handling
Atomic operations, conflict responses, invalid-state errors, retry-safe services, no partial aggregate writes.
## 27. Documentation Updates
Database/API/architecture/security/state/handoff/changelog/decisions.
## 28. Git Checkpoint Guidance
Checkpoint each domain task; never push.
## 29. Handoff Requirements
Record entity relationships, states/transitions, constraints, tests, and next task.
## 30. Phase Validation Checklist
- [ ] Client/related-person rules
- [ ] Designs/measurements/materials connected
- [ ] Workflow states persisted
- [ ] Services transactional
- [ ] Concurrency and isolation tested
## 31. Definition of Done
An authorized shop can take work from client request through Completed with all required links and no cross-shop access.
## 32. Common Implementation Mistakes
Fat views, free-form status edits, missing transactions, nullable links, floating-point money/quantity, unscoped search, no concurrency control.
## 33. Rollback / Recovery Notes
Use corrective migrations and data repair scripts; freeze transitions if corruption is detected; preserve audit evidence.
## 34. Phase Implementation Prompt
**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 4 only; it does not authorize T4-01 through T4-06. Before each task, present that task's objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. After confirmation, implement only that task, run its validation, update documentation, report the result, and stop. Do not begin the next task or Phase 5 automatically. Preserve the approved workflow and architecture.
## 35. Phase Completion Report Format
`Phase: 4` / `Entities:` / `Workflow:` / `Migrations:` / `Concurrency:` / `Tests:` / `Docs:` / `Next task:`.
