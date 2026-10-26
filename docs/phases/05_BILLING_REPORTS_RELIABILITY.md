# Phase 5 — Billing, Reports + Reliability

## 1. Phase Overview
Connect completed work to financial records, reports, files, jobs, audit, and recovery.

### 2026-10-26 local migration closure update

The user authorized the local `devdb` migration after review of the exact plan.
All 9 pending migrations (`catalog.0025`/`0026`, `works.0003`, and
`billing.0001`–`0006`) applied successfully; `migrate --plan` now reports no
pending operations. Before applying them, a `devdb` backup was created, archive
validated, and restored into a disposable database. Comparison against that
restore found no row-count changes in pre-existing business/catalog/work
tables. The only count changes were expected Django permission/content-type and
migration-ledger rows; the 12 new Phase 5 tables were added. The comparison DB
was removed and the ignored backup is retained locally for recovery. Focused
backend billing/pricing tests passed 21/21 on disposable PostgreSQL. Django
system check and migration drift check passed. Local frontend `/` and backend
readiness returned HTTP 200. Supported frontend 233/233, typecheck/build and
authenticated synthetic browser/API flow are verified in the earlier runs
below. Local Phase 5 schema setup is now complete; staging is deferred and no
staging, commit, or deployment action occurred. Production backup/object
retention, monitoring, deployed parity and production restore remain later
release gates.

### 2026-10-26 pre-migration audit snapshot (superseded for local DB status)

The local database and migration statements below describe the pre-migration
snapshot and are superseded by the **2026-10-26 local migration closure update**
at the top of this document. Staging/deployed parity and the listed release
gates remain unresolved.

The phase remains **PARTIAL**. The backend Project State Validator passed on
`main` (`d6560c7c5457df11820686c6b6f3f204338c530a`), reporting Phase 5 active,
dirty worktree, test discovery unavailable, and remote verification unavailable.
Initial staging health attempts timed out, but a later documented read-only
smoke returned HTTP 200 for liveness and readiness. Health is verified only at
that check time. Unauthenticated `/api/schema/` returned Admin login HTML, so
deployed API contracts could not be inspected. Provider deployed SHA and
migration state remain UNVERIFIED. Local Git worktrees show `staging` at
`e1a4aafe85308b96d329d963c91e4ccac17a9c26` and a separate sync candidate at
`cab810bb28bbdd4e50df124caf30b606d2bf8b07`; neither committed tree contains
the Phase 5 Billing feature, and the candidate is not in the local staging
branch history. The current remote staging branch is `4db6d9fe`; this does not
prove the deployed Render SHA. Docker
Desktop was not running and no fresh live local-app visual pass was performed.
No staging, persistent database, or deployment was changed. Existing local
verification and open release blockers below remain.

The supported sibling frontend's focused Billing and purge UI tests were
rerun (**13/13 PASS**); the full frontend suite passed (**233/233**), and
`tsc -b --pretty false` plus the Vite production build passed. A fresh
disposable PostgreSQL server could not be started: bundled PG15 executables
exited with `-1073741502`, Docker's engine pipe was absent, and port 5432 was
unavailable. The verified empty scratch directory was removed; no DB was
created and the selected `devdb` remains protected. Backend database suites
were not rerun; 2026-10-25 results remain the latest DB-backed evidence.
Django system check and database-independent Billing calculation/PDF tests
also passed (5/5). Migration drift check reported “No changes detected” but
could not reach PostgreSQL at `127.0.0.1:5432`; no staging migration ledger was
read. Fresh read-only Git queries confirmed `origin/staging=4db6d9fe` and the
separate sync candidate `cab810bb`; neither tree has Phase 5 Billing code.
The user authorized commit/deploy after phase closure, but no commit/deploy has
occurred because the exact release candidate, staging database precondition,
and recovery path are not verified.

## 2. Phase Objective
Deliver financially safe billing and operational reliability without weakening shop isolation.

### 2026-10-25 verification refresh

Full local Django (486/486), pytest (593/593; 392 warnings), and supported
frontend (233/233) suites passed. Frontend typecheck/build and Django system
check/migration drift passed; lint exited 0 with existing warnings. The R2
private storage adapter roundtrip and synthetic presigned PUT (HTTP 200,
metadata/read/checksum/cleanup) passed. A disposable migration/restore smoke
verified financial totals, Shop ownership, and one private A5 invoice PDF;
receipt/credit-note restore files were not verified. The validator passed with
593 discovered tests. Current browser E2E remains previously verified at its
local viewport. Headless Chrome device viewport emulation with mocked responses verified the
Work Billing panel, Billing History (All/Outstanding), and Design Editor
Shop-price panel at 320, 390, 600, 768, 1024, and 1280 CSS px; the Financial
Purge page at 320, 360, 390, 600, 768, 1024, and 1280 px. Width diagnostics
found no overflow; page screenshots at 320px/1280px were visually reviewed.
The New invoice disclosure was opened at 320px and the purge dialog checked
at each purge width; mocked viewport runs submitted no business mutation.
Separately, authenticated headless Chrome browser-to-API E2E used synthetic
records on disposable PostgreSQL `sgtp_p5_ui_e2e_f8436c08`: the UI purged
synthetic `INV-000001`, confirmed success, and a DB check verified the invoice
and linked financial/document rows absent while the `COMPLETED` tombstone and
idempotency record remained. The disposable DB, test servers, Chrome profile,
and temporary folder were removed; `devdb` remains untouched. The initial
test login needed only the synthetic password hash regenerated using local
`dev` settings because setup had used test settings. Automated FinancialPurgePage tests now cover Shop loading/disabled, Shop-list
error/retry, invoice-history loading/error/retry/empty, draft exclusion, exact
confirmation, storage-failure protection, and purge retry. The Retry button now
repeats the failed Shop, invoice-history, or purge operation. The focused page
suite passed 8/8 and the full frontend suite passed 233/233; typecheck/build
passed. Targeted lint exited 0 with two `react(set-state-in-effect)` warnings
in the page. Exhaustive manual visual validation of every state at every
viewport remains incomplete. Production backup/restore, retention alignment, alerting/monitoring,
deployed parity, statutory retention/anonymization, and production restore
remain open; the separate Catalog media upload-ticket flow is not a Billing
PDF workflow dependency. Phase 5 is PARTIAL.

### 2026-10-25 implementation delta — manual Super Admin invoice purge

An explicit Main Supplier Super Admin path now supports manual, reasoned
purging of a selected Shop's entire invoice bundle after exact invoice-number
confirmation. The flow retains audit/idempotency history and sequence
high-water values, does not run automatically, and keeps financial rows when
private-file deletion fails so the operation can be retried. `billing.0006`
adds purge request/idempotency tracking. The focused backend and frontend tests
pass on a disposable test DB and local UI test runner. The migration is not
applied to persistent `devdb`; no app financial data was purged. This does not
close legal retention, production backup/object-retention, alerting, or restore
gates, so Phase 5 remains PARTIAL.
## 3. Business Purpose
Turn completed tailoring work into invoices, balances, receipts, history, and actionable reports.
## 4. Technical Purpose
Implement money-safe transactions, idempotency, PDFs, object storage, background jobs, backups, and restore verification.
## 5. Preconditions
Phase 4 workflow and services pass; explicit activation.
## 6. Dependencies
Work aggregate, shop permissions, PostgreSQL, service layer, audit foundation.
## 7. Current Repository Assumptions
Phase 5 is active. Shop pricing, Work snapshots, Billing UI/API, audit/idempotency, invoice history, and localized private PDF generation are implemented locally across the canonical backend and supported sibling frontend. Authenticated browser-to-API E2E was verified with synthetic data on an isolated disposable PostgreSQL database; the persistent application DB was not migrated or written. Latest full disposable suites passed Django 486/486 and pytest 593/593 (392 pytest warnings); earlier 587/587, 483/483 and focused 54/54 backend results are historical checkpoints. On 2026-10-25, the supported frontend passed 233/233 with production build/typecheck. FinancialPurgePage passed 8 focused UI-state tests; Retry repeats the failed Shop load, invoice-history load, or purge. Targeted lint exited 0 with two `react(set-state-in-effect)` warnings in that page. Django system check, migration drift check, and Project State Validator (593 tests discovered) passed. A fresh disposable migration and A5 database/media restore passed; only an invoice PDF file was verified across media restore. R2 `PrivateReferenceStorage` upload/read/checksum/delete passed, as did a synthetic presigned PUT (HTTP 200), metadata check, private read/checksum, and exact-key deletion/absence verification. The separate Catalog private-media upload-ticket/browser flow remains unverified; Billing PDF generation writes FinancialDocument files directly through the shared private storage adapter and does not call that catalog endpoint, so the upload-ticket flow is not an R5-04 dependency. Cleanup confirmed the exact restore/test databases and temporary artifacts absent; `devdb` remained unmigrated and untouched. Production monitoring/alert delivery, backup/object-retention alignment, deployed parity, and production restore remain unverified. PDFs remain synchronous, so no background worker is required or claimed; see current handoff for exact evidence and remaining gates.
## 8. Exact Scope
Billing/accounts/transactions/outstanding, idempotency, audit, soft delete, PDFs/reports, storage, jobs, backups/restore.
## 9. Out of Scope
AI, supplier-wide finance aggregates, jurisdiction-specific tax/legal certification,
and staging/production rollout. Billing, Shop Design-price, and history UI are
in scope under PHASE-5-INTEGRATED-CLOSURE-01; unrelated screens are not.
## 10. Architecture Context
Billing records attach to Work but are not gated on the Completed stage: drafts may be created at any stage, and invoices may be issued/part-paid before completion. Payment never changes Work stage. Reliability features remain tenant-aware and failure-isolated.
## 11. Implementation Sequence
Money model → invoice/payment services → idempotency/audit → reports/PDF → storage/jobs → backup/restore → integration tests.
## 12. Detailed Task List

### R5-01 Billing and Shop Design pricing
Status: local API/UI integration is verified against synthetic data on disposable PostgreSQL. Shop Design prices are editable in Design UI; Work snapshots price/currency at creation. Billing supports multiple invoices, AUTO/MANUAL lines, draft edits, optional fixed/percentage discount, optional tax, issue-time sequential numbers, payment, void, credit note, manual refund record, outstanding/history, and localized PDF actions. Browser E2E verified AUTO and MANUAL drafts, issue/numbering, partial payment, credit/refund, void, Billing History, and Outstanding. The approved Main Supplier Super Admin manual invoice-bundle purge is an explicit exceptional action, covered by focused API/UI tests; it does not alter ordinary Shop invoice permissions. All 9 Phase 5 migrations are now applied to persistent local `devdb` after a verified backup/restore path; staging/production remain unchanged. No separate global price catalog or supplier-wide finance aggregate was added.

### R5-02 Financial service and idempotency
Status: source-implemented and database-tested. Shop-row locking serializes financial writes; idempotency keys are Shop/actor scoped and request-hash bound; new writes store the exact response snapshot/status for deterministic replay while pre-snapshot records retain a compatibility fallback. Append-only tenant-scoped audit records capture safe before/after state and request correlation. Latest clean disposable suites passed Django 483/483 and pytest 590/590; the earlier 587/587 full backend and post-context 54/54 focused runs are historical checkpoints. Retries and tenant isolation are covered by API tests; the browser smoke exercised live authorized writes on synthetic data.

### R5-03 Reports, history, and PDFs
Status: invoice, outstanding, and date/status-filtered Shop history plus invoice/receipt/credit-note PDFs are implemented with Shop-scoped authorization and per-document locale. Browser E2E verified the Billing History and Outstanding views and totals. API tests verify protected download/checksum and cross-Shop denial for each document type. The separate DB/media restore smoke verified the invoice PDF only; receipt/credit-note restore was not claimed. PDF output is synchronous. R2 `PrivateReferenceStorage` roundtrip and a synthetic presigned PUT (HTTP 200, metadata/read/checksum and exact-key cleanup) passed; the database-backed upload-ticket API and browser completion remain unverified. There is no supplier-wide aggregate, general statement/report API, or async document job. Approved tax/discount and number/refund rules are in `docs/BUSINESS_RULES.md`.

### R5-04 Storage and background jobs
Status: partial. Generated PDFs reuse the existing private `PrivateReferenceStorage` local/R2 abstraction, have Shop ownership checks, no public URL exposure, bounded generated size, checksum metadata, and protected download. Local filesystem behavior is tested. Required R2 settings are non-empty in the ignored local `.env`; HeadBucket, adapter upload/read/checksum/delete, and a synthetic presigned PUT (HTTP 200 with metadata/read/checksum and cleanup) passed. The separate Catalog private-media upload-ticket/browser flow remains unverified; Billing PDF generation writes FinancialDocument files directly through the shared private storage adapter and does not call that catalog endpoint, so the upload-ticket flow is not an R5-04 dependency. No Sentry/error-tracking SDK or DSN configuration was found in this checkout/local environment; provider choice/configuration and production alert delivery/monitoring remain open. Current PDF generation is synchronous and API failures surface to the caller, so no queue/worker was added without a demonstrated need. Manual financial purge semantics are approved and locally tested; statutory retention periods/anonymization, production backup/object-retention alignment, and external operational monitoring remain unresolved release questions. Purge file-deletion failure is retryable by an explicit repeat request; no automatic deletion or background retry worker is implemented.

### R5-05 Backup and restore verification
Status: local smoke test passed. Fresh migrations and PostgreSQL `pg_dump`/`pg_restore` verified financial totals, Shop ownership, and one private A5 invoice PDF v2 checksum/file across restore using disposable databases `sgtp_p5_restore_source_20261022a1b2` and `sgtp_p5_restore_target_20261022a1b2`. A repeat on 2026-10-25 using disposable databases `sgtp_p5_restore_source_20261025a75b` and `sgtp_p5_restore_target_20261025a75b` also passed; cleanup then confirmed those databases, the focused disposable test DB, dump, and temporary media absent. Invoice/receipt/credit-note API download and cross-Shop checks are covered separately by tests; only the invoice file was included in the restore claim. This does not verify scheduled production backups, external R2 snapshots, production restore, or legal retention/anonymization. Manual purge is now explicitly supported and locally validated, but production backup/object-retention alignment remains unverified.

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
Supported sibling frontend: Shop Design price editor, Work Billing panel, Billing History route, optional tax/discount and manual line controls, issue/payment/void/credit/refund actions, and protected localized PDF downloads. Full frontend tests (233/233), typecheck, and build pass; authenticated browser-to-API E2E passed at the current local viewport. Mocked responsive renders covered Work Billing, Billing History (All/Outstanding), Design Editor Shop-price, and Financial Purge at the viewport widths recorded above; no overflow was detected. This mocked responsive validation is complemented by authenticated purge browser-to-API E2E on a synthetic invoice in a disposable DB. FinancialPurgePage retry handling was corrected so Retry repeats the failed request and is covered by its 8 tests. Exhaustive manual visual validation across all loading/error/empty/disabled/action states remains incomplete. Catalog-media upload-ticket browser completion remains separate and unverified.
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
- [x] R5-01 billing API allows drafts and issue/payment before Work completion without changing Work stage
- [x] Authenticated Billing browser-to-API E2E on synthetic data in disposable PostgreSQL; persistent application DB intentionally untouched
- [x] Fresh disposable migration replay; latest full suites: Django 486/486, pytest 593/593 (392 warnings), and supported frontend 233/233; 587/587, 483/483, frontend 226/226, and focused 54/54 are historical checkpoints
- [x] R5-02 idempotency snapshots, Shop locking and append-only audit covered by DB-backed tests
- [x] Shop-scoped history/outstanding and invoice/receipt/credit-note protected download/API tests; Billing History and Outstanding also browser-verified
- [x] Local private storage tested; invoice PDF checksum/file survives the isolated media restore smoke
- [x] Manual Main Supplier Super Admin invoice-bundle purge is reason/number-confirmed, retry-safe on file failure, and covered by focused tests; audit/idempotency history and sequences are retained
- [x] Configured R2 storage adapter and synthetic presigned PUT tested with read/checksum/delete and exact-key cleanup; no pre-existing object was touched
- [x] Mocked responsive viewport checks: Work Billing, Billing History (All/Outstanding), and Design price panel at 320/390/600/768/1024/1280px; Financial Purge at 320/360/390/600/768/1024/1280px; no overflow; mocked responsive checks submitted no business mutation
- [x] Authenticated Main Supplier Super Admin Financial Purge UI/API E2E on one synthetic issued invoice in disposable PostgreSQL; invoice bundle removed and completion tombstone/idempotency retained; disposable DB cleaned
- [ ] Statutory retention/anonymization, production backup/object-retention alignment, alerting/monitoring, production restore, and exhaustive manual visual state validation remain release gates
- [x] The current PDF path is bounded and synchronous; no background worker is required or claimed
## 31. Definition of Done
Completed work can be billed, reported, and recovered safely with evidence.
## 32. Common Implementation Mistakes
Float money, duplicate retries, mutable invoices, public files, synchronous PDFs, unscoped reports, untested restore.
## 33. Rollback / Recovery Notes
Use compensating records for normal financial corrections. The explicitly approved Main Supplier Super Admin purge is the only implemented issued-bundle deletion exception; preserve its tombstone/audit/idempotency and sequence evidence. Restore to an isolated DB; a failed private-file delete must leave financial rows intact for retry.
## 34. Phase Implementation Prompt
**Implement ONLY this phase. Do not implement future phases.** Default policy is task-by-task confirmation. The explicit `PHASE-5-INTEGRATED-CLOSURE-01` confirmation authorizes its complete bounded R5-01–R5-05 package without additional per-R5 confirmations. Stop after this package; do not start Phase 6. New business rules, external deployment, shared-environment writes, or scope outside that approved plan remain excluded. Report any environment-blocked acceptance criteria without claiming completion.
## 35. Phase Completion Report Format
`Phase: 5` / `Financial invariants:` / `Files/jobs:` / `Restore:` / `Tests:` / `Docs:` / `Next task:`.
