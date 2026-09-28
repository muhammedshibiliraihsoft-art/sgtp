# Phase 5 — Billing, Reports + Reliability

## 1. Phase Overview
Connect completed work to financial records, reports, files, jobs, audit, and recovery.
## 2. Phase Objective
Deliver financially safe billing and operational reliability without weakening shop isolation.
## 3. Business Purpose
Turn completed tailoring work into invoices, balances, receipts, history, and actionable reports.
## 4. Technical Purpose
Implement money-safe transactions, idempotency, PDFs, object storage, background jobs, backups, and restore verification.
## 5. Preconditions
Phase 4 workflow and services pass; explicit activation.
## 6. Dependencies
Work aggregate, shop permissions, PostgreSQL, service layer, audit foundation.
## 7. Current Repository Assumptions
No billing, report, storage, worker, or audit implementation is complete.
## 8. Exact Scope
Billing/accounts/transactions/outstanding, idempotency, audit, soft delete, PDFs/reports, storage, jobs, backups/restore.
## 9. Out of Scope
AI, frontend screens, staging/production rollout.
## 10. Architecture Context
Billing is downstream of Completed work; reliability features must be tenant-aware and failure-isolated.
## 11. Implementation Sequence
Money model → invoice/payment services → idempotency/audit → reports/PDF → storage/jobs → backup/restore → integration tests.
## 12. Detailed Task List

### R5-01 Billing and account model
Objective: define invoice, line item, payment, balance, and outstanding semantics. Dependencies: Phase 4. Files: `backend/apps/billing/{models,migrations,serializers,views,tests}`. Steps: use Decimal (never float), immutable issued records, statuses, approved tax/discount rules only, shop scope, and Primary Client ownership for Related Person work. Support advance/deposit, partial and final payments; completion/QC cannot be bypassed by payment state. Keep cancellation/refund, overpayment, allocation and currency-change semantics as `BUSINESS DECISION REQUIRED` unless separately approved. DB: constraints/indexes. API: draft/issue/payment/outstanding/read. Security: financial permissions. Tests: totals/rounding/authorization, payment lifecycle, integrity, and Primary Client ownership. DoD: model is safe and approved ownership/payment rules are enforced without invented financial policy.

### R5-02 Financial service and idempotency
Objective: connect billing to Completed work and make writes retry-safe. Dependencies: R5-01. Steps: transactional issue/payment operations, idempotency keys, uniqueness, concurrency locks, immutable history, audit events, and explicit policy gates for refunds/allocations. Audit records capture actor UUID, Shop, action, object type/ID, safe before/after values, timestamp and request correlation; never passwords, tokens or secrets. DB: keys/constraints. API: idempotent responses linked to client/shop/work. Tests: retries/races/partial failure, duplicate submission, financial invariants, audit completeness and redaction. DoD: retries cannot create duplicate financial effects and no unapproved refund/allocation rule is chosen.

### R5-03 Reports, history, and PDFs
Objective: expose shop/supplier reports and generated PDFs. Dependencies: R5-02. Files: `backend/apps/reports/{models,migrations,serializers,views,tests}` and approved report/PDF services. Steps: define permitted aggregates, query indexes, templates, deterministic rendering, report history, linked invoice/payment/account/client/shop/work identity, and document-language override. Default document language follows User preference → authorized Shop default → English; allow one-document override without changing stored canonical data. Validate English, Arabic RTL, Bangla and Urdu shaping/fonts/layout, dates/numbers/currency. DB: report metadata and locale provenance if needed; historical money remains unchanged. API: async job/status/download. Security: no cross-Shop aggregates or public document links. Tests: totals/permissions/rendering/RTL and monetary integrity. DoD: verified scoped reports/documents.

### R5-04 Storage and background jobs
Objective: securely persist files and move heavy work off requests. Dependencies: R5-03. Steps: object storage abstraction for private design/reference galleries and generated PDFs, private paths, bounded signed access, content validation, worker queue, retries/dead letters, tenant metadata, and safe failure visibility/alerts. Add V1 notification/alert foundation for due/overdue Work, outstanding payment, failed job, and important account/security events; no provider integrations absent separate approval. Tests: file traversal/type/authorization, cross-Shop private access, job retry/failure and alert safety. DoD: durable private files/jobs and observable failures.

### R5-05 Backup and restore verification
Objective: document and exercise recovery. Dependencies: R5-01–04. Steps: backup DB/object metadata, retention decision, encryption, restore to isolated environment, verify migrations/data/files, and retain evidence. Retention duration and anonymization remain `BUSINESS DECISION REQUIRED` before production. DoD: recorded restore evidence and explicit unresolved retention policy.

## 13. Task Dependency Graph
`R5-01 → R5-02 → R5-03 → R5-04 → R5-05`.
## 14. Expected Files / Folders
`backend/apps/billing/`, `backend/apps/reports/`, `backend/core/services/`, storage/job/audit modules, migrations, worker config, templates, tests, runbooks.
## 15. Expected New Files
Financial models/services, report/PDF services, storage/job adapters, backup/restore scripts/docs.
## 16. Expected Modified Files
Work services/API, settings, URLs, requirements, Docker, docs.
## 17. Database Changes
Invoices, lines, payments, idempotency keys, audit/report metadata, indexes and constraints.
## 18. Migration Requirements
Money precision, immutable history, backfills, empty/representative DB tests, recovery plan.
## 19. API Changes
Billing, payments, outstanding, reports, PDF/job status/download contracts.
## 20. Backend Changes
Transactional services, permissions, storage/jobs, audit, report queries.
## 21. Frontend Changes
None.
## 22. Security Requirements
Financial authorization, immutable issued records, private storage, signed URLs, file validation, no sensitive logs. V1 observability includes approved error tracking (Sentry or approved equivalent direction), environment tags, request correlation IDs, failed-job visibility, critical failure alerts, and secret-safe logs; provider choice/credentials require explicit configuration and must not be committed.
## 23. Tenant / Permission Requirements
Every financial/report/file/job record must carry and enforce shop context.
## 24. Validation Requirements
Totals, idempotency, concurrent payments, report scopes, file access, job failure, restore.
## 25. Testing Requirements
Financial unit/API/integration, permission, file security, job failure, backup restore, regression.
## 26. Error / Failure Handling
Atomic financial writes, retry-safe jobs, dead-letter visibility, report failure status, no silent data loss.
## 27. Documentation Updates
API/database/security/operations/state/handoff/changelog/decisions.
## 28. Git Checkpoint Guidance
Checkpoint each reliability task; never push.
## 29. Handoff Requirements
Record financial invariants, storage/job contracts, recovery evidence, and next task.
## 30. Phase Validation Checklist
- [ ] Billing tied to Completed
- [ ] Idempotency/concurrency proven
- [ ] Reports/PDFs permissioned
- [ ] Files private/persistent
- [ ] Jobs retry safely
- [ ] Restore verified
## 31. Definition of Done
Completed work can be billed, reported, and recovered safely with evidence.
## 32. Common Implementation Mistakes
Float money, duplicate retries, mutable invoices, public files, synchronous PDFs, unscoped reports, untested restore.
## 33. Rollback / Recovery Notes
Never delete financial history; reverse with compensating records; restore to isolated DB; quarantine failed files/jobs.
## 34. Phase Implementation Prompt
**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 5 only; it does not authorize R5-01 through R5-05. Before each task, present that task's objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. After confirmation, implement only that task, run its validation, update documentation, report the result, and stop. Do not begin the next task or Phase 6 automatically. Preserve the approved financial and reliability architecture.
## 35. Phase Completion Report Format
`Phase: 5` / `Financial invariants:` / `Files/jobs:` / `Restore:` / `Tests:` / `Docs:` / `Next task:`.
