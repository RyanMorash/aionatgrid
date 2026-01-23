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

    async def __aenter__(self) -> "_DummyResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:  # type: ignore[override]
        return False

    async def json(self, content_type: str | None = None) -> dict[str, object]:
        return self._payload

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
async def test_execute_merges_headers() -> None:
    config = NationalGridConfig(endpoint="https://example.test/graphql", api_key="token")
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False
    session.post.return_value = _DummyResponse({"data": {}})

    client = NationalGridClient(config=config, session=session)

    await client.execute(
        GraphQLRequest(query="query Test { value }"),
        headers={"X-Test": "1"},
    )

    _, kwargs = session.post.call_args
    headers = kwargs["headers"]
    assert headers["Authorization"] == "Bearer token"
    assert headers["X-Test"] == "1"
    assert headers["Content-Type"] == "application/json"
