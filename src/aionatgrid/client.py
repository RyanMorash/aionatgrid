"""Async GraphQL client for National Grid."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import aiohttp

from .config import NationalGridConfig
from .graphql import GraphQLRequest, GraphQLResponse

logger = logging.getLogger(__name__)


class NationalGridClient:
    """High-level GraphQL client that reuses an aiohttp session."""

    def __init__(
        self,
        config: NationalGridConfig | None = None,
        *,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._config = config or NationalGridConfig()
        self._session = session
        self._owns_session = session is None

    @property
    def config(self) -> NationalGridConfig:
        return self._config

    async def __aenter__(self) -> "NationalGridClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.close()

    async def close(self) -> None:
        if self._session and not self._session.closed and self._owns_session:
            await self._session.close()
            self._session = None

    async def execute(
        self,
        request: GraphQLRequest,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> GraphQLResponse:
        session = await self._ensure_session()
        payload = request.to_payload()
        merged_headers = self._config.build_headers(headers)
        effective_timeout = aiohttp.ClientTimeout(total=timeout or self._config.timeout)

        logger.debug("POST %s", self._config.endpoint)
        async with session.post(
            self._config.endpoint,
            json=payload,
            headers=merged_headers,
            timeout=effective_timeout,
            ssl=self._config.verify_ssl,
        ) as response:
            response.raise_for_status()
            body = await response.json(content_type=None)

        graphql_response = GraphQLResponse.from_payload(body)
        if graphql_response.errors:
            logger.warning("GraphQL errors returned: %s", graphql_response.errors)
        return graphql_response

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        timeout = aiohttp.ClientTimeout(total=self._config.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def ping(self) -> bool:
        """Simple health-check that issues an empty request body."""

        dummy_request = GraphQLRequest(query="query Ping { __typename }")
        response = await self.execute(dummy_request)
        return response.data is not None
