# API

## Current starter state

The cloned starter contains partial backend/API scaffolding. It has Django URL configuration, DRF, JWT authentication, account endpoints, tenant endpoints, OpenAPI/Swagger routes, pagination/filtering configuration, serializers, and initial API tests. These are reusable starting components, not a complete SGTP V1 API.

Existing starter routes include `/api/v1/auth/`, `/api/v1/tenants/`, `/api/schema/`, and `/api/docs/`. Their current behavior and limitations are described in `docs/ARCHITECTURE.md` and `docs/PROJECT_STATE.md`.

## Target V1 application API

The complete V1 API does not yet exist. Implementation phases will refine the starter and add the approved supplier/back-office/shop, clients/related persons, catalog, works/production, billing, reports/PDF, storage/job, AI, and integration contracts under the canonical target architecture. Backend authorization, shop isolation, object permissions, workflow rules, and financial rules remain authoritative.

### Approved future contract requirements

- Preserve `/api/v1/` and document OpenAPI contracts, pagination, safe filters, machine-readable stable error codes, translated human display messages, and request/correlation IDs.
- Published authentication accepts legacy email login and `identifier` with User ID, email, or E.164 phone for the same UUID; normal account creation allows optional email/phone. Refresh remains HttpOnly-cookie/CSRF protected, rotated and blacklisted; credential changes revoke sessions. Initial credentials are generated and returned once with `Cache-Control: no-store`; email recovery is expiring/single-use and enumeration-resistant. No phone verification provider is included.
- **Published T3-04A identity contract:** permanent `user_code` is the User ID; UUID remains `id` and JWT `user_id`. Login accepts `identifier + password` for User ID, email, or phone; legacy `{email,password}` remains supported. Normal Users may omit email/phone. Main Supplier global management can reset credentials through the explicit generated-credential action; Shop Admins cannot. Exact User-ID membership lookup remains T3-05 and is not implemented.
- **Published T3-04B membership contract:** role changes, ADMIN hierarchy/cardinality, lifecycle, capacity, first-ADMIN creation, and User deactivation use transactional services. Published T3-04B-USER-SCOPE adds immutable owning-Shop identity and same-Shop account/membership operations; T3-04C remains gated by its own task plan and exact confirmation. **Remaining T3-05 Shop contract (not live):** ordinary Shop discovery is authorized-membership scoped; Main Supplier controls Shop activation/deactivation; ordinary Shop DELETE is unavailable; stats are limited to Main Supplier and that Shop's ADMIN. Preserve `/api/v1/tenants/` compatibility absent separately approved routing change.
- **Approved future Work Function contract (T3-04C, not live):** membership-scoped zero/many functions, Shop-local ADMIN management, no cross-Shop assignment; functions do not grant authorization. Phase 4 plans stage mapping; no function API is live.

### T3-02A implemented endpoints

- `POST /api/v1/auth/login/`: accepts `{email, password}` (backward compatible) or `{identifier, password}` where identifier is User ID, canonical email, or E.164 phone. Returns UUID and User ID in the profile; refresh remains in the HttpOnly cookie. Authentication failures are generic.
- `POST /api/v1/auth/users/`: Main Supplier Admin only. Accepts required first name, optional last name/email/E.164 phone. Generates the User ID and temporary password; returns both once with no-store headers. Anonymous registration is denied.
- `GET /api/v1/auth/users/me/` and `PATCH /api/v1/auth/users/update_profile/`: authenticated self profile/preferences. Locale and appearance are writable; phone and account activation are not self-service fields.
- `PATCH /api/v1/auth/users/{uuid}/`: Main Supplier Admin may manage phone; ordinary users remain restricted to their own profile and cannot change phone.
- `POST /api/v1/auth/users/password/change/`: requires current password, validated matching new password, revokes existing sessions, and clears refresh cookie. An initial-credential user may access this operation while other protected API use is gated.
- `POST /api/v1/auth/password/reset/` and `/api/v1/auth/password/reset/confirm/`: email-based reset request has the same response regardless of account existence; confirmation requires the emailed UID/token and a valid new password. Reset links require configured `PASSWORD_RESET_URL` and email delivery settings.
- `POST /api/v1/auth/users/{uuid}/reset-credentials/`: Main Supplier may reset credentials for the selected User. A Shop ADMIN may reset only a current same-Shop STAFF/VIEWER account. The generated temporary password is returned once with `Cache-Control: no-store` and `Pragma: no-cache`; sessions are revoked and password change is required. Global User DELETE is disabled; Django Admin's arbitrary password editor and delete action are disabled.
- Published T3-04B User-Scope account creation: `POST /api/v1/auth/users/` requires Main Supplier authority and explicit `shop`, `role`, and required `first_name`; it creates a new Shop-owned account and first membership atomically. `POST /api/v1/shops/{shop_id}/users/` derives the Shop from the authorized URL context and permits its Shop ADMIN to create only STAFF/VIEWER. Both return generated initial credentials once with `Cache-Control: no-store` / `Pragma: no-cache`. Existing account assignment/move is rejected; normal global list/read visibility is not added.
- Shop/Tenant list and detail retain their existing routes. Only Main Supplier Admin serializers include `default_locale`, `default_timezone`, and `default_currency`; ordinary authenticated global reads do not expose them. This is not Shop-context implementation.
- `GET /api/v1/shops/{shop_id}/context/` is the T3-03 context contract. The UUID path selects exactly one Shop; after JWT/session authentication and the password-change gate, the endpoint resolves an active Shop and active membership or explicit Main Supplier authority. Response fields are `shop_id`, selected-Shop `role` (null for Main Supplier), and `is_main_supplier`; Shop defaults are not returned.
- The account/login routes above implement the published T3-04A User-ID contract. T3-04B ADMIN membership lifecycle actions are published; authorized Shop listing/profile/stats and Work Function management remain assigned future scope. Do not infer new endpoint paths or response shapes in this rebaseline.
- Foreign, unauthorized, inactive, soft-deleted, unavailable, and nonexistent Shop requests return the same `404` envelope/code (`shop_context_unavailable`) without revealing Shop existence. Unauthenticated, invalid, and revoked authentication retain `401`. Malformed UUIDs do not match the UUID route and return 404 at URL resolution.
- Shop-scoped endpoints use `/shops/{shop_id}/...`; authorization precedes Shop-default access. Preferences never grant access. T3-04 now provides a trusted-context scoped queryset/write-ownership mixin and selected-Shop object permission contract. No business-resource endpoints exist yet; future routes must adopt and test these primitives.
- Client search includes name, normalized phone and stable client ID; Work number becomes searchable when available. Duplicate response warns only and never merges silently.
- Payment writes require idempotency and explicit safe outcomes. Invoices/receipts/reports may accept a per-document locale override without changing canonical data or money.

## Future documentation requirements

For each implemented endpoint, record its method and path, authentication and authorization expectations, request and response shape, validation errors, side effects, idempotency behavior, pagination/filtering, and compatibility policy.
