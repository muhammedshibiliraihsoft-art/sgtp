# SGTP Environment Progression

This document defines the approved V1 operating environments and boundaries.

```text
LOCAL → STAGING → PRODUCTION
```

Each deployment or environment change remains subject to the project's phase/task confirmation gate. Do not deploy unfinished commits automatically.

## Company and Domain Model

- **Company:** BiRKy
- **Technical/internal project name:** SGTP
- **Customer-facing product brand:** NOT YET DECIDED — do not invent a product name

### Staging Domains

| Purpose | Hostname |
|---|---|
| Active staging backend/API | `birky-staging-api.onrender.com` |
| Reserved future staging backend/API | `api-staging.birky.com` |
| Planned staging frontend (not provisioned) | `staging.birky.com` |

BiRKy does not currently own/control `birky.com`. The custom API hostname is reserved only and is not configured, DNS-verified, or TLS-verified. The Render provider hostname is the current operational T3-05A backend URL.

### Production Domains (reserved, not provisioned)

| Purpose | Hostname |
|---|---|
| Production frontend | `app.birky.com` |
| Production backend/API | `api.birky.com` |

Production domains are reserved architectural targets only. Do not provision, deploy, or claim they are operational until Phase 10 authorization.

## Local

Developer-controlled environment using local configuration and test data. Secrets remain outside Git. Local success does not establish deployability or production readiness.

## Staging

Staging is the single shared non-production deployment environment. It serves two lifecycle purposes without requiring separate infrastructure.

### Early / Active Development Use

During development, Staging may be used for:

- stable accepted checkpoints
- backend integration validation at `https://birky-staging-api.onrender.com`; client review at `staging.birky.com` awaits a provisioned frontend and controlled domain
- integration validation
- browser testing (auth, cookies, CSRF, CORS, locale, RTL, theme)
- API/frontend integration
- demo/test data

Only accepted stable checkpoints should be deployed. Do not deploy every commit automatically. Client feedback enters normal planning and governance; it does not authorize implementation.

### Phase 9 Formal Staging Use

When Phase 9 begins, the same Staging environment becomes the formal release-candidate validation environment:

- reset/clean staging data where required
- verify production-like configuration
- validate migrations, storage, workers, monitoring
- validate auth/cookies/CSRF/CORS
- validate locale/RTL/theme
- validate PDFs and Shop isolation
- validate backup/restore
- run full end-to-end acceptance

Phase 9 does NOT create a second Staging environment. Early development use is NOT sufficient evidence for Phase 9 completion.

### Staging Backend Foundation (T3-05A complete)

- Render resources and live backend deployment are verified; active URL is `https://birky-staging-api.onrender.com`. T3-05A live auth, token lifecycle, CORS, health, and Shop-isolation checks are complete; see `docs/runbooks/STAGING_BACKEND.md` for evidence.
- Intended Render Web Service and isolated PostgreSQL use the Free plan in Frankfurt. The checked-in `render.yaml` currently sets `autoDeployTrigger: "commit"` for the staging web service, so a `main` push may trigger a staging deploy and migrations; the live provider setting has not been independently verified in this checkpoint. Earlier T3-05A deployments were manual. Free Postgres is temporary (1 GB, 30-day expiry, no backups); free web services sleep after inactivity and use ephemeral filesystems. Free usage overages may be billable; inspect account usage/cost before provisioning and do not approve paid upgrades/add-ons without explicit approval.
- Staging secrets are generated/stored by Render, distinct from local/Production; use synthetic data only. Staging email reset delivery is disabled; the host-only CSRF flow is protected and exact-origin CORS/CSRF are configured.
- `api-staging.birky.com` is a reserved future target only because BiRKy does not currently control `birky.com`; custom DNS/TLS is deferred and is not a blocker for the provider-hosted backend. The staging frontend at `staging.birky.com` is not provisioned; full real-browser frontend/backend integration remains deferred.
- T3-05A is complete: the existing synthetic fixture was preserved; login, refresh/logout CSRF, cookie flags, rotation/reuse rejection, cookie clearing, post-logout rejection, membership/detail/User-ID/stats/Work-Function/direct-object isolation, and Main Supplier approved cross-Shop access were verified. Temporary credential variables are blank and bootstrap/rotation flags are false. Auto-deploy was off at that historical checkpoint; the current checked-in `render.yaml` requests commit-triggered staging deploys. Custom-domain DNS/TLS and real-browser frontend integration remain deferred; see the runbook for evidence and Free-plan limitations.

### Staging Frontend & Client Review Checkpoint (planned F7-01A)

- Future frontend at `staging.birky.com` connected to the active provider backend or, after domain control is established, the reserved `api-staging.birky.com`
- Visible `STAGING — NOT PRODUCTION` indicator; record accepted checkpoint/short SHA
- Browser-verify login, refresh, logout, cookies (SameSite/Secure/HttpOnly), CSRF, Origin, and credentialed CORS
- Use demo/test data and environment-specific configuration; do not add real customer data
- Validate locale support, RTL/LTR foundation, Light/Dark/System foundation

### Staging Security Requirements

- Isolated PostgreSQL (never production data)
- Isolated credentials and secrets
- Isolated object storage where applicable
- Non-production secrets only
- Demo/test data only
- Environment-tagged logs
- Frontend must visibly indicate `STAGING — NOT PRODUCTION` or equivalent
- Never use real production customer data, production payment credentials, production messaging credentials, live production integrations, or production secrets

## Production (Phase 10)

Phase 10 is the only production release gate. Only a Phase 9-approved release candidate may proceed.

Require production secrets, TLS/host/CORS review, PostgreSQL, private storage, workers, migrations, monitoring, tested backups/restore, final security review, complete V1 acceptance and handoff.

Production must NOT be provisioned or deployed before Phase 10 authorization.

Reserved future targets: `app.birky.com` (frontend), `api.birky.com` (backend).

Public product name/domains/hostnames and unresolved business policies require human decisions before they become configuration.

## Auth / Cookie / CSRF Requirements

For the planned custom-domain frontend/API pair (`staging.birky.com` and `api-staging.birky.com`), the roadmap requires browser validation of:

- refresh cookie delivery
- Secure flag
- HttpOnly flag
- SameSite behavior
- CSRF token handling
- Origin validation
- CORS configuration
- credentials mode
- refresh rotation
- logout/cookie clearing

Do not weaken security merely to make Staging work. CORS alone is not sufficient. Any cookie/domain strategy must preserve the existing approved authentication security architecture.

## Cross-environment Security Rules

- Keep credentials, databases, storage, logs, and customer data separated by environment.
- Never copy production data into Staging without explicit approved data-governance authorization and protections.
- Do not log secrets, passwords, tokens, or sensitive recovery material.
- Verify auth cookie `SameSite`/`Secure`, CSRF and Origin protections in a real browser wherever frontend/backend origins differ.
- Failed migrations, health checks, isolation checks, or restore drills stop progression; retain evidence and use the documented recovery path.
- Environment progression is not automatic. Each task/deployment requires its own explicit confirmation.

## Historical Note

An earlier roadmap revision used a four-tier `LOCAL → PREVIEW → STAGING → PRODUCTION` model with a separate Preview environment. That model was superseded by this three-tier model. Preview is not a separate V1 environment; its purposes (client review, early browser validation) are served by the single Staging environment.
