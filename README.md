# aionatgrid

Async Python client for National Grid's GraphQL and REST APIs.

## Installation
```bash
pip install aionatgrid
```

## Quick Start
```python
import asyncio
from aionatgrid import NationalGridClient, NationalGridConfig

async def main() -> None:
    config = NationalGridConfig(
        username="user@example.com",
        password="your-password",
    )

    async with NationalGridClient(config=config) as client:
        response = await client.linked_billing_accounts()
        print(response.data)

if __name__ == "__main__":
    asyncio.run(main())
```

## Query Methods

| Method | Description |
|--------|-------------|
| `linked_billing_accounts()` | Get linked billing account IDs |
| `billing_account_info()` | Get account details (region, meters, address) |
| `energy_usage_costs()` | Get energy costs for a billing period |
| `energy_usages()` | Get historical usage data |
| `ami_energy_usages()` | Get AMI hourly energy usage |
| `realtime_meter_info()` | Get real-time meter readings (REST) |

For custom queries, use `execute()` with a `GraphQLRequest` directly.

## Examples

```bash
uv run python examples/list-accounts.py --username user@example.com --password secret
uv run python examples/account-info.py --username user@example.com --password secret
uv run python examples/energy-usage.py --username user@example.com --password secret
uv run python examples/interval-reads.py --username user@example.com --password secret
uv run python examples/ami-usage.py --username user@example.com --password secret
```

## Development

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                # install dependencies
uv run pytest          # run tests
uv run ruff check .    # lint
uv run ruff format .   # format
uv run mypy src        # type-check
```
