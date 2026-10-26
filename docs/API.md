# API

## T4-04 Work/Order API (local, unpublished)

All routes are beneath `/api/v1/shops/{shop_id}/works/` and require an active
authenticated Shop context. `GET /` is paginated and accepts `search` (Work
number, client name, exact UUID), `status`, and `priority`. `POST /` accepts
`client_id`, `design_version_id`, `measurement_set_id`, optional
`related_person_id`, `material_id`, `priority`, `due_date`, and `notes`; one
garment creates one Work. Create requires an available published
`DesignVersion` whose parent Design is ACTIVE; an archived Design is rejected
with the existing DRF field-validation error contract even if its published
version remains. Its parent Family must also be ACTIVE; archived Family or
Design returns the same field-validation error. This does not change readability
of existing Work rows. Design list/detail responses expose read-only
`family_status`, used by the Order picker to omit Designs under archived
Families. `GET /{id}/` returns the record. `PATCH /{id}/`
updates only priority, due date and notes (ADMIN). `DELETE /{id}/` soft-deletes
only Request-stage Work (ADMIN). `POST /{id}/assign/` accepts nullable
`membership_id` (ADMIN); `POST /{id}/advance/` requires the current displayed
stage as `expected_status` and performs only the next fixed transition. A stale
stage returns HTTP 409 (`stale_work`) without advancing again; a missing or
invalid precondition returns 400. Successful Work mutations append an internal
WorkEvent in the same transaction; event records omit note contents and are not
exposed through an API. Responses include stable `work_number`, status,
assigned member and derived `due_indicator` (`UPCOMING`, `DUE_SOON`,
`DUE_TODAY`, `OVERDUE`, or null).
The source IDs cannot be replaced after creation. R5-01 later adds an optional
Work-time Design price/currency snapshot and separate Shop-scoped Billing API;
Work still has no stock reservation or inventory-consumption contract.

## Phase 5 Shop Design pricing and Billing API (local, unpublished)

Normal price and billing endpoints require authenticated active Shop context
and Shop ADMIN or STAFF with active CASHIER Work Function. CASHIER alone does
not grant Shop membership. The selected-Shop invoice-history read and manual
purge endpoint have a separate Main Supplier Super Admin authorization path.
Supported sibling callers are the Design price editor, Work Billing panel,
Billing History, and Back Office Financial Purge page; deployed parity remains
unverified.

- `GET/PUT /api/v1/shops/{shop_id}/design-prices/{design_id}/` reads or sets a
  Shop-specific price for an active global/Shop Design. PUT accepts only
  `{"amount":"12.50"}`; currency comes from the Shop's configured
  `default_currency`. Missing/invalid currency prevents price entry. Shop
  Design create may atomically include optional `price: {"amount": "..."}`.
- Work creation copies the current Shop Design price and currency into nullable
  `design_price_amount`/`design_price_currency` fields. Later Design price
  edits do not change an existing Work snapshot. A Work created without a price
  stays without one; no backfill occurs.
- `GET/POST /api/v1/shops/{shop_id}/works/{work_id}/invoices/` lists/creates
  invoices. POST accepts `mode: "AUTO"|"MANUAL"` and optional manual `lines`
  (`description`, `quantity`, `unit_price`). AUTO adds the immutable Work price
  snapshot line when present; manual items may be entered even if no snapshot
  exists. Multiple invoices per Work are allowed. Draft creation is valid at
  every Work stage.
- `GET /api/v1/shops/{shop_id}/invoices/{invoice_id}/` returns invoice, lines,
  payments, subtotal, amount paid, balance, currency, and issue metadata.
  Draft line items use `POST .../items/`, `PATCH .../items/{item_id}/`, and
  `DELETE .../items/{item_id}/`; only MANUAL lines are editable through PATCH.
  `POST .../issue/` requires at least one line and makes the invoice/lines
  immutable.
- `POST .../payments/` accepts `{ "amount": "..." }` on ISSUED invoices only.
  Each payment belongs to that invoice; partial payment is supported and does
  not advance Work stage. Overpayment is rejected by approved policy.
- `GET /api/v1/shops/{shop_id}/billing/outstanding/` returns paginated issued
  invoices with a positive balance. Related Person invoices identify the
  Primary Client as `client_id` and retain `related_person_id`.
- Invoice History at `/billing/invoices/?status=&from=&to=` is Shop-scoped and
  supports status and issued-date filters. Invoice numbers (`INV-000001`) and
  credit-note numbers (`CN-000001`) are Shop-sequential at issue; voided invoice
  numbers are not reused. Unpaid issued invoices may be voided with a reason.
- Main Supplier Super Admin may review invoice history for an explicitly
  selected Shop and manually purge one complete invoice bundle with
  `POST /api/v1/shops/{shop_id}/invoices/{invoice_id}/purge/`. The request
  requires a reason, exact invoice-number confirmation, and `Idempotency-Key`.
  Purge deletes invoice/line/payment/credit/refund rows, financial-document
  metadata, and associated private files. Existing audit/idempotency records
  and sequence counters remain. Storage deletion failure preserves the
  financial rows so the same request can be retried. Shop ADMIN/CASHIER roles
  do not receive this purge authority; there is no automatic purge. The
  existing selected-Shop API context requires an active Shop; inactive Shops
  are shown disabled in the Back Office selector.
- Optional invoice-level fixed/percentage discount and optional invoice-level
  tax are supported. Fixed discounts are proportionally allocated by line;
  per-line discount/tax uses currency minor-unit `ROUND_HALF_UP`. Tax is
  calculated after discount. No jurisdiction-specific compliance is claimed.
- A paid invoice is corrected using a linked partial/full credit note. Refunds
  are manually recorded only after external transfer, link to an actual payment
  and credit note, and cannot exceed eligible payment. The app does not transfer
  funds. Currency changes are frozen after Design prices or financial history;
  an explicit reviewed migration is required. Excess currency minor-unit
  decimals are rejected without implicit rounding.
- Every financial write requires `Idempotency-Key`. Keys bind Shop, actor,
  operation and request hash; new records store response snapshots/status for
  deterministic replay. `X-Request-ID` is retained in append-only financial
  audit events. Older idempotency rows without snapshots retain a compatibility
  resource lookup.
- Invoice, receipt and credit-note PDF requests accept an optional `locale`.
  Without it, the backend resolves User preference → authorized Shop locale →
  English. PDF metadata is Shop-scoped and exposes no file URL. Download uses
  `GET /api/v1/shops/{shop_id}/financial-documents/{document_id}/download/` and
  rechecks Shop access. New layout-version 2 PDFs use portrait A5; immutable
  version 1 A4 files remain available and are not regenerated or overwritten.
  Rendering and download are synchronous; no queue/job or supplier-wide
  financial report API is currently implemented.

All four generated backend/supported-sibling OpenAPI snapshots match and
validate with 0 errors / 29 existing warnings. Migrations through
`billing.0006` are local and were validated on a fresh disposable
`test_devdb` and were later applied to persistent local `devdb` after a local
backup/restore check. They have not been applied to staging or production.
Focused PDF API and renderer tests passed; the disposable test DB was removed
after the run. Deployed API/schema parity remains unverified.

## Current authentication and recovery contract (local, unpublished)

- The user-facing User ID is stored in the API's `login_id` field: entered casing is preserved after trimming outer whitespace, while uniqueness and login matching are case-insensitive. The generated internal `user_code` remains a separate stable reference/legacy alias. New login-enabled account creation returns this entered User ID and a one-time six-digit PIN; that PIN must be changed at first login and every new credential must be six digits. Successful change replaces the old credential and revokes sessions. Existing legacy passwords remain accepted until changed; no bulk conversion occurs.
- `POST /api/v1/auth/users/{id}/reset-credentials/` retains Main Supplier authority as already implemented. A Shop ADMIN may reset only an active STAFF account in that same Shop; VIEWER, ADMIN, inactive/ineligible and cross-Shop accounts are not eligible for that Shop Admin reset. A temporary six-digit PIN is returned once in `temporary_password`.
- `POST /api/v1/auth/pin-reset-requests/` accepts a registered phone and always returns a generic response without changing credentials. Main Supplier-only `GET .../pending/`, `POST .../{request_id}/approve/`, and `POST .../{request_id}/reject/` handle review. Approval returns a one-time PIN; resolved requests cannot reveal it again. Generated root and docs OpenAPI schemas reflect these local contracts. No staging publication yet.
- VIEWER records remain preserved but are not login-enabled and do not receive normal login credentials or PIN reset access. Email self-service password reset is removed from the current product/API; Shop Admin recovery is the phone request followed by Back Office review and approval.

## Current starter state

The cloned starter contains partial backend/API scaffolding. It has Django URL configuration, DRF, JWT authentication, account endpoints, tenant endpoints, OpenAPI/Swagger routes, pagination/filtering configuration, serializers, and initial API tests. These are reusable starting components, not a complete SGTP V1 API.

Existing starter routes include `/api/v1/auth/`, `/api/v1/tenants/`, `/api/schema/`, and `/api/docs/`. Their current behavior and limitations are described in `docs/ARCHITECTURE.md` and `docs/PROJECT_STATE.md`.

## BACKOFFICE-01 Main Supplier integration

- Auth user representations from `POST /api/v1/auth/login/` and `GET /api/v1/auth/users/me/` include read-only `is_main_supplier_admin`. It is derived from an active superuser and is a frontend routing hint; authorization is still enforced by backend permissions.
- `GET /api/v1/tenants/` lists Shops for an authenticated account, with existing pagination, search, `is_active` filtering, and ordering. Main Supplier receives the global authorized Shop list.
- `GET /api/v1/tenants/{id}/` reads a Shop under existing authorization rules. Main Supplier receives the administrative detail representation.
- `POST /api/v1/tenants/` requires Main Supplier Admin authorization and the existing password-change gate. Required body: `name`, `slug`, positive `max_users`, and `first_admin` with `first_name`, email, and phone. Optional Shop profile fields follow `TenantAdminSerializer`. The transaction creates the Shop and its first ADMIN account/membership together.
- Successful creation returns the Shop representation plus `first_admin_user_code` and `initial_password` once, with `Cache-Control: no-store` and `Pragma: no-cache`. The first ADMIN can authenticate with that permanent User ID and initial password, then must change the password before ordinary protected API use.
- `PATCH /api/v1/tenants/{id}/` updates allowed Shop profile fields. `POST /api/v1/tenants/{id}/activate/` and `/deactivate/` use existing Main Supplier authorization and lifecycle rules. Shops are not deleted.

## Internal OpenAPI documentation portal

- `/api/docs/` serves the single interactive Swagger UI and `/api/schema/` serves its generated OpenAPI document. Both require a Django Admin session for an active Main Supplier superuser whose forced-password-change gate is clear. Anonymous visitors are redirected to the existing Admin login; authenticated non-Main-Supplier accounts receive a generic not-found response. The root path redirects to `/api/docs/` and does not serve a second API reference.
- `/api/browse/` provides a DRF-style endpoint browser for the same protected audience. It loads the implemented endpoint list from the protected OpenAPI schema, accepts an access JWT in a masked input, and sends same-origin requests only to `/api/v1/`. Replace path placeholders and supply request JSON as needed. The browser keeps the access JWT only in page memory, never Web Storage; it does not log tokens. The root path now redirects to this browser.
- Sign in through `/admin/login/` using the existing account. No documentation-specific password or permanent token is created. A valid documentation session only renders the docs portal; backend API requests still need the normal JWT and endpoint permissions.
- The documentation session is separate from business API authentication. Business API requests use the versioned JWT authenticator; a Django Admin session alone does not authenticate them. The browser includes the JWT as a Bearer header, never targets another origin, and preserves the existing CSRF bootstrap for unsafe methods and cookie-based refresh/logout. Swagger authorization persistence is disabled, and portal/docs/schema responses are private and non-cacheable.
- `/api-auth/` and the old `templates/api_test.html` starter page were removed after checking references. The Browsable API renderer remains available in development; it does not provide a session-login path.
- Backend `schema.yml` and `docs/schema.yml`, plus the supported sibling frontend's two schema copies, are generated from current canonical `v1` backend routes. They include implemented Work/Order, Shop Design-price, Billing/history/document, and finance-authorized Shop-context contracts; future endpoints are not invented. All four local snapshots are identical and drf-spectacular validates with 0 errors and 29 existing warnings. This is local source/schema evidence, not deployed parity.

## T4-02 catalog and design contract

**Current Variant policy (confirmed 2026-10-18):** Variant management,
selection, and active materialization are retired. The Variant route details
below describe routes still present in the local `main` implementation; they
are not an approved active product contract and their continued write support
is an incomplete retirement. Keep only legacy reads needed for history until
an authorized code/API retirement removes the write paths. No deployment
contract is inferred from these local sources. The current OpenAPI snapshots
may still include registered legacy endpoints until that code task updates the
routes and regenerates the snapshots; they are not the approved active target.

- Creating and managing global catalog defaults and design templates is Main Supplier-only; approved global records may be read by authenticated Shop users where the endpoint permits it. Shop-local variants, styles, designs, and reference images use the explicit `/api/v1/shops/{shop_id}/...` context and never disclose another Shop's records.
- `GET/POST /api/v1/catalog/families/` lists global garment families and creates a family. `POST` is Main Supplier-only and requires a unique slug `code` plus unique `translations` including English; each translation accepts `locale`, `name`, and optional `description`. Creation is atomic and does not invent a variant or stock/material record.
- Family browse accepts `search` (case-insensitive code or translated-name search before pagination) and returns the standard page-number response. Ordinary Shop users can read ACTIVE families only. Main Supplier defaults to ACTIVE and may request `status=ACTIVE`, `status=ARCHIVED`, or `status=all` for management.
- `GET/PATCH /api/v1/catalog/families/{family_id}/` reads Family detail and allows Main Supplier to update translations and/or ordered applicable Option Groups. One PATCH may include both `translations` and `option_group_ids`; when both are included, the backend applies them in one locked database transaction and returns the updated detail. IDs retain the legacy optional `MULTI` defaults. The Family `code` is immutable. The authorized standalone `PUT .../{family_id}/option-groups/` remains supported. `POST .../{family_id}/archive/` and `POST .../{family_id}/reactivate/` provide a reversible Main Supplier-only lifecycle. Archived families remain stored, are hidden from normal Shop browsing, and are not hard-deleted.
- `POST/GET/DELETE /api/v1/catalog/families/{family_id}/image/` lets Main Supplier upload, replace, or remove one optional thumbnail and lets authenticated users read an active Family image. Upload accepts one JPEG, PNG, or WebP source image, optimizes it to private WebP storage, and returns metadata without embedding image bytes. The content route requires normal authentication; archived images are visible only to Main Supplier.
- New Shop Variants, Shop Designs, Global Design Templates, Measurement Profiles, and Measurement Definition mappings cannot target an archived Family. Existing Variants, Designs, and Measurement history remain intact and readable. Existing Family → Option Group GET/PUT remains global and ordered; only Main Supplier can replace the complete ordered mapping.
- `GET/POST /api/v1/catalog/option-groups/` lists and creates global option groups with the same Main Supplier-only create permission and translation contract. Family associations are configured separately through `PUT /api/v1/catalog/families/{family_id}/option-groups/`.
- Legacy Variant records retain their Family/Shop ownership, active-state fields, translations and nullable references for history. Variant list and detail GET routes remain readable: Global `/api/v1/catalog/variants/` and `/{variant_id}/`; Shop `/api/v1/shops/{shop_id}/catalog/variants/` and `/{variant_id}/`. Query filters (`family`, `search`, `status`, plus Shop `source`) remain for compatibility reads.
- Variant create, update, archive, reactivate and global set-default operations are retired in the canonical backend and return HTTP 405. The current Family-level active flow does not select a Variant. The separate sibling backend checkout is stale and still requires `variant_id`; do not treat it as the contract paired with `main`.
- Supported local integration is the `frontend/parallel-foundation` frontend pointed at the canonical `main` backend. The `main/frontend` copy still has Variant controls and the sibling checkout's duplicate `apps/` backend still requires `variant_id`; both are deprecated and unsupported, despite remaining runnable. See `docs/ENVIRONMENTS.md`.
- New Shop Designs, Global Design Templates and Measurement Profiles are Family-based; active Design-list filtering is by Family. Existing Design/Profile response fields and worksheet export may still display a legacy Variant label. Historical rows and version/export meaning are preserved; no record was rewritten.
- Variant thumbnails are deferred: the Family image implementation is model/route-specific rather than a reusable single-image abstraction. No gallery, stock, price, cost, supplier, warehouse, or BOM fields are added to Variants.
- `GET/POST /api/v1/catalog/design-templates/` lists/creates global templates; `GET /api/v1/catalog/design-templates/{design_id}/` retrieves one. Main Supplier sees an active template's latest draft or published version. Other authenticated Shop members can retrieve only active templates with a published version and see published data only; draft-only, archived, or unavailable templates return 404.
- A Shop design may be published by an active Shop ADMIN or an active STAFF member assigned the `STITCHING` Work Function. “Tailor” is that assigned STAFF function, not a new access role. Global template publication remains Main Supplier-only.
- Published design versions are immutable. New drafts snapshot selected style names/translations/reference images; reusable StyleOption images remain source-linked and copies remain independent. Reference image bytes are private, served only through authorized endpoints, and accept JPEG/PNG/WebP uploads.
- Historical migration `catalog.0012_seed_mens_shirt_design_defaults` seeds the Men’s Shirt Family mapping (ordered Sleeve, Collar, Cuff, Pocket, Placket, Embroidery, and Color groups) and published Global Design Templates that carry legacy Variant references. The `variant` query on `GET /api/v1/catalog/design-templates/` is a compatibility/read filter, not an active selection workflow; active configuration/rendering is Family-based.
- **Confidentiality limitation:** this GitHub repository is public and the generated `schema.yml` is committed. Protecting the live `/api/schema/` route does not make the committed schema confidential. If API contract confidentiality is required, repository visibility or schema publication must be changed through an owner-approved action.

Shop Style Options use the explicit Shop API: `GET/POST /api/v1/shops/{shop_id}/catalog/style-options/` and `PATCH /api/v1/shops/{shop_id}/catalog/style-options/{option_id}/`. The Shop list returns global defaults and Shop-owned reusable Catalog options; Design snapshot copies (`source_style_option` set) remain attached to their historical Designs but are not selectable Catalog options. PATCH accepts exactly one of `{"translations":[{"locale":"en","name":"New name"}]}` or `{"is_active":false}`. Translation updates merge only supplied locales; omitted locales/descriptions remain unchanged. Code, option group, and Shop owner are immutable. Existing ADMIN/STAFF/Main Supplier Shop-context write access remains; VIEWER cannot edit. Foreign-Shop and global-default edits through the Shop route return non-disclosing 404. Each Style Option exposes one current reusable reference image; an upload accepts exactly one image and atomically replaces which image is current. Previous image records/objects are retained so historical Design selections remain source-linked and unchanged.

## T4-03 measurements and materials contract

Every route requires authenticated, password-change-complete access and the existing explicit URL-path Shop context. Foreign, unauthorized, inactive, removed, and nonexistent Shop/resource requests do not expose another Shop's data.

- `GET/POST /api/v1/shops/{shop_id}/measurement-definitions/`; GET supports optional `family_id` and `locale=en|ar-KW|bn|ur` (no active Variant filter). Results use page-number pagination and stable Family mapping order. It returns global approved definitions plus active definitions owned by this Shop only.
- `GET/PATCH /api/v1/shops/{shop_id}/measurement-definitions/{definition_id}/`; `POST .../{definition_id}/archive/`. Create body includes stable `code`, optional `group_code`/`sort_order`, unique translations including English, and one or more Family-only `{family_id}` mappings. Patch changes only safe metadata/translations; codes and mappings are immutable. Global/system definitions are read-only. Archive is one-way; no delete/restore route.
- Client profiles: `GET/POST /api/v1/shops/{shop_id}/clients/{client_id}/measurement-profiles/`; profile detail GET; nested sets `GET/POST .../{profile_id}/sets/`; set detail GET; copy `POST .../{profile_id}/sets/{set_id}/copy/`; compare `GET .../{profile_id}/compare/?from_set_id={uuid}&to_set_id={uuid}`.
- Related Person profiles and the same nested set/copy/compare routes are under `/api/v1/shops/{shop_id}/clients/{client_id}/related-persons/{related_person_id}/measurement-profiles/`. Person/profile/set relations are checked inside the selected Shop and nested Primary Client. The pre-existing RelatedPerson→Primary Client link is used by R5-01 invoice ownership; billing remains associated with the Primary Client while optionally recording that Related Person.
- Worksheet export: `GET .../{profile_id}/worksheet.pdf` is available beneath both the Client and Related Person profile paths. Optional `measurement_set_id` selects an immutable version (otherwise latest); optional `design_id` resolves an authorized active Design for this request only. The current lookup still matches the Profile's legacy `variant_id` as well as Family; for Family-level Profiles this selects Family-level Designs. Keep only if required to render existing history, then remove after verified consumers/data are migrated. The private portrait A5 PDF is `no-store` and paginates long content onto additional A5 pages; it does not persist a Design↔Measurement relation, and its demo-only Bill/Estimate placeholder is presentation text—not billing data or an invoice.
- Profile create body: `{family_id}` only. Set create body: `{"values":[{"definition_id":"<uuid>","value":"36.1250","unit":"INCH|CM"}]}`. Values may be partial but each supplied value requires its explicit unit. Set/value update/delete is unavailable. Copy creates a new independent version with `copied_from` provenance. Historical English/culture labels are snapshots. Comparison returns raw values/units and a numeric `difference` only for matching units; it never converts.
- Materials: `GET/POST /api/v1/shops/{shop_id}/materials/`, `GET/PATCH .../materials/{material_id}/`, and `POST .../{material_id}/archive/`. The original T4-03 API accepts only `name`, optional Shop-local `code`, and `description`; status is response-only. `include_archived=true` is restricted to Shop ADMIN/Main Supplier. T4-03A adds the distinct inventory API below without changing measurement contracts.

## Private catalog media upload

- `POST /api/v1/catalog/media/uploads/` authorizes Main Supplier uploads to global catalog targets. `POST /api/v1/shops/{shop_id}/catalog/media/uploads/` uses the selected Shop and its existing write policy. Both accept `action=authorize` with target kind/UUID, MIME type and expected byte size, followed by `action=complete` with the short-lived upload token after a direct private-object PUT.
- Only JPEG, PNG and WebP up to 10 MB are accepted. Authorization is bound to actor, Shop, target, MIME and byte size; completion re-resolves the target, checks object metadata/size, and runs the existing image validation/optimization service. Responses carrying signed upload URLs/tokens are `no-store`. Images remain private and served through authorized application routes.

Measurement authorization: Shop ADMIN and Main Supplier in the selected Shop have full measurement access/custom-definition management. Active STAFF require `MEASUREMENT` in addition to active same-Shop membership for measurement reads/writes; STAFF may not archive definitions and may edit only their own safe custom-definition metadata. STAFF without the function and VIEWER cannot read measurement PII/history. Materials: ADMIN/Main Supplier selected-Shop manage; STAFF/VIEWER read active records only, no Work Function required. Work Function by itself never grants access.

## T4-03A inventory contract (implemented and validated locally)

- All endpoints require authentication, completed password-change gate, and explicit `/shops/{shop_id}/` context. Foreign, inactive, unavailable, and nonexistent Shop/item access is non-disclosing.
- `GET/POST /api/v1/shops/{shop_id}/inventory/items/`; `GET/PATCH /api/v1/shops/{shop_id}/inventory/items/{material_id}/`; `POST .../{material_id}/opening/`; `POST .../{material_id}/stock-in/`; `POST .../{material_id}/adjust/`; `GET .../{material_id}/movements/`; `POST .../{material_id}/archive/`.
- `POST /api/v1/shops/{shop_id}/materials/{material_id}/enable-inventory/` explicitly classifies a legacy Material and creates a zero balance, never opening stock. Create-item accepts name/code/description/category/stock_unit. Mutation bodies contain only quantity/reason; adjustment additionally accepts direction `IN|OUT`. Shop, actor, resulting balances, snapshots, and movement type are server-controlled.
- List is active-only by default, page-number paginated (20), deterministic by name/UUID, and supports `category`, `search` across name/code, and manager-only `include_archived=true`. Response quantities are Decimal strings and include on_hand/reserved/available/unit. Movement history is read-only and manager-only; archived history remains accessible to managers.
- Main Supplier and same-Shop ADMIN may manage/adjust/archive and read history; STAFF/VIEWER may read active selector data only. Work-linked reserve/release/consume/return is not exposed before Work exists.

`GET /api/v1/auth/csrf/` is a public, non-authenticating bootstrap for credentialed browser clients. It issues the host-only CSRF cookie and returns a masked `csrf_token` with `Cache-Control: no-store`; it returns no access or refresh credential. Staging allows credentialed CORS only from `https://staging.birky.com`, and refresh/logout remain CSRF-protected.

## Target V1 application API

The complete V1 API does not yet exist. Implemented local contracts include supplier/back-office/shop, clients/related persons, catalog, works/production, and the unpublished Phase 5 billing/pricing/history/document additions described above. Supplier-wide financial reporting, background storage jobs, AI, and integration contracts remain planned or incomplete under the canonical target architecture. Backend authorization, Shop isolation, object permissions, workflow rules, and financial rules remain authoritative.

### Approved future contract requirements

- Preserve `/api/v1/` and document OpenAPI contracts, pagination, safe filters, machine-readable stable error codes, translated human display messages, and request/correlation IDs.
- Current local auth contract: login-enabled accounts use the entered User ID (`login_id`) and approved legacy aliases in one identifier/credential flow. User ID casing is stored/displayed as entered (apart from trimming outer whitespace), with case-insensitive uniqueness and login matching. The generated `user_code` is an internal stable reference and compatible legacy alias. New/changed credentials are six-digit PINs; changes revoke sessions. Refresh remains HttpOnly-cookie/CSRF protected, rotated and blacklisted; initial/reset PINs are generated and returned once with `Cache-Control: no-store`. Email self-service recovery is removed; Shop Admin recovery requires registered-phone request and authorized Back Office approval. No phone verification provider is included.
- **Historical T3-04A identity baseline, extended by the current local transition:** UUID remains `id` and JWT `user_id`; generated `user_code` remains an internal permanent reference, while the human-facing User ID is the value entered at account provisioning. Normal Users may omit email/phone. Main Supplier authority remains unchanged; Shop Admin reset scope is active same-Shop STAFF only. Earlier identity/recovery wording is superseded by the current auth contract above.
- **Published T3-04B membership contract:** role changes, ADMIN hierarchy/cardinality, lifecycle, capacity, first-ADMIN creation, and User deactivation use transactional services. Published T3-04B-USER-SCOPE adds immutable owning-Shop identity and same-Shop account/membership operations. T3-04C Work Function endpoints are implemented and published with exact-SHA CI green. **Published T3-05:** authorized Shop discovery/profile/statistics; Main Supplier-only settings and lifecycle; no Shop DELETE; scoped exact User-ID member lookup; capacity lower-bound enforcement; and hardened Django Admin. Preserve `/api/v1/tenants/` compatibility. T3-05 commit `3d21a0943006cd866bc19bc728cbec05daae1630` passed exact-SHA Project State Validation run `36614638187`.
- **T3-04C Work Function contract (implemented):** `GET` and `PUT /api/v1/shops/{shop_id}/memberships/{membership_id}/functions/` read or replace the membership's function set. Only an active ADMIN of the selected Shop may use it; Main Supplier, STAFF, VIEWER, cross-Shop, removed, and unavailable membership access is denied without granting function-based authority. The set may be empty and accepts only the seven approved codes; duplicates/unknown values are validation errors. Response: `{membership_id, shop_id, functions}`. Functions never grant API permissions. Phase 4 still owns workflow-stage mapping; no workflow or assignment API is included.

### T3-02A endpoint baseline (historical; current auth rules above take precedence)

- `POST /api/v1/auth/login/`: accepts the shared identifier/credential contract with the entered User ID (`login_id`) and approved legacy aliases; legacy `{email,password}` remains supported. New credentials are six-digit PINs; the credential field remains compatible with existing legacy passwords. Returns UUID and profile identifiers; refresh remains in the HttpOnly cookie. Authentication failures are generic.
- `POST /api/v1/auth/users/`: Main Supplier Admin only. Accepts required first name and optional last name/email/E.164 phone. Login-enabled accounts receive the User ID supplied in `login_id` and a one-time temporary six-digit PIN; Viewer records receive no User ID/PIN and cannot authenticate. Credentials are returned once with no-store headers. Anonymous registration is denied.
- `GET /api/v1/auth/users/me/` and `PATCH /api/v1/auth/users/update_profile/`: authenticated self profile/preferences. Locale and appearance are writable; phone and account activation are not self-service fields.
- `PATCH /api/v1/auth/users/{uuid}/`: Main Supplier Admin may manage phone; ordinary users remain restricted to their own profile and cannot change phone.
- `POST /api/v1/auth/users/password/change/`: requires the current credential and a validated matching new credential, revokes existing sessions, and clears refresh cookie. An initial-credential user may access this operation while other protected API use is gated; PIN-format validation applies to PIN creation/change, not the shared login field.
- Email self-service credential reset is intentionally not part of the approved recovery model; the former public email reset request/confirm routes are removed. Shop Admin recovery uses phone request followed by authorized Back Office approval. Staff credentials are reset by their own Shop ADMIN.
- `POST /api/v1/auth/users/{uuid}/reset-credentials/`: Main Supplier authority remains unchanged; a Shop ADMIN may reset only an active same-Shop STAFF account. The generated temporary six-digit PIN is returned once with `Cache-Control: no-store` and `Pragma: no-cache`; sessions are revoked and a credential change is required. Global User DELETE is disabled; Django Admin's arbitrary password editor and delete action are disabled.
- Published T3-04B User-Scope account creation: `POST /api/v1/auth/users/` requires Main Supplier authority and explicit `shop`, `role`, and required `first_name`; it creates a new Shop-owned account and first membership atomically. `POST /api/v1/shops/{shop_id}/users/` derives the Shop from the authorized URL context and permits its Shop ADMIN to create only STAFF/VIEWER. Login-enabled accounts receive the user-entered User ID (API field `login_id`) and a one-time six-digit temporary PIN; Viewer records receive no User ID or PIN and cannot authenticate. Existing user passwords continue to work during the transition. Credentials are returned once with `Cache-Control: no-store` / `Pragma: no-cache`. Existing account assignment/move is rejected; normal global list/read visibility is not added.
- Shop/Tenant list and detail retain `/api/v1/tenants/`. Main Supplier responses may include settings and management statistics; a same-Shop ADMIN may receive management statistics but not settings; STAFF/VIEWER receive neither. Ordinary reads are membership-scoped; inactive memberships see an inactive historical profile only. Shop update/settings are Main Supplier-only, generic lifecycle mutation and DELETE are unavailable. These T3-05 changes are published with exact-SHA CI green.
- `GET /api/v1/shops/{shop_id}/context/` is the T3-03 context contract. The UUID path selects exactly one Shop; after JWT authentication and the password-change gate, the endpoint resolves an active Shop and active membership or explicit Main Supplier authority. Response fields are `shop_id`, selected-Shop `role` (null for Main Supplier), `is_main_supplier`, and `work_functions`. `work_functions` contains only the current actor's assigned codes in the selected Shop, in canonical order; Main Supplier returns an empty list because it has no Shop membership in this context. Shop defaults are not returned.
- T3-04C adds `GET`/`PUT /api/v1/shops/{shop_id}/memberships/{membership_id}/functions/`. PUT replaces the complete set using `{"functions":["SALES", "MEASUREMENT"]}` (empty list is allowed); both methods return the membership UUID, Shop UUID, and catalog-ordered code list. Shop-context authorization is required, followed by an active same-Shop ADMIN check; foreign, removed, or nonexistent memberships are indistinguishable. Work Functions are descriptive only.
- `GET /api/v1/tenants/{shop_id}/stats/` is available to Main Supplier for any Shop and to an active same-Shop ADMIN only; role-insufficient same-Shop requests receive 403 and foreign/nonexistent Shop requests are scoped to 404. `GET /api/v1/tenants/{shop_id}/member-lookup/?user_code=...` performs exact lookup only among current or removed membership history in the selected Shop and returns User ID/display name/role/status; it never attaches an account or searches the global User directory. These T3-05 endpoints are published with exact-SHA CI green.
- The account/login routes above implement the published T3-04A User-ID contract. T3-04B ADMIN membership lifecycle actions are published. Work Function management is implemented under T3-04C. Do not infer additional endpoint paths or response shapes.
- Foreign, unauthorized, inactive, soft-deleted, unavailable, and nonexistent Shop requests return the same `404` envelope/code (`shop_context_unavailable`) without revealing Shop existence. Unauthenticated, invalid, and revoked authentication retain `401`. Malformed UUIDs do not match the UUID route and return 404 at URL resolution.
- Shop-scoped endpoints use `/shops/{shop_id}/...`; authorization precedes Shop-default access. Preferences never grant access. T3-04 provides a trusted-context scoped queryset/write-ownership mixin and selected-Shop object permission contract. T4-01 Clients/Related Persons is the first business-resource API and adopts/tests these primitives; future routes must do likewise.
### T4-01 Clients and Related Persons (implemented)

All routes require authenticated, password-change-complete access and explicit authorized Shop context:

- `GET/POST /api/v1/shops/{shop_id}/clients/`
- `GET/PUT/PATCH/DELETE /api/v1/shops/{shop_id}/clients/{client_uuid}/`
- `GET/POST /api/v1/shops/{shop_id}/clients/{client_uuid}/related-persons/`
- `GET/PUT/PATCH/DELETE /api/v1/shops/{shop_id}/clients/{client_uuid}/related-persons/{related_person_uuid}/`

UUIDs are immutable identities; no Client code is returned. Lists use page-number pagination (`count`, `next`, `previous`, `results`), page size 20, and deterministic name/UUID ordering. Optional `search` performs Unicode-aware name containment, normalized-phone prefix matching, and exact UUID matching. Deleted records are omitted. Work-number search is not implemented until T4-04.

Create body: `{"name":"...","phone":"optional","email":"optional"}`. Updates accept the same fields; Shop/Primary Client ownership is server/path-derived. RelatedPerson responses also include `primary_client_id`; R5-01 Work billing stays owned by that Primary Client and may also identify the Related Person.

Successful writes include `warnings`, e.g. `[{"code":"possible_duplicate","field":"phone","matches":[{"id":"<uuid>","name":"..."}]}]`. Warnings cover same-Shop records of the same type only, return at most 10 references, do not reject or merge, and never reveal another Shop. Contact updates return warnings only when phone/email changed. Empty warnings means no same-Shop duplicate was found.

Main Supplier and active same-Shop ADMIN have read/create/update/soft-delete. Active STAFF has read/create/update. Active VIEWER is read-only. Inactive/removed memberships have no operational access. Work Functions do not alter Client permissions. Foreign/missing record and nested-parent lookups are non-disclosing 404s. DELETE soft-deletes and returns 204; there is no restore endpoint.

Phone search normalization applies Unicode NFKC, maps Unicode decimal digits to ASCII, removes other characters, and preserves `+` only when it is the first non-whitespace character. No country/region is inferred. Email matching uses trimmed case-folded text; stored contact values are trimmed but are not rewritten to the search key. Client/RelatedPerson duplicates are allowed; there is no phone/email uniqueness constraint.

### GARMENT-SYSTEM-BACKEND-01 (implemented locally; not yet released)

Authenticated, password-change-complete Shop-context routes; writes require a same-Shop ADMIN or STAFF (Main Supplier also retains authorized access). Global catalog mutation remains Main Supplier-only.

- `GET/POST /api/v1/shops/{shop_id}/catalog/garment-families/` lists global active defaults plus this Shop's active custom families, or creates a Shop-owned family with immutable `code` and English-required localized `translations` (`[{"locale":"en","name":"...","description":"optional"}]`). Response includes `tenant`, `code`, translated `name`, `status`, and private-image metadata. Other Shops' rows are never returned.
- `GET/POST /api/v1/shops/{shop_id}/catalog/option-groups/` lists reusable global groups plus this Shop's groups, or creates a Shop-owned group with the same translation contract. Response includes `is_global`; family IDs are scoped to the requesting Shop plus global families.
- `GET/PUT /api/v1/shops/{shop_id}/catalog/garment-families/{family_id}/option-groups/` reads configuration for an active global or same-Shop family, but PUT replaces mappings only for a family owned by the selected Shop. A global family is read-only through this Shop route; attempts to write it return 403, including Main Supplier calls made through the Shop route. Main Supplier updates global defaults through `/api/v1/catalog/families/{family_id}/option-groups/`. Shop-owned families may map global or same-Shop groups. PUT body: `{"option_groups":[{"option_group_id":"<uuid>","selection_mode":"SINGLE|MULTI","is_required":false,"sort_order":0}]}`. Global Catalog’s legacy `option_group_ids` request remains accepted and defaults those mappings to optional `MULTI`.
- The local `main` backend retains Variant list/detail GET routes for legacy reads, but rejects Variant writes with 405. Measurement definition mappings accept Family only after migration `0024`.
- The local `main` `POST /api/v1/shops/{shop_id}/designs/` contract is Family-only and does not declare `variant_id`. The sibling backend checkout still requires `variant_id`; do not treat either local contract mismatch as a deployed API guarantee. New active Designs must be Family-level. Published DesignVersions retain their configured Style Group validation.
- Shop Design editing reads the Shop-scoped `GET /api/v1/shops/{shop_id}/catalog/garment-families/{family_id}/option-groups/` mapping and the corresponding Shop-visible Style Options; this is the same garment-part source used by Measurements. `PATCH /api/v1/shops/{shop_id}/designs/{design_id}/` updates the current Draft name. `PATCH /api/v1/shops/{shop_id}/design-versions/{version_id}/selections/{selection_id}/` replaces an option only within that selection's existing configured group; published versions are immutable and Shop authorization is enforced server-side.
- Measurement-set POST accepts optional `design_version_id`, which must reference an available published DesignVersion whose Family matches the Profile; no Variant match is part of the active create contract. Response returns this immutable link. Copying a measurement set preserves the same DesignVersion link. Worksheet export still has a legacy Variant-aware Design lookup as noted above.

Migration `0019_shop_owned_garment_systems` is forward-only and keeps existing global rows/IDs. These routes and schema changes are implemented locally; no deployment or release is implied.
- Payment writes require idempotency and explicit safe outcomes. Invoices/receipts/reports may accept a per-document locale override without changing canonical data or money.

## Future documentation requirements

For each implemented endpoint, record its method and path, authentication and authorization expectations, request and response shape, validation errors, side effects, idempotency behavior, pagination/filtering, and compatibility policy.
# Family-level Design and Measurement contracts — current policy / implementation status

- The approved active contract is Family-level. The local `main` backend `DesignCreateSerializer` accepts `family_id` and `name` and does not declare `variant_id`; however, the `main` frontend still displays Variant controls and submits a `variant_id` property. The sibling backend checkout still requires `variant_id` to create a Design. These local contract mismatches are not verified as deployed behavior.
- The `main` Design list still supports a `variant` query filter for legacy rows; the sibling Orders UI still uses `design.variant` when matching Profiles. These are residual active dependencies, not approved active Variant behavior.
- Measurement definition filtering uses `family_id` and `locale`.
- Measurement mapping create accepts `family_id` and optional `sort_order`.
- The `main` Measurement Profile create contract accepts `family_id` only; its response may expose nullable `variant` for historical records. Model validation still permits a non-null Variant through direct ORM creation.
- Design responses may expose nullable `variant` for legacy/history reads; new active Design creation must remain Family-level.
