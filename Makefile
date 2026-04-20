.PHONY: up down build logs test lint migrate seed ingest

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f backend

db-shell:
	docker compose exec db psql -U jobhunter -d jobhunter

# Run inside the backend container
migrate:
	docker compose exec backend alembic upgrade head

migrate-new:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

test:
	docker compose exec backend python -m pytest -v

lint:
	docker compose exec backend python -m ruff check app/ tests/

ingest:
	docker compose exec backend python -m app.workers.run_ingestion

seed:
	docker compose exec backend python /app/scripts/seed_sources.py
