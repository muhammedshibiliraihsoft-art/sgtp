# Local `main` — Uncommitted Work Audit and Pre-Push Manifest

**Task:** `LOCAL-DIRTY-WORK-DOCUMENTATION-01`  
**Mode:** Original inventory was read-only. Later targeted updates recorded auth docs/OpenAPI, migration integrity, worktree isolation, and frontend reset-residue resolutions; `PRE-PUSH-AUDIT-WORDING-RECONCILIATION-05` aligns the current summaries. The original repository snapshot remains historical evidence.  
**Decision:** `PUSH_READY = NO` — see the exact blockers and exclusions below.

## STAGING-AUTH-INTEGRATION-AND-HARDENING-02 update (2026-10-09)

- **Locally resolved:** `arabic-reshaper==3.0.1` is in canonical `requirements.txt` and imports in `.venv`; Django system check passes. Auth rate limiting now has explicit trusted-client-IP configuration with safe `REMOTE_ADDR` default; pure IP-source regression tests pass 6/6, including spoofed forwarding headers, Render's configured header, native Nginx `X-Real-IP`, and invalid-header fallback.
- **Still blocked:** PostgreSQL-backed auth tests collected 38 but could not start because local PostgreSQL at `127.0.0.1:5432` is unavailable. Per user direction, local DB testing was stopped. Render's read-only SQL connector cannot reach the staging DB because its source IP is not allowlisted and TLS is required; no allowlist change was made. The active staging app database was not used as a test DB. Therefore login CSRF, PIN recovery backend, and DB-backed abuse/concurrency tests have not been validated on this task's exact working tree.
- **Staging state:** read-only Render inspection confirms `birky-staging-api` tracks `main`, auto-deploys on commits, and currently runs `d6560c7c5457df11820686c6b6f3f204338c530a`. No staging deployment or environment write occurred. Staging CSRF, PIN endpoint, and UI checks remain pending.
- **Push/deploy withheld:** the working tree contains extensive unrelated local changes and there is no validated disposable PostgreSQL environment. Before any push, pass focused DB auth tests and establish the exact auth/staging dependency closure; do not treat this update as staging-ready or production-ready.

## 1. Repository snapshot

| Item | Observed state |
|---|---|
| Repository | `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp` |
| Current branch | `main` |
| HEAD | `d6560c7c5457df11820686c6b6f3f204338c530a` |
| `origin/main` at inspection | Same SHA as HEAD; no fetch performed |
| Initial dirty inventory | 142 paths: 109 tracked modified, 33 untracked; all unstaged; 0 staged; 0 tracked deletions |
| After this audit file (initial snapshot) | 143 local paths total; this document was the one additional untracked audit artifact |
| Current `main` dirty inventory (2026-10-09) | 143 paths: 108 tracked modified, 35 untracked (including this audit file), 0 staged; `frontend/src/App.css` is clean after residue removal |
| Diff check | `git diff --check` reported no whitespace errors; Git emitted line-ending-normalization warnings for some CRLF files |
| Submodules | None reported |
| Other worktree | `sgtp-frontend`, branch `frontend/parallel-foundation`, 64 dirty paths; not part of `main` and excluded from this manifest |
| Migration inspection | Resolved by `PRE-PUSH-MIGRATION-INTEGRITY-02` on 2026-10-09. The project `.venv` loads `arabic_reshaper`; runtime graph has 65 nodes with no conflicts/cycles; fresh and published-baseline upgrade replays both pass on local disposable PostgreSQL 15.4. See sections 8 and 11. |

Local `main` HEAD and the local `origin/main` ref both point to the SHA above; the working tree has unpublished changes. `git branch -vv` at initial inspection also showed a local `staging` branch. This audit neither switched branches nor fetched remote state; local-ref equality is not live remote verification.

## 2. Executive disposition

- There is a large, multi-feature local candidate on `main`: authentication/Login ID/PIN and reset flows; Shop-owned garment/catalog/design behavior; measurement-history and measurement UI; client workspace; request/search changes; production-settings hardening; generated OpenAPI and project/task documentation.
- The initial file-by-file inventory contained **86 auth-related paths** when account/tenant implementation, auth tests, Team/Back Office/Login UI, reset services, settings, API docs and generated schema were counted together. This is a historical inventory count, not a recount of the current dirty tree.
- The work is mostly intentional and paired with tests, but it is not a single independently verified release candidate. Auth docs/OpenAPI, migration integrity, worktree isolation, and frontend reset residue have been resolved locally; the release-level blockers in section 3E remain.
- The account migration chain is `accounts.0006 → accounts.0007`. Catalog is `0017 → 0018 → 0019`. These migrations must travel with their models, services, API, tests and schema. The 0018 reverse is deliberately guarded and may refuse rollback if seeded records were edited.
- A `main` push can trigger the connected Render staging service to deploy and run startup migrations, according to the dated OPT-02 evidence. “Push for review” is therefore not deployment-neutral. This audit does not authorize that push.
- No comprehensive secret scan/sign-off is claimed. Ignored local env files are treated as secret-bearing by filename and were not opened or copied into this report. No secret values are reproduced here.

## 3. Exact pre-push manifest

### A. MUST COMMIT / PUSH — candidate paths only after blockers are cleared

There is **no unconditional ready-to-push file set**. Sections 4–5 preserve the original 142-path inventory; the current `main` inventory is 143 paths (108 modified, 35 untracked). The former `frontend/src/App.css` residue is now clean, while other local work and this untracked audit file remain. Keep ignored/local-only items in section 3B excluded. The current candidate still needs the release decisions in section 3E; include this audit artifact in Git only after an explicit include/exclude decision.

The inventory marks each path’s intended task, role, dependencies and candidate disposition. “Candidate” is not approval to stage, commit, push, deploy, or run migrations.

### B. MUST NOT COMMIT / PUSH

Ignored local files/artifacts discovered as relevant to this worktree. They are not in the 142-path Git dirty inventory, but must remain excluded even if a broad force-add is used:

- `.env`
- `.env.prod`
- `.env.test`
- `cloudflare.env`
- `frontend/.env.local`
- `.coverage`
- `backend/.coverage`
- `frontend/dist/`
- `django-admin-local.log`
- `pgsql15-auth-reset-test.log`
- `pgsql15-start.log`

Do not print, copy, force-add, or include contents from the env/credential files. The 64 dirty paths in the separate `frontend/parallel-foundation` worktree are also **not** part of the `main` commit manifest; preserve them and do not merge/cherry-pick them under this task. The precise path list is in section 10.

### C. MANUAL REVIEW BEFORE PUSH

Initial manual-review findings and their current status on `main`:

At the initial audit there were **17 exact paths across 15 findings**. The 13 auth documentation/OpenAPI paths and two frontend reset-residue paths have been resolved locally. The approved auth task reference also received a brief reading note. **Two exact manual-review paths remain open** as one paired production-settings/provider-acceptance issue.

- **Reconciled locally (not yet published):** `docs/API.md`, `docs/BUSINESS_RULES.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/ENVIRONMENTS.md`, `docs/HANDOFF.md`, `docs/PROJECT_STATE.md`, `docs/runbooks/STAGING_BACKEND.md`, `docs/task-plans/FRONTEND-MAIN-RECONCILIATION-01.md`, `docs/task-plans/current-feature-stabilization/02-existing-auth-request-flows.md`, `schema.yml`, and `docs/schema.yml`. Current policy is explicit; history is retained and marked superseded as needed. Both generated schema copies were regenerated and validated with the project virtual environment. `docs/task-plans/AUTH-RESET-MODEL-CORRECTION-01.md` received a reading note distinguishing its initial audit findings from the final approved rules.
- **RESOLVED locally (not yet published):** `frontend/src/App.css` — removed the unreferenced `.password-reset-links` and `.password-reset-success` rules after confirming no frontend consumers. `frontend/src/i18n.ts` — removed unused `authReset` dictionaries from all locales; active Login/PIN-reset copy remains. Frontend-wide residue search is clean; typecheck, focused App/PIN-reset/auth tests (21 tests), and production build pass.
- **PRODUCTION CONFIGURATION / PORTABILITY — RESOLVED LOCALLY (2026-10-09), not yet published:** `backend/config/settings/prod.py` and `core/tests/test_production_settings.py` pass synthetic fail-closed and configuration checks for three deployment shapes: DigitalOcean App Platform, DigitalOcean Droplet/VPS with Nginx + Gunicorn, and another Linux VPS. Hostnames, HTTPS origins, PostgreSQL connection, optional remote-database TLS mode/CA path, and R2 account/bucket remain environment-driven; no DigitalOcean or Render staging host is hard-coded in production settings. Production requires a strong secret, complete database configuration, remote PostgreSQL TLS mode, and private R2. A direct production-settings import cannot use `DJANGO_ENV=staging` to bypass R2; normal staging imports retain their own guard. **Provider switch requires application-code change: NO** within this PostgreSQL + R2 + trusted HTTPS proxy contract; deployment values and process/proxy configuration must change. `DATABASE_URL` now accepts only `sslmode` and `sslrootcert` query options; explicit `DJANGO_DB_SSLMODE` / `DJANGO_DB_SSLROOTCERT` override URL values. Split `DB_*` configuration remains supported, and unsupported or unsafe URL options fail closed. **PRODUCTION WIRING DECISION REQUIRED:** checked-in `docker-compose.prod.yml` is a production-intended template, not a verified live deployment. It does not pass `DJANGO_CSRF_TRUSTED_ORIGINS` or `R2_*` values, and its separate PostgreSQL container has no TLS configuration while production settings require TLS for nonlocal DB hosts. `.dockerignore` excludes `.env.prod`. The user deferred choosing between native Droplet/VPS and Compose runtime, so no Compose or replacement deployment wiring was changed or accepted. Nginx or another trusted proxy must strip client-supplied `X-Forwarded-Proto`, set it correctly, and prevent direct public Gunicorn access. **Production settings acceptance: PASS. Deployment wiring acceptance: DEFERRED pending runtime decision. Live DigitalOcean acceptance: DEFERRED.** No push, deploy, or live provider acceptance is claimed.

  **Superseding local decision — PRE-PUSH-NATIVE-VPS-PRODUCTION-WIRING-08 (2026-10-09):** The preceding runtime-decision/Compose paragraph is historical. **PRODUCTION RUNTIME: Native VPS — LOCKED. CURRENT PROVIDER: DigitalOcean Droplet. PORTABILITY: generic Linux VPS compatible. PRODUCTION WIRING: RESOLVED LOCALLY**, subject to focused validation noted below. `deploy/nginx/sgtp.conf.example` supplies HTTPS reverse proxy, fixed `X-Forwarded-Proto: https`, static alias, and loopback-only upstream; `deploy/systemd/sgtp.service` runs non-root Gunicorn from a venv with external env injection. `deploy/production.env.example` exposes explicit HTTPS CSRF/CORS hosts, both existing PostgreSQL configuration shapes and TLS variables, and all required private R2 variable names. Production settings fail closed without R2; there is no persistent local-media fallback in this runtime. Provider changes need infrastructure/env/DNS/TLS updates, not application-code changes. `docker-compose.prod.yml` is historical/container-only, not the current production runtime. Actual live deployment, secrets, firewall, database/backup acceptance, TLS issuance, and smoke tests remain deferred; no push/deploy is claimed.

  **Focused validation:** production/staging settings tests 49 passed (four existing Django `DATABASES` override warnings); synthetic production `manage.py check --deploy` exited 0 with 13 existing drf-spectacular warnings; static checks passed for env variables, loopback binding, proxy-header overwrite, and three provider-neutral VPS scenarios; `git diff --check` passed with only existing CRLF normalization notices. Native `systemd-analyze verify` and `nginx -t` were unavailable on this Windows host; they remain required against actual server paths/certificates before enabling the service. No live database/provider connection was attempted.

The code/migration inventory otherwise has no file whose purpose is wholly unknown from the observed diffs, task notes and tests. This does not replace a full independent code/security review.

### D. REQUIRED TO TRAVEL TOGETHER

1. **Login identity, PIN compatibility, Viewer eligibility and recovery:** account model/manager/identity/security/backend/serializer/view/routes; `accounts.0006` and `0007`; tenants membership/account creation and role-transition code; abuse/reset services and tests; frontend Login, Team, Shop creation, PIN request/approval UI and service; env/settings, schema and corrected auth docs. Do not publish model code without both migrations or routes without the UI/API tests and schema.
2. **Shop-owned garment system and family-level Design:** catalog models; migration `0019`; catalog services/serializers/views/URLs; measurement relation/serializer/service/view changes; Catalog/Design/Measurement UI and API types; catalog/measurement tests; generated `schema.yml` copies and garment-system API/architecture/business docs. Shop isolation rules and model constraints are one contract.
3. **Measurement version deactivation/history:** migration `0017` (`MeasurementSet.is_active` plus Design idempotency key); measurement model/service/view/API changes; Client history/detail UI and tests; OpenAPI. Keep last active version protection, audit history and pagination semantics together.
4. **Default style-only designs:** migration `0018`; research note; seed-migration safety tests; any schema/catalog tests. It depends on `0017`; never publish `0018` alone. Reverse intentionally raises `IrreversibleError` if a generated seed has been edited or deviated.
5. **Search/request and current client workspace UI:** debounced hook, Clients/Users API consumers and tests; Client detail/history components/styles; relevant service/API tests. Preserve request ordering, stale-result guards, Shop scoping, responsive layout and related-person access together.
6. **Production settings test isolation and hardening:** `backend/config/settings/prod.py`, `core/tests/test_settings.py`, `core/tests/test_production_settings.py`, related environment examples/docs. Do not treat the test configuration as a provisioned production deployment.
7. **Generated API copies:** `schema.yml` and `docs/schema.yml` were regenerated and validated together after the auth source/docs correction. Their SHA-256 hashes match; OpenAPI validation reported 0 errors and the previously recorded warning baseline. Keep both copies paired with API/code changes in any candidate.

### E. PUSH READINESS

**PUSH_READY = NO**

Blocking files/issues:

1. **Production live acceptance remains open, not a repository wiring defect:** native Linux VPS runtime is locked and locally wired; `docker-compose.prod.yml` is historical/container-only. VPS provisioning, DNS/certificates, secrets, firewall, external PostgreSQL connectivity and backup/restore, explicit migration timing, and live smoke checks remain deployment-time gates. No live provider acceptance is claimed.
2. Sign off the remaining candidate-after-review items identified in the inventory: `docs/phases/04_CORE_TAILOR_BUSINESS.md` and the citations in `docs/MEASUREMENT_DESIGN_RESEARCH.md`.
3. Decide whether this untracked audit document belongs in the eventual Git candidate, and complete the final secret scan/sign-off while excluding the local-only files in section 3B.
4. Form one exact reviewed candidate SHA and run the final release gates on that exact candidate. The current local work is uncommitted; earlier targeted checks do not sign off an exact release candidate.
5. Before any `main` push, decide how to handle the documented Render staging `autoDeploy=YES`, `trigger=commit`, and startup migrations.

### F. SAFE FULL-PUSH STATEMENT

**Can all currently approved local project changes be committed and pushed to `main` as the authoritative repository state for subsequent deep review?**

**NO.** Auth docs/OpenAPI, migration integrity, separate-worktree isolation, frontend reset residue, production settings, and native-VPS repository wiring are resolved locally. DigitalOcean live deployment and database recovery/migration acceptance remain deferred procedures. The remaining candidate-after-review sign-offs, audit-file decision, final secret scan, exact candidate SHA and release gates, and Render staging deploy/migration decision remain. All ignored files in section B stay excluded. Nothing was staged, committed, pushed, or deployed. Migrations were executed only against task-created local disposable test databases; no application, staging, or production database was migrated.

## 4. File-by-file inventory — tracked modified paths

All rows below were ` M` (tracked, unstaged modifications) at initial capture. “Candidate, paired” means intentional scope evidence exists but the whole repository is still blocked under section E.

| PATH | GIT STATUS | CATEGORY | FEATURE/TASK | WHAT CHANGED | WHY IT EXISTS | BUSINESS RULE | DEPENDENCIES | REQUIRED? | COMMIT? | RISK / NOTES |
|---|---|---|---|---|---|---|---|---|---|---|
| `.env.example` | M, unstaged | I. TOOLING / CONFIG | Auth PIN correction | Removes email reset URL examples | Keep local template aligned with removed route | No email self-service reset | Auth route/settings | Yes, paired | Candidate, paired | Low; placeholder template only |
| `.env.staging.example` | M, unstaged | I. TOOLING / CONFIG | Auth PIN correction | Removes staging email reset URL | Avoid stale deployment config | Recovery uses PIN request/approval | Auth code + staging settings | Yes, paired | Candidate, paired | Low; no live secret shown |
| `AGENTS.md` | M, unstaged | H. DOCUMENTATION | Production standard adoption | Points engineering work to project standard | Make approved gates discoverable | Standards do not authorize feature work | `docs/PRODUCTION_ENGINEERING_STANDARD.md` | Yes | Candidate | Low; docs-only |
| `apps/accounts/authentication.py` | M, unstaged | B. AUTHENTICATION / SECURITY | AUTH-RESET-MODEL-CORRECTION-01 | Rejects JWT users with `login_enabled=False` | Enforce no-login Viewer policy for issued tokens | Disabled accounts cannot use access tokens | User model + migration 0007 + JWT tests | Yes | Candidate, paired | High; auth gate |
| `apps/accounts/backends.py` | M, unstaged | B. AUTHENTICATION / SECURITY | Login ID / PIN transition | Resolves Login ID; checks `login_enabled` | Retain aliases and block Viewer authentication | Legacy password and PIN share existing hash/login | Identity + User + migration + login tests | Yes | Candidate, paired | High; login/authentication |
| `apps/accounts/identity.py` | M, unstaged | B. AUTHENTICATION / SECURITY | Login ID foundation | Adds Login ID pattern and normalization | Canonical unique human login alias | lowercase 3–32 chars, starts letter | Model/manager/serializer/backend | Yes | Candidate, paired | High; format consistency |
| `apps/accounts/models/__init__.py` | M, unstaged | B. AUTHENTICATION / SECURITY | PIN recovery / abuse controls | Exports reset and attempt models | Allow services/imports to use models | Reset requests persist separately from credentials | `models/reset.py`, migration 0006 | Yes | Candidate, paired | High; model registration |
| `apps/accounts/models/user_manager.py` | M, unstaged | B. AUTHENTICATION / SECURITY | Login ID foundation | Normalizes required superuser Login ID; gates initial secret change | Bootstrap Main Supplier account safely | Login-enabled identities have Login ID | User model + login ID migration | Yes | Candidate, paired | High; bootstrap CLI behavior |
| `apps/accounts/models/users.py` | M, unstaged | B. AUTHENTICATION / SECURITY | Login ID + Viewer eligibility | Adds `login_id`, `login_enabled`, constraints and immutability | Persist canonical identity and eligibility | Existing IDs/hashes preserved; Viewer-only cannot sign in | Migrations 0006/0007 + manager/tests | Yes | Candidate, paired | High; schema/data transition |
| `apps/accounts/security.py` | M, unstaged | B. AUTHENTICATION / SECURITY | PIN/reset/session lifecycle | Creates six-digit PINs, validates weak PINs, revokes sessions | Keep credential changes atomic and invalidate sessions | Legacy password remains valid; new/reset PIN is six digits | User model + reset service + membership transitions | Yes | Candidate, paired | High; credential/session handling |
| `apps/accounts/serializers/__init__.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Login ID, PIN and Viewer rules | Adds Login ID validation; removes email reset serializers; checks disabled login on refresh | Enforce request/response contract | Viewer has no credentials; login-enabled roles require ID | Accounts services/models + frontend + schema | Yes | Candidate, paired | High; API contract |
| `apps/accounts/services/user_lifecycle.py` | M, unstaged | B. AUTHENTICATION / SECURITY | Staff reset authorization | Restricts Shop Admin reset to active same-Shop STAFF | Keep reset authority within tenant/role boundary | Shop ADMIN resets STAFF only | Tenant membership + security service + tests | Yes | Candidate, paired | High; tenant authorization |
| `apps/accounts/tests/test_t302a.py` | M, unstaged | G. TEST | Auth reset correction | Tests email route removal and revised credential behavior | Prevent accidental recovery-route reintroduction | No email self-service route | Accounts serializers/views/URLs | Yes | Candidate, paired | High; contract regression |
| `apps/accounts/tests/test_t304a.py` | M, unstaged | G. TEST | Auth reset correction | Tests removed email endpoint and reset authority boundary | Prevent global reset bypass | Shop ADMIN reset only approved staff scope | User lifecycle + URL/view | Yes | Candidate, paired | High |
| `apps/accounts/tests/test_users.py` | M, unstaged | G. TEST | Login ID / account model | Adjusts superuser setup for required Login ID | Keep account creation tests aligned | Main Supplier login identity requires Login ID | Manager/model migration | Yes | Candidate, paired | Medium |
| `apps/accounts/urls.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Auth reset correction | Removes email-reset routes; retains PIN reset routes | Match public API to approved recovery | No email reset endpoint | Views + frontend PIN service + schema | Yes | Candidate, paired | High; breaking API removal approved |
| `apps/accounts/views/__init__.py` | M, unstaged | B. AUTHENTICATION / SECURITY | Login/PIN/abuse/recovery | Login-ID routing, attempt control, reset endpoints; email views removed | Serve approved auth operations | Generic Shop Admin request; Back Office approval; Staff reset by Shop Admin | Accounts services/models + tenants + frontend | Yes | Candidate, paired | High; public auth endpoints |
| `apps/catalog/measurement_models.py` | M, unstaged | C. BUSINESS RULE IMPLEMENTATION | Measurement/design binding | Adds optional DesignVersion and active flag; validates Shop/family/variant relationship | Preserve version history and scope exact design provenance | Measurement stays independent; optional exact published design link | Catalog DesignVersion + migration 0017/0019 | Yes | Candidate, paired | High; tenant and history integrity |
| `apps/catalog/measurement_serializers.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Measurement design/version API | Exposes design version/activity and create link field | Match new snapshot contract | Optional selected DesignVersion | Model/service + frontend measurement types/API | Yes | Candidate, paired | Medium |
| `apps/catalog/measurement_services.py` | M, unstaged | C. BUSINESS RULE IMPLEMENTATION | Measurement history / custom garment | Adds DesignVersion validation, safe version deactivation, Shop family scoping | Keep immutable measurements, permit recoverable removal | Last active version cannot be deactivated; foreign Shop hidden | Models + migration 0017/0019 + views | Yes | Candidate, paired | High; transaction/history |
| `apps/catalog/measurement_views.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Measurement version deletion | Filters inactive versions and adds owner-scoped DELETE | Expose recoverable deletion to frontend | Preserve history; protect final active version | Service + serializers + schema/tests | Yes | Candidate, paired | High; API and data lifecycle |
| `apps/catalog/models.py` | M, unstaged | D. DATABASE / MIGRATION | GARMENT-SYSTEM-BACKEND-01 | Adds Shop ownership, option selection policy, nullable Design variant and constraints | Support global defaults and Shop-created garment systems | Shop can use global or own records only | Migration 0019 + serializers/services/views | Yes | Candidate, paired | High; schema/tenant boundary |
| `apps/catalog/serializers.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Garment system / Design | Adds tenant-scoped family/group APIs and family-level design/selection payloads | Validate API boundaries | Required/single/multi selection policy; family-level Design allowed | Models/services/views/frontend/schema | Yes | Candidate, paired | High; contract |
| `apps/catalog/services.py` | M, unstaged | C. BUSINESS RULE IMPLEMENTATION | Shop garment / Design workflows | Adds Shop-owned family/group flows, idempotent Design creation and selection validation | Persist custom systems and versioned Designs | No cross-Shop objects; required/SINGLE constraints enforced | Models/migration 0019 + serializers/views/tests | Yes | Candidate, paired | High; transaction/isolation |
| `apps/catalog/tests/test_catalog_api.py` | M, unstaged | G. TEST | Catalog / garment system | Covers custom families, isolation, family-level Design, images, publish/idempotency | Prevent contract and tenant regressions | Shop scope and catalog policy enforced server-side | Catalog model/service/API + migration 0019 | Yes | Candidate, paired | High; broad backend regression |
| `apps/catalog/tests/test_catalog_concurrency.py` | M, unstaged | G. TEST | Design idempotency | Covers concurrent create/retry | Prevent duplicate Design writes | Client request ID is tenant-unique | Design model + migration 0017 + service | Yes | Candidate, paired | High; concurrency |
| `apps/catalog/tests/test_measurements_concurrency.py` | M, unstaged | G. TEST | Measurement writes | Covers concurrent version/write behavior | Guard immutable history under races | Version sequence remains consistent | Measurement service/models | Yes | Candidate, paired | High |
| `apps/catalog/tests/test_measurements_materials_api.py` | M, unstaged | G. TEST | Measurement/history/material API | Tests explicit units, design snapshots, deletion, isolation and export | Verify business/API safety | Exact version history; last active version retained | Measurement models/services/views + migrations | Yes | Candidate, paired | High |
| `apps/catalog/tests/test_mens_shirt_defaults.py` | M, unstaged | G. TEST | Measurement defaults | Tests default measurement/system policy | Prevent unintended default changes | Defaults are style/measurement definitions only as specified | Catalog seeds and measurement services | Yes | Candidate, paired | Medium |
| `apps/catalog/urls.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Catalog and measurement endpoints | Registers new scoped endpoints and version actions | Make new API reachable | Shop URL context governs operations | Views + serializers + OpenAPI | Yes | Candidate, paired | High; route contract |
| `apps/catalog/views.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Catalog/Design API | Adds custom family/group, group policy, nullable variant and idempotency handling | Expose backend services with auth checks | Main Supplier/global vs same-Shop access | Models/services/serializers/tests/schema | Yes | Candidate, paired | High; authorization |
| `apps/common/management/commands/bootstrap_staging_main_admin.py` | M, unstaged | I. TOOLING / CONFIG | Login ID/PIN bootstrap | Uses explicit Login ID and six-digit PIN instead of long bootstrap password | Align staging bootstrap with new identity | Initial admin changes temporary PIN | Account manager/security + env setup | Yes | Candidate, paired | High; operator credentials |
| `apps/common/management/commands/bootstrap_staging_smoke.py` | M, unstaged | I. TOOLING / CONFIG | Auth + staging smoke | Gives synthetic identities Login IDs and constructs smoke credentials safely | Keep repeatable staging smoke aligned | Synthetic accounts only; production identities untouched | Account and tenant creation services | Yes | Candidate, paired | High; staging-only command |
| `apps/common/tests/test_bootstrap_staging_main_admin.py` | M, unstaged | G. TEST | Staging admin bootstrap | Tests PIN config, idempotent collision/no-reset behavior | Prevent bootstrap from replacing existing identity | Existing account collision is no-op | Bootstrap command + User manager | Yes | Candidate, paired | High |
| `apps/tenants/serializers/__init__.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Shop creation / Login ID | Adds first-admin Login ID to Shop create contract | Provide canonical identity at account creation | Shop ADMIN gets Login ID and temporary PIN | Account serializer/service + frontend | Yes | Candidate, paired | High |
| `apps/tenants/serializers/membership.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Viewer promotion | Accepts new Login ID during role transition | Permit Viewer→Staff without credential reuse | Staff login-enabled; Viewer has no login credentials | Membership service + User model | Yes | Candidate, paired | High |
| `apps/tenants/services/membership.py` | M, unstaged | B. AUTHENTICATION / SECURITY | Role transition | Issues temporary PIN on promotion and revokes sessions on role changes | Make eligibility follow role | Staff→Viewer disables login but preserves history/hash | Accounts security + tenant policy + migration 0007 | Yes | Candidate, paired | High; concurrency/session safety |
| `apps/tenants/services/shop_accounts.py` | M, unstaged | C. BUSINESS RULE IMPLEMENTATION | Shop user provisioning | Creates Viewer with no Login ID/usable credential; login roles receive PIN | Enforce role-specific credentials | Viewer is a retained read-only record, not a login account | User model/security + migrations 0006/0007 | Yes | Candidate, paired | High |
| `apps/tenants/tests/test_concurrency.py` | M, unstaged | G. TEST | Membership concurrency | Adds/adjusts concurrency expectations | Prevent membership races/regressions | Membership lifecycle invariants remain atomic | Membership service | Yes | Candidate, paired | High |
| `apps/tenants/tests/test_membership_api.py` | M, unstaged | G. TEST | Role transitions / Login ID | Tests promotion credential return and demotion behavior | Prevent credential/session regression | Viewer→Staff needs login; Staff→Viewer blocks later sign-in | Membership API/service + account migration | Yes | Candidate, paired | High |
| `apps/tenants/tests/test_t302_remediation.py` | M, unstaged | G. TEST | Tenant identity remediation | Adjusts account fixtures/expectations for Login ID | Preserve existing scope regression coverage | Login-enabled accounts are well-formed | User model/serializer | Yes | Candidate, paired | Medium |
| `apps/tenants/tests/test_t304b.py` | M, unstaged | G. TEST | Tenant role lifecycle | Updates expected reset role constraints | Retain approved role boundaries | Viewer reset no longer allowed | User lifecycle/API | Yes | Candidate, paired | High |
| `apps/tenants/tests/test_t304b_concurrency.py` | M, unstaged | G. TEST | Membership concurrency | Adjusts test setup for new identity | Preserve race-test coverage | Same-Shop identity invariants | User model/membership service | Yes | Candidate, paired | Medium |
| `apps/tenants/tests/test_t305_concurrency.py` | M, unstaged | G. TEST | Shop concurrency | Adjusts identity setup | Preserve Shop lifecycle race coverage | Shop ownership/membership consistency | User model/shop services | Yes | Candidate, paired | Medium |
| `apps/tenants/tests/test_tenants.py` | M, unstaged | G. TEST | Shop provisioning | Adjusts account fixture/response expectations | Keep first-admin API tests valid | Shop gets one initial ADMIN identity | Tenant serializer/service/view | Yes | Candidate, paired | Medium |
| `apps/tenants/tests/test_user_scope.py` | M, unstaged | G. TEST | Shop user scope / Viewer | Tests viewer credentials and Staff-only reset | Prevent foreign-shop and role escalation | Tenant scoping; Viewer cannot authenticate/reset | Account + tenant services | Yes | Candidate, paired | High |
| `apps/tenants/views/__init__.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Shop create response | Returns first-admin Login ID and no-store credentials | Give creator exact onboarding identity once | Credentials not cached | Serializer/service + frontend Back Office | Yes | Candidate, paired | High; one-time secret response |
| `apps/tenants/views/membership.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Membership promotion | Returns one-time temp PIN only after promotion | Complete onboarding without a second reset | No-store, role-checked, one-time credential | Membership service + serializer + frontend | Yes | Candidate, paired | High; response secrecy |
| `apps/tenants/views/shop_users.py` | M, unstaged | F. API / CONTRACT / OPENAPI | Shop user create | Makes initial credential optional for Viewer response | Avoid issuing Viewer PIN | Viewer records have no login credential | Shop account service + frontend | Yes | Candidate, paired | High |
| `backend/config/settings/base.py` | M, unstaged | I. TOOLING / CONFIG | Email reset removal | Removes reset URL config | Remove dead email-reset setting | No email recovery link | Auth routes + env templates | Yes | Candidate, paired | Medium; shared settings |
| `backend/config/settings/prod.py` | M, unstaged | I. TOOLING / CONFIG | OPT-02 production guard | Requires debug false, explicit allowed hosts/HTTPS origins and durable R2 when prod runtime | Fail closed on unsafe deployment config | Production must not use wildcard host/origin or ephemeral media | Production tests + env contract | Yes | Candidate after review | High; not a DO deployment |
| `backend/config/settings/staging.py` | M, unstaged | I. TOOLING / CONFIG | Email reset removal | Updates disabled-email message and removes reset URL | Keep staging settings aligned | No email self-service reset | Auth settings/docs | Yes | Candidate, paired | Medium |
| `core/tests/test_settings.py` | M, unstaged | G. TEST | OPT-02 settings isolation | Runs production import in subprocess with fake config | Avoid cached-settings false failures | Production guards remain enforced | `prod.py` + test dependencies | Yes | Candidate, paired | Medium |
| `core/tests/test_staging_settings.py` | M, unstaged | G. TEST | Email reset removal | Removes obsolete reset URL assertion | Keep staging contract test accurate | Email delivery/reset path disabled | Staging settings | Yes | Candidate, paired | Low |
| `docs/API.md` | M, unstaged | H. DOCUMENTATION | Auth + GARMENT-SYSTEM-BACKEND-01 | Documents local Login ID/PIN, Shop catalog and measurement contracts | Explain new API behavior | Role and route statements must match code | Backend + schema | Yes | Auth drift cleared locally; broader manifest review remains | High; schema copies regenerated/validated locally |
| `docs/ARCHITECTURE.md` | M, unstaged | H. DOCUMENTATION | Auth + garment system | Adds local identity/catalog architecture | Document ownership and links | Current recovery rule must be authoritative | Models/services/migrations | Yes | Auth drift cleared locally; broader manifest review remains | High; schema copies regenerated/validated locally |
| `docs/BUSINESS_RULES.md` | M, unstaged | H. DOCUMENTATION | Auth + garment rules | Adds/edits business statements | Preserve rules and history | New PIN/Viewer policy supersedes older recovery sections | Auth and catalog implementation | Yes | Auth drift cleared locally; broader manifest review remains | High; schema copies regenerated/validated locally |
| `docs/CHANGELOG.md` | M, unstaged | H. DOCUMENTATION | Frontend/auth change log | Adds current-local changes | Record product history | Later entry explicitly supersedes email flow | Related task records | Yes | Auth drift cleared locally; broader manifest review remains | Medium; preserve dated historical entry |
| `docs/DEVELOPMENT_PLAN.md` | M, unstaged | H. DOCUMENTATION | Plan/status updates | Adds local work status | Track development state | Historical phases vs present rules are distinguished | Project state/handoff | Yes | Auth drift cleared locally; broader manifest review remains | Medium; preserve dated historical entries |
| `docs/ENVIRONMENTS.md` | M, unstaged | H. DOCUMENTATION | Staging recovery notes | Updates environment narrative | Clarify provider environment | No active email-reset behavior | Settings/runbook | Yes | Auth drift cleared locally; broader manifest review remains | Medium |
| `docs/HANDOFF.md` | M, unstaged | H. DOCUMENTATION | Auth/frontend handoff | Records frontend reset/search work | Transfer current implementation context | Current policy separated from historical task records | Actual routes + task notes | Yes | Auth drift cleared locally; broader manifest review remains | High; schema copies regenerated/validated locally |
| `docs/PROJECT_STATE.md` | M, unstaged | H. DOCUMENTATION | Main source-of-truth status | Records local task completion | State what is implemented | Current policy separated from dated history | Git state + tests + migrations | Yes | Auth drift cleared locally; broader manifest review remains | High; schema copies regenerated/validated locally |
| `docs/phases/04_CORE_TAILOR_BUSINESS.md` | M, unstaged | H. DOCUMENTATION | Phase 4 implementation note | Updates scope/status note | Keep domain phase record | No accidental scope expansion | Catalog/measurement rules | Yes | Candidate after review | Low/Medium; historical status |
| `docs/runbooks/STAGING_BACKEND.md` | M, unstaged | H. DOCUMENTATION | Staging runbook | Updates backend deployment note | Help operate staging | Current recovery does not use email reset | Staging settings | Yes | Auth drift cleared locally; broader manifest review remains | Medium |
| `docs/schema.yml` | M, unstaged | F. API / CONTRACT / OPENAPI | Generated OpenAPI copy | Regenerated schema | Reflect current API contract | Staff-only reset role; removed email endpoints | Django serializers/views + root schema copy | Yes | Auth drift cleared locally; broader manifest review remains | High; do not publish schema separately from its API/code contract |
| `frontend/src/App.css` | M, unstaged at initial capture; now clean | E. FRONTEND / UI | Reset-flow CSS residue | Initially added email-reset classes; removed by cleanup | Was for reset form presentation | Removed email route no longer uses these classes | App components | No stale selectors to publish | RESOLVED LOCALLY; no current diff | Initial finding retained; see section C |
| `frontend/src/App.test.tsx` | M, unstaged | G. TEST | Login/PIN navigation | Tests PIN reset and shared legacy-password/PIN field | Protect login UX compatibility | Same credential field accepts both | App + PinResetPage | Yes | Candidate, paired | Medium |
| `frontend/src/App.tsx` | M, unstaged | E. FRONTEND / UI | Auth recovery + shell | Links Forgot Password to PIN request; adds Back Office PIN request route; labels PIN-change screen | User-accessible approved recovery flow | Staff/Shop Admin recovery is role-separated | PinResetPage + services + backend routes | Yes | Candidate, paired | High; navigation/auth |
| `frontend/src/backoffice/BackOffice.test.tsx` | M, unstaged | G. TEST | Shop onboarding | Tests first-admin Login ID/PIN disclosure in memory only | Prevent local storage persistence | One-time credentials shown securely once | BackOffice pages + shops API | Yes | Candidate, paired | High; credential UI |
| `frontend/src/backoffice/BackOfficePages.tsx` | M, unstaged | E. FRONTEND / UI | Shop creation / Back Office reset link | Adds Login ID field and PIN display; links reset request review | Complete Main Supplier workflows | PIN revealed once; role-scoped staff actions | Shops API + pin reset page + backend | Yes | Candidate, paired | High; one-time secret display |
| `frontend/src/features/catalog/Catalog.css` | M, unstaged | E. FRONTEND / UI | GARMENT-SYSTEM-BACKEND-01 | Styles family group configuration controls | Usable custom family setup | Selection policy set per family-group relation | CatalogPage | Yes | Candidate, paired | Low; responsive visual review pending |
| `frontend/src/features/catalog/CatalogPage.test.tsx` | M, unstaged | G. TEST | Shop Catalog | Tests family/group editing UI | Prevent UI contract regressions | Shop can configure allowed style groups | CatalogPage/API | Yes | Candidate, paired | Medium |
| `frontend/src/features/catalog/CatalogPage.tsx` | M, unstaged | E. FRONTEND / UI | Shop garment system | Adds family/group configuration and creation UX | Allow current catalog customization | Viewer read-only; Shop records remain scoped | Catalog API/types + backend endpoints | Yes | Candidate, paired | High; tenant UI contract |
| `frontend/src/features/catalog/api.test.ts` | M, unstaged | G. TEST | Catalog client API | Tests custom family/group requests | Verify URL/body contract | Shop ID scopes mutations | `api.ts` + backend routes | Yes | Candidate, paired | Medium |
| `frontend/src/features/catalog/api.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | Catalog client API | Adds custom family/group endpoint calls | Connect UI to backend | Same-Shop or global records only | Backend Catalog API + schema | Yes | Candidate, paired | High |
| `frontend/src/features/catalog/types.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | Catalog types | Adds family group selection policy types | Model response/input accurately | SINGLE/MULTI and required flag per family | Backend serializer | Yes | Candidate, paired | Medium |
| `frontend/src/features/clients/ClientDetailPage.tsx` | M, unstaged | E. FRONTEND / UI | Client workspace UX | Reworks structured client detail and embeds measurement history surface | Match requested structured layout | Related-person actions remain owner-scoped | Client APIs + measurement history component/styles | Yes | Candidate, paired | Medium; responsive UI review |
| `frontend/src/features/clients/Clients.test.tsx` | M, unstaged | G. TEST | Client search/detail | Tests debounce, stale responses, access and related people | Prevent excess/stale requests | Only authorized Shop client data shown | ClientsPage/API/useDebouncedValue | Yes | Candidate, paired | Medium |
| `frontend/src/features/clients/ClientsPage.tsx` | M, unstaged | E. FRONTEND / UI | Client search optimization | Debounces search and ignores stale results | Reduce repeated API calls | Current Shop query only | Hook + clients API | Yes | Candidate, paired | Medium |
| `frontend/src/features/designs/DesignsPage.tsx` | M, unstaged | E. FRONTEND / UI | GARMENT-SYSTEM-BACKEND-01 | Allows family-level Designs and Shop-owned families | Remove forced variant dependency | Variant optional; scope is Family or Variant | Catalog API + Design API/types | Yes | Candidate, paired | Medium |
| `frontend/src/features/designs/api.test.ts` | M, unstaged | G. TEST | Family-level Design | Tests nullable variant request | Prevent UI/API incompatibility | Design may attach to family without Variant | Design API + backend serializer | Yes | Candidate, paired | Medium |
| `frontend/src/features/designs/types.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | Family-level Design | Makes variant nullable and adds selection/idempotency fields | Match server contract | Optional variant and selected style IDs | Backend schema/API | Yes | Candidate, paired | Medium |
| `frontend/src/features/measurements/ClientMeasurementsPage.test.tsx` | M, unstaged | G. TEST | Measurement workflow | Covers defaults, custom definitions, design selection, deletion, request safety | Protect workflow and tenant rules | Inch default; design optional; last version preserved | Page/API/backend + migrations 0017/0019 | Yes | Candidate, paired | High |
| `frontend/src/features/measurements/ClientMeasurementsPage.tsx` | M, unstaged | E. FRONTEND / UI | Measurement + Design workflow | Embeddable client measurement/history flow, lazy options, custom definition/design creation, version delete, idempotent save | Integrate agreed steps without separate profile action | Save creates profile/history as needed; Design can be family-level | Measurement APIs + catalog/design APIs + backend | Yes | Candidate, paired | High; many coupled workflows |
| `frontend/src/features/measurements/MeasurementEntryForm.test.tsx` | M, unstaged | G. TEST | Measurement keyboard/unit | Tests inch default, per-field override, Enter navigation | Prevent unit and keyboard regressions | Default INCH, user can override | Entry form | Yes | Candidate, paired | Medium |
| `frontend/src/features/measurements/MeasurementEntryForm.tsx` | M, unstaged | E. FRONTEND / UI | Measurement keyboard/unit | Adds global and per-field unit selection/Enter behavior | Make measurement entry faster | Default unit is inch; explicit values retained | Measurement page + tests | Yes | Candidate, paired | Medium; keyboard/mobile test |
| `frontend/src/features/measurements/Measurements.css` | M, unstaged | E. FRONTEND / UI | Measurement UI | Reworks structured responsive layout | Match Clients page visual language | Mobile one-column; larger viewport paired sections | Measurement components | Yes | Candidate, paired | Medium; visual QA pending |
| `frontend/src/features/measurements/StyleConfiguration.tsx` | M, unstaged | E. FRONTEND / UI | Measurement style configuration | Adapts style setup to family group configuration | Use Shop garment system | Required/single/multi choices from family | Catalog API/types | Yes | Candidate, paired | Medium |
| `frontend/src/features/measurements/api.test.ts` | M, unstaged | G. TEST | Measurement API | Tests version pagination, delete, design linkage and owner scope | Verify endpoint requests | Exact owner/history/version remains scoped | `api.ts` + backend views/schema | Yes | Candidate, paired | High |
| `frontend/src/features/measurements/api.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | Measurement client API | Adds design-version request field, definition creation and delete calls | Connect workflows to backend | Owner-scoped records and explicit units | Backend measurement API + schema | Yes | Candidate, paired | High |
| `frontend/src/features/measurements/types.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | Measurement types | Adds active/design-version and family-group fields | Model data contract | Historical snapshot records exact linked design | Backend serializers | Yes | Candidate, paired | Medium |
| `frontend/src/features/users/ConfirmActionModal.tsx` | M, unstaged | E. FRONTEND / UI | Staff promotion | Collects/validates Login ID when promoting Viewer | Create eligible account identity | Promoted Staff receives one-time PIN | Users API + membership view | Yes | Candidate, paired | High; credential onboarding |
| `frontend/src/features/users/MemberActionsMenu.tsx` | M, unstaged | E. FRONTEND / UI | Staff reset / Viewer | Limits reset action to Staff; role transitions remain | Prevent invalid reset UI | Viewer cannot sign in or be reset | Backend policy + tests | Yes | Candidate, paired | High |
| `frontend/src/features/users/UserForm.tsx` | M, unstaged | E. FRONTEND / UI | User creation | Requires Login ID for Staff; Viewer has no credentials | Match account rules | Viewer record has no Login ID/PIN | Users API + backend serializer | Yes | Candidate, paired | High |
| `frontend/src/features/users/Users.test.tsx` | M, unstaged | G. TEST | Team/credentials | Tests Viewer no-credentials, Staff create/reset and promotion | Prevent role-flow regression | Staff login; Viewer record-only | UserForm/UsersPage/API | Yes | Candidate, paired | High |
| `frontend/src/features/users/UsersPage.tsx` | M, unstaged | E. FRONTEND / UI | Team / Staff reset | Shows one-time PIN, promotion data and Viewer status | Complete role lifecycle UX | Credentials shown once; viewer no-login | Users API + tenant endpoint | Yes | Candidate, paired | High |
| `frontend/src/features/users/api.test.ts` | M, unstaged | G. TEST | Team API | Adjusts response/role contract tests | Guard client contract | Role transitions include needed Login ID | API + backend | Yes | Candidate, paired | Medium |
| `frontend/src/features/users/api.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | Team API | Supports Login ID in role change and one-time credential response | Connect Staff promotion/reset | Same-Shop actions only | Backend membership APIs | Yes | Candidate, paired | High |
| `frontend/src/features/users/types.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | Team types | Adds Login ID/role response fields | Match backend data | Viewer may have null Login ID | User serializer | Yes | Candidate, paired | Medium |
| `frontend/src/features/users/users.css` | M, unstaged | E. FRONTEND / UI | Team UI | Adds role/viewer presentation styles | Distinguish read-only records | No sign-in credential for Viewer | Users components | Yes | Candidate, paired | Low |
| `frontend/src/i18n.ts` | M, unstaged | H. DOCUMENTATION | Auth/measurement/catalog strings | Adds current UI strings; unused email-reset group removed locally | Localize changed user flows | Current text reflects approved PIN flow | App/components | Yes, paired with active UI | RESOLVED LOCALLY; candidate with active strings | Initial stale-key finding cleared; see section C |
| `frontend/src/index.css` | M, unstaged | E. FRONTEND / UI | Shared UI/layout | Adds global layout styling used by responsive pages | Avoid clipping/spacing defects | Shared design tokens/controls retained | Components/styles | Yes | Candidate | Low; global scope, verify visually |
| `frontend/src/services/apiClient.test.ts` | M, unstaged | G. TEST | Request efficiency/error handling | Tests request client behavior/CSRF retry boundary | Prevent auth request regressions | No false retry or duplicate writes | apiClient + auth service | Yes | Candidate, paired | Medium |
| `frontend/src/services/apiClient.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | API client | Validates response shape/timeouts/error flow as changed | Fail visibly on malformed backend payload | Preserve credentials/input on errors | Auth and all API services | Yes | Candidate, paired | High; shared client |
| `frontend/src/services/auth.test.ts` | M, unstaged | G. TEST | Login/session restore | Tests shared password/PIN field, refresh response behavior | Protect legacy password compatibility | Existing hashes remain valid | Auth service + backend refresh contract | Yes | Candidate, paired | High |
| `frontend/src/services/auth.ts` | M, unstaged | B. AUTHENTICATION / SECURITY | Login/session restore | Validates login/refresh user shapes and removes redundant CSRF call | Reduce requests without changing token semantics | Legacy password and PIN both accepted | API client + backend serializer/JWT | Yes | Candidate, paired | High; login/session flow |
| `frontend/src/services/shops.ts` | M, unstaged | F. API / CONTRACT / OPENAPI | Shop onboarding API | Adds first-admin Login ID/response type | Match server Shop creation | One-time PIN and Login ID returned | Tenant serializers/views + BackOffice | Yes | Candidate, paired | Medium |
| `render.yaml` | M, unstaged | I. TOOLING / CONFIG | Email reset removal | Removes stale reset URL variable from staging Blueprint | Prevent unused config drift | No email reset path | Backend staging settings + env docs | Yes, after docs sync | Candidate | Medium; main push can trigger deploy/migrations |
| `schema.yml` | M, unstaged | F. API / CONTRACT / OPENAPI | Generated OpenAPI copy | Regenerated schema | Root API artifact expected by tooling | Must match active endpoints/role scope | Django schema generator + docs copy | Yes | Auth drift cleared locally; broader manifest review remains | High; do not publish schema separately from its API/code contract |

## 5. File-by-file inventory — untracked paths

The original 33 source/migration/test/docs rows marked `??` below were present at initial capture. The last row is this audit file, created after capture. The table is a historical inventory, not an exact current untracked manifest: the later migration-integrity task added `apps/accounts/tests/test_account_login_eligibility_migration.py`. Current untracked count is 35, including that test and this audit file; see section 1.

| PATH | GIT STATUS | CATEGORY | FEATURE/TASK | WHAT CHANGED | WHY IT EXISTS | BUSINESS RULE | DEPENDENCIES | REQUIRED? | COMMIT? | RISK / NOTES |
|---|---|---|---|---|---|---|---|---|---|---|
| `apps/accounts/abuse.py` | ?? | B. AUTHENTICATION / SECURITY | Login/reset abuse controls | HMAC-keyed PostgreSQL attempt bucket consume/release and trusted-source selection | Cross-worker bounded abuse protection | Never trust client-supplied X-Forwarded-For prefix | Reset/User model + settings + views | Yes | Candidate, paired | High; proxy trust assumption documented |
| `apps/accounts/migrations/0006_authattemptbucket_shopadminpinresetrequest_and_more.py` | ?? | D. DATABASE / MIGRATION | Login ID + PIN recovery foundation | Creates attempt/reset request tables; adds Login ID and constraints | Persist aliases and pending review state | Unique canonical Login ID; one pending reset per user | Depends accounts.0005, auth.0012, tenants.0009; model/service/tests | Yes | Candidate, paired | High; migration must travel with code |
| `apps/accounts/migrations/0007_account_login_eligibility.py` | ?? | D. DATABASE / MIGRATION | AUTH-RESET-MODEL-CORRECTION-01 | Adds `login_enabled`, disables Viewer-only users, reverse restores eligibility | Preserve Viewer records while blocking sign-in | Viewer-only account is non-authenticating, hashes/history retained | Depends accounts.0006 + tenants membership schema | Yes | Candidate, paired | High; reversible RunPython, test upgrade/rollback |
| `apps/accounts/models/reset.py` | ?? | B. AUTHENTICATION / SECURITY | PIN reset request/abuse models | Defines attempt bucket and Shop Admin request state constraints | Keep approval audit durable | Phone request does not itself change credentials | Migration 0006 + reset service | Yes | Candidate, paired | High; PII retention policy should be reviewed |
| `apps/accounts/services/shop_admin_pin_reset.py` | ?? | B. AUTHENTICATION / SECURITY | Shop Admin recovery | Submits generic request; Main Supplier approval/rejection; one-time PIN | Controlled privileged recovery | Only eligible Shop Admin; approval revalidates role/contact | reset model + security + ShopRolePolicy | Yes | Candidate, paired | High; authorization/transaction |
| `apps/accounts/tests/test_auth_abuse.py` | ?? | G. TEST | Abuse controls | Tests trusted address extraction, lockout and cleanup | Prevent spoofing and counter regressions | Rate decision is server-side and bounded | abuse service + Postgres model | Yes | Candidate, paired | High |
| `apps/accounts/tests/test_auth_concurrency.py` | ?? | G. TEST | Auth/reset races | Tests concurrent bucket, Login ID, request approval and credential changes | Prevent duplicate/lost updates | Concurrent approval/reset resolves once | abuse/reset services + database constraints | Yes | Candidate, paired | High; DB backend required |
| `apps/accounts/tests/test_login_pin_reset.py` | ?? | G. TEST | Login ID/PIN/Viewer policy | Tests compatibility, reset, legacy passwords and Viewer gating | Capture approved credential transition | No bulk conversion; same hash field; Viewer cannot log in | Account models/services + migrations 0006/0007 | Yes | Candidate, paired | High |
| `apps/catalog/migrations/0017_measurement_version_deactivation_design_retry.py` | ?? | D. DATABASE / MIGRATION | Measurement history + Design idempotency | Adds measurement `is_active`, Design request UUID and tenant-scoped unique constraint | Recoverable version removal and retry safety | Last active version retained; duplicate Design request prevented | Depends catalog.0016, tenants.0009, User; models/services/tests | Yes | Candidate, paired | High; forward schema change |
| `apps/catalog/migrations/0018_seed_remaining_family_design_defaults.py` | ?? | D. DATABASE / MIGRATION | Default style-only designs / OPT-02 | Seeds style-only global designs for families; guarded reverse verifies exact seeded rows | Provide defaults without invented measurements | No numerical tailoring measurements or ease data seeded | Depends catalog.0017; models/seed tests/research doc | Yes | Candidate, paired | High; reverse refuses edited seeds |
| `apps/catalog/migrations/0019_shop_owned_garment_systems.py` | ?? | D. DATABASE / MIGRATION | GARMENT-SYSTEM-BACKEND-01 | Adds family/group Shop owner, selection policy and MeasurementSet DesignVersion; relaxes Design variant | Allow Shop-custom systems and family-level designs | Global or same-Shop references only | Depends catalog.0018, tenants.0009, User; all catalog code/tests/schema | Yes | Candidate, paired | High; schema and tenant isolation |
| `apps/catalog/tests/test_seed_migration_safety.py` | ?? | G. TEST | OPT-02 seed reverse | Tests same-name preservation and guarded rollback | Prevent accidental data deletion | Reverse deletes only unchanged exact seed records | Migration 0018 | Yes | Candidate, paired | High; historical migration state |
| `core/tests/test_production_settings.py` | ?? | G. TEST | OPT-02 production settings | Tests explicit HTTPS origins, durable storage, secure prod flags and fail-closed cases | Prove production settings reject unsafe values | Production cannot silently use unsafe host/origin/storage | `prod.py` + test subprocess | Yes | Candidate, paired | High; not proof of DO deployment |
| `docs/MEASUREMENT_DESIGN_RESEARCH.md` | ?? | H. DOCUMENTATION | Default design research | Records standards and limits of sizing evidence | Separate body measurements from style presets | Do not invent regional sizing/ease figures | Migration 0018 + tests | Yes | Candidate after citation review | Medium; source claims should remain current |
| `docs/OPT_01_BASELINE.md` | ?? | H. DOCUMENTATION | OPT-01 | Records dated baseline and phased plan | Preserve historical evidence | Baseline is not release/production approval | Repo/test evidence at stated date | Yes | Candidate as historical record | Low; date-specific, not current snapshot |
| `docs/OPT_02_RESULT.md` | ?? | H. DOCUMENTATION | OPT-02 | Records settings isolation, migration reverse guard, tests, Render auto-deploy observation | Preserve task-level evidence/limits | No push/deploy authority implied | Core tests + migration tests + Render read-only evidence | Yes | Candidate as historical record | Medium; exact time/scope note |
| `docs/PRODUCTION_ENGINEERING_STANDARD.md` | ?? | H. DOCUMENTATION | Production engineering standard | Adopts risk gates and cross-cutting acceptance | Make user-approved standard usable in repo | Security, data integrity and reliability not traded for cost | AGENTS.md reference | Yes | Candidate | Low; index/adoption document |
| `docs/task-plans/AUTH-RESET-MODEL-CORRECTION-01.md` | ?? | H. DOCUMENTATION | AUTH-RESET-MODEL-CORRECTION-01 | Records approved rules, implementation and checks | Audit auth change | Email reset removed; Staff-only reset; Viewer no-login | Auth code/tests/migrations | Yes | Candidate, paired | Medium; implementation-local status |
| `docs/task-plans/FRONTEND-MAIN-RECONCILIATION-01.md` | ?? | H. DOCUMENTATION | FRONTEND-MAIN-RECONCILIATION-01 | Records `main` reconciliation and test results | Explain UI/API reconciliation | Main-only implementation; no other worktree merge | Frontend code/tests + later Auth correction | Yes | Auth drift cleared locally; broader manifest review remains | High; historical email reset marked superseded |
| `docs/task-plans/current-feature-stabilization/01-current-state-migration-integrity.md` | ?? | H. DOCUMENTATION | CURRENT-STATE-MIGRATION-INTEGRITY-01 | Records migration-safety task | Explain chain validation and bounds | Preserve dirty changes; no staging/production writes | Migrations 0017–0019 + tests | Yes | Candidate historical task record | Medium; verification date-specific |
| `docs/task-plans/current-feature-stabilization/02-existing-auth-request-flows.md` | ?? | H. DOCUMENTATION | EXISTING-AUTH-REQUEST-FLOWS-01 | Records frontend email reset/search implementation on other worktree | Capture prior task history | Superseded auth scope is now explicit | Current AUTH-RESET task + frontend history | Yes | Auth drift cleared locally; broader manifest review remains | High; historical branch context preserved |
| `docs/task-plans/current-feature-stabilization/03-existing-domain-performance-media.md` | ?? | H. DOCUMENTATION | EXISTING-DOMAIN-PERFORMANCE-MEDIA-01 | Plans future media/performance work | Track unimplemented follow-up | Does not authorize implementation | Future task approval | Optional | Candidate plan only | Low; explicitly planned, not implemented |
| `docs/task-plans/current-feature-stabilization/README.md` | ?? | H. DOCUMENTATION | Current feature stabilization | Summarizes task sequence/status | Preserve phased scope | Task 3 still requires separate confirmation | Task plans 01–03 | Yes | Candidate after status cross-check | Medium; Task 2 location wording must be reconciled |
| `frontend/src/PinResetPage.test.tsx` | ?? | G. TEST | Shop Admin PIN reset UI | Tests generic request result and safe failure | Prevent account enumeration and false success | Request does not change PIN | PinResetPage + service/backend | Yes | Candidate, paired | High |
| `frontend/src/PinResetPage.tsx` | ?? | E. FRONTEND / UI | Shop Admin PIN reset UI | Phone submission, generic response and Staff guidance | Provide approved public recovery entry | Phone request alone never changes credentials | `pinReset.ts` + backend public endpoint | Yes | Candidate, paired | High; no email flow |
| `frontend/src/backoffice/PinResetRequestsPage.test.tsx` | ?? | G. TEST | Back Office PIN approval UI | Tests approve/reject and one-time result | Protect privileged recovery UX | PIN only on approval | Page/service/backend | Yes | Candidate, paired | High |
| `frontend/src/backoffice/PinResetRequestsPage.tsx` | ?? | E. FRONTEND / UI | Back Office PIN approval UI | Lists requests and reveals temporary PIN once | Complete Main Supplier recovery | Only Main Supplier resolves request | service + backend permission checks | Yes | Candidate, paired | High; sensitive one-time data |
| `frontend/src/features/clients/ClientMeasurementHistory.test.tsx` | ?? | G. TEST | Client measurement history | Tests pagination, exact version, copy and deletion guard | Prevent history UX regressions | Final active version cannot be removed | Component + Measurement API | Yes | Candidate, paired | High |
| `frontend/src/features/clients/ClientMeasurementHistory.tsx` | ?? | E. FRONTEND / UI | Client measurement history | Lazy pages, details, copy, compare, export and protected deletion | Present structured version history on client page | Existing immutable records remain auditable | API + measurement types | Yes | Candidate, paired | Medium/High |
| `frontend/src/features/clients/client-workspace.css` | ?? | E. FRONTEND / UI | Client workspace UX | Styles client overview/history and related persons | Reuse structured layout language | Related persons remain a separate region within layout | Client components | Yes | Candidate, paired | Medium; responsive review |
| `frontend/src/features/designs/DesignsPage.test.tsx` | ?? | G. TEST | Family-level Design | Tests create without Variant | Prevent forced-Variant regression | Family-level Design allowed | DesignsPage/API + backend | Yes | Candidate, paired | Medium |
| `frontend/src/hooks/useDebouncedValue.ts` | ?? | E. FRONTEND / UI | Search debounce helper | Small shared timing hook | Reduce requests during typing | No business data changes | Clients/users consumers | Yes | Candidate, paired | Low; source helper, not generated output |
| `frontend/src/services/pinReset.ts` | ?? | F. API / CONTRACT / OPENAPI | PIN recovery client | Calls public request and privileged review endpoints | Share endpoint contract between pages | Generic public response; authorized approval | Backend reset routes/schema | Yes | Candidate, paired | High |
| `docs/local-main-uncommitted-work-audit.md` | ?? (created by this audit) | H. DOCUMENTATION | LOCAL-DIRTY-WORK-DOCUMENTATION-01 | This read-only manifest/report | Preserve exact inventory and blockers for reviewer | Does not authorize publication | Initial Git snapshot + evidence above | Requested artifact | Commit only if user wants audit retained | Low; adds one new untracked file |

## 6. Business-rule and authentication source-of-truth map

| Concern | Current local source files | Rule / status |
|---|---|---|
| User identity / immutable IDs | `apps/accounts/models/users.py`, `apps/accounts/identity.py`, `apps/accounts/models/user_manager.py` | UUID remains primary identity; generated `user_code` remains; optional legacy contact aliases stay; canonical `login_id` is unique and immutable once assigned. |
| Login ID resolver | `apps/accounts/backends.py`, `apps/accounts/serializers/__init__.py` | Existing user_code/email/phone and Login ID resolve to the same User. |
| Legacy password + PIN compatibility | `apps/accounts/security.py`, `apps/accounts/serializers/__init__.py`, `frontend/src/App.tsx`, `frontend/src/services/auth.ts` | Same Django password hash/input. Existing long passwords are not bulk-converted or rejected; new/reset PINs are six digits. |
| PIN generation/validation/hash | `apps/accounts/security.py`, `apps/tenants/services/shop_accounts.py`, `apps/accounts/services/shop_admin_pin_reset.py` | Temporary PIN is generated; weak patterns are rejected; Django hashes it through existing password setting. |
| `login_enabled` / Viewer no-login | `apps/accounts/models/users.py`, migrations `0007`, `apps/accounts/backends.py`, `apps/accounts/authentication.py`, refresh serializer | Viewer-only account disabled without account/history/hash deletion; login, access JWT and refresh are checked. |
| JWT and session revocation | `apps/accounts/authentication.py`, `apps/accounts/security.py`, serializers/views | `auth_version` and blacklist revocation remain; role changes revoke sessions. |
| Abuse limits | `apps/accounts/abuse.py`, `apps/accounts/models/reset.py`, `apps/accounts/views/__init__.py`, migration `0006` | Persistent bounded attempt counters and generic reset response. Proxy address trust needs operations proxy assumption maintained. |
| Staff reset | `apps/accounts/services/user_lifecycle.py`, account views/serializers, Team frontend | Active same-Shop STAFF only, by that Shop ADMIN; VIEWER and cross-Shop reset denied. |
| Shop Admin recovery request | `apps/accounts/services/shop_admin_pin_reset.py`, `frontend/src/PinResetPage.tsx`, `frontend/src/services/pinReset.ts` | Phone submission returns generic response and does not change credentials. |
| Back Office approval | reset service, account views/URLs, `frontend/src/backoffice/PinResetRequestsPage.tsx` | Main Supplier approves/rejects; approval rechecks eligibility and reveals one-time PIN. |
| Role changes | `apps/tenants/services/membership.py`, tenant view/serializer, Users UI | Viewer→Staff may issue new Login ID/PIN; Staff→Viewer revokes sessions and blocks sign-in while preserving record/history. |
| Email reset | accounts URLs/views/serializers, `App.tsx`, auth service, settings and schema | Removed by approved AUTH-RESET task. Current docs/OpenAPI and unused frontend translation/CSS residue were reconciled locally; historical records remain labeled as such. |

## 7. Migration and generated-artifact map

### Dirty migrations

| Migration | Dependency / operations | Data and reversibility | Release risk / coupling |
|---|---|---|---|
| `apps/accounts/migrations/0006_authattemptbucket_shopadminpinresetrequest_and_more.py` | Depends on `accounts.0005_user_shop_ownership`, `auth.0012`, `tenants.0009_membership_work_functions`; creates AuthAttemptBucket and ShopAdminPinResetRequest, adds nullable Login ID and database constraints. | Schema-only; Django operations are reversible. Does not rewrite existing password hashes. | Must ship with accounts models, reset/abuse services, Login ID and API/frontend contracts. |
| `apps/accounts/migrations/0007_account_login_eligibility.py` | Depends on accounts 0006; adds `User.login_enabled` and data migration for Viewer-only accounts. | Reversible Python migration; reverse restores Viewer eligibility before field removal. Forward preserves users/password hashes/history. | Must ship with backend login/JWT/refresh gates and role-transition tests. |
| `apps/catalog/migrations/0017_measurement_version_deactivation_design_retry.py` | Depends catalog 0016, tenants 0009 and swappable User; adds MeasurementSet `is_active`, Design `client_request_id`, tenant+request uniqueness. | Schema-only and reversible. | Required for measurement deactivation and idempotent Design create. |
| `apps/catalog/migrations/0018_seed_remaining_family_design_defaults.py` | Depends catalog 0017; seeds global style-only Design presets. | Data migration with guarded reverse: deletes only exact deterministic seeds that still match; raises `IrreversibleError` if edited/extra selections detected. No body sizes/ease are seeded. | Must travel with research note and migration safety tests; production data must not be treated as disposable. |
| `apps/catalog/migrations/0019_shop_owned_garment_systems.py` | Depends catalog 0018, tenants 0009 and swappable User; adds per-family option policy, nullable Shop owners for families/groups, MeasurementSet DesignVersion FK; makes Design.variant nullable and changes code lengths/constraints. | Schema-only, reversible operations; existing global rows remain global. | Must travel with models, same-Shop services/API validation, frontend and generated schema. |

Static dependency order is `accounts.0006 → accounts.0007` and `catalog.0017 → catalog.0018 → catalog.0019`; tenant dependency is `tenants.0009`. **INITIAL FINDING:** the original audit could not load the runtime graph with system Python because `arabic_reshaper` was missing. **RESOLVED LOCALLY by `PRE-PUSH-MIGRATION-INTEGRITY-02`:** the project `.venv` loaded the 65-node graph without conflict/cycle; fresh and published-baseline PostgreSQL replays, drift check and targeted regression passed. This is local migration-integrity evidence, not an exact-candidate release sign-off.

`schema.yml` and `docs/schema.yml` are byte-for-byte identical (SHA-256 `89317C126F28AC1332BF9CF62F78BE4E831B97232B4D184EA2AD3D4CB6761105`). They were regenerated together from the Django OpenAPI metadata and validated with `--validate`: 0 schema errors, 29 warnings (13 unique). This matches the previously recorded warning count; no new warnings were observed. The reset-credentials description now says active same-Shop STAFF only for Shop Admin resets. No removed email-reset routes are present, and Login docs explicitly retain legacy-password + PIN compatibility.

## 8. Frontend and test map

- **Login/Back Office/Team:** `frontend/src/App.tsx`, `App.test.tsx`, `backoffice/BackOfficePages.tsx`, `BackOffice.test.tsx`, `features/users/{ConfirmActionModal,MemberActionsMenu,UserForm,UsersPage}.tsx`, their tests/API/types/styles, `PinResetPage.tsx`, `PinResetRequestsPage.tsx`, `services/pinReset.ts`. User-visible: PIN reset navigation/review, Login ID creation, one-time PIN display, Viewer no-credential state. The shared Login field remains compatible with legacy long passwords and PINs. API contract changed; navigation adds PIN review route. No broad login layout redesign is intended. The dead email-reset CSS/strings identified initially were removed locally; see section 11.
- **Catalog/Design:** `features/catalog/CatalogPage.tsx`, CSS, API/types/tests and `features/designs/DesignsPage.tsx`, API tests/types. User-visible: Shop family/group configuration, selection rules and family-level Design. Paired to catalog APIs/migrations/schema.
- **Measurements/history:** `features/measurements/ClientMeasurementsPage.tsx`, `MeasurementEntryForm.tsx`, `StyleConfiguration.tsx`, API/types/CSS/tests; `features/clients/ClientMeasurementHistory.tsx`, its tests and `client-workspace.css`. User-visible: inch default plus per-field override/keyboard, custom measurement/design save, version history/deactivation/copy/export, structured responsive client workspace. Historical data remains immutable; version deactivation is soft/recoverable.
- **Client search/detail:** `features/clients/ClientsPage.tsx`, `Clients.test.tsx`, `ClientDetailPage.tsx`; debounce/stale-response behavior and structured client detail. API pagination/authorization remain server-owned.
- **Shared request/auth:** `services/apiClient.ts`, `apiClient.test.ts`, `services/auth.ts`, `auth.test.ts`, `App.css`, `i18n.ts`, `index.css`; shared response validation/session bootstrap and global visual classes. Unreferenced email-reset remnants in `App.css`/`i18n.ts` were removed locally; active Login/PIN-reset presentation and strings remain.
- **Tests:** Modified tests cover auth roles, login compatibility, tenant membership/creation, catalog isolation, design idempotency, measurement history/deletion/units, UI navigation, request staleness and settings. New tests cover abuse/races, PIN review UI, migration reverse safety, production settings and client history. These are required in the coupled groups, not optional cleanup.

### Test/verification evidence and limits

- Task notes report 78 targeted backend account/reset/tenant tests passed, with the updated Viewer access-token denial test rerun separately; frontend focused suite 29 passed; TypeScript typecheck and build passed; staging settings suite 20 passed; Django check and migration drift check passed.
- OPT-02 records a clean disposable-PostgreSQL full backend run of 470/470 and frontend 142/142 plus typecheck/build. FRONTEND reconciliation records 166/166 on that task snapshot. These are previous task records, not reruns on this exact audit-created state.
- **INITIAL FINDING:** OpenAPI validation had zero schema errors and existing warnings, but the reset-role description drifted in both schema copies. **RESOLVED LOCALLY by `AUTH-DOCS-OPENAPI-RECONCILIATION-01`:** both copies were regenerated and matched byte-for-byte; validation reported 0 errors, 29 warnings (13 unique), matching the previous warning baseline. Removed email-reset routes are absent. The existing `--fail-on-warn` warning baseline is separate from the corrected reset-role text.
- The original audit's system-Python `showmigrations` attempt failed because that interpreter lacked `arabic_reshaper`. `PRE-PUSH-MIGRATION-INTEGRITY-02` resolved the environment issue without dependency-file changes: `.venv` Python 3.12.10, Django 5.1.4, and declared `arabic-reshaper==3.0.1`.
- Current targeted verification: runtime graph 65 nodes, no conflicts/cycles; `showmigrations` all applied; `manage.py check` passes on both disposable DBs; `makemigrations --check --dry-run` reports no changes. PostgreSQL 15.4 fresh zero→current and published baseline (`accounts.0005`, `catalog.0016`, `tenants.0009`)→current upgrade both pass. Legacy user hashes/codes, memberships, Viewer-attributed measurement history, and a same-name Design were preserved. `accounts.0007` reverse/reapply and `catalog.0018` safe/guarded reverse passed; critical uniqueness constraints were present and enforced. Focused migration tests: 4 passed. `git diff --check` passed; only existing CRLF normalization warnings were printed.

## 9. Temporary, ignored and suspicious artifacts

Relevant ignored local-only files are listed exactly in section 3B. `.env`, `.env.prod`, `.env.test`, `cloudflare.env`, and `frontend/.env.local` are treated as secret-bearing local configuration and were not opened; `.coverage` files and `frontend/dist/` are generated; the three `.log` files are local runtime/test logs. None belongs in a Git commit.

**INITIAL SNAPSHOT:** 33 untracked paths in the main worktree were source/migration/test/docs files rather than scratch output. **CURRENT STATUS:** 35 untracked paths, including this audit document; 108 tracked modified and 0 staged, for 143 main dirty paths. No untracked `.env`, log, database, build, cache, or credential dump appeared in the original `git status --untracked-files=all` inspection; ignored secret-bearing files were not opened. The generated OpenAPI pair was regenerated and validated locally after the contract-text correction.

## 10. Separate non-main worktree — excluded from this manifest

**WORKTREE ISOLATION BLOCKER: RESOLVED** — re-verified 2026-10-09. `git worktree list --porcelain` confirmed two distinct worktree directories and branches. At that check, primary `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp` (`main`, HEAD `d6560c7c5457df11820686c6b6f3f204338c530a`) had 144 dirty paths (109 modified, 35 untracked, 0 staged). **Current main count:** 143 paths (108 modified, 35 untracked, 0 staged) after the frontend CSS cleanup. Secondary `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp-frontend` (`frontend/parallel-foundation`, HEAD `9ff32bc30d94744cfa0c432e4bb1c57d4182a20c`) had 64 dirty paths (47 modified, 17 untracked, 0 staged) at the isolation check; it is excluded from main totals.

The branch merge-base equals the secondary HEAD; the secondary HEAD is an ancestor of `main`, and there are no secondary-only commits. The main index has no staged paths; no pending merge, cherry-pick, or rebase state exists on main. This confirms the main dirty inventory is its own worktree state: Git does not implicitly stage or copy the secondary worktree's uncommitted files. No secondary-only dirty module is imported by the current main source; previously recorded main typecheck/build evidence remains applicable, so no build or full suite was rerun for this isolation-only task.

Secondary dirty-path classification (every one of the 64 paths below is assigned exactly once):

**A. Already reconciled into main — 53 paths.** The following 23 are byte-identical to their current main counterparts:

```text
frontend/.env.example
frontend/ACCESSIBILITY.md
frontend/src/backoffice/ShopListPage.test.tsx
frontend/src/components/CustomSelect.css
frontend/src/components/CustomSelect.tsx
frontend/src/components/CustomSelect.test.tsx
frontend/src/components/DialogKeyboardManager.test.tsx
frontend/src/components/DialogKeyboardManager.tsx
frontend/src/features/catalog/VariantsPanel.test.tsx
frontend/src/features/catalog/VariantsPanel.tsx
frontend/src/features/clients/ClientForm.tsx
frontend/src/features/clients/ConfirmDeleteModal.tsx
frontend/src/features/materials/MaterialsInventoryPage.test.tsx
frontend/src/features/measurements/PrivateReferenceImage.test.tsx
frontend/src/features/measurements/PrivateReferenceImage.tsx
frontend/src/features/users/WorkFunctionsModal.tsx
frontend/src/hooks/useArrowKeyGrid.test.tsx
frontend/src/hooks/useArrowKeyGrid.ts
frontend/src/hooks/useCurrentShop.test.tsx
frontend/src/hooks/usePrivateImage.test.tsx
frontend/src/hooks/usePrivateImage.ts
frontend/src/services/privateMediaUpload.test.ts
frontend/src/services/privateMediaUpload.ts
```

The other 30 have different bytes but their current behavior is represented by the later/current main implementation:

```text
frontend/src/backoffice/BackOfficePages.tsx
frontend/src/backoffice/catalog/GlobalCatalogPage.test.tsx
frontend/src/backoffice/catalog/GlobalCatalogPage.tsx
frontend/src/features/catalog/Catalog.css
frontend/src/features/catalog/CatalogPage.test.tsx
frontend/src/features/catalog/CatalogPage.tsx
frontend/src/features/catalog/api.test.ts
frontend/src/features/catalog/api.ts
frontend/src/features/clients/ClientDetailPage.tsx
frontend/src/features/clients/Clients.test.tsx
frontend/src/features/clients/ClientsPage.tsx
frontend/src/features/clients/clients.css
frontend/src/features/designs/api.test.ts
frontend/src/features/materials/MaterialsInventoryPage.tsx
frontend/src/features/measurements/ClientMeasurementsPage.test.tsx
frontend/src/features/measurements/ClientMeasurementsPage.tsx
frontend/src/features/measurements/MeasurementEntryForm.test.tsx
frontend/src/features/measurements/MeasurementEntryForm.tsx
frontend/src/features/measurements/Measurements.css
frontend/src/features/measurements/StyleConfiguration.tsx
frontend/src/features/users/ConfirmActionModal.tsx
frontend/src/features/users/MemberActionsMenu.tsx
frontend/src/features/users/UserForm.tsx
frontend/src/features/users/Users.test.tsx
frontend/src/features/users/UsersPage.tsx
frontend/src/features/users/users.css
frontend/src/hooks/useCurrentShop.ts
frontend/src/index.css
frontend/src/services/apiClient.test.ts
frontend/src/services/apiClient.ts
```

Evidence includes main's debounced/stale-safe Clients and Users searches; current catalog, client workspace, measurement/design, Materials, keyboard-dialog/grid, private image/upload, and shop-context implementations/tests. For example, main `useCurrentShop` guards responses by user identity and clears stale/error/empty-shop state; main Client Detail imports its feature styles directly and includes the current embedded measurement/history workflow. The secondary README is documentation-only and is not needed to run the main candidate.

**B. Superseded by later main implementation — 8 paths.** These contain or route to the old email self-service password-reset flow. Current policy removes that flow in favor of phone-request → Back Office Shop Admin recovery; do not import these files or reintroduce email reset:

```text
frontend/src/App.tsx
frontend/src/features/auth/PasswordResetPage.test.tsx
frontend/src/features/auth/PasswordResetPage.tsx
frontend/src/features/auth/password-reset.css
frontend/src/services/AuthContext.tsx
frontend/src/services/auth-context.ts
frontend/src/services/auth.test.ts
frontend/src/services/auth.ts
```

**C. Secondary-only / not required for the current main candidate — 2 paths.** `frontend/README.md` is a worktree-specific documentation revision; `frontend/src/shared-ui.css` is not imported by main, whose current feature/app styles provide the needed presentation. Neither is evidence of a missing approved runtime feature.

**E. Historical / stale — 1 path.** `frontend/UI_STABILITY_HANDOFF.md` is a historical local handoff/validation record, not a runtime dependency. Its client stylesheet/deep-link and layout outcomes are represented in current main code; its uncommitted report itself is not required.

**D. Possible missing approved feature — 0 paths. F. Unknown — 0 paths.** No approved critical feature was found missing from main solely because it exists in the secondary worktree. Secondary import required: **NO**. Main has no runtime/build dependency on secondary dirty state. The secondary worktree can remain untouched for future reference/recovery, and the future main manifest must exclude all secondary-only paths. No merge, copy, checkout-across-worktrees, cherry-pick, rebase, reset, stash, clean, stage, commit, push, deploy, or secondary-worktree modification occurred. Global `PUSH_READY = NO` remains unchanged; unrelated release blockers remain.

Exact dirty paths observed there (relative to that worktree):

```text
M frontend/.env.example
M frontend/README.md
M frontend/src/App.tsx
M frontend/src/backoffice/BackOfficePages.tsx
M frontend/src/backoffice/catalog/GlobalCatalogPage.test.tsx
M frontend/src/backoffice/catalog/GlobalCatalogPage.tsx
M frontend/src/components/CustomSelect.css
M frontend/src/components/CustomSelect.tsx
M frontend/src/features/catalog/Catalog.css
M frontend/src/features/catalog/CatalogPage.test.tsx
M frontend/src/features/catalog/CatalogPage.tsx
M frontend/src/features/catalog/VariantsPanel.test.tsx
M frontend/src/features/catalog/VariantsPanel.tsx
M frontend/src/features/catalog/api.test.ts
M frontend/src/features/catalog/api.ts
M frontend/src/features/clients/ClientDetailPage.tsx
M frontend/src/features/clients/ClientForm.tsx
M frontend/src/features/clients/Clients.test.tsx
M frontend/src/features/clients/ClientsPage.tsx
M frontend/src/features/clients/ConfirmDeleteModal.tsx
M frontend/src/features/clients/clients.css
M frontend/src/features/designs/api.test.ts
M frontend/src/features/materials/MaterialsInventoryPage.tsx
M frontend/src/features/measurements/ClientMeasurementsPage.test.tsx
M frontend/src/features/measurements/ClientMeasurementsPage.tsx
M frontend/src/features/measurements/MeasurementEntryForm.test.tsx
M frontend/src/features/measurements/MeasurementEntryForm.tsx
M frontend/src/features/measurements/Measurements.css
M frontend/src/features/measurements/PrivateReferenceImage.tsx
M frontend/src/features/measurements/StyleConfiguration.tsx
M frontend/src/features/users/ConfirmActionModal.tsx
M frontend/src/features/users/MemberActionsMenu.tsx
M frontend/src/features/users/UserForm.tsx
M frontend/src/features/users/Users.test.tsx
M frontend/src/features/users/UsersPage.tsx
M frontend/src/features/users/WorkFunctionsModal.tsx
M frontend/src/features/users/users.css
M frontend/src/hooks/useCurrentShop.ts
M frontend/src/hooks/usePrivateImage.ts
M frontend/src/index.css
M frontend/src/services/AuthContext.tsx
M frontend/src/services/apiClient.test.ts
M frontend/src/services/apiClient.ts
M frontend/src/services/auth-context.ts
M frontend/src/services/auth.test.ts
M frontend/src/services/auth.ts
M frontend/src/services/privateMediaUpload.ts
?? frontend/ACCESSIBILITY.md
?? frontend/UI_STABILITY_HANDOFF.md
?? frontend/src/backoffice/ShopListPage.test.tsx
?? frontend/src/components/CustomSelect.test.tsx
?? frontend/src/components/DialogKeyboardManager.test.tsx
?? frontend/src/components/DialogKeyboardManager.tsx
?? frontend/src/features/auth/PasswordResetPage.test.tsx
?? frontend/src/features/auth/PasswordResetPage.tsx
?? frontend/src/features/auth/password-reset.css
?? frontend/src/features/materials/MaterialsInventoryPage.test.tsx
?? frontend/src/features/measurements/PrivateReferenceImage.test.tsx
?? frontend/src/hooks/useArrowKeyGrid.test.tsx
?? frontend/src/hooks/useArrowKeyGrid.ts
?? frontend/src/hooks/useCurrentShop.test.tsx
?? frontend/src/hooks/usePrivateImage.test.tsx
?? frontend/src/services/privateMediaUpload.test.ts
?? frontend/src/shared-ui.css
```

## 11. Conflict / drift findings

1. **Auth docs vs code — RESOLVED:** current-rule documents now match the approved email-reset removal, legacy-password + PIN compatibility, Shop Admin active same-Shop STAFF-only reset, Back Office approval recovery and Viewer no-login policy. Historical records are preserved and annotated.
2. **Plan history vs current policy — RESOLVED:** both frontend task records now prominently state that email-reset/Viewer auth scope is superseded while retaining their historical implementation records and non-auth outcomes.
3. **Backend metadata vs OpenAPI — RESOLVED:** the `reset_credentials` source description now limits Shop Admin reset to active same-Shop STAFF; the Login operation description documents Login ID/legacy aliases and legacy-password + PIN compatibility. The project's `.venv` generator regenerated both schema copies; they are byte-identical and validation reports 0 schema errors, 29 warnings (13 unique), matching the previously recorded baseline. Removed email-reset routes are absent from the schema.
4. **Model vs migration — RESOLVED for this blocker:** project `.venv` `makemigrations --check --dry-run` reports no changes; Django checks pass. This is targeted validation, not a global release sign-off.
5. **Frontend residue — RESOLVED locally (not yet published):** no current frontend consumer existed for `.password-reset-links`, `.password-reset-success`, or the `authReset` translation namespace. The stale CSS and locale dictionaries were removed; current Login/PIN-reset flows remain. Frontend-wide residue search, typecheck, focused App/PIN-reset/auth tests (21 tests), and production build pass.
6. **Migration graph / replay — RESOLVED for this blocker:** Django runtime graph has 65 nodes, no conflicts/cycles. PostgreSQL 15.4 fresh and published-baseline upgrade replays pass, including legacy-data and critical-constraint assertions. A rollback defect in `accounts.0007` was found and fixed: PostgreSQL's deferred `accounts.0005` ownership trigger is flushed before the reverse migration drops `login_enabled`. Regression coverage is in `apps/accounts/tests/test_account_login_eligibility_migration.py`; guarded `catalog.0018` reverse behavior also passes its focused tests. These files remain uncommitted and were tested only on disposable local databases.
7. **No deletion/secret finding:** no tracked deletions and no staged files. The ignored environment files remain local and were not inspected or printed.

## 12. Local `main` — current source of truth

- `HEAD`/`origin/main` is `d6560c7c5457df11820686c6b6f3f204338c530a`. The dirty tracked/untracked files listed here are newer local work and are not in that commit. No network fetch was made, so this is local-ref parity, not a live remote freshness claim.
- For auth implementation, local code of record is `apps/accounts/models/users.py`, `identity.py`, `security.py`, `backends.py`, `authentication.py`, `serializers/__init__.py`, account services/views/URLs, tenant membership/account services/views, and PIN frontend pages/services. Migrations 0006 and 0007 are required. `docs/task-plans/AUTH-RESET-MODEL-CORRECTION-01.md` and current auth documentation reflect the approved policy. Both schema artifacts were regenerated, byte-matched and validated locally (0 errors; 29 existing warnings, 13 unique).
- For custom garment systems, local code of record is `apps/catalog/models.py`, serializers/services/views/URLs, measurement modules and migrations 0017–0019. `docs/API.md` and `docs/ARCHITECTURE.md` describe the contract; generated schema copies are reconciled locally and must travel with the API/code candidate.
- `docs/OPT_01_BASELINE.md` and `docs/OPT_02_RESULT.md` are dated evidence. They do not authorize a main push, staging deploy, production creation, or DigitalOcean cutover.
- No path is currently staged or intentionally left staged. This audit file is an added record, not product code.

## 13. Commit grouping recommendation (do not commit in this task)

1. Auth/Login ID/PIN/recovery as one cohesive group, including both account migrations, tenant role transitions, Back Office/Team/Login UI, all focused tests, schema and corrected docs.
2. Measurement history/version lifecycle and catalog request idempotency: migration 0017, model/service/view/API/frontend/tests/OpenAPI.
3. Style-only global defaults: migration 0018, `docs/MEASUREMENT_DESIGN_RESEARCH.md`, migration safety and catalog tests; depends on group 2.
4. Shop-owned garment systems: migration 0019 and all model/serializer/service/view/frontend/test/schema/docs files; depends on catalog 0018.
5. Client workspace/search/UI changes and helper/tests; can be a separate frontend group only after checking shared measurement/catalog contracts.
6. OPT-02 production settings test isolation/config hardening and dated evidence; keep distinct from any provider provisioning or deployment.
7. A separate documentation commit may be appropriate; the auth behavior is already reflected consistently across the active docs and both generated schema copies locally. Keep the documentation paired with the reviewed API/code candidate.

Do not split a migration from its model/service/API tests; do not split the generated OpenAPI copies; do not include any `sgtp-frontend` worktree change in a `main` commit.

## 14. Final status

**Push-readiness classification:** C. **NOT READY — FIX / VALIDATION REQUIRED.**  
**PUSH_READY = NO.**  
**All currently approved local project changes safely commit/push to `main` now? NO.**

No staging, commit, push, deploy, migration, clean, reset, stash, restore, deletion, rename, or file move was performed.
