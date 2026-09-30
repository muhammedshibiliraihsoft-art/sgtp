# Frontend workspace instructions

- This directory is owned by the parallel frontend foundation track on `frontend/parallel-foundation`.
- Read the repository-root `AGENTS.md` and relevant canonical `docs/` before work. Do not edit canonical cross-project documentation from this branch; frontend-specific notes belong here.
- This is preparation, not Phase 7/F7-01 completion. Implement only the explicitly confirmed task; do not create business workflows or silently advance to future frontend tasks.
- Backend APIs are authoritative for authentication, roles, permissions, Shop ownership/context, and business rules. UI routing or hidden controls never enforce authorization.
- Ordinary Users have one immutable owning Shop. Never add a normal-user Shop picker, multi-Shop account model, signup flow, or account-linking behavior.
- Keep unimplemented API behavior behind typed adapters/mocks. Do not invent endpoint paths or claim preview fixtures are live data.
- Preserve English, ar-KW, Bangla, and Urdu locale support; Arabic/Urdu use RTL and English/Bangla use LTR. Light/Dark/System are presentation preferences only.
- Do not add secrets to Vite `VITE_*` values; these are public client-side build variables.
- Keep all frontend implementation and frontend tests under `/frontend`; do not modify backend code/tests, migrations, deployment, or root application configuration in this track.

- The Cloudflare Pages client-preview deployment remains frontend-only. Never place backend secrets in `VITE_*` environment variables.
- The existence of the client preview does not authorize business/API implementation.
- Canonical root repository documentation (`docs/`) must not be edited from this frontend branch.
