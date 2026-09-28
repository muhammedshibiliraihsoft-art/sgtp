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

## 6. Business Rule Change Log

*   **Initial Creation**: Added confirmed rules for Membership Lifecycle, Shop Capacity, and Governance.
