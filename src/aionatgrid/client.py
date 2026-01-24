"""Async client for National Grid GraphQL and REST endpoints."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urljoin

import aiohttp

from .auth import NationalGridAuth
from .config import NationalGridConfig, RetryConfig
from .exceptions import GraphQLError, RestAPIError, RetryExhaustedError
from .graphql import GraphQLRequest, GraphQLResponse
from .queries import (
    BILLING_ACCOUNT_INFO_SELECTION_SET,
    DEFAULT_SELECTION_SET,
    LINKED_BILLING_SELECTION_SET,
    billing_account_info_request,
    energy_usage_request,
    linked_billing_accounts_request,
)
from .rest import RestResponse
from .rest_queries import realtime_meter_info_request

logger = logging.getLogger(__name__)

# Buffer time before actual expiration to refresh token (5 minutes)
TOKEN_EXPIRY_BUFFER_SECONDS = 300


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
        self._token_expires_at: float | None = None
        self._auth_lock = asyncio.Lock()
        self._session_lock = asyncio.Lock()
        self._login_data: dict[str, Any] = {}

    @property
    def config(self) -> NationalGridConfig:
        return self._config

    async def __aenter__(self) -> NationalGridClient:
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

    def _calculate_retry_delay(self, attempt: int, retry_config: RetryConfig) -> float:
        """Calculate retry delay with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (0-indexed)
            retry_config: Retry configuration

        Returns:
            Delay in seconds before next retry
        """
        # Exponential backoff: initial_delay * (base ^ attempt)
        delay = retry_config.initial_delay * (retry_config.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, retry_config.max_delay)

        # Add jitter (±25% random variation) to prevent thundering herd
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay_with_jitter = delay + jitter

        return max(0, delay_with_jitter)

    def _should_retry(self, error: Exception, attempt: int, retry_config: RetryConfig) -> bool:
        """Determine if request should be retried based on error and config.

        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-indexed)
            retry_config: Retry configuration

        Returns:
            True if request should be retried, False otherwise
        """
        # Check if we've exhausted attempts
        if attempt >= retry_config.max_attempts - 1:
            return False

        # Extract original error from wrapped exceptions
        check_error = error
        if isinstance(error, (GraphQLError, RestAPIError)):
            if error.original_error:
                check_error = error.original_error

        # Retry on connection errors
        if retry_config.retry_on_connection_errors and isinstance(
            check_error, (aiohttp.ClientConnectionError, aiohttp.ServerDisconnectedError)
        ):
            return True

        # Retry on timeout errors
        if retry_config.retry_on_timeout and isinstance(
            check_error, (aiohttp.ServerTimeoutError, asyncio.TimeoutError)
        ):
            return True

        # Retry on specific HTTP status codes
        if isinstance(check_error, aiohttp.ClientResponseError):
            if check_error.status in retry_config.retry_on_status:
                return True
            # Also retry on 401 to trigger re-auth (but only once)
            if check_error.status == 401 and attempt == 0:
                return True

        # Also check status directly on our custom errors
        if isinstance(error, (GraphQLError, RestAPIError)):
            if error.status and error.status in retry_config.retry_on_status:
                return True
            if error.status == 401 and attempt == 0:
                return True

        return False

    async def execute(
        self,
        request: GraphQLRequest,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> GraphQLResponse:
        """Execute a GraphQL request with retry logic.

        Args:
            request: GraphQL request to execute
            headers: Additional headers to include
            timeout: Request timeout in seconds

        Returns:
            GraphQL response

        Raises:
            GraphQLError: When the request fails after all retries
            RetryExhaustedError: When all retry attempts are exhausted
        """
        retry_config = self._config.retry_config
        last_error: Exception | None = None

        for attempt in range(retry_config.max_attempts):
            try:
                session = await self._ensure_session()
                access_token = await self._get_access_token(session)
                payload = request.to_payload()
                merged_headers = self._config.build_headers(headers, access_token=access_token)
                effective_timeout = aiohttp.ClientTimeout(total=timeout or self._config.timeout)
                endpoint = request.endpoint or self._config.endpoint

                if attempt > 0:
                    logger.info(
                        "Retrying GraphQL request to %s (attempt %d/%d)",
                        endpoint,
                        attempt + 1,
                        retry_config.max_attempts,
                    )
                else:
                    logger.debug("POST %s", endpoint)

                async with session.post(
                    endpoint,
                    json=payload,
                    headers=merged_headers,
                    timeout=effective_timeout,
                    ssl=self._config.verify_ssl,
                ) as response:
                    try:
                        response.raise_for_status()
                    except aiohttp.ClientResponseError as e:
                        # Special handling for 401: clear token and retry
                        if e.status == 401:
                            logger.info("Received 401, clearing cached token")
                            self._access_token = None
                            self._token_expires_at = None

                        # Read response body for error context
                        try:
                            body = await response.json(content_type=None)
                        except Exception:
                            body = None

                        raise GraphQLError(
                            f"GraphQL request failed with status {e.status}",
                            endpoint=endpoint,
                            query=request.query,
                            variables=dict(request.variables) if request.variables else None,
                            status=e.status,
                            response_body=body,
                            original_error=e,
                        ) from e

                    body = await response.json(content_type=None)

                graphql_response = GraphQLResponse.from_payload(body)
                if graphql_response.errors:
                    logger.warning("GraphQL errors returned: %s", graphql_response.errors)
                return graphql_response

            except Exception as e:
                last_error = e

                # Check if we should retry this error
                should_retry = self._should_retry(e, attempt, retry_config)

                # Check if this is the last attempt
                is_last_attempt = attempt >= retry_config.max_attempts - 1

                # If not retryable, raise immediately (unless last attempt)
                if not should_retry and not is_last_attempt:
                    # Convert generic errors to GraphQLError with context
                    if not isinstance(e, GraphQLError):
                        raise GraphQLError(
                            f"GraphQL request failed: {e}",
                            endpoint=request.endpoint or self._config.endpoint,
                            query=request.query,
                            variables=dict(request.variables) if request.variables else None,
                            original_error=e,
                        ) from e
                    raise

                # Last attempt: fall through to RetryExhaustedError
                if is_last_attempt:
                    break

                # Calculate delay and retry
                delay = self._calculate_retry_delay(attempt, retry_config)
                logger.warning(
                    "Request failed (%s), retrying in %.2f seconds (attempt %d/%d)",
                    type(e).__name__,
                    delay,
                    attempt + 1,
                    retry_config.max_attempts,
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        raise RetryExhaustedError(
            "GraphQL request failed after all retry attempts",
            attempts=retry_config.max_attempts,
            last_error=last_error or Exception("Unknown error"),
        )

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
        """Issue a REST request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path_or_url: URL path or full URL
            params: Query parameters
            json: JSON payload
            data: Form data
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            REST response

        Raises:
            RestAPIError: When the request fails after all retries
            RetryExhaustedError: When all retry attempts are exhausted
        """
        retry_config = self._config.retry_config
        last_error: Exception | None = None

        for attempt in range(retry_config.max_attempts):
            try:
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

                if attempt > 0:
                    logger.info(
                        "Retrying REST request to %s (attempt %d/%d)",
                        url,
                        attempt + 1,
                        retry_config.max_attempts,
                    )
                else:
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
                    try:
                        response.raise_for_status()
                    except aiohttp.ClientResponseError as e:
                        # Special handling for 401: clear token and retry
                        if e.status == 401:
                            logger.info("Received 401, clearing cached token")
                            self._access_token = None
                            self._token_expires_at = None

                        # Read response body for error context
                        try:
                            response_text = await response.text()
                        except Exception:
                            response_text = None

                        raise RestAPIError(
                            f"REST request failed with status {e.status}",
                            url=url,
                            method=method,
                            status=e.status,
                            response_text=response_text,
                            original_error=e,
                        ) from e

                    payload = await self._read_rest_payload(response)
                    return RestResponse(
                        status=response.status,
                        headers=dict(response.headers),
                        data=payload,
                    )

            except Exception as e:
                last_error = e

                # Check if we should retry this error
                should_retry = self._should_retry(e, attempt, retry_config)

                # Check if this is the last attempt
                is_last_attempt = attempt >= retry_config.max_attempts - 1

                # If not retryable, raise immediately (unless last attempt)
                if not should_retry and not is_last_attempt:
                    # Convert generic errors to RestAPIError with context
                    if not isinstance(e, RestAPIError):
                        url = self._resolve_rest_url(path_or_url)
                        raise RestAPIError(
                            f"REST request failed: {e}",
                            url=url,
                            method=method,
                            original_error=e,
                        ) from e
                    raise

                # Last attempt: fall through to RetryExhaustedError
                if is_last_attempt:
                    break

                # Calculate delay and retry
                delay = self._calculate_retry_delay(attempt, retry_config)
                logger.warning(
                    "Request failed (%s), retrying in %.2f seconds (attempt %d/%d)",
                    type(e).__name__,
                    delay,
                    attempt + 1,
                    retry_config.max_attempts,
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        raise RetryExhaustedError(
            "REST request failed after all retry attempts",
            attempts=retry_config.max_attempts,
            last_error=last_error or Exception("Unknown error"),
        )

    async def _get_access_token(self, session: aiohttp.ClientSession) -> str | None:
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            # Add buffer time to refresh before actual expiration
            if time.time() < (self._token_expires_at - TOKEN_EXPIRY_BUFFER_SECONDS):
                return self._access_token
            logger.debug("Access token expired or expiring soon, refreshing")

        if not (self._config.username and self._config.password):
            return None

        async with self._auth_lock:
            # Double-check after acquiring lock
            if self._access_token and self._token_expires_at:
                if time.time() < (self._token_expires_at - TOKEN_EXPIRY_BUFFER_SECONDS):
                    return self._access_token

            auth_client = NationalGridAuth()
            token, expires_in = await auth_client.async_login(
                session,
                self._config.username,
                self._config.password,
                self._login_data,
                timeout=self._config.timeout,
            )
            if token and expires_in:
                self._access_token = token
                self._token_expires_at = time.time() + expires_in
                logger.debug("Access token refreshed, expires in %d seconds", expires_in)
            else:
                self._access_token = None
                self._token_expires_at = None

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
        # Fast path: check without lock if session exists and is open
        if self._session and not self._session.closed:
            return self._session

        # Slow path: acquire lock to create session
        async with self._session_lock:
            # Double-check after acquiring lock
            if self._session and not self._session.closed:
                return self._session

            timeout = aiohttp.ClientTimeout(total=self._config.timeout)
            # Create connector with configured limits
            connector = aiohttp.TCPConnector(
                limit=self._config.connection_limit,
                limit_per_host=self._config.connection_limit_per_host,
                ttl_dns_cache=self._config.dns_cache_ttl,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
            )
            return self._session

    async def ping(self) -> bool:
        """Simple health-check that issues an empty request body."""

        dummy_request = GraphQLRequest(query="query Ping { __typename }")
        response = await self.execute(dummy_request)
        return response.data is not None

    async def linked_billing_accounts(
        self,
        *,
        selection_set: str = LINKED_BILLING_SELECTION_SET,
        variables: Mapping[str, Any] | None = None,
        variable_definitions: str | Sequence[str] | None = None,
        field_arguments: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> GraphQLResponse:
        """Execute the linked billing accounts scaffold query."""
        session = await self._ensure_session()
        await self._get_access_token(session)
        if variables is None:
            sub_value = self._login_data.get("sub")
            if sub_value:
                variables = {"userId": sub_value}
        request = linked_billing_accounts_request(
            selection_set=selection_set,
            variables=variables,
            variable_definitions=variable_definitions,
            field_arguments=field_arguments,
        )
        return await self.execute(request, headers=headers, timeout=timeout)

    async def billing_account_info(
        self,
        *,
        selection_set: str = BILLING_ACCOUNT_INFO_SELECTION_SET,
        variables: Mapping[str, Any] | None = None,
        variable_definitions: str | Sequence[str] | None = None,
        field_arguments: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> GraphQLResponse:
        """Execute the billing account information scaffold query."""

        request = billing_account_info_request(
            selection_set=selection_set,
            variables=variables,
            variable_definitions=variable_definitions,
            field_arguments=field_arguments,
        )
        return await self.execute(request, headers=headers, timeout=timeout)

    async def energy_usage(
        self,
        *,
        selection_set: str = DEFAULT_SELECTION_SET,
        variables: Mapping[str, Any] | None = None,
        variable_definitions: str | Sequence[str] | None = None,
        field_arguments: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> GraphQLResponse:
        """Execute the energy usage scaffold query."""

        request = energy_usage_request(
            selection_set=selection_set,
            variables=variables,
            variable_definitions=variable_definitions,
            field_arguments=field_arguments,
        )
        return await self.execute(request, headers=headers, timeout=timeout)

    async def realtime_meter_info(
        self,
        *,
        premise_number: str,
        service_point_number: str,
        start_datetime: str,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> RestResponse:
        """Execute the real-time meter interval reads REST request."""

        request = realtime_meter_info_request(
            premise_number=premise_number,
            service_point_number=service_point_number,
            start_datetime=start_datetime,
            params=params,
            headers=headers,
        )
        return await self.request_rest(
            request.method,
            request.path_or_url,
            params=request.params,
            json=request.json,
            data=request.data,
            headers=request.headers,
            timeout=timeout,
        )
