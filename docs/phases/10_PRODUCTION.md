# Phase 10 — Production

## 1. Phase Overview

Perform the controlled SGTP production release and final acceptance after staging readiness is approved.

## 2. Phase Objective

Configure, deploy, validate, monitor, back up, and hand off the complete V1 product safely.

## 3. Business Purpose

Make the integrated supplier and shop platform available to real authorized users with operational safeguards.

## 4. Technical Purpose

Execute a repeatable production release with secure secrets, PostgreSQL, object storage, workers, migrations, monitoring, backups, and final documentation.

## 5. Preconditions

Phase 9 staging and restore readiness accepted; critical defects resolved/accepted; production approvals and secrets are available; explicit `CONFIRM PHASE 10` has been received.

## 6. Dependencies

Validated artifacts, staging evidence, migration/recovery plan, production infrastructure, secret management, monitoring, backup/object storage, worker operations, and final acceptance checklist.

## 7. Current Repository Assumptions

The current repository is a starter and is not production-ready. This playbook is future execution guidance and must not be treated as authorization to deploy now.

## 8. Exact Scope

Production configuration/secrets, PostgreSQL, object storage, workers, migrations, monitoring, backups, deployment validation, security review, final acceptance, documentation, and handoff.

## 9. Out of Scope

New features, architecture changes, unapproved schema changes, direct production experimentation, and bypassing staging or approval gates.

## 10. Architecture Context

Production must preserve supplier/back-office/shop isolation and the complete request-to-reports workflow under real operational controls.

## 11. Implementation Sequence

Release approval → secrets/configuration → infrastructure readiness → backup/migration → deploy/cutover → smoke/acceptance → monitoring/review → handoff.

## 12. Detailed Task List

### P10-01 Production configuration and secret readiness

- Objective: verify production configuration, secrets, domains, TLS, and access controls.
- Why it exists: incorrect configuration can expose data or prevent safe startup.
- Dependencies: Phase 9 accepted; explicit task confirmation.
- Files/areas: production manifests, secret references, runbooks, CI/CD environment protections.
- Steps: validate immutable Cloudflare Pages frontend and Render backend artifacts, Render PostgreSQL and private Cloudflare R2/S3-compatible storage references, secret manager references, hosts/CORS, service accounts, resource limits, logging/privacy, rollback plan.
- Database/API/security impact: production access policy only; no business changes.
- Tests: configuration/deploy checks and secret presence without printing values.
- Validation: review checklist and dry-run.
- Documentation: production runbook, security/state/handoff.
- DoD: configuration approved and secrets controlled.

### P10-02 Database, storage, workers, and backups

- Objective: prepare production dependencies and recovery protection.
- Why it exists: data durability and async operations are core product responsibilities.
- Dependencies: P10-01, explicit task confirmation.
- Files/areas: infrastructure/runbooks/monitoring configuration.
- Steps: verify PostgreSQL, backups/retention/encryption, object storage lifecycle/private access, worker queues/retries, alerting, restore procedure, capacity.
- Database: backup before migrations; record locks/timing and recovery objectives.
- API/security: least-privilege access, no public files, TLS.
- Tests: backup verification, storage access, worker health, alert delivery.
- Validation: readiness evidence.
- Documentation: operations/database/security/handoff.
- DoD: dependencies are durable and observable.

### P10-03 Controlled deployment and migrations

- Objective: deploy the approved artifact and apply migrations safely.
- Why it exists: production change must be repeatable and reversible.
- Dependencies: P10-02, explicit task confirmation.
- Files/areas: release pipeline and deployment runbook.
- Steps: confirm approval/artifact checksum, backup, maintenance strategy, migrate, deploy, collect assets, start workers, verify health/readiness, record release.
- Database: forward migration only with recovery path.
- API/security: enforce TLS/hosts/CORS/auth settings.
- Tests: deployment smoke and migration checks.
- Validation: no failed health/readiness or unexpected errors.
- Documentation: release record/state/handoff/changelog.
- DoD: production runs approved artifact with verified migrations.

### P10-04 Final acceptance, monitoring, and handoff

- Objective: validate the complete V1 journey and transfer operational ownership.
- Why it exists: V1 completion requires integrated evidence, not running services alone.
- Dependencies: P10-03, explicit task confirmation.
- Files/areas: acceptance suite, dashboards/alerts, runbooks, final docs.
- Steps: validate Supplier → Back Office → Shop → Client → Work → Design → Measurement → Fabric → Production → Completion → Billing → Reports; test Shop A/B isolation, files, jobs, billing/report integrity, alerts, rollback contact paths; record acceptance.
- Database/API/security: real authorized test accounts and controlled data only.
- Tests: final smoke/E2E/security/backup/monitoring checks.
- Validation: Definition of Done checklist signed/recorded.
- Documentation: all persistent docs, release notes, handoff.
- DoD: product accepted and support can operate/recover it.

## 13. Task Dependency Graph

`P10-01 → P10-02 → P10-03 → P10-04`.

## 14. Expected Files / Folders

Production manifests/workflows, secret templates, runbooks, monitoring/backup configuration, acceptance reports.

## 15. Expected New Files

Only approved Cloudflare Pages/Render deployment, operations, monitoring, backup, release, and acceptance documentation/configuration.

## 16. Expected Modified Files

Production configuration and runbooks; application code only through a separately confirmed corrective task.

## 17. Database Changes

Approved production migrations only, with backup, timing, lock, and recovery evidence.

## 18. Migration Requirements

Review, backup, rehearse, apply, verify, and document every migration; never bypass recovery controls.

## 19. API Changes

No feature API changes. Verify deployed schema, auth, health, and error behavior.

## 20. Backend Changes

Configuration/deployment/runtime operations only; no unapproved implementation during release.

## 21. Frontend Changes

Deploy approved build only; no feature work during production release.

## 22. Security Requirements

Secret manager, TLS, least privilege, private storage, secure headers/cookies, audit/monitoring, incident contacts, and final security review.

## 23. Tenant / Permission Requirements

Prove production Shop A/Shop B isolation and supplier cross-shop policy with controlled accounts before acceptance.

## 24. Validation Requirements

Release, migration, health, smoke, E2E, security, financial, storage, jobs, monitoring, backup, restore, and rollback validation.

## 25. Testing Requirements

Final acceptance suite plus production-safe smoke tests; record commands, artifacts, results, and limitations.

## 26. Error / Failure Handling

Abort on failed readiness/security/health checks; invoke rollback/recovery runbook; page owners; preserve audit/log evidence.

## 27. Documentation Updates

Update architecture/API/security/database/state/handoff/changelog/operations and final release record.

## 28. Git Checkpoint Guidance

Create a local release checkpoint only after review; never push automatically or rewrite history.

## 29. Handoff Requirements

Record release/artifact, migrations, infrastructure, monitoring, backups, contacts, acceptance evidence, known risks, and support procedures.

## 30. Phase Validation Checklist

- [ ] Production config/secrets reviewed
- [ ] PostgreSQL/storage/workers ready
- [ ] Backups and restore path verified
- [ ] Deployment/migrations pass
- [ ] Health/smoke/E2E pass
- [ ] Shop isolation/security pass
- [ ] Monitoring/alerts operational
- [ ] Final handoff complete

## 31. Definition of Done

The approved SGTP V1 product is running in production, its critical integrated workflows and security controls are accepted, and operators can monitor, back up, recover, and support it.

## 32. Common Implementation Mistakes

Deploying untested artifacts, printing secrets, migrating without backup, public storage, skipping isolation tests, accepting green health checks as V1 completion, changing code during cutover.

## 33. Rollback / Recovery Notes

Use the approved rollback/migration recovery/restore runbooks; stop traffic or feature flags when required; preserve financial/audit data and incident evidence.

## 34. Phase Implementation Prompt

**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 10 only; it does not authorize P10-01 through P10-04. Before each task, present its objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. Implement only the confirmed task, validate it, update documentation, report the result, and stop. Do not begin the next task automatically; Phase 10 has no later implementation phase.

## 35. Phase Completion Report Format

`Phase: 10` / `Task confirmed:` / `Artifact/release:` / `Migrations/backups:` / `Smoke/E2E/security:` / `Monitoring:` / `Acceptance:` / `Docs/handoff:` / `Unresolved risks:`.
