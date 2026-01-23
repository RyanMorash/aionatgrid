from __future__ import annotations

import pytest

from aionatgrid.config import DEFAULT_ENDPOINT, NationalGridConfig


def test_from_env_reads_expected_values(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = "https://example.test/graphql"
    username = "user@example.com"
    password = "super-secret"
    subscription_key = "sub-key"
    monkeypatch.setenv("NATIONALGRID_GRAPHQL_ENDPOINT", endpoint)
    monkeypatch.setenv("NATIONALGRID_USERNAME", username)
    monkeypatch.setenv("NATIONALGRID_PASSWORD", password)
    monkeypatch.setenv("NATIONALGRID_SUBSCRIPTION_KEY", subscription_key)

    config = NationalGridConfig.from_env()

    assert config.endpoint == endpoint
    assert config.username == username
    assert config.password == password
    assert config.subscription_key == subscription_key


def test_from_env_uses_defaults_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NATIONALGRID_GRAPHQL_ENDPOINT", raising=False)
    monkeypatch.delenv("NATIONALGRID_USERNAME", raising=False)
    monkeypatch.delenv("NATIONALGRID_PASSWORD", raising=False)
    monkeypatch.delenv("NATIONALGRID_SUBSCRIPTION_KEY", raising=False)

    config = NationalGridConfig.from_env()

    assert config.endpoint == DEFAULT_ENDPOINT
    assert config.username is None
    assert config.password is None
    assert config.subscription_key is None


def test_build_headers_merges_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NATIONALGRID_GRAPHQL_ENDPOINT", raising=False)
    config = NationalGridConfig(default_headers={"X-Test": "1"}, subscription_key="sub-key")

    headers = config.build_headers({"Another": "2"}, access_token="abc")

    assert headers["Authorization"] == "Bearer abc"
    assert headers["ocp-apim-subscription-key"] == "sub-key"
    assert headers["X-Test"] == "1"
    assert headers["Another"] == "2"
    assert headers["Content-Type"] == "application/json"
