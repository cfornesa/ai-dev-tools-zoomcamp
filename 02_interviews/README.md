# Interview Canvas MVP

## Local development

From this directory, copy `.env.example` to `.env`, then start the isolated services:

```bash
cp .env.example .env
DEV_ADMIN_EMAIL=admin@example.test DEV_ADMIN_PASSWORD=correct-horse docker compose up --build
```

The backend is available at `http://localhost:8000/docs`, the frontend at `http://localhost:5173`, and canvas sync at `http://localhost:8787/health`. Stop with `docker compose down`; PostgreSQL data is retained in the named `interviews-postgres` volume. Add `-v` only when intentionally resetting local data.

If local port 5432 is already occupied, set `POSTGRES_PORT=55432` in `.env`; the container remains on PostgreSQL's internal port 5432.

Run the project checks from this directory with:

```bash
cd backend && uv run pytest
cd ../frontend && npm test && npm run build
cd canvas-sync && npx tsc --noEmit --moduleResolution Bundler --module ESNext --target ES2022 --skipLibCheck src/server.ts
cd .. && DEV_ADMIN_EMAIL=admin@example.test DEV_ADMIN_PASSWORD=correct-horse npm run e2e
```

Apply migrations with `cd backend && uv run alembic upgrade head`. The PostgreSQL migration check is opt-in: set `TEST_DATABASE_URL` and run `uv run pytest tests/test_migration.py`.

The local development admin is created by setting `DEV_ADMIN_EMAIL` and `DEV_ADMIN_PASSWORD` before starting the backend. These values are never committed. With the Compose stack running, execute the browser smoke test from `frontend/` using `DEV_ADMIN_EMAIL=... DEV_ADMIN_PASSWORD=... npm run e2e`. Canvas sync is independently available; if it is unavailable, the live page shows a recoverable canvas error while preserving backend-owned session lifecycle, invitations, and evaluations.

The MVP deliberately excludes shared code editing, code execution, email delivery, production SSO, load testing, and production deployment checks. The supported demo path is administrator login → session/invite creation → candidate redemption → shared canvas → facilitator end/extend → private evaluation.
