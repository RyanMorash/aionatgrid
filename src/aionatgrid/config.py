"""Configuration utilities for the National Grid GraphQL client."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

DEFAULT_ENDPOINT = "https://myaccount.nationalgrid.com/api/user-cu-uwp-gql"
DEFAULT_TIMEOUT = 30.0


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

    @classmethod
    def from_env(
        cls,
        *,
        endpoint_env: str = "NATIONALGRID_GRAPHQL_ENDPOINT",
        username_env: str = "NATIONALGRID_USERNAME",
        password_env: str = "NATIONALGRID_PASSWORD",
    ) -> NationalGridConfig:
        """Load configuration values from environment variables."""

        endpoint = os.environ.get(endpoint_env, DEFAULT_ENDPOINT)
        username = os.environ.get(username_env)
        password = os.environ.get(password_env)
        return cls(endpoint=endpoint, username=username, password=password)

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
