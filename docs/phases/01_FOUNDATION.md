# Phase 1 — Foundation

## 1. Phase Overview

Build the verified technical foundation on top of the existing SGTP starter without creating business modules.

## 2. Phase Objective

Make the repository, runtime, settings, identity, shared model, PostgreSQL, and documentation foundations safe for later phases.

## 3. Business Purpose

Provide a stable base for supplier, shop, and tailor workflows without prematurely encoding business behavior.

## 4. Technical Purpose

Create reproducible environments, split settings, secure defaults, a custom User foundation, shared abstractions, and migration discipline.

## 5. Preconditions

- Explicit phase activation: `CONFIRM PHASE 1`; task authorization remains separate and uses `CONFIRM TASK F1-01` for the first task.
- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `docs/HANDOFF.md`, `docs/ARCHITECTURE.md`, `docs/PRODUCT_DEFINITION.md`, and this file.
- Starter repository is at the project root; do not replace it.

## 6. Dependencies

- Existing Django starter, `requirements.txt`, migrations, Docker files, and custom User code.
- Approved SGTP target; no future business module activation.

## 7. Current Repository Assumptions

The starter has `core/settings.py`, `apps/accounts`, `apps/common`, `apps/tenants`, PostgreSQL configuration, and Docker/devcontainer files. The host may not have dependencies installed.

## 8. Exact Scope

Repository verification, dependency/venv baseline, environment management, django-environ adoption if approved, settings split, User/core/shared model interfaces, PostgreSQL, migration policy, secure defaults, and baseline documentation.

## 9. Out of Scope

No supplier, shop, client, design, measurement, material, work, billing, report, AI, frontend screen, or production deployment implementation.

## 10. Architecture Context

The target is Django/DRF + PostgreSQL with supplier → back office → isolated shop hierarchy. This phase establishes interfaces only; Phase 3 defines shop tenancy and Phase 4 defines business entities.

## 11. Implementation Sequence

Repository baseline → dependency environment → environment/settings split → identity/shared model review → PostgreSQL/migrations → secure defaults → checks/documentation.

## 12. Detailed Task List

### F1-01 Repository and dependency baseline

- Objective: make local and container dependency installation reproducible.
- Why: later tests must run from a known baseline.
- Dependencies: none beyond activation.
- Files to create: optional `.python-version`, `backend/config/settings/{base.py,dev.py,prod.py}`, `backend/core/` shared-foundation interfaces, and `backend/manage.py` only if the approved migration to the target structure is activated; no business code.
- Files to modify: `requirements*.txt`, `pyproject.toml`, `Makefile`, README only where verified.
- Steps: inspect versions; create ignored virtual environment; install dev requirements; pin/add only necessary packages; record commands; run `pip check`.
- Database/API/security impact: none directly; do not change contracts.
- Tests: dependency import test and repository check.
- Validation: `python manage.py check`, `pytest`, lint commands or documented blockers.
- Documentation: update state/handoff with exact versions and result.
- DoD: clean reproducible baseline or explicit blocker.

### F1-02 Environment management and settings split

- Objective: separate base/development/test/production settings with consistent environment names.
- Why: unsafe defaults and mismatched Docker variables currently exist.
- Dependencies: F1-01.
- Files to create: settings package/modules and typed environment configuration only as needed.
- Files to modify: current starter `core/settings.py` during transition, target `backend/config/settings/*`, `.env.example`, Docker/devcontainer files, `.gitignore`.
- Steps: define required/optional variables; remove hard-coded production secrets; align `DEBUG`, database URL/DB fields, hosts, CORS placeholders, static/media paths; preserve import compatibility.
- Database/API/security impact: configuration only; do not change business endpoints.
- Tests: settings-load tests for development/test/production and missing-secret behavior.
- Validation: `manage.py check --deploy` under production-like settings.
- Documentation: update security/API/development docs.
- DoD: every environment loads deterministically and fails safely.

### F1-03 Identity and shared model foundation

- Objective: verify the custom User and shared base model contracts for future phases.
- Why: every later record depends on IDs, audit timestamps, deletion, and authentication identity.
- Dependencies: F1-02.
- Files to create: only approved `core` interfaces/tests.
- Files to modify: current starter `apps/accounts/models/*` during transition, target `backend/apps/accounts/*`, target `backend/core/models/*`, admin/tests as necessary.
- Steps: preserve email login; verify manager/password behavior; document audit-user semantics; decide whether soft delete is appropriate for identity records; expose stable imports.
- Database impact: only approved foundational migration changes.
- API/security impact: preserve existing auth contract; no new endpoints.
- Tests: user creation, password, superuser, UUID/timestamp/audit behavior, deletion semantics.
- Validation: migration graph and test database.
- Documentation: update database/security/architecture docs.
- DoD: identity and shared model contracts are explicit and tested.

### F1-04 PostgreSQL and migration strategy

- Objective: establish a reliable PostgreSQL-first migration workflow.
- Why: target persistence is PostgreSQL and future constraints depend on it.
- Dependencies: F1-02, F1-03.
- Files to modify: database settings, Compose/devcontainer setup, migration documentation.
- Steps: align service names/credentials; ensure test database path; document forward-only migrations, rollback expectations, backups, and migration review.
- Database impact: validate existing migrations; create only foundation migrations approved in F1.
- API/security impact: none; never commit credentials.
- Tests: migrate from empty DB, migrate test DB, show migrations, check constraints.
- Validation: clean setup from an empty PostgreSQL database.
- Documentation: update `docs/DATABASE.md`, state, handoff.
- DoD: empty-database setup is repeatable and documented.

### F1-05 Secure defaults and baseline documentation

- Objective: close foundation-level unsafe defaults and make the repository self-describing.
- Why: later phases rely on explicit security and operating rules.
- Dependencies: F1-02 to F1-04.
- Files to modify: settings, `.env.example`, `AGENTS.md`, relevant docs.
- Steps: configure secure cookies/headers by environment; validate hosts; document secret handling; add baseline health/check commands without business behavior.
- Tests: deploy checks, settings tests, secret leakage scan.
- Validation: no secrets tracked; docs match code.
- Documentation: update all affected persistent documents and handoff.
- DoD: foundation is reviewable and safe to hand to Phase 2.

## 13. Task Dependency Graph

`F1-01 → F1-02 → F1-03 → F1-04 → F1-05`.

## 14. Expected Files / Folders

Current starter paths `core/`, `apps/accounts/`, and `apps/common/` may be modified during transition; target foundation paths are `backend/config/`, `backend/apps/accounts/`, `backend/core/`, `requirements*.txt`, `.env.example`, Docker/devcontainer files, `tests/` if approved, and `docs/`.

## 15. Expected New Files

Settings modules, foundation tests, and environment/development documentation only where required by the approved baseline.

## 16. Expected Modified Files

Existing settings, dependency, Docker, User/shared model, migration, and documentation files; preserve starter behavior unless explicitly approved.

## 17. Database Changes

Only identity/shared-foundation corrections approved in this phase. No business tables.

## 18. Migration Requirements

Review existing migrations, test from empty PostgreSQL, keep migrations committed, and never edit an applied migration without a documented recovery plan.

## 19. API Changes

No new business APIs. Existing auth behavior may be corrected only when required by the foundation contract.

## 20. Backend Changes

Settings, runtime configuration, identity/shared model contracts, checks, and test infrastructure.

## 21. Frontend Changes

None. Do not implement screens or frontend business modules.

## 22. Security Requirements

No default production secret, explicit hosts, secure cookie/header policy, safe error behavior, secret exclusion, and deterministic environment validation.

## 23. Tenant / Permission Requirements

Define interfaces and decisions only. Do not implement shop tenancy or object permissions in Phase 1.

## 24. Validation Requirements

Clean install, settings load, Django checks, migration from empty DB, test suite, lint/format checks, and secret scan.

## 25. Testing Requirements

Foundation unit/settings/migration tests and existing account regression tests. Record unavailable infrastructure instead of skipping silently.

## 26. Error / Failure Handling

Fail startup clearly for missing required production variables, unavailable database, invalid settings, and migration failure.

## 27. Documentation Updates

Update `PROJECT_STATE`, `HANDOFF`, `ARCHITECTURE`, `DATABASE`, `SECURITY`, `CHANGELOG`, and `DECISIONS` for actual changes.

## 28. Git Checkpoint Guidance

Use one local checkpoint per completed task; never push. Keep code and documentation changes reviewable.

## 29. Handoff Requirements

Record task ID, files, migrations, commands, test results, blockers, decisions, and the exact next task. Do not activate Phase 2 automatically.

## 30. Phase Validation Checklist

- [ ] Dependencies reproducible
- [ ] Settings split and safe
- [ ] User/shared contracts verified
- [ ] PostgreSQL migration path verified
- [ ] Checks/tests/lint run
- [ ] Documentation current

## 31. Definition of Done

All F1 tasks completed or explicitly blocked, no business modules created, baseline checks pass, and handoff is sufficient for Phase 2.

## 32. Common Implementation Mistakes

Creating a replacement project; using SQLite as the target DB; committing secrets; changing auth semantics without tests; editing applied migrations; implementing shop/business models early.

## 33. Rollback / Recovery Notes

Use Git revert or a new corrective migration; restore environment files from local secure copies; never reset shared history or delete starter data without approval.

## 34. Phase Implementation Prompt

**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 1 only; it does not authorize F1-01 through F1-05. Before each task, present that task's objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. After confirmation, implement only that task, run its validation, update documentation, report the result, and stop. Do not begin the next task or Phase 2 automatically. Do not create business modules, shop workflows, billing, AI, frontend screens, or deployments.

## 35. Phase Completion Report Format

`Phase: 1` / `Tasks completed:` / `Files changed:` / `Database/migrations:` / `API/security impact:` / `Tests and results:` / `Known issues:` / `Documentation updated:` / `Next task:` / `Confirmation required:`.
