# Business Rules

## 1. Purpose
This file is the repository-level source of truth for approved business rules. Each business rule has a unique rule code, a clear name/title, its status, and its exact business meaning. Business rules must be strictly separated from technical implementation details. This document is not an implementation specification.

## 2. Rule Status Definitions
*   **CONFIRMED**: The business rule is approved and locked. It must be implemented and enforced by the application.
*   **BUSINESS DECISION REQUIRED**: Ambiguous behavior that requires explicit business approval before implementation.

---

## 3. Membership Business Rules

### BR-MEM-001 — Membership Lifecycle

**Status:** CONFIRMED

**Rule:**
The approved lifecycle for Shop Memberships is:

ACTIVE
  ↓ Deactivate
INACTIVE
  ↓ Reactivate
ACTIVE

INACTIVE
  ↓ Remove
REMOVED (Soft Delete)
  ↓ Undo within 5 seconds
Previous State


### BR-MEM-002 — Direct Active Removal Forbidden

**Status:** CONFIRMED

**Rule:**
An ACTIVE membership must NOT be removed directly. Removal is available only after the membership is INACTIVE.

**Allowed behavior:**
ACTIVE → Deactivate → INACTIVE → Remove

**Forbidden behavior:**
ACTIVE → Remove


### BR-MEM-003 — Inactive Membership Reactivation

**Status:** CONFIRMED

**Rule:**
An INACTIVE membership can be reactivated. Reactivation returns the membership to ACTIVE. The existing membership identity/history must be preserved.


### BR-MEM-004 — Removal Is Soft Delete

**Status:** CONFIRMED

**Rule:**
Removing an INACTIVE membership is a soft-delete operation. The membership must not be permanently deleted from the underlying historical record. REMOVED memberships are no longer part of normal membership behavior.


### BR-MEM-005 — Undo Window

**Status:** CONFIRMED

**Rule:**
After a membership is removed, an Undo opportunity exists for EXACTLY 5 seconds. After the 5-second period expires, Undo is no longer valid.


### BR-MEM-006 — Undo Restores Previous State

**Status:** CONFIRMED

**Rule:**
Undo restores the membership to its previous state. The previous state must be preserved so that restoration is accurate.

**Allowed behavior:**
For the currently approved flow, this will normally mean: REMOVED → INACTIVE.

---

## 4. Shop Capacity Business Rules

### BR-SHOP-001 — max_users Is Configurable

**Status:** CONFIRMED

**Rule:**
Shop max_users must be configurable/database-driven. It must NOT be represented as a fixed hard-coded business value. Do not define a fixed value such as 5, 10, 20, etc.


### BR-SHOP-002 — Active and Inactive Memberships Consume Capacity

**Status:** CONFIRMED

**Rule:**
Both ACTIVE and INACTIVE memberships count toward the Shop's max_users capacity.


### BR-SHOP-003 — Removed Memberships Do Not Consume Capacity

**Status:** CONFIRMED

**Rule:**
REMOVED / soft-deleted memberships do NOT count toward max_users. Removing an INACTIVE membership therefore frees one membership slot.


### BR-SHOP-004 — Capacity Count

**Status:** CONFIRMED

**Rule:**
Shop membership capacity is calculated as:
user_count =
ACTIVE memberships
+
INACTIVE memberships

REMOVED memberships are excluded.

---

## 5. Business Rule Governance

### BR-GOV-001 — Agents Must Not Invent Business Rules

**Status:** CONFIRMED

**Rule:**
If a future implementation encounters business meaning that is not covered by an approved business rule, the agent must stop and report: BUSINESS DECISION REQUIRED. Agents must not silently invent business behavior.


### BR-GOV-002 — Rule Codes Must Be Referenced

**Status:** CONFIRMED

**Rule:**
Technical tasks, implementation plans, tests, audits, and relevant documentation should reference the applicable Business Rule code (e.g., BR-MEM-002, BR-MEM-005, BR-SHOP-003).

**Allowed behavior:**
New business rules require:
1. a unique rule code
2. explicit business approval
3. an update to this Business Rules document

---

## 6. Approved V1 Account, Localization, and Tailoring Rules

### BR-ACC-001 — User Identity Preservation
**Status:** CONFIRMED
**Rule:** User UUID remains the primary identity and email remains required. Phone is an additional international identifier, normalized to E.164. Existing users without a phone remain valid; migrations must not fabricate phone values.

### BR-LOC-001 — Supported V1 Locales and Direction
**Status:** CONFIRMED
**Rule:** V1 UI supports English (`en`), Arabic Kuwait (`ar-KW`), Bangla (`bn`), and Urdu (`ur`). English is the fallback. Arabic and Urdu render RTL; English and Bangla render LTR. Mixed-direction values must be safely presented without altering canonical stored text.

### BR-LOC-002 — Locale Selection Precedence
**Status:** CONFIRMED
**Rule:** Locale precedence is persisted User preference, then the authorized Shop default, then English. A Shop default may be resolved only after the request is authorized for that Shop.

### BR-UX-001 — Appearance Preference Is Presentation Only
**Status:** CONFIRMED
**Rule:** User appearance preference is `system`, `light`, or `dark`, with `system` as default. It changes presentation only and must not affect identity, authorization, tenancy, workflow, stored business values, or calculations.

### BR-CLIENT-001 — Client Duplicate Warning
**Status:** CONFIRMED
**Rule:** A potential duplicate by phone or email is a warning, not an automatic merge. Duplicate checks and results are confined to the authorized Shop; concurrent writes must not silently merge records.

### BR-WORK-001 — Work Priority and Date Indicators
**Status:** CONFIRMED
**Rule:** V1 Work priorities are Normal, Urgent, and Very Urgent. Upcoming, due soon, due today, and overdue are derived date indicators, not workflow states. Exact due-soon threshold and date-cutoff semantics remain **BUSINESS DECISION REQUIRED** before implementation.

### BR-BILL-001 — Related Person Billing Owner
**Status:** CONFIRMED
**Rule:** The Primary Client owns billing for work belonging to a Related Person. Financial calculations use exact decimal-safe values; presentation locale cannot change stored monetary values.

### BR-DOC-001 — Document Language Override
**Status:** CONFIRMED
**Rule:** Invoice, receipt, or report language defaults to User preference, then authorized Shop default, then English. A user may select a per-document language override where authorized; this does not mutate canonical records or financial values.

### BR-GOV-003 — V1 Completion Gates Post-V1
**Status:** CONFIRMED
**Rule:** Post-V1 implementation may begin only after Phase 10 acceptance and the complete V1 Definition of Done pass. Client feedback and Staging review do not independently authorize implementation or production release.

### BR-ACC-002 — Global User Account Creation Authority
**Status:** CONFIRMED
**Rule:** Public self-registration is not allowed. For the current V1 foundation, only the Main Supplier Admin may create and manage global User accounts. Shop Admins do not receive global User-management authority. Any future Shop-scoped provisioning requires a separately approved authorization task. This policy is implemented by T3-02A; anonymous account creation is denied.

### BR-AUTH-001 — Email-or-Phone Login to One User Identity
**Status:** CONFIRMED
**Rule:** A User with a registered login phone may authenticate using either that phone or the required registered email plus the same password. Both identifiers authenticate the same User UUID; they must never create separate accounts or identities. Preserve existing email login. The eventual API uses one identifier concept and one coherent authentication/token flow.

### BR-PHONE-001 — User Login Phone Uniqueness and Representation
**Status:** CONFIRMED
**Rule:** User login phone is optional and existing Users without a phone remain valid. A phone used as a User login identifier belongs to only one User. Persist canonical international E.164 representation, support multiple countries with a maintained libphonenumber-compatible approach, and never infer a universal default region or fabricate/backfill a phone. This uniqueness rule applies only to User login phones, not Shop, Client, or External Supplier contact numbers.

### BR-PHONE-002 — User Login Phone Management
**Status:** CONFIRMED
**Rule:** For the current V1 foundation, adding, changing, or removing a User login phone is controlled through the authorized account-management flow, initially Main Supplier Admin. Ordinary Users do not receive unrestricted phone replacement/removal, and a phone is never silently reassigned between User UUIDs. Any enhanced change/reassignment workflow requires a separately approved task.

### BR-PHONE-003 — Phone Verification Is Not Required in V1
**Status:** CONFIRMED
**Rule:** V1 does not require OTP, SMS, WhatsApp, or 2FA phone verification. A phone registered through the authorized account-management flow may be used as a login identifier. No verification-provider infrastructure is authorized by this rule.

### BR-PASS-001 — Generated Initial Credential Safety
**Status:** CONFIRMED
**Rule:** When an authorized account creator uses a system-generated initial password, generate it with cryptographically secure randomness, store only the Django password hash, never persist or log plaintext, and expose plaintext at most once through an approved credential display/delivery flow. SMS/WhatsApp delivery is not approved.

### BR-PASS-002 — Change Generated Password at First Login
**Status:** CONFIRMED
**Rule:** A User created with a system-generated initial password must change it at first login. The application must persist enough state to distinguish that credential from a normal user-selected password.

### BR-PASS-003 — Email-Based Password Recovery
**Status:** CONFIRMED
**Rule:** V1 password recovery is email-based and uses secure, expiring, single-use semantics with generic responses that do not reveal account existence. Phone, SMS, and WhatsApp recovery are not part of V1.

### BR-PASS-004 — Revoke Refresh Sessions After Credential Change
**Status:** CONFIRMED
**Rule:** After a successful password change or reset, existing refresh-token sessions must be revoked. The User must authenticate again with the new password. Integrate with the existing SimpleJWT rotation/blacklist lifecycle; do not weaken it.

### BR-SHOP-005 — Explicit Shop Timezone
**Status:** CONFIRMED
**Rule:** Each Shop has an explicit timezone setting. Do not infer it from server, browser, company, IP, or Shop country. Until a concrete value is approved/configured, the data-model foundation may remain unset/null.

### BR-SHOP-006 — Explicit Shop Currency
**Status:** CONFIRMED
**Rule:** Each Shop has an explicit currency setting. Do not infer it from server/Shop country, locale, or browser. Do not invent an initial currency. Display currency must not alter canonical financial values. Currency changes after financial records exist remain BUSINESS DECISION REQUIRED.

### BR-SHOP-007 — Shop Settings Authority
**Status:** CONFIRMED
**Rule:** For the current V1 foundation, Main Supplier Admin may manage Shop-level locale, timezone, and currency settings. Shop Admins do not receive this authority under T3-02A; any scoped Shop Admin settings authority requires a separately approved authorization task.

### BR-LOC-003 — User Locale May Be Unset
**Status:** CONFIRMED
**Rule:** A User preferred locale may remain NULL until selected. Do not persist English merely as fallback. Resolve locale as User preference → authorized Shop default → English; consult a Shop default only after authorization. Locale never determines access.

## 7. Business Rule Change Log

*   **Initial Creation**: Added confirmed rules for Membership Lifecycle, Shop Capacity, and Governance.

*   **2026-09-28 — T3-02A business decision lock**: Added confirmed account-creation, unified email/phone identity, login-phone, generated-password/recovery/session, explicit Shop settings, and nullable locale rules. At the time, this recorded approved policy targets only; T3-02A was later separately implemented.

### BR-MEM-007 — Undo and Capacity Limits

**Status:** CONFIRMED

**Rule:**
Undo is valid only within the exact 5-second window. Current Shop capacity must be re-checked immediately before restoration. If current user_count < max_users, restore the same membership and previous state. If current user_count >= max_users, reject Undo and leave the membership REMOVED. Do not remove/deactivate another membership, and do not exceed max_users.

## 8. Environment and Deployment Rules

### BR-ENV-001 — V1 Environment Progression
**Status:** CONFIRMED
**Rule:** The approved V1 environment progression is LOCAL ? STAGING ? PRODUCTION. There is no separate Preview environment in V1. Client review and early non-production deployments use the Staging environment. Production is deferred until Phase 10.

### BR-ENV-002 — Staging Is Never Production
**Status:** CONFIRMED
**Rule:** Staging must always remain non-production with isolated PostgreSQL, isolated credentials, isolated object storage, demo/test data, and environment-tagged logs. Real production customer data, production payment credentials, production messaging credentials, and production secrets must never be used in Staging.
