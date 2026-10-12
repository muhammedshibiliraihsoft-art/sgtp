# LOCAL-TO-STAGING-SYNC-01

**Status:** In progress locally; release candidate worktree prepared. No push, deploy, staging account creation, or staging database write performed.
**Target:** Existing Render staging environment (`birky-staging-api` + `birky-staging-db`); Production and the local `devdb` are out of scope.
**Goal:** Move the verified local application state to staging, preserve useful staging data, then create and verify the requested Main Supplier Admin account for Back Office and Django Admin access.

## User intent and boundaries

- Bring the features currently working locally to a stable staging release.
- Reuse the existing staging resources if they are safe and suitable; do not create a parallel stack without a demonstrated need.
- Preserve useful staging data. The user allows a reset of staging-only data if specific existing rows block the release. Identify the exact conflict and recovery path before any reset; do not use `flush` as a shortcut.
- Never alter the local `devdb` or Production.
- Do not put passwords, PINs, tokens, connection strings, or other secrets in Git, this plan, terminal output, or logs.
- The supplied account details are for a Main Supplier Admin identity. Use the user-provided identity values only through the guarded staging bootstrap, not as committed fixture data. Require a PIN change at first login.

## Current known state and risks

- The source repository working tree contains a broad set of modified and untracked backend, frontend, migration, deployment, and documentation files. A separate `codex/local-to-staging-sync-01` worktree was created from `origin/staging`, and a reviewed application/documentation subset was copied there. The source checkout remains untouched except for three focused test repairs and this plan.
- A separate frontend worktree exists with a different UI snapshot. The two frontend snapshots have different tests and contents. Reconcile the intended frontend source deliberately; do not copy or merge the sibling worktree wholesale.
- The default local Django system check passes. The backend suite passes 546/546 against an isolated PostgreSQL cluster; three pre-existing test failures were repaired. The frontend candidate passes 189/189 tests, build, and lint (warnings only). The staging-settings check still needs a complete non-secret test configuration or the deployment environment.
- Backend PostgreSQL tests and migration checks used the disposable `staging_sync_test` cluster on port 55432, never `devdb`. A staging-branch migration baseline and then local catalog migrations 0017–0023 both applied successfully there; Django migration drift reports no changes.
- Prior staging inspection found the database is a Free PostgreSQL instance without a backup facility. A blind `flush` is particularly unsafe: seeded catalogue/default records are inserted by migrations, and those seed migrations would not rerun after flush because the migration ledger remains.
- Live Render inspection confirms the staging API and database, but no staging frontend service. This frontend requires its same-origin `/api/*` Cloudflare Pages Function, so a Render Static Site alone would not run the current authentication flow. Use the repository's Cloudflare Pages architecture for staging; verify its actual branch, project, generated hostname, and runtime bindings before publishing. If Cloudflare Pages access is unavailable, keep frontend deployment as an explicit blocker rather than claiming that an API-only deployment is complete.
- Live Render inspection confirms `birky-staging-api` tracks the `staging` branch with commit-triggered auto-deploy; current live SHA is `e1a4aafe85308b96d329d963c91e4ccac17a9c26`. Pushing the candidate branch does not target this service, but merging into `staging` does.
- Render's read-only SQL connector could not reach the staging database because of external TLS/IP allow-list restrictions. The staging migration ledger and data contents remain unverified.

## Execution plan

### 1. Freeze and inventory the candidate

1. Record current branch/SHA, `git status`, and the full changed-file inventory.
2. Preserve every existing change. Make a file-level audit and classify each change as required for this staging release, unrelated follow-up, generated/local-only, or secret-bearing.
3. Inspect migrations and deployment/configuration changes independently. Confirm `.env*`, local database files, private assets, and credentials are excluded from any release.
4. Resolve the canonical frontend snapshot by reviewing the main checkout and existing project rules; do not merge the second worktree wholesale.
5. Produce a bounded staging candidate from the verified changes only. Keep the current main checkout recoverable and do not use destructive Git commands.

**Gate:** No candidate is published until the changed-file inventory is reviewed and secrets/local-only files are confirmed absent.

### 2. Validate backend and frontend without touching shared data

1. Run Python formatting/lint, Django checks, repository validators, and the backend test suite using an isolated disposable PostgreSQL test database.
2. Run migration consistency checks and inspect each migration's forward/reverse behavior and data impact. Test the migration sequence against a disposable database initialized from the known starting schema; do not point tests at `devdb` or staging.
3. Run frontend tests, typecheck, lint, and production build on the selected frontend snapshot.
4. Run the exact-SHA CI/project-state validation required by the repository.
5. Validate staging settings using a safe, non-secret test configuration or the deployment environment, without printing or extracting Render secrets.

**Gate:** All release-blocking checks pass for the exact candidate SHA, or any exception is documented and explicitly accepted before deployment. A default-settings check alone is not staging validation.

### 3. Prepare staging deployment and data protection

1. Reconfirm Render workspace, exact service/database IDs, staging branch, current live SHA, auto-deploy behavior, environment isolation, and that no Production resource is targeted.
2. Establish a verified recoverable backup/export of the existing staging database before any schema/data write. If the current Free plan cannot provide a backup, stop before migration and present the exact recovery limitation and options. Any optional staging-only reset must name the affected rows and preserve seeded defaults or explicitly rebuild them.
3. Review current staging schema/migration ledger read-only. Check for migration drift and expected seed/default rows without exposing personal data.
4. Configure the staging Cloudflare Pages frontend with the existing same-origin API Function, staging `API_ORIGIN`, and its exact `FRONTEND_ORIGIN`. Add only that verified HTTPS origin to API CORS/CSRF allow-lists. The current staging settings hardcode an unowned custom domain; make the smallest settings change needed for the actual provider hostname and test the guardrails.
5. Set only required staging secrets/configuration through Render's secret environment settings. Never reuse local or Production secret keys, database credentials, or object-storage credentials.

**Gate:** Confirm recovery exists and the release targets only staging before applying migrations or changing service settings.

### 4. Publish and deploy the release candidate

1. Publish the reviewed candidate through a dedicated release branch/PR targeting the configured staging branch; never force-push or include unrelated dirty files.
2. Confirm CI passes for the exact commit and inspect the Render deployment preview/source SHA.
3. Deploy only after confirming the actual auto-deploy setting and target service. If deployment is automatic, the verified merge is the trigger; do not trigger a duplicate manual deploy.
4. Apply migrations once through the documented staging startup/deploy path. Watch migration and startup logs for errors while ensuring logs do not reveal secrets.
5. Verify readiness/liveness, static assets, API host/CORS/CSRF behavior, and frontend-to-API connectivity.

**Stop conditions:** Failed CI, unexpected migration plan, unverified backup, wrong branch/SHA, unexpected paid resource, any Production target, or any data-clearing operation.

### 5. Create and verify the requested account

1. Confirm the deployed code includes the guarded one-time `bootstrap_staging_main_admin` command and its required staging-only safeguards.
2. Check for exact identity collisions using non-sensitive identifiers; do not modify or reset a different existing account.
3. Supply the user-provided account fields and temporary PIN through a protected, non-logged bootstrap invocation. Do not save credentials in source, command history, fixtures, or task documents.
4. Verify the command created only the intended Main Supplier Admin and set the required first-login PIN-change state.
5. Perform staging-only smoke tests for sign-in, Back Office access, Django Admin access, and logout/session behavior. Avoid real customer data; use synthetic records for functional checks.
6. Ask the user to change the temporary PIN on first login and report only the account creation/access result, never the credential.

## Completion criteria

- A reviewed, exact-SHA release candidate passes required backend, frontend, migration, and CI checks.
- Staging is deployed from that verified SHA; API and staging UI are reachable and healthy.
- Useful staging data is preserved; any targeted cleanup is documented and schema changes are covered by a verified recovery path.
- The requested Main Supplier Admin can sign in to both Back Office and Django Admin and is required to change the temporary PIN.
- No local `devdb` or Production changes, credential leaks, unreviewed branch merges, or broad database resets occurred.
- Final handoff records the deployed SHA, Render deploy ID, migration outcome, smoke-test evidence, and any remaining limitations without sensitive values.

## Explicitly not part of this plan

- Broad or unverified reset of staging database rows or accounts.
- Copying local database contents to staging.
- Modifying Production or changing Production credentials.
- Creating a new Render database/API stack unless the existing staging resources fail the suitability checks and the user approves the alternative.
- Treating local UI + staging API as a finished staging deployment.
