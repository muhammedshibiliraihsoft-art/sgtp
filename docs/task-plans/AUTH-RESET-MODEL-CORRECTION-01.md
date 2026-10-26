# AUTH-RESET-MODEL-CORRECTION-01

**Status:** Implemented locally on `main` — not committed or deployed  
**Branch:** `main` only  
**Scope:** Align account recovery and login eligibility with the approved transitional password + PIN model.  
**Non-goal:** No production deployment, branch migration, unrelated auth redesign, or broad audit.

> **Reading note:** The audit findings and proposed task below record the initial pre-approval understanding. Where they mention a “PIN-only” model or prior Viewer access/reset behavior, those statements are historical and superseded. The approved credential transition and implementation result below are authoritative: existing legacy passwords remain valid in the shared credential field, and Viewer sign-in is disabled without deleting records or hashes.

## Audit findings

1. **Email password reset conflicts with the PIN credential model.** The login page links to an email password-reset flow and the frontend asks for a new password. The backend email reset endpoints and tests are present. This conflicts with a PIN-only account credential and with the supplied task's rule that email self-service reset is not approved.
2. **Shop Admin recovery is already implemented.** A Shop Admin can submit a phone-based request; it does not change credentials until Back Office approval. Approval generates a temporary PIN, revokes existing sessions, and requires a credential change. Preserve this flow and its generic response, rate/abuse controls, transactional behavior, and tests; do not rebuild it.
3. **Staff recovery is already available through the Shop Admin's Team page and backend reset action.** The backend checks same-Shop authorization and returns a one-time temporary PIN. Restrict it to active STAFF; the current code also allows VIEWER.
4. **Viewer is currently a real authenticated read-only role.** Team creation requires a Login ID for both STAFF and VIEWER; both get a PIN, Viewer can sign in, and the UI offers Viewer PIN reset. This directly conflicts with the proposed rule that Viewer has no login credentials and cannot sign in. Enforcing that rule removes Viewer access to the app, not merely the reset option.
5. **Existing Viewer accounts and records must be preserved.** Do not delete users, memberships, or history. If approved, block authentication for active Viewer-only accounts using current membership state; retain their records and allow access again only after an authorized role change to STAFF/ADMIN. Confirm behavior for accounts with multiple active Shop memberships before implementation.

## Proposed task card

### Objective

Use the existing shared Login ID + credential field for both legacy passwords and six-digit PINs; self-service email password reset is not exposed; Shop Admin recovery is approval-based; Staff recovery is handled by the Shop Admin; Viewers have no sign-in access.

### In scope

- Remove the login-page email-reset entry point and the associated reset UI/API client.
- Remove or disable public email-reset request/confirm routes and their backend implementation/tests after checking for internal callers. Treat removal as an intentional API contract change and document it.
- Preserve the existing Shop Admin phone-request → Back Office approval flow; make only necessary copy/UX corrections, without changing its established protections.
- Limit Shop Admin-initiated credential reset to active same-Shop STAFF. Keep one-time temporary PIN display, session revocation, and forced PIN change.
- Remove Viewer Login ID/PIN creation and Viewer reset controls. Preserve Viewer role as read-only business-data access only if that access can be provided without account authentication; otherwise do not silently replace its current behavior.
- Reject login for Viewer-only memberships while preserving account, membership, and historical data. Define and test role-promotion/demotion and multi-Shop membership behavior.
- Keep existing eligible login aliases and all unrelated authentication protections (JWT/session versioning, CSRF, throttling, tenant isolation, password-change gate).

### Out of scope

- Changing Shop Admin PIN approval workflow or its Back Office authorization model.
- Deleting or bulk-mutating existing Viewer accounts, credential hashes, memberships, or records.
- Changing Main Supplier bootstrap credentials, JWT architecture, or general user lifecycle behavior.
- Production deployment, migrations to production, or work on any branch other than `main`.

## Acceptance criteria

- Login page offers only the approved PIN recovery path; no misleading email/password reset screen remains.
- Email reset endpoints are no longer publicly reachable (or are explicitly disabled with a tested response); no password-reset token can change an account PIN/password.
- Shop Admin phone recovery remains non-enumerating and does not alter a PIN until authorized Back Office approval; approval is atomic, one-time, revokes sessions, and requires PIN change.
- Shop Admin can reset active same-Shop STAFF but cannot reset VIEWER, ADMIN, inactive, or cross-Shop users.
- New Viewer creation does not issue login credentials; Viewer-only users cannot authenticate. Existing Viewer data is retained.
- Approved role transitions and multi-Shop membership behavior are explicit and covered by tests.
- No unrelated files/behavior are changed; relevant auth, permission, tenant-isolation, concurrency, and frontend tests pass.
- No schema migration unless implementation proves one is required; if needed, it must be additive/reversible and preserve all existing data.

## Verification plan

1. Add/update focused backend tests for reset endpoint removal/disablement, eligible login roles, Staff-only reset authorization, Shop Admin PIN approval safety, and role transitions.
2. Add/update frontend tests for login recovery navigation, Team role creation, and reset actions.
3. Run targeted auth/accounts/tenant tests and relevant frontend tests, then lint/typecheck/build as applicable.
4. Review the final diff for secrets, data deletion, tenant boundary changes, migrations, and unrelated scope.

## Approved credential transition

The user approved removal of Viewer sign-in, preservation of existing Viewer records, Staff reset by Shop Admin, Shop Admin recovery through Back Office, and removal of email self-service reset. The shared Login page and credential field remain unchanged. Legacy passwords continue working; newly created or reset login-enabled accounts use a six-digit temporary PIN in the existing Django password hash field. No existing credential is bulk-converted, no forced mass logout occurs, and no six-digit-only validation is added to the Login endpoint. PIN length/pattern checks remain limited to PIN creation/change operations.

Viewer-to-Staff promotion requires a Login ID when the Viewer has none; the promotion issues a one-time temporary PIN and revokes old sessions. Staff-to-Viewer demotion revokes sessions but preserves the stored credential hash and account/history. Existing Viewer-only accounts are denied sign-in without deleting or rewriting their credentials.

Email reset endpoints are intentionally removed from the public API; this is an approved API contract change. No production deployment is included.

## Implementation result

- Added an additive `login_enabled` field and data migration that disables Viewer-only accounts without changing password hashes or deleting accounts/history. The flag is checked during credential login, access-token authentication, and refresh, avoiding a membership query on every request.
- New Viewers receive no Login ID or usable password. Viewer-to-Staff promotion collects a Login ID when needed, creates a temporary six-digit PIN, and revokes previous sessions. Staff-to-Viewer demotion revokes sessions but retains the credential hash.
- Staff reset is restricted to the active same-Shop STAFF by their Shop ADMIN. The existing Shop Admin phone-request/Back Office approval flow remains intact.
- Removed email reset UI, client methods, public endpoints, related implementation, configuration, and published schema entries. The Login page appearance and shared credential input are unchanged; existing long passwords and new PINs use that same field.
- No production deploy, commit, or push was performed.

### Verification evidence

- Backend: 78 targeted account/reset/tenant tests passed; the updated existing-Viewer access-token denial test passed separately.
- Frontend: 29 focused tests passed; TypeScript typecheck and production build passed.
- Staging settings: 20 pytest tests passed.
- Django system check passed; `makemigrations --check --dry-run` reported no model drift.
- OpenAPI validation reported zero schema errors and existing warnings; fail-on-warn remains nonzero due to those warnings.
