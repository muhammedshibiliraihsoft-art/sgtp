# EXISTING-AUTH-REQUEST-FLOWS-01

**Priority:** P1 (password recovery integration), P2 (request efficiency)  
**Status:** Complete locally in `frontend/parallel-foundation`; unpublished, not merged.  
**Effort:** Medium  
**Collision:** Medium/High — `App.tsx`, auth context/services, shared `apiClient`, i18n.

> **Supersession:** `AUTH-RESET-MODEL-CORRECTION-01` supersedes the email-reset and Viewer-login/reset parts of this task. The completion record below preserves what was implemented in the earlier `frontend/parallel-foundation` worktree; it is not current auth guidance. Its search debounce, stale-response protection, Users stats separation, and deferred Design-list request results remain historical records. Email self-service reset was later removed; Shop Admin recovery now uses registered-phone request → Back Office approval, and Shop Admin reset is active same-Shop STAFF only.

## Objective

നിലവിലുള്ള Auth/Shop/Users/Clients/Measurement flows-ൽ കണ്ടെത്തിയ integration, request-efficiency പ്രശ്നങ്ങൾ പരിഹരിക്കുക: backend password recovery-ക്ക് frontend flow, അനാവശ്യ sequential/duplicate auth calls, search-per-keystroke, Users stats refetch, Measurement selection request fan-out.

## Included findings

- Password reset backend ഉണ്ട്; frontend Forgot Password button alert placeholder മാത്രം.
- Session restore: CSRF → refresh → `/users/me` sequential waterfall.
- Login-ൽ duplicate CSRF bootstrap.
- Users/Clients search ഓരോ keystroke-ലും request; Users search/filter മാറ്റങ്ങളിൽ stats വീണ്ടും fetch.
- Family തിരഞ്ഞെടുക്കുമ്പോൾ Measurement definitions/groups/Designs, തുടർന്ന് per-group options ഉൾപ്പെടെ അധിക requests.

## Expected files likely to change

- `frontend/src/App.tsx`, auth routes/screens/context, `frontend/src/services/auth.ts`, auth/API tests.
- `frontend/src/features/users/UsersPage.tsx` / tests.
- `frontend/src/features/clients/ClientsPage.tsx` / tests.
- `frontend/src/features/measurements/ClientMeasurementsPage.tsx`, `api.ts`, tests.
- ആവശ്യമായ locale strings മാത്രം `frontend/src/i18n.ts`.
- Backend code touch only if actual API contract defect is reproduced; report says recovery endpoints exist.

## Must not touch

- JWT claims/lifetime, refresh rotation/blacklisting, HttpOnly cookie policy, CSRF checks, password-change-required gate, Shop/role permissions.
- Backend auth endpoints/schema unless confirmed contract bug blocks UI.
- Other domain pages or shared layout redesign.

## Implementation boundaries

- Password reset request response account enumeration അനുവദിക്കാത്ത generic behavior തന്നെയാകണം; token validation/backend API authoritative ആയിരിക്കണം.
- Auth requests parallelize ചെയ്യുന്നതിന് മുമ്പ് dependency prove ചെയ്യുക; CSRF/refresh ordering മാറ്റരുത്.
- Search debounce bounded ആക്കുക; പഴയ response പുതിയ search result overwrite ചെയ്യാതിരിക്കാൻ cancellation/request identity നൽകുക.
- Users stats filter/page state-ിൽ നിന്ന് വേർതിരിച്ച് fetch ചെയ്യുക; Shop/auth context മാറുമ്പോൾ ശരിയായി refresh വേണം.
- Measurement-ൽ ഇതിനകം loaded family/Shop data reuse ചെയ്യുക; selected group/options മാറുമ്പോൾ മാത്രം ആവശ്യമായ fetch. Tenant authorization bypass ചെയ്യരുത്.

## Validation / impact

- **API/DB/Infra:** മാറ്റമില്ലെന്നാണ് ലക്ഷ്യം; migration ഇല്ല.
- **Business logic:** ഇല്ല; UI/API integration മാത്രം.
- **Security:** auth, CSRF, token lifecycle, generic reset responses സംരക്ഷിക്കുന്ന tests നിർബന്ധം.
- **Focused tests:** reset request/token/expired/error states; login CSRF call count; refresh failure/logout; rapid search/out-of-order response; Users stats call count; Measurement request count, Shop switch.
- **Then domain regression:** existing auth/users/clients/measurement suites. Full suites milestone-ൽ.
- **Rollback:** frontend-only changes revert ചെയ്യാം; API contract additive-only, database state മാറ്റമില്ല.
- **Parallel safe:** NO within this task's files; Task 3-ൽ `apiClient`/shared data work parallel ആക്കരുത്.

## Acceptance

Forgot password UI real backend endpoints ഉപയോഗിക്കുന്നു; generic secure recovery behavior നിലനിൽക്കുന്നു; auth security tests പാസാകുന്നു; search/family selection അനാവശ്യ request storms സൃഷ്ടിക്കുന്നില്ല; existing Shop data flows regress ചെയ്യില്ല.

## Historical completion record — 2026-10-08 (email reset superseded)

- Added a public password-reset request/confirm route using the existing anonymous backend endpoints. Generic account-enumeration-safe response behavior is retained; failed requests preserve the user's email/input, and successful confirmation clears the current in-memory session.
- Removed the redundant post-login CSRF bootstrap while retaining the required pre-login CSRF request and existing CSRF-protected login contract. Refresh/session restore ordering was not changed because it is a security/session dependency.
- Debounced Users and Clients search (250 ms) and guarded results against stale responses. Users summary statistics no longer refetch for search/filter/page changes.
- Deferred global/Shop Design list requests until the Design selector is opened, with request deduplication-by-scope, loading/error/retry states, and stale selection protection.
- Frontend full suite: 135/135 across 29 files; typecheck and production build passed. Lint exited 0 with project `set-state-in-effect` warnings. `git diff --check` passed.
- No backend/API/schema change. Authenticated browser/email-delivery verification was not performed. Work remains local and uncommitted in the frontend worktree; no merge, push, deployment, or cloud write occurred.
