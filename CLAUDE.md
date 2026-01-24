# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
uv sync                    # Install dependencies (creates .venv)
```

### Testing and Quality
```bash
uv run pytest              # Run all tests
uv run pytest tests/test_client.py::test_execute_returns_response_payload  # Run single test
uv run ruff check .        # Lint code
uv run ruff format .       # Format code
uv run mypy src            # Type-check source code
```

### Running Examples
```bash
# Set required environment variables first
export NATIONALGRID_GRAPHQL_ENDPOINT="https://myaccount.nationalgrid.com/api/user-cu-uwp-gql"
export NATIONALGRID_USERNAME="user@example.com"
export NATIONALGRID_PASSWORD="your-password"

uv run python examples/basic_usage.py       # Run basic example
uv run python examples/interval-reads.py    # Run interval reads example
uv run python examples/list-accounts.py     # Run account listing example
```

### Makefile Shortcuts
```bash
make install    # Same as uv sync
make test       # Same as uv run pytest
make lint       # Same as uv run ruff check .
make format     # Same as uv run ruff format .
make type       # Same as uv run mypy src
make example    # Same as uv run python examples/basic_usage.py
make clean      # Remove cache directories
```

## Architecture Overview

### Core Client Design
The package is built around `NationalGridClient` (src/aionatgrid/client.py), an async context manager that:
- Manages a single reusable `aiohttp.ClientSession` with configurable timeouts
- Handles OIDC authentication via Azure AD B2C (configured in auth.py with tenant/policy constants)
- Caches access tokens with thread-safe locking (`_auth_lock`) to prevent duplicate login requests
- Supports both GraphQL and REST endpoints with shared authentication headers

### Multi-Endpoint GraphQL Architecture
National Grid uses **separate GraphQL endpoints** for different data domains:
- `user-cu-uwp-gql`: User account links (queries.py:LINKED_BILLING_ENDPOINT)
- `billingaccount-cu-uwp-gql`: Account metadata (queries.py:BILLING_ACCOUNT_INFO_ENDPOINT)
- `energyusage-cu-uwp-gql`: Usage data (queries.py:ENERGY_USAGE_ENDPOINT)

Each query helper method (e.g., `linked_billing_accounts()`, `billing_account_info()`) automatically routes to the correct endpoint via the `endpoint` field in `GraphQLRequest`.

### Query Builder Pattern
The `StandardQuery` dataclass (queries.py) provides a scaffolding system for GraphQL operations:
- Composes selection sets with proper indentation
- Handles variable definitions (single string or sequence)
- Supports field arguments for parameterized queries
- Automatically generates properly formatted GraphQL query strings via `compose_query()`

Helper functions like `linked_billing_accounts_request()` provide pre-configured query templates with sensible defaults for selection sets and variable definitions.

### Authentication Flow
1. First API call triggers `_get_access_token()` with double-checked locking
2. Before using cached token, checks if it's expired (with 5-minute buffer for safety)
3. `NationalGridAuth.async_login()` delegates to `oidchelper.async_auth_oidc()`
4. OIDC helper performs Azure AD B2C flow using the client's existing session (no duplicate sessions created)
5. Returns tuple of `(access_token, expires_in_seconds)` instead of just the token
6. Token and expiry timestamp cached in `_access_token` and `_token_expires_at`
7. Automatic token refresh before expiration prevents 401 errors
8. `login_data` dict accumulates session info (e.g., `sub` claim for userId extracted from verified JWT)

### Configuration Management
`NationalGridConfig` (config.py) is a frozen dataclass with:
- `from_env()` class method for environment variable loading
- `build_headers()` method that merges authentication, subscription keys, and custom headers
- `with_overrides()` for creating modified config instances
- Hard-coded subscription key (`e674f89d7ed9417194de894b701333dd`) required for API access

### Request/Response Abstractions
- `GraphQLRequest`/`GraphQLResponse` (graphql.py): Thin wrappers around GraphQL payloads
- `RestRequest`/`RestResponse` (rest.py, rest_queries.py): Parallel abstractions for REST endpoints
- Both support endpoint overrides at the request level

## Testing Patterns

Tests use mocked `aiohttp.ClientSession` objects with custom response classes (`_DummyResponse`, `_DummyRestResponse`). Key patterns:
- Monkeypatch `NationalGridAuth.async_login` to avoid real OIDC calls
- Verify header merging (auth token, subscription key, custom headers)
- Test endpoint routing for multi-endpoint queries
- Use `pytest-asyncio` for async test support (all tests marked with `@pytest.mark.asyncio`)

## Key Constraints

- Python 3.10+ required (uses `slots=True`, match statements, and modern type hints)
- `uv` is the required dependency manager (not pip or poetry)
- All GraphQL requests require `ocp-apim-subscription-key` header (configured in config.py)
- OIDC authentication is mandatory for production usage (username/password required)
- Session management follows context manager pattern (prefer `async with` over manual `close()`)
- Access tokens expire after ~1 hour and are automatically refreshed 5 minutes before expiration
- JWT signature verification requires network access to fetch signing keys from JWKS endpoint

## Recent Security Improvements

- **JWT Verification**: ID tokens are now cryptographically verified using PyJWT with RS256 signature validation
- **Token Expiration**: Access tokens are tracked and automatically refreshed before expiration
- **Session Reuse**: Authentication reuses the client's session instead of creating duplicate connections
- **Robust Parsing**: Settings extraction uses dual-strategy parsing (string slicing + regex fallback)
