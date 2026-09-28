# SGTP Target Final Product / Definition of Done

## What SGTP is

SGTP is the **Supplier-Centric Garment & Tailor Platform**. V1 is a complete integrated business system for a supplier that manages multiple tailoring shops. Tailor Management is the core V1 business module.

> **Note on Naming & Branding:** BiRKy is the company; SGTP is the technical/internal project identifier. The customer-facing product brand is not yet decided. Do not invent a product brand or finalize public production domains/hostnames beyond the already approved environment decisions. Technical internal API paths (e.g. `/api/v1/`, `/shops/{shop_id}/`) are independent of branding and may proceed.

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

## V1 Supplier / Shop / External Supplier Model

This section is authoritative for V1 business meaning:

- V1 has exactly one top-level **Supplier / Main Admin**. V1 is not a multi-supplier SaaS platform.
- The hierarchy is **one Main Supplier / Main Admin → Supplier Back Office → multiple Shops**.
- A **Shop** is the actual business workspace and the tenant/isolation boundary.
- Shop-owned records include the Shop's users/memberships and permitted clients, related persons, designs, measurements, materials, works, production records, billing, reports/history, and external supplier records.
- An **External Supplier** is a shop-owned business-contact record. It is not the Main Supplier, a user, a tenant, a member, a role, or an authenticated system participant.
- External Suppliers have no login, dashboard, permissions, API account, or cross-shop visibility in V1.
- Each External Supplier record belongs to exactly one Shop. Similar real-world suppliers in different Shops are separate records; there is no global or shared supplier directory.
- Shop A data must never be exposed to Shop B through IDs, lists, search, filters, ordering, pagination, counts, aggregates, autocomplete, nested relations, foreign-key traversal, or URL manipulation.
- The Main Supplier / Main Admin may have explicitly authorized cross-shop operational visibility, but that does not make Shop data globally shared with Shop users.
- The existing starter `Tenant` model is a legacy technical input and must not automatically be interpreted as the Main Supplier, an External Supplier, a Shop, or a platform-wide multi-supplier tenant. Its compatibility mapping is governed by the Phase 3 T3-01 decision gate.

## V1 Account and Preference Policy

Confirmed business rules are maintained canonically in `docs/BUSINESS_RULES.md`. Public self-registration is prohibited; Main Supplier Admin is the current authority for global User account creation and management. Email is required, UUID remains permanent identity, and optional unique E.164 User login phone plus email authenticate the same account. Phone verification is not required in V1; phone lifecycle is controlled through authorized account management. Generated initial credentials require secure one-time handling and first-login change; recovery is email-based and credential changes revoke refresh sessions. The current public User-create endpoint remains existing code behavior and has not yet been changed. T3-02A remains a future implementation task, not completed work.

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
- International account phone support with email-or-phone login; persisted nullable preferred locale and Light/Dark/System appearance preferences (implementation remains future work).
- English (`en`), Arabic Kuwait (`ar-KW`), Bangla (`bn`), and Urdu (`ur`) UI localization, English fallback, Arabic/Urdu RTL, English/Bangla LTR, and mixed-direction field support.
- Shop default locale/timezone/currency settings and per-document language override, applied only after Shop authorization; canonical records and historical financial values remain unchanged by display locale.
- Client quick search and duplicate warnings without silent merge; measurement templates/history/compare; private design-reference gallery; Work priority/date indicators; advance/partial/final payments and outstanding balances.
- Multilingual invoices, receipts and reports/PDFs; V1 audit events, critical alerts, safe logging, error tracking and request correlation.
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
18. English/ar-KW/Bangla/Urdu localization, RTL/LTR and Light/Dark/System work without affecting authorization or canonical data.
19. Client search, measurement history/compare, private references, Work priority/dates, payment/outstanding, receipts and multilingual documents satisfy their approved rules.
20. V1 audit, alert, observability, privacy, backup and restore requirements are operational; retention policy is decided before Production.

## V1 release boundary

V1 is strict-first: Post-V1 work cannot begin until Phase 10 acceptance and all Definition of Done criteria above pass. Client review uses Staging (`staging.birky.com`), which is not Production. Client feedback enters normal planning and is not implementation authorization. The bounded Small Enhancement Lane is defined in `docs/POST_V1_ROADMAP.md`.

Running backends, frontends, individual APIs, individual pages, or isolated tests is not sufficient for V1 completion.

## V1 boundaries

The approved hierarchy and workflow are fixed for V1. New business modules, technology-stack changes, or direct AI/integration control of core operations require an explicit product decision and documentation update. This document is the target reference; implementation documents must be updated whenever a change affects the target.
