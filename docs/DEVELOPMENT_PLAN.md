# Development Plan

This plan is subordinate to `docs/PRODUCT_DEFINITION.md`. It must preserve the supplier → back office → isolated shop hierarchy and the complete persisted production-to-billing workflow.

## Phase 0 — repository and product definition

- Preserve and inspect the original SGTP starter repository.
- Define the target final product, V1 boundaries, business hierarchy, workflow, and Definition of Done.
- Record starter reuse, contradictions, risks, and unresolved decisions.

## Phase 1 — foundation alignment and technical baseline

- Confirm the authoritative V1 requirements and entity/relationship model.
- Define supplier, shop, user membership, active-shop context, tenant isolation, and object-level authorization.
- Align Django settings, environment variables, PostgreSQL configuration, CORS, allowed hosts, token revocation, and production security.
- Establish dependency management, local/staging/production configuration, CI, baseline tests, API schema generation, and documentation maintenance.
- Establish the React + Vite + Tailwind frontend shell and its authenticated API boundary.
- Define service-layer, audit, persistent storage, background-job, monitoring, and error-handling boundaries.

Phase 1 is not implementation-ready until these decisions are reviewed against the target and the starter checks run successfully.

## Phase 2 — identity, supplier back office, and shop workspaces

- Complete authentication and authorization.
- Implement supplier/main-admin back-office capabilities.
- Implement shop creation, membership, active-shop selection, workspace isolation, and shop-level permissions.
- Prove cross-shop access denial with security and integration tests.

## Phase 3 — Tailor Management core workflow

- Implement clients and V1-related persons rules.
- Implement designs, measurements, fabric/material records, and their relationships.
- Implement persisted production work and authorized transitions:
  `Client Request → Design → Measurement → Fabric/Material → Cutting → Stitching → Check → Finishing → QC → Completed`.
- Add audit history and workflow transition tests.

## Phase 4 — billing, reports, files, and operations

- Connect billing to completed work.
- Implement reports/history and PDF generation.
- Add secure persistent object storage and asynchronous jobs where appropriate.
- Add monitoring, operational error handling, staging/production validation, and recovery checks.

## Phase 5 — integrated V1 validation

- Validate the complete journey end-to-end:
  `Supplier → Back Office → Shop → Client → Work → Design → Measurement → Fabric → Production → Completion → Billing → Reports`.
- Verify tenant isolation, object-level permissions, secure files, background jobs, AI/integration isolation, critical tests, CI, monitoring, staging, production, and documentation accuracy.
- Declare V1 complete only when the integrated business workflows operate together; module-level completion is insufficient.

## Out of scope for V1 unless explicitly added

- Unapproved business modules or changes to the supplier/shop hierarchy.
- AI or third-party integrations that can directly control or break core business workflows.
- Technology-stack replacement.
