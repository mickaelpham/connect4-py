.PHONY: test lint format check db-up db-down migrate serve fe-dev fe-build fe-test fe-lint fe-lint-fix

test:
	uv run pytest

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

check: lint
	uv run ruff format --check src tests

db-up:
	docker compose up -d

db-down:
	docker compose down

migrate:
	uv run alembic upgrade head

serve:
	uv run uvicorn connect4.api.app:app --reload --env-file .env

fe-dev:
	cd frontend && npm run dev

fe-build:
	cd frontend && npm run build

fe-test:
	cd frontend && npm test

fe-lint:
	cd frontend && npm run lint

fe-lint-fix:
	cd frontend && npm run lint:fix
