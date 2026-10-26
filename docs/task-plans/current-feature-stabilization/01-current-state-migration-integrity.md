# CURRENT-STATE-MIGRATION-INTEGRITY-01

**Priority:** P1 — release integrity / data safety  
**Status:** Complete — local/unpublished; `CONFIRM TASK CURRENT-STATE-MIGRATION-INTEGRITY-01` പ്രകാരം മാത്രം scope നടപ്പാക്കി.  
**Effort:** Medium  
**Collision:** High — dirty `main`, catalog models/migrations, generated schema, existing user changes.

## Objective

ഇപ്പോൾ local `main`-ൽ ഉള്ള implemented feature set-നെ reproducible, migration-safe baseline ആക്കുക. Uncommitted changes-ന്റെ ownership/scope സംരക്ഷിച്ച് Catalog/Measurement migrations `0017–0019` clean database-ൽ apply ചെയ്യാനും upgrade/reverse safety-യും തെളിയിക്കുക.

## Verified reason / why first

Audit സമയത്ത് വലിയ dirty working tree-യും മൂന്ന് untracked migrations-ഉം ഉണ്ടായിരുന്നു. OPT-02 settings-test failure ശരിയാക്കി, `0018` seed reverse സുരക്ഷിതമാക്കി, full backend 470/470, frontend 142/142 പാസാക്കി. എന്നിരുന്നാലും local changes ഒന്നും commit/push ചെയ്തിട്ടില്ല; exact release candidate ഇല്ല. OPT-02 tests clean test DB-ൽ migrations ഓടിച്ചതാണ്, പക്ഷേ ഈ task migration set/code/schema-യുടെ സമഗ്ര candidate review ഉറപ്പാക്കുന്നു.

## Expected scope / files likely to change

- `apps/catalog/migrations/0017*`, `0018*`, `0019*`; അനുബന്ധ migration tests.
- ആവശ്യമായാൽ ബന്ധപ്പെട്ട catalog models/services/tests, `docs/schema.yml`, root `schema.yml` എന്നിവയിൽ minimal mismatch correction.
- Current changed-file list മാത്രം ഉപയോഗിച്ച് review; unrelated user changes preserve ചെയ്യുക.

## Must not touch

- Auth, business behavior, frontend UX, staging/production data, provider settings, secrets, unrelated migrations.
- Explicit user review ഇല്ലാതെ `git reset`, checkout/discard, commit, push, deployment.

## Change boundaries

- **Backend:** migration replay/reversal findings തെളിഞ്ഞാൽ മാത്രം targeted fix.
- **Frontend:** മാറ്റമില്ല; backend contract mismatch യഥാർത്ഥമായി സ്ഥിരീകരിച്ചാൽ മാത്രം coordinating follow-up രേഖപ്പെടുത്തുക.
- **DB:** disposable local test database മാത്രം. Migration/data backfill മാറ്റം ആവശ്യമായി വന്നാൽ forward/rollback compatibility test നിർബന്ധം.
- **API/Infrastructure:** മാറ്റമില്ല.
- **Business logic:** approved garment/design/measurement behavior മാറ്റരുത്.

## Validation

- Fresh disposable PostgreSQL database-ൽ migrations `0017–0019` clean replay; നിലവിലെ migration state-ിലേക്ക് upgrade.
- `0018` seed idempotency/reverse safety, migration dependencies, existing Design references, Shop isolation സംബന്ധിച്ച focused regression.
- `makemigrations --check --dry-run`, Django check, focused backend tests; candidate file review + `git diff --check`.
- ഈ task-ന്റെ അവസാന milestone-ൽ full backend/frontend tests, typecheck/build, repository validator.

## Impact / recovery

- **API contract:** മാറ്റമില്ലെന്ന് ലക്ഷ്യം; ആവശ്യമായെങ്കിൽ additive-compatible മാത്രം.
- **Security:** Shop boundaries മാറ്റരുത്; existing negative isolation tests നിലനിർത്തുക.
- **Migration required:** നിലവിലുള്ള migrations ഉണ്ട്; പുതിയ migration ആവശ്യമെന്ന് തെളിഞ്ഞാൽ മാത്രം, backward-compatible ആയി.
- **Infra:** ഇല്ല; staging/production write ഇല്ല.
- **Rollback:** പുതിയ schema code മാത്രം ചേർത്തിട്ടുണ്ടെങ്കിൽ forward correction migration; data seed rollback-ൽ edited/user-owned rows സംരക്ഷിക്കുക. User-owned dirty files delete/discard ചെയ്യരുത്.
- **Parallel safe:** NO — shared Catalog models, migrations, schema files, same dirty checkout.

## Acceptance

Migration chain fresh database-ൽ പുനരാവർത്തിക്കാം; existing IDs/history സുരക്ഷിതം; Shop scoping tests pass; worktree-ൽ ഏത് change ഏത് feature/task-നാണെന്ന് വ്യക്തം; exact commit ഉണ്ടാക്കിയിട്ടില്ല.
