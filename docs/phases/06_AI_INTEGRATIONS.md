# Phase 6 — AI + Integrations

## 1. Phase Overview
Add isolated AI and external integration adapters after core workflows are reliable.
## 2. Phase Objective
Provide controlled assistance without allowing AI/integrations to bypass core rules.
## 3. Business Purpose
Offer optional automation while preserving supplier/shop operational continuity.
## 4. Technical Purpose
Define tools, adapters, permissions, timeouts, validation, webhooks, retries, and isolation.
## 5. Preconditions
Phase 5 reliability DoD passed; explicit activation.
## 6. Dependencies
Service layer, shop context, storage/jobs, audit, security, billing/workflow APIs.
## 7. Current Repository Assumptions
No `ai_agents` or integrations exist; target requires them to remain supporting systems.
## 8. Exact Scope
AI agents/tools, service interfaces, permissions, tenant awareness, timeout/fallback/output validation, integration adapters/webhooks/retries/idempotency.
## 9. Out of Scope
Core workflow redesign, autonomous financial authority, frontend AI screens beyond documented interface.
## 10. Architecture Context
AI calls approved services; it never writes protected domain data directly or changes authorization.
## 11. Implementation Sequence
Interfaces → tool allowlist → agent orchestration → fallback/validation → adapters/webhooks → failure/security tests.
## 12. Detailed Task List

### I6-01 Service and tool interfaces
Objective: define narrow typed interfaces for core actions. Dependencies: Phases 3–5. Files: `ai_agents/`, integration contracts, tests. Steps: allowlist operations, tenant context, actor identity, dry-run/approval semantics. DoD: no direct ORM access.

### I6-02 AI execution controls
Objective: implement timeout, budget, cancellation, fallback, output schema validation, and audit. Dependencies: I6-01. DB: job/audit metadata if approved. API: async status. Security: prompt/data boundaries, least privilege. Tests: timeout, malformed output, denial, retry.

### I6-03 Integration adapters and webhooks
Objective: connect external systems through adapters. Dependencies: I6-01. Steps: signature validation, replay protection, idempotency keys, retry/backoff, dead letters, tenant mapping. Tests: invalid signatures/replays/outages.

### I6-04 Isolation and operational validation
Objective: prove failures cannot break core operations. Dependencies: I6-02/03. Steps: inject provider outage/slow response/malformed payload; verify core workflow remains usable and audit records exist.

## 13. Task Dependency Graph
`I6-01 → I6-02 → I6-03 → I6-04`.
## 14. Expected Files / Folders
`ai_agents/`, `integrations/`, adapters, schemas, jobs, tests, security docs.
## 15. Expected New Files
Interfaces, tool registry, agent services, adapters, webhook handlers, tests.
## 16. Expected Modified Files
Settings, URLs, service interfaces, job/audit modules, requirements, docs.
## 17. Database Changes
Only approved execution/webhook/audit/idempotency metadata; no direct AI-owned business tables without decision.
## 18. Migration Requirements
Tenant-aware metadata, replay/idempotency constraints, retention policy.
## 19. API Changes
Explicit async request/status/webhook contracts with authentication and schema.
## 20. Backend Changes
Adapters/services/jobs/audit and failure isolation.
## 21. Frontend Changes
Document interface only; no broad UI.
## 22. Security Requirements
Least privilege, tenant context, secret isolation, output validation, signed webhooks, replay protection, no sensitive prompts/logs.
## 23. Tenant / Permission Requirements
Every tool invocation and adapter event is scoped to authorized shop/supplier context.
## 24. Validation Requirements
Provider failure, timeout, invalid output, replay, cross-tenant, and core-workflow continuity tests.
## 25. Testing Requirements
Contract, unit, integration, security, failure, idempotency, retry, regression tests.
## 26. Error / Failure Handling
Fallback to manual workflow; bounded retries; dead-letter visibility; never silently fabricate business data.
## 27. Documentation Updates
API/security/architecture/state/handoff/changelog/decisions/runbooks.
## 28. Git Checkpoint Guidance
Checkpoint each adapter/control task; never push.
## 29. Handoff Requirements
Record tools, permissions, timeouts, providers, failure tests, and next task.
## 30. Phase Validation Checklist
- [ ] Interfaces narrow and typed
- [ ] No direct ORM/privileged access
- [ ] Tenant/security controls tested
- [ ] Webhooks validated/idempotent
- [ ] Core workflow survives outages
## 31. Definition of Done
Optional AI/integrations are useful, bounded, auditable, and unable to break core workflows.
## 32. Common Implementation Mistakes
Giving agents admin access, trusting output, missing tenant context, infinite retries, accepting unsigned webhooks, coupling core operations to providers.
## 33. Rollback / Recovery Notes
Disable provider/adapters feature flags; replay validated events; preserve manual core workflow and audit.
## 34. Phase Implementation Prompt
**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 6 only; it does not authorize I6-01 through I6-04. Before each task, present that task's objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. After confirmation, implement only that task, run its validation, update documentation, report the result, and stop. Do not begin the next task or Phase 7 automatically. Preserve core autonomy and the approved integration boundaries.
## 35. Phase Completion Report Format
`Phase: 6` / `Interfaces:` / `Controls:` / `Adapters:` / `Failure evidence:` / `Tests:` / `Docs:` / `Next task:`.
