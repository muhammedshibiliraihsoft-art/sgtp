# OPT-01 — local baseline and release preflight (2026-10-07)

Scope: evidence collection and phased plan only. No application behavior change, commit, push, cloud provisioning, business-data write or deployment. This is **not** a production-readiness sign-off.

## Repository and checks

- Checkout: `main`; HEAD and `origin/main` both `db67725e47b21ef8033f46fb7cecf5a4d600d1a2` at inspection. The candidate work is dirty/unpublished: 47 tracked modified paths and 9 untracked paths before this report. Three untracked catalog migrations are `0017`–`0019`. No deployable exact SHA represents them.
- Backend: 468 collected on a disposable local PostgreSQL test database, external R2 variables explicitly empty; **467 passed, 1 failed**. The isolated failing test is `core/tests/test_settings.py::test_prod_settings_security_flags`. It sets fake R2 environment values, but `backend.config.settings.base` is imported at test-module import time and remains cached, so its `R2_ENABLED` does not update when `prod` is re-imported. Production's fail-closed R2 requirement is intentional. Repair test isolation; do not remove the guard. The full suite is not green.
- Local Django `check` passed; `makemigrations --check --dry-run` reported no changes. The three new migrations were exercised only in the disposable test database; no staging/production migration was run.
- Frontend: 142/142 tests across 30 files, typecheck and production build passed. Lint exited 0 with existing `react(set-state-in-effect)` warnings. Authenticated browser flows, weak-network/low-end-phone timings and R2 media delivery were **not** verified.
- Build artifact observations only: initial `index` JS ~390 KB (~120 KB gzip); Measurement route JS ~46 KB (~12 KB gzip); login image files ~1.6–1.8 MB each. These are file sizes, not measured transfer payload or a proven user experience. Do not infer that every image loads on each visit.
- `git diff --check` and `python scripts/verify_project_state.py` passed; validator discovered 468 backend tests and reported a dirty worktree with local/remote HEAD parity. Passing repository-state validation does not override the failed backend test.

## Confirmed preflight risks / decisions

1. **Blocking before candidate publication:** fix the stale settings-import test and rerun the complete backend suite. Review all uncommitted/untracked changes and migrations, then form an exact candidate commit and verify CI for that SHA. Do not call the old remote HEAD the new release.
2. **Potential unintended staging change:** `render.yaml` has `autoDeployTrigger: "commit"` and the entrypoint runs migrations. The live Render auto-deploy setting has not been verified. A `main` push is not a harmless file upload; verify the live trigger and staging R2/secrets before publishing.
3. **Performance candidates, not measured regressions:** private image completion downloads/processes media inside a database transaction; the API client and direct-upload XHR have no explicit request timeout. Inspect and measure in a separate confirmed task before changing contracts. Existing route splitting, pagination and image placeholders should be preserved.
4. **Production operations decision required:** existing docs assume managed PostgreSQL with provider backups/PITR, while the proposed DigitalOcean basic Droplet would self-host PostgreSQL. The backup frequency, restore test, RPO/RTO, off-host encrypted R2 backup, monitoring and ownership must be decided before production. R2 stores media; it is not automatically a PostgreSQL backup.
5. **Scope boundary:** application is incomplete V1. A temporarily available client demo must be called a staging/demo environment, not accepted production. Host size and monthly cost must be checked against current provider pricing and usage before purchase; no capacity or bill is guaranteed by this report.

## Task sequence (each requires separate confirmation)

1. **OPT-02 — Safe baseline remediation:** fix test isolation, rerun all checks, inspect migration/data safety and exact deployment trigger. No unrelated workflow redesign.
2. **OPT-03 — Targeted performance/failure hardening:** measure authenticated critical paths and image handling; address verified timeout, duplicate-request, transaction and media bottlenecks with regression tests. Preserve existing UX and contracts.
3. **OPT-04 — Demo/release candidate:** review dirty tree, exact-SHA CI, staging smoke, low-end/mobile checks, image failure/retry and security/isolation; publish only after push/deploy effects are understood. Use an honestly labelled demo/staging environment.
4. **OPT-05 — DigitalOcean production setup, last:** after the preceding gates and business/operations choices, follow current DigitalOcean documentation to provision minimum viable expandable compute, isolated PostgreSQL, TLS/proxy, secrets, R2 media, off-host database backup and tested restore, health/monitoring, deployment/rollback. Perform the final live cutover only with explicit authorization and an accepted production candidate. No $6/$7 host size is hard-coded in application architecture.

OPT-01 ends with the baseline above. It does **not** authorize OPT-02, DigitalOcean purchase or production deployment.
