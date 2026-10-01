# TravelMate Web

The user-facing React application supports Supabase email/password authentication, optional configured OAuth providers, profile onboarding, and privacy preferences. It is separate from the admin application.

## Local development

Set the browser-safe values in the workspace `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-public-anon-key
VITE_AUTH_PROVIDERS=google,apple
```

Only include OAuth providers that are enabled in the Supabase project. Never put service-role keys or other server credentials in Vite variables.

From the repository root, run `npm run dev --workspace apps/web`. The app uses Supabase browser session persistence and sends the access token through a centralized API client.

## API coverage and current limits

The user app reads `/me`, `/me/profile`, `/me/preferences`, `/me/privacy`, and `/verification/status`, and submits the backend profile/preferences/privacy contracts. Profile completion is calculated by the backend. Profile photos use the secure `/media/uploads` presign/complete flow when R2 is configured; the browser never receives R2 credentials. Date of birth is excluded from browser draft storage and sent only to the profile API for authoritative 18+ validation.

English is the only translated resource currently shipped. i18next is configured with an English fallback and locale identifiers for major Indian languages, ready for reviewed translation resources.
# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

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
