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
Objective: persist measurement sets and fabric/material records tied to client/work context. Dependencies: T4-01/T4-02. Files: `backend/apps/catalog/{models,migrations,serializers,views,tests}`. Steps: define extensible measurement templates (initial examples may include Shirt, Thobe, Pant, Abaya), typed values/units, immutable measurement versions, history and comparison-ready current/previous/difference data, plus material quantity/status/reservation rules. DB: constraints/indexes/decimal handling. API: create/update/read/history/compare contracts. Security: scope/PII. Tests: units, template evolution, immutable history, comparison, ownership. DoD: history is preserved and usable without hard-coding the template catalog.

### T4-04 Work aggregate and workflow state
Objective: create work/order aggregate and approved states. Dependencies: T4-01–03 and completed Phase 3 T3-04A–T3-04C/T3-05 prerequisites. Files: `backend/apps/works/{models,migrations,serializers,views,tests}`. Steps: model client/design/measurement/material links, stable searchable Work number, status, due dates, and priority `Normal|Urgent|Very Urgent`; implement only Request, Cutting, Stitching, Check, Finishing, QC, Completed transitions. Do not model TAILOR/SALESMAN/CASHIER as access roles. Workflow eligibility/assignment must use authorized Shop context + membership Access Role + applicable Work Function + explicit service policy. A Work Function alone never authorizes a transition. Specify stage-to-function mapping in this task; if Check requires an additional catalog function, record BUSINESS DECISION REQUIRED rather than inventing one. Keep workflow fixed and do not add a per-Shop workflow builder. Expose upcoming/due-soon/today/overdue as derived date indicators, not workflow states. DB: state/index/constraints. API: work CRUD/transition/search endpoints. Security: shop scope/transition permissions. Tests: valid/invalid transitions, role/function/assignment matrix, denial when membership/function/context is absent or foreign, priority, due-date derivation/cutoff decision gate, Work search and cross-Shop denial. DoD: persisted workflow and priority without unapproved workflow states or function-based permission escalation.

### T4-05 Service layer and concurrency
Objective: enforce domain rules outside views. Dependencies: T4-04. Steps: transactional services, select-for-update/version checks, idempotent transitions, audit events, validation and conflict errors. DB: transactions/unique constraints. API: service error mapping. Tests: races, retries, duplicate transitions, rollback. DoD: views cannot bypass rules.

### T4-06 Domain integration validation
Objective: verify the complete shop workflow before billing. Dependencies: T4-05. Steps: API integration scenario from request to completed; verify data links and isolation. DoD: documented evidence.

## 13. Task Dependency Graph
`T4-01 → T4-02 → T4-03 → T4-04 → T4-05 → T4-06`.
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
