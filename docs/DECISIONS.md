# Architectural Decisions

## 2026-10-25 — Approve bounded manual Super Admin financial purge

The user approved a Main Supplier Super Admin-only, manually initiated purge of
a selected Shop's complete issued invoice bundle. Require a reason and exact
invoice-number confirmation. Include the invoice, lines, linked payments,
credit notes/refunds, document metadata, and private files. Do not schedule or
automatically delete records. Keep all pre-existing financial audit and
idempotency records (including saved response snapshots) and retain Shop
invoice/credit-note sequence high-water values. Preserve a purge tombstone and
append an audit event. Storage deletion failure must leave financial rows
available and allow a safe retry. This is an explicit exception to normal
issued-history immutability, not a general Shop deletion permission or a
statutory retention/anonymization decision. Implementation and local test
status are recorded in `docs/PROJECT_STATE.md`; the migration remains
unapplied to the persistent application database.

## 2026-10-21 — Approve Phase 5 pricing, billing, and documents

The user approved the expanded one-task Phase 5 implementation plan and settled
the following business rules:

- Shop-specific Design price applies to global and Shop Designs. Price entry
  requires Shop `default_currency`; Work snapshots the selected price/currency
  at creation and later price edits do not change existing Work.
- ADMIN and STAFF with CASHIER function may manage Shop Design prices and
  financial records. A Work may have multiple invoices, with one currency per
  invoice. Drafts may be created at any Work stage; issuing or paying never
  advances production. Each payment is linked to one specified invoice, and
  overpayment is rejected.
- AUTO lines use a Work price snapshot when present. Manual lines contain
  description, quantity and unit price. Invoice-level discount is optional,
  fixed or percentage-based. Fixed discount is allocated proportionally across
  lines; minor-unit rounding uses `ROUND_HALF_UP` with the residual assigned to
  the final line. Optional invoice-level tax is applied after discount and
  rounded per line with `ROUND_HALF_UP`.
- Issue-time invoice numbers are sequential per Shop (`INV-000001`) and never
  reused after void. An unpaid issued invoice may be voided with a reason. A
  paid invoice is corrected with a linked partial/full credit note (`CN-000001`,
  sequential per Shop); record only refunds already transferred externally,
  linked to an actual payment. The app never transfers money.
- Currency freezes once a Shop Design price or financial history exists; a
  change needs an explicit reviewed migration. Amounts beyond currency
  minor-unit precision are rejected without implicit rounding.
- An explicit document-language override is allowed; the default is User
  preference, then authorized Shop locale, then English. Rendering locale does
  not alter canonical money.

Implementation and runtime status are maintained in `docs/PROJECT_STATE.md` and
the Phase 5 task plan. This approval records policy only; it does not assert
that migrations were applied to an application or shared database.

## 2026-10-22 — Standardize generated PDFs on portrait A5

All current PDF exports (Measurement worksheet, invoice, receipt, and credit
note) use portrait A5 pages. A compact layout is acceptable, but content must
wrap and continue onto additional A5 pages rather than clip or omit values.
Measurement worksheets are regenerated on request. Financial PDFs are
immutable: retain existing A4 renditions and generate the new A5 format as a
new layout version; do not rewrite historical files or financial source data.

## 2026-10-18 — Retire the active Garment Variant workflow

The user resolved the Variant business decision: active Variant selection,
management, and materialization are retired. Global and Shop bootstrap must
not require active Variant rows. Any retained Variant records/foreign keys are
temporary legacy support only for compatibility, immutable history, or safe
migration; they must not drive new active product behavior. Existing Variant
rules below are superseded where they authorize active Variant workflows.

Repository audit on local `main` and the sibling
`frontend/parallel-foundation` checkout found retirement incomplete: Variant
CRUD routes/services and a Variant management UI remain in `main`; Design
creation is family-level in the `main` backend but the `main` frontend still
exposes Variant selectors; the sibling backend still requires Variant for new
Designs and its Orders UI matches profiles by Variant; `WorkOrder.clean()` in
`main` still requires exact Design/Profile Variant equality; and catalog seed
migrations still materialize/use active Variants. No runtime database rows,
applied migration state, or deployed environment was queried. See the current
status and correction sequence in `docs/architecture/03-DEPENDENCY-IMPACT-MAP.md`.

**Implementation verification correction (2026-10-19):** the current dirty
`main` backend restricts Global/Shop Variant list/detail views to GET/HEAD/
OPTIONS and lifecycle views to OPTIONS; focused API tests assert mutation
requests return 405 while legacy reads remain available. Variant mutation
service functions and handler bodies still exist in source, but references are
confined to those method-restricted handlers and direct legacy service tests;
they are not reachable through the current HTTP contract. The separate
`main/frontend` Variant management UI remains stale/deprecated and is not the
supported frontend pairing. Migration `catalog.0025` repairs missing
Family-level baseline defaults without editing historical migrations; database
replay is not yet verified. The preceding audit text is historical, not a
statement that current local HTTP writes succeed.

## 2026-10-16 — T4-04 Work/Order cardinality and operating rules

User confirmed one garment per Work; two Shop-local calendar days for due
soon; a new `CHECK` Work Function; reassignment at every stage; and ADMIN or
SALES/MEASUREMENT STAFF creation. The local backend contract follows these
choices. Assignment and metadata changes are ADMIN-managed; an assigned stage
is advanced only by its eligible assignee. No billing, inventory consumption,
frontend or publication is included in this backend task.

## 2026-10-02 — Approve T4-03A Shop-scoped inventory foundation

The user approved `T4-03A — Inventory & Stock Foundation` as an additive Phase 4 task following the completed T4-03. The existing Material UUID remains canonical. Inventory category/unit are explicit, legacy Materials are not inferred or given opening stock, and all stock mutations require immutable ledger provenance plus atomic balance maintenance. Supported V1 categories are FABRIC/BUTTON/ZIP/THREAD/HOOK/INTERLINING/OTHER; units are METRE/YARD/PIECE/ROLL with no conversion. Work-linked allocation/reservation/consumption and financial costing remain deferred until their authorized domain tasks. See `docs/BUSINESS_RULES.md`, `docs/DATABASE.md`, and `docs/API.md` for exact contracts.

## 2026-09-25 — Establish repository-contained continuity

The repository will contain explicit agent instructions and persistent state, architecture, decision, plan, API, security, database, changelog, and handoff documents. This makes work transferable between agents and IDEs without relying on conversation history.

## 2026-09-25 — Record the project as uninitialized

Because the repository has no application code or requirements, the initial documents describe absence rather than assuming a Django architecture, database, API, or security model.

## 2026-09-25 — Adopt the SGTP V1 target product definition

SGTP V1 is the Supplier-Centric Garment & Tailor Platform, with Tailor Management as the core business module. The approved hierarchy is Supplier/Main Admin → Supplier Back Office → isolated Shop workspaces. The approved workflow runs from Client Request through Design, Measurement, Fabric/Material, Cutting, Stitching, Check, Finishing, QC, Completed, Billing, and Reports/History.

This decision expands the prior generic-starter planning context into an integrated product definition. It does not authorize implementation in this task and does not change the technology stack. The target and Definition of Done are maintained in `docs/PRODUCT_DEFINITION.md`.

## 2026-09-25 — Approve tenant context, billing ownership, and CSRF phase gate

- Tenant context resolution: use URL-path context in the form `/shops/{shop_id}/...`. T3-03 implemented and tested this approved mechanism; it must not be replaced by another context mechanism.
- Related Person billing ownership: the Primary Client owns billing for work belonging to a Related Person. R5-01 must enforce and test this rule.
- CSRF: protection is a fixed requirement for refresh-cookie flows. Phase 2 owns selection, implementation, and validation of the concrete CSRF mechanism; the mechanism must be explicitly documented and tested before Phase 2 is complete.

## 2026-09-27 – Product and Company Name Rule

The public company/product name has not been finalized as of this 2026-09-27 entry. Superseded in part by the 2026-09-28 decision below: the company is BiRKy; the customer-facing product brand remains undecided. "SGTP" is explicitly an internal project identifier.
- Do not invent a public product name or replace "SGTP" with an assumed brand name.
- Do not finalize production domains, subdomains, hostnames, or public URLs.
- Technical API paths (e.g., `/api/v1/`) and shop context paths (e.g., `/shops/{shop_id}/`) are permitted as they are separate from public branding.
- When public URL/domain naming becomes technically necessary for deployment or configuration, agents must halt and raise a **BUSINESS DECISION REQUIRED** prompt to the user, requesting:
  1. Final customer-facing product brand
  2. Preferred primary domain
  3. Public app/API hostname structure

## 2026-09-27 - Lock V1 Supplier / Shop / External Supplier model

- V1 has exactly one top-level Supplier / Main Admin.
- The single Main Supplier / Main Admin owns and manages multiple Shops.
- Shop is the actual tenant/workspace and isolation boundary.
- Each Shop may maintain its own External Supplier records.
- An External Supplier is a Shop-owned business record only. It is not a user, tenant, member, role, login participant, dashboard user, or system participant.
- External Supplier data belongs only to its owning Shop. Shop A must not see Shop B's External Supplier records.
- There is no multi-supplier SaaS model in V1.
- Do not create a global/shared External Supplier directory.
- The existence of External Suppliers does not justify platform-level Supplier tenancy.

## 2026-09-28 — Approve V1 localization, appearance, and workflow requirements

The following are approved V1 product requirements mapped in `docs/DEVELOPMENT_PLAN.md` and the phase playbooks. This records target requirements, not completed implementation:

- Supported UI locales: English (`en`), Arabic Kuwait (`ar-KW`), Bangla (`bn`), and Urdu (`ur`), with English fallback; Arabic/Urdu use RTL and English/Bangla LTR, including mixed-direction fields.
- User preferred locale is nullable until selected; precedence is User preference → authorized Shop default → English. Shop authorization must occur before resolving Shop defaults.
- User appearance is persisted as `system|light|dark`, default `system`; presentation choices never affect access, roles, tenancy, workflow, canonical data, or calculations.
- At the time of this 2026-09-28 entry, account target preserved required email and UUID with optional E.164 phone. The required-email target was superseded by the 2026-09-29 rebaseline below; T3-02A's implementation remains email-required pending T3-04A.
- V1 includes searchable Clients, duplicate warnings without silent merge, measurement templates/history/compare, private design references, Work priorities and derived delivery indicators, advance/partial/final payment support, outstanding balances, multilingual receipts/invoices/reports, audit/alerts/observability, and controlled Staging checkpoints as mapped in phase plans.
- Environment progression is LOCAL → STAGING → PRODUCTION. Client review uses Staging (`staging.birky.com` / `api-staging.birky.com`). Phase 9 reuses the same Staging for formal release-candidate validation. Phase 10 remains the sole Production gate.
- Strict V1-first: Post-V1 features remain gated until Phase 10 acceptance and the full V1 Definition of Done pass.

At the time of this 2026-09-28 entry, ordinary-user Shop read visibility and Shop delete/archive/deactivate were unresolved; they were resolved as target rules on 2026-09-29. Still unresolved: Shop Admin scoped settings authority; deployment defaults and public hostnames beyond approved environment configuration; currency changes after financial history; due-soon threshold/date cutoff; advance cancellation/refund, overpayment/allocation; notification channels; retention durations and anonymization. Account creation, phone, initial-password/recovery/session, Main Supplier Shop-settings authority, and locale/appearance policies are recorded below and in `docs/BUSINESS_RULES.md`.

## 2026-09-28 — V1 roadmap confirmation gate

`CONFIRM TASK V1-ROADMAP-UPDATE` authorizes documentation/roadmap changes only. It does not authorize T3-02A, T3-03, T3-05A, F7-01A implementation, application code, migrations, or deployment. Every future task retains its own explicit confirmation gate.

## 2026-09-28 — Approve V1 environment model and company naming

The approved V1 environment progression is LOCAL → STAGING → PRODUCTION. There is no separate Preview environment in V1. The single Staging environment serves both early client review and later Phase 9 formal release-candidate validation.

Company: BiRKy. Technical project name: SGTP. Customer-facing product brand: not yet decided.

Staging domains: `staging.birky.com` (frontend), `api-staging.birky.com` (backend). Production domains reserved: `app.birky.com` (frontend), `api.birky.com` (backend). Production is not provisioned until Phase 10.

T3-05A is renamed from "Backend Preview" to "Staging Backend Foundation". F7-01A is renamed from "Client Preview Frontend" to "Staging Frontend & Client Review Checkpoint". F7-01 and F7-01A may execute immediately after T3-05A in the dependency sequence.

This decision supersedes the earlier four-tier LOCAL → PREVIEW → STAGING → PRODUCTION model.

## 2026-09-28 — Lock T3-02A account, authentication, and preference business rules

Human-approved V1 decisions, recorded as confirmed rules in `docs/BUSINESS_RULES.md` (BR-ACC-002, BR-AUTH-001, BR-PHONE-001–003, BR-PASS-001–004, BR-SHOP-005–007, BR-LOC-003):

- Public self-registration is prohibited. Main Supplier Admin is the current authority for global User-account creation/management; Shop Admins receive no global authority. At the time of this 2026-09-28 decision, the unauthenticated create endpoint had not yet been disabled; T3-02A later implemented the denial.
- Email remains required and an email login identifier; UUID remains permanent identity. A registered optional E.164 phone may also log into the same UUID account with the same password. User login phones are unique to one User; this rule does not apply to Shop, Client, or External Supplier contact numbers.
- No V1 phone OTP/SMS/WhatsApp/2FA verification. Phone add/change/remove is controlled through the authorized account-management flow, initially Main Supplier Admin; no unrestricted self-service or silent reassignment.
- Generated initial passwords use cryptographic randomness, are stored only as hashes, are never logged/persisted in plaintext, and may be revealed once through an approved flow. Such credentials require password change at first login.
- V1 recovery is email-based, secure, expiring, single-use, and account-enumeration resistant. Successful password change/reset revokes existing refresh-token sessions.
- Every Shop has explicit timezone and currency settings; values are not inferred and may remain unset until configured. Display currency cannot change canonical financial values. Main Supplier Admin manages Shop settings in the current foundation; Shop Admin settings authority is not granted here.
- User locale may remain NULL; resolution is User preference → authorized Shop default → English. Appearance is `system|light|dark`, default `system`, and presentation-only.

This 2026-09-28 entry records a documentation/business-rule lock and did not itself implement the rules, disable the public create endpoint, create migrations, or authorize T3-02A or T3-03. T3-02A was later separately confirmed and implemented. Currency changes after financial history remain a separate business decision.

**Supersession note (2026-09-29):** The historical statement that email remains required is superseded by the approved Phase 3 business architecture rebaseline below. UUID remains the internal identity, but a permanent User ID becomes the universal login identifier; normal Shop Users may omit email and phone. T3-04A and T3-04B remediation are published. T3-02A's email/phone login compatibility and security lifecycle remain protected.

## 2026-09-28 — Clarify company and product naming

Company: BiRKy. Technical/internal project: SGTP. Customer-facing product brand: not yet decided.

## 2026-09-28 — Approve T3-03 Shop-context denial disclosure

- For `/api/v1/shops/{shop_id}/...` context authorization, foreign, unauthorized, inactive, soft-deleted, unavailable, and nonexistent Shops return one uniform non-disclosing 404 response.
- Unauthenticated, invalid, and revoked authentication continue to use the existing 401 behavior.
- This decision governs Shop-context establishment only. It does not define T3-04 object/queryset behavior or change global Shop visibility.
- Historical scope note: ordinary-user Shop visibility was subsequently resolved as membership-authorized by the 2026-09-29 rebaseline; this does not alter the T3-03 context-resolution 404/401 contract.

## 2026-09-29 — Approve Phase 3 global identity, membership authority, and Work Function model

This historical business architecture rebaseline records approved target behavior at that time; its multi-Shop global User assumption was later superseded by the T3-04B User-Scope decision below. See `docs/BUSINESS_RULES.md` and `docs/PROJECT_STATE.md` for current rules and implementation state.

- **Permanent User ID:** Email cannot be universal because ordinary Shop employees may not have or need email. Every global User receives a permanent, system-generated, globally unique, human-usable User ID, while UUID remains the internal database identity. The ID is role-, Shop-, and brand-neutral.
- **One identity across Shops (SUPERSEDED):** Historical target allowed the same global User to work in multiple Shops. This was superseded by the later Shop-owned ordinary-account decision below.
- **Access Role vs Work Function:** Authority and the work a person performs are distinct. V1 access roles are ADMIN, STAFF, VIEWER; no OWNER role is introduced. TAILOR, SALESMAN, CASHIER, and CUTTER are not access roles.
- **Function per membership:** A Shop-owned User's membership may have zero or multiple controlled Work Functions; functions do not grant API permissions. A real-world person working in another Shop has a separate account and membership there.
- **Fixed V1 workflow, flexible people:** The approved workflow remains stable; Shops vary in who performs each stage. No per-Shop workflow builder is added.
- **Admin safety:** Each Shop maintains one or two active ADMIN memberships. Main Supplier controls ADMIN hierarchy and global account administration; Shop Admins manage only permitted same-Shop non-ADMIN accounts and Shop-local Work Functions. Shop creation requires a valid first ADMIN account. User deactivation cannot leave the owning Shop without an active ADMIN.
- **Contact and recovery:** Normal Users need User ID/password and may omit email/phone. Active Shop ADMIN and Main Supplier accounts require both. Shop Admins cannot reset a global password; normal users without email recovery use controlled Main Supplier/global-account reset.
- **Shop policy resolved:** Ordinary Users see only authorized Shops. Main Supplier alone manages Shop lifecycle/settings; deactivation preserves data/memberships, and ordinary Shop DELETE is not a V1 operation. `max_users` cannot be reduced below current user_count.
- **Migration safety:** Later remediation must preserve UUIDs, password hashes, existing emails, memberships, and approved session semantics; generate unique User IDs without fabricating contacts or duplicating accounts. Migration strategy must be based on repository/data analysis in the implementation task.

These decisions supersede conflicting earlier target assumptions, including required email, globally discoverable Shops, unresolved Shop deletion semantics, and unrestricted max_users reduction. They do not authorize implementation or alter T3-03/T3-04 context/isolation contracts.

## 2026-09-29 — Approve T3-04B Shop-owned ordinary accounts

- Each ordinary account belongs permanently to exactly one Shop. The same real-world person may have separate independent accounts in different Shops, with separate UUIDs, User IDs, credentials, and histories.
- Do not attach an existing account to another Shop. Main Supplier accounts remain global and have no owning Shop. Email and phone remain globally unique when supplied.
- Shop creation atomically creates its first Shop-owned ADMIN account and membership. Main Supplier may create any approved Shop role; a Shop ADMIN may create only STAFF/VIEWER in their own Shop and reset only current same-Shop STAFF/VIEWER credentials.
- Existing multi-Shop or unowned ordinary-account data must be preflighted. Migration stops with actual affected identifiers; do not merge accounts or fabricate ownership.
- This decision supersedes only the multi-Shop global User identity and account-attachment assumptions above. It does not authorize T3-04C or otherwise change role names, Shop isolation, or approved ADMIN lifecycle rules.
- **Implementation status:** Membership-scoped Work Function persistence and Shop-local management are implemented and published under T3-04C; exact-SHA Project State Validation passed in run `36605653294`. Phase 4 workflow-stage mapping remains deferred and is not resolved by this implementation.

## 2026-09-29 — Approve T3-04A display-name rule

- `first_name` is required and nonblank after trimming; `last_name` is optional.
- Human display name is `first_name` or `first_name + " " + last_name` when last name is present.
- Do not add a separate `display_name` field or fall back to email, phone, UUID, or User ID for a valid account.
- Existing records must be preflighted. Never fabricate a name; stop migration for approved real-data remediation if a usable first name is missing.
- This decision resolves the T3-04A display-name question and does not itself authorize implementation.

**Implementation note (2026-09-29):** T3-04A is published. Current T3-04B remediation status is maintained in `docs/PROJECT_STATE.md`; this historical display-name decision does not authorize later tasks.

## 2026-09-30 — Approve Phase 4–6 before formal frontend resequencing (SUPERSEDED)

**SUPERSEDED by FRONTEND-DELIVERY-LOCK-01 below.** This historical block (from `PHASE4-RESEQUENCE-01`) previously mandated Phase 4 → 5 → 6 before any frontend work, but this is no longer the active roadmap.

## 2026-09-30 — Contract-First Paired Delivery & UI Reference Gate (FRONTEND-DELIVERY-LOCK-01)

- **Paired Delivery Strategy**: The strict Phase 4-6 backend-before-frontend roadmap is superseded. Frontend development will resume immediately on `frontend/parallel-foundation` to implement all current backend features (Auth, Layout, Profile, Shop, Members, Work Functions, Main Supplier). Future Phase 4 and Phase 5 features will follow a **Contract-First Paired Delivery** rule: Backend Domain Accepted → Corresponding Frontend Slice.
- **UI REFERENCE GATE**: No frontend page, screen, component, or visual workflow may be implemented without an approved visual/design reference supplied or explicitly accepted by the user. If an implementation task reaches the UI stage and no approved reference exists: STOP AND WAIT FOR THE UI REFERENCE. Engineering agents must NOT invent the final UI or independently design new pages.
- **Approved Layout References**: The current Work page on `frontend/parallel-foundation` is the approved authenticated visual/layout reference. Its layout patterns (desktop shell, sidebar, mobile nav) may be reused, but its data and stages remain strictly mock/template-only until T4-04 (Work Backend API) is accepted. The current `LoginPage` is only a scaffold/preview and NOT an approved Login UI reference.
- **Dashboard Last Rule**: The real Dashboard is intentionally LAST. It will only aggregate real information after the real business modules and data contracts exist.

## 2026-09-30 — Approve non-blocking parallel backend delivery (PHASE4-PARALLEL-UNBLOCK-01)

- Backend Phase 4/5/6 work may proceed in parallel with frontend integration of existing backend capabilities. Frontend completion is not a prerequisite to start Phase 4 or to advance between backend tasks whose dependencies are satisfied.
- Backend task dependencies remain authoritative. A corresponding frontend domain slice may follow only after its backend contract is accepted; frontend remains contract-first and must not invent API or business behavior.
- This clarifies and supersedes any blocking interpretation of the delivery sequence recorded under `FRONTEND-DELIVERY-LOCK-01`; it does not erase that historical decision or alter its UI Reference Gate, Dashboard Last Rule, phase boundaries, or task-confirmation rules.
