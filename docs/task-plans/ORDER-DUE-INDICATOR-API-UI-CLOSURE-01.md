# TASK ID: ORDER-DUE-INDICATOR-API-UI-CLOSURE-01

Status: VERIFICATION COMPLETE. Backend API serialization and frontend
rendering regression checks passed. No product fix was needed. Authenticated
browser-to-API E2E remains unverified because this frontend has no browser E2E
runner; this is a documented validation limitation, not a blocker for the
approved test-based acceptance criteria.

## Execution note (2026-10-21)

- Backend `DueIndicatorTests` plus
  `WorkApiTests.test_due_indicator_is_serialized_on_work_list_and_detail`:
  3/3 passed. Coverage includes OVERDUE, DUE_TODAY, DUE_SOON at +1/+2 days,
  UPCOMING at +3 days, null due date, and a Shop-local midnight boundary; API
  list and detail both serialize `due_date` and `due_indicator` correctly.
- Tests used the new isolated PostgreSQL database
  `test_order_due_indicator_closure_20261021_01`; Django removed it after the
  run. Read-only post-check confirmed persistent `devdb` and existing `testdb`
  remained present. Neither was used for test writes.
- Active sibling Orders page/API/deleted-orders tests: 35/35 passed; frontend
  typecheck and production build passed. Django model checks passed.
- No application behavior, schema, migration, or API contract changed.
  Frontend component rendering and backend serialization are independently
  covered. Authenticated browser-to-API runtime E2E remains unverified because
  no Playwright/Cypress runner is present.

## Objective

Close the remaining verification gap for Order delivery indicators: prove that
the approved Shop-local due-date rule is serialized by the Work API and shown
correctly in the active Orders list and detail UI. Make a narrowly scoped code
fix only if a test reproduces a defect. The current evidence does not establish
that product code is broken.

## Verified current state

- `docs/BUSINESS_RULES.md` approves the rule: `OVERDUE` after the due date,
  `DUE_TODAY` on the Shop-local due date, `DUE_SOON` beginning two Shop-local
  calendar days before delivery, and no indicator for a missing due date.
- `apps/works/services.py::due_indicator` implements that rule using the Shop
  timezone. `apps/works/serializers.py::WorkSerializer` exposes
  `due_indicator` on Work responses.
- The active sibling frontend's `OrdersPage.tsx` conditionally renders the
  indicator on list cards and includes it in the detail summary. Its type
  union and indicator styles already exist.
- Existing backend unit coverage checks overdue, due-today, two-days-before,
  and upcoming. Existing Orders UI fixtures use a null due date; they do not
  prove visible badge rendering for non-null indicators.
- Current `devdb` has no Order with a due date. Therefore the real runtime
  API-to-UI badge path has not been demonstrated. This is a verification gap,
  not proof of a user-facing defect.

## Scope and ownership

Backend contract/tests, only if required:

- `apps/works/tests/test_work_api.py`
- `apps/works/services.py` or `apps/works/serializers.py` only if a failing
  assertion demonstrates a production-code defect.

Frontend tests/fix, only if required, in the supported sibling worktree
`C:\Users\Admin\Documents\ChatGPT\django 2\sgtp-frontend`:

- `frontend/src/features/orders/OrdersPage.test.tsx`
- `frontend/src/features/orders/OrdersPage.tsx`, `types.ts`, or `orders.css`
  only if a failing test demonstrates a rendering/type/style defect.

Do not edit `sgtp/frontend` or copy/sync source between worktrees. Preserve the
backend `main` and frontend `frontend/parallel-foundation` ownership boundary.

## Execution plan

1. Reconfirm the approved rule and current implementation; capture Git status
   in both worktrees and preserve all existing dirty work.
2. Add/extend backend API tests using the framework's isolated transactional
   test database. Freeze the instant and calculate dates in the Shop timezone.
   Verify the serialized `due_date` and `due_indicator` on list and detail for
   `OVERDUE`, `DUE_TODAY`, `DUE_SOON` at both +1 and +2 days, `UPCOMING` at +3
   days, and a null due date. Include a timezone-boundary case so the cutoff
   is not accidentally tied to UTC.
3. Add/extend active sibling Orders page tests using the corresponding API
   response shape. Verify list badge rendering and detail summary for each
   non-null indicator, and verify that a null indicator shows no badge/label.
4. If a failure occurs, identify whether it is in service calculation, API
   serialization, or UI rendering, then fix only that layer and add a
   regression assertion. Preserve the approved business rule and API shape.
5. Run the focused backend Work API tests and frontend Orders tests, then the
   frontend typecheck/build and Django system check as applicable. If an
   existing authenticated browser E2E harness can safely target an isolated
   test database, also verify the rendered badge through it; otherwise report
   that browser-level runtime E2E remains unverified rather than claiming it
   passed.
6. Inspect the final diff and test discovery/results; update `docs/PROJECT_STATE.md`
   and `docs/HANDOFF.md` only if implementation/validation makes a new current
   state claim necessary.

## Safety and exclusions

- Never set due dates on `ORD-000002` or `ORD-000003`, create/delete Orders in
  persistent `devdb`, or use the current Orders UI to mutate user data for
  testing. Use only the isolated test database or an explicitly disposable
  environment.
- No schema, migration, endpoint, API-contract, workflow, permission, or
  business-rule changes are expected. Any proposed expansion requires a
  separate task and confirmation.
- No reset/clean/stash, commit, push, deploy, or destructive cleanup.
- Do not change the indicator threshold or add a new UX surface. Do not make
  visual changes unless a test proves the existing indicator is not visible or
  legible.

## Acceptance criteria

- The backend response contract is verified for all approved due states,
  including the exact two-day `DUE_SOON` boundary and no due date.
- The active Orders list and detail render the received indicator correctly;
  null remains visually absent.
- Tests execute against isolated data and leave the persistent development DB
  unchanged.
- Any implementation change is minimal, has a regression test, and preserves
  the existing API/business contract.
- Results explicitly separate backend API verification, frontend rendering
  verification, and real browser E2E verification; unrun checks are not
  described as passed.

## Documentation impact

Planning alone does not change architecture docs. If the approved contract,
data flow, dependency map, or compatibility behavior does not change, those
documents remain untouched. Update current-state docs only after verified
implementation and only for materially changed truth.

## Open decisions

None. The due-date business rule is already approved. Whether a code fix is
needed remains unknown until the contract/rendering checks run.
