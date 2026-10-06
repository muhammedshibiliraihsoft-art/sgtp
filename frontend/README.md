# SGTP frontend

This React/Vite application is not Phase 7 completion. The approved `BACKOFFICE-01` slice adds a live Main Supplier Back Office backed by the existing Django Shop APIs; the other unfinished Work/business views remain mock-backed.

## Cloudflare Pages Client Preview

**A. PURPOSE**
This Cloudflare deployment is a temporary client-preview environment intended solely for UX and visual design reviews (themes, navigation, layout).

**B. SOURCE BRANCH**
`main` is the canonical development/integration branch. The existing Cloudflare Pages preview's configured source branch is an external setting and was not verified here; do not treat this document as evidence that Pages has been remapped.

**C. BUILD SETTINGS**
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Build Output Directory:** `dist`
- **Node Version:** `20` (specified in `.node-version`)

**D. SCOPE & LIMITATIONS**
The preview demonstrates current frontend UX/design ONLY. It is not full Phase 7 completion. It does not imply unfinished backend APIs are implemented.

**E. MOCK BOUNDARY**
The Work page and unfinished business views remain behind mock adapters. The Main Supplier Back Office calls the existing `/api/v1/tenants/` contract on the configured API origin; it does not use Work mock content.

**F. SECURITY**
Never place secrets, database credentials, or private API keys in `VITE_*` values. Browser frontend environment values are inherently public.

**G. CANONICAL OWNERSHIP**
`main` is the canonical frontend/backend integration branch. `frontend/parallel-foundation` is a legacy source worktree and must remain intact until its local changes are reconciled and verified.

**H. DEPLOYMENT FLOW**
Reconcile frontend work on `main` → typecheck/lint/tests/build → review → publish only with explicit authorization. Cloudflare preview behavior depends on its external branch mapping and is not confirmed by this repository documentation.

## SGTP foundation scope

- React + TypeScript + Vite, React Router, Tailwind CSS v4.
- Responsive sign-in and workspace-preview shells plus the Main Supplier Back Office routes `/backoffice`, `/backoffice/shops`, `/backoffice/shops/new`, and `/backoffice/shops/:shopId`.
- Main Supplier Back Office supports real Shop list/search/filter/order/pagination, atomic Shop + first-ADMIN creation, Shop detail/edit, and activation/deactivation through `/api/v1/tenants/`. The one-time initial User ID/password is held in component memory for display and is not stored in Web Storage.
- English, `ar-KW`, Bangla, and Urdu locale support. Arabic and Urdu are RTL; English and Bangla are LTR. English is fallback.
- Light, Dark, and System appearance preference; typed adapter/result contracts are not live endpoints or authorization logic.
- Intentional `_headers` ensures the temporary preview is not indexed by search engines (`X-Robots-Tag: noindex, nofollow`).

## Catalog and Designs integration status

- Shop Catalog and Main Supplier Global Catalog read live catalog APIs. Shop users can browse/search paginated active garment families; the responsive Family drawer contains that family's variants and assigned style groups, with variant details/actions and the next Designs step in the same flow. Main Supplier manages global variants within a Family rather than a bulk Variants tab. Family images and lifecycle actions use the existing protected APIs.
- Shop style options are grouped under their backend Option Groups (for example, Collar and Cuff); each group card expands to show its options and provides a group-specific add action.
- Shop Designs and Global Design Templates use the backend design APIs for listing, archiving, draft selections, version publishing, and private reference-image uploads. Shop users can create a draft design from an existing family and Shop/global variant.
- API responses and uploads follow the backend serializer contract. Catalog and design screens do not fall back to invented mock records when the service request fails.
- The current UI does not offer Option Group or Global Template creation forms. Those controls need their own reviewed frontend slice even though the backend has the corresponding protected API contracts.
- Clients and Shop Users use their accepted live integrations. The Measurement workspace uses real Client, catalog/design, inventory-read, and immutable Measurement APIs. Work and other unfinished business views remain mock-backed until their individual integrations are accepted. Inventory management has no dedicated frontend screen in this branch yet.

## Measurement workflow integration

- `/clients/:clientId/measurements` uses selected-Shop context, backend Client/Related Person data, active Family/Variant catalog data, the ordered backend Family → Option Group mapping, global and Shop Designs, backend Measurement Definitions, immutable Profiles/Sets, and the inventory selector’s read-only availability data.
- Men’s Shirt has three backend-published defaults: Classic Formal Shirt, Smart Casual Shirt, and Modern Evening Shirt. The visible style sections come only from the backend Family mapping; the UI does not construct a separate style list.
- Values require an explicit CM or INCH choice and Decimal input. Save, profile creation, design save, and copy actions are guarded against duplicate in-flight requests. Existing versions remain read-only; correction means saving a new version.
- No Work record, Cutting stage, stock reservation, or inventory deduction is created by the workflow.

## Reusable style image references

- Main Supplier Global Catalog → Style Options supports private reference-image uploads for existing global Style Options. New global options can select optional images at creation; after the option is created, the files are uploaded through the existing private media API to R2.
- Shop Catalog → Style Options allows an optional private reference-image upload while creating a Shop-owned Style Option.
- Selecting a Shop-owned option opens a responsive preview/editor: its English name can be updated through the existing Shop-context PATCH API, and one private reference image can be added or replaced with upload progress. Global options remain read-only in the Shop editor. Each style option displays one current image; historical Design snapshots retain their original references. A failed post-create upload can be retried without creating the option again.
- The Global Design Template editor also supports adding a reusable image to a selected Style Option. This is distinct from the existing Design Version `Reference images` upload, which remains attached only to that design version.
- Measurements read `StyleOption.reference_images` from the backend; uploaded images therefore appear on the matching option card without listing R2 folders or exposing public object URLs. This display path introduces no additional permission behavior.

## Local loading characteristics

- Frontend routes are loaded on demand; the login illustration uses a responsive `<picture>` so only the matching viewport asset is requested. Catalog Style Options load their required option groups and options concurrently without fetching unrelated garment families.
- Identical concurrent default GET requests share one in-flight request. There is no persistent response cache, and mutations and auth changes invalidate in-flight sharing.
- Local Vite `/api` currently proxies to the Render staging backend. This preserves the existing Shop data and login workflow but makes local API latency dependent on the remote service/network; the local database is not an equivalent replacement without Shop data.
- The local performance pass shares Shop context across route navigation, limits Main Supplier Catalog requests to the active tab, filters already-loaded Measurement designs on variant changes, and debounces Back Office Shop/Inventory searches. These reduce avoidable requests but do not guarantee zero remote latency; authenticated browser timing remains unverified.

## Keyboard accessibility

- `ACCESSIBILITY.md` documents the shared keyboard interaction expectations. Components use native control behavior where possible; custom listboxes, card grids, tabs, and modal focus handling have focused tests.
- Responsive/authenticated manual checks are still required at desktop and phone sizes before production readiness.

## Local handoff — Catalog style grouping (2026-10-03)

- The Shop Catalog `Style Options` tab now renders backend Option Groups as expandable cards; options are listed inside their own group, with a group-specific add action. The current backend already provides the groups and Shop-scoped options, so no API or schema changes were needed.
- Local validation: `npm run build` PASS; `python scripts/verify_project_state.py` PASS with the expected dirty-worktree and test-discovery warnings; `git diff --check` PASS. Tests were not run.
- The active Vite server in `C:\Users\Admin\Documents\ChatGPT\django 2\sgtp-frontend\frontend` serves the updated Catalog module at port 5173. Open Catalog → Style Options, then expand Collar or Cuff. These changes are local-only and are not committed, pushed, or deployed.

## Local handoff — Shop Catalog and Design selection UX (2026-10-03)

- Kept the Shop Catalog on backend-provided Option Group cards and widened Catalog/Design content on desktop while keeping the existing app shell and compact layouts at mobile/tablet widths.
- Design style selection now presents active options grouped into selectable cards. If the selected family has no active groups or options, it explains the missing configuration and points Shop users to the Main Supplier; no Shop-side global configuration permission was added.
- Shop Design list cards show family, variant, status, and version; the empty state guides design creation. Creation is disabled unless the Shop has a family with an available variant, and links to Catalog when a Shop variant is needed.
- Validation: `npm run typecheck`, `npm run build`, and `npm test -- --run` PASS (47 tests); `npm run lint` exits 0 with six warnings in unchanged files; `git diff --check` PASS; `python scripts/verify_project_state.py` PASS with dirty-worktree and test-discovery warnings.
- Local only. No commit, push, or deployment was performed.

## Local handoff — Garment Families integration (2026-10-03)

- Main Supplier Global Catalog now uses the authenticated Family endpoints for server-side search/status/pagination, Family creation, translation updates, archive/reactivate, private image upload/removal, and ordered Option Group assignment. Family codes remain read-only after creation. Existing Group and Global Style Option screens remain available.
- Shop Catalog now presents active Families as browse-only cards, supports backend search/pagination, opens Family details and assigned style groups, and filters the existing Shop Variant/Design views by selected Family. Family management controls remain in the Main Supplier Back Office.
- Kept the existing app shell, design tokens, mobile drawer layout, and en/ar-KW/bn/ur locale resources. The API remains authoritative for authorization and archived Family restrictions.
- Validation: `npm run typecheck`, `npm test` (59 tests), and `npm run build` PASS; `git diff --check` PASS (Git printed expected CRLF/LF working-copy notices). `npm run lint` exits 0 with six existing warnings in unchanged shared files (`App.tsx`, `useCurrentShop.ts`, `usePrivateImage.ts`, `ClientForm.tsx`, and `UsersPage.tsx`).
- Responsive layout uses fluid card columns (250px minimum), one-column phone layout, a full-height phone sheet, semantic layout tokens, and logical inline positioning for RTL. Automated component/API tests cover list, search, count/pagination, browse-only detail, family-filtered Variants/Design navigation, Main Supplier create/edit/mapping/lifecycle/image controls. Authenticated visual checks at the requested desktop/tablet/phone sizes were not performed because the open localhost tab is at `/login`; credentials remain for the user to enter.

Run `npm ci`, `npm run dev`, `npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`. Ordinary Users have one backend-resolved owning Shop. Do not add a normal-user Shop selector. Read repository and frontend `AGENTS.md` before continuing.
