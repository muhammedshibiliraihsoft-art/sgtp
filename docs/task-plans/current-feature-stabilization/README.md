# നിലവിലുള്ള Features Stabilization — Task Set

**Status:** Tasks 1–2 complete locally (unpublished). Task 3 remains planned and requires its own `CONFIRM TASK <ID>`.  
**പരിധി:** നിലവിൽ code ഉള്ള authentication, Shop/Client/Catalog/Design/Measurement/Inventory/private-media flows സ്ഥിരപ്പെടുത്തുകയും audit-ൽ കണ്ടെത്തിയ API/query/media പ്രശ്നങ്ങൾ പരിഹരിക്കുകയും ചെയ്യുക.  
**ഇവിടെ ഉൾപ്പെടില്ല:** പുതിയ Work/Orders/Billing/Reports/Notifications modules, DigitalOcean production creation/cutover, production data/config writes, broad UI redesign.

## Task ക്രമം

1. [`CURRENT-STATE-MIGRATION-INTEGRITY-01`](./01-current-state-migration-integrity.md) — complete: migration chain, data-safe reverse, schema/model alignment പരിശോധിച്ചു.
2. [`EXISTING-AUTH-REQUEST-FLOWS-01`](./02-existing-auth-request-flows.md) — password recovery frontend integration, auth startup, duplicate/rapid requests എന്നിവ ശരിയാക്കുക.
3. [`EXISTING-DOMAIN-PERFORMANCE-MEDIA-01`](./03-existing-domain-performance-media.md) — fetch-all, Design N+1, Measurement request fan-out, private image/upload performance എന്നിവ പരിഹരിക്കുക.

Task 1-ന്റെ clean baseline-ന് ശേഷം Task 2, 3-ൽ തമ്മിൽ collision ഇല്ലാത്ത ചെറിയ work batches ആക്കാം; shared `apiClient`, `App.tsx`, catalog serializers, migrations എന്നിവ ഒരേസമയം മാറുന്നുവെങ്കിൽ serial ആയി നടത്തണം. ഓരോ task-ും സ്വതന്ത്രമായി review ചെയ്ത് അടുത്ത task-ന് മുമ്പ് നിർത്തണം.

## പൊതുവായ സംരക്ഷണങ്ങൾ

- Shop/tenant isolation, server-side permissions, CSRF, JWT/refresh rotation, must-change-password, immutable measurement/design history, API response meaning എന്നിവ നിലനിർത്തുക.
- Private images public ആക്കരുത്; R2 credentials frontend-ൽ എത്തിക്കരുത്.
- UI redesign, പുതിയ business rules, പുതിയ modules, അനാവശ്യ database/cache infrastructure എന്നിവ scope-ൽ ഇല്ല.
- ഓരോ task-ിലും focused tests; ബന്ധപ്പെട്ട domain regression; milestone അവസാനം മാത്രം full suites/build/typecheck/lint/Django/migration/repository gates.
- `main` push ഇപ്പോൾ Render staging auto-deploy + startup migrations trigger ചെയ്യാം. ഈ task set local implementation/staging verification വരെ മാത്രം; push/deploy ഒരു task-ിന്റെയും implied step അല്ല.

## തീർന്നതിന് ശേഷമുള്ള വേറിട്ട roadmap

Work/Orders workflow → Billing → operational Reports/Dashboard → staging release-candidate verification → DigitalOcean production ഏറ്റവും അവസാനം. ഇവ ഈ task set-ിൽ ഇല്ല.
