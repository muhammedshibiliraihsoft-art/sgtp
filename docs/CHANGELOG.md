# Changelog

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
- The GitHub Actions run for the previous committed baseline failed on PostgreSQL connectivity. The updated workflow has not run on GitHub because these closure changes remain local and have not been pushed.

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
