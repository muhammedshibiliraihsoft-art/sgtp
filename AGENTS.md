# Agent Engineering Instructions

## Source of truth

This repository is the source of truth for project context. Do not depend on prior AI conversations, a particular model, or a particular IDE. At the start of every task, read:

1. `AGENTS.md`
2. `docs/PROJECT_STATE.md`
3. `docs/HANDOFF.md`
4. `docs/ARCHITECTURE.md`
5. `docs/DECISIONS.md`
6. `docs/PRODUCT_DEFINITION.md`
7. `../sdb-master-audit-protocol.md` (Mandatory for all auditing tasks)
8. Any additional document relevant to the task

Inspect the current code and Git status before editing. If documentation and code disagree, verify the code, update the documentation, and record the correction in `docs/CHANGELOG.md`.

## Auditing Guidelines

All auditing tasks must strictly follow the rules, procedures, and evidence hierarchies defined in `../sdb-master-audit-protocol.md`. When an audit prompt is given, auditing agents (including OpenCode, Codex, and others) must read and adhere to this master audit protocol before proceeding.

## Working rules

- Preserve existing user work and make the smallest safe change.
- Never reset, force-push, or rewrite shared history.
- Never commit secrets. Keep local configuration and credentials out of Git.
- Run appropriate tests and record their results.
- Whenever making a meaningful change, update `docs/PROJECT_STATE.md` and `docs/HANDOFF.md`; update the other project documents when their subject changes.
- Before ending a meaningful session, leave a continuation-ready handoff with changed files, tests, known issues, blockers, and the next action.

## Repository-state completion gate

- Git is authoritative for the current repository state, including `HEAD`, branch, working-tree status, and local/remote parity. Documentation must not be treated as an authoritative substitute for Git.
- Before declaring a meaningful task complete, run `python scripts/verify_project_state.py` and record its result. A task is not complete when the validator reports a blocking error.
- Current-state claims must be evidence-backed by the repository and commands actually run. Historical facts must be labelled historical; do not copy historical commit hashes or test counts into current-state sections.
- Local-ahead-of-remote is not equivalent to synchronized or published. State local, remote, and push status separately.
- Do not silently invent or resolve business decisions. Public company/product names, production domains, hostnames, and public URL architecture require a human/business decision.
- Before ending a meaningful task, verify documentation consistency, validator output, relevant tests/checks, and Git state. Update `docs/PROJECT_STATE.md` and `docs/HANDOFF.md` only with evidence from the current repository.

## Target product and definition of done

SGTP means Supplier-Centric Garment & Tailor Platform. The target V1 is a complete integrated product, with Tailor Management as the core business module. The business hierarchy is Supplier/Main Admin → Supplier Back Office → isolated Shop workspaces → Clients and their Designs, Measurements, Fabric/Materials, Work, Billing, and Reports.

The V1 business hierarchy is exactly one Supplier/Main Admin → Supplier Back Office → multiple isolated Shop workspaces. External Suppliers are separate Shop-owned business records, not users, tenants, members, roles, or authenticated participants. There is no multi-supplier SaaS model in V1.

The core persisted workflow is:

`Client Request → Design → Measurement → Fabric/Material → Cutting → Stitching → Check → Finishing → QC → Completed → Billing → Reports/History`

The target stack is React + Vite + Tailwind CSS for the frontend; Django + Django REST Framework + Django ORM for the backend; PostgreSQL for persistence; custom User plus secure token authentication; tenant isolation; object-level permissions; service layer; persistent object storage; background jobs; audit logging; testing; CI; monitoring; and automatic documentation. AI and third-party integrations remain isolated supporting systems.

V1 is not complete merely because the backend, frontend, individual APIs, pages, or tests work in isolation. Completion requires an end-to-end validation across Supplier, Back Office, Shop, Client, Work, Design, Measurement, Fabric, Production, Completion, Billing, and Reports, including security, isolation, files, background jobs, staging/production, monitoring, and documentation.

When implementation changes affect this target, update `docs/PRODUCT_DEFINITION.md`, `docs/PROJECT_STATE.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_PLAN.md`, and `docs/HANDOFF.md` as applicable. Do not silently change the approved hierarchy or V1 boundaries.

## Phase and task confirmation gate

- A phase confirmation activates the phase only; it does not authorize every task in that phase.
- Before each individual task, present the task objective, expected files/areas, dependencies/preconditions, and validation/tests, then wait for explicit `CONFIRM TASK <TASK-ID>`.
- Implement only the explicitly confirmed task.
- After that task, run its validation, update the relevant documentation, report what was completed, and stop.
- Never begin the next task or next phase automatically. Each requires a new explicit confirmation.
- Casual conversation is not confirmation. Valid examples are `CONFIRM PHASE 1` to activate a phase and `CONFIRM TASK F1-01` to authorize one task.

## Current repository status

This repository is the SGTP starter project. It contains a Django/DRF application with accounts, tenants, common base models, PostgreSQL configuration, Docker/devcontainer infrastructure, migrations, and tests. The authoritative inspection, target product, and current gaps are recorded in `docs/PRODUCT_DEFINITION.md`, `docs/PROJECT_STATE.md`, `docs/ARCHITECTURE.md`, and `docs/HANDOFF.md`. Do not begin implementation phases until the current foundation contradictions are reviewed against the target, and do not invent business behavior outside the documented V1 boundaries.
