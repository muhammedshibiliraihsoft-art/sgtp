# FRONTEND-MAIN-RECONCILIATION-01

**Status:** Implemented locally on `main`; unpublished.  
**Working location:** Existing local `main` checkout only.  
**Other branches/worktrees:** Inactive; do not switch to, edit, merge, cherry-pick from, reset, delete, or archive them during this task.  
**Purpose:** Reconcile the requested frontend improvements with what already exists in the current `main` checkout, then implement only the missing behavior directly on `main`.

> **Supersession:** `AUTH-RESET-MODEL-CORRECTION-01` supersedes the email-reset and Viewer-login/reset parts of this task. Its recorded email reset screen and acceptance criteria describe a prior implementation state only and are not current requirements. The following remain valid as historical task outcomes: duplicate post-login CSRF removal, Users-stat request separation, and the non-auth UI/request-efficiency checks. Current recovery is Shop Admin phone request → Back Office approval; Shop Admin staff reset is limited to active same-Shop STAFF; VIEWER has no login.

## User rule

All future implementation for this task is performed in the existing `main` checkout only. A separate frontend branch/worktree is not an implementation source. Do not copy files from it. Its uncommitted work must remain untouched and recoverable while the requested behavior is independently reconciled and implemented on `main`.

## Main-only baseline from source inspection

Already present in the current `main` checkout (avoid duplicate implementation):

- Keyboard foundations: arrow-key grid/tab helpers, custom dropdown keyboard behavior, dialog keyboard manager, and Enter-based Measurement field navigation.
- Shop context/provider and the existing Shop, Team, Client, Catalog, Design, Measurement, Materials, and Inventory screens/API integrations.
- Debounced search behavior in Users, Clients, and Inventory in the current working tree.
- Private-image retry handling and private R2 upload/backend support. Image bytes are still served through the authorized Django endpoint; this plan does not presume that delivery is already CDN/direct-read optimized.
- Client workspace and current Catalog/Measurement UI foundations.

## Historical implementation result — 2026-10-09 (auth recovery superseded)

- At this task's checkpoint, email password reset was added as a distinct public `/reset-password` flow. That email self-service flow was later removed by AUTH-RESET-MODEL-CORRECTION-01; retain this bullet only as historical implementation evidence.
- Login now performs only the required pre-login CSRF bootstrap followed by login; the redundant successful-login CSRF request was removed after checking the current backend contract.
- Users membership listing and Shop capacity stats use independent requests. Stats refresh on Shop/permission changes and member create/deactivate/reactivate/remove, not on search, role/status filter, or pagination. Existing search debounce and stale-result protection remain.
- Rechecked the other listed flows on `main`: Users/Clients/Inventory debouncing, Catalog/measurement keyboard foundations, Measurement Enter navigation, Shop-context stale-user guard, Design-list request bounded to the selected family without re-fetch on Variant changes, and private-image retry behavior are already present. No duplicate implementation or speculative image/CDN/backend change was added.
- No schema/backend changes, commit, push, deployment, shared-database write, or other worktree operation was performed. Existing dirty work was preserved.
- Validation: frontend 166/166 tests across 33 files on final rerun; `npm run typecheck`, `npm run build`, lint (exit 0 with React `set-state-in-effect` warnings), project-state validator, and `git diff --check` passed. One unrelated Catalog pagination assertion was intermittent on the first final run, then passed in isolation and the full-suite rerun. Authenticated browser/email delivery and PostgreSQL-backed backend tests were not part of this frontend-only task. Build output confirms existing login background assets are individually ~1.57–1.83 MB; this is documented as a measured media-optimization follow-up rather than silently recompressing user assets in this task.

Confirmed gaps or behavior requiring targeted reconciliation in `main`:

- The login “Forgot password?” path opens the approved Shop Admin PIN-reset request page. Email self-service reset endpoints and UI are intentionally removed by AUTH-RESET-MODEL-CORRECTION-01.
- Login still performs a second CSRF bootstrap after successful login, although the pre-login CSRF token is sufficient under the current backend contract.
- Users membership and capacity-stat requests are coupled; statistics are fetched again when search/filter/page state changes.
- Several listed Catalog, Measurement, Client/Users UI and Shop-context refinements must be checked against the current `main` behavior before any change; implement only verified gaps. Do not infer that every difference in another worktree is needed.

## Safe implementation sequence

### 0. Preserve and baseline `main`

- Record `git status`, current `main` SHA, existing modified/untracked paths, current test results, and the local frontend server state.
- Treat every pre-existing dirty file as user work. Do not reset, checkout, clean, overwrite, or broadly format it.
- Make a file-level overlap map before edits. Do not merge a whole branch or import a branch worktree.

### 1. Auth recovery and request correctness

- **SUPERSEDED:** Add an explicit email password-reset request and token-confirm screen on `main`, backed by the existing anonymous reset endpoints. Email self-service reset is no longer part of the approved product model.
- Keep the existing Shop Admin PIN-reset flow distinct; do not change its meaning or URL behavior unintentionally.
- Preserve generic account-enumeration-safe responses, CSRF protections, session invalidation, and form values on failure.
- Remove the redundant post-login CSRF bootstrap only after confirming the backend contract/tests; retain the required pre-login CSRF bootstrap and session restore ordering.
- Add UI/service tests for request, confirmation, incomplete/expired link, generic success, server/network failure, and session clearing.

### 2. Reduce avoidable requests

- Isolate Users statistics from search/filter/page requests; refresh stats only when Shop/auth scope or a membership-changing action requires it.
- Audit debounce and stale-response behavior for Users, Clients, and Inventory in the current `main` files. Keep existing working debounce; fix only any reproduced gap.
- Audit Shop-context and Design-picker request counts for duplication/fan-out; preserve authorization and tenant scoping.
- Add request-count and out-of-order response tests. Do not parallelize CSRF/refresh/session dependencies without proving safety.

### 3. Targeted keyboard and workflow reconciliation

- Verify the keyboard foundations already present on `main` are actually wired into the needed Catalog tabs/grids, dropdowns, modals, and Measurement workflow.
- Preserve native keyboard behavior in text/numeric fields and page scrolling; avoid global arrow-key interception.
- Check Catalog family/variant → Design navigation and Measurement Client/garment/Design flow for missing loading, empty, error, retry, focus, and validation behavior.
- Fix only confirmed deficiencies; no broad visual redesign or duplicated component system.

### 4. Client/Users UI and private media

- Verify current Client and Users dialogs/forms, responsive layout, focus restoration, and direct deep-link styling on `main`.
- Keep existing image retry behavior. Inspect private image read delivery and upload fallback separately; make no storage/CDN/security change without a measured bottleneck and explicit scope.
- Preserve private object authorization, Shop isolation, upload limits, and R2 credential boundaries.

### 5. Validation and handoff

- Affected focused tests, the complete frontend suite, typecheck, production build, lint, project-state validator, and `git diff --check` are complete; evidence is recorded above.
- Run relevant backend auth/Shop-isolation tests only where contracts are touched; if PostgreSQL is unavailable, report the verification limit rather than claiming the suite passed.
- **SUPERSEDED:** Perform local UI checks for email reset and representative keyboard flows where an authenticated session permits. The email-reset portion is no longer current; do not treat its planned verification as an active requirement. Do not claim email delivery/browser E2E without evidence.
- Update the main-owned task/handoff records with exact changed files, test evidence, remaining warnings, and any blocked verification.

## Hard safety boundaries

- Do not switch to or operate on another branch/worktree; do not cherry-pick, merge, copy, archive, or delete the separate frontend worktree.
- Do not lose or overwrite any existing dirty `main` changes.
- No backend/schema/migration changes unless a reproduced contract issue makes one necessary; any migration must have separate data-safety review and tests.
- No commit, push, staging/production deploy, shared-database write, cloud-resource change, or real user data creation in this plan.
- Do not claim that changes are committed/published merely because they exist in the local `main` working tree.

## Completion criteria

- The requested features are reconciled against current `main`, with existing functionality retained and only verified gaps changed.
- **SUPERSEDED:** Email password reset is distinct from Shop Admin PIN reset and passes the existing backend contract. Current task acceptance does not include email self-service reset.
- Search/stat request behavior avoids unnecessary calls without stale results or permission regressions.
- Relevant keyboard and responsive flows work without breaking native text entry, focus, or tenant isolation.
- Required local checks pass or each unavailable check is clearly reported.
- All work remains in the existing local `main` checkout; no separate branch/worktree is used.
