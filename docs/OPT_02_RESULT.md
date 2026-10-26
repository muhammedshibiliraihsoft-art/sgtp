# OPT-02 — safe baseline remediation (2026-10-07)

Scope: repair the production-settings test isolation, review/fix an unsafe unpublished seed-migration reverse path, verify the live staging push trigger read-only, and rerun local gates. No product workflow/API change, credential change, commit, push or deploy.

## Corrections

- `core/tests/test_settings.py`: the production security test now imports settings in a fresh subprocess with explicit fake production/R2 values. It continues to assert HTTPS redirect, secure cookies, non-debug production mode and R2 enabled. The production fail-closed R2 guard is unchanged. The separate negative production-settings tests also remain intact.
- `apps/catalog/migrations/0018_seed_remaining_family_design_defaults.py`: generated global default Designs now have deterministic, seed-specific UUIDs. Reverse migration deletes only those exact seed IDs after checking their original family/status/version/translation/selections; edited seeds cause a guarded rollback failure instead of silent data loss. A pre-existing global Design with the same display name is left alone. The migration is uncommitted and has not run in staging/production.
- Two new regression tests use the historical migration model state to prove duplicate-name preservation and refusal to delete a changed seed. Existing older-schema rollback tests also exercise the legitimate reverse path.

## Evidence and limits

- OPT-01 baseline: 468 backend tests collected, 467 pass / 1 production-settings test fail. OPT-02 final clean disposable-PostgreSQL run: **470 collected / 470 passed**, 313 warnings, no skips/exclusions. The +2 are the migration-safety regression tests; the prior failing production test now passes. Earlier partial/intermediate failing runs are not a sign-off.
- Frontend baseline rechecked: 142/142 tests, typecheck and production build pass. Lint exits 0 with existing React effect warnings. Django check and migration drift check pass. Changed-file Black/Flake8 and `git diff --check` pass. Repository validator passes with 470 backend tests discovered; it warns that the working tree remains dirty.
- Render service `birky-staging-api` was read read-only through the connected account: branch `main`, `autoDeploy=yes`, `autoDeployTrigger=commit`. The checked-in startup script runs migrations. A `main` push can therefore affect the live staging deployment/database. Neither the service nor the trigger was changed.
- Three new catalog migrations and other feature code are still dirty/unpublished. OPT-02 does not create an exact release candidate SHA or authorize publication. No authenticated browser or performance measurement is claimed.

## Task-level audit verdict

- **Correctness:** task-level PASS on local checks; full backend and frontend suites pass. This is not a live-release verdict.
- **Scope:** settings-test isolation, unpublished migration safety, regression tests and documentation only; no unrelated application behavior changed.
- **Integrity:** baseline and partial failures recorded; no weakened security assertion, skip, excluded path or hidden test-count change.
- **Architecture:** production storage fail-closed behavior and forward migration semantics preserved; reverse is intentionally guarded.
- **Decision authority:** no new product or production-domain decision. Staging push effect is verified; production remains deferred.

Next separately confirmed work remains OPT-03 measured hardening. Before any `main` push, review the exact committed candidate and staging migration/storage readiness; do not treat this task's local checks as deployment approval.
