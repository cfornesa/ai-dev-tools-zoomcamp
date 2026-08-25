.DEFAULT_GOAL := help

.PHONY: help up down test-backend test-frontend build-frontend test-canvas typecheck-canvas migrate e2e test-all contract-check sqlite-check compose-check

help:
	@printf '%s\n' 'Interview Canvas local commands:' '  make up               Start the Compose stack' '  make down             Stop services (retain database volume)' '  make test-backend     Run backend tests' '  make test-frontend    Run frontend unit tests' '  make build-frontend   Build the frontend' '  make test-canvas      Run canvas-sync lifecycle tests' '  make typecheck-canvas Type-check canvas-sync' '  make migrate          Apply Alembic migrations' '  make e2e              Run Playwright smoke tests' '  make test-all         Run local unit/build checks' '  make contract-check   Compare checked-in OpenAPI with FastAPI' '  make sqlite-check     Verify SQLite restart persistence'
	@printf '%s\n' '  make compose-check    Validate root and project Compose entrypoints'

up:
	docker compose up --build

down:
	docker compose down

test-backend:
	cd backend && uv run pytest

test-frontend:
	cd frontend && npm test

build-frontend:
	cd frontend && npm run build

typecheck-canvas:
	cd frontend/canvas-sync && npm run typecheck

test-canvas:
	cd frontend/canvas-sync && npm test

migrate:
	docker compose exec backend alembic upgrade head

e2e:
	set -a; [ ! -f .env ] || . ./.env; set +a; cd frontend && npm run e2e

contract-check:
	cd backend && uv run python scripts/compare_openapi.py

sqlite-check:
	cd backend && uv run pytest tests/test_sqlite_restart.py

compose-check:
	cd .. && docker compose config --services | awk 'BEGIN { expected["postgres"]; expected["backend"]; expected["frontend"]; expected["canvas-sync"]; expected["canvas-editor"] } { if ($$0 in expected) found[$$0]=1 } END { for (name in expected) if (!(name in found)) exit 1; if (length(found) != 5) exit 1 }'
	docker compose config --services | awk 'BEGIN { expected["postgres"]; expected["backend"]; expected["frontend"]; expected["canvas-sync"]; expected["canvas-editor"] } { if ($$0 in expected) found[$$0]=1 } END { for (name in expected) if (!(name in found)) exit 1; if (length(found) != 5) exit 1 }'
	docker compose config --quiet

test-all: test-backend test-frontend build-frontend typecheck-canvas test-canvas contract-check
