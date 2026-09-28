# Architectural Decisions

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
- Account foundation preserves User UUID identity and required email; international phone uses canonical E.164 and email-or-phone login. No fabricated phone backfill.
- V1 includes searchable Clients, duplicate warnings without silent merge, measurement templates/history/compare, private design references, Work priorities and derived delivery indicators, advance/partial/final payment support, outstanding balances, multilingual receipts/invoices/reports, audit/alerts/observability, and controlled Staging checkpoints as mapped in phase plans.
- Environment progression is LOCAL → STAGING → PRODUCTION. Client review uses Staging (`staging.birky.com` / `api-staging.birky.com`). Phase 9 reuses the same Staging for formal release-candidate validation. Phase 10 remains the sole Production gate.
- Strict V1-first: Post-V1 features remain gated until Phase 10 acceptance and the full V1 Definition of Done pass.

These approvals do not resolve implementation-independent business policies. The following remain **BUSINESS DECISION REQUIRED**: ordinary-user Shop read visibility; Shop delete/archive/deactivate; Shop Admin scoped settings authority; deployment defaults and public hostnames beyond approved environment configuration; currency changes after financial history; due-soon threshold/date cutoff; advance cancellation/refund, overpayment/allocation; notification channels; retention durations and anonymization. Account creation, phone, initial-password/recovery/session, Main Supplier Shop-settings authority, and locale/appearance policies are now locked below and in `docs/BUSINESS_RULES.md`.

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

## 2026-09-28 — Clarify company and product naming

Company: BiRKy. Technical/internal project: SGTP. Customer-facing product brand: not yet decided.

## 2026-09-28 — Approve T3-03 Shop-context denial disclosure

- For `/api/v1/shops/{shop_id}/...` context authorization, foreign, unauthorized, inactive, soft-deleted, unavailable, and nonexistent Shops return one uniform non-disclosing 404 response.
- Unauthenticated, invalid, and revoked authentication continue to use the existing 401 behavior.
- This decision governs Shop-context establishment only. It does not define T3-04 object/queryset behavior or change global Shop visibility.
