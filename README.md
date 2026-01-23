# aionatgrid

Asynchronous Python client for communicating with National Grid's GraphQL API using `aiohttp`. The package focuses on pragmatic defaults, simple configuration, and predictable responses when orchestrating data collection jobs.

## Features
- Async `NationalGridClient` with context-manager support and connection reuse
- Configurable endpoint, API key, and request headers via `NationalGridConfig`
- Typed `GraphQLRequest` / `GraphQLResponse` helpers for reuse across queries
- Minimal dependency set (only `aiohttp`) with optional tooling for linting and typing
- Example script plus pytest suite for smoke testing your integration

## Requirements
- Python 3.10+
- `uv` for dependency management (install from Astral before continuing)

## Installation
```bash
uv sync
```
The command creates a `.venv` managed by `uv` and installs runtime plus development dependencies declared in `pyproject.toml`.

## Usage
1. Export the endpoint and API key (optional) used by National Grid's GraphQL service:
   ```bash
   export NATIONALGRID_GRAPHQL_ENDPOINT="https://api.nationalgrid.example/graphql"
   export NATIONALGRID_API_KEY="replace-with-real-key"
   ```
2. Run the example script, which issues a sample query:
   ```bash
   uv run python examples/basic_usage.py
   ```

The client can also be imported into any application:
```python
import asyncio
from aionatgrid import GraphQLRequest, NationalGridClient, NationalGridConfig

async def main() -> None:
    request = GraphQLRequest(query="""
        query CurrentFrequency {
            currentFrequency {
                timestamp
                value
            }
        }
    """)

    config = NationalGridConfig.from_env()

    async with NationalGridClient(config=config) as client:
        response = await client.execute(request)
        print(response.data)

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing and linting
```bash
uv run pytest          # run unit tests
uv run ruff check .    # lint
uv run ruff format .   # format
uv run mypy src        # type-check
```

All commands above also have Makefile shortcuts (see `Makefile`).

## Project layout
```
.
├── examples/           # runnable samples
├── src/aionatgrid/     # library source
├── tests/              # pytest suite
├── Makefile            # developer shortcuts
└── pyproject.toml      # packaging metadata
```

## Next steps
- Replace the placeholder endpoint with your tenant-specific URL
- Extend the query helpers in `aionatgrid/graphql.py` for your data products
- Integrate the client with your ETL or dashboarding stack
