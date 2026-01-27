from __future__ import annotations

from aionatgrid.config import DEFAULT_ENDPOINT, NationalGridConfig


def test_default_config_values() -> None:
    config = NationalGridConfig()

    assert config.endpoint == DEFAULT_ENDPOINT
    assert config.username is None
    assert config.password is None
    assert config.subscription_key == "e674f89d7ed9417194de894b701333dd"


def test_config_with_credentials() -> None:
    config = NationalGridConfig(
        username="user@example.com",
        password="super-secret",
    )

    assert config.username == "user@example.com"
    assert config.password == "super-secret"


def test_build_headers_merges_overrides() -> None:
    config = NationalGridConfig(default_headers={"X-Test": "1"}, subscription_key="sub-key")

    headers = config.build_headers({"Another": "2"}, access_token="abc")

    assert headers["Authorization"] == "Bearer abc"
    assert headers["ocp-apim-subscription-key"] == "sub-key"
    assert headers["X-Test"] == "1"
    assert headers["Another"] == "2"
    assert headers["Content-Type"] == "application/json"


def test_connection_pool_defaults() -> None:
    """Verify default connection pool settings."""
    config = NationalGridConfig()
    assert config.connection_limit == 100
    assert config.connection_limit_per_host == 30
    assert config.dns_cache_ttl == 300


def test_connection_pool_overrides() -> None:
    """Verify custom connection pool configuration."""
    config = NationalGridConfig(
        connection_limit=50,
        connection_limit_per_host=10,
        dns_cache_ttl=600,
    )
    assert config.connection_limit == 50
    assert config.connection_limit_per_host == 10
    assert config.dns_cache_ttl == 600
