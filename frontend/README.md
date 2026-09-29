# SGTP frontend foundation

This isolated React/Vite shell is a preparation track, not Phase 7 completion. It contains no live business workflows and is not connected to authentication or business APIs.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.

## SGTP foundation scope

- React + TypeScript + Vite, React Router, Tailwind CSS v4.
- Responsive sign-in and workspace-preview shells; no public registration, live session, or business operations.
- English, `ar-KW`, Bangla, and Urdu locale support. Arabic and Urdu are RTL; English and Bangla are LTR. English is fallback.
- Light, Dark, and System appearance preference; typed adapter/result contracts are not live endpoints or authorization logic.

Run `npm ci`, `npm run dev`, `npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`. Never put secrets in `VITE_*` values; they are exposed to browser code. Ordinary Users have one backend-resolved owning Shop. Do not add a normal-user Shop selector. Read repository and frontend `AGENTS.md` before continuing.
