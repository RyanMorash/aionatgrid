"""Tests for retry logic and error handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import aiohttp
import pytest

from aionatgrid import (
    GraphQLError,
    NationalGridClient,
    NationalGridConfig,
    RestAPIError,
    RetryConfig,
    RetryExhaustedError,
)
from aionatgrid.graphql import GraphQLRequest


class _MockResponse:
    """Mock aiohttp response."""

    def __init__(self, payload: dict, status: int = 200, raise_on_status: bool = False):
        self._payload = payload
        self.status = status
        self._raise_on_status = raise_on_status
        self.headers = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self, content_type=None):
        return self._payload

    async def text(self):
        return str(self._payload)

    def raise_for_status(self):
        if self._raise_on_status:
            raise aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=self.status,
                message=f"HTTP {self.status}",
            )


@pytest.mark.asyncio
async def test_retry_on_500_error(monkeypatch: pytest.MonkeyPatch):
    """Test that 500 errors trigger retry."""
    config = NationalGridConfig(retry_config=RetryConfig(max_attempts=3, initial_delay=0.01))
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False

    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            # First two calls fail with 500
            return _MockResponse({}, status=500, raise_on_status=True)
        # Third call succeeds
        return _MockResponse({"data": {"value": 42}})

    session.post = mock_post

    async def _fake_login(self, session, username, password, login_data):
        return "token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)
    request = GraphQLRequest(query="query Test { value }")

    response = await client.execute(request)

    assert response.data == {"value": 42}
    assert call_count == 3  # Should have retried twice


@pytest.mark.asyncio
async def test_retry_exhausted_raises_error(monkeypatch: pytest.MonkeyPatch):
    """Test that exhausted retries raise RetryExhaustedError."""
    config = NationalGridConfig(retry_config=RetryConfig(max_attempts=2, initial_delay=0.01))
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False

    # Always fail with 500
    session.post.return_value = _MockResponse({}, status=500, raise_on_status=True)

    async def _fake_login(self, session, username, password, login_data):
        return "token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)
    request = GraphQLRequest(query="query Test { value }")

    with pytest.raises(RetryExhaustedError) as exc_info:
        await client.execute(request)

    assert exc_info.value.attempts == 2
    assert isinstance(exc_info.value.last_error, GraphQLError)


@pytest.mark.asyncio
async def test_401_clears_token_and_retries(monkeypatch: pytest.MonkeyPatch):
    """Test that 401 errors clear cached token and retry once."""
    config = NationalGridConfig(
        username="test@example.com",
        password="test-password",
        retry_config=RetryConfig(max_attempts=3, initial_delay=0.01),
    )
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False

    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call fails with 401
            return _MockResponse({}, status=401, raise_on_status=True)
        # Second call succeeds (after re-auth)
        return _MockResponse({"data": {"value": 42}})

    session.post = mock_post

    login_count = 0

    async def _fake_login(self, session, username, password, login_data):
        nonlocal login_count
        login_count += 1
        return f"token_{login_count}", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)
    request = GraphQLRequest(query="query Test { value }")

    response = await client.execute(request)

    assert response.data == {"value": 42}
    assert call_count == 2  # Should have retried once
    assert login_count == 2  # Should have authenticated twice


@pytest.mark.asyncio
async def test_graphql_error_includes_context(monkeypatch: pytest.MonkeyPatch):
    """Test that GraphQL errors include helpful context."""
    config = NationalGridConfig(retry_config=RetryConfig(max_attempts=1, initial_delay=0.01))
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False

    def mock_post(*args, **kwargs):
        return _MockResponse({}, status=404, raise_on_status=True)

    session.post = mock_post

    async def _fake_login(self, session, username, password, login_data):
        return "token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)
    request = GraphQLRequest(
        query="query Test($id: ID!) { user(id: $id) { name } }",
        variables={"id": "123"},
    )

    with pytest.raises((GraphQLError, RetryExhaustedError)) as exc_info:
        await client.execute(request)

    # Get the actual error (might be wrapped in RetryExhaustedError)
    error = exc_info.value
    if isinstance(error, RetryExhaustedError):
        error = error.last_error

    assert isinstance(error, GraphQLError)
    assert error.endpoint is not None
    assert error.query is not None
    assert error.variables == {"id": "123"}
    assert error.status == 404
    assert "404" in str(error)


@pytest.mark.asyncio
async def test_rest_api_error_includes_context(monkeypatch: pytest.MonkeyPatch):
    """Test that REST API errors include helpful context."""
    config = NationalGridConfig(retry_config=RetryConfig(max_attempts=1, initial_delay=0.01))
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False

    def mock_request(*args, **kwargs):
        return _MockResponse({}, status=503, raise_on_status=True)

    session.request = mock_request

    async def _fake_login(self, session, username, password, login_data):
        return "token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)

    with pytest.raises((RestAPIError, RetryExhaustedError)) as exc_info:
        await client.request_rest("GET", "/api/test")

    # Get the actual error (might be wrapped in RetryExhaustedError)
    error = exc_info.value
    if isinstance(error, RetryExhaustedError):
        error = error.last_error

    assert isinstance(error, RestAPIError)
    assert error.url is not None
    assert error.method == "GET"
    assert error.status == 503
    assert "503" in str(error)


@pytest.mark.asyncio
async def test_no_retry_on_400_error(monkeypatch: pytest.MonkeyPatch):
    """Test that 400 errors don't trigger retry (client error)."""
    config = NationalGridConfig(retry_config=RetryConfig(max_attempts=3, initial_delay=0.01))
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False

    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return _MockResponse({}, status=400, raise_on_status=True)

    session.post = mock_post

    async def _fake_login(self, session, username, password, login_data):
        return "token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)
    request = GraphQLRequest(query="query Test { value }")

    with pytest.raises(GraphQLError):
        await client.execute(request)

    assert call_count == 1  # Should NOT have retried


@pytest.mark.asyncio
async def test_retry_on_timeout(monkeypatch: pytest.MonkeyPatch):
    """Test that timeout errors trigger retry."""
    config = NationalGridConfig(retry_config=RetryConfig(max_attempts=3, initial_delay=0.01))
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False

    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise aiohttp.ServerTimeoutError()
        # Third call succeeds
        return _MockResponse({"data": {"value": 42}})

    session.post = mock_post

    async def _fake_login(self, session, username, password, login_data):
        return "token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)
    request = GraphQLRequest(query="query Test { value }")

    response = await client.execute(request)

    assert response.data == {"value": 42}
    assert call_count == 3


@pytest.mark.asyncio
async def test_custom_retry_config():
    """Test that custom retry configuration is respected."""
    custom_retry = RetryConfig(
        max_attempts=5,
        initial_delay=0.5,
        max_delay=20.0,
        exponential_base=3.0,
    )
    config = NationalGridConfig(retry_config=custom_retry)

    assert config.retry_config.max_attempts == 5
    assert config.retry_config.initial_delay == 0.5
    assert config.retry_config.max_delay == 20.0
    assert config.retry_config.exponential_base == 3.0


def test_retry_delay_calculation():
    """Test retry delay calculation with exponential backoff."""
    config = NationalGridConfig(
        retry_config=RetryConfig(initial_delay=1.0, max_delay=10.0, exponential_base=2.0)
    )
    client = NationalGridClient(config=config)

    # First retry (attempt 0)
    delay_0 = client._calculate_retry_delay(0, config.retry_config)
    assert 0.75 <= delay_0 <= 1.25  # 1.0 ± 25% jitter

    # Second retry (attempt 1)
    delay_1 = client._calculate_retry_delay(1, config.retry_config)
    assert 1.5 <= delay_1 <= 2.5  # 2.0 ± 25% jitter

    # Third retry (attempt 2)
    delay_2 = client._calculate_retry_delay(2, config.retry_config)
    assert 3.0 <= delay_2 <= 5.0  # 4.0 ± 25% jitter

    # Large attempt should cap at max_delay
    delay_large = client._calculate_retry_delay(10, config.retry_config)
    assert delay_large <= 12.5  # max_delay + 25% jitter
