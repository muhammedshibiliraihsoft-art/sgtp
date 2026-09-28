# Security

## V1 roadmap security requirements (planned, not yet implemented)

- Preserve User UUID identity; phone is normalized to E.164 and must not be fabricated for existing users. Never log/store plaintext passwords. Do not add OTP/SMS/WhatsApp/2FA providers without separate approval.
- User/Shop locale and theme are never authorization inputs. Authorize Shop context before resolving its defaults; every preference/settings endpoint remains subject to object and tenant permissions.
- Staging uses isolated services, demo/test data and separate secrets at `staging.birky.com` / `api-staging.birky.com`; verify cookie SameSite/Secure, CSRF, Origin and credentialed CORS in a real browser. Never expose production credentials/data.
- Audit events may contain actor UUID, Shop, action, object identity, safe before/after fields, timestamp and request correlation only; exclude passwords, tokens, secrets and sensitive prompts. Logs must be secret-safe.
- Private reference files and generated documents remain Shop-scoped. Test wrong-Shop access, expiring links, upload validation and cross-Shop download denial.
- Retention, anonymization, account deletion and public host/domain policies must be settled before Production; unresolved items are listed in `docs/DECISIONS.md` as `BUSINESS DECISION REQUIRED`.

## Current starter state

The cloned starter contains partial security scaffolding: a custom email-based User, Django/DRF authentication, SimpleJWT access/refresh endpoints, session middleware, CSRF middleware, security middleware, CORS middleware, soft-delete/audit base-model fields, and production security settings. These controls are incomplete and have not established the full SGTP V1 security architecture.

The repository now contains `TenantMember`/`ShopRolePolicy`, User API protections, Main Supplier Shop-write checks, membership lifecycle controls, an auth throttle scope, and a JWT blacklist application. T3-03 URL-path context and end-to-end Shop isolation are pending. The blacklist application's presence is configuration evidence; runtime token rotation/reuse behavior is separately covered by auth lifecycle tests. A control must not be treated as complete merely because a related dependency or middleware is present.

## Target V1 security architecture

The target security architecture will be built and verified by the implementation phases. It includes secure access/refresh-token handling with an HttpOnly/Secure refresh cookie, rotation and reuse detection, an approved CSRF strategy for cookie-authenticated state-changing requests, supplier/shop isolation, object-level permissions, secure private object storage, audit logging, rate limiting, safe errors, monitoring, and security testing. The complete target architecture does not yet exist in code.

## Verified T3-02 remediation controls

- Ordinary authenticated users cannot enumerate, modify, or delete other users through the User API. Self-profile updates remain available, while account activation state is not writable through the profile serializer.
- Shop write and activate/deactivate actions require the existing Main Supplier authority from `ShopRolePolicy`; Django `is_staff` alone is insufficient.
- Membership lifecycle state is not writable through generic PATCH/PUT. Deactivate, reactivate, remove, and undo actions remain the controlled lifecycle paths.
- Authentication throttling is wired to the `auth` scope for login, refresh, and logout and is covered by a non-mocked repeated-login test.

These controls do not establish T3-03 URL context or complete Shop isolation. Global User administration ownership, ordinary-user Shop read visibility, and Shop deletion semantics remain unresolved and are not inferred here.

## Future review areas

- Secret and environment-variable handling
- Authentication, authorization, and tenant isolation
- CSRF, session, cookie, and security-header configuration
- Input validation, output encoding, and file-upload handling
- Dependency and supply-chain controls
- Database access and backups
- Logging, privacy, and incident response

Do not claim a control is enabled until it is implemented and verified.
