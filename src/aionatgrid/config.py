"""Configuration utilities for the National Grid GraphQL client."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

DEFAULT_ENDPOINT = "https://myaccount.nationalgrid.com/api/user-cu-uwp-gql"
DEFAULT_TIMEOUT = 30.0


@dataclass(slots=True)
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3  # Maximum number of attempts (including initial request)
    initial_delay: float = 1.0  # Initial retry delay in seconds
    max_delay: float = 10.0  # Maximum retry delay in seconds
    exponential_base: float = 2.0  # Base for exponential backoff
    retry_on_status: tuple[int, ...] = (408, 429, 500, 502, 503, 504)  # HTTP statuses to retry
    retry_on_connection_errors: bool = True  # Retry on connection errors
    retry_on_timeout: bool = True  # Retry on timeout errors


@dataclass(slots=True)
class NationalGridConfig:
    """Holds reusable client configuration."""

    endpoint: str = DEFAULT_ENDPOINT
    rest_base_url: str = "https://myaccount.nationalgrid.com/api"
    username: str | None = None
    password: str | None = None
    subscription_key: str = "e674f89d7ed9417194de894b701333dd"
    default_headers: Mapping[str, str] = field(default_factory=dict)
    timeout: float = DEFAULT_TIMEOUT
    verify_ssl: bool = True
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    # Connection pool settings
    connection_limit: int = 100  # Total connection pool size
    connection_limit_per_host: int = 30  # Connections per individual host
    dns_cache_ttl: int = 300  # DNS cache TTL in seconds

    def build_headers(
        self,
        extra_headers: Mapping[str, str] | None = None,
        *,
        access_token: str | None = None,
        content_type: str | None = "application/json",
    ) -> dict[str, str]:
        """Combine default headers, authentication, and ad-hoc overrides."""

        headers: dict[str, str] = {
            "Accept": "application/json",
        }
        if content_type:
            headers["Content-Type"] = content_type
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if self.subscription_key:
            headers["ocp-apim-subscription-key"] = self.subscription_key
        headers.update(self.default_headers)
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def with_overrides(self, **overrides: object) -> NationalGridConfig:
        """Return a cloned config with updated fields."""

        data = asdict(self)
        data.update(overrides)
        return NationalGridConfig(**data)
