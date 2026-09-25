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
Phase 3 isolation DoD passed; explicit activation; all required documents read.
## 6. Dependencies
Shop context/membership, permissions, shared models, PostgreSQL.
## 7. Current Repository Assumptions
Only generic accounts/tenants exist; no business modules or services exist.
## 8. Exact Scope
Clients, family/related persons, catalog/designs, measurements, materials, works/orders, workflow services, indexes, constraints, concurrency.
## 9. Out of Scope
Billing, PDF/report generation, AI integrations, frontend screens, production deployment.
## 10. Architecture Context
Every record is shop-scoped; service methods are the business boundary; transitions are explicit and audited.
## 11. Implementation Sequence
Clients → related persons → catalog/designs → measurements → materials → work aggregate → workflow services → APIs/tests.
## 12. Detailed Task List

### T4-01 Clients and related persons
Objective: model shop-scoped clients and approved related-person relationships. Dependencies: Phase 3. Files: `backend/apps/clients/{models,migrations,serializers,views,tests}`. Steps: define identity/contact fields, soft deletion, uniqueness, relationship rules, privacy. DB: FKs/indexes/constraints. API: CRUD/search. Security: shop scope/PII. Tests: isolation/validation. DoD: records are safely managed.

### T4-02 Catalog and designs
Objective: model reusable/catalog designs and shop-owned design records. Dependencies: T4-01. Files: `backend/apps/catalog/{models,migrations,serializers,views,tests}`. Steps: define ownership, versions/status, media references without implementing storage, design-to-work link. DB: indexes/status constraints. API: CRUD/version contract. Security: shop scope. Tests: ownership/version rules. DoD: designs connect to work.

### T4-03 Measurements and materials
Objective: persist measurement sets and fabric/material records tied to client/work context. Dependencies: T4-01/T4-02. Files: `backend/apps/catalog/{models,migrations,serializers,views,tests}`. Steps: define typed measurement values/units/versioning and material quantity/status/reservation rules. DB: constraints/indexes/decimal handling. API: create/update/read contracts. Security: scope/PII. Tests: units/versions/ownership. DoD: data is consistent and usable.

### T4-04 Work aggregate and workflow state
Objective: create work/order aggregate and approved states. Dependencies: T4-01–03. Files: `backend/apps/works/{models,migrations,serializers,views,tests}`. Steps: model client/design/measurement/material links, identifiers, status, due dates; implement only Request, Cutting, Stitching, Check, Finishing, QC, Completed transitions; define allowed roles and terminal behavior. DB: state/index/constraints. API: work CRUD/transition endpoints. Security: shop scope/transition permissions. Tests: valid/invalid transitions. DoD: persisted workflow.

### T4-05 Service layer and concurrency
Objective: enforce domain rules outside views. Dependencies: T4-04. Steps: transactional services, select-for-update/version checks, idempotent transitions, audit events, validation and conflict errors. DB: transactions/unique constraints. API: service error mapping. Tests: races, retries, duplicate transitions, rollback. DoD: views cannot bypass rules.

### T4-06 Domain integration validation
Objective: verify the complete shop workflow before billing. Dependencies: T4-05. Steps: API integration scenario from request to completed; verify data links and isolation. DoD: documented evidence.

## 13. Task Dependency Graph
`T4-01 → T4-02 → T4-03 → T4-04 → T4-05 → T4-06`.
## 14. Expected Files / Folders
`backend/apps/clients/`, `backend/apps/catalog/`, `backend/apps/works/`, `backend/core/services/`, migrations, serializers/views/URLs, tests, domain docs.
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
