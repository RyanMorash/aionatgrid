"""Data extraction helpers for converting raw responses to typed models."""

from __future__ import annotations

from typing import cast

from .exceptions import DataExtractionError
from .graphql import GraphQLResponse
from .models import (
    AccountLink,
    AmiEnergyUsage,
    BillingAccount,
    EnergyUsage,
    EnergyUsageCost,
    IntervalRead,
)
from .rest import RestResponse


def extract_linked_accounts(response: GraphQLResponse) -> list[AccountLink]:
    """Extract linked accounts from a GraphQL response.

    Args:
        response: The GraphQL response from linked_billing_accounts()

    Returns:
        List of account links

    Raises:
        ValueError: If the response contains GraphQL errors
        DataExtractionError: If the expected data path is missing
    """
    response.raise_on_errors()

    if response.data is None:
        raise DataExtractionError(
            "Response data is null",
            path="data",
            response_data=None,
        )

    user = response.data.get("user")
    if user is None:
        raise DataExtractionError(
            "Missing 'user' field in response",
            path="data.user",
            response_data=response.data,
        )

    account_links = user.get("accountLinks")
    if account_links is None:
        raise DataExtractionError(
            "Missing 'accountLinks' field in response",
            path="data.user.accountLinks",
            response_data=response.data,
        )

    nodes = account_links.get("nodes")
    if nodes is None:
        raise DataExtractionError(
            "Missing 'nodes' field in accountLinks",
            path="data.user.accountLinks.nodes",
            response_data=response.data,
        )

    return cast(list[AccountLink], nodes)


def extract_billing_account(response: GraphQLResponse) -> BillingAccount:
    """Extract billing account info from a GraphQL response.

    Args:
        response: The GraphQL response from billing_account_info()

    Returns:
        Billing account information

    Raises:
        ValueError: If the response contains GraphQL errors
        DataExtractionError: If the expected data path is missing
    """
    response.raise_on_errors()

    if response.data is None:
        raise DataExtractionError(
            "Response data is null",
            path="data",
            response_data=None,
        )

    billing_account = response.data.get("billingAccount")
    if billing_account is None:
        raise DataExtractionError(
            "Missing 'billingAccount' field in response",
            path="data.billingAccount",
            response_data=response.data,
        )

    return cast(BillingAccount, billing_account)


def extract_energy_usage_costs(response: GraphQLResponse) -> list[EnergyUsageCost]:
    """Extract energy usage costs from a GraphQL response.

    Args:
        response: The GraphQL response from energy_usage_costs()

    Returns:
        List of energy usage costs

    Raises:
        ValueError: If the response contains GraphQL errors
        DataExtractionError: If the expected data path is missing
    """
    response.raise_on_errors()

    if response.data is None:
        raise DataExtractionError(
            "Response data is null",
            path="data",
            response_data=None,
        )

    energy_usage_costs = response.data.get("energyUsageCosts")
    if energy_usage_costs is None:
        raise DataExtractionError(
            "Missing 'energyUsageCosts' field in response",
            path="data.energyUsageCosts",
            response_data=response.data,
        )

    nodes = energy_usage_costs.get("nodes")
    if nodes is None:
        raise DataExtractionError(
            "Missing 'nodes' field in energyUsageCosts",
            path="data.energyUsageCosts.nodes",
            response_data=response.data,
        )

    return cast(list[EnergyUsageCost], nodes)


def extract_energy_usages(response: GraphQLResponse) -> list[EnergyUsage]:
    """Extract energy usages from a GraphQL response.

    Args:
        response: The GraphQL response from energy_usages()

    Returns:
        List of energy usages

    Raises:
        ValueError: If the response contains GraphQL errors
        DataExtractionError: If the expected data path is missing
    """
    response.raise_on_errors()

    if response.data is None:
        raise DataExtractionError(
            "Response data is null",
            path="data",
            response_data=None,
        )

    energy_usages = response.data.get("energyUsages")
    if energy_usages is None:
        raise DataExtractionError(
            "Missing 'energyUsages' field in response",
            path="data.energyUsages",
            response_data=response.data,
        )

    nodes = energy_usages.get("nodes")
    if nodes is None:
        raise DataExtractionError(
            "Missing 'nodes' field in energyUsages",
            path="data.energyUsages.nodes",
            response_data=response.data,
        )

    return cast(list[EnergyUsage], nodes)


def extract_ami_energy_usages(response: GraphQLResponse) -> list[AmiEnergyUsage]:
    """Extract AMI energy usages from a GraphQL response.

    Args:
        response: The GraphQL response from an AMI energy usages query

    Returns:
        List of AMI energy usages

    Raises:
        ValueError: If the response contains GraphQL errors
        DataExtractionError: If the expected data path is missing
    """
    response.raise_on_errors()

    if response.data is None:
        raise DataExtractionError(
            "Response data is null",
            path="data",
            response_data=None,
        )

    ami_energy_usages = response.data.get("amiEnergyUsages")
    if ami_energy_usages is None:
        raise DataExtractionError(
            "Missing 'amiEnergyUsages' field in response",
            path="data.amiEnergyUsages",
            response_data=response.data,
        )

    nodes = ami_energy_usages.get("nodes")
    if nodes is None:
        raise DataExtractionError(
            "Missing 'nodes' field in amiEnergyUsages",
            path="data.amiEnergyUsages.nodes",
            response_data=response.data,
        )

    return cast(list[AmiEnergyUsage], nodes)


def extract_interval_reads(response: RestResponse) -> list[IntervalRead]:
    """Extract interval reads from a REST response.

    Args:
        response: The REST response from realtime_meter_info()

    Returns:
        List of interval reads

    Raises:
        DataExtractionError: If the response data is not in expected format
    """
    if response.data is None:
        raise DataExtractionError(
            "Response data is null",
            path="data",
            response_data=None,
        )

    if not isinstance(response.data, list):
        raise DataExtractionError(
            "Expected list of interval reads",
            path="data",
            response_data=response.data,
        )

    return cast(list[IntervalRead], response.data)
