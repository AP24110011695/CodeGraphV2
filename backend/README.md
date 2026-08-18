# CodeGraph v2 backend

CodeGraph analyzes uploaded or cloned repositories, builds a dependency graph,
indexes source chunks, and exposes retrieval and chat APIs.

## Local development

Requires Python 3.12+, PostgreSQL 16 with the `vector` extension, and Redis 7.

```powershell
cd backend
Copy-Item .env.example .env
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

In another terminal, run the worker:

```powershell
cd backend
uv run celery -A app.workers.celery_app worker -Q analysis -l info
```

The API documentation is at `http://localhost:8000/docs`; health and metrics
are available at `/health` and `/metrics`.

## Docker Compose

At the repository root, create a `.env` containing at least a strong
`SECRET_KEY` (and set `LLM_API_KEY` when using a hosted model provider), then:

```bash
docker compose up --build
```

Compose starts PostgreSQL with pgvector, Redis, a one-off migration service,
the API on port 8000, and the Celery analysis worker. Production containers run
as a non-root user, use JSON logging, and do not run migrations in the API
process.

## Tests and quality checks

```bash
uv run pytest tests/unit tests/integration -v
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
uv run ruff check app tests
uv run mypy app
```

The PostgreSQL integration suite requires `TEST_DATABASE_URL`; it creates and
drops a fresh schema and needs pgvector enabled. The E2E smoke test is skipped
unless `E2E=true` and requires a running Compose stack with real provider
credentials.

`make dev`, `make migrate`, `make test`, `make lint`, and `make worker` provide
the same common commands.
