# Agent Engineering Instructions

## Source of truth

This repository is the source of truth for project context. Do not depend on prior AI conversations, a particular model, or a particular IDE. At the start of every task, read:

1. `AGENTS.md`
2. `docs/PROJECT_STATE.md`
3. `docs/HANDOFF.md`
4. `docs/ARCHITECTURE.md`
5. `docs/DECISIONS.md`
6. Any additional document relevant to the task

Inspect the current code and Git status before editing. If documentation and code disagree, verify the code, update the documentation, and record the correction in `docs/CHANGELOG.md`.

## Working rules

- Preserve existing user work and make the smallest safe change.
- Never reset, force-push, or rewrite shared history.
- Never commit secrets. Keep local configuration and credentials out of Git.
- Run appropriate tests and record their results.
- Whenever making a meaningful change, update `docs/PROJECT_STATE.md` and `docs/HANDOFF.md`; update the other project documents when their subject changes.
- Before ending a meaningful session, leave a continuation-ready handoff with changed files, tests, known issues, blockers, and the next action.

## Current repository status

This repository is the SGTP starter project. It contains a Django/DRF application with accounts, tenants, common base models, PostgreSQL configuration, Docker/devcontainer infrastructure, migrations, and tests. The authoritative inspection and current gaps are recorded in `docs/PROJECT_STATE.md`, `docs/ARCHITECTURE.md`, and `docs/HANDOFF.md`. Do not begin Phase 1 or invent V1 requirements until those requirements are explicitly available in the repository.
