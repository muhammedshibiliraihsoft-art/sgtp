# Security

## Internal API documentation

- `/api/docs/` and `/api/schema/` require an active Main Supplier superuser session through Django Admin. Forced-password-change accounts and ordinary Shop ADMIN/STAFF/VIEWER accounts are denied. Anonymous requests are sent to the existing Admin login without returning docs/schema content.
- `/api/browse/` uses the same portal gate. Business API calls from its browser UI require a Bearer access JWT and remain subject to existing endpoint/Shop permissions. The UI allows only same-origin `/api/v1/` requests, holds access JWT only in page memory, and does not write it to Web Storage or log it. Django Admin session authentication remains disabled for DRF business APIs; CSRF bootstrap and refresh/logout cookie protections are unchanged.
- Both responses use private, no-store cache controls. Swagger does not persist bearer authorization. Documentation visibility grants no business API authentication; application API requests retain their JWT and endpoint-specific authorization, Shop-context, and object-isolation checks.
- Root `/` redirects to the protected Browsable API portal; Swagger remains at `/api/docs/`. The stale public API test page and unused `/api-auth/` route were removed. Health probes remain available and return only minimal status.
- **Public repository limitation:** `schema.yml` is committed to the public GitHub repository, so its API paths and contract metadata remain publicly readable regardless of route protection. If that information must be confidential, repository visibility or the committed-schema publication strategy needs an owner-approved change. Endpoint secrecy does not replace authorization.

## V1 roadmap security requirements

- Published T3-04A, T3-04B remediation, and T3-04B-USER-SCOPE retain UUID identity, permanent immutable `user_code`, optional email/phone for normal Users, User ID/email/phone login aliases, required first name, Admin-grade contact safeguards, no anonymous self-registration, credential protections, refresh-session revocation, membership/Admin lifecycle protections, and one immutable owning Shop per ordinary account. T3-04B-USER-SCOPE commit `ed845e89d7656bf9d9e1e24f03b79e7de0d3bd9c` passed exact-SHA Project State Validation run `36591864481`.
- UUID and JWT `user_id` continue to identify the same account. Main Supplier reset returns a generated temporary password once with no-store headers, increments `auth_version`, blacklists refresh tokens, and forces password change. The published User-Scope implementation permits Shop ADMIN reset only for current same-Shop STAFF/VIEWER accounts; it does not provide global directory access. No OTP/SMS/WhatsApp/2FA provider is introduced.
- Existing T3-04B implementation preserves at least one active ADMIN in each owning Shop during global User deactivation; each Shop has 1–2 active ADMIN memberships; Shop Admin cannot alter ADMIN hierarchy. Global User hard deletion is not an ordinary V1 management action.
- Published T3-05: ordinary Users may discover only authorized Shops; no global User enumeration for Shop Admin; exact User-ID lookup returns only User ID and display name. Work Functions are membership-scoped descriptions of eligible work and never an authorization shortcut; cross-Shop assignment is denied. Django Admin is for Main Supplier/platform administration only and must not bypass Shop authority, capacity, ADMIN invariants, membership lifecycle, immutable relations, function ownership, or actor stamping. Exact-SHA Project State Validation run `36614638187` succeeded for commit `3d21a0943006cd866bc19bc728cbec05daae1630`.
- T3-04C implementation: Work Function GET/PUT is Shop-path scoped and additionally requires an active Shop ADMIN; Main Supplier does not gain this operational authority. Foreign, removed, or missing target memberships are non-disclosing. STAFF/VIEWER remain unable to manage the set, and assigning a function changes no role or permission. Changes are transactional, Shop-first locked, and actor-attributed; removed assignments retain soft-deleted history.
- Generated initial passwords are hash-only at rest, returned once with `Cache-Control: no-store`, and require a password change before normal API use. Existing email recovery uses expiring single-use tokens and generic responses. Password change/reset increments `auth_version` and blacklists outstanding refresh tokens. Never log/store plaintext credentials. No OTP/SMS/WhatsApp/2FA provider is implemented.
- User/Shop locale and theme are never authorization inputs. Authorize Shop context before resolving its defaults; every preference/settings endpoint remains subject to object and tenant permissions.
- Staging uses isolated services, synthetic data and separate secrets. Its current API is `https://birky-staging-api.onrender.com`; `staging.birky.com` and `api-staging.birky.com` remain reserved future targets, not verified or operational domains. T3-05A provider-hostname checks verified cookie SameSite/Secure/HttpOnly, CSRF, Origin/CORS, token lifecycle and Shop isolation; real-browser integration remains deferred until the frontend exists. Never expose production credentials/data.
- T3-05A staging settings fail closed unless DEBUG is false and CORS/CSRF origins are exactly `https://staging.birky.com`; allowed hosts include only explicitly configured hosts plus Render's validated injected service hostname. The staging DB connection is isolated and uses Render's internal connection string; secrets stay in provider storage. Recovery-email delivery is disabled to avoid writing reset tokens to shared logs.
- `GET /api/v1/auth/csrf/` returns only a masked CSRF token and sets the API-host cookie for an allowlisted credentialed browser origin. It does not authenticate the caller or return refresh/access tokens. Refresh/logout remain CSRF-protected; cookies remain host-only, Secure in staging, and SameSite=Lax. Full browser integration is deferred until the frontend staging task.
- Free staging has no DB backups, limited retention, an ephemeral web filesystem, and process-local throttling cache; do not treat it as durable, production-grade, or globally rate-limit coordinated. The staging reset command requires both `DJANGO_ENV=staging`, exact DB name `sgtp_staging`, and an explicit flag.
- Audit events may contain actor UUID, Shop, action, object identity, safe before/after fields, timestamp and request correlation only; exclude passwords, tokens, secrets and sensitive prompts. Logs must be secret-safe.
- Private reference files and generated documents remain Shop-scoped. Test wrong-Shop access, expiring links, upload validation and cross-Shop download denial.
- Retention, anonymization, account deletion and public host/domain policies must be settled before Production; unresolved items are listed in `docs/DECISIONS.md` as `BUSINESS DECISION REQUIRED`.

## Current starter state

The cloned starter contains partial security scaffolding: a custom email-based User, Django/DRF authentication, SimpleJWT access/refresh endpoints, session middleware, CSRF middleware, security middleware, CORS middleware, soft-delete/audit base-model fields, and production security settings. These controls are incomplete and have not established the full SGTP V1 security architecture.

The repository contains `TenantMember`/`ShopRolePolicy`, User API protections, Main Supplier Shop-write checks, membership lifecycle controls, an auth throttle scope, and a JWT blacklist application. T3-02A implements phone login, first-login password change, email reset, session invalidation, persisted preferences, and Main Supplier-only exposure of Shop defaults. T3-03 implements request-local URL-path Shop context after DRF authentication; foreign, unauthorized, inactive, deleted, unavailable, and nonexistent Shops receive a uniform 404, while authentication failures remain 401. T3-04 adds trusted-context queryset scoping, server-controlled Shop ownership on scoped create/update, and object-to-selected-Shop permission checks. T4-01 Clients/Related Persons, T4-02 Catalog/Design, and T4-03 Measurements/Materials adopt these primitives with endpoint-specific isolation tests. Work/Orders and later domains remain future work. Runtime token rotation/reuse and revocation paths are covered by tests; dependency presence alone is not runtime evidence.

## Target V1 security architecture

The target security architecture will be built and verified by the implementation phases. It includes secure access/refresh-token handling with an HttpOnly/Secure refresh cookie, rotation and reuse detection, an approved CSRF strategy for cookie-authenticated state-changing requests, supplier/shop isolation, object-level permissions, secure private object storage, audit logging, rate limiting, safe errors, monitoring, and security testing. The complete target architecture does not yet exist in code.

## Verified T3-02 remediation and T3-02A controls

- Ordinary authenticated users cannot enumerate or modify other users through the User API. Self-profile updates remain available, while account activation state is not writable through the profile serializer. Global account creation and phone lifecycle are Main Supplier Admin-only; anonymous self-registration is disabled.
- Shop write and activate/deactivate actions require the existing Main Supplier authority from `ShopRolePolicy`; Django `is_staff` alone is insufficient.
- Membership lifecycle state is not writable through generic PATCH/PUT. Deactivate, reactivate, remove, and undo actions remain the controlled lifecycle paths.
- Authentication throttling is wired to the `auth` scope for login, refresh, and logout and is covered by a non-mocked repeated-login test.
- Temporary account credentials are emitted once with no-store response headers; no plaintext credential is persisted. Forced first-login password change gates protected API operations.
- Email reset is enumeration-resistant and single-use. Successful password change/reset invalidates prior access tokens by auth-version and refresh tokens by blacklist.
- Ordinary globally authenticated Shop serializers omit Shop default locale/timezone/currency; Main Supplier Admin serializers manage and read them.

T3-04 primitives do not automatically secure views that do not adopt them. T4-01 Client and Related Person endpoints adopt explicit Shop context and tenant-scoped querysets; the role matrix is enforced independently of Work Functions. Main Supplier must select an authorized Shop in the URL. ADMIN/STAFF/VIEWER access is limited to active same-Shop membership; role-insufficient writes are denied and foreign object/parent reads use non-disclosing 404 behavior. Duplicate matching is restricted to the selected Shop and same record type; only safe same-Shop UUID/name references are returned.

The 2026-09-29 rebaseline resolves Shop policy: ordinary Shop discovery is membership-authorized; Shop DELETE is not a V1 operation (deactivate instead); Main Supplier alone manages Shop settings/lifecycle; stats are limited to Main Supplier and the Shop's ADMIN; max_users cannot be lowered below user_count. T3-05 implements and publishes these Shop-management controls; exact-SHA CI passed. T3-02A grants no Shop Admin settings authority.

## T4-03 measurement and material access

Every T4-03 request resolves an explicit Shop through the existing authenticated URL-path context. Measurement PII and history are available only to that Shop's ADMIN, Main Supplier operating inside that selected Shop, or active STAFF assigned the `MEASUREMENT` Work Function. The function is an additional eligibility check and cannot authorize a foreign/inactive membership. VIEWER and STAFF without the function are denied measurement access. Related Person measurement profiles remain nested under their Primary Client, retaining the existing billing-owner relationship without adding billing behavior. Foreign person/profile/set/definition objects are filtered to the selected Shop and return non-disclosing not-found responses.

Saved measurement sets, values, and label snapshots are immutable; history corrections create a new set/version. Definitions with history and Materials are archived rather than deleted. Measurement units must be explicitly `INCH` or `CM`; comparison never converts units. No frontend authorization assumption is permitted.

## T4-03A inventory authorization and integrity

Inventory uses the same explicit Shop context and Material access policy: Main Supplier must select a Shop; same-Shop ADMIN manages; STAFF/VIEWER read active items only; no Work Function grants mutation authority. Every detail, selector, movement, and mutation is constrained to that Shop, with foreign records returning non-disclosing not-found. Movement history is read-only; balance writes are limited to atomic services that append a ledger entry. Admin registration is inspection-only. No Work reservation, client-supplied Shop/actor/balance, frontend permission trust, or public inventory route is introduced.

## Future review areas

- Secret and environment-variable handling
- Authentication, authorization, and tenant isolation
- CSRF, session, cookie, and security-header configuration
- Input validation, output encoding, and file-upload handling
- Dependency and supply-chain controls
- Database access and backups
- Logging, privacy, and incident response

Do not claim a control is enabled until it is implemented and verified.
