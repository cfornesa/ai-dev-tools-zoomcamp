# AI Dev Tools Zoomcamp

This repository contains independent projects. `01_todo` remains separate from
the Interview Canvas stack. The root Compose entrypoint includes only
`02_interviews` and is equivalent to running Compose in that project directory.

If `docker compose` previously reported `no configuration file provided`, run
it from this repository root (where `compose.yaml` now lives) or from
`02_interviews`.

## Interview Canvas from the repository root

```bash
cp .env.example .env
docker compose config
docker compose up --build
docker compose down                 # retain named volumes
docker compose down -v               # intentionally reset local data
```

The project-scoped commands remain supported:

```bash
cd 02_interviews
cp .env.example .env
docker compose up --build
make test-all
make e2e
```

If a host port is occupied, set `POSTGRES_PORT`, `CANVAS_SYNC_PORT`, or
`CANVAS_EDITOR_PORT` in the selected `.env`; keep the browser-facing Vite URLs
aligned with the changed ports. The full variable inventory is in
`02_interviews/.env.example` and `02_interviews/docs/environment.md`.

## Interview Canvas (`02_interviews`)

```bash
cd 02_interviews
cp .env.example .env
docker compose up --build       # start/rebuild the stack
docker compose down             # stop it and retain named volumes
docker compose down -v          # stop and intentionally remove local data
make test-all                   # backend/frontend/canvas checks
make e2e                        # browser checks (stack must be running)
```

The stack provides PostgreSQL, FastAPI, React, canvas-sync, and the local
canvas editor. See [02_interviews/README.md](02_interviews/README.md) for
ports, environment variables, and direct service commands.

## Todo (`01_todo`)

The Django task manager is separate and does not use the Interview Canvas
Compose stack. Run its checks from `01_todo` with `python manage.py test`.
