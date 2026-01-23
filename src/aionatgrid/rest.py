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
