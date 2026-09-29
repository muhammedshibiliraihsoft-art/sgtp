# Security

## V1 roadmap security requirements

- Implemented in T3-02A: preserve User UUID/email identity; optional unique E.164 login phone without fabricated backfill; no anonymous self-registration; Main Supplier Admin controls global account creation and phone lifecycle. Generated initial passwords are hash-only at rest, returned once with `Cache-Control: no-store`, and require a password change before normal API use. Email recovery uses expiring single-use tokens and generic responses. Password change/reset increments `auth_version` and blacklists outstanding refresh tokens. Never log/store plaintext credentials. No OTP/SMS/WhatsApp/2FA provider is implemented.
- User/Shop locale and theme are never authorization inputs. Authorize Shop context before resolving its defaults; every preference/settings endpoint remains subject to object and tenant permissions.
- Staging uses isolated services, demo/test data and separate secrets at `staging.birky.com` / `api-staging.birky.com`; verify cookie SameSite/Secure, CSRF, Origin and credentialed CORS in a real browser. Never expose production credentials/data.
- Audit events may contain actor UUID, Shop, action, object identity, safe before/after fields, timestamp and request correlation only; exclude passwords, tokens, secrets and sensitive prompts. Logs must be secret-safe.
- Private reference files and generated documents remain Shop-scoped. Test wrong-Shop access, expiring links, upload validation and cross-Shop download denial.
- Retention, anonymization, account deletion and public host/domain policies must be settled before Production; unresolved items are listed in `docs/DECISIONS.md` as `BUSINESS DECISION REQUIRED`.

## Current starter state

The cloned starter contains partial security scaffolding: a custom email-based User, Django/DRF authentication, SimpleJWT access/refresh endpoints, session middleware, CSRF middleware, security middleware, CORS middleware, soft-delete/audit base-model fields, and production security settings. These controls are incomplete and have not established the full SGTP V1 security architecture.

The repository contains `TenantMember`/`ShopRolePolicy`, User API protections, Main Supplier Shop-write checks, membership lifecycle controls, an auth throttle scope, and a JWT blacklist application. T3-02A implements phone login, first-login password change, email reset, session invalidation, persisted preferences, and Main Supplier-only exposure of Shop defaults. T3-03 implements request-local URL-path Shop context after DRF authentication; foreign, unauthorized, inactive, deleted, unavailable, and nonexistent Shops receive a uniform 404, while authentication failures remain 401. T3-04 adds trusted-context queryset scoping, server-controlled Shop ownership on scoped create/update, and object-to-selected-Shop permission checks. No production business-resource endpoints exist yet; their adoption and endpoint-specific isolation proof remain required. Runtime token rotation/reuse and revocation paths are covered by tests; dependency presence alone is not runtime evidence.

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

T3-04 primitives do not automatically secure views that do not adopt them; no business-resource endpoints currently exist. Ordinary-user global Shop read visibility and Shop deletion semantics remain unresolved and are not inferred here. T3-02A grants no Shop Admin settings authority.

## Future review areas

- Secret and environment-variable handling
- Authentication, authorization, and tenant isolation
- CSRF, session, cookie, and security-header configuration
- Input validation, output encoding, and file-upload handling
- Dependency and supply-chain controls
- Database access and backups
- Logging, privacy, and incident response

Do not claim a control is enabled until it is implemented and verified.
