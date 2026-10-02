# API

## Current starter state

The cloned starter contains partial backend/API scaffolding. It has Django URL configuration, DRF, JWT authentication, account endpoints, tenant endpoints, OpenAPI/Swagger routes, pagination/filtering configuration, serializers, and initial API tests. These are reusable starting components, not a complete SGTP V1 API.

Existing starter routes include `/api/v1/auth/`, `/api/v1/tenants/`, `/api/schema/`, and `/api/docs/`. Their current behavior and limitations are described in `docs/ARCHITECTURE.md` and `docs/PROJECT_STATE.md`.

## BACKOFFICE-01 Main Supplier integration

- Auth user representations from `POST /api/v1/auth/login/` and `GET /api/v1/auth/users/me/` include read-only `is_main_supplier_admin`. It is derived from an active superuser and is a frontend routing hint; authorization is still enforced by backend permissions.
- `GET /api/v1/tenants/` lists Shops for an authenticated account, with existing pagination, search, `is_active` filtering, and ordering. Main Supplier receives the global authorized Shop list.
- `GET /api/v1/tenants/{id}/` reads a Shop under existing authorization rules. Main Supplier receives the administrative detail representation.
- `POST /api/v1/tenants/` requires Main Supplier Admin authorization and the existing password-change gate. Required body: `name`, `slug`, positive `max_users`, and `first_admin` with `first_name`, email, and phone. Optional Shop profile fields follow `TenantAdminSerializer`. The transaction creates the Shop and its first ADMIN account/membership together.
- Successful creation returns the Shop representation plus `first_admin_user_code` and `initial_password` once, with `Cache-Control: no-store` and `Pragma: no-cache`. The first ADMIN can authenticate with that permanent User ID and initial password, then must change the password before ordinary protected API use.
- `PATCH /api/v1/tenants/{id}/` updates allowed Shop profile fields. `POST /api/v1/tenants/{id}/activate/` and `/deactivate/` use existing Main Supplier authorization and lifecycle rules. Shops are not deleted.

## Internal OpenAPI documentation portal

- `/api/docs/` serves the single interactive Swagger UI and `/api/schema/` serves its generated OpenAPI document. Both require a Django Admin session for an active Main Supplier superuser whose forced-password-change gate is clear. Anonymous visitors are redirected to the existing Admin login; authenticated non-Main-Supplier accounts receive a generic not-found response. The root path redirects to `/api/docs/` and does not serve a second API reference.
- `/api/browse/` provides a DRF-style endpoint browser for the same protected audience. It loads the implemented endpoint list from the protected OpenAPI schema, accepts an access JWT in a masked input, and sends same-origin requests only to `/api/v1/`. Replace path placeholders and supply request JSON as needed. The browser keeps the access JWT only in page memory, never Web Storage; it does not log tokens. The root path now redirects to this browser.
- Sign in through `/admin/login/` using the existing account. No documentation-specific password or permanent token is created. A valid documentation session only renders the docs portal; backend API requests still need the normal JWT and endpoint permissions.
- The documentation session is separate from business API authentication. Business API requests use the versioned JWT authenticator; a Django Admin session alone does not authenticate them. The browser includes the JWT as a Bearer header, never targets another origin, and preserves the existing CSRF bootstrap for unsafe methods and cookie-based refresh/logout. Swagger authorization persistence is disabled, and portal/docs/schema responses are private and non-cacheable.
- `/api-auth/` and the old `templates/api_test.html` starter page were removed after checking references. The Browsable API renderer remains available in development; it does not provide a session-login path.
- `schema.yml` is generated from the current `v1` backend routes and validated with drf-spectacular. It includes implemented APIs, including T4-01 Clients/Related Persons and T4-02 Catalog/Design contracts; it does not invent later endpoints.

## T4-02 catalog and design contract

- Global catalog defaults and global design templates are Main Supplier-only. Shop-local catalog variants, styles, designs, and reference images use the explicit `/api/v1/shops/{shop_id}/...` context and never disclose another Shop's records.
- A Shop design may be published by an active Shop ADMIN or an active STAFF member assigned the `STITCHING` Work Function. “Tailor” is that assigned STAFF function, not a new access role. Global template publication remains Main Supplier-only.
- Published design versions are immutable. New drafts snapshot selected style names/translations/reference images; reusable StyleOption images remain source-linked and copies remain independent. Reference image bytes are private, served only through authorized endpoints, and accept JPEG/PNG/WebP uploads.
- **Confidentiality limitation:** this GitHub repository is public and the generated `schema.yml` is committed. Protecting the live `/api/schema/` route does not make the committed schema confidential. If API contract confidentiality is required, repository visibility or schema publication must be changed through an owner-approved action.

`GET /api/v1/auth/csrf/` is a public, non-authenticating bootstrap for credentialed browser clients. It issues the host-only CSRF cookie and returns a masked `csrf_token` with `Cache-Control: no-store`; it returns no access or refresh credential. Staging allows credentialed CORS only from `https://staging.birky.com`, and refresh/logout remain CSRF-protected.

## Target V1 application API

The complete V1 API does not yet exist. Implementation phases will refine the starter and add the approved supplier/back-office/shop, clients/related persons, catalog, works/production, billing, reports/PDF, storage/job, AI, and integration contracts under the canonical target architecture. Backend authorization, shop isolation, object permissions, workflow rules, and financial rules remain authoritative.

### Approved future contract requirements

- Preserve `/api/v1/` and document OpenAPI contracts, pagination, safe filters, machine-readable stable error codes, translated human display messages, and request/correlation IDs.
- Published authentication accepts legacy email login and `identifier` with User ID, email, or E.164 phone for the same UUID; normal account creation allows optional email/phone. Refresh remains HttpOnly-cookie/CSRF protected, rotated and blacklisted; credential changes revoke sessions. Initial credentials are generated and returned once with `Cache-Control: no-store`; email recovery is expiring/single-use and enumeration-resistant. No phone verification provider is included.
- **Published T3-04A identity contract:** permanent `user_code` is the User ID; UUID remains `id` and JWT `user_id`. Login accepts `identifier + password` for User ID, email, or phone; legacy `{email,password}` remains supported. Normal Users may omit email/phone. Main Supplier global management can reset credentials through the explicit generated-credential action; Shop Admins cannot.
- **Published T3-04B membership contract:** role changes, ADMIN hierarchy/cardinality, lifecycle, capacity, first-ADMIN creation, and User deactivation use transactional services. Published T3-04B-USER-SCOPE adds immutable owning-Shop identity and same-Shop account/membership operations. T3-04C Work Function endpoints are implemented and published with exact-SHA CI green. **Published T3-05:** authorized Shop discovery/profile/statistics; Main Supplier-only settings and lifecycle; no Shop DELETE; scoped exact User-ID member lookup; capacity lower-bound enforcement; and hardened Django Admin. Preserve `/api/v1/tenants/` compatibility. T3-05 commit `3d21a0943006cd866bc19bc728cbec05daae1630` passed exact-SHA Project State Validation run `36614638187`.
- **T3-04C Work Function contract (implemented):** `GET` and `PUT /api/v1/shops/{shop_id}/memberships/{membership_id}/functions/` read or replace the membership's function set. Only an active ADMIN of the selected Shop may use it; Main Supplier, STAFF, VIEWER, cross-Shop, removed, and unavailable membership access is denied without granting function-based authority. The set may be empty and accepts only the seven approved codes; duplicates/unknown values are validation errors. Response: `{membership_id, shop_id, functions}`. Functions never grant API permissions. Phase 4 still owns workflow-stage mapping; no workflow or assignment API is included.

### T3-02A implemented endpoints

- `POST /api/v1/auth/login/`: accepts `{email, password}` (backward compatible) or `{identifier, password}` where identifier is User ID, canonical email, or E.164 phone. Returns UUID and User ID in the profile; refresh remains in the HttpOnly cookie. Authentication failures are generic.
- `POST /api/v1/auth/users/`: Main Supplier Admin only. Accepts required first name, optional last name/email/E.164 phone. Generates the User ID and temporary password; returns both once with no-store headers. Anonymous registration is denied.
- `GET /api/v1/auth/users/me/` and `PATCH /api/v1/auth/users/update_profile/`: authenticated self profile/preferences. Locale and appearance are writable; phone and account activation are not self-service fields.
- `PATCH /api/v1/auth/users/{uuid}/`: Main Supplier Admin may manage phone; ordinary users remain restricted to their own profile and cannot change phone.
- `POST /api/v1/auth/users/password/change/`: requires current password, validated matching new password, revokes existing sessions, and clears refresh cookie. An initial-credential user may access this operation while other protected API use is gated.
- `POST /api/v1/auth/password/reset/` and `/api/v1/auth/password/reset/confirm/`: email-based reset request has the same response regardless of account existence; confirmation requires the emailed UID/token and a valid new password. Reset links require configured `PASSWORD_RESET_URL` and email delivery settings.
- `POST /api/v1/auth/users/{uuid}/reset-credentials/`: Main Supplier may reset credentials for the selected User. A Shop ADMIN may reset only a current same-Shop STAFF/VIEWER account. The generated temporary password is returned once with `Cache-Control: no-store` and `Pragma: no-cache`; sessions are revoked and password change is required. Global User DELETE is disabled; Django Admin's arbitrary password editor and delete action are disabled.
- Published T3-04B User-Scope account creation: `POST /api/v1/auth/users/` requires Main Supplier authority and explicit `shop`, `role`, and required `first_name`; it creates a new Shop-owned account and first membership atomically. `POST /api/v1/shops/{shop_id}/users/` derives the Shop from the authorized URL context and permits its Shop ADMIN to create only STAFF/VIEWER. Both return generated initial credentials once with `Cache-Control: no-store` / `Pragma: no-cache`. Existing account assignment/move is rejected; normal global list/read visibility is not added.
- Shop/Tenant list and detail retain `/api/v1/tenants/`. Main Supplier responses may include settings and management statistics; a same-Shop ADMIN may receive management statistics but not settings; STAFF/VIEWER receive neither. Ordinary reads are membership-scoped; inactive memberships see an inactive historical profile only. Shop update/settings are Main Supplier-only, generic lifecycle mutation and DELETE are unavailable. These T3-05 changes are published with exact-SHA CI green.
- `GET /api/v1/shops/{shop_id}/context/` is the T3-03 context contract. The UUID path selects exactly one Shop; after JWT authentication and the password-change gate, the endpoint resolves an active Shop and active membership or explicit Main Supplier authority. Response fields are `shop_id`, selected-Shop `role` (null for Main Supplier), and `is_main_supplier`; Shop defaults are not returned.
- T3-04C adds `GET`/`PUT /api/v1/shops/{shop_id}/memberships/{membership_id}/functions/`. PUT replaces the complete set using `{"functions":["SALES", "MEASUREMENT"]}` (empty list is allowed); both methods return the membership UUID, Shop UUID, and catalog-ordered code list. Shop-context authorization is required, followed by an active same-Shop ADMIN check; foreign, removed, or nonexistent memberships are indistinguishable. Work Functions are descriptive only.
- `GET /api/v1/tenants/{shop_id}/stats/` is available to Main Supplier for any Shop and to an active same-Shop ADMIN only; role-insufficient same-Shop requests receive 403 and foreign/nonexistent Shop requests are scoped to 404. `GET /api/v1/tenants/{shop_id}/member-lookup/?user_code=...` performs exact lookup only among current or removed membership history in the selected Shop and returns User ID/display name/role/status; it never attaches an account or searches the global User directory. These T3-05 endpoints are published with exact-SHA CI green.
- The account/login routes above implement the published T3-04A User-ID contract. T3-04B ADMIN membership lifecycle actions are published. Work Function management is implemented under T3-04C. Do not infer additional endpoint paths or response shapes.
- Foreign, unauthorized, inactive, soft-deleted, unavailable, and nonexistent Shop requests return the same `404` envelope/code (`shop_context_unavailable`) without revealing Shop existence. Unauthenticated, invalid, and revoked authentication retain `401`. Malformed UUIDs do not match the UUID route and return 404 at URL resolution.
- Shop-scoped endpoints use `/shops/{shop_id}/...`; authorization precedes Shop-default access. Preferences never grant access. T3-04 provides a trusted-context scoped queryset/write-ownership mixin and selected-Shop object permission contract. T4-01 Clients/Related Persons is the first business-resource API and adopts/tests these primitives; future routes must do likewise.
### T4-01 Clients and Related Persons (implemented)

All routes require authenticated, password-change-complete access and explicit authorized Shop context:

- `GET/POST /api/v1/shops/{shop_id}/clients/`
- `GET/PUT/PATCH/DELETE /api/v1/shops/{shop_id}/clients/{client_uuid}/`
- `GET/POST /api/v1/shops/{shop_id}/clients/{client_uuid}/related-persons/`
- `GET/PUT/PATCH/DELETE /api/v1/shops/{shop_id}/clients/{client_uuid}/related-persons/{related_person_uuid}/`

UUIDs are immutable identities; no Client code is returned. Lists use page-number pagination (`count`, `next`, `previous`, `results`), page size 20, and deterministic name/UUID ordering. Optional `search` performs Unicode-aware name containment, normalized-phone prefix matching, and exact UUID matching. Deleted records are omitted. Work-number search is not implemented until T4-04.

Create body: `{"name":"...","phone":"optional","email":"optional"}`. Updates accept the same fields; Shop/Primary Client ownership is server/path-derived. RelatedPerson responses also include `primary_client_id`; future Work billing stays owned by that Primary Client, with no billing routes or fields implemented.

Successful writes include `warnings`, e.g. `[{"code":"possible_duplicate","field":"phone","matches":[{"id":"<uuid>","name":"..."}]}]`. Warnings cover same-Shop records of the same type only, return at most 10 references, do not reject or merge, and never reveal another Shop. Contact updates return warnings only when phone/email changed. Empty warnings means no same-Shop duplicate was found.

Main Supplier and active same-Shop ADMIN have read/create/update/soft-delete. Active STAFF has read/create/update. Active VIEWER is read-only. Inactive/removed memberships have no operational access. Work Functions do not alter Client permissions. Foreign/missing record and nested-parent lookups are non-disclosing 404s. DELETE soft-deletes and returns 204; there is no restore endpoint.

Phone search normalization applies Unicode NFKC, maps Unicode decimal digits to ASCII, removes other characters, and preserves `+` only when it is the first non-whitespace character. No country/region is inferred. Email matching uses trimmed case-folded text; stored contact values are trimmed but are not rewritten to the search key. Client/RelatedPerson duplicates are allowed; there is no phone/email uniqueness constraint.
- Payment writes require idempotency and explicit safe outcomes. Invoices/receipts/reports may accept a per-document locale override without changing canonical data or money.

## Future documentation requirements

For each implemented endpoint, record its method and path, authentication and authorization expectations, request and response shape, validation errors, side effects, idempotency behavior, pagination/filtering, and compatibility policy.
