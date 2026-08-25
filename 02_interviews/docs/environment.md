# Environment reference

Copy `.env.example` to `.env` in `02_interviews/` before using Compose. Values
in that file are local-only placeholders; replace secrets and provider values in
staging or production without committing them.

| Variable | Required | Used by | Purpose |
| --- | --- | --- | --- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose | Postgres/backend | Database identity; local defaults are non-secret development values. |
| `POSTGRES_PORT` | No | Compose | Host port for PostgreSQL; the container remains on 5432. |
| `DATABASE_URL` | Compose/backend commands | Backend/Alembic | SQLAlchemy connection URL. Compose uses the `postgres` service; local checks may use SQLite. |
| `DEV_ADMIN_EMAIL`, `DEV_ADMIN_PASSWORD` | No | Backend/browser smoke | Seeds a development administrator when both are set. |
| `ADMIN_SESSION_SECRET`, `INVITE_TOKEN_SECRET`, `CANVAS_TOKEN_SECRET` | Yes outside local | Backend/canvas-sync | Signs admin, candidate, and canvas credentials. |
| `INVITE_EXPIRY_MINUTES`, `APP_SESSION_TTL_MINUTES` | No | Backend | Credential lifetimes. |
| `FRONTEND_ORIGINS`, `WS_ALLOWED_ORIGINS` | Yes outside local | Backend | CORS and WebSocket origin allowlists. |
| `CANVAS_SYNC_URL`, `CANVAS_SYNC_INTERNAL_URL`, `CANVAS_SYNC_PORT`, `CANVAS_EDITOR_PORT`, `DRAWIO_STATE_DIR` | No | Backend/frontend/canvas-sync/Compose | Canvas service URLs, host ports, and durable XML state path. |
| `VITE_API_URL`, `VITE_CANVAS_SYNC_URL`, `VITE_DRAWIO_EDITOR_URL` | No | Vite frontend | Browser-facing backend, canvas-sync, and local editor URLs. |
| `VITE_SERVICE_MODE` | No | Vite frontend | `real` for Compose or `mock` for frontend-only work. |
| `VITE_CANVAS_MODE` | No | Vite/Compose | Selects the self-hosted draw.io-compatible path. |
| `GOOGLE_PROVIDER_MODE`, `GOOGLE_CLIENT_ID`, `GOOGLE_PUBLIC_KEY`, `GOOGLE_ISSUER`, `GOOGLE_ALLOWED_DOMAINS`, `GOOGLE_AUTO_APPROVE` | No | Backend/frontend | Federated administrator login configuration; disabled by default. |
| `RECAPTCHA_MODE`, `RECAPTCHA_SECRET`, `RECAPTCHA_ALLOWED_HOSTNAMES`, `RECAPTCHA_ALLOW_SCORE`, `RECAPTCHA_STEPUP_SCORE`, `RECAPTCHA_MAX_AGE_SECONDS` | No | Backend/frontend | Server-verified abuse signal; mock mode is used in local/CI. |
| `VITE_GOOGLE_CLIENT_ID`, `VITE_RECAPTCHA_MODE`, `VITE_RECAPTCHA_SITE_KEY` | No | Vite frontend | Public provider configuration only; never put provider secrets here. |
| `E2E_BASE_URL`, `TEST_DATABASE_URL` | No | Playwright/backend tests | Optional browser base URL and PostgreSQL migration-test URL. |

Common recovery:

- If port 5432 is occupied, set `POSTGRES_PORT=55432`; if 5173, 8000, 8787,
  or 8090 is occupied, set `FRONTEND_PORT`, `BACKEND_PORT`,
  `CANVAS_SYNC_PORT`, or `CANVAS_EDITOR_PORT` and update the corresponding
  browser URL.
- If the backend cannot resolve `postgres`, start through Compose or use a
  host-reachable `DATABASE_URL` for direct commands.
- If provider credentials are absent, keep Google disabled and reCAPTCHA in
  mock mode. Real provider credentials are never required for local tests.
- If only frontend work is needed, set `VITE_SERVICE_MODE=mock` and run the
  frontend independently; this intentionally does not test backend auth.

The project-level commands are documented in `README.md` and exposed through
the `Makefile`. `make test-all` runs local unit/build checks; `make e2e` requires
the Compose stack and Playwright's browser installation.
