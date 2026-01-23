"""Configuration utilities for the National Grid GraphQL client."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Mapping
import os

DEFAULT_ENDPOINT = "https://api.nationalgrid.example/graphql"
DEFAULT_TIMEOUT = 30.0


@dataclass(slots=True)
class NationalGridConfig:
    """Holds reusable client configuration."""

    endpoint: str = DEFAULT_ENDPOINT
    api_key: str | None = None
    default_headers: Mapping[str, str] = field(default_factory=dict)
    timeout: float = DEFAULT_TIMEOUT
    verify_ssl: bool = True

    @classmethod
    def from_env(
        cls,
        *,
        endpoint_env: str = "NATIONALGRID_GRAPHQL_ENDPOINT",
        api_key_env: str = "NATIONALGRID_API_KEY",
    ) -> "NationalGridConfig":
        """Load configuration values from environment variables."""

        endpoint = os.environ.get(endpoint_env, DEFAULT_ENDPOINT)
        api_key = os.environ.get(api_key_env)
        return cls(endpoint=endpoint, api_key=api_key)

    def build_headers(self, extra_headers: Mapping[str, str] | None = None) -> dict[str, str]:
        """Combine default headers, authentication, and ad-hoc overrides."""

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.default_headers)
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def with_overrides(self, **overrides: object) -> "NationalGridConfig":
        """Return a cloned config with updated fields."""

        data = asdict(self)
        data.update(overrides)
        return NationalGridConfig(**data)
