# SGTP Staging Backend Runbook

## Purpose and status

This runbook covers the early shared, non-production backend for T3-05A. It is not the formal Phase 9 release-candidate sign-off and is never Production. Repository configuration is prepared in `render.yaml`; a Render account/service is not connected or verified from this workspace, so no staging service or database is currently claimed as provisioned or operational.

Target API: `https://api-staging.birky.com`
Target frontend (later F7-01A): `https://staging.birky.com`

## Intended infrastructure

- Provider: Render Web Service using the repository Dockerfile and an isolated Render PostgreSQL resource.
- Resource names: `sgtp-staging-api` and `sgtp-staging-db`.
- Repository branch: `main`; auto-deploy is explicitly off. Deploy only an intentionally accepted, exact-SHA GitHub-CI-green checkpoint, manually.
- Region: Frankfurt for web and database co-location and proximity to the approved Kuwait-oriented timezone configuration. This is an operational latency choice, not a legal data-residency commitment. Render does not support changing a resource's region in place.
- Database: PostgreSQL 15, separate staging resource, `sgtp_staging` database name, internal connection string, no public IP allow-list entries.
- Health check: `/api/health/ready/`; liveness remains `/api/health/live/`.
- No frontend, Redis/Key Value, worker, object storage, Production resource, or Production domain is defined here.

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

Password-reset delivery is intentionally unavailable: the dummy email backend drops messages and does not write recovery links/tokens to logs. The configured future frontend reset path is `https://staging.birky.com/reset-password`; end-to-end recovery must not be claimed until a separately approved staging email service and frontend exist.

## Create and manually deploy

1. Connect the repository in the authorized Render workspace and inspect the Blueprint preview before applying it. Confirm both resources remain Free, Frankfurt, and named as staging; confirm the DB is isolated and no paid feature/add-on is selected.
2. If Render requests GitHub authorization, account login, or billing details, the account owner performs that action. Do not share credentials in chat.
3. Apply `render.yaml` only after checking the displayed service/database plan and projected cost. Keep auto-deploy off.
4. Add/verify the DNS record using only the exact target Render supplies; never guess it. Wait until Render confirms the custom domain and managed TLS.
5. For each deploy, select a pushed `main` SHA whose `Project State Validation` workflow succeeded for that exact SHA. Trigger deployment manually from Render. Record the deployed application SHA and deploy identifier, separately from later docs-only `main` commits.
6. The container waits for PostgreSQL for at most `DB_WAIT_TIMEOUT_SECONDS`, fails nonzero on timeout, applies committed migrations (`migrate --noinput`), runs `collectstatic`, and then execs Gunicorn using Render's `PORT` and optional concurrency settings. Migration failure stops startup. Never generate migrations in Staging.

## Health, smoke tests, and application checks

Run the unauthenticated health checks without credentials:

```powershell
python scripts/staging_smoke.py https://api-staging.birky.com
```

The script checks only `/api/health/live/` and `/api/health/ready/`; both must return HTTP 200. A 503 readiness response means the service is not ready. Then verify the HTTPS certificate, approved/unapproved Host behavior, CORS preflight for `https://staging.birky.com`, CSRF bootstrap, and refresh/logout rejection without CSRF and success with CSRF. Use synthetic accounts only for login, refresh, logout, Shop A/Shop B isolation, Shop list/context/profile/stats, and migration smoke checks. Never place credentials in shell history or output.

The CSRF bootstrap endpoint returns only a masked CSRF token and sets the API-host CSRF cookie; it does not authenticate a caller or expose the refresh token. The refresh cookie remains HttpOnly, Secure in Staging, host-only, and SameSite=Lax. The allowed frontend uses credentialed requests and the returned CSRF token for refresh/logout. No broader `.birky.com` cookie domain is configured. Browser integration remains deferred until the separately authorized staging frontend is actually available (F7-01A).

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
- Password reset email is disabled; private object storage, durable media, background workers, backup/restore drills, formal Phase 9 acceptance, and full frontend browser integration are not delivered by this backend task.
- Phase 9 reuses this same staging environment after its own authorization and reset/reconfiguration; early T3-05A staging is not Phase 9 completion.
- Production services, database, secrets, domains (`app.birky.com`, `api.birky.com`), data, DNS, migrations, and deployment are prohibited in T3-05A. Phase 10 owns Production.
