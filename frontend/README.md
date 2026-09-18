# ShadowWatch supervisor application

React/Vite workspace for the existing FastAPI and PostgreSQL analytics.

## Run locally

Start the populated backend in one terminal:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

In another terminal, from repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). The default same-origin
`/api` proxy forwards to `http://127.0.0.1:8000` without requiring backend CORS.
Optional `frontend/.env.local` values are documented in `.env.example`:

- `VITE_API_BASE_URL`: browser-visible API prefix, default `/api`.
- `API_PROXY_TARGET`: local Vite development/preview upstream, default port 8000.

Restart Vite after environment changes. Never place credentials in `VITE_*`
variables: Vite includes them in the public browser bundle.

## Verification

```bash
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
```

The E2E suite starts its own backend on port 8123 and Vite on port 5174, using the
existing backend virtual environment and PostgreSQL configuration. Both ports
must be free. Tests use the populated demo database, make read-only API requests,
and discover entities/findings dynamically. Error and empty states are tested
with browser request interception, not application fixtures. Browser installation
requires network access once. Failure traces are in ignored `test-results/`.

## Deployment

`npm run build` outputs `dist/`. Serve it with SPA fallback to `index.html` for
client routes and reverse-proxy `/api` to FastAPI. Vite's development proxy is not
included in the built files. An absolute cross-origin API URL additionally needs
server CORS configuration; the existing backend does not configure it.
`npm run preview` is a local build check, not a production server.

## Implementation

- `src/api/`: centralized URL, timeout, error and pagination handling.
- `src/context/`, `src/hooks/`: shared read-only workspace and cancellable requests.
- `src/pages/`: routed supervisor screens.
- `src/components/`: reusable tables, evidence, charts, workflow and shell.
- `src/utils/`: display formatting; no risk or priority scoring.

See [API inventory](../docs/frontend_api_inventory.md) and
[delivery/verification report](../docs/frontend_verification.md).
Human review controls are disabled until backend persistence is implemented.
