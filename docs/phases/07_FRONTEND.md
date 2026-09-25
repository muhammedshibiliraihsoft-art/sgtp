# Phase 7 — Frontend

## 1. Phase Overview

Create the React + Vite + Tailwind client for the approved SGTP workflows after backend contracts and security foundations are ready.

## 2. Phase Objective

Deliver a role-aware, shop-aware frontend that consumes documented APIs without becoming an authorization boundary.

## 3. Business Purpose

Give supplier/main-admin and shop users usable back-office and tailoring workspaces.

## 4. Technical Purpose

Establish frontend structure, API client, authentication/session handling, routing, tenant context, feature screens, loading/error states, and accessibility.

## 5. Preconditions

Phase 6 is complete or explicitly accepted as a dependency; backend API schemas and permission contracts are stable; explicit `CONFIRM PHASE 7` has been received.

## 6. Dependencies

Phases 1–5 backend foundations, Phase 6 integration contracts where UI exposure is approved, API schema, auth/token behavior, shop context, and object permissions.

## 7. Current Repository Assumptions

The repository currently has an empty `frontend/` placeholder and no React implementation. Backend work is the source of truth for authorization and data contracts.

## 8. Exact Scope

React/Vite/Tailwind foundation, authenticated API client, role-aware routing, tenant context, supplier back office, shop workspace, Clients, Designs, Measurements, Materials, Works, Billing, Reports, and approved AI interface points.

## 9. Out of Scope

Changing backend architecture, inventing business rules, bypassing API permissions, adding unapproved modules, deployment, and direct provider/AI control of core workflows.

## 10. Architecture Context

Frontend state and route visibility improve usability only. Every read/write must use backend-authorized APIs and handle denial safely.

## 11. Implementation Sequence

Frontend shell → API/auth client → role/shop routing → back office/shop shell → domain screens → billing/reports → approved AI surfaces → accessibility and integration validation.

## 12. Detailed Task List

### F7-01 Frontend foundation and authenticated API client

- Objective: create the React/Vite/Tailwind shell and typed/request-safe API client.
- Why it exists: all later screens depend on consistent auth, errors, loading, and request behavior.
- Dependencies: approved backend API schema, Phase 2 auth contract, explicit task confirmation.
- Files to create: `frontend/package.json`, Vite/Tailwind config, `src/` shell, API client, auth/session modules, tests.
- Files to modify: only frontend documentation/configuration and root docs as needed.
- Steps: define scripts, environment variables, API base URL, token handling, refresh/revocation behavior, request IDs, normalized errors, loading/cancellation patterns, and secure storage policy.
- Database impact: none.
- API impact: consume documented contracts only; no backend API changes by assumption.
- Security impact: never trust client roles; avoid unsafe token persistence; clear session on invalid refresh.
- Tests required: client errors, token expiry, refresh failure, logout, environment validation.
- Validation: production build, lint/type checks, unit tests, API contract smoke test.
- Documentation update: frontend setup, API contract, state, handoff.
- Definition of Done: shell builds and authenticated requests fail safely.

### F7-02 Role-aware routing and shop context

- Objective: implement supplier back-office and shop workspace navigation with active-shop context.
- Why it exists: users must see the correct workspace without weakening backend isolation.
- Dependencies: F7-01, Phase 3 membership/context API, explicit task confirmation.
- Files to create: route guards, layout/navigation, context stores, permission-aware components, tests.
- Files to modify: API client and app shell.
- Steps: load identity/memberships, select permitted shop, handle inactive/missing context, protect routes, show supplier cross-shop views only when API permits.
- Database impact: none.
- API impact: consume membership/context endpoints; document missing contracts rather than inventing them.
- Security impact: route guards are UX only; handle 401/403/404 and never infer access from hidden UI.
- Tests required: route access matrix, context switching, stale context, denied response handling.
- Validation: browser smoke flows and cross-shop API denial.
- Documentation update: frontend/UX/API/state/handoff.
- Definition of Done: correct shell/context behavior with backend enforcement intact.

### F7-03 Supplier Back Office and Shop workspace

- Objective: deliver approved supplier/shop management screens.
- Why it exists: this is the product hierarchy users operate.
- Dependencies: F7-02, Phase 3 API completion, explicit task confirmation.
- Files to create: back-office/shop pages, forms, tables, empty/error/loading states, accessibility tests.
- Files to modify: route map/navigation and generated API types if used.
- Steps: implement shop/membership views, shop dashboard, filtering/pagination, permission-aware actions, safe destructive/activation confirmations.
- Database impact: none.
- API impact: consume supplier/shop endpoints only.
- Security impact: prevent accidental cross-shop display; do not cache data across contexts without a scope key.
- Tests required: role rendering, denied actions, pagination/filter scope, keyboard/accessibility.
- Validation: end-to-end supplier and shop workspace smoke test.
- Documentation update: state, handoff, UI/API docs.
- Definition of Done: supplier and shop shells are usable and scoped.

### F7-04 Tailor Management screens

- Objective: expose Clients, Designs, Measurements, Materials, Works, workflow, Billing, and Reports using approved contracts.
- Why it exists: frontend must represent the integrated business journey.
- Dependencies: Phases 4–5 APIs, explicit task confirmation.
- Files to create: domain pages/components/forms, workflow timeline, report/PDF actions, tests.
- Files to modify: routes, API client/types, navigation.
- Steps: connect records in workflow order; show transition availability from API; handle conflict/validation/job states; provide history and accessible feedback.
- Database impact: none.
- API impact: consume only versioned endpoints; do not encode unapproved transitions.
- Security impact: render only permitted data; safe file/PDF links; no client-side authorization bypass.
- Tests required: integrated user flows, invalid transitions, 403/404, job failure, file access.
- Validation: end-to-end request-to-report flow in an authorized shop.
- Documentation update: API/UI/state/handoff.
- Definition of Done: frontend supports the approved workflow without duplicating business rules.

### F7-05 Approved AI interface and frontend hardening

- Objective: add only approved AI/integration entry points and harden usability/accessibility.
- Why it exists: supporting tools must remain optional and isolated.
- Dependencies: F7-04, Phase 6 controls, explicit task confirmation.
- Files to create/modify: approved AI widgets, error boundaries, accessibility/performance tests.
- Steps: show consent/status/fallback, never expose provider secrets, handle timeout, add responsive/accessibility/performance checks.
- Database impact: none.
- API impact: async/status contracts only.
- Security impact: no sensitive data leakage; backend remains authoritative.
- Tests required: fallback, timeout, unauthorized action, keyboard/mobile/performance.
- Validation: production build and critical browser journey.
- Documentation update: state, handoff, frontend/security docs.
- Definition of Done: approved UI is resilient and does not couple core workflow to AI.

## 13. Task Dependency Graph

`F7-01 → F7-02 → F7-03 → F7-04 → F7-05`.

## 14. Expected Files / Folders

`frontend/`, `src/`, frontend tests, API client/types, and frontend documentation.

## 15. Expected New Files

Frontend package/configuration, shell, API client, routes, contexts, pages, components, tests.

## 16. Expected Modified Files

Only frontend files, generated contract artifacts, and affected documentation; do not alter backend business rules.

## 17. Database Changes

None directly. Backend schema changes belong to their approved backend phase.

## 18. Migration Requirements

No migrations. Verify frontend compatibility with the deployed API schema.

## 19. API Changes

No unplanned API changes. Record any required contract gap for a separate backend task.

## 20. Backend Changes

None unless a documented contract defect is separately approved; never patch backend behavior silently from frontend work.

## 21. Frontend Changes

All implementation is confined to the approved React/Vite/Tailwind scope and task confirmation.

## 22. Security Requirements

Backend authorization remains authoritative; protect tokens, handle 401/403 safely, avoid sensitive client logs, and scope caches by shop.

## 23. Tenant / Permission Requirements

Route/UI guards mirror backend policy but do not replace it. Active shop must be explicit and visible where appropriate.

## 24. Validation Requirements

Build, lint/type checks, unit tests, accessibility checks, API contract checks, and authorized end-to-end browser flows.

## 25. Testing Requirements

Auth/session, routing/roles, shop context, denial states, workflow forms, billing/report views, file links, AI fallback, regression.

## 26. Error / Failure Handling

Consistent loading/empty/error states, refresh failure logout, 403/404 handling, retries only when safe, cancellation for abandoned requests.

## 27. Documentation Updates

Update API/UI notes, architecture only where actual boundaries change, state, handoff, changelog, and relevant security docs.

## 28. Git Checkpoint Guidance

Create local checkpoints per frontend task; never push automatically.

## 29. Handoff Requirements

Record task, routes/components, API contracts, tests, browser validation, known UX/security issues, and the next task; stop.

## 30. Phase Validation Checklist

- [ ] Shell builds
- [ ] Auth/session is safe
- [ ] Role/shop routing is scoped
- [ ] Back office and shop workspace work
- [ ] Tailor workflow screens use backend contracts
- [ ] Accessibility and browser tests pass

## 31. Definition of Done

Authorized users can operate the approved SGTP workflow through the frontend without frontend-only security assumptions or unapproved business behavior.

## 32. Common Implementation Mistakes

Trusting hidden buttons, storing tokens unsafely, duplicating backend rules, leaking cached shop data, assuming 200 responses, ignoring keyboard/mobile/error states.

## 33. Rollback / Recovery Notes

Revert frontend task commits; disable a broken route behind a feature flag; preserve backend operation; clear stale client caches after contract changes.

## 34. Phase Implementation Prompt

**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 7 only; it does not authorize F7-01 through F7-05. Before each task, present its objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. Implement only the confirmed task, validate it, update documentation, report the result, and stop. Do not begin the next task or Phase 8 automatically.

## 35. Phase Completion Report Format

`Phase: 7` / `Task confirmed:` / `Files/routes:` / `API contracts:` / `Tests/build/browser validation:` / `Security/accessibility:` / `Known issues:` / `Docs updated:` / `Next task requires confirmation:`.
