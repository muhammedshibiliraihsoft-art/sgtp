# Project State

## Phase 5 local migration closure (2026-10-26; unpublished)

The user authorized the local `devdb` migration after review of the exact plan.
All 9 pending migrations (`catalog.0025`/`0026`, `works.0003`, and
`billing.0001`–`0006`) applied successfully; `migrate --plan` reports no
pending operations. Before migration, a backup was created, archive-validated,
and restored into a disposable PostgreSQL database. Comparing that restored
copy with current `devdb` found no row-count changes in pre-existing
business/catalog/work tables. Only expected Django permission/content-type and
migration-ledger counts increased; 12 new Phase 5 tables were added. The exact
comparison DB was removed. The ignored local backup remains at
`.test-private-assets/phase5-devdb-backup-20261026-d19f24a3726e/` for recovery.

Fresh focused backend billing/pricing tests passed **21/21** on an isolated
disposable test database, which was removed. Django system check and
`makemigrations --check --dry-run` passed. Local frontend `/` and backend
readiness returned HTTP 200. Prior frontend validation remains 13/13 focused
tests, 233/233 full suite, typecheck and production build; prior authenticated
synthetic billing E2E remains documented. No feature code changed in this
refresh. Staging is deferred; no staging, commit, or deployment action occurred.

Local Phase 5 database setup is complete. Overall Phase 5 remains **PARTIAL**
for release because production backup/object-retention, monitoring, restore,
deployed parity, and any applicable retention/anonymization policy remain
unverified. Port 8001 did not return an HTTP health response; backend readiness
on `8000` is healthy.

The Project State Validator passed and discovered 593 backend tests; full-suite
test discovery is not a claim that all 593 ran in this refresh. Remote
verification was unavailable and the working tree remains dirty.

## Current follow-up — Manual Super Admin financial purge (2026-10-25; local, unpublished)

Current task: PHASE-5-INTEGRATED-CLOSURE-01 follow-up — approved manual Main
Supplier Super Admin invoice-bundle purge, implemented and locally validated.

Implemented the approved manual invoice-bundle purge in the canonical backend
and supported sibling frontend. Only Main Supplier Super Admin can choose a
Shop, review its invoice history, and purge an issued bundle after providing a
reason and exact invoice-number confirmation. Purge deletes the invoice, lines,
linked payments/credit notes/refunds, financial-document metadata, and private
files; existing audit/idempotency records and Shop invoice/credit sequences
remain. A tombstone and new audit event record the request/result. If private
file deletion fails, financial DB rows remain and the same operation can be
retried. Automatic deletion is not implemented.

`billing.0006` is additive and unapplied to persistent `devdb`; no existing
financial bundle or persistent R2 object was deleted. A unique synthetic R2
object upload/read/checksum/delete probe passed through the app's
`PrivateReferenceStorage` adapter and was absent afterward; it did not touch
existing objects. A separate presigned PUT returned HTTP 200; object metadata,
private read/checksum, deletion, and absence verification passed. This tests
the configured provider URL, not the separate Catalog private-media
upload-ticket/browser flow; Billing PDF generation does not call that Catalog
endpoint. Headless Chrome device viewport emulation with mocked responses verified the Work Billing panel, Billing History (All and Outstanding), and Design Editor Shop-price panel at 320, 390, 600, 768, 1024, and 1280 CSS px; the Financial Purge page was checked at 320, 360, 390, 600, 768, 1024, and 1280 px. Document/body widths matched each viewport and overflow scans found no out-of-viewport elements. Main page screenshots at 320px and 1280px were visually reviewed; the New invoice disclosure was opened at 320px and the purge confirmation dialog was checked at all purge widths. The mocked responsive runs submitted no business mutation. Separately, authenticated headless Chrome browser-to-API E2E used only synthetic records on disposable PostgreSQL `sgtp_p5_ui_e2e_f8436c08`: the Main Supplier Super Admin purged synthetic `INV-000001` through the UI, which reported success; a DB check confirmed the invoice and linked payment/credit/refund/document rows absent, with a `COMPLETED` purge tombstone and one idempotency row retained. The disposable DB, test servers, Chrome profile, and temporary test folder were removed; `devdb` remained untouched. The first login attempt exposed a test-only password-hasher mismatch; only the synthetic user's hash was regenerated under the local `dev` settings before the successful E2E. Automated FinancialPurgePage tests cover Shop loading/disabled, Shop-list error/retry, invoice-history loading/error/retry/empty, draft exclusion, exact confirmation, storage-failure protection, and repeating a failed purge. Retry now repeats the failed Shop load, invoice-history load, or purge operation. The focused page suite passed 8/8 and the full supported frontend passed 233/233; typecheck/build also passed. Targeted lint exited 0 with two `react(set-state-in-effect)` warnings in this page. These automated checks do not replace exhaustive manual visual verification of every state at every viewport. A fresh focused backend purge rerun passed 3/3 on disposable PostgreSQL
sgtp_p5_purge_gate_20261025_f0361ddd; the test runner destroyed it and a
read-only PostgreSQL catalog check confirmed the database absent afterward; FinancialPurgePage focused tests passed 8/8; the full supported frontend
suite passed 233/233, with typecheck/build passing. Targeted lint exited 0
with two `react(set-state-in-effect)` warnings in this page. On 2026-10-25, the full Django suite passed 486/486 on a
unique disposable PostgreSQL DB, the full pytest suite passed 593/593 (392
warnings), the supported frontend passed 233/233; typecheck/build passed, and targeted
lint exited 0 with two `react(set-state-in-effect)` warnings in FinancialPurgePage. Django system check and migration drift
check passed. A fresh disposable migration + PostgreSQL dump/restore verified
financial totals, Shop ownership, and one private A5 invoice PDF checksum;
receipt/credit-note file restore was not verified. Exact test/restore DB names
were absent after cleanup. Configured `devdb` remains unmigrated and untouched.
The Project State Validator passed after this documentation update; test
discovery was unavailable and it warned that the working tree is dirty. This
follow-up does not close Phase 5:
production backup/object-retention alignment,
production restore/monitoring, and deployed parity remain open; manual purge
does not define an automatic retention period or anonymization policy.

## Status

### PHASE-5-INTEGRATED-CLOSURE-01 (2026-10-22; local, unpublished; PARTIAL)

Current verified status is refreshed in the 2026-10-25 follow-up above; the
dated checkpoints below preserve their original test counts and limitations.

Current task: PHASE-5-INTEGRATED-CLOSURE-01; CONFIRM TASK PHASE-5-INTEGRATED-CLOSURE-01.
Phase 5 is active; activation was explicitly confirmed with `CONFIRM PHASE 5`.

The confirmed local package includes per-Shop Design pricing and Work
price/currency snapshots, the supported sibling price/Billing/history UI,
approved invoice/discount/tax/number/void/credit/refund rules, financial
authorization, audit/idempotency, private localized PDFs, and additive
migrations through `billing.0005`. The latest API/frontend correction adds
optional `billing_currency` to Shop context only for Shop ADMIN and active
CASHIER STAFF; normal staff still receive no financial Shop setting. No
migration was applied to the persistent application database.

Latest local validation (2026-10-22): fresh disposable Django suite 483/483 and
fresh disposable pytest suite 590/590 (389 warnings); the earlier backend
587/587 and focused post-contract 54/54 results are historical checkpoints.
`makemigrations --check --dry-run` and Project State Validator passed (590 tests
discovered). The supported sibling frontend passed Vitest 225/225 and its
production build/typecheck. OpenAPI validation passed with 0 errors / 29
existing warnings and four generated backend/sibling schema artifacts matched.
A focused schema-context privacy test confirms non-financial staff are
unchanged.

2026-10-25 revalidation: Django system check reported no issues; migration
drift check found no changes; Project State Validator passed with 590 tests
discovered. The supported sibling frontend was rechecked: Vitest 225/225,
production build/typecheck passed, and lint exited 0 with existing warnings.
The focused disposable Django Billing/Work API suite also passed 38/38. A
repeat fresh migration plus PostgreSQL dump/restore and A5 invoice PDF v2
checksum check passed against isolated databases; cleanup confirmed the new
restore/test databases and temporary media absent. `devdb` still had no Billing
migrations and was not written.

Authenticated browser E2E used only synthetic Shop/user data in disposable
PostgreSQL database `sgtp_p5_restore_source_9d3a61c542be`: AUTO and MANUAL
invoice drafts, fixed and percentage discounts, optional tax, sequential issue
numbers, partial payment, credit note, payment-linked refund, unpaid-invoice
void, Billing History, and Outstanding were verified; Work remained at Request.
The initial issue failure was invalid fixture setup (numbered seed records with
no matching Shop sequence rows), corrected in the test helper, not in runtime
numbering code.

Fresh disposable migration replay and PostgreSQL dump/restore verified money
totals, Shop ownership, and one private A5 invoice PDF v2 checksum/file across
restore; the invoice/receipt/credit-note protected downloads and cross-Shop
denial are separately covered by API tests. On 2026-10-25, read-only cleanup
checks confirmed the exact 2026-10-22 and 2026-10-25 restore source/target DBs,
the focused disposable test DB, dump, and temporary media absent; only `devdb`
and the pre-existing `test_devdb` were listed. `devdb` has no Billing
migrations and was not written or migrated.
Local filesystem storage is verified. Required R2 setting assignments are
non-empty in the ignored local `.env`; HeadBucket returned HTTP 200, and one
unique synthetic object passed upload/read/checksum/delete with absence
confirmed afterward. No existing object was touched. Application-generated
presigned uploads and browser integration remain unverified. No
Sentry/error-tracking SDK or DSN configuration was found in this checkout or
local environment. Production alert delivery/monitoring remains unverified;
retention/anonymization and production restore also remain open. The bounded
synchronous PDF path has no worker; no
retry/dead-letter worker behavior is claimed. No staging/production, commit,
push, or deployment occurred. Phase 5 remains **PARTIAL** pending the remaining
R5-04/production reliability gates and final cleanup/state verification.

### Follow-up — Portrait A5 PDF exports (2026-10-22; local, unpublished)

Measurement worksheets and newly generated invoice, receipt, and credit-note
PDFs now use portrait A5. Financial PDF layout version 2 is additive;
immutable A4 layout-version 1 files remain unchanged and downloadable. The
`billing.0005` migration and all four backend/supported-sibling schema
snapshots were validated. Five focused renderer/API tests passed on a fresh
disposable `test_devdb`, which was removed afterward; Django checks and schema
validation passed with 0 errors / 29 existing warnings. Representative A5
PDFs were visually checked for legibility, wrapping, and page size. Persistent
`devdb` was not migrated or written; Phase 5 remains **PARTIAL** and no commit,
push, or deployment occurred.

### Historical checkpoint — R5-01 Shop Design pricing and Billing backend (2026-10-21; local, unpublished)

- Current task: R5-01 is complete locally; `CONFIRM TASK R5-01` and `APPROVE R5-01 EXPANSION PLAN` were provided.
- Phase 5 is active; activation was explicitly confirmed with `CONFIRM PHASE 5`.

Implemented the approved Shop-specific Design pricing and Billing backend:
Shop ADMIN or CASHIER STAFF may set/read prices; Work stores price/currency
snapshots; invoices support AUTO snapshot or MANUAL lines, multiple invoices
per Work, draft edits, issue, invoice-bound partial payments, and outstanding
reads. Drafts may be created at any Work stage; issue/payment never advances
production. Related Person invoices belong to the Primary Client. A regression
found and fixed an ordered-`distinct()` query that misclassified repeated
same-currency invoices. Focused backend tests passed 30/30 on disposable
PostgreSQL 15, including tenant/permission scope, currency precision, Work
snapshot, stage isolation, issue immutability paths, and Primary Client billing.
Django model check and migration-drift check passed; OpenAPI generation
validated with 0 errors (existing warnings remain). Additive migrations were
generated but not applied to the configured application `devdb` or any shared
database. No frontend billing UI, catalog price-catalog, idempotency/audit,
reports, commit, push, deployment, or browser E2E is included. Overpayment
policy, refunds/cancellation, currency-change policy, and invoice numbering
remain unresolved. Current API overpayment rejection is fail-closed, not an
approved business rule.

### Historical task — T4-06 Domain integration validation (2026-10-21; local, unpublished)

`CONFIRM TASK T4-06` authorized the historical Phase 4 API integration validation.

`CONFIRM TASK T4-06` authorized Phase 4 API integration validation. A new Work
API regression creates a Work from its Client, published DesignVersion, and
MeasurementSet; assigns and advances through every approved stage to
`COMPLETED`; verifies those exact source IDs remain linked; and confirms a
foreign-Shop ADMIN sees an empty list and receives 404 for Work detail.
Existing tests separately reject foreign-Shop Client, wearer, DesignVersion,
and MeasurementSet IDs. Backend Work tests passed 22/22 on fresh isolated
PostgreSQL 15 after replaying migrations through `works.0002`. Django removed
the test database `test_sgtp_t406`; persistent `devdb` and `testdb` were not
used. Sibling Orders tests passed 36/36; frontend typecheck/build, Django model
check, migration-drift check, and project-state validator tests (35/35) passed.
The project-state validator passed with its existing dirty-tree warning and a
test-discovery warning because `pytest` is not installed in this Python
environment. Authenticated browser-to-API E2E,
staging, and production were not tested. No application behavior, API
contract, schema, or migration changed; no commit, push, or deployment
occurred. At this checkpoint, Phase 5/R5-01 remained separately gated.

### T4-05 Service layer and concurrency (2026-10-21; local, unpublished)

`CONFIRM TASK T4-05` authorized Work service/concurrency hardening. All Work
mutations now write an internal append-only `WorkEvent` atomically with the
Work change; event state excludes note contents. Stage advancement requires the
currently displayed `expected_status`; a stale or replayed stage returns 409
without a second transition. The active sibling Orders caller sends this
precondition and refreshes detail after a conflict. Backend Work API tests
passed 21/21 on a fresh isolated PostgreSQL database, including concurrent
same-stage requests (one 200, one 409), replay, event rollback scope, and
notes-free audit snapshots. Frontend Orders API/page tests passed 33/33;
typecheck, production build, Django model checks, migration drift check, and
OpenAPI validation passed (0 errors, 29 existing warnings). Tests used a fresh
disposable PostgreSQL database, which Django dropped afterward; `testdb` was
not used. After read-only verification of configured `devdb` / `devuser` in
Docker `django_app_db` and its existing `works.0001` ledger, additive migration
`works.0002_workevent` was applied to that local development DB. Post-migration
read-only checks found 4 existing Works and 0 events; no historical events
were fabricated. Backend/frontend liveness returned HTTP 200. No commit, push,
deployment, or authenticated browser-to-API E2E was performed.

### ORDER-DUE-INDICATOR-API-UI-CLOSURE-01 (2026-10-21; verification complete)

The focused backend due-indicator tests passed 3/3 against an explicitly named
isolated PostgreSQL test database, including Shop-local cutoff boundaries and
Work API list/detail serialization for OVERDUE, DUE_TODAY, DUE_SOON (+1/+2),
UPCOMING, and null due dates. The test database was removed by Django after the
run; persistent `devdb` and the existing `testdb` remained present and were not
used for test writes. Active sibling Orders tests passed 35/35; frontend
typecheck and production build passed; Django model checks passed. No product
behavior, API contract, schema, or migration changed. No authenticated
browser-to-API E2E harness is available, so that runtime presentation check
remains unverified; frontend component rendering and backend API serialization
are independently covered by tests.

### ORDER-WORKFLOW-LOCAL-E2E-CLOSURE-01 (2026-10-21; local E2E completed)

**Current result:** The user explicitly authorized local testing of existing
functions and specified that `ORD-000002` must remain unchanged. Verified local
pair: canonical backend `127.0.0.1:8000` and supported sibling frontend
`127.0.0.1:5173`; backend liveness/readiness and frontend proxied readiness
returned HTTP 200. The database is persistent user-data development state:
`devdb` / `devuser` in Docker `django_app_db`, Compose project `devcontainer`,
volume `devcontainer_pgdata`.

One user-approved test Order, `ORD-000003`, was created with the selected
Client, MeasurementSet, and published DesignVersion. It was assigned and
advanced through Request → Cutting → Stitching → Check → Finishing → QC →
Completed. Each transition cleared assignment, and assignment was repeated at
each next stage. CHECK was exercised distinctly. An ineligible STAFF assignment
at Stitching was rejected. After the run, the normal Orders list showed
`ORD-000003` Completed and `ORD-000002` still Request / Normal / no due date;
the latter was not modified.

The user's authorization permitted temporarily granting all eight current Work
Functions to the existing Admin membership for the test; its active function
set was restored to its original empty state using the existing service. A
current read-only DB check confirms the Admin remains empty and the other
member's pre-existing CASHIER/QC/SALES assignments remain active. No role
changed. Eight soft-deleted function-history rows remain. `ORD-000003` remains
Completed and unassigned; it was not deleted as cleanup.

Deleted Orders filtering was exercised in the UI read-only: the exact
2026-10-18 date range returned existing `ORD-000001`, 2026-10-19 returned the
empty state, and Clear restored the unfiltered record. The focused backend Work
API suite passed 15/15 again on isolated PostgreSQL 15; its deleted-order
coverage includes Shop scope, dates, validation, and access denial. The focused
frontend Orders suite passed 25/25 again; typecheck/build passed earlier in
this task. Django `check --tag models` passed. The due-indicator unit test
passed for Shop-local overdue, today, two-day DUE_SOON, and upcoming cutoffs.
The current `devdb` Orders both have no due date, so actual API-to-UI due badge
rendering remains unverified. No application code, schema, API contract, or
migration changed; no commit, push, or deployment occurred.

The initial pre-authorization snapshot below is historical and superseded by
this execution result.

The supported frontend Order flow was revalidated: Orders, Orders API, and
Deleted Orders tests pass 25/25; frontend typecheck and production build pass.
Canonical backend model/system check passes, and the focused Work API suite
passes 15/15 against an isolated PostgreSQL 15 test container. Tests cover
Shop-scoped listing/deleted filtering, stage sequence/function requirements,
assignment clearing after a transition, and completion. The inline stage action
remains sequential: only the next stage is actionable, the existing advance API
is called, pending requests disable repeat actions, and the displayed stage
changes only from a successful response.

On 2026-10-21, authenticated local UI read-only checks loaded the Dashboard,
Orders list, and detail for `ORD-000002`; the list/detail agreed on the order.
Its detail showed Request / Normal, no due date, the selected Client, a linked
Measurement page, and a DesignVersion reference. This is a record in the
persistent user-data development DB, not a disposable test Order. No Order
fields or stages were changed. A read-only ORM check confirmed its MeasurementSet
belongs to the same Client and Shop, and its published DesignVersion is Shop-
available and matches the MeasurementSet's Abaya Family. The Order's Client,
MeasurementSet, and DesignVersion IDs match the earlier user-opened New Order
URL inputs. The Deleted Orders page also loaded its read-only history and date
filters. A read-only eligibility query found active Shop function assignments
for SALES, QC, and CASHIER only; CUTTING, STITCHING, CHECK, and FINISHING have
no active eligible members in this Shop. The current Order is unassigned, so
live UI stage progression/reassignment is blocked by the plan's existing-user
eligibility gate. Memberships and Work Functions were not changed.

On the latest 2026-10-21 runtime check, the canonical backend is running at
`127.0.0.1:8000` and the active sibling frontend at `127.0.0.1:5173`. Backend
liveness and readiness both return HTTP 200; the frontend `/api/health/ready/`
proxy also returns HTTP 200. The listening Vite process runs from
`sgtp-frontend/frontend`; its `.env.local` sets `AUTH_API_PROXY_TARGET` to
`http://127.0.0.1:8000`. Although that checkout's `.env` contains the staging
API origin, the active local Vite configuration uses the local `.env.local`
override, corroborated by the proxied health response. `.env` identifies
`devdb@localhost:5432`; the
connection maps to `django_app_db` in the `devcontainer` Compose project,
backed by persistent volume `devcontainer_pgdata`. A read-only query confirmed
database `devdb` and role `devuser`. This is the configured development
database, not a disposable test target. `.env.test` points to `testdb@db:5432`;
it was not contacted. Backend tests used a separate PostgreSQL 15 container
`codex_order_acceptance_test_20261021`, bound only to `127.0.0.1:55439`, with a
new isolated Docker volume and test-only role/database. The test runner created
and removed its own test database there; it did not connect to or alter `devdb`.
The frontend Order tests pass 25/25, typecheck and production build pass, and
`manage.py check --tag models` passes. Live UI stage progression and the
Order-to-COMPLETED end-to-end flow remain **UNVERIFIED** because the only
visible Order is in persistent `devdb`, not an explicitly designated disposable
test environment.

The four-block acceptance plan in
[ORDER-WORKFLOW-LOCAL-E2E-CLOSURE-01](task-plans/ORDER-WORKFLOW-LOCAL-E2E-CLOSURE-01.md)
is in progress. Runtime pairing, read-only Order list/detail/history, frontend
regressions, and disposable-PostgreSQL Work API checks are verified. Live
Order stage transitions/reassignment remain unverified because the current
Order is in the persistent user-data DB.

### Create Order final closure (2026-10-20; local, unpublished)

New Work now requires an ACTIVE parent Family and Design plus an available
published DesignVersion. Creation locks Shop → Family → Design, so the
current Family state is checked in the same transaction as sequence allocation;
archiving a parent blocks new Work but does not hide existing Work. Design
list/detail responses include read-only `family_status`, which the Order picker
uses to omit Designs beneath archived Families. A URL-preselected Material is
not silently discarded when catalog lookup fails: creation remains blocked
until the Material is verified, replaced, or explicitly cleared. When no
Material was preselected, a lookup failure does not prevent a no-material order.
No schema migration is required.

Validation: disposable-PostgreSQL Work API tests 15/15; supported sibling
Orders, Measurement Review and Client Measurements tests 34/34; frontend
typecheck, Django system check and migration drift check passed. OpenAPI
generation validates with 0 errors / 29 existing warnings. Browser E2E remains
unverified; no shared development, staging or production database was used.
No commit, push or deployment.

### Create Order archive-eligibility closure (2026-10-19; local, unpublished)

New Work creation now rejects a published DesignVersion when its parent Design
is archived. The authoritative model validation is reached by the transactional
creation service, which locks the Shop and then Design row to serialize against
Design archival; existing Work and its protected source references remain
readable. No schema change or migration is required. Archived-Family eligibility
is not defined by approved rules and remains a business decision.

Validation: archived Design creation was reproduced as a 201 before the fix;
the focused disposable-PostgreSQL Work API suite now passes 12/12, including
historical Work read, active/global Design, family/measurement compatibility,
authorization, and cross-Shop wearer/Design/Measurement rejection. Focused
supported-frontend order and Measurement Review suites pass 15/15 and typecheck
passes. Both OpenAPI snapshots were regenerated: 0 errors, 29 existing
warnings. Full Client Measurements page run remains 16/18 because two existing
expectations conflict with current behavior/accessibility markup. Browser
Create→detail→list E2E is unverified; no dev, staging, or production DB was
changed. No commit, push, or deployment.

### Variant retirement release-blocker correction (2026-10-19; local, unpublished)

Repository verification confirmed that `0018_seed_remaining_family_design_defaults`
skips all Family option-group/option/Design seeding for a family when it finds no
active global Variant. Added forward-only data migration
`catalog.0025_reconcile_family_design_defaults` after `0024`; it reuses the
approved `0018` preset definitions, fills only missing global Family defaults,
creates missing presets with `variant=NULL`, and leaves same-name Design rows,
versions, selections and Shop-owned catalog data unchanged. Its reverse is a
no-op to avoid deleting default data that may already be copied or referenced.

The second reported blocker is already resolved in the current backend source:
Global/Shop Variant list/detail views permit read methods only and lifecycle
views permit OPTIONS only; existing API tests assert write attempts return 405.
Mutation service functions and handler bodies remain in source, but the current
HTTP method guards make them unreachable. One stale Measurement test that still
expected Variant archive to return 200 now verifies 405, legacy Profile reads,
and Family-level new records after an inactive legacy Variant is set up in the
test.

Validation (CATALOG-0025-DISPOSABLE-POSTGRES-REPLAY-AND-DB-VERIFICATION-01,
2026-10-19): a new isolated PostgreSQL 15 instance was bound only to
`127.0.0.1:55439`; Django's effective target was explicitly checked before DB
commands. Fresh replay passed through `catalog.0025`, then `works.0001`; the
exact `catalog.0017`–`0025` ledger was present. A second database reproduced
the no-active-Variant `0018` skip (Abaya presets 0/3), then verified `0025`
repaired Family groups/options/translations, published presets, selections and
Family-only measurements. A third database upgraded representative Variant-era
Design/version history, Family-level and Shop-owned records, and measurements;
all snapshots remained intact. Reversing `0025` left data unchanged, and
reapplying it was idempotent. `manage.py check` and
`makemigrations --check --dry-run` passed.

Selected DB-backed tests: 100/108 passed. The eight failures are confined to
test setup/environment: one new reconciliation test calls nonexistent
`SafeDeleteQueryset.hard_delete`; six Measurement tests still construct or
filter the retired `MeasurementDefinitionMapping.variant` field; one Catalog
image-upload test cannot resolve its Cloudflare R2 endpoint. These are test
harness incompatibilities, not proven migration/runtime regressions; the
manually replayed critical scenario passed.
The broader backend suite was not run because focused tests did not all pass.
All migration/test DB writes were confined to the disposable PostgreSQL
instance; development, staging, and production databases were not touched. No
application code, historical migration, commit, push, or deployment was
changed.

**Release verdict: FOUNDATION MIGRATION PARTIAL — fresh, Variant-absent and
upgrade migration safety are verified; stale Measurement/reconciliation test
fixtures and the external R2 test environment remain unresolved, so broader
backend validation is pending.**

### Variant-retirement staging release preflight (2026-10-18; read-only, local)

Render identifies the staging API source as repository `sgtp`, branch `staging`,
root Docker context / `./Dockerfile`, auto-deploy on commits, and live SHA
`4db6d9fe14d389c89721707e44ed4526af6a5be3`. That SHA is present in the local
Git object database and equals `origin/staging`; its source still contains
Variant mutation methods and Variant-compatible Design/Profile create fields,
and does not contain `catalog.0024_retire_variant_measurement_mappings`. Thus
staging is not at the current Family-based retirement candidate. No Render
frontend service was listed; Pages source/settings remain unverified. The
current executor could not resolve the API hostname. The staging DB's empty IP
allowlist blocked read-only SQL, leaving its migration ledger and Variant
mapping count unknown; 0024's fail-closed startup precondition is therefore a
release blocker. No code, provider config, staging/local app data, commit, push,
or deployment was changed.

Fresh migration replay including 0024 passed while creating disposable
`test_devdb`, which the test runner removed. Backend suites ran 164 tests with
2 failures (R2 network fixture and an old test expecting the now-retired Variant
archive mutation); supported frontend tests ran 60 with 3 failures. Frontend
typecheck, Django check, and `makemigrations --check --dry-run` passed. Full
details are in the current handoff section below.

### Variant middle-layer retirement implementation (2026-10-18; local, unpublished)

The confirmed retirement is implemented in the canonical `main` backend and
active sibling frontend within their assigned ownership areas. Global/Shop
Variant endpoints now preserve authenticated legacy list/detail reads but reject
mutations (405); Work Design/Profile compatibility checks use Family identity.
The active sibling frontend resolves Order profiles by Family, prefers the
Family-level profile, and starts a new Family-level Measurement profile rather
than extending a legacy Variant-linked profile. Legacy Variant rows, nullable
Design/Profile references, model relations, and historical seed migrations
remain for compatibility. This task did not apply a migration or write to an
application database. The dirty checkout already contains
`catalog.0024_retire_variant_measurement_mappings`, which removes only the
MeasurementDefinitionMapping Variant field after a fail-closed precondition;
its application is documented for the local snapshot but was not re-queried in
this task. Staging migration/data state remains unverified.

The retirement is **PARTIAL across local checkouts**: the separate `main`
frontend still contains Variant UI, and the sibling checkout's duplicate
backend still contains stale Variant contracts. Ownership instructions prohibit
changing those copies from this task's respective worktree; do not pair the
stale copies with the canonical backend/active frontend. Deployment/runtime
parity remains unverified. Focused backend checks passed (12/12 targeted tests,
Django check, migration drift); active sibling frontend typecheck and focused
tests passed. A broader backend test run was stopped when tests attempted remote
R2 fixtures that could not resolve in this environment; broader frontend suites
also have remaining failures. See `docs/HANDOFF.md` for details. No commit,
push, or deployment occurred.

### Variant cross-checkout support boundary (2026-10-18; local)

The one supported local pair is `sgtp` backend on `main` with
`sgtp-frontend/frontend` on `frontend/parallel-foundation`. Runtime evidence:
the current Vite process on port 5173 is launched from that sibling frontend;
Docker `django_app_web` is bind-mounted from the canonical `sgtp` main
worktree; the sibling frontend local env file points its API proxy to
`127.0.0.1:8000`.

Two copies are intentionally deprecated, not supported or pairable: `sgtp/frontend`
still mounts Variant UI; `sgtp-frontend/apps/` still has a Design create
serializer requiring `variant_id`. Both remain technically runnable, but
worktree ownership prevented implementation edits. `frontend/README.md` and
`docs/ENVIRONMENTS.md` now mark the support boundary. No code, schema, migration,
legacy data, or database was changed. There is no launcher-level block; do not
mistake documentation status for technical prevention of manual startup.

### Variant retirement dependency audit (2026-10-18; local, unpublished)

The user resolved the business policy: active Variant selection, management,
and materialization are retired; Global/Shop bootstrap must not require active
Variant rows; retained rows/FKs are only for compatibility, immutable history,
or migration safety. Current repository code is **incomplete retirement**:
local `main` still has writable Variant APIs and management/Design-selection
UI; its Work model compares Design/Profile Variant IDs; direct Profile model
creation still permits a Variant; catalog seed migrations create/use active
Variants. The sibling backend still requires Variant for Design creation, and
its Orders UI matches Profiles by Variant. The `main` Design/Profile APIs are
Family-level, and Shop catalog initialization copies no Variant rows.

Aligned the approved rule and current-state docs. This task changed documents
only; no code, migration, schema snapshot, database, runtime, or deployment was
changed or queried. No tests were run. Migration application state and actual
data reference counts remain **UNVERIFIED**. The safe correction sequence is
recorded in `docs/architecture/03-DEPENDENCY-IMPACT-MAP.md`; implementation
requires a separate task. `python scripts/verify_project_state.py` exited
PASS with the existing dirty-tree and unavailable-test-discovery warnings;
`git diff --check` exited PASS with existing line-ending notices. Product tests
and runtime/database checks were intentionally not run.

### Dependency map audit (2026-10-18; local, unpublished)

Updated only §1 of `docs/architecture/03-DEPENDENCY-IMPACT-MAP.md` from current local backend and frontend code. The map now separates required Work references from optional Material/RelatedPerson/assignment links, distinguishes a MeasurementSet's optional published DesignVersion reference from MeasurementProfile ownership, and shows Shop access, action-level Work Functions, inventory movement/balance behavior, and frontend-to-API consumption. The Orders UI is in the sibling frontend checkout; Client and Measurement UIs are in this checkout.

At that audit, the bootstrap/documentation mismatch was unresolved. The user has since resolved the Variant policy; this follow-up confirms bootstrap service behavior is aligned but identifies remaining active code/migration dependencies as incomplete retirement. No product code, APIs, schema/migrations, tests, or database were changed; no runtime/deployment check was performed in that earlier task. Its recorded validator/diff-check result is historical.

### Deleted Orders archive (2026-10-18; local, unpublished)

The existing Request-stage Work deletion remains a recoverable soft delete. An ADMIN-only, read-only `GET /api/v1/shops/{shop_id}/works/deleted/` archive now lists only the selected Shop's deleted orders, with search, pagination, and inclusive `deleted_from` / `deleted_to` filters interpreted in the Shop timezone. The separate frontend `/orders/deleted` page is linked from Orders for admins and offers date filters; no restore or permanent-delete action was added. No migration or application-data mutation was needed. Focused backend Work tests 8/8, Django check, migration drift, focused frontend Orders tests 10/10, typecheck and build passed. The local authenticated browser displayed the existing deleted order; matching and nonmatching date filters behaved correctly. No commit, push, or deployment.

- Historical checkpoint: T4-04 Work backend/frontend were locally implemented under `CONFIRM TASK T4-04` and remained unpublished. The `ORDER-WORKFLOW-LOCAL-E2E-CLOSURE-01` revalidation was then partial; authenticated E2E was blocked until Docker, an explicitly isolated PostgreSQL target, and local app listeners were available. This checkpoint is superseded by the later T4-06 and local E2E evidence above.

- Local Docker runtime update (2026-10-16): after explicit user approval, applied `tenants.0010` and `works.0001` to the existing `devdb` used by `django_app_web`. The Orders list now loads in the authenticated local browser and correctly shows an empty list (0 Work rows); the previous HTTP 500 was caused by the missing `works_workorder` table. User count remained 3 and Client count remained 1. No staging or production database was touched. Backend Work tests 6/6 and frontend Orders tests 6/6 passed; frontend typecheck and repository-state validator passed. No real Order creation was performed.

### T4-04 Work aggregate and workflow state (2026-10-16; local, unpublished)

Backend-only `apps/works` now persists one garment per Shop Work/Order with
protected Client, DesignVersion, MeasurementSet and optional Material links,
stable per-Shop Work number, Normal/Urgent/Very Urgent priority, optional due
date, and fixed Request → Cutting → Stitching → Check → Finishing → QC →
Completed transitions. New `CHECK` Work Function was explicitly approved.
ADMIN or SALES/MEASUREMENT STAFF can create; every transition requires an
applicable Work Function and clears the assigned worker for reassignment.
Due soon begins two Shop-local calendar days before delivery. API supports
Shop-scoped list/search/create/detail/update, assign, advance, and Request-only
soft delete. Migrations `tenants.0010` and `works.0001` were initially files only; they were subsequently applied to the approved local Docker `devdb` as recorded above. Disposable PostgreSQL Work/Function tests 23/23
PASS, Django check, migration drift, OpenAPI generation (0 errors),
project-state validator and its 33/33 tests PASS. T4-05 concurrency/idempotency/audit,
T4-06 integration, frontend and publication remain separate. No commit/push/deploy.

### MEASUREMENT-HEADER-RESPONSIVE-STRUCTURE-01 (2026-10-16; local, unpublished)

The Measurements page heading is structured as an icon/eyebrow, client-aware title, and supporting description in a background-free layout. The title wraps safely on narrow screens, and a subtle bottom divider separates the header from page content. No API, backend, or database changes.

### CLIENT-MEASUREMENTS-DESKTOP-RESPONSIVE-01 (2026-10-16; local, unpublished)

The embedded Client Measurements workspace is now capped at 1440px and centered on wide desktop screens. Desktop uses a compact two-column garment/design and fabric layout; the measurement form can place expanded saved history beside its inputs, while the closed form uses the full row. The review summary spans the content width. Tablet spacing is tighter in a single column; the phone wizard behavior is unchanged. Frontend production build and scoped `git diff --check` PASS. No backend, database, schema, or API changes; no commit, push, or deployment.

### MEASUREMENT-REVIEW-SUMMARY-ROWS-01 (2026-10-16; local, unpublished)

The Measurement final-review summary cards now render as compact label/value rows with subtle separators, reducing empty column space on mobile and desktop. Existing summary values, styling selections, and workflow are unchanged. Frontend typecheck and scoped `git diff --check` PASS; no backend, database, schema, or API changes. No commit, push, or deployment.

### MEASUREMENT-HISTORY-ON-DEMAND-01 (2026-10-16; local, unpublished)

Measurement history is now closed by default and removed from the mobile wizard's automatic step sequence. An explicit History button opens/closes the saved-version list on demand, including from final review after save. Opening a saved version from the Client page still seeds the measurement form without opening the history panel. Four focused frontend regressions and typecheck pass; no backend, database, schema, or API changes. No commit, push, or deployment.

The active entry flow now places `Add measurement` and `Measurement history` side by side above the Body measurements form. `Add measurement` uses the normal secondary style; History is the black primary action. When expanded during entry, the history panel appears between the action row and the Body measurements form; in final review it remains available on demand. History version cards use a responsive fixed-width grid capped at two cards per row.

### MEASUREMENT-REVIEW-DESIGN-GRID-01 (2026-10-16; local, unpublished)

Design-section cards in Measurement final review now use a responsive grid: at least two cards per row on mobile and additional cards as viewport space permits. Group labels and selected design details remain unchanged. Frontend typecheck and scoped `git diff --check` PASS; no backend, database, schema, or API changes. No commit, push, or deployment.

### GARMENT-SETUP-PARTS-AND-MEASUREMENTS-IMPLEMENT-01 (2026-10-13; local, unpublished)

Shop Catalog garment setup now reuses the existing Family, Variant, OptionGroup, and FamilyOptionGroup models and APIs. The family detail flow configures its style groups/cardinality, maps existing Shop-owned measurement definitions at Family or Shop Variant scope, creates a new Shop-owned definition with its mapping, and offers a return path to the in-progress Design draft. No parallel GarmentPart model or migration was added. The mapping endpoint validates active Shop ownership and family/variant consistency; global definitions remain immutable and saved measurement history is untouched. Backend focused tests 4/4 PASS (including scope/permission and Shop isolation); frontend focused tests 32/32 PASS; typecheck/build, Django check, migration drift, and OpenAPI validation PASS (0 errors; 29 warnings / 13 unique). Validation used disposable `test_devdb`; configured app DB `devdb` was not written. Existing dirty worktrees were preserved. No commit, push, staging/production access, or deployment.

### MEASUREMENT-PROFILE-SAVE-AND-RECOVERY-01 (2026-10-12; local, unpublished)

Measurement saves for Shop-materialized garments now validate against the same effective family/variant mappings as the definitions listing, including mappings inherited from the linked global template. The save validation had checked only mappings attached directly to the Shop-owned family, so a field visible in the UI was rejected on save. The client now refreshes profiles after a create conflict and selects the already-existing matching profile; if the failed request used a family ID no longer present in the refreshed active catalog, it clears the stale family/variant selection. Profile uniqueness remains enforced server-side and a different garment still creates its own profile. Regression coverage saves a local-template measurement and confirms it appears in set history; duplicate same-garment rejection plus a second-garment profile remain covered. Backend Measurement/Materials API: 34/34 PASS. Frontend Measurement page: 15/15 PASS; typecheck and production build PASS. Checks used disposable `test_testdb`; configured app DB `devdb` was not queried or changed. No schema/application-data changes, commit, push, or deployment.

### GARMENT-FAMILY-DEFAULT-MEASUREMENTS-01 (2026-10-12; local, unpublished)

All four seeded garment families now have a family-level body-measurement baseline. Existing Men's Shirt and Kuwaiti Dishdasha defaults remain unchanged; additive migration `catalog.0023_seed_abaya_darraa_measurement_defaults` adds Abaya and Darraa / Long Dress definitions without numerical sizing values or historical-data rewrites. Family mappings apply to every variant. The Shop `Add measurement` UI now creates family-level mappings so a new body-measurement field is available across that garment's variants. Regression coverage verifies exact ordered defaults for all four families through default-variant API responses and confirms a newly added family field appears for both selected and alternate variants. Measurement/Materials API: 34/34 PASS before the final family-scope adjustment; focused fresh-database regression after it: 2/2 PASS; approved defaults/concurrency: 8/8 PASS; frontend Measurement/API tests: 28/28 PASS after the UI update. Django check and migration drift PASS; migration Flake8/compile and scoped diff checks PASS. `black --check` stalled without output and was stopped. Tests used disposable `test_devdb`; after test validation, migration `0023` was applied to verified local application DB `devdb` (`devuser` at `127.0.0.1:5432`) and resulting mappings were verified. No staging/production database, commit, push, or deployment.

### GARMENT-DEFAULT-MEASUREMENT-STRUCTURE-RESTORE-01 (2026-10-11; local, unpublished)

The Measurement API now resolves effective definitions for a Shop-materialized garment family from both that Shop family and its linked current global `template_source`; a Shop variant also resolves its linked source-variant mappings. This restores approved structured family defaults without cloning mappings, changing schema, or adding garment-specific code. Effective API ordering uses the applicable mapping's order (rather than a shared definition order that can be changed by another family); supplemental Shop definitions retain their configured order. Active family/variant ownership remains scoped to the selected Shop, and definition rows remain restricted to global + that Shop. Regression coverage: materialized Men's Shirt defaults/order and deduplication; source-variant-specific addition; an independent Dishdasha family; Shop-local supplemental addition; and Shop A/Shop B isolation. Backend Measurement/Materials API: 33/33 PASS; approved seeded defaults + measurement concurrency: 8/8 PASS; frontend Measurement page/form: 25/25 PASS. Django check PASS; migration drift reports no changes, while migration-history consistency could not connect to configured test base DB `testdb`. Flake8 PASS; `git diff --check` PASS; project-state validator PASS (545 discovered tests, dirty-tree warning). Formatter validation was partially blocked by a pre-existing formatting discrepancy in the broadly dirty Measurement API test file and a later stalled Black process; no whole-file reformat was applied. Tests used disposable local `test_testdb`, which was removed afterward; configured local `devdb` was not written. No frontend change, migration, commit, push, staging, or production action.

### STYLE-OPTION-SNAPSHOT-LEAK-FIX-01 (2026-10-11; local, unpublished)

Root cause confirmed in read-only local `devdb`: the `sleeve` picker had 4 reusable global options plus 12 active Shop-owned Design snapshot copies (copy-suffixed codes), all serialized by the Shop style-option list. The shared Shop Catalog-options queryset now excludes rows with `source_style_option` set. The same filtered source is used by Shop Catalog listing, initial Design selection, Draft selection add/replace, and Shop option editing, so historical snapshots remain attached to existing Designs but cannot re-enter selectable Catalog flows. Regression test verifies list omission, rejection from Design creation/add/replace, and that copying a published Design still retains its independent snapshot. Focused regression + copy-preservation tests: 2/2 PASS. Full Catalog API module: 47/50 PASS; remaining 2 failures and 1 error are unrelated to this change: global-template publish test expects Shop ADMIN to publish despite current Main Supplier-only service gate (403), and two Arabic translation tests fail because the ephemeral test DB is WIN1252 rather than UTF-8. Django check PASS; migration drift reports no changes; project-state validator PASS with existing dirty-tree/test-discovery warnings. Tests ran against disposable `test_devdb`; configured `devdb` was read-only and unchanged. No migration, application-data edit, commit, push, or deploy.

### DESIGN-EDITOR-ACTION-BUTTON-STYLING-01 (2026-10-11; local, unpublished)

The Design editor's `Edit name`, `Add selection`, and reference-image `Upload` controls now have an explicit scoped secondary-button style: consistent horizontal icon/label alignment, visible border/surface, minimum touch height, hover, disabled, and focus states. This fixes the unstyled/stacked appearance without changing actions or API behavior. Frontend Design tests 13/13 PASS; typecheck/build PASS; `git diff --check` PASS (only pre-existing line-ending notices). No backend/database change, commit, push, or deployment.

### SHOP-DESIGN-CATALOG-SOURCE-AND-EDIT-01 (2026-10-11; local, unpublished)

Shop Design editor now reads garment-part mappings from the same Shop-scoped Family → Option Group API used by Measurements, rather than the global-only Option Group list. The exact screenshot Design exists in local `devdb`; its family has 8 configured mappings, confirming a frontend source-selection bug rather than missing catalog data. Draft Design names and individual Draft style selections are editable; selection replacement is transactionally validated by a new Shop/version-scoped endpoint. Published versions remain immutable; there is no duplicate catalog or migration. Frontend Design tests 13/13 PASS, typecheck/build PASS; focused backend Design API tests 3/3 PASS and system checks clean. `devdb` was queried read-only and not changed. No commit, push, or deployment.

### BACKOFFICE-GLOBAL-DESIGN-CREATION-IO-ROOT-CAUSE-01 (2026-10-11; local, unpublished)

The Back Office Global Design page no longer claims the global variant API is missing: the existing Main-Supplier-only `/api/v1/catalog/variants/` endpoint and frontend `getAllGlobalVariants(family)` helper are reused. The page now loads active global families, loads variants scoped to the selected family, creates a backend-validated family-level or variant-level draft, then navigates to the existing template editor. Existing Design styles are explicitly loaded by both Back Office list and editor routes, fixing direct-route unstyled rendering. No backend/API/schema/permission/lifecycle change or migration. Frontend focused Back Office Design tests 4/4 PASS; typecheck/build PASS. Backend Catalog variant + Design API tests 55/55 PASS; Django check PASS; migration drift `No changes detected`; OpenAPI validation 0 errors (29 existing warnings). No staging/production, commit, push, or deployment. The worktree was already broadly dirty; unrelated changes were preserved.

### BACKOFFICE-MINIMAL-CLIENT-SCOPE-CORRECTION-01 (2026-10-11; local, unpublished)

Back Office no longer exposes the Shop operational Measurements navigation/route. A read-only Client contact directory is available from an explicitly selected Shop and renders only name, phone, and email with neutral missing-value fallbacks; it reuses the existing Shop-scoped Clients API, which does not serialize measurement/tailoring records. Backend `MeasurementAccess` denies Main Supplier access to Client/Related Person profiles, saved versions, worksheets, and comparisons, while preserving explicitly selected-Shop measurement-definition configuration and existing Shop `ADMIN`/assigned `STAFF` behavior. Catalog is unchanged. Focused frontend suite: 28/28 PASS; typecheck/build PASS. Focused backend Client + Measurement/Materials suite: 42/42 PASS. Django check PASS; migration drift NOT REQUIRED (no model change); project-state validator PASS (test discovery warning: count not independently checked). No commit, push, staging, or production access/deploy.

### GLOBAL-CATALOG-ATOMIC-SAVE-02 (2026-10-11; local, unpublished)

Global Catalog family editing submits translations and ordered group IDs in one PATCH. The backend locks the global family and applies both under one transaction; the existing standalone group endpoint remains compatible and uses the same mapping replacement service. Tests reproduce the old split-request partial state and prove the combined request rolls back both metadata and mappings on a controlled failure. Backend Catalog API/concurrency/default tests: 51/51 PASS; focused atomic/isolation/auth tests: 7/7 PASS. Frontend focused Global Catalog/API/Shop Catalog/Variants suite: 42/42 PASS; typecheck/build PASS. Django system check PASS; OpenAPI 0 errors (29 warnings, 13 unique) and schema copies match. Migration drift reports no model changes; history check was unavailable because local base DB `testdb` is absent. Project-state validator PASS (532 discovered). No migration, staging/production DB access, commit, push, or deployment.

### CATALOG-SHOP-GLOBAL-FAMILY-READONLY-UX-ALIGN-01 (2026-10-10; local, unpublished)

Shop Catalog now treats a family as editable only when its structured `tenant` owner matches the current Shop and the role is not VIEWER. Global family/group configuration remains visible with disabled controls and an explanatory read-only hint; the Save action is omitted, and the handler independently refuses non-Shop-owned writes. Shop-owned editing remains available. No backend, API, schema, or Design behavior changed. CatalogPage + VariantsPanel tests: 21/21 PASS; frontend typecheck and production build PASS. Three local PostgreSQL backend regressions covering global rejection, Main Supplier global update, and Shop-owned configuration/Design validation PASS. No commit, push, Render access, or deployment.

### CATALOG-SHOP-FAMILY-GROUP-ISOLATION-FIX-01 (2026-10-10; local, unpublished)

The Shop family-option-group endpoint still reads active global families, but its PUT now locks the family and rejects global-family writes; only a family owned by the selected Shop can be reconfigured there. Main Supplier global changes remain on the Global Catalog endpoint. Regression coverage proves a rejected Shop A write leaves global rows unchanged, Shop B and a new Shop retain the global default, Shop A's owned-family config stays private, and Design publishing continues enforcing required/SINGLE/MULTI rules. No schema change or migration. Catalog API + approved defaults: 42/42 PASS on local PostgreSQL; focused isolation/global-management tests: 3/3 PASS. Django check, migration drift (`No changes detected`), OpenAPI validation (0 errors; existing warnings), `git diff --check`, and project-state validator (529 discovered tests) PASS. Frontend was not changed; the backend remains authoritative and rejects global-family PUTs. No staging/production DB access, commit, push, or deployment.

### SHOP-ADMIN-USER-ID-AND-PIN-01 (2026-10-10; local, unpublished)

The user-facing User ID is the exact entered `login_id` (preserve casing, trim outer whitespace); lookup/uniqueness remain case-insensitive. Generated `user_code` remains internal and accepted as a legacy alias, but Back Office/Edit Shop and Team credential surfaces show the entered User ID. New accounts receive a one-time six-digit PIN and require first-login change; PIN changes remain exactly six digits, replace the prior credential, and revoke sessions. Added migration `accounts.0008` to widen the `login_id` database format check; existing stored lowercase values are unchanged. Focused backend auth/Shop creation tests 32/32 pass; full frontend suite 170/170 pass after one transient Catalog pagination test failure passed in isolated and full reruns. Django check, migration drift, `git diff --check`, and project-state validator pass (525 tests discovered; existing dirty-tree warning). The full backend suite ran 420 tests: 417 passed and 3 errored. Captured errors include a missing admin static manifest entry for `core/api_browser.css` and a legacy membership migration test querying `accounts_user.login_id` before that column exists; the third error detail was truncated and remains unidentified. Black `--check` reports eight backend files would be reformatted; because those files contain broader existing changes, no file-wide reformat was applied. No commit, push, staging, or deploy.

### Historical checkpoint — BACKOFFICE-SHOP-ADMIN-USER-ID (2026-10-10; superseded by SHOP-ADMIN-USER-ID-AND-PIN-01)

The earlier implementation displayed generated `user_code` values in Edit Shop. The confirmed follow-up replaces that user-facing value with the entered `login_id` User ID; `user_code` remains internal/legacy alias. See current task above.

### CLOUDFLARE-FRONTEND-ENV-READINESS-09B (2026-10-10; local repository wiring only)

Cloudflare Pages now uses a shared frontend bundle and environment-specific runtime bindings (`API_ORIGIN`, exact `FRONTEND_ORIGIN`). The staging sample points to the active Render staging API; production has no default/fallback and must be configured only after its API exists. Missing/invalid bindings fail closed. `public/_redirects` retains the SPA fallback. No provider/dashboard changes, secrets, deploy, commit, or push. Pages root/build settings and live bindings remain externally unverified.

### STAGING-AUTH-INTEGRATION-AND-HARDENING-02 (2026-10-09; local partial, staging blocked)

Authentication rate limiting now selects its client-IP source through `AUTH_TRUSTED_CLIENT_IP_HEADER`, with the safe `REMOTE_ADDR` default and only single-address proxy headers allowed. Render's `render.yaml` selects `HTTP_CF_CONNECTING_IP`; the native VPS environment template selects Nginx-sanitized `HTTP_X_REAL_IP`, while the Nginx/Gunicorn trust boundary remains explicit. `arabic-reshaper==3.0.1` is already declared in `requirements.txt` and imports in the project `.venv`. Local `manage.py check` and six non-database auth IP-source tests pass. PostgreSQL-backed auth tests are blocked because no local PostgreSQL service/tools or running Docker engine are available; local DB testing was stopped per user direction. Render's read-only SQL connector could not access the staging database because its source IP is not allowlisted and TLS is required; no allowlist change was made, and the active staging application DB was not used for tests. Read-only Render service inspection confirms `birky-staging-api` watches `main` with commit auto-deploy and currently serves the prior published `main` revision; no deploy, environment mutation, commit, or push occurred. Staging CSRF/recovery/browser smoke tests remain unverified. Do not push until focused PostgreSQL auth tests pass and the exact staging dependency closure is safely isolated from the extensive unrelated dirty `main` worktree.

### Native VPS production wiring (local, unpublished)

`PRE-PUSH-NATIVE-VPS-PRODUCTION-WIRING-08` selects a provider-neutral native Linux VPS runtime (initially DigitalOcean Droplet) and adds Nginx, systemd/Gunicorn, non-secret environment template, and a short runbook. Render staging and application/business code are unchanged. This is repository configuration only; no production provisioning, migration, commit, push, or deployment is claimed.

### Current authentication state (local, unpublished)

AUTH-RESET-MODEL-CORRECTION-01 is the current policy: legacy passwords and newer six-digit PINs remain compatible in the shared credential field; Login ID and approved legacy aliases are supported; Shop Admin can reset only active same-Shop STAFF; Shop Admin recovery is registered-phone request → Back Office approval; VIEWER cannot sign in and existing records/hashes remain preserved; email self-service reset is removed. Main Supplier/Back Office authority remains unchanged. The dated task entries below preserve what was implemented at their checkpoints and must not be read as the current recovery policy.

- **Historical task record — FRONTEND-MAIN-RECONCILIATION-01 (2026-10-09; email reset later superseded):** This task added an email password-reset screen/service at that checkpoint, removed the redundant successful-login CSRF bootstrap, and split Users capacity stats from membership search/filter/page requests. AUTH-RESET-MODEL-CORRECTION-01 later removed email self-service reset; that feature is not current. The remaining recorded UI/request-efficiency work and validation evidence are retained as history. No commit, push, deployment, or shared data write occurred in this task.

- **AUTH-LOGIN-PIN-RESET-IMPLEMENTATION-01 (2026-10-08; local, unpublished; DB validation pending):** Added nullable globally unique Login ID, six-digit PIN generation/change, database-backed login/reset attempt limits, Shop ADMIN phone reset-request and Main Supplier approval/rejection, Team reset action, first ADMIN/Shop user Login ID forms, dedicated reset page, and generated OpenAPI updates. Existing Login page markup/styles are unchanged except Forgot password navigation. Django check and migration drift pass; 2 pure PIN tests pass; frontend 154/154 tests, typecheck, and build pass. PostgreSQL-backed tests and migration replay are not verified because local DB/Docker are unavailable, and shared staging DB must not be used as a test database. No commit, push, deploy, or staging migration.

- **EXISTING-AUTH-REQUEST-FLOWS-01 (2026-10-08; complete locally, unpublished):** Added frontend password-reset request/confirmation against existing anonymous backend endpoints; removed duplicate post-login CSRF bootstrap while preserving the required login CSRF contract; debounced Users/Clients search with stale-response protection; separated Users stats from search/filter/page changes; and deferred Design-list requests until the picker is opened. Frontend work is isolated in `sgtp-frontend` on `frontend/parallel-foundation`; this main checkout contains only task/state documentation updates, no application/backend/API/schema edits. Frontend suite 135/135 across 29 files, typecheck/build passed, lint exits 0 with `set-state-in-effect` warnings, `git diff --check` passed. No authenticated browser/email-delivery verification, merge, commit, push, or deployment.

- **CURRENT-STATE-MIGRATION-INTEGRITY-01 (2026-10-08; complete, local/unpublished):** inspected Catalog migrations `0017–0019` against current models and Shop-isolation rules. Fixed a rollback-safety defect in `0018`: duplicate selections in one option group could previously be collapsed by a dictionary and mistaken for an unchanged seed. Reverse now compares the complete sorted selection rows and refuses to remove an altered seed; added a regression test. Fresh UTF-8 PostgreSQL migration replay passed; all 471 backend tests, frontend 142/142 on final rerun, frontend typecheck/build, Django check, and migration drift check passed. No new schema migration, commit, push, staging/production migration, or cloud write.

- **OPT-02 local remediation (2026-10-07; complete, unpublished):** isolated the cached production-settings test in a fresh process without weakening production R2/security guards. Made the unpublished catalog `0018` seed migration's reverse identify its own Designs by deterministic UUID and reject altered seeds; duplicate-name preservation and edited-seed refusal have regression tests. Full backend suite passed 470/470 on disposable local PostgreSQL; frontend 142/142, typecheck/build pass, lint exits 0 with existing warnings. Live Render staging service was read-only verified as `main` + auto-deploy `commit`; a push can deploy and run migrations. No push, staging change or production setup. See `docs/OPT_02_RESULT.md` for scope and evidence.

- **OPT-01 baseline (2026-10-07; local, audit-only):** current `main` HEAD matches `origin/main`, but the new application work remains dirty/unpublished and is not represented by that SHA. The frontend suite is green (142/142, typecheck/build); the backend suite is **not** green (467/468) because a production-settings test re-imports `prod` after changing R2 environment variables but retains cached `base` settings. No app code, commit, push or deployment was made by OPT-01. Current evidence, blockers and separately confirmed follow-up tasks are in `docs/OPT_01_BASELINE.md`; the user-supplied engineering standard is indexed in `docs/PRODUCTION_ENGINEERING_STANDARD.md`. DigitalOcean is a proposed final production task, not a provisioned or approved live environment.

- **Current local task: `FRONTEND-GARMENT-SYSTEM-INTEGRATION-01` (2026-10-07; implementation complete, unpublished).** Integrated the existing garment-system backend capabilities into the established Catalog, Designs, and Measurements frontend flows: Shop-owned garment families and option groups, family-to-group selection/required rules, family-level Designs without a Variant, inline custom measurement definitions, and optional Design-version linkage on saved measurement sets. Existing variant workflows remain supported; no new parallel UI or mock data was introduced. Frontend suite passed 142/142 across 30 files; typecheck, production build, project-state validator, and `git diff --check` passed. Lint exited 0 with React `set-state-in-effect` warnings, including several in ClientMeasurementsPage. No commit, push, deployment, or authenticated browser verification.
- **Current local task: `MEASUREMENT-HISTORY-DESIGN-DEFAULTS-01` (2026-10-07; implementation complete, unpublished).** Measurement history now supports concurrency-safe soft deactivation of a version while protecting the last active version and retaining immutable values, snapshots, audit/copy provenance, and version high-water numbering. Design creation is transactional and idempotent across the draft and style selections, including correct empty-catalog versus catalog-failure behavior. Additive migrations introduce the deactivation/idempotency schema and style-only presets for all remaining existing seeded families; no numeric measurements or ease are seeded. Primary-source research and gaps are recorded in `docs/MEASUREMENT_DESIGN_RESEARCH.md`. Validation passed with the 456-test backend suite on a clean UTF-8 PostgreSQL test database, focused backend measurement/catalog coverage 70/70, catalog concurrency 6/6, frontend 133/133 across 29 files, typecheck/build, repository validator, its 31-test suite, Django/system/deploy checks, migration drift, OpenAPI (0 errors; 29 warnings/13 unique), Black, Flake8, schema parity, and diff checks. No commit, push, deploy, staging database write, or customer/demo measurement creation occurred.
- **Current local task: `CLIENT-WORKSPACE-HISTORY-01` (2026-10-06; implementation complete, unpublished).** Implemented on local `main` only. Client detail is now a compact Client workspace with independent Client/Related Person loading states, responsive summary and related-person panel, and measurement profile/version history for authorized Shop users. The Related Persons panel now follows the same card/header structure as Measurements, with aligned count, add action, loading/error, empty, and populated states. The Measurements action now lazy-opens the existing full measurement-entry workflow in-place on the client detail route, passing the already-loaded client, shop, and Related Persons context to avoid duplicate client-context requests; direct measurement routes remain supported. Measurement workflow steps now use the Clients workspace visual language: individually bordered cards, consistent surface/padding/shadows, and visible step badges (desktop and mobile), preserving the established content and sequence. Steps 01 (Client) and 02 (Garment) share one outer bordered panel and sit side-by-side above 900px with a central divider; smaller screens stack them inside that same border with a horizontal divider. History pages are loaded only when expanded and use the existing paginated sets/detail/copy/compare/PDF APIs. Saved versions remain read-only; copy calls the canonical immutable copy endpoint and refreshes from its response/history. The root viewport scrollbar is visually hidden while native scrolling remains available to reach older versions. No backend/API or schema change occurred. Frontend full suite: 124 passed across 29 files; typecheck and production build PASS; lint exits 0 with effect warnings; authenticated browser verification was not performed because the local browser remains at login. Local `main` is not committed/pushed; no deployment occurred. The separate frontend worktree was not modified.
- The Related Person Add action is restricted to the Client overview; the in-place Measurement view keeps existing people available for wearer selection but hides person creation controls.
- The Measurement profile step is now nested inside the preceding Style card with an internal divider. In Measurement view the Related Persons side panel is hidden and the measurement workspace expands to the full available width; the Client overview retains the panel and its management actions. Frontend suite remains 124/124; typecheck/build and `git diff --check` pass. No backend/API changes.
- Body Measurement entry now gives new fields an `INCH` default while retaining independent per-field unit controls. Changing the main unit applies it to every field; afterward each field can still be changed independently. Values are never converted, and the explicit-unit backend contract is unchanged. Frontend suite is 125/125; typecheck/build pass and lint exits 0 with existing effect warnings. Inventory API regression tests pass 16/16. Requested demo Fabric records remain pending because the frontend proxy targets the staging backend and there is no authenticated local backend/Shop context; no data record was created.
- **Current task: `STAGING-STYLE-IMAGE-MIGRATION-FIX-01` (2026-10-06; published and staging-verified).** Corrective implementation is on both `main` and `staging`; exact-SHA Project State Validation passed with the full application suite (448 passed). Render staging deploy `dep-db2c8jm7bikc73dr7800` is live; logs confirm `catalog.0015_styleoptionimage_primary` and `catalog.0016_styleoptionimage_one_primary` applied successfully, and live/ready health endpoints return HTTP 200. The additive migration split leaves deterministic backfill in 0015 and the conditional unique constraint in 0016; its regression test covers existing image rows. Local validator, focused migration regression (1 passed), Django check, migration drift, OpenAPI validation, Black, Flake8, and diff checks passed. Production was not deployed or migrated.
- **Previous local frontend performance audit (2026-10-05; historical checkpoint).** In the separate `frontend/parallel-foundation` worktree, changes reduced redundant Main Supplier Catalog, Shop-context, Measurement-design, Inventory-search, and Back Office Shop-search requests without changing backend contracts or business rules. Repeated warm health checks measured about 0.31–0.75 seconds through the local proxy. Authenticated Back Office/Shop browser timing was not verified. Billing/pricing UI remains outside the implemented local frontend scope.
- **Current integration checkpoint (2026-10-05; publication in progress).** Local `main` contains the Measurement-R2/Style Option backend APIs and migrations `catalog.0013`/`0014`, plus the integrated frontend baseline. R2 variables have been merged into the existing Render staging API and its environment-only deployment is live on the previously published SHA; the R2-aware code and its fail-fast staging guard are in local unpublished commits. Local tests recorded before this final publication pass: backend suite 446 passed, focused staging tests 20 passed, frontend suite 117 passed with typecheck/build; details in `docs/HANDOFF.md`. Do not claim image upload/display verification until performed through the authenticated app.
- **Previous local backend task: `CATALOG-STYLE-OPTION-EDIT-API-01`.** Shop-owned Style Option translation editing is implemented through the existing Shop-context PATCH route. Partial locale updates preserve omitted translations; code/group/Shop ownership remain immutable, and existing `is_active` updates are supported. Shop isolation and existing ADMIN/STAFF/Main Supplier Shop-context authorization are preserved. Focused Catalog API tests: 32 passed; full PostgreSQL-backed suite: 445 passed; repository validator PASS (445 discovered); validator tests: 37 passed; Django check PASS; OpenAPI: 0 errors/29 warnings (13 unique); no migration generated; changed-file Black/Flake8 PASS. At that task's validation checkpoint the frontend editor had not yet started.
- **Previous authorized task: `MEASUREMENT-R2-UI-01`.** Local implementation and validation completed; at that point full PostgreSQL-backed suite: 442 passed; focused Catalog/Measurement suite: 54 passed; validator: PASS (442 discovered); validator tests: 37 passed; Django check and migration drift: PASS; production deploy check: 0 errors (13 existing warnings); OpenAPI: 0 errors, 29 warnings (13 unique); changed-file Black/Flake8 and backend/frontend diff checks: PASS. Frontend: 89 tests passed, typecheck/build passed; lint exits 0 with React effect warnings and an existing large-chunk advisory. Three compressed samples are standalone private objects under `birky-desgin-test/`; they are not attached to a Shop/StyleOption and no business records were created. No commit, push, or deployment occurred.
- **Previous authorized task: `MEASUREMENT-E2E-01`.** Frontend/backend remediation is implemented, merged into `main`, published to the canonical remote branch, and its GitHub Actions Project State Validation passed. Render staging deployment and authenticated manual-browser verification remain pending because Render account access is unavailable in this workspace. The full test and check record is in the handoff history.

- **Previous authorized task: `T4-02-API-ENDPOINTS-01`.** Added Main Supplier-only global Family/Option Group creation, paginated Main Supplier-only global variant listing, and visibility-safe Global Design Template detail retrieval. No model or migration change. Catalog API tests: 22 passed; one existing Arabic-data test was excluded because the local PostgreSQL cluster uses WIN1252. Django checks passed with environment/schema warnings; OpenAPI had zero errors. Repository validator passed. Published to GitHub `main` on 2026-10-03 at implementation commit `3d17271dae879f5f26ceba5b46c413bf2d501310`; remote SHA was verified. No deployment occurred.

- **Previous authorized task: Catalog and Designs frontend integration.** Its implementation was committed on `frontend/parallel-foundation`, merged locally into `main`, and published with T4-02 API commit `3d17271dae879f5f26ceba5b46c413bf2d501310`. Frontend checks and the repository state validator passed. It connects existing Catalog and Designs pages to T4-02 APIs, replaces mock fallbacks with visible errors, and fills supported create/select/publish/archive/image-upload flows. No deployment occurred, and authenticated staging browser E2E was not performed. Remaining frontend UI gaps are recorded in `docs/HANDOFF.md`.

- **Historical task: STAGING-MAIN-ADMIN-BOOTSTRAP-01 is complete, pushed, and live on Render staging.** The implementation passed exact-SHA Project State Validation. One Main Supplier Admin was created through the guarded one-time command, with first-login password change required. The bootstrap switch is off, all four temporary inputs are blank, and the cleanup deploy is live with readiness HTTP 200. No Shop or migration was added.

- **Previously authorized maintenance: DJANGO-ADMIN-UX-01 is implemented, published to `main`, and CI-verified.** Native Django Admin now groups the existing account, Shop, client, catalog, measurement, and material models, with an explicit Main Supplier-only permission boundary. Catalog/business records are inspection-only unless an existing safe Shop service already supports an operation. Focused tests: 18 passed; full PostgreSQL-backed suite: 388 passed; validator tests: 30 passed; migration drift: no changes. No schema, migration, dependency, frontend, or deployment changes.

- **Historical task: BACKOFFICE-01 backend implementation is published to `main` and live on Render staging.** Readiness and CSRF bootstrap endpoints returned 200 after deploy. Its frontend implementation reused the existing shell and live Shop APIs; the Work page mock content was not reused. At that task's completion its feature branch had not yet been published. Backend adds a derived read-only `is_main_supplier_admin` profile field and no migration. Exact deployment evidence is in the historical changelog and handoff entries.
- Phase 1 and Phase 2 are complete.
- Phase 3 is COMPLETE; it was activated with `CONFIRM PHASE 3` and the approved T3-05A staging foundation is complete (custom-domain DNS/TLS remains explicitly deferred).
- Phase 4 is ACTIVE; Core Tailor Business activation was explicitly confirmed with `CONFIRM PHASE 4`. T4-01, T4-02, and T4-03 are COMPLETE, committed, published, and CI-verified. T4-03A — Inventory & Stock Foundation is COMPLETE, COMMITTED, PUBLISHED, and exact-SHA CI-VERIFIED. T4-04, T4-05, and T4-06 are confirmed and complete locally, unpublished; Phase 5 remains separately gated.
- T4-03A is an additive extension to completed T4-03. Focused T4-03A/T4-03 tests: 41 passed; full PostgreSQL-backed suite: 409 passed; validator: PASS with 409 tests discovered; validator tests: 32 passed; Django check: PASS; production deploy check: 0 errors with 12 warnings; migration drift: clean; OpenAPI: 0 errors, 28 warnings (12 unique); Black/Flake8/schema parity/diff check: PASS. GitHub Actions Project State Validation succeeded for the T4-03A implementation commit. Migrations were applied only to the disposable PostgreSQL test database. No deployment or shared/staging/production migration occurred.
- Historical T4-02 baseline `1287d61a1406bbdd3edddc778b91f59c9cca52df` passed Project State Validation run `36970391503`.
- T4-03 implementation checkpoint `d9ca27bbab8587c2da5ceb8c1f61f913087fdc48` passed Project State Validation run `37006408609`.
- API-DOC-REFRESH-01 and API-BROWSABLE-PORTAL-01 are completed historical maintenance tasks; neither changed Phase 4 authorization.
- Completed Phase 3 tasks include T3-01, T3-02, T3-02-REMEDIATION, T3-02A, T3-03, T3-04, T3-04A, T3-04B-REMEDIATION-01, T3-04B-USER-SCOPE, and T3-04C. T3-04C implementation commit `dfbf6eecdbcd36c014a45a5d297c26e4e27a4113` is published; exact-SHA Project State Validation run `36605653294` succeeded.
- T3-04B-USER-SCOPE is COMPLETE, COMMITTED, and PUBLISHED on `main` at `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c`; GitHub Actions Project State Validation run `36591864481` completed successfully for that exact SHA.
- T3-04 is COMPLETE, COMMITTED, and PUSHED on `main`. Live verification on 2026-09-29: local `HEAD`, `origin/main`, and remote `refs/heads/main` matched; derive the current SHA from Git.
- T3-04A is published at `304e6ec4a6811b0153db4dea1417d24affa11bec`; its GitHub CI passed.
- Initial T3-04B publication `5e3b1714289e7b5660e1a54d6cb2752b64d54683` failed GitHub Actions Run #36545855022 and was reverted. T3-04B-REMEDIATION-01 was published as the corrective checkpoint; T3-04B-USER-SCOPE is now published with its exact-SHA CI gate green.
- Historical Phase 3 publication record: T3-04B-REMEDIATION-01, T3-04B-USER-SCOPE, T3-04C, and T3-05 were implemented, validated, and published. T3-04C exact-SHA CI passed in run `36605653294`; T3-05 implementation commit `3d21a0943006cd866bc19bc728cbec05daae1630` passed Project State Validation run `36614638187`. T3-05A repository implementation and local validation were published; implementation checkpoint CI run `36652187336` succeeded.
- Current staging state: T3-05A is COMPLETE, published, and exact-SHA CI-green. Live provider-hostname checks verified login/cookie behavior, refresh rotation/reuse rejection/logout clearing, membership/User-ID/stats/Work-Function/direct-object isolation in both Shop directions, and Main Supplier access to approved Shop surfaces. The synthetic fixture remains; temporary credential variables are blank and bootstrap/rotation flags are false. Final cleanup deploy `dep-dau9ptlg1s2s73c2foig` is live on the published implementation checkpoint and both health endpoints return 200. Reserved custom-domain DNS/TLS and real frontend browser integration remain deferred.
- Historical T3-05A implementation checkpoint (not current HEAD): commit `9af6424116ebba12896d90d032c36bd25328a4d0`.
- The Parallel Frontend Foundation Track is an approved pre-Phase-7 preparation lane, separate from Phase 7/F7-01 completion and its formal dependencies. Its frontend source belongs in an isolated frontend branch/worktree; `main` remains the canonical backend/integration branch and owner of cross-project documentation. Unimplemented APIs/business workflows must remain behind mock adapters.
- The PHASE4-PARALLEL-UNBLOCK-01 roadmap correction makes backend Phase 4/5/6 delivery non-blocking with respect to frontend completion. Existing backend feature integration may continue independently on `frontend/parallel-foundation`; each new frontend domain slice remains contract-first and follows acceptance of its backend API. The UI Reference Gate and Dashboard Last Rule remain in force. Phase 4 activation and each task retain separate confirmation gates.

- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Phase 1 corrective implementation was completed and published to `origin/main`.
- Current branch: `main`
- Target status: SGTP V1 is explicitly defined in `docs/PRODUCT_DEFINITION.md`
- Starter foundation: exists in the cloned SGTP repository.
- Phase 1 implementation: **Historical - Complete.**
- Historical confirmation snapshot (updated 2026-10-21): Phase 4 and T4-01/T4-02/T4-03/T4-03A/T4-04/T4-05 were authorized earlier. T4-06 is now confirmed and complete locally as recorded above; Phase 5 and other frontend business modules remain separately gated.
- **Historical STARTUP-PRIVATE-IMAGE-01 follow-up (2026-10-05):** R2 reliability and existing image recovery were pending at that checkpoint. This dated handoff is not the current task status.
- Detailed phase playbooks: 01-10 present.
- Later-phase decisions: Tenant context is approved as URL-path based (`/shops/{shop_id}/...`), and Related Person billing is owned by the Primary Client.
- T3-05A (Staging Backend Foundation) is complete. Active backend: `https://birky-staging-api.onrender.com`; reserved future API hostname: `https://api-staging.birky.com` (not owned/controlled, configured, DNS-verified, or TLS-verified). On 2026-09-30, live checks with synthetic Main Supplier and Shop A/B accounts verified login without refresh-token JSON exposure; Secure/HttpOnly/SameSite=Lax refresh cookie; CSRF-required refresh/logout; rotation, old-token reuse rejection, cookie clearing, and post-logout refresh rejection. Membership list/detail, exact User-ID, stats, Work Function, and direct-object isolation were verified for Shop A→B and B→A; Main Supplier access to approved surfaces in both Shops was verified. Temporary credentials are blank and bootstrap/rotation flags are false. Final cleanup deploy is live and both health endpoints return 200. No real customer data was used. F7-01A remains planned only; frontend browser integration and custom-domain DNS/TLS are deferred. T3-02A implemented the account/preference data and API foundation; frontend localization, RTL/LTR layout, and full Light/Dark/System UI remain Phase 7 work.
- At T3-02A completion, email was required and optional unique E.164 phone could authenticate the same UUID account. T3-04A subsequently made normal-user email and phone optional while retaining Main Supplier-controlled global account creation, no-store initial credentials, email reset, session revocation, locale/appearance preferences, and Shop defaults.
- T3-04A implements the published permanent User ID, optional normal-user email/phone, required first name, admin-grade contact safeguards, alias login, controlled reset, and User hard-delete denial. Published T3-04B remediation enforces membership/Admin lifecycle and cardinality invariants. Published T3-04B-USER-SCOPE adds one immutable owning Shop per ordinary account, same-Shop membership enforcement, scoped creation/reset, and a guarded migration. Published T3-04C adds normalized membership-scoped Work Functions and Shop-ADMIN-only set management without permission escalation. T3-05 Shop visibility/lifecycle/API/Admin hardening is published at `3d21a0943006cd866bc19bc728cbec05daae1630`; exact-SHA Project State Validation run `36614638187` succeeded.
- T3-02A and T3-03 historical CI records remain below. The published T3-04 baseline and the later T3-REBASELINE-01 documentation checkpoint passed GitHub Actions Project State Validation (runs #36511111586 and #36524789793 respectively).

## Current Verification Results

- **AUTH-LOGIN-PIN-RESET-IMPLEMENTATION-01:** 476 backend tests discovered; PostgreSQL-backed suite not run. Two pure PIN tests passed. Django check and migration drift passed; frontend 154/154, typecheck and build passed. OpenAPI generated with zero errors and 29 existing warnings. No staging/production database was used.

- **Historical CURRENT-STATE-MIGRATION-INTEGRITY-01 checkpoint:** full backend suite passed 471/471 on a fresh disposable UTF-8 PostgreSQL test DB at that earlier checkpoint. Catalog migrations `0017–0019` were present in `django_migrations`; five expected partial unique indexes were present in `pg_indexes`. Focused seed rollback safety 3/3, Django system check, and `makemigrations --check --dry-run` passed then. Frontend full suite passed 142/142 on rerun; typecheck and production build passed. No staging/production database was used.

- **MEASUREMENT-E2E-01 local validation:** Backend full PostgreSQL suite 433 passed; focused Measurement API/concurrency/default-template and Shop-context tests 40 passed. Frontend tests 84 passed, typecheck and production build passed, lint exited 0 with React state-in-effect warnings. Django system check passed; production deploy check had 13 drf-spectacular warnings; OpenAPI generated/validated with 0 errors and 29 warnings (13 unique). No model changes detected. Migration-history consistency check could not connect because configured base database `testdb` does not exist. The frontend integration is merged and published to `main`; local and `origin/main` both resolve to `a619ca6cd395cf47f85bc09b75ee34dc977dfb6c`, and GitHub Actions Project State Validation run `37114613711` passed for that SHA. Backend/frontend diff checks pass and schema copies match. No authenticated browser test, Render deployment, or shared/staging/production migration occurred because Render account access is unavailable in this workspace.


- **Previous GARMENT-VARIANTS-01 backend and frontend checkpoint:** Full PostgreSQL-backed backend suite: 430 passed; focused Catalog/Measurement/Variant API and concurrency suite: 56 passed; validator tests: 30 passed; repository state validator PASS (430 discovered). Django system and production deploy checks PASS (12 existing OpenAPI warnings); migration drift clean; OpenAPI 0 errors/28 warnings (12 unique); Black/Flake8/schema generation/diff check PASS. Frontend typecheck PASS; seventy frontend test cases across 13 files PASS; lint exits 0 with six existing warnings in unchanged shared files; build PASS with an existing bundle-size advisory; diff check PASS. Backend branch `main` and frontend branch `frontend/parallel-foundation` remain local/uncommitted with Family changes preserved. Only disposable UTF-8 PostgreSQL test databases were migrated. No push, merge, deployment, or shared/staging/production migration. Authenticated manual browser check remains pending user login.

- **GARMENT-FAMILIES-01 frontend checkpoint:** Shop Family browse/search/pagination/detail and filtered Variant/Design navigation; Main Supplier create/edit/archive/reactivate, private image management, and ordered Option Group mapping. Typecheck PASS; frontend tests 59 passed; build PASS; diff check PASS; lint exits 0 with six existing warnings in unchanged files. Authenticated visual responsive verification is pending user login. Frontend changes are local/uncommitted on `frontend/parallel-foundation`.

- **DJANGO-ADMIN-UX-01 validation:** focused Admin/security suite 18 passed; full PostgreSQL-backed application suite 388 passed; repository validator PASS (388 tests discovered); validator tests 30 passed. Django system check PASS; production deployment check PASS with 12 existing nonfatal OpenAPI warnings; migration drift: no changes; OpenAPI: zero errors with existing warnings; Black, Flake8, and `git diff --check` PASS. Implementation commit `608362d6509b286ba0daa9ede4e33d39d2888a6c` passed exact-SHA Project State Validation run `37017703294`. No schema/migration/frontend/deployment changes.

- **T4-03 complete and published:** focused measurement/material API and PostgreSQL concurrency tests: 20 passed; full PostgreSQL-backed application suite: 370 passed using project test settings with a UTF-8 disposable database. Repository validator: PASS (370 application tests discovered); validator suite: 30 passed. Django system check: PASS; `DJANGO_ENV=prod check --deploy`: no errors (12 nonfatal drf-spectacular warnings); migration drift: no changes. OpenAPI: zero errors, 28 warnings (12 unique, including type-hint/enum warnings and automatically disambiguated measurement operation IDs). Black, Flake8, schema artifact parity, and `git diff --check` passed. Implementation commit `d9ca27bbab8587c2da5ceb8c1f61f913087fdc48` passed exact-SHA Project State Validation run `37006408609`. No deployment occurred.

- **API-DOC-REFRESH-01:** Internal `/api/docs/` and `/api/schema/` access is restricted to authenticated Main Supplier users via Django Admin session; anonymous access redirects to Admin login and other authenticated users receive a non-disclosing 404. Root redirects to docs; session auth is excluded from business APIs; Swagger authorization persistence is disabled. The stale public test page and unused `/api-auth/` route were removed. Live anonymous checks: root/docs/schema redirects verified; both health probes returned 200. Focused PostgreSQL-backed tests: 62 passed; full suite: 315 passed. Repository validator PASS (315 tests discovered); validator tests 27 passed; Django system and production deployment checks PASS; migration drift: no changes; OpenAPI: zero errors, 23 warnings (7 unique); Black, Flake8 and `git diff --check` PASS. Published at checkpoint `9e93a77754ac03839d038e5e3a32458208bc02e9`; exact-SHA CI run `36850074419` succeeded. No deployment occurred.
- **API-BROWSABLE-PORTAL-01:** Added Main Supplier-only `/api/browse/` endpoint explorer from protected OpenAPI schema; root points to this page and Swagger remains at `/api/docs/`. Requests stay same-origin under `/api/v1/`; required API calls use Bearer JWT in page memory only, while Django Admin session alone still returns 401 from business APIs. CSRF bootstrap is used on unsafe requests; refresh/logout continue using their existing protected cookie lifecycle. Browser smoke showed 50 operations, static assets returned 200, and no console errors. Focused docs/browser tests: 10 passed; full PostgreSQL-backed suite: 319 passed. Repository validator PASS (319 application tests discovered); validator tests: 27 passed; Django system and production deployment checks PASS; migration drift: no changes; collectstatic dry-run PASS (166 assets discovered); OpenAPI: zero errors, 23 warnings (7 unique); Black, Flake8, JavaScript syntax check and `git diff --check` PASS. Published at implementation commit `304c9666f680e3e32aa05e4545b44aa049963e19`; exact-SHA GitHub Actions Project State Validation run `36862739900` succeeded. No model/API behavior, migration, dependency, React frontend, or deployment changes.

- T4-01 validation: focused Clients/Related Persons API and PostgreSQL concurrency tests: 15 passed; full PostgreSQL 15-backed application suite: 309 passed. Repository validator: PASS (309 application tests discovered); validator tests: 27 passed. GitHub Actions Project State Validation run `36796609814` succeeded for exact commit `e4e5e4126d60bfb563fbd25fbf0baab9e85963f9`.
- Django system check and production `check --deploy`: PASS; `makemigrations --check --dry-run`: no changes detected. OpenAPI validation: zero errors, 23 warnings (7 unique, existing serializer type-hint/role-enum warnings). Black and Flake8 checks for the changed/new Python files and `git diff --check` passed.
- The full-suite run used local PostgreSQL 15; GitHub Actions separately completed successfully for the exact published T4-01 SHA. No deployment occurred.
- T3-05A live staging security/isolation verification passed using only the existing synthetic fixture. Staging-focused tests: 28 passed; authentication/CSRF lifecycle regressions: 7 passed. Docker image build and disposable local Docker/PostgreSQL smoke passed: migrations and static collection completed; liveness/readiness/CSRF bootstrap returned HTTP 200.
- Historical staging bootstrap evidence and deploy IDs below remain checkpoint records. Final T3-05A evidence: implementation commit `b29a897897d35ec9163c510456bd9197b8a4f6e1`; Project State Validation run `36667104952` succeeded for that exact SHA with 294 application tests. Render was verified as Free/Frankfurt Docker service plus Free/Frankfurt PostgreSQL 15, auto-deploy off and DB IP allow-list unchanged. Final application deploy `dep-dau9ptlg1s2s73c2foig` runs that SHA; logs confirmed migrations, collectstatic, and Gunicorn startup, with no secret exposure found. Credential variables were blanked and both bootstrap/rotation flags false; both health routes return 200. Complete authenticated endpoint isolation and token lifecycle checks passed. Custom DNS/TLS and frontend browser integration remain deferred.

## Verification history

- **T3-05 — published (task-time record):** commit `3d21a0943006cd866bc19bc728cbec05daae1630`; GitHub Actions Project State Validation run `36614638187` completed SUCCESS for that exact SHA. Local focused tests: 30 passed. Full PostgreSQL-backed application suite: 231 passed (186 warnings). Repository validator PASS (231 discovered); validator tests 14 passed; Django system/deployment checks, migration drift, OpenAPI (zero errors), Black, Flake8, and `git diff --check` passed. No migration/dependency changes. At that T3-05 checkpoint, T3-05A, Phase 4, frontend, and deployment were unstarted.

- T3-04B remediation focused suite: 77 passed, including exact immutable-identity/error-envelope assertions and Shop/Admin lifecycle cases.
- PostgreSQL-backed full application suite: 183 passed (113 warnings), including separate-connection tests for concurrent promotions, demotion versus global deactivation, and first-ADMIN creation versus User deactivation.
- Regression suite for T3-04A identity/authentication, T3-03 Shop context, membership and migration behavior: 39 passed.
- Repository validator: PASS (183 tests discovered); validator tests: 14 passed. Django system check and `DJANGO_ENV=prod` deployment check: PASS. OpenAPI schema validation: PASS. Black and Flake8 for changed Python files: PASS; `git diff --check`: PASS.
- `makemigrations --check --dry-run`: PASS against the available local PostgreSQL `devdb`; no model changes or migration-history warnings.
- The initial T3-04B commit remains historical failed evidence and was reverted before this correction. Confirm the Project State Validation result for the exact T3-04B publication SHA before proceeding.

### Latest T3-02A Verification

- Full application suite: 130 collected, 130 passed (`pytest -q -p no:cacheprovider --no-cov`).
- Repository validator: PASS; validator tests: 11 passed. Validator confirms 130 discovered application tests and reports only the expected dirty-worktree warning.
- Django system check: PASS. Production deployment check (`DJANGO_ENV=prod`): PASS with no issues. The default local development `check --deploy` emits six expected development-environment security warnings; the production settings check is clean.
- Migration status: both new migrations applied locally; `makemigrations --check --dry-run`: no changes detected.
- API schema validation: PASS. Black check for new/rewritten account implementation: PASS; Black and Flake8 checks for `scripts/`: PASS; Flake8 for account implementation: PASS.
- `git diff --check`: PASS. GitHub Actions Project State Validation Run #17 reported SUCCESS for the pushed commit.

### Latest T3-03 Verification

- T3-03 uses DRF request-local context at `/api/v1/shops/{shop_id}/context/`; authentication and the password-change gate precede Shop resolution.
- Shop context requires an active, non-deleted Shop and either an active, non-deleted membership or explicit Main Supplier authority. ADMIN, STAFF, and VIEWER memberships may enter context; selected-Shop role is attached to the request.
- Foreign, unauthorized, inactive, deleted, unavailable, and nonexistent Shop requests return the same non-disclosing 404 (`shop_context_unavailable`). Unauthenticated, invalid, and revoked credentials preserve 401 behavior.
- T3-04 reusable queryset/object isolation primitives are complete; actual business-resource endpoints must adopt and verify them. This T3-03 verification entry is historical: ordinary Shop visibility and Shop deletion were unresolved at that task's completion, then resolved as target rules by the 2026-09-29 rebaseline. Shop Admin settings authority remains not granted; currency changes after financial history remain deferred for a financial-policy decision.
- Focused context/membership/permission suite: 76 passed; the dedicated Shop-context module contains 15 tests.
- Full application suite: 145 passed (144 warnings). Django check, migration drift check, OpenAPI schema validation, validator unit tests (14 passed), Black, Flake8, and `git diff --check` passed.
- Repository validator: PASS; Phase 3 is recorded as active with explicit activation in both current-state documents. It discovered 145 application tests.
- No database schema or dependency changes. T3-03 is committed and pushed; GitHub Actions Project State Validation Run #19 passed.

### T3-04 Verification Record (initial local completion; later published)

- Added trusted-context queryset scoping and server-controlled Shop ownership in `TenantScopedMixin`; bound `IsTenantMember` object authorization to the selected Shop, including Main Supplier requests.
- Updated the temporary proof model to use a UUID Shop foreign key and soft-delete base; added tests for selected-Shop lists/counts, foreign direct IDs, Main Supplier one-Shop scope, create ownership, update/reparenting, absent/mismatched context, and deleted rows.
- Focused scope/context tests: 28 passed. Full application suite: 152 passed (144 warnings). Repository validator: PASS (152 discovered; dirty-tree warning expected); validator tests: 14 passed. Django system check: PASS; migration drift check: no changes; OpenAPI schema validation: PASS; Black check: PASS; Flake8: PASS; `git diff --check`: PASS.
- No business models/APIs, migrations, or dependencies were added. `BaseModelWithTenant.tenant` remains nullable because no concrete business subclass exists. No production schema, dependency, API-route, or business-module changes were made.
- The local validation figures above are task-completion evidence. T3-04 was subsequently committed/pushed on `main`; the verified published commit and CI status are recorded in the current Status section. T3-REBASELINE-01 was later published as a documentation-only checkpoint and passed GitHub Actions Project State Validation.

## Locked V1 business tenancy model

- Exactly one top-level Supplier / Main Admin exists in V1; there is no multi-supplier SaaS model. Enforced via `Supplier` singleton model.
- The hierarchy is one Main Supplier / Main Admin → Supplier Back Office → multiple Shops.
- Shop is the actual business workspace and tenant/isolation boundary.
- External Supplier records belong to exactly one Shop and are non-user, non-tenant business records with no login or system permissions.
- External Supplier data is never global/shared and is isolated by Shop.
- **Tenant mapping:** The legacy starter `Tenant` model has been retained and structurally mapped as the implementation of the `Shop` entity. T3-01 verified this structural safety and created the `Supplier` owning entity.

## Repository verification

- `git ls-remote` succeeded against the corrected URL.
- The existing cloned SGTP repository is now the project root.
- `AGENTS.md` and `docs/` were moved into the SGTP repository without overwriting starter files.
- Phase 1 corrective changes have been committed and pushed.

## Starter structure

- `core/`: Django settings, URL configuration, ASGI, and WSGI.
- `apps/accounts/`: custom email-based user, manager, JWT/login/logout endpoints, admin, migration, and tests.
- `apps/tenants/`: tenant model, admin, CRUD/action API, migration, and tests.
- `apps/common/`: abstract UUID/audit/soft-delete base models, including a tenant-aware base model.
- `templates/api_test.html`: simple endpoint reference page.
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `setup.cfg`: runtime and development dependencies/tooling.
- `Dockerfile`, `Dockerfile.dev`, `docker-compose.prod.yml`, `.devcontainer/`: container and PostgreSQL infrastructure.
- `.vscode/launch.json`, `Makefile`, `.env.example`, `.gitignore`, `README.md`, `LICENSE`: local development and project documentation.

## Existing technologies

- Python 3.13 container target; local inspection interpreter was Python 3.12.10.
- Django 5.1.4 and Django REST Framework 3.15.2.
- PostgreSQL 15 through psycopg 3.2.3.
- SimpleJWT, drf-spectacular, django-filter, django-cors-headers, django-safedelete, WhiteNoise, Gunicorn, Pillow, and python-dotenv.
- Docker Compose and VS Code Dev Container workflows.
- pytest configuration plus Django TestCase-based tests; Black, Flake8, isort, and coverage tooling.

## Existing reusable components

- Custom `User` model using email as `USERNAME_FIELD`.
- User manager with password hashing and superuser validation.
- JWT access/refresh login, refresh, logout, and user profile endpoints.
- `BaseModel` with UUID primary key, timestamps, audit-user fields, and cascade soft delete.
- `BaseModelWithTenant` with an optional tenant foreign key.
- Tenant CRUD/action API, admin, serializers, migrations, and initial tests.
- API schema/Swagger routes and DRF pagination/filter/search/order configuration.
- PostgreSQL/Docker/devcontainer setup and production Gunicorn entrypoint.

## Target alignment and contradictions

- The project target is now a complete Supplier-Centric Garment & Tailor Platform, not merely a generic Django/DRF starter.
- Tailor Management is the core V1 business module, with isolated shop workspaces under a supplier back office.
- The required end-to-end workflow is documented. T4-01 provides Clients/Related Persons, T4-02 provides Catalog/Designs, T4-03 provides Measurements/Materials, and T4-03A provides Shop inventory. Work/production stages, billing, and reports remain unimplemented.
- At this main-branch baseline, the target requires React/Vite/Tailwind but the repository has no tracked frontend application yet. Parallel frontend foundation work is isolated from `main`; the empty-directory/branch implementation state is verified separately by Git.
- The target requires a service layer, object-level permissions, persistent object storage, background jobs, audit logging, CI, monitoring, and automatic documentation; the starter does not implement these as complete capabilities.
- T3-03 request-local active-Shop context and T3-04 reusable queryset/object isolation primitives are implemented. T4-01 is the first business-resource API and adopts/tests them; later endpoints must do likewise.

## Phase 3+ Missing or incomplete business logic

- `BaseModelWithTenant.tenant` remains nullable, but T4-01 Client/RelatedPerson models use required Shop FKs and endpoint isolation tests. Other future Shop-owned models/endpoints must enforce and test their own scope.
- Tenant-context resolution is implemented at `/api/v1/shops/{shop_id}/...`; T4-01 adopts T3-04 shared query/object primitives. Remaining endpoint-specific isolation work is future work.
- Billing ownership for work belonging to a Related Person is approved as Primary Client ownership and must be enforced in Phase 5.
- Implemented Phase 4 business modules are Clients/Related Persons, Catalog/Designs, and the T4-03 Measurements/Materials foundation, alongside accounts, tenants, and membership. Work/production workflow and Phase 5 billing/reporting remain unimplemented.

### PRE-P3-02 result

- The V1 Supplier / Shop / External Supplier business meaning is now explicit across the governing documentation.
- Historical PRE-P3-02 task-time outcomes: T3-01, T3-02, T3-02-REMEDIATION, T3-02A, T3-03, and T3-04 were complete; T3-05 and subsequent tasks then remained individually gated.

### T3-02 remediation result

- User API access is restricted so ordinary authenticated users cannot enumerate, modify, or delete other users; self-profile updates remain available and account activation state is read-only through the serializer.
- Shop write actions and activation/deactivation use the existing `ShopRolePolicy` Main Supplier authority instead of Django `is_staff` alone.
- Generic membership updates cannot change `is_active`; lifecycle actions remain authoritative.
- Authentication throttling is explicitly wired to the `auth` scope and verified with a non-mocked repeated-login test.
- Duplicate CORS test method names were corrected so all intended tests are collected.
- CI retains project-state validation and is configured to run the application suite, Django system checks, and migration checks with PostgreSQL. The GitHub Actions run for the reviewed baseline successfully passed all checks, including the application suite, Django system checks, and PostgreSQL integration. Remote CI confirmation is fully green and the PostgreSQL connectivity issue is resolved.
- Production compose now propagates `DJANGO_CORS_ALLOWED_ORIGINS` without inventing a deployment origin.
- No migrations were required or changed.
- Remaining decisions include Shop Admin settings authority (not granted), currency changes after financial history, and later items listed in `docs/DECISIONS.md`. T3-04A identity, T3-04B membership/Admin invariants, T3-04B-USER-SCOPE, and T3-04C Work Functions are published; broader Shop API visibility/lifecycle enforcement remains T3-05.

### Phase 3+ Deferred Implementations

- T4-01 Client/Related Person endpoints have Shop A/B direct-ID, search, relationship, and duplicate non-disclosure tests. End-to-end isolation across the complete V1 business workflow is not yet demonstrated; all later business endpoints must adopt/test T3-04 primitives.
- Tenant-aware base model permits `tenant = NULL`; T3-03 establishes trusted request context and T3-04 provides reusable query/object scoping, but neither changes model nullability nor creates domain queries.
- Tenant-context resolution is implemented as URL-path based (`/api/v1/shops/{shop_id}/...`).
- Billing ownership for work belonging to a Related Person is approved as Primary Client ownership and must be enforced in Phase 5.
- Clients/Related Persons, Catalog/Designs, and Measurements/Materials are implemented and published through T4-03; Work, billing, and reports remain unimplemented.

## Historical Phase 1 Verification results

- Repository access: passed.
- Clone: passed.
- Phase 1 corrective changes were committed and published to `origin/main`.
- File inventory and source/configuration inspection: completed.
- Django check: passes without issues.
- Application tests: the then-current full project suite passed (historical; see Current Verification Results above for the present verified result).

## Current root verification

- Repository root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- Documentation: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- `backend/` contains settings and shared model foundation code; runtime Django apps remain under root `apps/`. `apps/clients` and `apps/catalog` are implemented and published through T4-03. `frontend/` is maintained in the isolated frontend worktree; Work, billing, and reports remain unimplemented.

## Historical completed task — T3-04B-USER-SCOPE

- Status: COMPLETE, COMMITTED, and PUBLISHED on `main`; commit `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c`; GitHub Actions Project State Validation run `36591864481` SUCCESS for the exact commit.
- Approved rule: each ordinary User is permanently owned by one Shop. The same person in another Shop has a separate account. Main Supplier accounts remain global. Existing accounts cannot be moved or attached to another Shop.
- Implemented and published: `User.owning_shop`, guarded migration `accounts.0005_user_shop_ownership`, database membership/ownership consistency and immutability checks, atomic Shop-owned account creation, Main Supplier and Shop ADMIN account authority, Shop Admin STAFF/VIEWER reset scope, and regression tests/docs.
- Preflight evidence: local development PostgreSQL database contained zero Users and zero memberships before this migration was applied locally; GitHub CI migration/application validation ran against its disposable PostgreSQL database and passed. No shared/staging/production ownership preflight was performed and no such migration was applied; migration stops with affected UUIDs if it encounters ordinary accounts spanning multiple Shops or with no determinable Shop.
- Pre-publication local validation: focused account/membership/auth regressions 138 passed; PostgreSQL-backed full suite 192 passed, including four concurrency cases; validator tests 14 passed; Django and migration checks passed; OpenAPI passed with two nonfatal role-enum naming warnings; Black/Flake8 passed on new Python files. GitHub Actions Project State Validation passed for the published exact SHA. Shared/staging/production ownership preflight was NOT PERFORMED, and no shared/staging/production migration was applied.
- At the T3-04B-USER-SCOPE checkpoint, T3-04C was awaiting its own authorization. It has since been completed and published. T3-05, T3-05A and Phase 4 have not been started by this task.

## Phase playbook confirmation audit

- All ten phase implementation prompts use the mandatory phase-level activation plus task-level confirmation model.
- Phase confirmation activates scope only; it does not authorize all tasks.
- Each task requires a separate task brief and explicit `CONFIRM TASK <TASK-ID>` before implementation.
- After one task, the agent must validate, document, report, and stop; next-task and next-phase activation are never automatic.
- Phase playbooks 07-10 have now been added with task IDs, validation, handoff, rollback, Definition of Done, and implementation prompts.

## Completed Implementation Record (Phase 2 Complete)

- Phase 1 is complete. F1-01 through F1-05 are all complete.
- Phase 2 is complete.
- B2-01 DRF API Baseline is complete.
- B2-02 JWT Lifecycle implementation is completed and verified.
  - Standard Django CSRF mechanism is implemented.
  - Refresh token cookie lifecycle is implemented.
  - Rotation and blacklist/reuse behavior are implemented.
  - Relevant validation results are recorded accurately .
- B2-03 Permission and tenant-scope interfaces implementation is completed and verified.
  - Reusable tenant queryset scoping is implemented via `TenantScopedMixin`.
  - `IsTenantMember` is intentionally a deny-by-default Phase 3 contract.
  - Actual Shop/User membership is implemented (T3-02), but business tenant isolation (URL context) remains Phase 3.
  - 403/404 boundaries strictly enforced and validated .
- B2-04 is complete and audit-cleared.
  - Custom API exception handler normalizes errors.
  - Throttling configured for auth scopes.
  - `CORS_ALLOWED_ORIGINS` explicitly restricted.
  - Lightweight `/api/health/live/` and DB-connected `/api/health/ready/` probes are operational.
- B2-05 is complete. Schema generation fixed, throttling and CORS tests added. F-01, C-01, C-02, and C-03 resolved. Phase 2 is now complete.
- Python virtual environment `.venv` created, and dependency baseline established. `manage.py check` passed.
- Historical at Phase 2 completion: lint tools ran with existing starter violations; the application suite passed against the devcontainer PostgreSQL database. Current remediation closure validation is recorded above and supersedes old test claims.
- Environment settings are now split into base, dev, test, and prod. `core/settings.py` acts as a backward-compatible router rejecting unknown environments. Missing secrets fail safely.
- The `User` model was decoupled from `django-safedelete` (replaced with `TimeStampedUUIDModel`) to fix identity uniqueness issues with soft-deletion, and base models were refactored to `backend/core/models/base.py`.
- The database migration strategy has been established and documented in `docs/DATABASE.md`. A fresh PostgreSQL migration from an empty database applies perfectly, and the forward-only migration policy is in place.
- JWT configuration hardened with explicit algorithm, UUID claims, signing key, UPDATE_LAST_LOGIN, and 30-min access tokens. Security cookie flags are explicit per environment (dev: disabled, prod: HttpOnly + Secure). Logout view no longer leaks exception details. `.env.example` documents all required variables including `DJANGO_ENV`.
- The JWT blacklist app is installed and configured.

## Canonicalization audit

- The approved target Django structure is documented separately from the current starter paths: `backend/config/settings`, `backend/apps/{accounts,shops,clients,catalog,works,billing,reports,ai_agents,integrations}`, and `backend/core/{models,tenancy,permissions,exceptions,services}`.
- Current root-level `core/`, `apps/accounts/`, `apps/tenants/`, and `apps/common/` references are explicitly labeled as starter transition inputs, not target implementation boundaries.
- Infrastructure direction is documented as Cloudflare Pages, Render, Render PostgreSQL, Cloudflare R2/S3-compatible storage, and an open Django-Q or Celery+Redis worker choice.
- Auth planning now explicitly includes an HttpOnly/Secure refresh cookie, rotation, and reuse detection.

## Historical roadmap update status (2026-09-28; current task status is recorded above)

- V1-ROADMAP-UPDATE and V1-ENVIRONMENT-LOCK were documentation/roadmap work only. T3-02A through T3-04 are implemented. T3-05 onward, T3-05A (Staging Backend Foundation), F7-01A (Staging Frontend & Client Review Checkpoint), and deployments remain unimplemented; each requires its own confirmation. Environment model is locked as LOCAL → STAGING → PRODUCTION.
- Post-V1 work is gated until Phase 10 and the complete V1 Definition of Done are accepted.
- GitHub Actions run 36415017163 passed on repository HEAD before this documentation-only change. This historical CI result does not validate the current documentation diff.
- Historical local validation for the roadmap documentation update: repository validator PASS; validator tests 11 passed; application suite 120 passed; Django system check PASS; migration drift check PASS; `git diff --check` PASS. This does not describe the current T3-03 diff.

## 2026-10-07 — GARMENT-SYSTEM-BACKEND-01 local implementation status

- Exact task confirmation received; implementation is backend-only. Added nullable Shop ownership for garment families and option groups while preserving global rows and global catalog routes. Shop-context APIs create/list Shop families and groups, and replace per-family group configuration with explicit `SINGLE`/`MULTI` plus required/optional settings. Global and same-Shop reuse are allowed; cross-Shop scope is rejected.
- Designs now support nullable Variant at both Shop and global creation APIs. Publishing checks configured group membership, required groups, and single-selection maximum. MeasurementSet can optionally reference an exact published DesignVersion; family/variant/Shop scope is validated and copies preserve the link.
- Migration `0019_shop_owned_garment_systems.py` is authored and was applied by the test runner to the uniquely named disposable PostgreSQL test DB. `manage.py check` PASS; migration drift check reports no model changes. The `apps/` suite passed 390 tests; focused catalog/measurement suite passed 65 tests. OpenAPI regenerated to both schema artifacts with zero errors (29 warnings/13 unique, existing non-blocking warning set). Black and Flake8 PASS; `git diff --check` PASS (line-ending normalization warnings only); `scripts/verify_project_state.py` PASS (459 tests discovered; working tree remains dirty). Existing dirty files from preceding tasks are preserved. No frontend, commit, push, or deploy is included.

## 2026-10-11 — CATALOG-TENANT-DEFAULT-TEMPLATE-LIFECYCLE-CORRECTION-01 local implementation status

- Confirmed behavior: only newly created Shops receive an atomic snapshot of active Back Office family/variant defaults, family translations and group mappings, and published default Designs. Existing Shops are unchanged and are not backfilled; Back Office default edits affect future Shops only.
- For legacy Shops, an explicit per-family **Edit in this Shop** action materializes only the selected global family into an isolated Shop-owned copy; it does not bulk-backfill the Shop or mutate global/other-Shop data. STAFF and ADMIN can then edit the selected working configuration through the same scoped API.
- Shop ADMIN/STAFF can edit and archive/restore Shop-owned seeded families and restore seeded Designs. Family restore reads the latest Back Office default configuration; Design restore creates a new Shop-owned version from the latest published Back Office default while retaining history and source provenance. Global sources and other Shops are not mutated.
- Local migrations `0020_tenant_default_template_sources.py`, `0021_default_seeded_designs.py`, and `0022_unique_tenant_template_variant.py` were created. The backend implementation and frontend lifecycle controls are local and uncommitted. No staging/production, commit, push, or deploy was performed.
- Focused backend lifecycle/catalog/shop-creation PostgreSQL tests: 6 passed on a uniquely named disposable test database. Django system check and migration drift check passed. Frontend catalog/design focused tests: 36 passed; TypeScript typecheck and production build passed (recorded during this task). OpenAPI schema validation and broader test coverage remain to be completed before declaring the task fully closed.
# Variant retirement status

The active Catalog, Design creation, Design listing, and Client Measurement workflows are family-level. Historical Variant references remain readable. Physical removal of the legacy Variant table and historical foreign keys is deferred to a later cleanup after compatibility consumers are confirmed absent.
