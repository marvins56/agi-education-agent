.PHONY: install dev test lint migrate docker-up docker-down format

install:
	pip install -e ".[dev]"

dev:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --tb=short

test-cov:
	pytest -v --cov=src --cov-report=html

lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-reset:
	docker compose down -v
	docker compose up -d
