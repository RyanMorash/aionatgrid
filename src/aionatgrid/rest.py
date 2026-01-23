"""Helper types for REST responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True)
class RestResponse:
    """Normalized REST response envelope."""

    status: int
    headers: Mapping[str, str]
    data: Any
