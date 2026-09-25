# API

## Current starter state

The cloned starter contains partial backend/API scaffolding. It has Django URL configuration, DRF, JWT authentication, account endpoints, tenant endpoints, OpenAPI/Swagger routes, pagination/filtering configuration, serializers, and initial API tests. These are reusable starting components, not a complete SGTP V1 API.

Existing starter routes include `/api/v1/auth/`, `/api/v1/tenants/`, `/api/schema/`, and `/api/docs/`. Their current behavior and limitations are described in `docs/ARCHITECTURE.md` and `docs/PROJECT_STATE.md`.

## Target V1 application API

The complete V1 API does not yet exist. Implementation phases will refine the starter and add the approved supplier/back-office/shop, clients/related persons, catalog, works/production, billing, reports/PDF, storage/job, AI, and integration contracts under the canonical target architecture. Backend authorization, shop isolation, object permissions, workflow rules, and financial rules remain authoritative.

## Future documentation requirements

For each implemented endpoint, record its method and path, authentication and authorization expectations, request and response shape, validation errors, side effects, idempotency behavior, pagination/filtering, and compatibility policy.
