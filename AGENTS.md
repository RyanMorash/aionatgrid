# Repository Guidelines

## Project Structure & Module Organization
- `src/aionatgrid/` contains the client library, config models, and GraphQL/REST helpers.
- `tests/` holds the pytest suite for async client behavior and request helpers.
- `examples/` provides runnable scripts (e.g., `examples/basic_usage.py`) for smoke testing.
- `Makefile` and `pyproject.toml` define developer commands and tool configuration.

## Build, Test, and Development Commands
- `uv sync`: create the `.venv` and install runtime + dev dependencies.
- `uv run pytest`: run the full test suite.
- `uv run ruff check .`: lint for style and import issues.
- `uv run ruff format .`: apply formatting.
- `uv run mypy src`: run strict type checks.
- `make test|lint|format|type|example`: convenient shortcuts for the above.

## Coding Style & Naming Conventions
- Python 3.10+ only; use type hints throughout.
- Indentation is 4 spaces; line length is 100 (ruff).
- Follow ruff import ordering; run `ruff format` before commits.
- Prefer descriptive, domain-focused names (e.g., `NationalGridClient`, `GraphQLRequest`).

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` for async tests.
- Keep tests in `tests/` and name files `test_*.py`.
- Aim to cover new public behaviors and error handling paths; include async context manager use.

## Commit & Pull Request Guidelines
- Commits follow short, sentence-case summaries (imperative, no prefixes), e.g.,
  "Add retry handling for auth refresh".
- PRs should include a clear description, linked issues (if any), and test evidence.
- If behavior or examples change, update `README.md` or add an `examples/` script.

## Security & Configuration Tips
- Required env vars include `NATIONALGRID_GRAPHQL_ENDPOINT`,
  `NATIONALGRID_USERNAME`, and `NATIONALGRID_PASSWORD`.
- Never commit real credentials; use local env files or CI secrets.
- For additional contributor notes, see `CLAUDE.md`.
