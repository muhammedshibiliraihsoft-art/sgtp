# EXISTING-DOMAIN-PERFORMANCE-MEDIA-01

**Priority:** P2 — performance / media reliability  
**Status:** Planned; Task 1, 2-ന് ശേഷം അല്ലെങ്കിൽ Task 1 baseline കഴിഞ്ഞ് വേറെ confirmed task ആയി.  
**Effort:** High (വ്യത്യസ്ത modules ഉള്ളതിനാൽ ചെറിയ serial batches ആയി നടപ്പാക്കുക)  
**Collision:** High — Catalog serializers/views, pagination consumers, shared image hook, private upload service.

## Objective

ഇതിനകം പ്രവർത്തിക്കുന്ന Catalog, Designs, Measurements, Inventory, private R2 image flows-ൽ verified N+1, fetch-all, repeat image download, slow upload-completion transaction പ്രശ്നങ്ങൾ പരിഹരിക്കുക. നിലവിലെ UI, pagination semantics, private access, API compatibility എന്നിവ സംരക്ഷിക്കുക.

## Included findings and likely files

1. **Design list N+1:** `apps/catalog/serializers.py` (`DesignSerializer`), Catalog view/query loading, serializer query-count tests.
2. **Fetch-all pages:** Catalog/Designs/Measurements/Materials/Inventory frontend services/pages/tests; server API-യിൽ നിലവിലുള്ള pagination/filter contract ഉണ്ടെങ്കിൽ അത് ഉപയോഗിക്കുക. Backend pagination നിലവിലില്ലെന്ന് തെളിഞ്ഞാൽ അതിന് minimal paired API change വേറെ review ചെയ്യുക.
3. **Private image repeat downloads:** `frontend/src/hooks/usePrivateImage.ts`, ബന്ധപ്പെട്ട image components/tests; backend `apps/catalog/views.py` നിലവിലെ authorized endpoint contract.
4. **Upload complete transaction:** `apps/catalog/private_uploads.py`, ബന്ധപ്പെട്ട service/transaction tests.
5. **Designs page request failure (additional):** screenshot-ൽ Designs page `The request could not be completed.` കാണിക്കുന്ന നിലവിലുള്ള failure-ന്റെ യഥാർത്ഥ failed endpoint/status/response ആദ്യം കണ്ടെത്തുക. Root cause ഉറപ്പാക്കാതെ UI/API മാറ്റരുത്; സ്ഥിരീകരിച്ച പ്രശ്നം മാത്രം fix ചെയ്യുക. `frontend/src/features/designs/DesignsPage.tsx`, അതിന്റെ API/service, ബന്ധപ്പെട്ട frontend tests, ആവശ്യമായാൽ ബന്ധപ്പെട്ട Catalog backend view/serializer/tests പരിശോധിക്കുക.

## Must not touch

- Private R2 objects public ആക്കൽ, frontend-ൽ R2 credentials, Shop/object authorization weakening.
- Original image quality/business data, reference ownership, published design history.
- Redis/cache service, broad CDN/API redesign, unrelated Catalog schema.

## Implementation boundaries

- Design list query-ൽ required related objects prefetch/select ചെയ്ത് name/latest-version lookups ഒരേ loaded result ഉപയോഗിക്കുക; output shape മാറ്റരുത്.
- Frontend ആദ്യം നിലവിലുള്ള server pagination ഉപയോഗിക്കണം; full collection memory-ൽ കെട്ടിവയ്ക്കരുത്. Existing filters/page-size behavior നിലനിർത്തുക.
- Image request dedupe/cache per authorized URL/session boundary മാത്രം; logout/Shop/account change-ൽ cache invalidate, object URL cleanup, bounded retry; lazy loading + fixed image slot.
- Server response caching എടുക്കുന്നെങ്കിൽ private user/Shop boundary proof വേണം; shared public cache ഇല്ല.
- Upload completion: R2 network/read/image processing DB transaction-ിന് പുറത്തേക്ക് മാറ്റുന്നതിന് മുൻപ് object verify, duplicate completion, DB failure, orphan-object handling flow പരിശോധിക്കുക. Final DB state atomic/idempotent ആയിരിക്കണം.
- Designs request error: browser/network trace-ൽ failed request URL, HTTP status, safe response/error code എന്നിവ രേഖപ്പെടുത്തി backend logs/request ID-യുമായി correlate ചെയ്ത് failure layer (frontend/config, authentication/Shop authorization, API, അല്ലെങ്കിൽ transient network) വേർതിരിക്കുക. Existing auth, Shop isolation, API contract സംരക്ഷിച്ച് user-ന് actionable localized error/retry നൽകുക; unrelated requests/images പരാജയപ്പെട്ടാൽ മുഴുവൻ Design screen മറയ്ക്കരുത്. Error state-ൽ input/selection നശിപ്പിക്കരുത്, server success ഇല്ലാതെ success കാണിക്കരുത്.

## Impact / tests

- **API contract:** ആദ്യ ലക്ഷ്യം unchanged; cache/signed URL അല്ലെങ്കിൽ server pagination API മാറ്റം ആവശ്യപ്പെട്ടാൽ വേറെ minimal contract plan/approval വേണം.
- **DB:** migration ഇല്ലെന്നാണ് പ്രതീക്ഷ; index add ചെയ്യാൻ query evidence ആവശ്യമാണ്.
- **Infra:** പുതിയ cache/worker/storage infra ഇല്ല.
- **Security:** private image authorization, Shop isolation, upload target binding/MIME/size/expiry checks unchanged.
- **Focused tests:** Design list/detail query count + payload; Designs list API non-2xx, malformed/unavailable response, retry and preserved screen state; pagination no fetch-all, filter/page transitions; duplicate image request + logout/Shop switch cleanup; slow/missing image local fallback; upload transaction boundary, storage failures, retry/idempotency, partial-write safety.
- **Then domain regression:** Catalog/Design/Measurement/Inventory/media suites; milestone അവസാനം full suites, build/typecheck, migration checks.
- **Rollback:** per-domain changes ചെറിയ commits/patch groups ആയി വേർതിരിച്ച് revert ചെയ്യാവുന്ന വിധം; DB schema change ഒഴിവാക്കുക.
- **Parallel safe:** എല്ലാം ഒരുമിച്ച് NO. Design N+1-ഉം upload transaction-ഉം വ്യത്യസ്ത files ആയതിനാൽ വേറെ സമയത്ത് parallel സാധ്യം; pagination tasks തമ്മിൽ UI/service/shared API overlap ഉള്ളപ്പോൾ serial.

## Acceptance

List flows ആവശ്യമായ page മാത്രം load ചെയ്യുന്നു; Design list query എണ്ണം അനിയന്ത്രിതമായി കൂടുന്നില്ല; Designs request failure-ന്റെ root cause evidence-ോടെ തിരിച്ചറിഞ്ഞ്, failure-ൽ clear retryable UI കാണിക്കുന്നു; private image repeat transfer കുറയുന്നു, private access അതേപടി; upload/storage failure-ൽ false success/partial DB state ഇല്ല; UI payload, Shop isolation, responsive behavior regress ചെയ്യുന്നില്ല.
