# Business Rules

## 1. Purpose
This file is the repository-level source of truth for approved business rules. Each business rule has a unique rule code, a clear name/title, its status, and its exact business meaning. Business rules must be strictly separated from technical implementation details. This document is not an implementation specification.

## 2. Rule Status Definitions
*   **CONFIRMED**: The business rule is approved and locked. It must be implemented and enforced by the application.
*   **BUSINESS DECISION REQUIRED**: Ambiguous behavior that requires explicit business approval before implementation.
*   **SUPERSEDED**: A previously approved rule has been replaced by a later explicitly approved rule; the historical rule remains traceable below.

Status records business approval, not implementation completion. A CONFIRMED rule may still be a target awaiting its assigned remediation task.

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
**Status:** SUPERSEDED by BR-ACC-003–BR-ACC-005 (2026-09-29)
**Historical rule:** User UUID remains the primary identity and email remains required. Phone is an additional international identifier, normalized to E.164. Existing users without a phone remain valid; migrations must not fabricate phone values.
**Current rule:** UUID remains the internal permanent database identity. A system-generated permanent User ID is the universal human-usable login identifier. Email and phone are optional for normal Shop Users and, when registered, may be alternative identifiers. Implemented locally by T3-04A; publication remains pending.

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

### BR-CLIENT-002 — Client and Related Person Access
**Status:** CONFIRMED
**Rule:** Main Supplier may read, create, update, and soft-delete Client and Related Person records only through an explicit authorized Shop context. An active Shop ADMIN has the same actions only in their own Shop. An active STAFF may read, create, and update those records in their own Shop but may not delete them. An active VIEWER is read-only in their own Shop. Inactive or removed memberships have no operational access. Work Functions do not grant or restrict these Client permissions; no SALES or other function is required. No Client tags or separate human-readable Client code are part of this V1 task; the immutable UUID is the stable API identifier. Related Person Work remains billed to the Primary Client under BR-BILL-001.

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
**Rule:** Public self-registration is not allowed. Main Supplier Admin retains global User-account authority and may create any approved Shop role. Shop Admins have no global User-management authority, but may create STAFF/VIEWER accounts only in their own Shop and reset only current same-Shop STAFF/VIEWER credentials. T3-04B-USER-SCOPE implements this Shop-scoped provisioning; anonymous account creation remains denied.

### BR-AUTH-001 — Email-or-Phone Login to One User Identity
**Status:** CONFIRMED
**Rule:** A User authenticates through one `identifier + password` flow. The identifier may be the permanent User ID, or a registered email/phone when present. Every identifier resolves to the same global User UUID and never creates a separate identity. Email-only existing login compatibility is preserved. Normal Users need no email or phone to log in by User ID. Admin-grade contact requirements are governed by BR-ACC-006. Implemented locally by T3-04A.

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
**Rule:** Admin-grade accounts with a registered email may use secure, expiring, single-use email recovery with generic responses that do not reveal account existence. A normal User without email recovery uses a controlled global-account reset process under Main Supplier/global User management. Shop Admins must not reset another User's global password. Phone, SMS, and WhatsApp recovery are not part of V1. Implemented locally by T3-04A.

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

## 6A. Phase 3 Business Architecture Rebaseline — Approved Target Rules

These are authoritative business rules. Implementation status is recorded separately in `docs/PROJECT_STATE.md`, `docs/HANDOFF.md`, and the Phase 3 playbook; status notes below do not alter rule meaning.

### BR-ACC-003 — One Global User Across Shops (SUPERSEDED)
**Status:** SUPERSEDED
**Rule:** Historical 2026-09-29 target: one person had one global User UUID and could hold memberships in multiple Shops. The approved T3-04B User-Scope decision below supersedes this rule: each ordinary account is permanently owned by exactly one Shop. Preserve UUID and authentication compatibility while applying the new scope.

### BR-ACC-004 — Permanent Human-Usable User ID
**Status:** CONFIRMED
**Rule:** Every User has a system-generated, globally unique, permanent, role-neutral and Shop-neutral User ID. It is the universal human-usable login identifier and must not encode mutable role, Shop, or brand meaning. Preserve UUID as internal database identity. T3-04A is published; existing-user migration is guarded by a name/contact/email preflight.

### BR-ACC-005 — Normal User Contact Optionality
**Status:** CONFIRMED
**Rule:** A normal Shop User requires User ID and password; email and phone are optional. Registered email or phone may be an alternative login identifier for the same UUID. Never fabricate contact data. T3-04A is published.

### BR-ACC-006 — Admin-Grade Account Contacts
**Status:** CONFIRMED
**Rule:** An active Shop ADMIN and the Main Supplier/Main Admin require User ID, password, email, and phone. T3-04A implements Main Supplier account validation and prevents required-contact removal while a User has an active ADMIN membership. T3-04B enforces the contact rule on Shop creation, ADMIN promotion/reactivation, and global User lifecycle. No OTP/SMS/WhatsApp/2FA provider is implied.

### BR-ACC-007 — Global Account and Credential Authority
**Status:** CONFIRMED
**Rule:** Public signup remains disabled. Main Supplier may create Shop-owned accounts with any approved role. A Shop ADMIN may create STAFF/VIEWER accounts only in their own Shop and reset credentials only for that Shop's current STAFF/VIEWER accounts. Ordinary accounts cannot be attached to another Shop or found through a global User directory. Main Supplier controls global credential reset. Exact User-ID lookup for membership operations remains separately scoped future work. Initial credentials are returned once with no-store headers.

### BR-ACC-008 — Human Display Name
**Status:** CONFIRMED
**Rule:** `first_name` is required and nonblank after trimming; `last_name` is optional. Display name is `first_name` or `first_name + " " + last_name` when present. Do not add a separate `display_name` field or use email, phone, UUID, or User ID as a normal display fallback. Preflight existing users and never fabricate names. T3-04A is published; migration stops if existing rows lack a usable first name.

### BR-MEM-008 — Membership-Scoped Access Role
**Status:** CONFIRMED
**Rule:** Each ordinary account has one membership in its owning Shop, with access role ADMIN, STAFF, or VIEWER. Do not add OWNER or use business jobs such as TAILOR, SALESMAN, CASHIER, or CUTTER as access roles. The historical multi-Shop membership assumption in this rule was superseded by T3-04B User-Scope; its approved role catalog remains unchanged.

### BR-MEM-009 — Active Shop ADMIN Cardinality
**Status:** CONFIRMED
**Rule:** Each Shop must have at least one and no more than two ACTIVE ADMIN memberships. Inactive or removed memberships do not consume an active-ADMIN slot. Any operation leaving zero or three active ADMINs is invalid. T3-04B remediation enforces this invariant.

### BR-MEM-010 — ADMIN Authority and Shop Creation
**Status:** CONFIRMED
**Rule:** Main Supplier manages ADMIN assignment, promotion, demotion and removal, while preserving the 1–2 active ADMIN invariant. Shop Admins cannot change another membership's ADMIN authority. Shop creation must atomically establish its first valid ADMIN before the Shop enters normal operation. Shop Admins may manage permitted non-ADMIN memberships and Work Functions only within their own Shop. ADMIN lifecycle and first-ADMIN safeguards are published in T3-04B remediation and T3-04B-USER-SCOPE; membership Work-Function management is implemented in T3-04C.

### BR-MEM-011 — Global User Deactivation Guard
**Status:** CONFIRMED
**Rule:** Reject global User deactivation if it would leave any Shop with zero active ADMIN memberships. Establish a replacement ADMIN first. Global hard deletion is not an ordinary V1 management action; preserve history through deactivation. The safeguard is published in T3-04B remediation; no global hard-delete behavior is added.

### BR-MEM-012 — Membership Capacity Lower Bound
**Status:** CONFIRMED
**Rule:** `user_count` remains ACTIVE + INACTIVE memberships; REMOVED memberships do not count. Reject any reduction of `max_users` below current `user_count`; first remove memberships through the approved lifecycle. API and Django Admin must enforce the same rule. **Implementation status:** T3-05 is implemented and published; exact-SHA Project State Validation run `36614638187` succeeded for commit `3d21a0943006cd866bc19bc728cbec05daae1630`.

### BR-SHOP-008 — Authorized Shop Visibility
**Status:** CONFIRMED
**Rule:** Ordinary Users may discover only Shops for which they have authorized membership/access, including list, detail, search, filters, ordering, pagination, stats, autocomplete, counts, foreign-key traversal and direct IDs. A User with a relevant inactive membership may see that Shop only as disabled/inactive historical context, never as selectable operational context. Main Supplier retains authorized cross-Shop visibility. Preserve T3-03/T3-04 non-disclosure and isolation. **Implementation status:** T3-05 is implemented and published; exact-SHA Project State Validation run `36614638187` succeeded for commit `3d21a0943006cd866bc19bc728cbec05daae1630`.

### BR-SHOP-009 — Shop Deactivation and Delete
**Status:** CONFIRMED
**Rule:** Only Main Supplier manages Shop activation/deactivation. Deactivation preserves Shop data, memberships and history, and makes operational context unavailable until reactivation. V1 does not expose ordinary Shop DELETE; deactivate is the operational shutdown action. Archive is a separate future concept. **Implementation status:** T3-05 is implemented and published; exact-SHA Project State Validation run `36614638187` succeeded for commit `3d21a0943006cd866bc19bc728cbec05daae1630`.

### BR-SHOP-010 — Shop Profile and Management Statistics Visibility
**Status:** CONFIRMED
**Rule:** Main Supplier may view Shops cross-Shop. An authorized Shop member may view appropriate profile/contact/address information for that Shop only. Management statistics (`user_count`, `max_users`, capacity state) are limited to Main Supplier and that Shop's ADMIN; they are not exposed to STAFF/VIEWER or foreign Shops. **Implementation status:** T3-05 is implemented and published; exact-SHA Project State Validation run `36614638187` succeeded for commit `3d21a0943006cd866bc19bc728cbec05daae1630`.

### BR-FUNC-001 — Work Functions Are Membership-Scoped and Not Permissions
**Status:** CONFIRMED
**Rule:** A membership may have zero, one, or multiple Work Functions, independently of its access role. The controlled V1 catalog is SALES, MEASUREMENT, CUTTING, STITCHING, FINISHING, QC, and CASHIER. Functions are managed by that Shop's ADMINs, including for ADMIN memberships, but never across Shops. A function describes work eligibility; it does not grant permissions or override endpoint/service authorization. A VIEWER does not gain operational/write authority from a descriptive function; Phase 4 must define the action policy without treating a function as sufficient authorization. Main Supplier cross-Shop administrative authority does not automatically create operational membership or Work Functions in every Shop. Membership deactivation preserves functions; reactivation restores eligibility; removal/undo preserves associated history; fresh re-add requires explicit assignment. The membership-scoped persistence and Shop-local management foundation is implemented by T3-04C. Any distinct function for the Check workflow stage remains a Phase 4 mapping decision.

### BR-FLOW-001 — Fixed Workflow, Flexible Staffing
**Status:** CONFIRMED
**Rule:** Keep the approved V1 tailoring workflow canonical and stable. Shops vary in which eligible memberships perform stages, not by creating independent workflow engines. Future stage assignment may associate a stage with eligible Work Functions and Shop memberships, with optional specific User assignment. Work Function eligibility alone is not final authorization. Implementation planning belongs to Phase 4; no workflow builder is in V1.

### BR-ACC-009 — Shop-Owned Ordinary Accounts
**Status:** CONFIRMED
**Rule:** Every ordinary User account belongs permanently to exactly one Shop. Two accounts for the same real-world person in different Shops are independent identities with separate UUIDs, User IDs, credentials, and histories. Do not attach an existing account to another Shop. Main Supplier accounts are global and have no owning Shop. Email and phone remain globally unique where supplied. Existing data must be preflighted; migration must stop with actual conflicting/unowned account identifiers and must not fabricate assignments.

### BR-MEM-013 — Shop Account Creation and Authority
**Status:** CONFIRMED
**Rule:** Shop creation atomically creates its first Shop-owned ADMIN account and membership. Main Supplier may create an account with any approved Shop role. A Shop ADMIN may create only STAFF or VIEWER accounts in that ADMIN's own Shop and may reset credentials only for that Shop's current active STAFF/VIEWER. Existing accounts cannot be assigned as a first membership or moved between Shops. Preserve membership lifecycle and ADMIN invariants; account creation returns any generated initial password once with no-store headers.

## 7. Business Rule Change Log

*   **Initial Creation**: Added confirmed rules for Membership Lifecycle, Shop Capacity, and Governance.

*   **2026-09-28 — T3-02A business decision lock**: Added confirmed account-creation, unified email/phone identity, login-phone, generated-password/recovery/session, explicit Shop settings, and nullable locale rules. At the time, this recorded approved policy targets only; T3-02A was later separately implemented.

*   **2026-09-29 — Phase 3 business architecture rebaseline**: Superseded the required-email assumption and approved the global User/User ID, multi-Shop membership, ADMIN cardinality/authority, Work Function, Shop visibility/deactivation, and capacity rules above. The multi-Shop User assumptions are now superseded by BR-ACC-009/BR-MEM-013. Other policies remain as recorded and implementation status is in the project state.

### BR-MEM-007 — Undo and Capacity Limits

**Status:** CONFIRMED

**Rule:**
Undo is valid only within the exact 5-second window. Current Shop capacity must be re-checked immediately before restoration. If current user_count < max_users, restore the same membership and previous state. If current user_count >= max_users, reject Undo and leave the membership REMOVED. Do not remove/deactivate another membership, and do not exceed max_users.

## T4-03 implemented measurement and material contract

T4-03 implementation preserves these approved boundaries:

- A measurement profile belongs to exactly one Shop-owned Client or Related Person. A Related Person remains linked to its existing Primary Client, which remains the future billing owner; this task adds no billing model or behavior.
- Only the approved Men's Shirt and Kuwaiti Dishdasha system templates are seeded. Abaya and Darraa have no guessed complete mappings. Shop-created definitions are reusable only in their owning Shop and configured family/optional variant; they require an English canonical label, while English, ar-KW, Bangla, and Urdu labels may be stored. Stable codes identify definitions; labels are not identity.
- Measurement sets are immutable history. Corrections create a new version. Copies create independent values and retain source-set provenance. Values are partial, Decimal-based, and require an explicit `INCH` or `CM` unit; no default or implicit conversion exists. A comparison difference is returned only for matching units.
- Measurement access requires an active selected-Shop membership and role; STAFF additionally require `MEASUREMENT`. The function alone never authorizes access. Main Supplier operations remain bound to an explicitly selected Shop. VIEWER and unassigned STAFF cannot read measurements.
- In its original T4-03 scope, Material is an active/archived Shop-owned reference record only; T4-03A later adds inventory additively without changing Measurement ownership/history.

## T4-03A approved inventory rules

### BR-INV-001 — Canonical Shop-owned inventory identity
**Status:** CONFIRMED
**Rule:** Existing Material UUID is the sole item identity. Every inventory record belongs to exactly one Shop. Legacy Materials are not auto-classified and receive no inferred opening stock; enablement is explicit.

### BR-INV-002 — Explicit classification and units
**Status:** CONFIRMED
**Rule:** Categories are `FABRIC`, `BUTTON`, `ZIP`, `THREAD`, `HOOK`, `INTERLINING`, `OTHER`; units are `METRE`, `YARD`, `PIECE`, `ROLL`. No automatic conversion is allowed; PIECE/ROLL quantities are whole numbers. Shop/category/unit are immutable after movement history exists.

### BR-INV-003 — Ledger and balance integrity
**Status:** CONFIRMED
**Rule:** Every stock change is an immutable ledger movement paired atomically with a materialized balance. `On Hand - Reserved = Available`; on-hand/available cannot become negative. Balance starts at zero; direct edits and movement update/delete are forbidden. Corrections use compensating movements. Opening stock is explicit and recorded once; stock-in and authorized adjustments use positive quantities and a reason.

### BR-INV-004 — Inventory access and archive
**Status:** CONFIRMED
**Rule:** Main Supplier must use an explicit Shop path; Shop ADMIN manages same-Shop inventory/history; STAFF reads active inventory/availability only; VIEWER reads active inventory only. Foreign/unauthorized data is non-disclosing. Archived items are not selectable and cannot be archived with non-zero on-hand/reserved balance; authorized managers retain history access.

### BR-INV-005 — No premature Work or costing behavior
**Status:** CONFIRMED
**Rule:** Work-linked reservation, release, consumption, return, cutting, and allocation require the real Work aggregate and remain deferred. Inventory selection beside measurement UI is not measurement history and does not reserve/deduct stock. No cost, procurement, warehouse, lot, or valuation is added.

## 8. Environment and Deployment Rules

### BR-ENV-001 — V1 Environment Progression
**Status:** CONFIRMED
**Rule:** The approved V1 environment progression is LOCAL ? STAGING ? PRODUCTION. There is no separate Preview environment in V1. Client review and early non-production deployments use the Staging environment. Production is deferred until Phase 10.

### BR-ENV-002 — Staging Is Never Production
**Status:** CONFIRMED
**Rule:** Staging must always remain non-production with isolated PostgreSQL, isolated credentials, isolated object storage, demo/test data, and environment-tagged logs. Real production customer data, production payment credentials, production messaging credentials, and production secrets must never be used in Staging.
