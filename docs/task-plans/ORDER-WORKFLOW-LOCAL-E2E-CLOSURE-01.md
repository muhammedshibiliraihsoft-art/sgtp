# TASK ID: ORDER-WORKFLOW-LOCAL-E2E-CLOSURE-01

Status: executed locally on 2026-10-21. This file records the plan and verified
execution result; it does not itself change application code or runtime state.

## Objective

Complete a safe, time-boxed local acceptance pass for the existing Order/Work
flow, from its Client/Measurement/Design inputs through the approved production
stages to `COMPLETED`, then record the verified result. The frontend/backend
pair and core Order creation have already had focused checks; do not repeat
broad setup analysis unless a preflight reveals a mismatch.

Total planned time: **110 minutes**. Each block is time-boxed. If a safety
precondition is unknown or a block cannot finish in its allotted time, stop at
that boundary, preserve state, and report the blocker instead of skipping a
gate or extending into unsafe data work.

## Verified architecture boundaries to preserve

- One garment creates one Work. A Work references the selected Client,
  MeasurementSet, and published DesignVersion; do not substitute a mutable or
  differently selected source during the run.
- The existing sequence is `REQUEST → CUTTING → STITCHING → CHECK → FINISHING
  → QC → COMPLETED`. The backend remains authoritative for stage authorization.
- Each stage requires its applicable Work Function. `CHECK` is distinct. A
  transition clears the prior assignee; the next stage needs a new assignment.
- `Due soon` begins two Shop-local calendar days before delivery. It is a
  derived indicator, not a stage.
- Request-stage delete is recoverable/soft delete; the Deleted Orders view is
  read-only. This plan does not delete an Order as test cleanup.
- No schema, migration, new endpoint, workflow rule, role/function change,
  commit, push, or deployment is in scope. A defect requiring one becomes a
  separately scoped task.

### User authorization amendment

The user subsequently clarified that this is a non-production local system and
explicitly authorized testing existing functions. The user separately chose to
create a new test Order in `devdb` while preserving `ORD-000002`. This
authorization superseded only the plan's no-function-change limitation for
temporary test setup; no role or schema changes were authorized or made. The
Admin membership's original empty active function set was restored after the
test. The user-data Order was retained, not deleted as cleanup.

## Four execution blocks

### 1. Docker and local runtime/data-target preflight — 10 minutes

The user opens Docker/local services. Read-only checks confirm Docker Engine is
reachable, the intended frontend is on `127.0.0.1:5173`, the intended backend is
reachable on its configured local endpoint (expected port `8000`), and the
frontend points to that backend. Identify the exact backend database/container
and persistent volume from the running configuration without printing secrets
or changing database selection.

**Gate:** do not run migrations or submit writes if Docker is unavailable, the
backend/DB identity is ambiguous, or the frontend points at another backend.
Report the mismatch and stop this block.

### 2. Core Order integration — 30 minutes

Use the already validated frontend/backend pairing and an authenticated Shop
user. Confirm the selected Client, saved MeasurementSet, and published
DesignVersion are the intended inputs on the final Order review. Prefer an
existing, explicitly user-designated test Order if available. If a new Order is
necessary, state the exact database target and obtain/use only the user's
designated Client and inputs before saving; create at most one and do not
silently clean it up.

Verify the saved Order appears in detail and the normal Orders list with the
same Client, MeasurementSet, DesignVersion, garment, priority, and due date.

### 3. Stage progression and reassignment — 30 minutes

On the explicitly designated test Order, verify each next-stage action in
sequence through `COMPLETED`. At every stage, use an existing eligible Shop
member/Work Function, confirm the previous assignment is cleared on transition,
and assign the next eligible worker. Confirm `CHECK` uses the distinct CHECK
function and that the UI does not permit skipping or reversing a stage. Verify
the rendered stage follows the successful server response and remains unchanged
on a rejected/failed action.

Do not alter memberships, Work Functions, roles, or business records to make a
test pass. If suitable eligible users are unavailable, capture the exact
missing precondition and stop this block.

### 4. Regression and final evidence — 40 minutes

- Check the Order detail/list after refresh and confirm the server-persisted
  final state and source references.
- Verify a representative due date against the approved two-day Shop-local
  `Due soon` cutoff, if the selected test Order has a suitable date.
- Read the Deleted Orders archive/filter path without deleting or restoring
  data; verify Shop scope and its read-only behavior.
- Run focused Work API tests only against a verified disposable test PostgreSQL
  target. Rerun focused frontend Orders tests, typecheck/build, and repository
  state validation if code or task docs changed.
- Update only current-state/architecture sections whose verified truth changed;
  retain `UNVERIFIED` for any flow not exercised. Record exact environment,
  test results, and remaining blockers in `PROJECT_STATE.md` and `HANDOFF.md`.

## Completion criteria

1. The correct local frontend/backend/database pairing is identified and
   documented without changing the database target.
2. A user-designated Order is verified against its selected source records.
3. Every approved stage and stage-level reassignment is validated through
   `COMPLETED`, or a precise blocker is reported without fabricating permissions
   or modifying data to force success.
4. Relevant focused checks pass; no user-data cleanup, migration, commit, push,
   or deployment occurs; the final handoff distinguishes verified evidence
   from unverified behavior.

## Pre-authorization prerequisite snapshot (2026-10-21; superseded)

Docker Engine is reachable. `django_app_db` (Compose project `devcontainer`)
publishes PostgreSQL only on `127.0.0.1:5432` and uses persistent volume
`devcontainer_pgdata`; read-only `psql` confirmed `devdb` / `devuser`, matching
`.env`. The canonical backend is running on `127.0.0.1:8000`; backend liveness,
readiness, and the active sibling frontend's `127.0.0.1:5173/api/health/ready/`
proxy returned HTTP 200. The local frontend is running on `127.0.0.1:5173` and
its Vite process runs from `sgtp-frontend/frontend`. `.env.local` sets
`AUTH_API_PROXY_TARGET=http://127.0.0.1:8000`; despite `.env` containing a
staging origin, the local override is active, as confirmed by the proxied
health response.

The authenticated UI's Orders list and detail both loaded `ORD-000002` in
Request / Normal, with no due date; detail displayed its Client, Measurement
link, and DesignVersion reference. The Deleted Orders UI loaded read-only
history, search, and date-range filters. This is in the persistent user-data
DB, not a disposable test Order. A read-only ORM check confirmed the Client,
MeasurementSet, and DesignVersion IDs match the earlier user-opened New Order
URL inputs; the MeasurementSet belongs to the same Shop and Client, and both
sources share the Abaya Family with the DesignVersion published and available
to the Shop. It remains unchanged; live stage progression was not exercised.

Backend Work API tests passed 15/15 against a separate PostgreSQL 15 container
`codex_order_acceptance_test_20261021`, bound only to `127.0.0.1:55439`, with
an isolated Docker volume and test-only role/database. The suite covers Shop
scope, deleted-order date filtering, the full API stage sequence/function
requirements, and clearing assignment after transition. The test runner only
created/removed its own test DB there. Effective Django settings and a
read-only SQL query confirmed the test target as `testdb@127.0.0.1:55439`, role
`sgtp_test`; the app backend's effective settings and read-only SQL query
separately confirmed `devdb@localhost:5432`, role `devuser`. `.env.test` still
points to `testdb@db:5432` and was not used. Do not use `devdb` for API test
writes or Order stage changes. Reconfirm all live targets read-only at the
planned run.

Read-only stage eligibility check for the selected Shop found active work
function assignments only for SALES, QC, and CASHIER; CUTTING, STITCHING,
CHECK, and FINISHING have no active eligible members. The selected Order is
unassigned. Do not change memberships/functions or advance the persistent
Order; use a separately designated disposable Shop/Order with eligible test
memberships for live stage/reassignment acceptance.

## Execution result (2026-10-21)

**Runtime and DB:** Verified Docker `django_app_db`, Compose project
`devcontainer`, persistent volume `devcontainer_pgdata`, database `devdb`, and
role `devuser`. Canonical backend `127.0.0.1:8000` and active sibling frontend
`127.0.0.1:5173` were running and paired; liveness/readiness and frontend
proxied readiness returned HTTP 200.

**Core Order:** Created the user-approved test Order `ORD-000003` through the
authenticated UI with the selected Client, MeasurementSet, and published
DesignVersion. It appeared in the Orders list. It remains in the persistent
development DB; no cleanup/delete was performed. `ORD-000002` was verified
unchanged at Request / Normal / no due date.

**Stage progression:** With the user's authorization, temporarily enabled all
eight current Work Functions on the existing Admin membership and assigned it
at Request, Cutting, Stitching, Check, Finishing, and QC. The Order advanced in
the approved sequential order through `COMPLETED`; each transition cleared the
previous assignment. CHECK operated as a distinct stage. An ineligible STAFF
assignment at Stitching was rejected. The Admin membership's active function
set was restored to its original empty state using the existing service. No
role changed; eight soft-deleted function-history rows remain as an audit
trail. The Order is now Completed and unassigned. A fresh Orders list showed
the persisted result. The Deleted Orders view was then tested without changing
data: filtering from and to `2026-10-18` returned `ORD-000001`; filtering
`2026-10-19` returned the empty state; Clear restored the archived record.

**Validation:** Frontend Orders page/API/Deleted Orders tests passed 25/25;
frontend typecheck and production build passed. Focused Work API tests passed
15/15 again on a separate isolated PostgreSQL 15 test container; Django
`check --tag models` passed. The Shop-local due-indicator unit test passed for
overdue, due-today, two-days-before (`DUE_SOON`), and upcoming dates. The live
`devdb` has no Orders with a due date, so actual API-to-UI badge rendering is
not E2E-verified. A read-only database check confirmed the temporary Admin
function grant was removed from the active set; pre-existing STAFF
CASHIER/QC/SALES assignments remain. No application source, schema, migration,
API contract, commit, push, or deployment changed.

**Closure:** Local runtime pairing, order/source integration, all sequential
stage transitions/reassignment, ineligible-worker rejection, detail/list
persistence, and Deleted Orders positive/empty date-filter behavior are
verified. Due-indicator calculation is unit-tested, but runtime API/UI rendering
remains unverified until a suitable already-dated Order is available or a
separately authorized safe test fixture is established.
