# Phase 3 — Shop / Tenant

## 1. Phase Overview
Implement the single Main Supplier / Main Admin, Supplier Back Office, Shop, membership, role, and isolation foundation.
## 2. Phase Objective
Make each Shop the isolated V1 business workspace/tenant boundary, with controlled Main Supplier cross-Shop visibility.
## 3. Business Purpose
Allow the single Main Supplier / Main Admin to manage Shops while preventing unauthorized cross-Shop access.
## 4. Technical Purpose
Implement tenant context, membership, scoped querysets, object permissions, constraints, and tests.
## 5. Preconditions
Phase 2 passed; explicit `CONFIRM PHASE 3`; product definition and architecture read.
## 6. Dependencies
User/auth, permission primitives, PostgreSQL, service boundaries.
## 7. Current Repository Assumptions
Starter Tenant exists but User has no membership; BaseModelWithTenant is nullable; no isolation mixin exists.
## 8. Exact Scope
Main Supplier / Main Admin, Supplier Back Office, Shop, UserShop/membership, roles, context, scoping, authorized Main Supplier visibility, admin/back-office API, isolation tests. External Supplier records are Shop-owned non-user records and are not authenticated participants in this phase.
## 9. Out of Scope
Clients, designs, production, billing, reports, AI, frontend screens.
## 10. Architecture Context
Exactly one Main Supplier / Main Admin owns/oversees multiple Shops. Shop is the tenant/workspace boundary; Shop-scoped records require active membership and object-level authorization. External Suppliers are separate Shop-owned business records, not users, tenants, members, or roles.
## 11. Implementation Sequence
Entity model → membership/roles → T3-02A account/preferences → URL context → query/permission enforcement → APIs/admin → isolation tests → Staging Backend Foundation.
## 12. Detailed Task List

### T3-01 Supplier and Shop entities
Objective: define the V1 entity and ownership model for exactly one Main Supplier / Main Admin, the Supplier Back Office, and multiple isolated Shops. Shop is the actual tenant/workspace boundary. External Supplier means only a Shop-owned, non-user business-contact record; it is not a tenant, member, login, role, or top-level Supplier entity, and T3-01 must not create external-supplier authentication or a global supplier directory.

Why: the current generic `Tenant` starter model does not establish the approved Shop-based business meaning. Before selecting any compatibility strategy, inspect the existing Tenant model, migration, database assumptions, APIs, tests, and all references. Assess presence, meaning, references, migration impact, preservation/mapping, and rollback/recovery.

Dependencies: Phase 2 and explicit `CONFIRM TASK T3-01` after Phase 3 activation. Files: target `backend/apps/shops/{models,migrations,admin,tests}` and documented transition handling for current `apps/tenants/`. Steps: document the evidence; define Supplier/Main Admin cardinality; define Shop ownership and isolation boundary; define the distinction from External Supplier; then select a technically compatible Tenant strategy only if it preserves approved business meaning. Do not automatically rename, retain, replace, adapt, or reinterpret Tenant. If the choice changes business meaning or approved architecture, stop and report `BUSINESS DECISION REQUIRED`.

DB: only the approved entity/migration strategy; no migration is authorized by this documentation task. API: internal/admin contract only; no external supplier login, portal, API account, or public supplier directory. Security: enforce the future Shop boundary and prevent cross-Shop discovery. Tests: cardinality/ownership constraints, legacy Tenant evidence, preservation/mapping, rollback/recovery, and explicit rejection of cross-Shop access assumptions. Docs: architecture, database, decisions, state, handoff, and changelog. DoD: the entity model and legacy Tenant compatibility strategy are explicitly approved, or the exact unresolved business decision is reported without implementation.
Validation:
- existing Tenant data preservation/mapping strategy
- migration impact
- forward migration verification
- rollback/recovery considerations
- unique constraints
- active/inactive behavior
- audit fields
- soft-delete behavior

### T3-02 User-Shop membership and roles
Objective: connect users to Shops and approved roles under the single Main Supplier / Main Admin model. Dependencies: T3-01. Files: membership model, role constants/permissions, serializers/tests. Steps: model membership/status/role; prevent duplicate membership; define explicit Main Supplier cross-Shop authority; enforce inactive Shop/user. External Suppliers do not receive membership, roles, credentials, or permissions. DB: FK/index/unique constraints. API: membership management only. Security: least privilege. Tests: role matrix and external-supplier non-user boundary. DoD: explicit role policy.

### T3-02A Account, phone, locale, and preference foundation
Objective: establish account and preference contracts needed before Shop context and frontend work, preserving the existing User UUID and required email identity.
Why: later Shop APIs and frontend flows require stable phone, locale, appearance, and Shop-default fields without conflating preferences with authorization.
Dependencies: T3-02 and T3-02-REMEDIATION closed; separate exact `CONFIRM TASK T3-02A`.
Files to create: account/phone/preference services, validators, serializers/views, tests, and migrations only if required by approved schema.
Files to modify: User model/manager/authentication, Shop/Tenant model and API foundation, settings/dependencies, relevant docs.
Implementation steps: apply confirmed rules BR-ACC-002, BR-AUTH-001, BR-PHONE-001–003, BR-PASS-001–004, BR-SHOP-005–007, BR-LOC-003, and BR-UX-001. Keep UUID primary key and required email; normalize international phone numbers to canonical E.164 with a maintained country-aware library; implement one coherent email-or-phone login path; preserve existing users with nullable phone and no fabricated backfill. Reconcile the existing unauthenticated User-create endpoint with the confirmed prohibition on public self-registration; Main Supplier Admin controls global User creation and phone add/change/remove. Generated initial credentials must be secure, exposed once, and changed at first login; recovery is email-only and credential changes revoke refresh sessions. Persist nullable User locale and `system|light|dark` appearance (default `system`); add explicit Shop locale/timezone/currency foundation without inferring timezone/currency or inventing initial values. Main Supplier Admin manages Shop settings. Ensure locale/theme never grant access; use additive, forward-only migrations and preserve memberships.
Database impact: additive nullable/appropriately defaulted fields and constraints only after collision/data review; no fake values.
API impact: account login/password/preferences and Shop settings foundation; document stable errors and authorization prerequisites.
Security impact: hashed passwords only; no plaintext logging; no OTP/SMS/WhatsApp/2FA; throttle auth; authorize Shop before reading its defaults.
Tests required: registration denied to anonymous users and global account creation restricted to Main Supplier Admin; old-user migration/no phone fabrication, UUID/membership preservation, E.164 normalization/unique collisions, same-account email/phone login, generic auth failures, one-time generated credential and first-login password change, email recovery expiry/single-use/account-enumeration behavior, refresh-session revocation after credential change, locale/theme persistence and fallback, Shop settings restricted to Main Supplier Admin, no preference/access coupling.
Validation: migration replay/upgrade, auth and API tests, Django checks, migration drift, repository validator.
Documentation update: architecture, decisions, security, database, API, business rules where applicable, state, handoff, changelog.
Definition of Done: foundation and contracts pass tests without resolving any listed business-policy question by assumption.
Confirmed policy is in `docs/BUSINESS_RULES.md` and `docs/DECISIONS.md`. T3-02A is implemented: public account creation is denied, Main Supplier Admin controls account creation/phone lifecycle and Shop defaults, and nullable preferences/settings are persisted. Decisions still `BUSINESS DECISION REQUIRED` include Shop Admin scoped settings authority and currency changes after financial history, plus unrelated later-phase decisions.

### T3-03 Tenant context
Objective: resolve the active Shop safely per request. Dependencies: T3-02 and completed T3-02A. Files: context middleware/service/request helpers/tests. Steps: implement the approved URL-path tenant context `/shops/{shop_id}/...`; validate membership; avoid ambient mutable globals; support only explicitly authorized Main Supplier-selected Shop access. API: context errors and Shop-scoped URL contracts. Security: path spoofing resistance and object-level authorization. Tests: missing/invalid/inactive/cross-Shop paths and URL-context spoofing. DoD: deterministic, authorized URL-path context.
Additional guard: T3-02A locale/appearance preferences and Shop defaults are presentation/configuration only; resolve Shop defaults only after authorization and never infer membership or role from them.

### T3-04 Scoped querysets and object permissions
Objective: enforce Shop isolation at backend boundaries. Dependencies: T3-03. Files: managers/querysets, permissions, base viewsets, tests. Steps: filter all Shop-scoped reads/writes; deny foreign IDs; define Main Supplier reporting visibility; require explicit unscoped access only for platform-level records. External Supplier records must be scoped to exactly one Shop. DB: indexes. API: 403/404 policy. Tests: Shop A never sees Shop B through direct IDs, lists, search, filters, ordering, pagination, counts, aggregates, autocomplete, or nested relations. DoD: isolation proven.
Include locale/settings endpoints and ensure language, theme, timezone, and currency presentation do not bypass the same object/tenant authorization. Defer unresolved ordinary-user Shop visibility policy rather than inventing it.

### T3-05 Back-office/shop APIs and admin
Objective: expose only approved supplier/shop management. Dependencies: T3-01–04. Files: views/serializers/URLs/admin/tests/docs. Steps: implement CRUD, membership actions, activation/deactivation, audit. DB: migrations already defined. API: contracts/schema. DoD: API and isolation tests pass.

### T3-05A Staging Backend Foundation
Objective: establish the first shared non-production staging backend environment after Phase 3 APIs and isolation are verified.
Why: allow controlled client review and early integration validation through a shared staging environment.
Dependencies: T3-05 accepted; T3-04 isolation evidence; exact task confirmation.
Files to create/modify: staging-specific deployment/configuration templates, health/readiness checks, runbooks, smoke tests, and environment documentation; no secrets.
Implementation steps: connect staging backend at `api-staging.birky.com` to isolated staging PostgreSQL; use demo/test data and separate credentials; display/record non-production identity and optional short build SHA; verify migrations, hosts/CORS, auth/cookies/CSRF/origin behavior in a real browser when frontend is available; define safe reset, logs, health and rollback. Never deploy automatically per commit.
Database/API impact: isolated staging schema/data only; no new business API by virtue of preview.
Security: no production secrets/data; HTTPS and restricted access; secrets out of logs; prove auth/refresh/CSRF boundaries.
Tests/validation: config validation, migration/health checks, smoke/auth checks, isolation checks, safe reset verification.
Documentation: `docs/ENVIRONMENTS.md`, runbook, state/handoff/changelog.
DoD: reviewed and verified staging backend is isolated and operational. Phase 9 later reuses this same staging environment for formal release-candidate validation after appropriate reset/reconfiguration. This task does not authorize deployment without its own confirmation.

## 13. Task Dependency Graph
`T3-01 → T3-02 → T3-02-REMEDIATION → T3-02A → T3-03 → T3-04 → T3-05 → T3-05A`.
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
Shop-scoped by default; Main Supplier cross-Shop access only through explicit backend role/policy; no frontend-only enforcement. External Suppliers never receive system access.
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
- [ ] Single Main Supplier / Main Admin and Shop model approved
- [ ] External Supplier explicitly remains a Shop-owned non-user record
- [ ] Legacy Tenant compatibility strategy approved without unreviewed business reinterpretation
- [ ] Membership/roles tested
- [ ] Context deterministic
- [ ] Querysets scoped
- [ ] Shop A cannot access Shop B
## 31. Definition of Done
Supplier and shop boundaries are persisted, authorized, tested, and ready for business records.
## 32. Common Implementation Mistakes
Nullable scope, trusting `shop_id` from client, filtering only list views, leaking counts/search/order, conflating Main Supplier and External Supplier, treating External Suppliers as users, and mapping legacy Tenant automatically.
## 33. Rollback / Recovery Notes
Use data migration rollback plan; disable affected endpoints if isolation regression appears; revoke access changes safely.
## 34. Phase Implementation Prompt
**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 3 only; it does not authorize any task. Before each task, present its objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for exact `CONFIRM TASK <TASK-ID>`. Implement only that task, validate, update documentation, report, and stop. Never start another task or phase automatically. Preserve the locked Supplier/Shop model. T3-02A must apply the approved account/authentication rules in `docs/BUSINESS_RULES.md`, reconcile the currently public create endpoint, retain UUID identity and all existing JWT protections, and keep preferences presentation-only. Do not add phone OTP/SMS/WhatsApp/2FA. T3-05A Staging Backend Foundation is not Production and requires its own task confirmation.
## 35. Phase Completion Report Format
`Phase: 3` / `Tasks:` / `Role matrix:` / `Migrations:` / `Isolation tests:` / `API:` / `Docs:` / `Next task:`.
