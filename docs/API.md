# API

## Current starter state

The cloned starter contains partial backend/API scaffolding. It has Django URL configuration, DRF, JWT authentication, account endpoints, tenant endpoints, OpenAPI/Swagger routes, pagination/filtering configuration, serializers, and initial API tests. These are reusable starting components, not a complete SGTP V1 API.

Existing starter routes include `/api/v1/auth/`, `/api/v1/tenants/`, `/api/schema/`, and `/api/docs/`. Their current behavior and limitations are described in `docs/ARCHITECTURE.md` and `docs/PROJECT_STATE.md`.

## Target V1 application API

The complete V1 API does not yet exist. Implementation phases will refine the starter and add the approved supplier/back-office/shop, clients/related persons, catalog, works/production, billing, reports/PDF, storage/job, AI, and integration contracts under the canonical target architecture. Backend authorization, shop isolation, object permissions, workflow rules, and financial rules remain authoritative.

### Approved future contract requirements

- Preserve `/api/v1/` and document OpenAPI contracts, pagination, safe filters, machine-readable stable error codes, translated human display messages, and request/correlation IDs.
- T3-02A is implemented: login accepts the existing `email` field or `identifier` containing email/E.164 phone and authenticates the same UUID User. Refresh remains HttpOnly-cookie/CSRF protected, rotated and blacklisted; access/refresh credentials are versioned so password changes revoke sessions. Anonymous account creation is denied; Main Supplier Admin account creation returns a cryptographically generated initial password once with `Cache-Control: no-store`, and the user must change it before normal API use. Email recovery uses expiring single-use tokens and enumeration-resistant responses. User locale and appearance, plus nullable Shop locale/timezone/currency settings, are persisted. Shop settings appear in global Shop reads/writes only for Main Supplier Admin; ordinary authenticated serializers omit the new settings. No phone verification provider is included.

### T3-02A implemented endpoints

- `POST /api/v1/auth/login/`: accepts `{email, password}` (backward compatible) or `{identifier, password}` where identifier is an email or E.164 phone. Returns access token and user profile; refresh remains in the HttpOnly cookie. Authentication failures are generic.
- `POST /api/v1/auth/users/`: Main Supplier Admin only. Accepts email, names, optional E.164 phone. Returns account data and one generated initial password exactly once; response is no-store. Anonymous registration is denied.
- `GET /api/v1/auth/users/me/` and `PATCH /api/v1/auth/users/update_profile/`: authenticated self profile/preferences. Locale and appearance are writable; phone and account activation are not self-service fields.
- `PATCH /api/v1/auth/users/{uuid}/`: Main Supplier Admin may manage phone; ordinary users remain restricted to their own profile and cannot change phone.
- `POST /api/v1/auth/users/password/change/`: requires current password, validated matching new password, revokes existing sessions, and clears refresh cookie. An initial-credential user may access this operation while other protected API use is gated.
- `POST /api/v1/auth/password/reset/` and `/api/v1/auth/password/reset/confirm/`: email-based reset request has the same response regardless of account existence; confirmation requires the emailed UID/token and a valid new password. Reset links require configured `PASSWORD_RESET_URL` and email delivery settings.
- Shop/Tenant list and detail retain their existing routes. Only Main Supplier Admin serializers include `default_locale`, `default_timezone`, and `default_currency`; ordinary authenticated global reads do not expose them. This is not Shop-context implementation.
- Shop-scoped endpoints use `/shops/{shop_id}/...`; authorization precedes Shop default resolution. Preferences never grant access.
- Client search includes name, normalized phone and stable client ID; Work number becomes searchable when available. Duplicate response warns only and never merges silently.
- Payment writes require idempotency and explicit safe outcomes. Invoices/receipts/reports may accept a per-document locale override without changing canonical data or money.

## Future documentation requirements

For each implemented endpoint, record its method and path, authentication and authorization expectations, request and response shape, validation errors, side effects, idempotency behavior, pagination/filtering, and compatibility policy.
