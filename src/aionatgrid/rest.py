"""Helper types for REST responses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RestResponse:
    """Normalized REST response envelope."""

    status: int
    headers: Mapping[str, str]
    data: Any


@dataclass(slots=True)
class RestRequest:
    """Simple REST request definition."""

    method: str
    path_or_url: str
    params: Mapping[str, str] | None = None
    json: Any | None = None
    data: Any | None = None
    headers: Mapping[str, str] | None = None
