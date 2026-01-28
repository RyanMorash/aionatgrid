# aionatgrid

[![PyPI](https://img.shields.io/pypi/v/aionatgrid)](https://pypi.org/project/aionatgrid/)

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
        accounts = await client.get_linked_accounts()
        for account in accounts:
            print(account["billingAccountId"])

if __name__ == "__main__":
    asyncio.run(main())
```

## API Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_linked_accounts()` | `list[AccountLink]` | Get linked billing account IDs |
| `get_billing_account()` | `BillingAccount` | Get account details (region, meters, address) |
| `get_energy_usage_costs()` | `list[EnergyUsageCost]` | Get energy costs for a billing period |
| `get_energy_usages()` | `list[EnergyUsage]` | Get historical usage data |
| `get_ami_energy_usages()` | `list[AmiEnergyUsage]` | Get AMI hourly energy usage |
| `get_interval_reads()` | `list[IntervalRead]` | Get real-time meter interval reads |

All methods return typed results using TypedDict models.

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
