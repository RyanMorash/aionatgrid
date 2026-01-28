"""Public package exports for aionatgrid."""

from .client import NationalGridClient
from .config import NationalGridConfig, RetryConfig
from .exceptions import (
    CannotConnectError,
    DataExtractionError,
    GraphQLError,
    InvalidAuthError,
    NationalGridError,
    RestAPIError,
    RetryExhaustedError,
)
from .helpers import create_cookie_jar
from .models import (
    AccountLink,
    AccountLinksConnection,
    BillingAccount,
    CustomerInfo,
    EnergyUsage,
    EnergyUsageCost,
    EnergyUsageCostsConnection,
    EnergyUsagesConnection,
    FuelType,
    IntervalRead,
    Meter,
    MeterConnection,
    ServiceAddress,
)
from .oidchelper import LoginData

__all__ = [
    "NationalGridClient",
    "NationalGridConfig",
    "RetryConfig",
    "LoginData",
    "create_cookie_jar",
    # Exceptions
    "NationalGridError",
    "GraphQLError",
    "RestAPIError",
    "RetryExhaustedError",
    "DataExtractionError",
    "CannotConnectError",
    "InvalidAuthError",
    # TypedDict models
    "AccountLink",
    "AccountLinksConnection",
    "BillingAccount",
    "CustomerInfo",
    "EnergyUsage",
    "EnergyUsageCost",
    "EnergyUsageCostsConnection",
    "EnergyUsagesConnection",
    "FuelType",
    "IntervalRead",
    "Meter",
    "MeterConnection",
    "ServiceAddress",
]
