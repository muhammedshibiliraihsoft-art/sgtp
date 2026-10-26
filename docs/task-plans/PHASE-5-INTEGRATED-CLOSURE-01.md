# PHASE-5-INTEGRATED-CLOSURE-01 — Single-Approval Implementation Roadmap

**Current status (2026-10-26): LOCAL PHASE 5 DATABASE SETUP COMPLETE; release status remains PARTIAL.** After explicit user authorization, all 9 pending local `devdb` migrations (`catalog.0025`/`0026`, `works.0003`, `billing.0001`–`0006`) applied successfully and no migrations remain pending. A pre-migration backup was archive-validated and restored to a disposable DB; existing business/catalog/work table row counts matched after migration. Expected Django permission/content-type/migration rows and 12 new Phase 5 tables were added; the disposable comparison DB was removed and the ignored backup retained. Focused backend billing/pricing tests passed 21/21 on a disposable DB; Django check and migration drift pass. The local frontend and backend readiness return HTTP 200. Earlier full backend/frontend suites, authenticated synthetic E2E, responsive checks, and storage verification remain recorded with their original dates and scope. Staging is deferred; no staging, commit, or deployment action occurred. Production backup/object-retention, restore/monitoring, deployed parity, and applicable retention/anonymization policy remain release gates. No automatic deletion was implemented. The 2026-10-22 status/checkpoint below is historical.

## Goal

Close the Phase 5 Billing, Reports, and Reliability work as one integrated end-to-end package, including Shop Design pricing and a supported frontend experience. After one explicit confirmation of this task, execute its in-scope milestones without asking for separate confirmation for R5-01 through R5-05. Stop at the end of this package; do not start Phase 6.

## Initial verified baseline (before this task was confirmed)

- Canonical backend is the dirty local `main` checkout. The supported Orders frontend is the sibling `frontend/parallel-foundation` worktree; inspect both worktree instructions and ownership before any cross-worktree change.
- R5-01 backend code exists locally for Shop Design prices, Work price/currency snapshots, multiple invoices per Work, AUTO/MANUAL lines, issue, invoice-bound payment, outstanding balances, and ADMIN/CASHIER authorization.
- R5-01 focused backend tests and disposable-PostgreSQL migration replay are documented as passing 30/30. Generated migrations `catalog.0026`, `works.0003`, and `billing.0001` were not applied to the configured application database or shared environments.
- No supported Billing/Design-price frontend integration, R5-02 idempotency/audit, R5-03 reporting/PDF, R5-04 storage/jobs, or R5-05 recovery closure is verified.
- The working tree already contains extensive user changes. Preserve all existing work; do not reset, clean, stash, or copy between checkouts blindly.

## Current implementation checkpoint (2026-10-22)

The single approval still bounds work to the local Phase 5 package. Local
source covers per-Shop Design prices and Work price/currency snapshots, the
supported sibling price/Billing/history UI, approved invoice/tax/discount/
number/void/credit/refund rules, Shop-scoped financial authorization,
idempotency/audit, private localized PDFs, and additive migrations through
`billing.0004`. None of these migrations was applied to the persistent
application database.

The supported local app was authenticated as a synthetic Shop ADMIN against
only disposable PostgreSQL database `sgtp_p5_restore_source_9d3a61c542be`.
Browser-to-API E2E verified currency-gated billing access, AUTO Design-snapshot
draft and optional fixed discount/tax, issue-time `INV-000002`, partial payment,
`CN-000002`, a payment-linked manual refund, MANUAL quantity/unit-price lines
with percentage discount/tax, `INV-000003`, and reasoned void of the unpaid
invoice. The Billing History page showed all three records; Outstanding showed
only the two non-void invoices with balances consistent with payment, credit,
and refund. Billing left Work at Request. The initial issue error was caused by
the synthetic restore fixture having manually inserted numbered records but
no matching Shop sequence rows; the fixture now seeds its high-water marks.
No invoice-number runtime behavior was changed to work around test data.

After the finance-only Shop-context currency field change, focused backend
Shop-context/Work/Billing calculation tests passed 54/54, full frontend Vitest
passed 225/225, and frontend typecheck/build passed. The complete backend suite
passed 587/587 before that narrow context-contract change. `manage.py check`,
`makemigrations --check --dry-run`, and drf-spectacular validation passed; all
four generated schema snapshots (backend root/docs and supported sibling
frontend root/docs) are identical and validate with 0 errors / 29 existing
warnings. The context contract adds nullable `billing_currency` only for Shop
ADMIN and active CASHIER STAFF; non-financial staff remain unchanged.

Separate disposable PostgreSQL migration replay and `pg_dump`/`pg_restore`
verified financial totals, Shop ownership, and one private invoice PDF's
checksum/file restoration. Invoice, receipt, and credit-note download and
cross-Shop checks are covered by API tests; the restore smoke did **not** verify
receipt/credit-note files across restore. Both earlier restore-smoke databases
and their media were removed. The authenticated E2E database was dropped after
verifying zero connections and preserving `devdb` OID 17142; temporary app
ports 8002/5174 have no listeners. One synthetic invoice PDF remains at
`.test-private-assets/sgtp-phase5-restore-9d3a61c542be/source-private-media/`
because the exact local file-removal command was blocked. No alternate cleanup
method was attempted. Persistent `devdb` was never written or migrated. Local
filesystem storage is verified; external R2 persistence and production restore
are not.

R5-04 remains partial: current PDFs are bounded synchronous operations, so no
queue was introduced; external storage, configured operational alerting, and
production retention/anonymization are not verified. No staging/production,
commit, push, or deployment occurred. Overall status: **PARTIAL — local billing
flows verified; production/reliability gates remain open**.

## Approved business rules to implement

These decisions were given in the conversation on 2026-10-21; the current canonical business/decision documents still contain stale unresolved statements and must be reconciled during the approved task.

- Design prices are Shop-specific, including for global Designs. A valid Shop `default_currency` is required. Work captures a price/currency snapshot on creation; later price edits do not affect existing Work.
- Shop ADMIN and STAFF with CASHIER function can manage Shop Design prices and financial operations. CASHIER alone does not grant Shop access.
- One Work may have multiple invoices. Drafts are allowed at any Work stage; issue and payment never advance or bypass production.
- AUTO lines use the Work's price snapshot when present; MANUAL lines use description, quantity, and unit price. Issued invoices/lines are immutable. A payment is linked to one specified invoice; overpayment is rejected.
- Currency amounts reject precision beyond the currency minor unit. Shop currency is frozen after price/financial history exists; a change requires an explicit migration.
- Issue-time invoice numbers are sequential per Shop (`INV-000001` pattern); voided numbers are never reused.
- Invoice-level discount may be fixed or percentage. Fixed discounts are allocated to lines in proportion to pre-discount line amounts; currency rounding uses `ROUND_HALF_UP`, with any residual assigned to the final line. Discount cannot exceed subtotal.
- Tax is optional. When entered, the invoice-level tax rate applies after discount; tax is rounded per line to currency minor units with `ROUND_HALF_UP`. The tax and resulting total must appear in invoice/payment amounts. No jurisdiction-specific tax-registration or legal-compliance claims are included.
- Draft invoices may be deleted. An unpaid issued invoice may be voided with a reason. A paid invoice is corrected through a linked partial/full credit note, sequentially numbered per Shop (`CN-000001` pattern); record only an actually transferred refund, linked to its payment/credit note. The app does not transfer money. Refund cannot exceed actual eligible payments.
- Related Person Work is billed to its Primary Client.

## Execution workstreams and sequence

All workstreams below are part of this single task confirmation; the order is dependency order, not separate approval gates.

### 0. Reconcile policy and ownership

- Re-read applicable `AGENTS.md` files, Git state, phase/business/decision docs, architecture maps, API contracts, current code/tests, and supported frontend ownership.
- Record the approved rules above in the canonical Business Rules and Decisions documents, correcting only stale R5-01 statements. Keep implementation status distinct from approved target behavior.
- Resolve the conflicting Phase 5 confirmation language: repository-wide `AGENTS.md` says phase confirmation covers in-scope tasks, while Phase 5 §92 currently demands a separate confirmation for each R5 task. Under this single-task plan, one `CONFIRM TASK PHASE-5-INTEGRATED-CLOSURE-01` authorizes the bounded workstreams below; no per-R5 confirmation is requested.

### 1. R5-01 closure — pricing and Billing experience

- Complete Shop Design price/catalog management and integrate the supported frontend with existing Shop-scoped API contracts.
- Build the invoice list/detail/create/edit-draft/issue/payment experience for AUTO and MANUAL lines, optional discount/tax, sequential invoice number, outstanding amount, and correct payment total.
- Add void, credit-note, and manual refund-record flows under the approved immutability and authorization rules.
- Add currency-change guardrails after financial history and an explicit, tested migration path; never silently reinterpret historic money.
- Preserve current Work-stage behavior and Related Person → Primary Client billing ownership.
- UI is a first-class deliverable: follow the supported frontend's existing page structure, typography, spacing, control tokens, icon usage, and primary/secondary/destructive button hierarchy. Reuse shared components; do not introduce a one-off visual system.
- Make pricing, invoice editing, issue/payment, credit/refund, and history views responsive for narrow phone, normal phone, tablet, laptop, and desktop. Keep mobile controls compact but touch-safe; use responsive composition rather than merely shrinking desktop layouts. Prevent overflow, clipped labels/amounts, and fixed-action overlap.
- Design and test loading, empty, validation/error, success, and disabled states; preserve accessible labels/focus/keyboard behavior and localized text expansion where supported.

### 2. R5-02 — financial write safety and audit

- Make draft creation, issue, payment, void, credit-note, and refund writes idempotent and concurrency-safe, with server-side uniqueness/locking and deterministic retry responses.
- Add append-only, tenant-scoped audit events with actor, Shop, action, object, safe before/after values, timestamp, and correlation; exclude credentials, tokens, and sensitive payment data.
- Keep issued invoice/line, payment, credit-note, and refund history immutable; corrections are additive records, never edits to prior financial history.

### 3. R5-03 — history, statements, and documents

- Add Shop-scoped invoice/payment/outstanding history and deterministic invoice/receipt/credit-note PDFs, including localized layout support already required by the product.
- Derive document totals from canonical financial records and snapshots; never change historic amounts when Design prices or Shop settings change.
- Do not introduce supplier-wide financial aggregates unless an explicit business rule authorizes them; initially keep financial visibility within the selected Shop.

### 4. R5-04 — private files, jobs, and failure visibility

- Store generated financial documents privately with Shop ownership checks, safe content handling, bounded downloads, and no public object URLs.
- Use background jobs only for work that needs them (for example, PDF generation); implement bounded retries, idempotent processing, visible failure state, and operational logging.
- Keep external notification/payment-provider integrations out of scope. No payment is sent by the application.

### 5. R5-05 — backup and restore verification

- Define and test an isolated backup/restore procedure for database and private-file metadata; replay migrations and verify invoice/payment/credit-note totals and ownership after restore.
- Do not backfill fictional historical prices/events or mutate existing customer records merely to satisfy tests.
- Production retention duration and anonymization remain a release blocker until a business policy is supplied; no retention period is invented by this plan.

### 6. End-to-end validation and documentation

- Verify the complete flow: Shop Design price → Work snapshot → AUTO/MANUAL invoice → optional discount/tax → issue/number → partial/full payment → balance/history/PDF → credit note/refund → restored backup.
- Validate permissions and cross-Shop isolation at every API and file boundary; test retries, concurrency, invalid money precision, rounding residuals, refund ceilings, and immutable history.
- Run focused backend/frontend tests, migration replay against disposable PostgreSQL, schema/OpenAPI checks, typecheck/build, and an authenticated local browser/API flow where the configured environment safely permits it.
- Perform UI checks at narrow-phone (~320–360px), normal-phone (~390–430px), tablet (~768–1024px), and desktop widths; verify the existing component/button patterns, no horizontal overflow, readable money values, and usable touch targets.
- Apply/replay migrations only on disposable isolated PostgreSQL databases within this package. Do not write to the persistent local application DB; migrating that database is explicitly outside this one-shot scope. Never alter staging/production or deploy in this package.
- Update only verified-current Business Rules, Decisions, Phase 5, Data Flow, API Flow, Dependency Impact, and Change Compatibility sections that materially change. Record exact tests, database target, and limitations in Project State/Handoff; run the repository project-state validator.

## Explicit unresolved gates / excluded claims

- Tax is a simple optional invoice-level rate as approved. Jurisdiction-specific legal compliance, registration numbers, and statutory invoice wording are not claimed or built without a jurisdiction-specific decision.
- Backup retention duration/anonymization must be decided before production readiness; isolated restore verification can be developed without inventing that policy.
- Supplier-wide consolidated reporting is excluded; Shop-scoped financial history is the safe initial boundary.
- External payment processing, external notification providers, staging/production migration, deployment, commit, and push are excluded.
- Persistent application-DB migration, staging/production migration, and deployment are excluded. Browser E2E/environment readiness are verified only if actually run; source/tests alone are not proof.

## Completion criteria

1. All implemented UI/API flows enforce the approved policies above, with no cross-Shop access or duplicate financial effects on retry.
2. Fresh disposable migration replay, focused tests, frontend build/typecheck, API/schema checks, and the end-to-end local flow pass; failures are reported without weakening tests.
3. Existing Work, Design, Measurement, Order, and financial history is preserved; currency and historic-money meaning are not silently changed.
4. Current-state docs accurately distinguish implemented behavior, approved-but-not-implemented policy, and production blockers.
5. No staging/production change, commit, push, or deployment occurs.

## Single approval gate

After review of this roadmap, one `CONFIRM TASK PHASE-5-INTEGRATED-CLOSURE-01` authorizes the in-scope local implementation workstreams above. No separate R5-01/R5-02/R5-03/R5-04/R5-05 confirmation will be requested. Any materially new business rule, external deployment, production/staging write, or scope outside this roadmap remains excluded and requires separate direction.
