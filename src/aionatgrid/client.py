"""Async client for National Grid GraphQL and REST endpoints."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any
from urllib.parse import urljoin

import aiohttp

from .auth import NationalGridAuth
from .config import NationalGridConfig
from .graphql import GraphQLRequest, GraphQLResponse
from .rest import RestResponse

logger = logging.getLogger(__name__)


class NationalGridClient:
    """High-level client that reuses an aiohttp session."""

    def __init__(
        self,
        config: NationalGridConfig | None = None,
        *,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._config = config or NationalGridConfig()
        self._session = session
        self._owns_session = session is None
        self._access_token: str | None = None
        self._auth_lock = asyncio.Lock()

    @property
    def config(self) -> NationalGridConfig:
        return self._config

    async def __aenter__(self) -> "NationalGridClient":
        await self._ensure_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any | None,
    ) -> None:
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
        access_token = await self._get_access_token(session)
        payload = request.to_payload()
        merged_headers = self._config.build_headers(headers, access_token=access_token)
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

    async def request_rest(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> RestResponse:
        """Issue a REST request against the configured base URL."""

        session = await self._ensure_session()
        access_token = await self._get_access_token(session)
        url = self._resolve_rest_url(path_or_url)
        content_type = "application/json" if json is not None else None
        merged_headers = self._config.build_headers(
            headers,
            access_token=access_token,
            content_type=content_type,
        )
        effective_timeout = aiohttp.ClientTimeout(total=timeout or self._config.timeout)

        logger.debug("%s %s", method.upper(), url)
        async with session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            headers=merged_headers,
            timeout=effective_timeout,
            ssl=self._config.verify_ssl,
        ) as response:
            response.raise_for_status()
            payload = await self._read_rest_payload(response)
            return RestResponse(
                status=response.status,
                headers=dict(response.headers),
                data=payload,
            )

    async def _get_access_token(self, session: aiohttp.ClientSession) -> str | None:
        if self._access_token:
            return self._access_token
        if not (self._config.username and self._config.password):
            return None
        async with self._auth_lock:
            if self._access_token:
                return self._access_token
            auth_client = NationalGridAuth()
            self._access_token = await auth_client.async_login(
                session,
                self._config.username,
                self._config.password,
                {},
            )
        return self._access_token

    def _resolve_rest_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        if not self._config.rest_base_url:
            raise ValueError("rest_base_url is required for relative REST paths.")
        return urljoin(self._config.rest_base_url.rstrip("/") + "/", path_or_url.lstrip("/"))

    async def _read_rest_payload(self, response: aiohttp.ClientResponse) -> Any:
        try:
            return await response.json(content_type=None)
        except aiohttp.ContentTypeError:
            return await response.text()

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
