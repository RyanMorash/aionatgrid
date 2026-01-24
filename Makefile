PYTHON ?= uv run python

.PHONY: install test lint format type example clean

install:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy src

example:
	uv run python examples/list-accounts.py

clean:
	rm -rf .mypy_cache .pytest_cache ruff_cache
