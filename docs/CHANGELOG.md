# Changelog

## 2026-09-30 — T3-05A Staging Backend Foundation (published; CI green)

- Prepared an explicit secure staging settings profile, PostgreSQL URL support, Render Blueprint with manual deployment and isolated Free PostgreSQL, bounded database startup readiness, provider PORT/Gunicorn configuration, CSRF bootstrap, guarded staging reset command, smoke checker, and staging runbook.
- Local PostgreSQL-backed application suite: 255 passed; staging-focused tests: 28 passed; auth/CSRF lifecycle regressions: 7 passed; validator tests: 23 passed. Staging Django/deploy checks, migration drift, OpenAPI (zero errors), Black, Flake8, and `git diff --check` passed. Docker build and disposable local PostgreSQL-backed container smoke passed.
- Black/Flake8 passed for new staging and validator Python modules; whole-file checks of touched legacy files report existing style findings and no broad reformat was applied. Published as `9af6424116ebba12896d90d032c36bd25328a4d0`; Project State Validation run `36652187336` succeeded for that exact SHA. No application business models or migrations, dependency changes, frontend, worker, storage, or Production resources were added. No Render account/resource, DNS/TLS, or live staging deployment has been verified or performed.

## 2026-09-30 — T3-05 Back-office / Shop API and Admin hardening (published; CI green)

- Implemented membership-scoped Shop discovery/profile reads, role-limited statistics, Main Supplier-only Shop settings and lifecycle operations, exact User-ID member lookup, capacity lower-bound enforcement, and hardened Django Admin paths without changing the approved business rules.
- Added API/Admin, authorization, regression, and PostgreSQL concurrency coverage. Full PostgreSQL-backed suite: 231 passed; repository validator and 14 validator tests passed; Django check, production deployment check, migration drift check, OpenAPI validation (zero errors), Black, Flake8, and `git diff --check` passed. OpenAPI/deployment checks report nonfatal serializer type-hint and role-enum warnings.
- No migration or dependency changes. Published as commit `3d21a0943006cd866bc19bc728cbec05daae1630`; exact-SHA Project State Validation run `36614638187` succeeded. T3-05A, Phase 4, frontend, and deployment work have not started.

## 2026-09-29 — T3-04C Work-Function foundation (published; CI green)

- Added normalized membership-scoped persistence for the approved seven-code catalog, additive migration with no backfill, Shop ADMIN-only GET/PUT management, Shop isolation, actor attribution, transactional set replacement, and soft-deleted assignment history.
- Added model/API/lifecycle/migration and PostgreSQL concurrency regression coverage. Focused tests: 19 passed; full PostgreSQL-backed suite: 211 passed (172 warnings). Repository validator, validator tests, Django/migration/OpenAPI checks, Black, Flake8, and diff check passed. Published implementation commit `dfbf6eecdbcd36c014a45a5d297c26e4e27a4113`; GitHub Actions Project State Validation run `36605653294` succeeded for that exact SHA.
- Updated current product-definition, decision, API, architecture, database, security, business-rule, phase, development-plan, project-state, and handoff descriptions. Phase 4 stage/function mapping remains deferred; T3-05 and later tasks have not started.

## 2026-09-29 — Parallel Frontend Foundation Track governance

- Documented a separate same-repository frontend branch/worktree strategy while retaining `main` as the backend/integration source and canonical cross-project documentation owner.
- Approved early frontend foundation preparation as distinct from Phase 7/F7-01 completion; F7-01/F7-01A retain their existing T3-05A sequencing. Frontend work must be mock-first for unfinished APIs, backend-authorized, and respect the single-owning-Shop ordinary-account model.

## 2026-09-29 — T3-04B User-Scope remediation (published)

- Replaced the superseded one-global-User/multi-Shop assumption with one immutable owning Shop per ordinary account; separate Shops require distinct accounts even for the same real-world person.
- Added Shop-owned account creation and reset authority, atomic Shop/first-ADMIN account creation, same-Shop membership enforcement, and guarded ownership backfill/database consistency protections.
- Added/updated account-scope, membership, Shop creation, reset, and migration-preflight regression tests. Pre-publication local validation: focused User-Scope suite: 9 passed; PostgreSQL-backed full application suite: 192 passed. Validator, validator tests, Django check, migration drift and OpenAPI pass; OpenAPI/deploy checks report two nonfatal role-enum naming warnings. New Python files pass Black/Flake8; broad lint/format checks on touched legacy files still show existing style findings.
- Updated current architecture, business rules, API, database, security, phase plan, project state, and handoff docs. Published as commit `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c`; GitHub Actions Project State Validation run `36591864481` completed SUCCESS for that exact SHA. T3-04C and later tasks remain unstarted.

## 2026-09-29 — T3-04B Remediation publication checkpoint

- Restored the T3-04B transactional membership and global User-lifecycle services on the verified post-revert `main` baseline. Shop creation commits with exactly one active first ADMIN; membership User/Shop identity is immutable; ADMIN hierarchy/cardinality, locked User validation, global deactivation invariants, undo ordering, and approved capacity/reactivation rules are enforced in services.
- Disabled direct Django Admin Shop creation and membership writes; routed User Admin deactivation through the global lifecycle service. Updated inactive-Shop Shop Admin denial to 403, corrected exact normalized undo error assertions, and updated reactivation-at-capacity expectations.
- Added Shop creation, ADMIN/User lifecycle, Django Admin, multi-Shop, and PostgreSQL separate-connection race regression tests. No migration, dependency change, T3-04C, T3-05, or later-phase implementation.
- Local validation before publication: focused remediation 77 passed; T3-04A/T3-03/membership/migration regressions 39 passed; full PostgreSQL-backed suite 183 passed (113 warnings); validator 183 discovered and 14 validator tests passed; Django/deployment checks, OpenAPI, Black, Flake8, and diff check passed. Require Project State Validation SUCCESS for the exact publication SHA before T3-04C.

## 2026-09-29 — T3-04A Global Identity / User-ID / Authentication

- Implemented the confirmed global identity foundation locally: generated permanent User ID, canonical optional email/phone identity for normal users, required trimmed first name, alias-based authentication, contact safeguards, controlled credential reset, and hard-delete denial.
- Added a preflight/backfill migration that refuses unsafe legacy rows rather than fabricating names or contacts; added identity, authentication, API, and migration-preservation regression coverage. Existing UUID primary keys, JWT UUID identity, memberships, and audit references are preserved.
- Read-only local database preflight found no existing User/superuser/Shop rows or email/name issues. After preflight, the local PostgreSQL database successfully applied required tenant migrations and `accounts.0004_t304a_global_identity`; no production database was accessed.
- Focused identity/authentication suite: 29 passed; T3-02A compatibility regression: 10 passed. Full PostgreSQL-backed application suite: 167 passed (155 warnings); repository validator PASS; 14 validator tests passed; Django system/deployment checks, migration drift, OpenAPI validation, Black and Flake8 for newly added Python modules, and `git diff --check` passed. A broader Flake8 run over touched legacy files still reports findings and is not reported as clean.
- At the original T3-04A task-time checkpoint, changes were local-only and GitHub CI had not run; they were subsequently published. T3-04B and later tasks were unstarted at that historical checkpoint.

## 2026-09-28 — T3-04 Scoped Querysets and Object Permissions

- Updated `TenantScopedMixin` to require authorized T3-03 context, verify actor/URL/compatibility alias consistency, filter by the trusted Shop, and force Shop ownership on create/update.
- Bound `IsTenantMember` object checks to the selected Shop for ordinary members and Main Supplier; added temporary UUID/FK/soft-delete test proof for direct IDs, lists/counts, Main Supplier scope, writes, and fail-closed mismatches.
- No business models/endpoints, migrations, dependencies, global Tenant/member API changes, or T3-05 work. Future business endpoints must adopt and prove the shared boundary.
- Initial task-completion validation (before publication): focused tests 28 passed; full application suite 152 passed (144 warnings); repository validator PASS (152 discovered); validator tests 14 passed; Django check, migration drift, OpenAPI, Black, Flake8, and `git diff --check` passed. The implementation was subsequently committed/pushed; current publication and CI evidence is recorded in the 2026-09-29 entry below.

## 2026-09-29 — T3-REBASELINE-01 Phase 3 business architecture and state sync

- Reconciled approved global User/User ID, optional normal-user contacts, admin-grade contacts, multi-Shop membership, ADMIN cardinality/authority, Shop visibility/lifecycle, capacity, and membership-scoped Work Function rules. Marked them as confirmed target policy, not implemented code; assigned prerequisite work to T3-04A–T3-04C before T3-05.
- Updated product, architecture, API/security/database, Phase 3/4/7/8 plans, project state, handoff, and decision/business-rule records. Preserved T3-03/T3-04 path-context and isolation contracts and the fixed V1 workflow.
- Corrected current T3-04 repository state: live verification showed `main`/`origin/main`/remote main in parity (derive current SHA from Git); GitHub Actions Project State Validation run #36511111586 succeeded for the published baseline. Current documentation changes are local/uncommitted and are not covered by that CI result.
- Validation: repository validator PASS (152 discovered); validator tests 14 passed; Django check PASS; migration drift reports no changes with local PostgreSQL unavailable; full pytest collected 152 but was blocked by unavailable PostgreSQL; `git diff --check` PASS. Documentation audit found 52 unique Business Rule IDs and consistent task sequencing. No application source or migration changes.
- Documentation/planning only. No application code, migrations, dependencies, tests, frontend, staging, commit, or push.

## 2026-09-28 — T3-03 Tenant / Shop Request Context

- Added a request-local Shop context resolver and reusable DRF context base that authenticates before Shop authorization and preserves the mandatory password-change gate.
- Added `GET /api/v1/shops/{shop_id}/context/` with UUID path selection, selected-Shop membership role, and explicit Main Supplier context; no Shop defaults are returned.
- Added the approved uniform non-disclosing 404 contract for foreign, unauthorized, inactive, soft-deleted, unavailable, and nonexistent Shops; authentication failures retain 401.
- Updated `IsTenantMember` to require the resolved request context and added focused context/security regressions. T3-04 query/object isolation remains out of scope; no business model, migration, dependency, or global Shop-visibility policy changed.
- T3-02A current-state documentation was reconciled while updating task handoff; dated historical decision/audit records were retained and labelled historical where needed.
- T3-03 was committed and pushed; GitHub Actions Project State Validation Run #19 passed for the implementation commit.

## 2026-09-28 — T3-02A Account and preference foundation

- Implemented the confirmed account/authentication foundation: unique optional E.164 phone and email-or-phone login, Main Supplier Admin-only account creation/phone management, one-time no-store initial credentials with forced password change, and email reset with refresh-session revocation.
- Added nullable User locale, `system|light|dark` appearance, and nullable Shop default locale/timezone/currency; ordinary authenticated global Shop reads omit the new defaults.
- Added additive accounts/tenants migrations and regression tests; preserved UUID identity, existing memberships, email login, JWT/CSRF/refresh rotation/blacklist protections, and production throttle rates.
- Updated current API, architecture, database, security, phase plan, project state, and handoff descriptions. No T3-03 or later-phase implementation, CI push, or GitHub push was performed.

## 2026-09-28 — T3-02A-BUSINESS-DECISION-LOCK

- Recorded human-approved account creation, email/phone identity and management, credential lifecycle, Shop timezone/currency/settings authority, nullable locale, and appearance rules in `docs/BUSINESS_RULES.md` and `docs/DECISIONS.md`.
- Reconciled architecture, product definition, API, database, security, phase plan, project state, handoff, and agent instructions. Explicitly recorded that public User creation remains enabled in current code and email-only login remains implemented; T3-02A must reconcile these behaviors.
- Repaired the identified Windows-1252 em-dash encoding bytes in `BUSINESS_RULES.md` and `DECISIONS.md` without changing their business meaning; strict UTF-8 validation now passes.
- Documentation/business-rule reconciliation only. No application source, migrations, dependencies, deployment, commit, or push; T3-02A and T3-03 remain unimplemented and unauthorized.

## 2026-09-28 — V1-ENVIRONMENT-LOCK

- Locked the V1 environment model as LOCAL → STAGING → PRODUCTION. Removed the separate Preview tier from the approved architecture.
- Recorded company name BiRKy and staging domains `staging.birky.com` / `api-staging.birky.com`. Production domains `app.birky.com` / `api.birky.com` are reserved but not provisioned.
- Renamed T3-05A from "Backend Preview" to "Staging Backend Foundation" and F7-01A from "Client Preview Frontend" to "Staging Frontend & Client Review Checkpoint".
- Moved F7-01/F7-01A earlier in the dependency sequence (immediately after T3-05A) to enable early client staging and auth/i18n/theme browser validation.
- Updated Phase 9 to reuse the same Staging environment for formal release-candidate validation after reset/reconfiguration.
- Added BR-ENV-001 and BR-ENV-002 environment/deployment business rules.
- Documentation/roadmap only: no application code, migrations, or deployment was changed.

## 2026-09-28

- Completed and committed the T3-02-REMEDIATION implementation with security and integrity fixes; subsequent closure review identified CI PostgreSQL connectivity and test throttle-cache isolation issues.
- Restricted User API targeting, aligned Shop writes with Main Supplier policy, protected membership lifecycle state, verified real authentication throttling, restored duplicate CORS test coverage, expanded CI health checks, and wired production CORS environment propagation.
- Added regression coverage; 120 application tests are collected. The initial CI result and full-suite details were corrected during the closure follow-up below; no migrations were created.
- Left global User administration ownership, ordinary-user Shop read visibility, Shop DELETE semantics, and T3-03 work unresolved/deferred.

## 2026-09-28 — T3-02-REMEDIATION validation closure

- Mapped the PostgreSQL service port to the GitHub Actions runner so the PostgreSQL-backed application suite can connect to its service.
- Isolated auth-throttle cache state in the API tests that expect baseline login responses; production throttle rates and behavior were not changed.
- Corrected current-state claims in project state, handoff, architecture, security, and README documentation.
- Local validation: 120/120 application tests passed; 69 focused tests passed; 11 repository-validator tests passed; repository validator and Django system check passed; migration check reported no changes.
- Historical note: the earlier run failed on PostgreSQL connectivity. This was superseded by the later verified green GitHub Actions run 36415017163 on `0ac45e1e80606539210ff8f7ad5a653eb4ba5215`; that run does not validate subsequent local documentation changes.

## 2026-09-28 — V1 roadmap update

- Updated the approved V1 requirement-to-task map while preserving the ten-phase architecture and task-level confirmation gate.
- Added planned Phase 3 tasks T3-02A and T3-05A, and Phase 7 task F7-01A; assigned localization, RTL/LTR, Light/Dark/System, tailoring, billing, documents, audit, observability, preview, testing, staging, production, and Post-V1 requirements to their owning plans.
- Created `docs/POST_V1_ROADMAP.md` and `docs/ENVIRONMENTS.md`.
- Documentation/roadmap only: no application code, migrations, or deployment was authorized or changed.

## 2026-09-27

- Completed PRE-P3-02 documentation-only governance correction.
- Locked the V1 model as exactly one Main Supplier / Main Admin above multiple isolated Shops.
- Clarified that External Suppliers are Shop-owned non-user records with no login, tenant role, or global/shared directory.
- Hardened the Phase 3 T3-01 brief and preserved the legacy Tenant compatibility decision gate.
- No Phase 3 business implementation, models, migrations, APIs, or application source changes were made.

## 2026-09-25

- Bootstrapped repository continuity documentation and agent instructions.
- Recorded the verified baseline: empty Git repository with no Django implementation.
- Established the SGTP V1 Target Final Product / Definition of Done, including the supplier/shop hierarchy, Tailor Management workflow, technical capabilities, boundaries, and end-to-end validation requirements.
- Realigned the architecture, development plan, project state, handoff, and agent instructions to the approved target without changing application code.
- Clarified the project-wide confirmation gate: phase confirmation activates scope only; each task requires a separate explicit task confirmation and ends with a stop boundary.
- Added the missing Phase 7–10 Antigravity implementation playbooks without changing the approved architecture, scope, order, or implementation decisions.
- Canonicalized target implementation paths, domain boundaries, deployment direction, and refresh-token handling across the phase plan while preserving current-starter descriptions.
- Documented the required CSRF strategy decision point for cookie-based refresh; the concrete mechanism remains a Phase 2 selection, implementation, and validation task.
- Corrected project state to distinguish the existing starter foundation from unimplemented Phase 1 work; recorded Phase 1 as independently audited and ready, but inactive and unconfirmed.
- Recorded approved URL-path tenant context (`/shops/{shop_id}/...`) and Primary Client ownership for Related Person billing; retained Phase 2 CSRF mechanism selection and validation as an explicit task.

## 2026-09-27

- Added the dependency-light `scripts/verify_project_state.py` validator, focused validator tests, and a GitHub Actions state-validation gate.
- Added an evidence-backed repository-state completion rule to `AGENTS.md` and synchronized current Phase 2/B2-05, 47-test, and Phase 3-not-started documentation claims.
- Activated Phase 1 and completed Task F1-01 (Repository and dependency baseline). Established virtual environment and verified manage.py check. Documented validation limitations: existing starter lint violations remain and pytest is blocked by unavailable PostgreSQL; no application source cleanup was performed.
- Completed Task F1-02 (Environment management and settings split) by modularizing core/settings.py into ackend/config/settings/{base,dev,prod,test}.py, updating .env.example, and ensuring safe failure on missing secrets.

## 2026-09-28 — T3-02-REMEDIATION final documentation closure

- Confirmed that the GitHub Actions run for the closure commit successfully passed the application suite, Django system checks, and PostgreSQL integration.
- Confirmed T3-02-REMEDIATION is now fully CLOSED.
- Added agent transition note regarding the shift to Codex for upcoming engineering work, maintaining all established governance and architectural rules.
