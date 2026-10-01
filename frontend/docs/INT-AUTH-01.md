# INT-AUTH-01 — browser authentication integration

Date: 2026-10-01  
Branch: `frontend/parallel-foundation`

## Implemented contract

The frontend uses `VITE_API_BASE_URL` as a public API origin; when unset, calls use the current origin. Requests include cookies. Access credentials remain in memory and are sent as Bearer tokens. Refresh tokens remain in backend-owned HttpOnly cookies and are never read by JavaScript.

- `GET /api/v1/auth/csrf/` returns `{csrf_token}` and sets the CSRF cookie. The frontend bootstraps CSRF before login and refresh/logout and sends `X-CSRFToken` on refresh/logout.
- `POST /api/v1/auth/login/` sends `{identifier,password}` and receives `{access,user}`. Backend profile properties remain snake_case, including `must_change_password`.
- `POST /api/v1/auth/token/refresh/` sends no JSON token. The browser includes the HttpOnly cookie; the backend returns `{access}`. Concurrent 401 responses share one refresh, and a request retries at most once. A late 401 reuses an already refreshed access token.
- `GET /api/v1/auth/users/me/` restores a session after refresh. `POST /api/v1/auth/users/password/change/` sends `{current_password,new_password,new_password_confirm}`; frontend session state is cleared after the backend revokes sessions.
- `POST /api/v1/auth/logout/` uses the access token, cookie credentials, and CSRF header. Frontend auth state is cleared on success or terminal failure; JavaScript does not delete HttpOnly cookies.

Protected routes wait for session restoration. Unauthenticated users go to login; a generated-credential account with `must_change_password` can only enter the password-change screen. Failed refresh clears credentials and auth state. A private response arriving after an account session changes is discarded. No private query cache exists yet.

## Validation

After the auth files were reconciled, `npm run typecheck`, `npm test -- --run` (23 tests across 4 files), and `npm run build` passed. `npm run lint` completed with one existing `react(set-state-in-effect)` warning in `App.tsx`'s workspace menu effect.

`git diff --check` passed (Git reports existing CRLF normalization warnings in user-edited UI files). `python ../scripts/verify_project_state.py` returned PASS with warnings that test discovery is unavailable and the working tree is dirty.

## Known limits

Staging browser CORS/CSRF verification remains outstanding. The checked-in backend `schema.yml` predates T4-01 and does not include current Shop/Client routes; runtime URL/view/serializer/test sources were used instead. Password reset UI remains a follow-up. No backend files were changed and no deployment occurred.

Pre-existing uncommitted UI/logo edits in `App.tsx`, `App.test.tsx`, styles, brand component, image assets, and `frontend/.env.example` were preserved.
