from __future__ import annotations

from unittest.mock import MagicMock

import aiohttp
import pytest

from aionatgrid.client import NationalGridClient
from aionatgrid.config import NationalGridConfig
from aionatgrid.graphql import GraphQLRequest


class _DummyResponse:
    def __init__(self, payload: dict[str, object]):
        self._payload = payload

    async def __aenter__(self) -> _DummyResponse:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:  # type: ignore[override]
        return False

    async def json(self, content_type: str | None = None) -> dict[str, object]:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class _DummyRestResponse:
    def __init__(self, payload: object, *, content_type: str = "application/json"):
        self._payload = payload
        self.headers = {"Content-Type": content_type}
        self.status = 200

    async def __aenter__(self) -> _DummyRestResponse:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:  # type: ignore[override]
        return False

    async def json(self, content_type: str | None = None) -> object:
        return self._payload

    async def text(self) -> str:
        return "ok"

    def raise_for_status(self) -> None:
        return None


@pytest.mark.asyncio
async def test_execute_returns_response_payload() -> None:
    config = NationalGridConfig(endpoint="https://example.test/graphql")
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False
    payload = {"data": {"value": 42}}
    session.post.return_value = _DummyResponse(payload)

    client = NationalGridClient(config=config, session=session)
    request = GraphQLRequest(query="query Test { value }")

    response = await client.execute(request)

    assert response.data == {"value": 42}
    session.post.assert_called_once()


@pytest.mark.asyncio
async def test_execute_uses_request_endpoint() -> None:
    config = NationalGridConfig(endpoint="https://example.test/graphql")
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False
    session.post.return_value = _DummyResponse({"data": {}})

    client = NationalGridClient(config=config, session=session)
    request = GraphQLRequest(
        query="query Test { value }",
        endpoint="https://example.test/override",
    )

    await client.execute(request)

    args, kwargs = session.post.call_args
    assert args[0] == "https://example.test/override"
    assert kwargs["json"]["query"] == "query Test { value }"


@pytest.mark.asyncio
async def test_execute_merges_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    config = NationalGridConfig(
        endpoint="https://example.test/graphql",
        username="user@example.com",
        password="super-secret",
        subscription_key="sub-key",
    )
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False
    session.post.return_value = _DummyResponse({"data": {}})

    async def _fake_login(
        self, session: aiohttp.ClientSession, username: str, password: str, login_data: dict
    ) -> tuple[str, int]:
        assert username == "user@example.com"
        assert password == "super-secret"
        return "token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)

    await client.execute(
        GraphQLRequest(query="query Test { value }"),
        headers={"X-Test": "1"},
    )

    _, kwargs = session.post.call_args
    headers = kwargs["headers"]
    assert headers["Authorization"] == "Bearer token"
    assert headers["ocp-apim-subscription-key"] == "sub-key"
    assert headers["X-Test"] == "1"
    assert headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_request_rest_uses_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    config = NationalGridConfig(
        endpoint="https://example.test/graphql",
        rest_base_url="https://example.test/api/",
        username="user@example.com",
        password="super-secret",
        subscription_key="sub-key",
    )
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False
    session.request.return_value = _DummyRestResponse({"value": 42})

    async def _fake_login(
        self, session: aiohttp.ClientSession, username: str, password: str, login_data: dict
    ) -> tuple[str, int]:
        return "rest-token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)

    response = await client.request_rest("GET", "v1/usage", params={"a": "b"})

    assert response.data == {"value": 42}
    session.request.assert_called_once()
    _, kwargs = session.request.call_args
    assert kwargs["url"] == "https://example.test/api/v1/usage"
    headers = kwargs["headers"]
    assert headers["Authorization"] == "Bearer rest-token"
    assert headers["ocp-apim-subscription-key"] == "sub-key"


@pytest.mark.asyncio
async def test_execute_uses_oidc_token(monkeypatch: pytest.MonkeyPatch) -> None:
    config = NationalGridConfig(
        endpoint="https://example.test/graphql",
        username="user@example.com",
        password="super-secret",
    )
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False
    session.post.return_value = _DummyResponse({"data": {}})

    async def _fake_login(
        self, session: aiohttp.ClientSession, username: str, password: str, login_data: dict
    ) -> tuple[str, int]:
        assert username == "user@example.com"
        assert password == "super-secret"
        return "oidc-token", 3600

    monkeypatch.setattr("aionatgrid.client.NationalGridAuth.async_login", _fake_login)

    client = NationalGridClient(config=config, session=session)

    await client.execute(GraphQLRequest(query="query Test { value }"))

    _, kwargs = session.post.call_args
    headers = kwargs["headers"]
    assert headers["Authorization"] == "Bearer oidc-token"
