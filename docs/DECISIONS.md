# Architectural Decisions

## 2026-09-25 — Establish repository-contained continuity

The repository will contain explicit agent instructions and persistent state, architecture, decision, plan, API, security, database, changelog, and handoff documents. This makes work transferable between agents and IDEs without relying on conversation history.

## 2026-09-25 — Record the project as uninitialized

Because the repository has no application code or requirements, the initial documents describe absence rather than assuming a Django architecture, database, API, or security model.

## 2026-09-25 — Adopt the SGTP V1 target product definition

SGTP V1 is the Supplier-Centric Garment & Tailor Platform, with Tailor Management as the core business module. The approved hierarchy is Supplier/Main Admin → Supplier Back Office → isolated Shop workspaces. The approved workflow runs from Client Request through Design, Measurement, Fabric/Material, Cutting, Stitching, Check, Finishing, QC, Completed, Billing, and Reports/History.

This decision expands the prior generic-starter planning context into an integrated product definition. It does not authorize implementation in this task and does not change the technology stack. The target and Definition of Done are maintained in `docs/PRODUCT_DEFINITION.md`.

## 2026-09-25 — Approve tenant context, billing ownership, and CSRF phase gate

- Tenant context resolution: use URL-path context in the form `/shops/{shop_id}/...`. T3-03 must implement and test this approved mechanism; it must not substitute another context mechanism.
- Related Person billing ownership: the Primary Client owns billing for work belonging to a Related Person. R5-01 must enforce and test this rule.
- CSRF: protection is a fixed requirement for refresh-cookie flows. Phase 2 owns selection, implementation, and validation of the concrete CSRF mechanism; the mechanism must be explicitly documented and tested before Phase 2 is complete.
