# SGTP frontend

This React/Vite application is not Phase 7 completion. The approved `BACKOFFICE-01` slice adds a live Main Supplier Back Office backed by the existing Django Shop APIs; the other unfinished Work/business views remain mock-backed.

## Cloudflare Pages Client Preview

**A. PURPOSE**
This Cloudflare deployment is a temporary client-preview environment intended solely for UX and visual design reviews (themes, navigation, layout).

**B. SOURCE BRANCH**
The preview is deployed *exclusively* from `frontend/parallel-foundation`.

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
`main` remains the canonical backend/integration branch. The preview branch is strictly isolated.

**H. DEPLOYMENT FLOW**
Frontend branch → Validation (typecheck/lint/test/build) → Reviewed commit → Push to origin → Cloudflare client preview deployment triggers automatically.
(Do not merge to `main` for preview updates. A branch push publishes a preview deployment.)

## SGTP foundation scope

- React + TypeScript + Vite, React Router, Tailwind CSS v4.
- Responsive sign-in and workspace-preview shells plus the Main Supplier Back Office routes `/backoffice`, `/backoffice/shops`, `/backoffice/shops/new`, and `/backoffice/shops/:shopId`.
- Main Supplier Back Office supports real Shop list/search/filter/order/pagination, atomic Shop + first-ADMIN creation, Shop detail/edit, and activation/deactivation through `/api/v1/tenants/`. The one-time initial User ID/password is held in component memory for display and is not stored in Web Storage.
- English, `ar-KW`, Bangla, and Urdu locale support. Arabic and Urdu are RTL; English and Bangla are LTR. English is fallback.
- Light, Dark, and System appearance preference; typed adapter/result contracts are not live endpoints or authorization logic.
- Intentional `_headers` ensures the temporary preview is not indexed by search engines (`X-Robots-Tag: noindex, nofollow`).

## Catalog and Designs integration status

- Shop Catalog and Main Supplier Global Catalog read live catalog APIs; Shop users can create Shop variants and style options, and Main Supplier can create global style options.
- Shop Designs and Global Design Templates use the backend design APIs for listing, archiving, draft selections, version publishing, and private reference-image uploads. Shop users can create a draft design from an existing family and Shop/global variant.
- API responses and uploads follow the backend serializer contract. Catalog and design screens do not fall back to invented mock records when the service request fails.
- Backend endpoints now support Main Supplier creation of Garment Families and Option Groups, global-variant listing, and Global Design Template detail retrieval. The current frontend still needs UI forms to call the new Family/Option Group create endpoints; Global Template creation UI also remains incomplete. These are frontend tasks, not missing backend routes.
- Clients, Shop Users, Work, and other unfinished business views remain mock-backed until their individual integrations are accepted. Measurements and Inventory have no frontend screens in this branch yet.

Run `npm ci`, `npm run dev`, `npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`. Ordinary Users have one backend-resolved owning Shop. Do not add a normal-user Shop selector. Read repository and frontend `AGENTS.md` before continuing.
