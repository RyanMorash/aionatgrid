"""TypedDict models for National Grid API responses."""

from __future__ import annotations

from typing import TypedDict


# Linked Billing Accounts (user-cu-uwp-gql)
class AccountLink(TypedDict):
    """A linked billing account identifier.

    Attributes:
        accountLinkId: Unique identifier for the account link
        billingAccountId: The billing account number
    """

    accountLinkId: str
    billingAccountId: str


class AccountLinksConnection(TypedDict):
    """Connection type for account links.

    Attributes:
        totalCount: Total number of linked accounts
        nodes: List of account link records
    """

    totalCount: int
    nodes: list[AccountLink]


# Billing Account Info (billingaccount-cu-uwp-gql)
class FuelType(TypedDict):
    """Fuel type information.

    Attributes:
        type: Fuel type name (e.g., "ELECTRIC", "GAS")
    """

    type: str


class ServiceAddress(TypedDict):
    """Service address information.

    Attributes:
        serviceAddressCompressed: Single-line formatted service address
    """

    serviceAddressCompressed: str


class CustomerInfo(TypedDict):
    """Customer information.

    Attributes:
        customerType: Type of customer (e.g., "RESIDENTIAL", "COMMERCIAL")
    """

    customerType: str


class Meter(TypedDict):
    """Meter information.

    Attributes:
        isSmartMeter: Whether this is a smart meter
        hasAmiSmartMeter: Whether this meter has AMI smart meter capability
        deviceCode: Device code identifier
        fuelType: Fuel type served by this meter (e.g., "ELECTRIC", "GAS")
        meterPointTypeCode: Meter point type classification code
        meterPointNumber: Meter point number
        servicePointNumber: Service point number
        meterNumber: Meter number identifier
    """

    isSmartMeter: bool
    hasAmiSmartMeter: bool
    deviceCode: str
    fuelType: str
    meterPointTypeCode: str
    meterPointNumber: int
    servicePointNumber: int
    meterNumber: str


class MeterConnection(TypedDict):
    """Connection type for meters.

    Attributes:
        nodes: List of meter records
    """

    nodes: list[Meter]


class BillingAccount(TypedDict):
    """Billing account information.

    Attributes:
        region: Service region name
        regionAbbreviation: Abbreviated region code
        type: Account type
        fuelTypes: Fuel types associated with this account
        status: Account status (e.g., "ACTIVE")
        serviceAddress: Service address for the account
        customerInfo: Customer information
        customerNumber: Customer number
        premiseNumber: Premise number
        meter: Connected meters for the account
    """

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
    """Energy usage cost data.

    Attributes:
        date: Date of usage in YYYY-MM-DD format
        fuelType: Fuel type (e.g., "ELECTRIC", "GAS")
        amount: Cost amount in dollars
        month: Billing month in YYYYMM format
    """

    date: str
    fuelType: str
    amount: float
    month: int


class EnergyUsageCostsConnection(TypedDict):
    """Connection type for energy usage costs.

    Attributes:
        nodes: List of energy usage cost records
    """

    nodes: list[EnergyUsageCost]


# Energy Usages (energyusage-cu-uwp-gql)
class EnergyUsage(TypedDict):
    """Historical energy usage data.

    Attributes:
        usage: Energy usage quantity
        usageType: Type of usage measurement
        usageYearMonth: Year and month in YYYYMM format (e.g., 202401)
    """

    usage: float
    usageType: str
    usageYearMonth: int


class EnergyUsagesConnection(TypedDict):
    """Connection type for energy usages.

    Attributes:
        nodes: List of energy usage records
    """

    nodes: list[EnergyUsage]


# AMI Energy Usages (energyusage-cu-uwp-gql)
class AmiEnergyUsage(TypedDict):
    """AMI hourly energy usage data.

    Attributes:
        date: Date of usage in YYYY-MM-DD format
        fuelType: Fuel type (e.g., "ELECTRIC", "GAS")
        quantity: Energy usage quantity for the day
    """

    date: str
    fuelType: str
    quantity: float


class AmiEnergyUsagesConnection(TypedDict):
    """Connection type for AMI energy usages.

    Attributes:
        nodes: List of AMI energy usage records
    """

    nodes: list[AmiEnergyUsage]


# REST: Interval Reads
class IntervalRead(TypedDict):
    """Real-time meter interval read data (15-minute intervals).

    Attributes:
        startTime: Start of interval in ISO 8601 format with timezone
                   (e.g., "2026-01-22T13:00:00-05:00")
        endTime: End of interval in ISO 8601 format with timezone
                 (e.g., "2026-01-22T13:15:00-05:00")
        value: Energy usage in kWh for this interval
    """

    startTime: str
    endTime: str
    value: float
