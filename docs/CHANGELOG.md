# Changelog

## 2026-09-28 — T3-04 Scoped Querysets and Object Permissions

- Updated `TenantScopedMixin` to require authorized T3-03 context, verify actor/URL/compatibility alias consistency, filter by the trusted Shop, and force Shop ownership on create/update.
- Bound `IsTenantMember` object checks to the selected Shop for ordinary members and Main Supplier; added temporary UUID/FK/soft-delete test proof for direct IDs, lists/counts, Main Supplier scope, writes, and fail-closed mismatches.
- No business models/endpoints, migrations, dependencies, global Tenant/member API changes, or T3-05 work. Future business endpoints must adopt and prove the shared boundary.
- Validation: focused tests 28 passed; full application suite 152 passed (144 warnings); repository validator PASS (152 discovered); validator tests 14 passed; Django check, migration drift, OpenAPI, Black, Flake8, and `git diff --check` passed. Changes are local only, with no commit, push, or CI run.

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
