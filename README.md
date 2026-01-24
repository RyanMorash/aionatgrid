# aionatgrid

Asynchronous Python client for communicating with National Grid's GraphQL and REST APIs using `aiohttp`. The package provides pre-built query helpers for common operations, automatic OIDC authentication, and multi-endpoint routing.

## Features
- Async `NationalGridClient` with context-manager support and connection reuse
- Pre-built query helpers for linked accounts, billing info, and energy usage data
- Automatic OIDC authentication via Azure AD B2C with token caching and refresh
- Multi-endpoint GraphQL routing (user, billing account, energy usage endpoints)
- REST API support with shared authentication
- Configurable via `NationalGridConfig` with environment variable loading
- JWT token verification and automatic expiration handling

## Requirements
- Python 3.10+
- `uv` for dependency management (install from [Astral](https://docs.astral.sh/uv/))

## Installation
```bash
uv sync
```
The command creates a `.venv` managed by `uv` and installs runtime plus development dependencies declared in `pyproject.toml`.

## Usage

### Configuration
Export your National Grid credentials:
```bash
export NATIONALGRID_GRAPHQL_ENDPOINT="https://myaccount.nationalgrid.com/api/user-cu-uwp-gql"
export NATIONALGRID_USERNAME="user@example.com"
export NATIONALGRID_PASSWORD="your-password"
```

### Quick Start
```python
import asyncio
from aionatgrid import NationalGridClient, NationalGridConfig

async def main() -> None:
    config = NationalGridConfig.from_env()

    async with NationalGridClient(config=config) as client:
        # Get linked billing accounts
        response = await client.linked_billing_accounts()
        print(response.data)

if __name__ == "__main__":
    asyncio.run(main())
```

### Available Query Methods

The client provides convenience methods for common National Grid API operations:

| Method | Description | Endpoint |
|--------|-------------|----------|
| `linked_billing_accounts()` | Get user's linked billing account IDs | user-cu-uwp-gql |
| `billing_account_info()` | Get account details (region, meters, address) | billingaccount-cu-uwp-gql |
| `energy_usage_costs()` | Get energy costs for a billing period | energyusage-cu-uwp-gql |
| `energy_usages()` | Get historical usage data | energyusage-cu-uwp-gql |
| `realtime_meter_info()` | Get real-time meter readings (REST) | REST endpoint |

### Example: Fetching Energy Usage Data

```python
import asyncio
from datetime import date
from aionatgrid import NationalGridClient, NationalGridConfig

async def main() -> None:
    config = NationalGridConfig.from_env()

    async with NationalGridClient(config=config) as client:
        # Step 1: Get linked accounts
        accounts = await client.linked_billing_accounts()
        account_id = accounts.data["user"]["accountLinks"]["nodes"][0]["billingAccountId"]

        # Step 2: Get account info (for region/companyCode)
        info = await client.billing_account_info(
            variables={"accountNumber": account_id}
        )
        region = info.data["billingAccount"]["region"]

        # Step 3: Fetch energy usage costs
        costs = await client.energy_usage_costs(
            variables={
                "accountNumber": account_id,
                "date": date.today().isoformat(),
                "companyCode": region,
            }
        )
        print(costs.data)

        # Step 4: Fetch historical usage (last 12 months)
        from_month = (date.today().year - 1) * 100 + date.today().month
        usages = await client.energy_usages(
            variables={
                "accountNumber": account_id,
                "from": from_month,
                "first": 12,
            }
        )
        print(usages.data)

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom GraphQL Queries

For custom queries, use the `execute()` method directly:
```python
from aionatgrid import GraphQLRequest

request = GraphQLRequest(
    query="query MyQuery { ... }",
    variables={"key": "value"},
    endpoint="https://myaccount.nationalgrid.com/api/custom-endpoint"
)
response = await client.execute(request)
```

### REST API Access

```python
response = await client.request_rest("GET", "/api/endpoint")
print(response.status, response.data)
```

## Examples

Run the included example scripts:
```bash
uv run python examples/list-accounts.py    # List linked billing accounts
uv run python examples/account-info.py     # Fetch billing account details
uv run python examples/energy-usage.py     # Fetch energy costs and usage history
uv run python examples/interval-reads.py   # Fetch interval meter readings
```

## Testing and Linting
```bash
uv run pytest          # run unit tests
uv run ruff check .    # lint
uv run ruff format .   # format
uv run mypy src        # type-check
```

All commands above also have Makefile shortcuts (see `Makefile`).

## Project Layout
```
.
├── examples/
│   ├── account-info.py      # Billing account details example
│   ├── energy-usage.py      # Energy costs and usage example
│   ├── interval-reads.py    # Interval meter readings example
│   └── list-accounts.py     # Account listing example
├── src/aionatgrid/
│   ├── __init__.py          # Public exports
│   ├── auth.py              # Authentication helpers
│   ├── client.py            # NationalGridClient implementation
│   ├── config.py            # NationalGridConfig and RetryConfig
│   ├── exceptions.py        # Custom exception classes
│   ├── graphql.py           # GraphQL request/response types
│   ├── helpers.py           # Utility functions
│   ├── oidchelper.py        # OIDC authentication flow
│   ├── queries.py           # GraphQL query builders
│   ├── rest.py              # REST request/response types
│   └── rest_queries.py      # REST query builders
├── tests/
│   ├── test_client.py       # Client unit tests
│   ├── test_config.py       # Configuration tests
│   └── test_retry.py        # Retry logic tests
├── Makefile                 # Developer shortcuts
└── pyproject.toml           # Packaging metadata
```

## Architecture

### Multi-Endpoint Routing
National Grid uses separate GraphQL endpoints for different data domains. The query helpers automatically route requests to the correct endpoint:
- **user-cu-uwp-gql**: User account links
- **billingaccount-cu-uwp-gql**: Billing account metadata
- **energyusage-cu-uwp-gql**: Energy usage and cost data

### Authentication
The client handles OIDC authentication automatically:
1. First API call triggers authentication
2. Tokens are cached with thread-safe locking
3. Expired tokens are refreshed automatically (5-minute buffer)
4. JWT signatures are verified cryptographically
