.PHONY: dev migrate test lint worker

dev:
	docker compose up --build

migrate:
	uv run alembic upgrade head

test:
	uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80

lint:
	uv run ruff check app tests
	uv run mypy app

worker:
	uv run celery -A app.workers.celery_app worker -Q analysis -l info
