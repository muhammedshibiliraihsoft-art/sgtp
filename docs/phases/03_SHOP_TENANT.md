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
The Phase 3 foundation through T3-04C is published. T3-04C preserves URL-path Shop context and reusable T3-04 scoped query/object primitives; exact-SHA Project State Validation passed. T3-05 has been explicitly confirmed, implemented, and locally validated; its commit/publication and exact-SHA CI remain pending. T3-05A remains separately gated and unstarted.
## 8. Exact Scope
Main Supplier / Main Admin, Supplier Back Office, Shop, UserShop/membership, roles, context, scoping, authorized Main Supplier visibility, admin/back-office API, isolation tests. External Supplier records are Shop-owned non-user records and are not authenticated participants in this phase.
## 9. Out of Scope
Clients, designs, production, billing, reports, AI, frontend screens.
## 10. Architecture Context
Exactly one Main Supplier / Main Admin owns/oversees multiple Shops. Shop is the tenant/workspace boundary; Shop-scoped records require active membership and object-level authorization. External Suppliers are separate Shop-owned business records, not users, tenants, members, or roles.
## 11. Implementation Sequence
Completed foundation: entity model → membership/roles → T3-02A account/preferences → T3-03 URL context → T3-04 query/object isolation. Current sequence: T3-04A, T3-04B safeguards, T3-04B-USER-SCOPE, and T3-04C Work-Function foundation are published with exact-SHA CI green → T3-05 Shop/API/Admin hardening → T3-05A Staging Backend Foundation. Each task requires separate exact confirmation.
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
Confirmed policy is in `docs/BUSINESS_RULES.md` and `docs/DECISIONS.md`. T3-02A is implemented: public account creation is denied, Main Supplier Admin controls account creation/phone lifecycle and Shop defaults, and nullable preferences/settings are persisted. Shop Admin settings authority is not granted; currency changes after financial history and other later-phase questions remain deferred or `BUSINESS DECISION REQUIRED` as recorded canonically.
Historical scope note: this completed T3-02A implementation preserved required email, which remains current code behavior; the later approved target now makes email optional for normal Users and assigns that change to T3-04A. Do not retroactively mark T3-02A as implementing the new target.

### T3-03 Tenant context — complete
Objective: resolve one authorized active Shop per request. Dependencies: completed T3-02, T3-02-REMEDIATION, and T3-02A. Files: request-local context resolver, reusable DRF context base, Shop URL pattern, context API/test coverage. Steps: after DRF authentication and before view permissions/handler, resolve `/api/v1/shops/{shop_id}/...`, attach the trusted Shop and actor-specific membership context, and support explicit Main Supplier selection without synthetic membership. Use no Django middleware, ambient mutable globals, or alternate Shop selectors. API: `GET /api/v1/shops/{shop_id}/context/`; uniform non-disclosing 404 for denied/unavailable Shop context, with existing 401 authentication behavior preserved. Security: password-change gate, URL spoofing resistance, request-local state. Tests: malformed/missing/foreign/inactive/deleted paths, lifecycle and role cases, multi-Shop selection, and context leakage. T3-04 owns business object/queryset isolation. DoD: deterministic authorized URL-path context; no claim of full data isolation.
Additional guard: T3-02A locale/appearance preferences and Shop defaults are presentation/configuration only; resolve Shop defaults only after authorization and never infer membership or role from them.

### T3-04 Scoped querysets and object permissions
Status: COMPLETE — reusable isolation foundation implemented and regression-tested; no business-resource modules/endpoints were introduced.
Objective: enforce Shop isolation at backend boundaries. Dependencies: T3-03. Files: `apps/common/views.py`, `core/permissions.py`, and test-only proof coverage. `TenantScopedMixin` requires trusted `request.shop_context`, verifies actor/URL/compatibility-alias consistency, scopes the queryset, and forces ownership from the selected Shop during create/update. `IsTenantMember` requires an object’s Shop to equal the selected context, including for Main Supplier. Missing context/configuration cannot fall back to global rows. No concrete business models exist, so no database index or migration was warranted. Shop-scoped endpoints remain one-Shop scoped; cross-Shop reporting requires a separate explicitly authorized platform path and is not added here. Tests prove Shop A list/count and detail isolation, Main Supplier one-Shop scope, multi-Shop-user isolation, ownership/reparenting safety, missing/mismatched context, and soft-delete exclusion. Future resources must apply same-Shop validation to related IDs and test filter/search/pagination/nested paths as those APIs are introduced. DoD: reusable boundary passes the proof matrix without claiming that unimplemented business endpoints are already isolated.
Include locale/settings endpoints and ensure language, theme, timezone, and currency presentation do not bypass the same object/tenant authorization. Ordinary-user Shop visibility is now approved as membership-authorized (BR-SHOP-008); its implementation belongs to T3-04B/T3-05, not the completed T3-04 primitive task.

### T3-04A — Global identity, User ID, and authentication remediation (PUBLISHED)
Objective: implement the approved permanent User ID and normal/admin-grade contact and recovery contracts without losing existing account identity or authentication protections. Why: each Shop account requires stable identity while normal Shop staff may have no email/phone. Dependencies: completed T3-04 and rebaseline decision record; exact task confirmation was received. Current implementation retains `USERNAME_FIELD=email` for Django Admin/CLI compatibility while API login resolves User ID/email/phone. `first_name` is required and `last_name` optional; display name derives only from those fields. The later T3-04B-USER-SCOPE decision requires separate Shop-owned accounts; it supersedes the earlier multi-Shop identity assumption, not T3-04A's identifier/authentication contracts.
Files/areas: `apps/accounts/` User/manager/authentication/serializers/views/admin/migrations/tests and targeted API/security/database docs. Database: analyze existing production/fixture data first; plan a forward migration/backfill preserving UUID, password hashes, email, memberships and session semantics; generate globally unique User IDs; do not fabricate contact values or duplicate accounts. API: universal `identifier + password` accepts User ID and registered email/phone; preserve existing email-login compatibility. Normal User email/phone optional; active Shop ADMIN and Main Supplier require both. Assess whether existing first/last name fields satisfy the minimal display-name contract before adding schema. Admin promotion/contact-removal checks integrate with T3-04B; required contacts cannot be removed while the User is active ADMIN in any Shop. Password reset for no-email Users is controlled global account administration; Shop Admin cannot reset global credentials. Security: preserve JWT, CSRF, refresh rotation/blacklist, revocation, throttling and safe errors; no OTP/SMS/WhatsApp/2FA. Tests: User ID uniqueness/login, normal no-email account, admin-grade contact validation and contact-removal guard, old-account migration, login compatibility, password/recovery/session regression. Validation: migration upgrade/replay, full auth suite, schema checks, repository validator. DoD: target identity is implemented with no identity/session loss and all compatibility/security tests pass.

### T3-04B — Membership, ADMIN invariant, and lifecycle authority remediation (PUBLISHED; original task)
Objective: enforce membership/Admin invariants under the then-approved global-identity model. This historical plan was implemented and published by T3-04B-REMEDIATION-01; its multi-Shop User assumption is superseded by T3-04B-USER-SCOPE below. The one-to-two active ADMIN invariant, Main Supplier-only ADMIN hierarchy changes, membership lifecycle, capacity, context, and isolation safeguards remain in force.

### T3-04B-USER-SCOPE — Shop-owned ordinary account remediation (PUBLISHED)
This completed task introduces immutable owning-Shop identity for ordinary Users, same-Shop membership consistency, Shop-scoped account creation and reset authority, and atomic creation of a Shop with a new first ADMIN account. It preserves UUID/JWT identity, password/session protections, existing membership/Admin invariants, and the T3-03/T3-04 security boundaries. Its migration preflights historical memberships (including removed rows), assigns only a uniquely determinable Shop, and stops with actual affected UUIDs for multi-Shop/unowned accounts. This task does not implement Work Functions or broader Shop visibility APIs. Commit `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c` passed GitHub Actions run `36591864481`.

### T3-04C — Membership-scoped Work-Function foundation (PUBLISHED; CI GREEN)
Objective: model and manage zero-to-many approved Work Functions per membership without conflating functions with access roles or permissions. Why: staffing differs across Shops while the V1 workflow remains fixed. Dependencies: published T3-04B safeguards and completed/published T3-04B-USER-SCOPE; exact task confirmation. Files/areas: membership/domain model, services, Shop-local admin/API contracts, migrations/tests and docs. Database: analyze normalized representation, constraints, indexes, history, fresh re-add, inactive preservation and five-second undo semantics; do not choose arrays/JSON/bit flags without implementation analysis. Catalog: SALES, MEASUREMENT, CUTTING, STITCHING, FINISHING, QC, CASHIER only; CHECK-to-function mapping is a Phase 4 decision if needed. Authority: Shop ADMINs manage functions for memberships only in that Shop, including ADMIN memberships; function assignment never grants endpoint permission. Tests: zero/one/many, separate accounts/functions by Shop for the same real-world person, cross-Shop denial, non-permission behavior, inactive/reactivation/undo/removal/fresh re-add lifecycle. Out of scope: workflow stages, work assignment, builder, custom catalog. DoD: membership function foundation and lifecycle are isolated, auditable and regression-tested.

### T3-05 Back-office/shop APIs and admin
Status: explicitly confirmed, implemented, and locally validated; commit/publication and exact-SHA CI remain pending. Implement only this task. T3-05A remains unstarted and unauthorized.
Objective: expose and harden approved Supplier/Shop management only after T3-04A, T3-04B and T3-04C pass. Dependencies: completed T3-01–T3-04C; exact task confirmation. Files: Shop/membership views, serializers, URLs, services, Django Admin, tests, OpenAPI and docs. Apply BR-SHOP-007–010 and BR-MEM-009–012. Preserve `/api/v1/tenants/` compatibility unless separately approved. Scope includes authorized Shop list/detail/profile/stats, Main Supplier-only settings/lifecycle/slug-domain management, Shop ADMIN normal-member management, exact User-ID member lookup, actor attribution, concurrency/undo handling, and hardened Django Admin. Enforce `max_users >= user_count` on updates and match API/Admin behavior. Do not add generic Supplier CRUD or expose Supplier deletion; disable delete affordances. Treat Supplier `is_active` as hidden/read-only/deferred if it has no defined authorization effect. No ordinary Shop DELETE; deactivation preserves Shop data and memberships; do not invent final archive semantics. Database: no migration assumption; add only if the individually confirmed task and repository analysis require one. Tests include API/Admin parity, tenant isolation, OpenAPI actions, max_users lower-bound, and race/error cases. DoD: target management contracts are enforced and tested after prerequisite remediations.

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
`T3-01 (complete) → T3-02 (complete) → T3-02-REMEDIATION (closed) → T3-02A (complete) → T3-03 (complete) → T3-04 (complete) → T3-04A (published) → T3-04B-REMEDIATION-01 (published) → T3-04B-USER-SCOPE (published; exact-SHA CI green) → T3-04C (published; exact-SHA CI green) → T3-05 → T3-05A`.
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
