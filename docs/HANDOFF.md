# Handoff

## Current phase

Phase 3 is ACTIVE; activation was explicitly confirmed with `CONFIRM PHASE 3`.

Completed foundation tasks: T3-01, T3-02, T3-02-REMEDIATION, T3-02A, T3-03, and T3-04. T3-04 is committed/pushed; verified `main`, `origin/main`, and remote `main` match; derive the current SHA from Git.
CI evidence: GitHub Actions Project State Validation succeeded for the published baseline (run #36511111586).

## Current task

T3-04A — implementation and local validation are complete. Task was explicitly confirmed. No commit or push has been made; there is no CI result for this diff.

## Current state and next gate

- T3-04A implements permanent generated `user_code`, optional email/phone for normal Users, required trimmed `first_name`, unified User ID/email/phone login, controlled Main Supplier credential reset, account contact safeguards, and global User hard-delete denial.
- UUID remains the internal database and JWT `user_id` identity. Existing membership and audit references are preserved. T3-04B/C and T3-05 behavior is not implemented.
- Approved ordinary-Shop visibility, Shop deactivation/no-delete, and max_users lower-bound rules are pending T3-05 implementation.
- Next candidate: T3-04B — membership/Admin invariants. It is not confirmed or authorized; do not begin automatically.

## Tests and checks

- Focused identity/authentication suite: 29 passed; T3-02A compatibility regressions: 10 passed. Full pytest suite: 167 passed (155 warnings) against the local PostgreSQL test database. One earlier run was interrupted by the stopped local PostgreSQL process; the existing service was restarted without resetting its data, and a clean complete rerun passed.
- Repository validator: PASS (167 tests discovered); validator tests: 14 passed. `manage.py check` and `DJANGO_ENV=prod manage.py check --deploy`: PASS; `makemigrations --check --dry-run`: no changes detected; OpenAPI validation: PASS; `git diff --check`: PASS.
- Read-only local PostgreSQL preflight found 0 Users, 0 superusers, and 0 Shops, with no unusable names, blank emails, or case-insensitive duplicate email groups. Then the normal local migration command applied T3-04A and its tenant prerequisites successfully. The migration regression test separately verifies preservation of representative legacy identity, password, membership, and audit references.
- Black and Flake8 pass for all six newly added Python modules. A broader Flake8 run over touched legacy files still reports style/unused-import findings, so whole touched-file lint is not clean. GitHub CI has not run for this local diff.
- T3-04A changes remain uncommitted and unpushed. No commit or push has been made.

## T3-REBASELINE-01 validation

- Repository validator: PASS (152 tests discovered; expected dirty-tree warning). Validator unit tests: 14 passed.
- `manage.py check`: PASS. `makemigrations --check --dry-run`: no changes detected; PostgreSQL at `127.0.0.1:5432` was unavailable, so migration-history consistency was not verified locally.
- Full pytest: 152 collected but not completed; database-backed setup errored because PostgreSQL was unavailable. Do not report a local full-suite pass. The published checkpoint's GitHub Actions validation succeeded; local PostgreSQL-backed full-suite execution remains unverified here.
- `git diff --check`: PASS. 52 Business Rule IDs checked, no duplicates; Phase 3 task sequence consistent across the development plan and playbook.
- Application code/migrations/dependencies/tests: unchanged. Documentation checkpoint committed and pushed; no deployment occurred.

## T3-04 verification record (historical task evidence)

- **Implemented:** `TenantScopedMixin` requires T3-03 authorized request context, checks actor/URL/compatibility alias, scopes reads, and assigns selected-Shop ownership on create/update. `IsTenantMember` now requires object-to-context Shop equality for members and Main Supplier.
- **Security:** missing context/configuration fails closed; URL, alias, and actor mismatches are non-disclosing 404s. Foreign direct IDs are excluded by scoped lookup. T3-03 uniform Shop-context 404 and authentication 401 behavior are preserved.
- **Database/API scope:** no production business models, API routes, migrations, or dependencies added. Test-only UUID/FK/soft-delete proof model validates the reusable boundary. At T3-04 completion, Tenant/member APIs were unchanged; later-approved visibility/deactivation rules are now recorded as target behavior for T3-04B/T3-05.
- **Validation:** 28 focused scope/context tests passed; full suite 152 passed (144 warnings); repository validator PASS (152 discovered); 14 validator tests passed; Django check PASS; migration check reports no changes; OpenAPI validation, Black, Flake8, and `git diff --check` PASS. T3-04 was subsequently pushed and its current CI evidence is stated above.
- **Next task at that historical point:** T3-05 was the proposed next task; the 2026-09-29 rebaseline supersedes that order with T3-04A–C prerequisites.
- **Known warning baseline:** Django tests emit existing test-key-length, local staticfiles, and DRF format-converter warnings; these are not T3-03 failures.

## T3-04 verification record

- T3-03 context/membership tests remain covered by the validation matrix. Focused T3-04 permission/scope plus T3-03 context tests: 28 passed.
- Full suite: 152 passed (144 warnings). Repository validator: PASS, 152 discovered, dirty-tree warning expected. Validator tests: 14 passed. Django system check: PASS. Migration drift: no changes. OpenAPI validation: PASS. Black and Flake8: PASS. `git diff --check`: PASS.
- No production schema/dependency changes or business modules. T3-05 remains not started and unauthorized.

### Historical: T3-02A verification record

- **Implemented:** optional unique E.164 User phone and compatible email/phone login; anonymous account creation denied; Main Supplier Admin account/phone administration; one-time random initial password with no-store response and forced first-login change; email password reset with generic response, expiry/single use, and refresh-session revocation; nullable user locale, `system|light|dark` appearance; nullable Shop locale/timezone/currency with Main Supplier Admin-only serialization; versioned JWT access/refresh revocation.
- **Database:** additive migrations `accounts.0003_alter_user_options_user_appearance_preference_and_more` and `tenants.0008_tenant_default_currency_tenant_default_locale_and_more`; UUID identity/memberships preserved; no fabricated phones or inferred Shop defaults.
- **Tests added/updated:** T3-02A account/auth/Shop settings regressions; existing account-creation tests aligned to the confirmed deny-anonymous/admin-create contract; auth lifecycle test cache is cleared between tests without changing runtime throttling; historical tenant migration test now uses historical models and restores the latest schema.
- **Files/areas:** accounts models/auth/serializers/views/URLs/settings/dependency and tests; tenant settings model/serializers/permissions/view/migration/tests; docs/API, ARCHITECTURE, DATABASE, SECURITY, Phase 3 plan, DEVELOPMENT_PLAN, PROJECT_STATE, HANDOFF, CHANGELOG, `.env.example`.
- **Validation:** final test/check results are recorded in the T3-02A verification section below.
- **Known limitations:** no front-end localization/theme UI, no Shop URL context or tenant isolation, no later-phase business modules. Shop defaults must not be read by ordinary users. Email reset delivery requires deployment email configuration and `PASSWORD_RESET_URL`.
- **Unresolved decisions at T3-02A completion (historical):** ordinary-user Shop read visibility and Shop deletion semantics were later resolved as target policy by the 2026-09-29 rebaseline. Shop Admin settings authority remains not granted; currency changes after financial history remain deferred.
- **Next task:** T3-03, but NOT AUTHORIZED; prepare its task plan and wait for exact `CONFIRM TASK T3-03`. Do not implement it automatically.
- **Git/CI:** T3-02A is complete. Commit is on `origin/main`. CI is green (GitHub Actions Project State Validation Run #17 SUCCESS).

### T3-02A verification record

Final verification outcomes are recorded in the `Tests and checks` section below.

## Historical tests and checks — T3-02A

- Application suite: 130 collected, 130 passed (`python -m pytest -q -p no:cacheprovider --no-cov`).
- Dedicated T3-02A module: 10 passed; the complete 130-test run also covers existing auth lifecycle, migration, and API error tests.
- Historical T3-02A validation: repository validator PASS; validator tests: 11 passed; detected 130 application tests and expected dirty working tree.
- `manage.py check`: PASS. `manage.py check --deploy` with `DJANGO_ENV=prod`: PASS. Default development `check --deploy`: exit 0 with six expected local dev security warnings (DEBUG, development secret, SSL redirect/HSTS, secure session/CSRF cookies).
- `manage.py makemigrations --check --dry-run`: PASS, no changes. Both T3-02A migrations are applied locally. API schema validation: PASS.
- Black check for new/rewritten account implementation: PASS. Black and Flake8 for `scripts/`: PASS. Flake8 for account implementation: PASS. `git diff --check`: PASS.
- GitHub Actions: the GitHub Actions workflow passed successfully for T3-02A.
- Git status: local working tree is clean. Branch `main` is up to date with `origin/main`.
- **Historical Changed areas:** User API authorization/serializer, Main Supplier Shop-write permission, membership serializer lifecycle protection, real throttle wiring/tests, duplicate CORS tests, production CORS environment propagation, CI validation, remediation regression tests, and documentation.
- **Validation:** remote CI is green: the latest GitHub Actions workflow passed successfully.
- **Historical next implementation candidate:** T3-03 was then unconfirmed; it has since been completed as recorded above.
- **Policies as of T3-03 completion (historical):** ordinary-user global Shop read visibility and Shop delete/archive/deactivate semantics were then unresolved; the 2026-09-29 rebaseline approved membership-authorized Shop visibility and deactivate/no-ordinary-DELETE. Shop Admin scoped settings authority remains not granted; currency changes after financial history remain deferred.
- **Agent Transition Note:** Upcoming engineering work may be executed through Codex; repository governance and explicit task-confirmation rules remain authoritative regardless of implementation agent.
## Repository state evidence
- Verify current HEAD with `git rev-parse HEAD`
- Verify remote parity with `git status -sb`
- Do not treat a stored commit hash in documentation as authoritative.

## Repository and workspace

- Project root: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp`
- `AGENTS.md`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\AGENTS.md`
- `docs/`: `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp\docs\`
- Remote: `https://github.com/muhammedshibiliraihsoft-art/sgtp.git`
- Historical Phase 1 corrective implementation was completed and published to `origin/main`.
- At the reviewed baseline, branch `main`, HEAD and `origin/main` matched; T3-02 remediation is committed and GitHub Actions was green. Recheck Git and CI after documentation updates; prior evidence does not validate this diff.
- Starter source files were modified for Phase 1.
- Existing SGTP `.git` metadata and history preserved.

## Target final product

SGTP is now defined as the Supplier-Centric Garment & Tailor Platform, with Tailor Management as the core V1 module. The hierarchy is Supplier/Main Admin -> Supplier Back Office -> isolated Shop workspaces -> Clients, Designs, Measurements, Fabric/Materials, Work, Billing, and Reports.

The required persisted flow is:

`Client Request -> Design -> Measurement -> Fabric/Material -> Cutting -> Stitching -> Check -> Finishing -> QC -> Completed -> Billing -> Reports/History`

The full product definition and Definition of Done are in `docs/PRODUCT_DEFINITION.md`.

## Locked V1 tenancy model

- V1 has exactly one top-level Supplier / Main Admin and no multi-supplier SaaS model.
- The hierarchy is Main Supplier / Main Admin → Supplier Back Office → multiple isolated Shops.
- Shop is the tenant/workspace boundary.
- External Supplier records are owned by exactly one Shop and are not users, tenants, members, roles, or authentication participants. They do not log in.
- External Supplier records are not global/shared; Shop isolation applies to all access and discovery paths.
- The starter `Tenant` model has been retained and structurally mapped as the V1 technical implementation for `Shop`. T3-01 verified this structural mapping was safe. A `Supplier` singleton model was created to enforce exactly one top-level platform owner.

## Inspection summary

The starter is a Django 5.1.4 / DRF 3.15.2 PostgreSQL project with Docker, devcontainer, JWT authentication, a custom email user, tenants, UUID/audit/soft-delete base models, OpenAPI/Swagger, and tests. It contains `core/`, `apps/accounts/`, `apps/tenants/`, `apps/common/`, templates, dependency/tooling files, Docker infrastructure, and editor configuration.

## Reusable

- Django project wiring and environment-loading pattern.
- Custom user model, user manager, admin, JWT endpoints, serializers, and initial tests.
- Tenant model/admin/API/migrations/tests as a starting point only.
- UUID, timestamps, audit fields, and soft-delete base model.
- PostgreSQL, Docker, devcontainer, Gunicorn, WhiteNoise, Makefile, and tooling setup.

## Phase 3+ Deferred Implementations

- `BaseModelWithTenant.tenant` remains nullable. T3-03 establishes request context and T3-04 provides reusable query/object isolation primitives; future concrete Shop-owned endpoints must adopt and verify those primitives.
- The starter is not yet the target product: Clients, Related Persons, Designs, Measurements, Materials, production stages, billing, reports/PDFs, frontend, persistent storage, workers, complete audit capture, monitoring, and end-to-end validation remain unimplemented. T3-03's pushed baseline passed GitHub Actions run #19. T3-04 is complete and published (current evidence is in the handoff header); T3-04A is implemented and validated locally but unpublished; T3-04B/C, T3-05, and later work remain unimplemented and individually gated.
- The target requires React/Vite/Tailwind, but the starter has only an empty `frontend/` placeholder. English/ar-KW/Bangla/Urdu localization, RTL/LTR, and Light/Dark/System are planned V1 requirements, not implemented.
- Tenant context is implemented as URL-path based (`/api/v1/shops/{shop_id}/...`); T3-04 primitives are available, and each future Shop-owned endpoint must apply them to queries and objects.
- Related Person billing ownership is approved as Primary Client ownership and must be implemented/tested in Phase 5.

## Historical Phase Status

Phase 1 and Phase 2 are complete. 
Historical Phase 3 task outcomes:
- **T3-01 Supplier and Shop Entities**: Complete. The repository has a reproducible database baseline, Shop mapping, and Supplier singleton constraint.
- **T3-02 User-Shop membership and roles**: Complete. `TenantMember` and `ShopRolePolicy` firmly establish user roles and Main Supplier cross-shop authority.

## T3-02 remediation status

- Ordinary users cannot enumerate or target other User records through the User API; self-profile updates remain supported.
- Shop write and activate/deactivate permissions now use `ShopRolePolicy.is_main_supplier_admin`, so `is_staff` alone is insufficient.
- Membership `is_active` is read-only in generic PATCH/PUT; lifecycle actions remain the only state-transition API.
- Real authentication throttling is verified by an integration-style repeated-login test; duplicate CORS tests are independently collected.
- CI now includes the full application suite, Django check, and migration check in addition to project-state validation.
- Production CORS configuration receives `DJANGO_CORS_ALLOWED_ORIGINS` from deployment environment variables.
- No migrations were created.
- At that historical checkpoint T3-03 request context, External Supplier records, and future business modules remained unimplemented; T3-03 has since been completed as recorded above.

## Historical roadmap handoff (superseded by the current T3-04 status above)

T3-02A-BUSINESS-DECISION-LOCK authorized documentation/business-rule reconciliation only. Do not implement T3-02A, T3-03, T3-05A (Staging Backend Foundation), F7-01A (Staging Frontend & Client Review Checkpoint), any application feature, or deploy any environment under this task. T3-02A remains the next candidate and requires its own task plan and exact explicit confirmation. Newly approved account/authentication policies are targets, not implemented behavior; remaining policy items stay `BUSINESS DECISION REQUIRED` in the canonical decision record.

## Historical tests and checks — V1-ROADMAP-UPDATE

- Repository validator: PASS (dirty working tree warning is expected until documentation changes are committed).
- Validator tests: 11 passed.
- Application suite: 120 passed; collection was 120.
- Django system check: PASS.
- Migration check: no changes detected.
- `git diff --check`: PASS (Git emitted only CRLF-to-LF normalization warnings).
- GitHub Actions: the previously verified baseline run was green; this local documentation diff has not been pushed and has no new CI run.
- Scope: documentation only; no application source, migrations, deployment, commit, or push.

## Historical: T3-02A-BUSINESS-DECISION-LOCK (superseded by the current T3-02A status above)

- Decision: approved T3-02A account/authentication, phone, credential lifecycle, Shop settings, locale, and appearance rules are now recorded in the canonical business-rule and decision documents.
- Code status: unchanged. Anonymous User creation is still available in the current endpoint, and login remains email-only; T3-02A must reconcile these approved policy targets.
- Validation: repository validator PASS (dirty-tree warning expected); validator tests 11 passed; full pytest 120 passed; Django check PASS; migration drift check no changes; `git diff --check` PASS. Business Rule IDs are unique and `BUSINESS_RULES.md`/`DECISIONS.md` pass strict UTF-8 decoding. Current local diff has no new CI run.
- Next task: T3-02A remains unauthorized; obtain its exact task confirmation before implementation. T3-03 also remains unauthorized.
