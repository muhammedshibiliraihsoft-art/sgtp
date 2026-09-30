# SGTP frontend foundation

This isolated React/Vite shell is a preparation track, not Phase 7 completion. It contains no live business workflows and is not connected to authentication or business APIs.

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
Current unfinished Work/business functionality remains safely behind mock adapters. No live production endpoints are connected.

**F. SECURITY**
Never place secrets, database credentials, or private API keys in `VITE_*` values. Browser frontend environment values are inherently public.

**G. CANONICAL OWNERSHIP**
`main` remains the canonical backend/integration branch. The preview branch is strictly isolated.

**H. DEPLOYMENT FLOW**
Frontend branch → Validation (typecheck/lint/test) → Reviewed commit → Push to origin → Cloudflare client preview deployment triggers.
(Do not merge to `main` for preview updates.)

## SGTP foundation scope

- React + TypeScript + Vite, React Router, Tailwind CSS v4.
- Responsive sign-in and workspace-preview shells; no public registration, live session, or business operations.
- English, `ar-KW`, Bangla, and Urdu locale support. Arabic and Urdu are RTL; English and Bangla are LTR. English is fallback.
- Light, Dark, and System appearance preference; typed adapter/result contracts are not live endpoints or authorization logic.
- Intentional `_headers` ensures the temporary preview is not indexed by search engines (`X-Robots-Tag: noindex, nofollow`).

Run `npm ci`, `npm run dev`, `npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`. Ordinary Users have one backend-resolved owning Shop. Do not add a normal-user Shop selector. Read repository and frontend `AGENTS.md` before continuing.
