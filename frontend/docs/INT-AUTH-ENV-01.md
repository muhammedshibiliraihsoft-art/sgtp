# INT-AUTH-ENV-01 — local and Cloudflare staging auth connectivity

## Architecture

- The browser always calls relative `/api/...` paths. The backend URL is not embedded in frontend assets or `VITE_*` variables. The CSRF client validates the expected JSON shape and shows a clear proxy-configuration error if Pages serves the SPA HTML fallback.
- Local Vite development proxies `/api` to the HTTPS API origin supplied by the server-only `AUTH_API_PROXY_TARGET` variable in ignored `frontend/.env`.
- Cloudflare Pages uses `functions/api/[[path]].ts` as a same-origin `/api/*` proxy. It requires a complete HTTPS `STAGING_API_ORIGIN` and an exact `FRONTEND_ORIGIN` variable matching the Pages request origin.
- No direct cross-site browser requests are used. The Pages function checks unsafe request Origins, forwards Cookie and `X-CSRFToken`, rewrites the already-validated Origin to the API origin for Django CSRF validation, strips upstream cookie Domain attributes so cookies become host-only on the Pages hostname, and returns API responses as `private, no-store`.
- Access-token memory handling, HttpOnly refresh cookie, CSRF bootstrap, bounded refresh retry, single-flight refresh, forced password change and logout clearing remain in the existing auth client.

## Local setup

`frontend/.env` is ignored by Git and should contain:

```env
AUTH_API_PROXY_TARGET=https://birky-staging-api.onrender.com
```

No `VITE_API_BASE_URL` is needed. Restart Vite after changing `.env`. The dev proxy accepts state-changing requests only when their Origin matches the local request host. It rewrites that checked Origin to the upstream API origin for Django's CSRF Origin check. It does not log request headers or bodies.

## Cloudflare Pages configuration

The repository has no Pages or Wrangler config, so confirm the Cloudflare Pages project root includes `frontend/` (or move the function to the configured Pages root) before deploying. Configure these non-secret environment variables in the staging Pages project for each environment that should be reachable:

- `STAGING_API_ORIGIN=https://birky-staging-api.onrender.com`
- `FRONTEND_ORIGIN=https://birky-staging.pages.dev`

Use this exact Pages origin; do not use a wildcard. For local `wrangler pages dev`, copy `.dev.vars.example` to `.dev.vars` and set `FRONTEND_ORIGIN` to the actual local Pages dev origin (normally `http://localhost:8788`). The Pages function fails closed if variables are missing or invalid. No deployment was performed.

Because the browser talks only to its own origin, browser CORS is not used. Django still receives CSRF protection: the proxy accepts unsafe browser requests only from its exact configured frontend origin before supplying the configured API Origin to the backend CSRF middleware. The auth CSRF cookie and refresh cookie are forwarded back as host-only cookies on the frontend origin; existing Secure, HttpOnly, and SameSite flags are preserved. Authenticated API responses are not cached.

## Validation and limits

The repository backend settings show credentialed CORS with an explicit origin list and CORS-all disabled. The deployed Render settings are not available from this checkout, so live staging settings were not independently verified. The exact current `*.pages.dev` hostname was also not present in the repository; set it in Pages as shown above before deploy/browser testing.

Validation completed: frontend typecheck passed; 26 tests across 5 files passed, including 2 Pages proxy tests and a regression test for the HTML fallback; production build passed; lint completed with one existing `react(set-state-in-effect)` warning in `App.tsx`'s workspace menu effect; `git diff --check` passed. The Pages function and its tests also passed a standalone TypeScript check. Local Vite proxy smoke test returned `200` for CSRF bootstrap with a `csrf_token` response property and a `csrftoken` cookie; cookie values were not recorded. A read-only request to the supplied live Pages origin at `/api/v1/auth/csrf/` returned `200 text/html` (the SPA page), not the expected JSON API response, so the current deployment does not serve the Pages API function yet. The project-state validator returned PASS with its standard dirty-tree and test-discovery warnings.

Full browser matrix (login, `/users/me/`, refresh, logout, re-login, forced password change) requires staging credentials and the Cloudflare Pages function to be deployed/configured. Cloudflare/Render deployment and production configuration were not changed. Staging deployment approval is required before Cloudflare browser verification.
