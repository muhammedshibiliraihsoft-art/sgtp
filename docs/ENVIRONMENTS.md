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
| Staging frontend | `staging.birky.com` |
| Staging backend/API | `api-staging.birky.com` |

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
- client progress review at `staging.birky.com`
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

### Staging Backend Foundation (planned T3-05A)

- Render staging backend connected to isolated staging PostgreSQL
- Demo/test data, separate credentials/configuration, HTTPS, health/readiness checks, safe reset and explicit non-production identity
- No production secrets, customer data, or automatic deployment of every unfinished commit
- Verify environment/host/CORS configuration, migrations, logs, smoke tests and isolation

### Staging Frontend & Client Review Checkpoint (planned F7-01A)

- Frontend at `staging.birky.com` connected to staging backend at `api-staging.birky.com`
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

Because staging frontend and API use separate subdomains (`staging.birky.com` and `api-staging.birky.com`), the roadmap explicitly requires browser validation of:

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
