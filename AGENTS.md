# Agent Engineering Instructions

## Source of truth

This repository is the source of truth for project context. Do not depend on prior AI conversations, a particular model, or a particular IDE. At the start of every task, read:

1. `AGENTS.md`
2. `docs/PROJECT_STATE.md`
3. `docs/HANDOFF.md`
4. `docs/ARCHITECTURE.md`
5. `docs/DECISIONS.md`
6. `docs/PRODUCT_DEFINITION.md`
7. Any additional document relevant to the task

Inspect the current code and Git status before editing. If documentation and code disagree, verify the code, update the documentation, and record the correction in `docs/CHANGELOG.md`.

## Working rules

- Preserve existing user work and make the smallest safe change.
- Never reset, force-push, or rewrite shared history.
- Never commit secrets. Keep local configuration and credentials out of Git.
- Run appropriate tests and record their results.
- Whenever making a meaningful change, update `docs/PROJECT_STATE.md` and `docs/HANDOFF.md`; update the other project documents when their subject changes.
- Before ending a meaningful session, leave a continuation-ready handoff with changed files, tests, known issues, blockers, and the next action.

## Target product and definition of done

SGTP means Supplier-Centric Garment & Tailor Platform. The target V1 is a complete integrated product, with Tailor Management as the core business module. The business hierarchy is Supplier/Main Admin → Supplier Back Office → isolated Shop workspaces → Clients and their Designs, Measurements, Fabric/Materials, Work, Billing, and Reports.

The core persisted workflow is:

`Client Request → Design → Measurement → Fabric/Material → Cutting → Stitching → Check → Finishing → QC → Completed → Billing → Reports/History`

The target stack is React + Vite + Tailwind CSS for the frontend; Django + Django REST Framework + Django ORM for the backend; PostgreSQL for persistence; custom User plus secure token authentication; tenant isolation; object-level permissions; service layer; persistent object storage; background jobs; audit logging; testing; CI; monitoring; and automatic documentation. AI and third-party integrations remain isolated supporting systems.

V1 is not complete merely because the backend, frontend, individual APIs, pages, or tests work in isolation. Completion requires an end-to-end validation across Supplier, Back Office, Shop, Client, Work, Design, Measurement, Fabric, Production, Completion, Billing, and Reports, including security, isolation, files, background jobs, staging/production, monitoring, and documentation.

When implementation changes affect this target, update `docs/PRODUCT_DEFINITION.md`, `docs/PROJECT_STATE.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_PLAN.md`, and `docs/HANDOFF.md` as applicable. Do not silently change the approved hierarchy or V1 boundaries.

## Current repository status

This repository is the SGTP starter project. It contains a Django/DRF application with accounts, tenants, common base models, PostgreSQL configuration, Docker/devcontainer infrastructure, migrations, and tests. The authoritative inspection, target product, and current gaps are recorded in `docs/PRODUCT_DEFINITION.md`, `docs/PROJECT_STATE.md`, `docs/ARCHITECTURE.md`, and `docs/HANDOFF.md`. Do not begin implementation phases until the current foundation contradictions are reviewed against the target, and do not invent business behavior outside the documented V1 boundaries.
