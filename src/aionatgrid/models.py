"""TypedDict models for National Grid API responses."""

from __future__ import annotations

from typing import TypedDict


# Linked Billing Accounts (user-cu-uwp-gql)
class AccountLink(TypedDict):
    """A linked billing account identifier."""

    accountLinkId: str
    billingAccountId: str


class AccountLinksConnection(TypedDict):
    """Connection type for account links."""

    totalCount: int
    nodes: list[AccountLink]


# Billing Account Info (billingaccount-cu-uwp-gql)
class FuelType(TypedDict):
    """Fuel type information."""

    type: str


class ServiceAddress(TypedDict):
    """Service address information."""

    serviceAddressCompressed: str


class CustomerInfo(TypedDict):
    """Customer information."""

    customerType: str


class Meter(TypedDict):
    """Meter information."""

    isSmartMeter: bool
    hasAmiSmartMeter: bool
    deviceCode: str
    fuelType: str
    meterPointTypeCode: str
    meterPointNumber: int
    servicePointNumber: int
    meterNumber: str


class MeterConnection(TypedDict):
    """Connection type for meters."""

    nodes: list[Meter]


class BillingAccount(TypedDict):
    """Billing account information."""

    region: str
    regionAbbreviation: str
    type: str
    fuelTypes: list[FuelType]
    status: str
    serviceAddress: ServiceAddress
    customerInfo: CustomerInfo
    customerNumber: int
    premiseNumber: int
    meter: MeterConnection


# Energy Usage Costs (energyusage-cu-uwp-gql)
class EnergyUsageCost(TypedDict):
    """Energy usage cost data."""

    date: str
    fuelType: str
    amount: float
    month: str


class EnergyUsageCostsConnection(TypedDict):
    """Connection type for energy usage costs."""

    nodes: list[EnergyUsageCost]


# Energy Usages (energyusage-cu-uwp-gql)
class EnergyUsage(TypedDict):
    """Historical energy usage data."""

    usage: float
    usageType: str
    usageYearMonth: int


class EnergyUsagesConnection(TypedDict):
    """Connection type for energy usages."""

    nodes: list[EnergyUsage]


# REST: Interval Reads (total=False for flexible schema)
class IntervalRead(TypedDict, total=False):
    """Real-time meter interval read data."""

    timestamp: str
    value: float
    unit: str
    quality: str
