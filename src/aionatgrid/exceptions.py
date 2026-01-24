"""Exceptions."""

from __future__ import annotations

from typing import Any


class CannotConnectError(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuthError(Exception):
    """Error to indicate there is invalid auth."""


class NationalGridError(Exception):
    """Base exception for National Grid API errors."""


class GraphQLError(NationalGridError):
    """Raised when GraphQL request fails."""

    def __init__(
        self,
        message: str,
        endpoint: str,
        query: str | None = None,
        variables: dict[str, Any] | None = None,
        status: int | None = None,
        response_body: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize GraphQL error with context.

        Args:
            message: Human-readable error message
            endpoint: GraphQL endpoint URL
            query: GraphQL query that failed (optional)
            variables: Query variables (optional)
            status: HTTP status code (optional)
            response_body: Response body if available (optional)
            original_error: Original exception that caused this (optional)
        """
        super().__init__(message)
        self.endpoint = endpoint
        self.query = query
        self.variables = variables
        self.status = status
        self.response_body = response_body
        self.original_error = original_error

    def __str__(self) -> str:
        """Return detailed error representation."""
        parts = [super().__str__()]
        parts.append(f"Endpoint: {self.endpoint}")
        if self.status is not None:
            parts.append(f"Status: {self.status}")
        if self.query:
            # Truncate long queries
            query_preview = self.query[:200] + "..." if len(self.query) > 200 else self.query
            parts.append(f"Query: {query_preview}")
        if self.variables:
            parts.append(f"Variables: {self.variables}")
        if self.original_error:
            parts.append(f"Caused by: {type(self.original_error).__name__}: {self.original_error}")
        return "\n".join(parts)


class RestAPIError(NationalGridError):
    """Raised when REST API request fails."""

    def __init__(
        self,
        message: str,
        url: str,
        method: str,
        status: int | None = None,
        response_text: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize REST API error with context.

        Args:
            message: Human-readable error message
            url: Full request URL
            method: HTTP method (GET, POST, etc.)
            status: HTTP status code (optional)
            response_text: Response body text (optional)
            original_error: Original exception that caused this (optional)
        """
        super().__init__(message)
        self.url = url
        self.method = method
        self.status = status
        self.response_text = response_text
        self.original_error = original_error

    def __str__(self) -> str:
        """Return detailed error representation."""
        parts = [super().__str__()]
        parts.append(f"Request: {self.method} {self.url}")
        if self.status is not None:
            parts.append(f"Status: {self.status}")
        if self.response_text:
            # Truncate long responses
            text_preview = (
                self.response_text[:500] + "..."
                if len(self.response_text) > 500
                else self.response_text
            )
            parts.append(f"Response: {text_preview}")
        if self.original_error:
            parts.append(f"Caused by: {type(self.original_error).__name__}: {self.original_error}")
        return "\n".join(parts)


class RetryExhaustedError(NationalGridError):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_error: Exception,
    ) -> None:
        """Initialize retry exhausted error.

        Args:
            message: Human-readable error message
            attempts: Number of attempts made
            last_error: The final error that caused failure
        """
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error

    def __str__(self) -> str:
        """Return detailed error representation."""
        return (
            f"{super().__str__()} (after {self.attempts} attempts)\nLast error: {self.last_error}"
        )
