# Phase 9 — Staging

## 1. Phase Overview

Deploy the validated SGTP system to a production-like staging environment for operational verification.

## 2. Phase Objective

Prove configuration, migrations, storage, workers, monitoring, smoke tests, end-to-end flows, and backup recovery outside local development.

## 3. Business Purpose

Give stakeholders a safe environment to validate the integrated supplier and shop workflows before production.

## 4. Technical Purpose

Exercise deployment automation and operational controls with staging-specific secrets and data boundaries.

## 5. Preconditions

Phase 8 release gates pass; deployment artifacts are reviewed; staging accounts/services are provisioned; explicit `CONFIRM PHASE 9` has been received.

## 6. Dependencies

Validated backend/frontend artifacts, PostgreSQL migration path, object storage, worker/job configuration, monitoring, CI, backup/restore procedures, and approved environment variables.

## 7. Current Repository Assumptions

The starter has Docker/Compose foundations but no verified staging environment. Staging must not reuse production secrets or uncontrolled local data.

## 8. Exact Scope

Staging environment, database, secrets/configuration, deployment, migrations, object storage, workers, monitoring, smoke/E2E tests, backup restore drill, production-readiness evidence.

## 9. Out of Scope

Production cutover, unapproved feature work, architecture redesign, real customer data import, and bypassing release gates.

## 10. Architecture Context

Staging mirrors production topology sufficiently to reveal configuration, network, storage, worker, and migration problems before launch.

## 11. Implementation Sequence

Environment definition → isolated infrastructure → deploy/migrate → storage/workers/monitoring → smoke/E2E → restore drill → readiness review.

## 12. Detailed Task List

### S9-01 Staging environment and configuration

- Objective: define reproducible staging infrastructure and configuration.
- Why it exists: local success does not prove deployability.
- Dependencies: Phase 8 DoD, explicit task confirmation.
- Files to create/modify: deployment manifests, environment templates, CI workflow, runbooks; never secrets.
- Steps: define Cloudflare Pages frontend staging, Render backend staging, Render PostgreSQL staging, private Cloudflare R2/S3-compatible storage, worker choice (Django-Q or Celery + Redis), domains, network, resource limits, secret references, CORS/hosts, logging, data policy, and access roles.
- Database/API/security impact: staging-only configuration and isolation.
- Tests: configuration validation and secret reference checks.
- Validation: dry-run/deployment plan.
- Documentation: staging runbook, state, handoff.
- DoD: reviewed reproducible plan.

### S9-02 Deploy, migrations, storage, and workers

- Objective: deploy immutable artifacts and initialize dependencies safely.
- Why it exists: runtime coordination is a release risk.
- Dependencies: S9-01, explicit task confirmation.
- Files: deployment scripts/manifests, migration/job/storage runbooks.
- Steps: deploy app, run forward migrations, configure private object storage, start workers/schedulers, verify health/readiness, record versions.
- Database: staging DB migrations only; backup first.
- API/security: TLS, secrets, service accounts, worker permissions.
- Tests: migration, storage upload/download authorization, job execution.
- Validation: health checks and logs.
- Docs: deployment/database/security/handoff.
- DoD: staging services healthy and isolated.

### S9-03 Smoke and end-to-end validation

- Objective: validate the approved integrated workflow in staging.
- Why it exists: production-like behavior must be proven before launch.
- Dependencies: S9-02, explicit task confirmation.
- Files: smoke/E2E configuration and runbook.
- Steps: validate Supplier → Back Office → Shop → Client → Work → Design → Measurement → Fabric → Production → Completion → Billing → Reports; test Shop A/B denial, files, jobs, reports, monitoring.
- Database/API/security impact: controlled test data only.
- Tests: smoke/E2E/security checks.
- Validation: artifacts and pass/fail evidence.
- Docs: release report, state, handoff.
- DoD: no critical staging failures.

### S9-04 Backup restore drill and readiness review

- Objective: prove recovery and document production readiness.
- Why it exists: deployment is incomplete without recoverability.
- Dependencies: S9-03, explicit task confirmation.
- Files: backup/restore scripts/runbooks, readiness checklist.
- Steps: backup DB/object metadata, restore isolated staging, verify migrations/files/jobs/audit, measure recovery objectives, review unresolved risks.
- Database: restore verification only.
- Security: access controlled and secrets rotated where appropriate.
- Tests: restore and integrity checks.
- Validation: signed/evidenced readiness review.
- Docs: handoff, operations, state, changelog.
- DoD: staging and recovery evidence accepted.

## 13. Task Dependency Graph

`S9-01 → S9-02 → S9-03 → S9-04`.

## 14. Expected Files / Folders

Cloudflare Pages and Render deployment manifests/workflows, environment templates, staging runbooks, smoke/E2E configuration, backup scripts.

## 15. Expected New Files

Staging configuration templates, CI jobs, runbooks, readiness/restore scripts and reports.

## 16. Expected Modified Files

Docker/deployment/CI/settings/docs files only as approved; never commit secrets.

## 17. Database Changes

Staging database creation/migrations, controlled seed/test data, backup/restore artifacts.

## 18. Migration Requirements

Forward migration rehearsal, backup before migrate, timing/locking record, restore validation.

## 19. API Changes

None expected; verify deployed schema/version and health endpoints.

## 20. Backend Changes

Deployment/configuration only; fix product defects through separately confirmed tasks.

## 21. Frontend Changes

Build/deploy configuration and smoke tests only.

## 22. Security Requirements

Separate staging secrets/data, TLS, least-privilege service accounts, private storage, restricted admin access, safe logs.

## 23. Tenant / Permission Requirements

Run cross-shop and supplier-visibility tests against deployed staging APIs, not just local mocks.

## 24. Validation Requirements

Deployment, health/readiness, migrations, storage, worker, monitoring, smoke, E2E, isolation, and restore checks.

## 25. Testing Requirements

Smoke, E2E, migration, file, job, security, backup/restore, and operational alert tests.

## 26. Error / Failure Handling

Abort rollout on failed migrations/health checks; preserve logs; provide rollback/runbook; avoid partial cutovers.

## 27. Documentation Updates

Update deployment/security/database/API/operations/state/handoff/changelog.

## 28. Git Checkpoint Guidance

Checkpoint manifests/runbooks locally; never push or expose secrets.

## 29. Handoff Requirements

Record environment, artifact/version, migrations, checks, incidents, recovery evidence, unresolved risks, and next task.

## 30. Phase Validation Checklist

- [ ] Staging is isolated
- [ ] Deployment and migrations pass
- [ ] Storage/workers/monitoring work
- [ ] End-to-end workflow passes
- [ ] Shop isolation passes
- [ ] Restore drill passes
- [ ] Readiness risks recorded

## 31. Definition of Done

A production-like staging environment runs the integrated product and has evidence for deployment, security, workflow, monitoring, and recovery readiness.

## 32. Common Implementation Mistakes

Reusing production secrets, skipping migration rehearsal, public storage, no worker monitoring, manual undocumented changes, testing only health endpoint.

## 33. Rollback / Recovery Notes

Use deployment rollback and documented migration recovery; restore isolated staging before retry; never improvise production changes.

## 34. Phase Implementation Prompt

**Implement ONLY this phase. Do not implement future phases.** Phase confirmation activates Phase 9 only; it does not authorize S9-01 through S9-04. Before each task, present its objective, affected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`. Implement only the confirmed task, validate it, update documentation, report the result, and stop. Do not begin the next task or Phase 10 automatically.

## 35. Phase Completion Report Format

`Phase: 9` / `Task confirmed:` / `Environment/artifact:` / `Migrations:` / `Smoke/E2E:` / `Monitoring:` / `Restore evidence:` / `Risks:` / `Docs updated:` / `Next task requires confirmation:`.
