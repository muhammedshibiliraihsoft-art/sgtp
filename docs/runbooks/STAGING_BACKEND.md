# SGTP Staging Backend Runbook

## Purpose and status

This runbook covers the early shared, non-production backend established by T3-05A. It is not the formal Phase 9 release-candidate sign-off and is never Production. Render reports the API/DB resources available, but the current application HTTP smoke check could not resolve the API hostname from this executor. The existing synthetic fixture and T3-05A auth/token and Shop-isolation results are historical checkpoint evidence, not a fresh application check. The 2026-10-18 release preflight verified the service source repository/branch/deploy SHA; that artifact still contains Variant mutation routes and has no `catalog.0024` migration. The staging database's empty IP allowlist blocked SQL inspection, so its current schema, migration ledger, and rows remain **UNVERIFIED**. Custom-domain DNS/TLS and real-browser frontend integration remain deferred.

Active API: `https://birky-staging-api.onrender.com`
Reserved future API target: `https://api-staging.birky.com` (BiRKy does not currently own/control `birky.com`; no active custom-domain declaration, DNS verification, or TLS verification)
Planned frontend (later F7-01A; not provisioned): `https://staging.birky.com`

## Intended infrastructure

- Provider: Render Web Service using the repository Dockerfile and an isolated Render PostgreSQL resource.
- Resource names: `birky-staging-api` and `birky-staging-db`.
- Live Render snapshot (2026-10-18): service `birky-staging-api` uses `https://github.com/muhammedshibiliraihsoft-art/sgtp`, branch `staging`, blank root directory, Docker context `.`, Dockerfile `./Dockerfile`, and auto-deploy trigger `commit`. Latest live deploy is `dep-db6bmmflk1mc73cloku0` at SHA `4db6d9fe14d389c89721707e44ed4526af6a5be3` (2026-10-12); `origin/staging` and the local Git object database contain this SHA. Inspecting that exact source shows Variant mutation methods and Variant-compatible Design/Profile create fields, but no `catalog.0024_retire_variant_measurement_mappings`. This is source-artifact evidence, not a live API response. Render listed no frontend service; Cloudflare Pages settings were not available to this preflight. A GET request could not resolve the API hostname from the current executor. Do not assume the older manual-deploy process still describes provider state; re-check before any publication.
- Region: Frankfurt for web and database co-location and proximity to the approved Kuwait-oriented timezone configuration. This is an operational latency choice, not a legal data-residency commitment. Render does not support changing a resource's region in place.
- Database: PostgreSQL 15, separate staging resource, `sgtp_staging` database name, internal connection string, no public IP allow-list entries.
- Health check: `/api/health/ready/`; liveness remains `/api/health/live/`.
- No frontend, Redis/Key Value, worker, object storage, Production resource, or Production domain is defined here. Full real-browser frontend/API integration is deferred until an actual staging frontend and controlled domain exist.

## Current free-plan limits and cost guard

The Blueprint selects Render's Free web and Postgres plans, currently listed at $0/month. This is temporary demo/test staging, not durable infrastructure. As checked against Render's official documentation on 2026-09-30:

- Free web services spin down after 15 minutes without traffic, take about a minute to resume, can restart, have an ephemeral filesystem, cannot scale beyond one instance, have no persistent disk or shell/SSH access, and cannot send SMTP traffic on ports 25/465/587.
- Free Postgres is limited to 1 GB, expires 30 days after creation (with a 14-day upgrade grace period before deletion), can restart or be unavailable for maintenance, and has no backups or managed connection pooling. Only one Free Postgres may be active per workspace.
- Free services consume included bandwidth/build-pipeline allowances; excess usage may be billed. Check the Render workspace's current billing/usage before creating resources. Do not accept paid upgrades, add-ons, or usage spend without explicit billing approval.
- The free plan does not provide Render's paid pre-deploy command. This single-instance staging configuration runs only committed migrations during guarded startup, after bounded database readiness. It is not a Production migration strategy.

Official references: [Render free services and datastores](https://render.com/docs/free), [Render pricing](https://render.com/pricing), [Blueprint specification](https://render.com/docs/blueprint-spec), [Render deploys and pre-deploy commands](https://render.com/docs/deploys).

## Configuration and secrets

Set `DJANGO_ENV=staging`; `DEBUG` is forced false and startup fails if `DJANGO_DEBUG` is not false. Configure only the canonical API host, the provider-injected `RENDER_EXTERNAL_HOSTNAME`, and the exact frontend origin for CORS/CSRF. Wildcards and unapproved origins fail closed. Render's generated `DJANGO_SECRET_KEY` and the database's internal `DATABASE_URL` must be unique to staging and stored only in Render's secret/environment settings. Do not reuse local or Production secrets or copy Production data.

`.env.staging.example` contains placeholders only. Never create or commit `.env.staging`. The container build excludes local staging env files. The runtime may log the environment and safe host/port diagnostics; it must never log database URLs, passwords, tokens, CSRF values, reset tokens, or secret keys.

Email self-service password reset is superseded and is not part of the current recovery model; no email provider or `/reset-password` email flow is required. A Shop Admin recovery request uses the registered phone number and changes no credential until authorized Back Office approval. The staging dummy email backend remains non-delivering and must never log credentials or recovery material.

## Create and publish

The following is a controlled publication procedure, not a claim that the current service is manual-deploy or connected to `main`. The 2026-10-18 Render snapshot reports commit-triggered auto-deploy from `staging`; any branch push may therefore publish and run committed migrations during startup. Verify current provider branch, trigger, exact deploy SHA, and DB readiness before authorizing a push or deployment. No publication or configuration change was made during the read-only Variant-retirement audit.

1. Connect the repository in the authorized Render workspace and inspect the Blueprint preview before applying it. Confirm both resources remain Free, Frankfurt, and named as staging; confirm the DB is isolated and no paid feature/add-on is selected.
2. If Render requests GitHub authorization, account login, or billing details, the account owner performs that action. Do not share credentials in chat.
3. The resources are `birky-staging-api` and `birky-staging-db`, both Free in Frankfurt. The API is active at `https://birky-staging-api.onrender.com`; PostgreSQL 15 uses logical DB/user `sgtp_staging`. Current provider branch/auto-deploy state is the snapshot above and may differ from the original provisioning setup.
4. The custom API domain is deferred until BiRKy controls `birky.com`. Do not add a custom domain or configure guessed DNS; when ownership is established, use only the exact record Render provides.
5. For each authorized publication, select an accepted SHA whose `Project State Validation` workflow succeeded for that exact SHA; verify the configured provider branch and deployment trigger first. Record the deployed application SHA and deploy identifier. Do not assume a docs-only commit is the live application revision.
6. The container waits for PostgreSQL for at most `DB_WAIT_TIMEOUT_SECONDS`, fails nonzero on timeout, applies committed migrations (`migrate --noinput`), runs `collectstatic`, and then execs Gunicorn using Render's `PORT` and optional concurrency settings. Migration failure stops startup. Never generate migrations in Staging.

## Health, smoke tests, and application checks

Run the unauthenticated health checks without credentials:

```powershell
python scripts/staging_smoke.py https://birky-staging-api.onrender.com
```

The script checks only `/api/health/live/` and `/api/health/ready/`; both must return HTTP 200. A 503 readiness response means the service is not ready. The current provider HTTPS hostname is valid. Verify approved/unapproved Host behavior, CORS preflight for the planned origin `https://staging.birky.com`, CSRF bootstrap, and refresh/logout rejection without CSRF and success with CSRF. Use synthetic accounts only for login, refresh, logout, Shop A/Shop B isolation, Shop list/context/profile/stats, and migration smoke checks. Never place credentials in shell history or output. Real-browser frontend/backend integration is deferred until the frontend exists.

### Initial Render provisioning checkpoint (historical, 2026-09-30)

- Service `birky-staging-api`: Free, Frankfurt, Docker; application auto-deploy off. Database `birky-staging-db`: Free, Frankfurt, PostgreSQL 15, `sgtp_staging` database/user; expires 2026-10-30 and has no backups.
- Initial live deploy `dep-dau6e4ad0e5s73eemlkg` runs application SHA `26760fb9da305968236126024fe98dbbec16f5fc`. Startup logs show committed migrations applied, 164 static files collected, and Gunicorn started. The bootstrap deploy `dep-dau7htek1f9s73amb5p0` created only the synthetic Main Supplier/Shop A/Shop B fixture; no customer data was used. Cleanup deploy `dep-dau7muhsrm7s73b4h1g0` is live on the same SHA after setting the bootstrap flag false and blanking all three credential variables. Health endpoints return HTTP 200 after cleanup.
- Provider-hostname CORS preflight allowed `https://staging.birky.com`; an unapproved origin received no `Access-Control-Allow-Origin`. Synthetic account login succeeded. Refresh without CSRF returned 403; valid-CSRF refresh returned 200 and rotated the refresh cookie. The refresh cookie was Secure, HttpOnly, SameSite=Lax. Authenticated logout without CSRF returned 403 and valid-CSRF logout returned 200. Refresh-cookie clearing and old-token revocation were not conclusively verified. Shop A/B context requests returned own-Shop 200 and foreign-Shop 404; Main Supplier context requests to both Shops returned 200. Membership list/detail, exact User-ID, stats, Work Function, and direct-object isolation remain unverified.
- At this initial provisioning checkpoint, only context-level isolation had been tested. The later final verification below supersedes its partial-verification status; preserve this paragraph as historical evidence.

### Final T3-05A staging verification (2026-09-30)

- Render service `birky-staging-api` is Free, Frankfurt, Docker, with auto-deploy off. Database `birky-staging-db` is Free, Frankfurt, PostgreSQL 15, logical DB `sgtp_staging`; its IP allow-list remains unchanged/empty. No Production resources were created.
- Implementation SHA `b29a897897d35ec9163c510456bd9197b8a4f6e1` passed exact-SHA Project State Validation run `36667104952`. Final cleanup deploy `dep-dau9ptlg1s2s73c2foig` is live on the same SHA. Logs confirmed migrations, collectstatic, and Gunicorn startup; no secret exposure was found. `/api/health/live/` and `/api/health/ready/` returned 200.
- The existing fixture was preserved. Main Supplier, Shop A Admin, and Shop B Admin login succeeded; login JSON omitted refresh tokens. Refresh cookies were HttpOnly, Secure, and SameSite=Lax. Refresh/logout without CSRF were rejected; valid-CSRF refresh rotated the cookie, old-token reuse was rejected, logout cleared the cookie, and refresh after logout was rejected. Approved CORS worked; an unapproved origin received no CORS permission.
- Shop A↔Shop B membership-list/detail, exact User-ID, stats, Work Function, Shop context/profile, and direct-object checks enforced the existing isolation contract in both directions. Main Supplier access to approved Shop A/B surfaces succeeded; Shop-local Work Function management remained denied to Main Supplier as designed.
- Credential rotation was limited to the exact existing synthetic identities and did not recreate Users/Shops/memberships/Work Functions. Temporary credential vars are blank; bootstrap and rotation flags are false. The fixture remains synthetic staging data. The provider hostname is active; custom DNS/TLS and frontend browser integration remain deferred.

The CSRF bootstrap endpoint returns only a masked CSRF token and sets the API-host CSRF cookie; it does not authenticate a caller or expose the refresh token. The refresh cookie remains HttpOnly, Secure in Staging, host-only, and SameSite=Lax. The allowed frontend uses credentialed requests and the returned CSRF token for refresh/logout. No broader `.birky.com` cookie domain is configured. Browser integration remains deferred until the separately authorized staging frontend is actually available (F7-01A).

## One-time Main Supplier Admin bootstrap

Use task `STAGING-MAIN-ADMIN-BOOTSTRAP-01` only when the staging Main Supplier login must be initialized. The `bootstrap_staging_main_admin` management command creates at most one User, does not create a Shop, refuses to promote or reset any existing User, and marks a newly created account `must_change_password=True`. It independently requires `DJANGO_ENV=staging`, settings environment `staging`, database name `sgtp_staging`, an explicit command confirmation, the Render-only enable switch, valid contact details, and a 40-character minimum password. The entrypoint runs it only when `STAGING_MAIN_ADMIN_BOOTSTRAP_ENABLED=true` and `DJANGO_ENV=staging`; the flag defaults off.

For any separately authorized one-time operation, first re-check Render's configured branch and trigger. The latest snapshot above reports `staging` + commit-triggered auto-deploy; do not follow the earlier `main`/manual-deploy assumption. Configure `STAGING_MAIN_ADMIN_EMAIL`, `STAGING_MAIN_ADMIN_FIRST_NAME`, `STAGING_MAIN_ADMIN_LOGIN_ID`, `STAGING_MAIN_ADMIN_PHONE` in E.164 format, and a one-time policy-compliant six-digit `STAGING_MAIN_ADMIN_PIN` in Render secret settings only after approval. Enable the switch only for an accepted exact-CI-green commit on the configured branch. Inspect startup logs only for the generic created/no-op result; they must never reveal input values. Confirm the User through the authorized login/profile route, then immediately set the enable flag to `false` and blank all five input variables and trigger a cleanup deploy. Verify health after cleanup. Do not put secrets in Git, shell history, chat output, or logs. If the configured email, phone, or Login ID is already in use, the command is a successful no-op and leaves that User unchanged; investigate the existing identity separately rather than trying another PIN.

### STAGING-MAIN-ADMIN-BOOTSTRAP-01 completion (2026-10-01)

- Commit `9b8fbc94741d85e018be10fdee41b34bd283af52` passed exact-SHA Project State Validation run `36887320909` and was pushed to `main`. The staging Main Supplier Admin was created by deploy `dep-dav83hhsrm7s73e9llsg`; its startup log confirmed creation without exposing input values. A second same-SHA deploy re-ran the guard and left the account unchanged.
- Cleanup deploy `dep-dav84r3bc2fs738dghi0` is live. The bootstrap switch is disabled, the four input variables are blank, and `/api/health/ready/` returned HTTP 200. No migration, Shop, or Production changes were made.

## Data, reset, and recovery

Only synthetic/demo data is allowed. No seed users/passwords are committed; no demo data is automatically seeded during deploy. Do not upload customer data or Production backups. Persistent private business-file storage is not present; the container filesystem is ephemeral and must not be used as durable media storage.

An operator may clear staging rows while retaining schema/migration history only by running:

```text
python manage.py reset_staging --confirm-staging-reset
```

The command refuses unless `DJANGO_ENV=staging`, the configured DB name is exactly `sgtp_staging`, and the explicit flag is supplied. It is not a public endpoint and does not reseed data. Verify target environment and database identity before running it.

Free Postgres has no backup/restore capability. Do not promise restore or use this setup for valuable data. If a deploy fails, stop further deploys, inspect safe provider build/start logs, and manually redeploy the last known-good exact CI-green application SHA when its schema remains compatible. Migrations are forward-only; do not roll back schema by editing applied migrations. Free-plan database loss means recreate a fresh empty staging database, reapply committed migrations, and regenerate synthetic data. Any future non-additive/destructive migration requires a separately reviewed recovery plan and an appropriate approved plan before deployment.

## Operational limitations and boundaries

- Django's default process-local cache remains in use; auth throttling is not globally coordinated across instances. No Redis/Key Value is added.
- Email self-service password reset is not a current feature; private object storage, durable media, background workers, backup/restore drills, formal Phase 9 acceptance, and full frontend browser integration are not delivered by this backend task.
- Phase 9 reuses this same staging environment after its own authorization and reset/reconfiguration; early T3-05A staging is not Phase 9 completion.
- Production services, database, secrets, domains (`app.birky.com`, `api.birky.com`), data, DNS, migrations, and deployment are prohibited in T3-05A. Phase 10 owns Production.
