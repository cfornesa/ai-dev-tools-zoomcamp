# AI Dev Tools Zoomcamp

This repository contains independent projects. Commands must be run from the
project directory named below; the root directory is not a Compose project.

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
