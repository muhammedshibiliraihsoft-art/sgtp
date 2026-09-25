# Phase 3 — Shop / Tenant

## 1. Phase Overview
Implement the supplier, back office, shop, membership, role, and isolation foundation.
## 2. Phase Objective
Make each shop an isolated business workspace with controlled supplier cross-shop visibility.
## 3. Business Purpose
Allow a supplier to manage shops while preventing unauthorized cross-shop access.
## 4. Technical Purpose
Implement tenant context, membership, scoped querysets, object permissions, constraints, and tests.
## 5. Preconditions
Phase 2 passed; explicit `CONFIRM PHASE 3`; product definition and architecture read.
## 6. Dependencies
User/auth, permission primitives, PostgreSQL, service boundaries.
## 7. Current Repository Assumptions
Starter Tenant exists but User has no membership; BaseModelWithTenant is nullable; no isolation mixin exists.
## 8. Exact Scope
Supplier, Shop, UserShop/membership, roles, context, scoping, supplier visibility, admin/back-office API, isolation tests.
## 9. Out of Scope
Clients, designs, production, billing, reports, AI, frontend screens.
## 10. Architecture Context
Supplier owns/oversees shops; shop-scoped records require active membership and object-level authorization.
## 11. Implementation Sequence
Entity model → membership/roles → context → query/permission enforcement → APIs/admin → isolation tests.
## 12. Detailed Task List

### T3-01 Supplier and Shop entities
Objective: define supplier/shop data model and ownership. Why: current Tenant is not the approved hierarchy. Dependencies: Phase 2. Files: target `backend/apps/shops/{models,migrations,admin,tests}` and transition adapters for current `apps/tenants/`. Steps: decide Tenant rename/compatibility, add Supplier/Shop identities, unique constraints, active status, audit fields. DB: models/indexes/constraints. API: internal/admin contract. Security: ownership. Tests: constraints/soft delete. Docs: database/architecture. DoD: approved model.

### T3-02 User-Shop membership and roles
Objective: connect users to shops and supplier roles. Dependencies: T3-01. Files: membership model, role constants/permissions, serializers/tests. Steps: model membership/status/role; prevent duplicate membership; define supplier cross-shop role; enforce inactive shop/user. DB: FK/index/unique constraints. API: membership management. Security: least privilege. Tests: role matrix. DoD: explicit role policy.

### T3-03 Tenant context
Objective: resolve active shop safely per request. Dependencies: T3-02. Files: context middleware/service/request helpers/tests. Steps: define header/route/session strategy; validate membership; avoid ambient mutable globals; support supplier selected shop with authorization. API: context errors. Security: spoofing resistance. Tests: missing/invalid/inactive/cross-shop context. DoD: deterministic context.

### T3-04 Scoped querysets and object permissions
Objective: enforce isolation at backend boundaries. Dependencies: T3-03. Files: managers/querysets, permissions, base viewsets, tests. Steps: filter all shop-scoped reads/writes; deny foreign IDs; define supplier reporting visibility; require explicit unscoped access for platform-only records. DB: indexes. API: 403/404 policy. Tests: Shop A never sees Shop B. DoD: isolation proven.

### T3-05 Back-office/shop APIs and admin
Objective: expose only approved supplier/shop management. Dependencies: T3-01–04. Files: views/serializers/URLs/admin/tests/docs. Steps: implement CRUD, membership actions, activation/deactivation, audit. DB: migrations already defined. API: contracts/schema. DoD: API and isolation tests pass.

## 13. Task Dependency Graph
`T3-01 → T3-02 → T3-03 → T3-04 → T3-05`.
## 14. Expected Files / Folders
Target `backend/apps/shops/`, `backend/apps/accounts/`, `backend/core/{tenancy,permissions,services}/`, migrations/tests; current `apps/tenants/` and `apps/accounts/` are starter transition inputs only.
## 15. Expected New Files
Shop/membership models, role policy, context/scoping modules, tests.
## 16. Expected Modified Files
Existing Tenant/User models, base querysets, URLs, settings, admin, docs.
## 17. Database Changes
Supplier/shop/membership tables, FKs, unique constraints, active flags, indexes, migration data strategy.
## 18. Migration Requirements
Preserve existing tenant data or document mapping; test forward migration and rollback recovery.
## 19. API Changes
Supplier/back-office/shop/membership/context endpoints with schema and authorization.
## 20. Backend Changes
Models, services, querysets, permissions, serializers, views, admin, audit hooks.
## 21. Frontend Changes
None; document context contract only.
## 22. Security Requirements
Backend isolation, role least privilege, no IDOR, inactive membership rejection, audit membership changes.
## 23. Tenant / Permission Requirements
Shop-scoped by default; supplier cross-shop only through explicit role/policy; no frontend-only enforcement.
## 24. Validation Requirements
Cross-shop matrix, supplier visibility, inactive access, direct-ID attacks, pagination/filter leakage.
## 25. Testing Requirements
Model constraints, membership roles, context, queryset, object permissions, API and regression tests.
## 26. Error / Failure Handling
Fail closed for missing context, unauthorized shop, deleted/inactive membership, and stale selections.
## 27. Documentation Updates
Architecture, database, security, API, state, handoff, changelog, decisions.
## 28. Git Checkpoint Guidance
Checkpoint each T3 task; never push.
## 29. Handoff Requirements
Record role matrix, context strategy, migrations, isolation evidence, and next task.
## 30. Phase Validation Checklist
- [ ] Supplier/shop model approved
- [ ] Membership/roles tested
- [ ] Context deterministic
- [ ] Querysets scoped
- [ ] Shop A cannot access Shop B
## 31. Definition of Done
Supplier and shop boundaries are persisted, authorized, tested, and ready for business records.
## 32. Common Implementation Mistakes
Nullable scope, trusting `shop_id` from client, filtering only list views, leaking counts/search/order, conflating supplier and shop roles.
## 33. Rollback / Recovery Notes
Use data migration rollback plan; disable affected endpoints if isolation regression appears; revoke access changes safely.
## 34. Phase Implementation Prompt
**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 3 only; it does not authorize T3-01 through T3-05. Before each task, present that task's objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. After confirmation, implement only that task, run its validation, update documentation, report the result, and stop. Do not begin the next task or Phase 4 automatically. Preserve the approved shop-isolation architecture.
## 35. Phase Completion Report Format
`Phase: 3` / `Tasks:` / `Role matrix:` / `Migrations:` / `Isolation tests:` / `API:` / `Docs:` / `Next task:`.
