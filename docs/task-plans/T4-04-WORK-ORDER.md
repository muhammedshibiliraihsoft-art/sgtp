# T4-04 — Work aggregate and workflow state

Status: Phase 4 was confirmed on 2026-10-16; T4-04–T4-06 are complete in the current staging-source audit candidate. Live staging deployment and database state are unverified.

## Objective

Add Shop-scoped persisted Work/Order records linked to the existing Client,
Design, Measurement, and Material domains. Support a stable searchable Work
number, the approved priority values, due dates, and the fixed workflow from
Request through Completed. This task owns the backend contract. Frontend and
Billing remain outside Phase 4 backend scope; T4-05 transactional hardening
and T4-06 integration validation are later tasks in the same Phase 4 scope.

## Implementation sequence

1. Record the business choices needed for order cardinality, due-soon cutoff,
   and stage-to-function mapping before encoding those rules.
2. Add `apps/works` to the runtime app list and API URLs. Use the existing
   `apps.*` package layout; `backend/apps/works` in the older Phase 4 playbook
   is not a runtime package in this repository.
3. Add additive models and migrations with Shop ownership, protected domain
   references, uniqueness/check constraints, and search/date indexes.
4. Add Shop-scoped list/create/detail and controlled transition endpoints.
   Resolve Shop context before querying linked objects. Reject foreign IDs
   without disclosure and enforce role, membership, function, and assignment
   policy at the backend boundary.
5. Add focused tests for relation validity, Shop isolation, search/pagination,
   priorities/dates, transition policy, and failure cases. Validate schema,
   migration drift, Django checks, and project state using a disposable test DB.

## Confirmed business decisions

- One garment = one Work. Multiple garments require separate Work records.
- Due soon begins two Shop-local calendar days before delivery; due today and
  overdue are separate derived indicators.
- `CHECK` is a new Work Function. Each stage has its own eligible function.
- Clear the assigned worker at every stage transition; assign again for the
  next stage.
- Work creation: active Shop ADMIN, or active STAFF with `SALES` or
  `MEASUREMENT`. VIEWER and Main Supplier without Shop membership cannot write.

## Implemented local backend contract

`apps/works` owns one-garment WorkOrder, stable per-Shop `ORD-000001` numbers,
priority and due date, protected links, fixed transitions, Shop-scoped API and
role/function/assignment policy. Request-stage Work can be soft-deleted by
ADMIN; started/completed Work cannot be deleted. Priority/due/notes updates
require ADMIN. Assignment requires ADMIN and a current-stage-eligible member.
An assigned Work can be advanced only by that member, with the relevant current
stage function; advancement clears assignment. Number high-water mark includes
soft-deleted rows. `tenants.0010` adds CHECK; `works.0001` creates WorkOrder.

### Historical T4-04 delivery validation (2026-10-16)

Validation: disposable PostgreSQL `test_t404_validation_20261016` database,
23/23 Work and Work Function tests PASS; Django check, migration drift,
OpenAPI generation (0 errors, 29 existing warnings), project-state validator
and its 33/33 tests PASS. The app DB was
not migrated. At this checkpoint, the full suite, T4-05 race/audit behavior,
and T4-06 integration validation had not yet been completed.

### Current staging-source revalidation (2026-11-06)

The fetched `origin/staging` source contains the T4-04 aggregate/API and the
T4-05 transactional workflow and audit behavior. T4-06's API journey verifies
Client, DesignVersion, MeasurementSet, Request-to-Completed transitions, and
cross-Shop denial. Focused Work API tests passed 34/34, the full backend suite
passed 598/598 (326 warnings), and the script suite passed 52/52 before a
validator-test cleanup-only change. After that test change, its validator
module passed 46/46 with `unittest`. Fresh PostgreSQL migration replay passed
through the Phase 5 Billing graph. No Work implementation,
API, schema, or migration change was made in this local candidate. This is
source and disposable-database evidence only; no live staging deployment or
database inspection was performed.

No existing local or staging application database is a migration target for
this task without separate explicit authorization.
