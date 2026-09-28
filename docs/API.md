# API

## Current starter state

The cloned starter contains partial backend/API scaffolding. It has Django URL configuration, DRF, JWT authentication, account endpoints, tenant endpoints, OpenAPI/Swagger routes, pagination/filtering configuration, serializers, and initial API tests. These are reusable starting components, not a complete SGTP V1 API.

Existing starter routes include `/api/v1/auth/`, `/api/v1/tenants/`, `/api/schema/`, and `/api/docs/`. Their current behavior and limitations are described in `docs/ARCHITECTURE.md` and `docs/PROJECT_STATE.md`.

## Target V1 application API

The complete V1 API does not yet exist. Implementation phases will refine the starter and add the approved supplier/back-office/shop, clients/related persons, catalog, works/production, billing, reports/PDF, storage/job, AI, and integration contracts under the canonical target architecture. Backend authorization, shop isolation, object permissions, workflow rules, and financial rules remain authoritative.

### Approved future contract requirements

- Preserve `/api/v1/` and document OpenAPI contracts, pagination, safe filters, machine-readable stable error codes, translated human display messages, and request/correlation IDs.
- T3-02A plans one backward-compatible identifier-plus-password authentication flow for required email or an optional unique E.164 User login phone, both resolving to the same UUID User. Preserve refresh HttpOnly cookie, CSRF, rotation/blacklist/reuse protection, logout, throttling, and generic credential errors. The current SimpleJWT path authenticates email first; phone login is not implemented. Main Supplier Admin is the approved global account/phone-management authority; public self-registration is prohibited by policy, but the existing public create endpoint remains enabled pending T3-02A implementation. Password recovery is email-based; password change/reset revokes refresh sessions. Persisted User locale/appearance and explicit Shop locale/timezone/currency settings remain unimplemented.
- Shop-scoped endpoints use `/shops/{shop_id}/...`; authorization precedes Shop default resolution. Preferences never grant access.
- Client search includes name, normalized phone and stable client ID; Work number becomes searchable when available. Duplicate response warns only and never merges silently.
- Payment writes require idempotency and explicit safe outcomes. Invoices/receipts/reports may accept a per-document locale override without changing canonical data or money.

## Future documentation requirements

For each implemented endpoint, record its method and path, authentication and authorization expectations, request and response shape, validation errors, side effects, idempotency behavior, pagination/filtering, and compatibility policy.
