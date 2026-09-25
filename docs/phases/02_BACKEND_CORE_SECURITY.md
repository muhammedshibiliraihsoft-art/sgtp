# Phase 2 — Backend Core + Security

## 1. Phase Overview
Harden the backend API/security foundation after Phase 1.
## 2. Phase Objective
Deliver versioned DRF infrastructure, secure JWT behavior, permissions primitives, error handling, rate limiting, schema, and health checks.
## 3. Business Purpose
Ensure every future shop/business operation has consistent secure API behavior.
## 4. Technical Purpose
Standardize authentication, authorization hooks, errors, throttling, observability, and API contracts.
## 5. Preconditions
Phase 1 DoD passed; explicit `CONFIRM PHASE 2`; read all required context and this file.
## 6. Dependencies
Phase 1 settings, User, PostgreSQL, tests, and migration baseline.
## 7. Current Repository Assumptions
Starter has DRF, SimpleJWT, schema routes, session auth, and incomplete blacklist/CORS configuration.
## 8. Exact Scope
DRF defaults, CORS, `/api/v1/`, JWT rotation/reuse policy, permissions interfaces, throttling, exceptions, OpenAPI, health, and security validation.
## 9. Out of Scope
Shop model, business entities, frontend, AI, billing, production deployment.
## 10. Architecture Context
Security is backend-enforced; frontend visibility is never the authorization boundary.
## 11. Implementation Sequence
API baseline → JWT → permission/tenant interfaces → errors/throttling → docs/health → security tests.
## 12. Detailed Task List

### B2-01 DRF API baseline
Objective: establish versioned API settings and response conventions. Why: later clients need stable contracts. Dependencies: Phase 1. Create/modify: target `backend/config/urls.py`/API modules and current starter `core/urls.py` only during transition. Steps: define `/api/v1/`, pagination, filtering, request IDs, schema conventions; preserve compatibility deliberately. DB: none. API: versioning/error envelope decision. Security: deny-by-default. Tests: routing, auth defaults, pagination. Validation: schema and checks. Docs: API/state/handoff. DoD: stable baseline.

### B2-02 JWT lifecycle
Objective: secure access/refresh, rotation, reuse detection, logout/revocation. Why: identity must be reliable. Dependencies: B2-01. Create/modify: target `backend/apps/accounts/`, `backend/core/services/`, auth settings/models/migrations/tests. Steps: choose token family/revocation storage, configure access-token lifetimes, rotation, refresh-token reuse detection, HttpOnly/Secure refresh-cookie handling, blacklist, replay handling, logout; never log tokens. DB: token/revocation tables if approved. API: login/refresh/logout contract. Security: replay, brute force, disabled users. Tests: happy/expired/rotated/reused/revoked tokens and cookie flags. Validation: migration and API tests. Docs: security/API. DoD: documented lifecycle passes.

### B2-03 Permission and tenant-scope interfaces
Objective: provide reusable object-permission and queryset hooks without implementing shops. Dependencies: B2-01. Create/modify: permissions/services/base viewsets/tests. Steps: define policy interfaces, deny-by-default behavior, owner/object checks, future tenant context contract. DB: none. API: 403/404 policy. Security: no IDOR. Tests: anonymous/authenticated/forbidden/object cases. DoD: reusable primitives documented.

### B2-04 Exceptions, throttling, CORS, health
Objective: make failures safe and operations observable. Dependencies: B2-01/B2-02. Create/modify: exception handler, throttles, health views, settings. Steps: normalize validation/auth/server errors, rate-limit auth/sensitive endpoints, configure explicit CORS, add liveness/readiness checks. DB: readiness only. API: health/error contracts. Security: avoid stack traces/secrets. Tests: status/envelope/throttle/CORS/health. DoD: safe predictable behavior.

### B2-05 API documentation and security validation
Objective: publish accurate OpenAPI and run security regression checks. Dependencies: B2-02 to B2-04. Create/modify: schema annotations/tests/docs. Steps: document auth/errors/pagination, run deploy checks, dependency/security scans, verify no secret leakage. DoD: docs and tests match.

## 13. Task Dependency Graph
`B2-01 → B2-02 → B2-03 → B2-04 → B2-05`.
## 14. Expected Files / Folders
Target `backend/config/`, `backend/apps/accounts/`, `backend/core/{permissions,exceptions,services}/`, shared API/security modules, tests, docs; current root-level starter paths are transition inputs only.
## 15. Expected New Files
Permission, exception, throttle, health, token/revocation modules and tests as required.
## 16. Expected Modified Files
Settings, URLs, auth views/serializers, requirements, API docs.
## 17. Database Changes
Only token/revocation/security support tables approved by B2-02.
## 18. Migration Requirements
Review and test all auth/security migrations from an empty DB.
## 19. API Changes
Versioning, auth lifecycle, health, errors, schema, and throttling behavior.
## 20. Backend Changes
DRF settings, permissions, exceptions, throttles, health, auth services.
## 21. Frontend Changes
None; only document the future client contract.
## 22. Security Requirements
Secure JWT lifecycle, deny-by-default permissions, CORS allowlist, throttling, safe errors, no token logging.
## 23. Tenant / Permission Requirements
Provide interfaces; do not create Shop/Tenant business implementation.
## 24. Validation Requirements
Django checks, API tests, schema generation, deploy checks, security scans.
## 25. Testing Requirements
Auth lifecycle, replay, IDOR, permissions, throttling, CORS, errors, health, regression.
## 26. Error / Failure Handling
Consistent errors, safe 5xx, dependency outage behavior, token replay rejection.
## 27. Documentation Updates
API, security, architecture, state, handoff, changelog, decisions.
## 28. Git Checkpoint Guidance
Local checkpoint per B2 task; never push.
## 29. Handoff Requirements
Record token policy, endpoint changes, migrations, tests, and next task; stop.
## 30. Phase Validation Checklist
- [ ] API versioned
- [ ] JWT lifecycle tested
- [ ] Permissions deny by default
- [ ] Errors/throttles/CORS/health verified
- [ ] OpenAPI/security docs current
## 31. Definition of Done
Backend core security contracts are tested and ready for shop tenancy.
## 32. Common Implementation Mistakes
Trusting frontend roles, permissive CORS, logging tokens, ignoring refresh replay, returning 500 for validation, skipping object tests.
## 33. Rollback / Recovery Notes
Revert settings/code; use corrective migrations; revoke token families if security behavior changes.
## 34. Phase Implementation Prompt
**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 2 only; it does not authorize B2-01 through B2-05. Before each task, present that task's objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. After confirmation, implement only that task, run its validation, update documentation, report the result, and stop. Do not begin the next task or Phase 3 automatically. Preserve architecture.
## 35. Phase Completion Report Format
`Phase: 2` / `Tasks:` / `Files:` / `API/security:` / `Migrations:` / `Tests:` / `Issues:` / `Docs:` / `Next task:`.
