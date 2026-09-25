# Phase 8 — Testing + Hardening

## 1. Phase Overview

Validate the integrated SGTP product and harden business, security, reliability, and performance behavior.

## 2. Phase Objective

Prove critical workflows and security boundaries work together, especially that Shop A can never access Shop B data.

## 3. Business Purpose

Prevent regressions that could corrupt tailoring operations, financial records, files, or tenant trust.

## 4. Technical Purpose

Expand unit/API/integration/end-to-end/security/performance coverage and resolve verified defects without changing approved scope.

## 5. Preconditions

Phases 1–7 are implemented or explicitly accepted; staging-like services are available for tests; explicit `CONFIRM PHASE 8` has been received.

## 6. Dependencies

All implemented backend/frontend modules, shop isolation, workflow services, billing, reports, storage/jobs, AI boundaries, CI configuration, and test data strategy.

## 7. Current Repository Assumptions

The starter currently has only limited account/tenant tests; this phase is a future validation phase and must not be used to hide missing implementation.

## 8. Exact Scope

Unit, API, integration, authentication, permission, tenant-isolation, workflow, billing, file-security, failure, regression, security-hardening, and performance validation.

## 9. Out of Scope

Adding new business scope, redesigning architecture, production deployment, or marking incomplete functionality complete by weakening tests.

## 10. Architecture Context

Tests must validate the system as one connected supplier → shop → tailoring → billing → reporting workflow, not only isolated modules.

## 11. Implementation Sequence

Test inventory → unit/API coverage → auth/permissions/isolation → workflow/billing/files/jobs → end-to-end → security/performance → regression gate.

## 12. Detailed Task List

### H8-01 Test inventory and deterministic fixtures

- Objective: map critical requirements to tests and create safe deterministic fixtures/factories.
- Why it exists: coverage must reflect the Definition of Done, not implementation convenience.
- Dependencies: completed/accepted product features; explicit task confirmation.
- Files to create: test matrix, factories/fixtures, seed helpers, test configuration.
- Files to modify: CI/test settings only as required.
- Steps: inventory endpoints/workflows/roles/failures, define isolated test data, avoid production secrets and shared state.
- Database impact: test DB/fixtures only.
- API/security impact: define expected status/data-leak behavior.
- Tests: fixture isolation and repeatability.
- Validation: repeated test run produces same results.
- Documentation update: test plan, state, handoff.
- Definition of Done: traceable test matrix and deterministic setup.

### H8-02 Unit/API/authentication and permission coverage

- Objective: cover models, services, serializers, endpoints, auth lifecycle, roles, object permissions, and tenant isolation.
- Why it exists: backend enforcement must be proven directly.
- Dependencies: H8-01, explicit task confirmation.
- Files to create/modify: tests only plus narrowly justified test configuration.
- Steps: add happy/invalid/auth/replay/IDOR/cross-shop cases; assert no forbidden data appears in lists, search, ordering, counts, or errors.
- Database impact: test data/migrations only.
- API/security impact: identify defects; do not weaken assertions.
- Validation: Shop A must NEVER access Shop B data.
- Documentation update: security/API/state/handoff.
- Definition of Done: critical backend security coverage passes.

### H8-03 Workflow, billing, file, job, and failure tests

- Objective: test the integrated production-to-billing path and failure recovery.
- Why it exists: business correctness depends on state, money, files, and jobs together.
- Dependencies: H8-02, explicit task confirmation.
- Files to create/modify: integration tests, job/file test adapters, report/PDF tests.
- Steps: exercise request through Completed and Billing/Reports; test invalid transitions, concurrent writes, idempotency, private files, job retries/dead letters, provider outages.
- Database impact: transactional test data.
- API/security impact: assert scoped responses and safe failures.
- Validation: end-to-end journey and recovery evidence.
- Documentation update: state/handoff/operations.
- Definition of Done: critical workflow and failure behavior is proven.

### H8-04 End-to-end, security hardening, and performance

- Objective: run browser/system journeys, dependency/security checks, and performance validation.
- Why it exists: module tests cannot prove integrated product readiness.
- Dependencies: H8-03, explicit task confirmation.
- Files to create/modify: E2E suites, load/security configs, CI workflows.
- Steps: test supplier/back office/shop journey, access attacks, file attacks, rate limits, query counts, latency, pagination, worker behavior; triage only verified issues.
- Database impact: benchmark/test data only.
- API/security impact: hardening corrections must be separately scoped and documented.
- Validation: agreed thresholds and no critical/high unresolved defects.
- Documentation update: test/security/performance reports, state, handoff.
- Definition of Done: release-quality evidence exists.

## 13. Task Dependency Graph

`H8-01 → H8-02 → H8-03 → H8-04`.

## 14. Expected Files / Folders

Backend tests, frontend/E2E tests, factories, CI/security/performance configurations, reports.

## 15. Expected New Files

Test modules, fixtures, E2E suites, scanners/load scripts, CI jobs, test reports.

## 16. Expected Modified Files

Test settings, CI configuration, narrowly verified defects, documentation; no scope changes.

## 17. Database Changes

Test fixtures and performance datasets; production schema changes only through separately approved corrections.

## 18. Migration Requirements

Run migrations from empty DB and representative DB; test migration compatibility and rollback/recovery procedure.

## 19. API Changes

Normally none; document any defect and obtain task confirmation before changing a contract.

## 20. Backend Changes

Tests and narrowly scoped hardening fixes only when explicitly confirmed as the task.

## 21. Frontend Changes

Test harness and verified accessibility/performance fixes only; no new features by implication.

## 22. Security Requirements

Test authentication, authorization, IDOR, tenant leakage, rate limits, secrets, files, webhooks, AI boundaries, and error leakage.

## 23. Tenant / Permission Requirements

The critical invariant is absolute: Shop A must never access Shop B data through any endpoint, filter, export, file, report, job, or UI path.

## 24. Validation Requirements

Repeatable test runs, coverage for critical paths, E2E evidence, security scan, performance thresholds, and defect triage.

## 25. Testing Requirements

All categories named in scope, with results recorded—not merely test existence.

## 26. Error / Failure Handling

Capture artifacts/logs safely, quarantine flaky tests, distinguish environment failures from product failures, and block release on critical defects.

## 27. Documentation Updates

Update test/security/API/architecture/state/handoff/changelog and issue records for actual findings.

## 28. Git Checkpoint Guidance

Checkpoint test additions and fixes separately; never push automatically.

## 29. Handoff Requirements

Record test commands, artifacts, pass/fail counts, unresolved defects, environment limitations, and next task; stop.

## 30. Phase Validation Checklist

- [ ] Deterministic fixtures
- [ ] Auth/permission coverage
- [ ] Shop isolation proven
- [ ] Workflow/billing/files/jobs tested
- [ ] E2E journey tested
- [ ] Security/performance gates recorded

## 31. Definition of Done

Critical business/security behavior is tested end-to-end with no unresolved release-blocking defects.

## 32. Common Implementation Mistakes

Testing only 200 responses, trusting frontend isolation, sharing tenant fixtures, ignoring exports/files/jobs, hiding flaky tests, lowering assertions to pass.

## 33. Rollback / Recovery Notes

Revert test/hardening changes independently; preserve failed artifacts; disable unsafe features rather than suppressing critical tests.

## 34. Phase Implementation Prompt

**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 8 only; it does not authorize H8-01 through H8-04. Before each task, present its objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. Implement only the confirmed task, validate it, update documentation, report the result, and stop. Do not begin the next task or Phase 9 automatically.

## 35. Phase Completion Report Format

`Phase: 8` / `Task confirmed:` / `Tests added/run:` / `Isolation evidence:` / `Failures/defects:` / `Security/performance:` / `Docs updated:` / `Next task requires confirmation:`.
