# API

## Current starter state

The cloned starter contains partial backend/API scaffolding. It has Django URL configuration, DRF, JWT authentication, account endpoints, tenant endpoints, OpenAPI/Swagger routes, pagination/filtering configuration, serializers, and initial API tests. These are reusable starting components, not a complete SGTP V1 API.

Existing starter routes include `/api/v1/auth/`, `/api/v1/tenants/`, `/api/schema/`, and `/api/docs/`. Their current behavior and limitations are described in `docs/ARCHITECTURE.md` and `docs/PROJECT_STATE.md`.

## Target V1 application API

The complete V1 API does not yet exist. Implementation phases will refine the starter and add the approved supplier/back-office/shop, clients/related persons, catalog, works/production, billing, reports/PDF, storage/job, AI, and integration contracts under the canonical target architecture. Backend authorization, shop isolation, object permissions, workflow rules, and financial rules remain authoritative.

### Approved future contract requirements

- Preserve `/api/v1/` and document OpenAPI contracts, pagination, safe filters, machine-readable stable error codes, translated human display messages, and request/correlation IDs.
- Current T3-02A implementation remains email-centric: login accepts email or `identifier` containing email/E.164 phone for the same UUID; account creation requires email. Refresh remains HttpOnly-cookie/CSRF protected, rotated and blacklisted; credential changes revoke sessions. Initial credentials are generated and returned once with `Cache-Control: no-store`; email recovery is expiring/single-use and enumeration-resistant. No phone verification provider is included.
- **Approved future identity contract (T3-04A, not live):** universal permanent User ID login through `identifier + password`; optional email/phone for normal Users; both contacts required for active Shop ADMIN/Main Supplier accounts; preserve email-login compatibility for existing Users. Normal Users without email use controlled global-account recovery. Shop Admins cannot create global Users, enumerate the global directory, or reset another User's password. Exact User-ID membership lookup returns only User ID and display name. Do not document these as live endpoints until implemented and validated.
- **Approved future Shop contract (T3-04B/T3-05, not live):** ordinary Shop discovery is authorized-membership scoped; Main Supplier can access cross-Shop management. No ordinary Shop DELETE; explicit Main Supplier activation/deactivation preserves records/memberships. Stats are limited to Main Supplier and that Shop's ADMIN. Preserve `/api/v1/tenants/` compatibility absent separately approved routing change.
- **Approved future Work Function contract (T3-04C, not live):** membership-scoped zero/many functions, Shop-local ADMIN management, no cross-Shop assignment; functions do not grant authorization. Phase 4 plans stage mapping; no function API is live.

### T3-02A implemented endpoints

- `POST /api/v1/auth/login/`: accepts `{email, password}` (backward compatible) or `{identifier, password}` where identifier is an email or E.164 phone. Returns access token and user profile; refresh remains in the HttpOnly cookie. Authentication failures are generic.
- `POST /api/v1/auth/users/`: Main Supplier Admin only. Accepts email, names, optional E.164 phone. Returns account data and one generated initial password exactly once; response is no-store. Anonymous registration is denied.
- `GET /api/v1/auth/users/me/` and `PATCH /api/v1/auth/users/update_profile/`: authenticated self profile/preferences. Locale and appearance are writable; phone and account activation are not self-service fields.
- `PATCH /api/v1/auth/users/{uuid}/`: Main Supplier Admin may manage phone; ordinary users remain restricted to their own profile and cannot change phone.
- `POST /api/v1/auth/users/password/change/`: requires current password, validated matching new password, revokes existing sessions, and clears refresh cookie. An initial-credential user may access this operation while other protected API use is gated.
- `POST /api/v1/auth/password/reset/` and `/api/v1/auth/password/reset/confirm/`: email-based reset request has the same response regardless of account existence; confirmation requires the emailed UID/token and a valid new password. Reset links require configured `PASSWORD_RESET_URL` and email delivery settings.
- Shop/Tenant list and detail retain their existing routes. Only Main Supplier Admin serializers include `default_locale`, `default_timezone`, and `default_currency`; ordinary authenticated global reads do not expose them. This is not Shop-context implementation.
- `GET /api/v1/shops/{shop_id}/context/` is the T3-03 context contract. The UUID path selects exactly one Shop; after JWT/session authentication and the password-change gate, the endpoint resolves an active Shop and active membership or explicit Main Supplier authority. Response fields are `shop_id`, selected-Shop `role` (null for Main Supplier), and `is_main_supplier`; Shop defaults are not returned.
- The existing account/login and tenant/membership routes above remain the current API surface. The newly approved User-ID login, authorized Shop listing/profile/stats policy, ADMIN lifecycle actions, and Work Function management are target contracts only until their assigned tasks are implemented; do not infer new endpoint paths or response shapes in this rebaseline.
- Foreign, unauthorized, inactive, soft-deleted, unavailable, and nonexistent Shop requests return the same `404` envelope/code (`shop_context_unavailable`) without revealing Shop existence. Unauthenticated, invalid, and revoked authentication retain `401`. Malformed UUIDs do not match the UUID route and return 404 at URL resolution.
- Shop-scoped endpoints use `/shops/{shop_id}/...`; authorization precedes Shop-default access. Preferences never grant access. T3-04 now provides a trusted-context scoped queryset/write-ownership mixin and selected-Shop object permission contract. No business-resource endpoints exist yet; future routes must adopt and test these primitives.
- Client search includes name, normalized phone and stable client ID; Work number becomes searchable when available. Duplicate response warns only and never merges silently.
- Payment writes require idempotency and explicit safe outcomes. Invoices/receipts/reports may accept a per-document locale override without changing canonical data or money.

## Future documentation requirements

For each implemented endpoint, record its method and path, authentication and authorization expectations, request and response shape, validation errors, side effects, idempotency behavior, pagination/filtering, and compatibility policy.
