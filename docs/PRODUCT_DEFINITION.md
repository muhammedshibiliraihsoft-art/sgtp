# SGTP Target Final Product / Definition of Done

## What SGTP is

SGTP is the **Supplier-Centric Garment & Tailor Platform**. V1 is a complete integrated business system for a supplier that manages multiple tailoring shops. Tailor Management is the core V1 business module.

The product is not defined as a generic Django backend, a set of disconnected APIs, or a collection of screens. It must connect the business records and workflow so that a supplier and each authorized shop can operate their work from request through billing and history.

## Business hierarchy

```text
Supplier / Main Admin
        ↓
Supplier Back Office
        ↓
Shop A | Shop B | Shop C
        ↓
Each shop's isolated tailoring workspace
        ↓
Clients, Designs, Measurements, Fabric, Work, Billing, Reports
```

The supplier/main admin manages the back office and shop workspaces. Each shop is an isolated business workspace. Users may access only the shops and records permitted by their role and membership.

## Core V1 business flow

```text
Client Request
  → Design
  → Measurement
  → Fabric / Material
  → Cutting
  → Stitching
  → Check
  → Finishing
  → QC
  → Completed
  → Billing
  → Reports / History
```

The flow must be persisted, connected, auditable, and authorization-aware. A completed work item must be connectable to the client, design, measurements, materials, production history, billing, and reports.

## V1 contents

- Supplier/main-admin back office
- Isolated shop workspaces
- Custom-user authentication and secure token sessions
- Supplier, shop, membership, role, and object-level access controls
- Client management and V1-defined related-person management
- Designs and design-to-work relationships
- Measurements linked to the appropriate client/work context
- Fabric/material records linked to work
- Production work with controlled transitions through cutting, stitching, check, finishing, QC, and completion
- Billing connected to completed work
- Reports, history, and PDF output
- Secure persistent file/object storage
- Background jobs for work that should not block core operations
- Audit logging, security controls, automated API documentation, tests, CI, staging, production configuration, monitoring, and operational error handling

AI and third-party integrations are supporting systems only. They must be isolated behind controlled boundaries and must not be able to compromise or break the core workflow.

## Final expected user experience

The supplier/main admin can operate the back office, create and manage shops, and see permitted business information. Shop users enter their own workspace, manage clients and related persons, create or use designs and measurements, attach materials, progress work through authorized production stages, complete QC, issue billing, and review reports/history. Attempts to access another shop's data are denied by backend controls, not merely hidden by the frontend.

## Final technical capabilities

- Frontend: React, Vite, Tailwind CSS
- Backend: Django and Django REST Framework
- Database/ORM: PostgreSQL and Django ORM
- Authentication: custom User model with secure token authentication
- Authorization: tenant/shop isolation and object-level permissions
- Business logic: service layer with explicit workflow transitions
- Files: secure persistent object storage
- Async work: background jobs with retry/error handling where appropriate
- Governance: audit logging, tests, CI, monitoring, and automatic documentation

## Definition of Done

V1 is complete only when the integrated end-to-end journey is verified:

`Supplier → Back Office → Shop → Client → Work → Design → Measurement → Fabric → Production → Completion → Billing → Reports`

The final validation must demonstrate:

1. Supplier/main admin can use the back office.
2. Shops can operate isolated workspaces.
3. Shop data is isolated.
4. Authorized users can access only permitted records.
5. Clients and related persons follow V1 rules.
6. Designs, measurements, and materials work together.
7. Work follows the defined production workflow.
8. Billing is connected to completed work.
9. Reports and PDFs work correctly.
10. Files are stored securely and persistently.
11. Background tasks do not unnecessarily block core operations.
12. AI/integrations cannot break core business workflows.
13. Backend security controls are enforced and tested.
14. Critical business and security behavior is covered by tests and CI.
15. Staging and production configurations are functional.
16. Monitoring and error handling are operational.
17. Documentation reflects the actual implementation.

Running backends, frontends, individual APIs, individual pages, or isolated tests is not sufficient for V1 completion.

## V1 boundaries

The approved hierarchy and workflow are fixed for V1. New business modules, technology-stack changes, or direct AI/integration control of core operations require an explicit product decision and documentation update. This document is the target reference; implementation documents must be updated whenever a change affects the target.
