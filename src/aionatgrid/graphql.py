"""Thin abstractions around GraphQL request and response payloads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from textwrap import dedent
from typing import Any


@dataclass(slots=True)
class GraphQLRequest:
    """A reusable GraphQL request payload."""

    query: str
    variables: Mapping[str, Any] | None = None
    operation_name: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": dedent(self.query).strip()}
        if self.variables:
            payload["variables"] = dict(self.variables)
        if self.operation_name:
            payload["operationName"] = self.operation_name
        return payload


@dataclass(slots=True)
class GraphQLResponse:
    """Normalized GraphQL response envelope."""

    data: Mapping[str, Any] | None
    errors: list[Mapping[str, Any]] | None = None
    extensions: Mapping[str, Any] | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "GraphQLResponse":
        return cls(
            data=payload.get("data"),
            errors=payload.get("errors"),
            extensions=payload.get("extensions"),
        )

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def raise_on_errors(self) -> None:
        """Raise a ValueError when the response contains GraphQL errors."""

        if not self.errors:
            return
        raise ValueError(f"GraphQL errors encountered: {self.errors}")


def compose_query(operation: str, selection_set: str, *, variables: str | None = None) -> str:
    """Helper to build a GraphQL query string with consistent indentation."""

    header_parts = [operation]
    if variables:
        header_parts.append(f"({variables})")
    header = "".join(header_parts)
    return dedent(
        f"""
        query {header} {{
        {selection_set}
        }}
        """
    ).strip()
