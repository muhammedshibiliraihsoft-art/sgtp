# T4-04 — Work aggregate and workflow state

Status: confirmed on 2026-10-16; backend implementation locally verified, not published.

## Objective

Add Shop-scoped persisted Work/Order records linked to the existing Client,
Design, Measurement, and Material domains. Support a stable searchable Work
number, the approved priority values, due dates, and the fixed workflow from
Request through Completed. This task owns the backend contract. The frontend
slice, transactional workflow hardening in T4-05, integrated T4-06 acceptance,
and Billing are separately gated.

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

Validation: disposable PostgreSQL `test_t404_validation_20261016` database,
23/23 Work and Work Function tests PASS; Django check, migration drift,
OpenAPI generation (0 errors, 29 existing warnings), project-state validator
and its 33/33 tests PASS. The app DB was
not migrated. Full suite, race/idempotency/audit (T4-05), integrated validation
(T4-06), frontend and staging publication remain unverified/separately gated.

No existing local or staging application database is a migration target for
this task without separate explicit authorization.
