"""Public package exports for aionatgrid."""

from .client import NationalGridClient
from .config import NationalGridConfig, RetryConfig
from .exceptions import (
    CannotConnectError,
    GraphQLError,
    InvalidAuthError,
    NationalGridError,
    RestAPIError,
    RetryExhaustedError,
)
from .graphql import GraphQLRequest, GraphQLResponse
from .oidchelper import LoginData
from .queries import (
    DEFAULT_SELECTION_SET,
    ENERGY_USAGE_COSTS_SELECTION_SET,
    ENERGY_USAGES_SELECTION_SET,
    StandardQuery,
    billing_account_info_request,
    energy_usage_costs_request,
    energy_usages_request,
    linked_billing_accounts_request,
)
from .rest import RestRequest, RestResponse
from .rest_queries import RealtimeMeterInfo, realtime_meter_info_request

__all__ = [
    "NationalGridClient",
    "NationalGridConfig",
    "RetryConfig",
    "GraphQLRequest",
    "GraphQLResponse",
    "LoginData",
    "DEFAULT_SELECTION_SET",
    "ENERGY_USAGE_COSTS_SELECTION_SET",
    "ENERGY_USAGES_SELECTION_SET",
    "RestRequest",
    "RestResponse",
    "StandardQuery",
    "billing_account_info_request",
    "energy_usage_costs_request",
    "energy_usages_request",
    "linked_billing_accounts_request",
    "RealtimeMeterInfo",
    "realtime_meter_info_request",
    # Exceptions
    "NationalGridError",
    "GraphQLError",
    "RestAPIError",
    "RetryExhaustedError",
    "CannotConnectError",
    "InvalidAuthError",
]
