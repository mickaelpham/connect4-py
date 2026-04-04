.PHONY: test lint format check

test:
	uv run pytest

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

check: lint
	uv run ruff format --check src tests
