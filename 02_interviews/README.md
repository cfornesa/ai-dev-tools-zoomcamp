# Interview Canvas MVP

## Local development

All commands in this section are scoped to the `02_interviews` Interview
Canvas project. The same stack can also be started from the repository root;
the root `compose.yaml` includes this file. Use the project directory when
running the Makefile and service-local tests.

From this directory, copy `.env.example` to `.env`, review the non-secret local
defaults, and start the isolated services:

```bash
cp .env.example .env
docker compose up --build
```

To rebuild after changing an image or dependency, run `docker compose build
--no-cache && docker compose up`. The same project-scoped Compose command works
from a clean checkout because it uses this directory's `.env.example`, relative
build contexts, health checks, dependencies, and named volumes.

The backend is available at `http://localhost:8000/docs`, the frontend at `http://localhost:5173`, canvas sync at `http://localhost:8787/health`, and the self-hosted editor at `http://localhost:8090/editor.html`. Stop with `docker compose down`; PostgreSQL and canvas XML data are retained in named volumes. Add `-v` only when intentionally resetting local data.

If local port 5432 is already occupied, set `POSTGRES_PORT=55432` in `.env`; the container remains on PostgreSQL's internal port 5432. Similarly, use `CANVAS_SYNC_PORT` or `CANVAS_EDITOR_PORT` for host conflicts and update the matching browser-facing `VITE_CANVAS_SYNC_URL` or `VITE_DRAWIO_EDITOR_URL` value.

The Makefile is the primary project-local command interface:

```bash
make help
make up
make test-all
make e2e
make down
```

For frontend-only work, set `VITE_SERVICE_MODE=mock` in `.env` and run
`cd frontend && npm run dev`. Mock mode provides seeded session/invite data and
deterministic failure states without FastAPI or PostgreSQL; the default `real`
mode uses the Compose-backed service boundary.

Run the equivalent direct checks from this directory with:

```bash
cd backend && uv run pytest
cd ../frontend && npm test && npm run build
cd canvas-sync && npm test && npm run typecheck
cd .. && DEV_ADMIN_EMAIL=admin@example.test DEV_ADMIN_PASSWORD=correct-horse npm run e2e
```

Apply migrations with `make migrate` while the Compose stack is running; this
executes Alembic inside the backend container. For a direct host command, set
`DATABASE_URL` to a host-reachable PostgreSQL URL before running `cd backend &&
uv run alembic upgrade head`. The PostgreSQL migration check is opt-in: set
`TEST_DATABASE_URL` and run `uv run pytest tests/test_migration.py`. For a
lightweight local backend profile, use `DATABASE_URL=sqlite:///./interviews.db`
and `make sqlite-check`; SQLite is supported for development verification but
PostgreSQL remains the default Compose/demo database.

The local development admin is created by setting `DEV_ADMIN_EMAIL` and `DEV_ADMIN_PASSWORD` before starting the backend. These values are never committed. With the Compose stack running, execute the browser smoke test from `frontend/` using `DEV_ADMIN_EMAIL=... DEV_ADMIN_PASSWORD=... npm run e2e`. The self-hosted canvas is the default live path; if its editor or sync service is unavailable, the live page shows a recoverable canvas error while preserving backend-owned session lifecycle, invitations, and evaluations.

Federated Google and reCAPTCHA providers are disabled/mock by default for local
and CI use. Configure real provider values only in a protected staging or
production environment; the manual verification checklist is in
`docs/authentication.md`. Public signup remains disabled.

The complete environment-variable inventory, required/optional status, and
port-conflict recovery guidance is in `docs/environment.md`.

The MVP deliberately excludes shared code editing, code execution, email delivery, production SSO, load testing, and production deployment checks. See
`docs/spec.md` for the product contract and `openapi.yaml` for the REST
surface. Run `make contract-check` after API changes. The supported demo path
is administrator login → session/invite creation → candidate redemption →
shared canvas → facilitator end/extend → private evaluation.
