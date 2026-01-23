from __future__ import annotations

import pytest

from aionatgrid.config import DEFAULT_ENDPOINT, NationalGridConfig


def test_from_env_reads_expected_values(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = "https://example.test/graphql"
    api_key = "secret"
    monkeypatch.setenv("NATIONALGRID_GRAPHQL_ENDPOINT", endpoint)
    monkeypatch.setenv("NATIONALGRID_API_KEY", api_key)

    config = NationalGridConfig.from_env()

    assert config.endpoint == endpoint
    assert config.api_key == api_key


def test_from_env_uses_defaults_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NATIONALGRID_GRAPHQL_ENDPOINT", raising=False)
    monkeypatch.delenv("NATIONALGRID_API_KEY", raising=False)

    config = NationalGridConfig.from_env()

    assert config.endpoint == DEFAULT_ENDPOINT
    assert config.api_key is None


def test_build_headers_merges_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NATIONALGRID_GRAPHQL_ENDPOINT", raising=False)
    config = NationalGridConfig(api_key="abc", default_headers={"X-Test": "1"})

    headers = config.build_headers({"Another": "2"})

    assert headers["Authorization"] == "Bearer abc"
    assert headers["X-Test"] == "1"
    assert headers["Another"] == "2"
    assert headers["Content-Type"] == "application/json"
