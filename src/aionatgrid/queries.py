"""Scaffolded GraphQL query builders for National Grid."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from textwrap import dedent, indent
from typing import Any

from .graphql import GraphQLRequest, compose_query

DEFAULT_SELECTION_SET = "__typename"
LINKED_BILLING_ENDPOINT = "https://myaccount.nationalgrid.com/api/user-cu-uwp-gql"
BILLING_ACCOUNT_INFO_ENDPOINT = "https://myaccount.nationalgrid.com/api/billingaccount-cu-uwp-gql"
ENERGY_USAGE_ENDPOINT = "https://myaccount.nationalgrid.com/api/energyusage-cu-uwp-gql"
LINKED_BILLING_SELECTION_SET = """
accountLinks {
    totalCount
    nodes {
        accountLinkId
        billingAccountId
    }
}
"""
BILLING_ACCOUNT_INFO_SELECTION_SET = """
region
regionAbbreviation
type
fuelTypes {
    type
}
status
serviceAddress {
    serviceAddressCompressed
}
customerInfo {
    customerType
}
customerNumber
premiseNumber
meter {
    nodes {
        isSmartMeter
        hasAmiSmartMeter
        deviceCode
        fuelType
        meterPointTypeCode
        meterPointNumber
        servicePointNumber
        meterNumber
    }
}
"""
ENERGY_USAGE_COSTS_SELECTION_SET = """
nodes {
    date
    fuelType
    amount
    month
}
"""
ENERGY_USAGES_SELECTION_SET = """
nodes {
    usage
    usageType
    usageYearMonth
}
"""


@dataclass(slots=True)
class StandardQuery:
    """Generic query definition for scaffolding GraphQL operations."""

    operation_name: str
    root_field: str
    selection_set: str = DEFAULT_SELECTION_SET
    variables: Mapping[str, Any] | None = None
    variable_definitions: str | Sequence[str] | None = None
    field_arguments: str | None = None
    endpoint: str | None = None

    def to_request(self) -> GraphQLRequest:
        """Convert this scaffold into a `GraphQLRequest`."""

        selection_set = dedent(self.selection_set).strip() or DEFAULT_SELECTION_SET
        selection_block = indent(selection_set, "  ")
        field_args = f"({self.field_arguments})" if self.field_arguments else ""
        selection = dedent(
            f"""
            {self.root_field}{field_args} {{
            {selection_block}
            }}
            """
        ).strip()
        variable_definitions = _normalize_variable_definitions(self.variable_definitions)
        query = compose_query(self.operation_name, selection, variables=variable_definitions)
        return GraphQLRequest(
            query=query,
            variables=self.variables,
            operation_name=self.operation_name,
            endpoint=self.endpoint,
        )


def linked_billing_accounts_request(
    *,
    selection_set: str = LINKED_BILLING_SELECTION_SET,
    variables: Mapping[str, Any] | None = None,
    variable_definitions: str | Sequence[str] | None = "$userId: String!",
    field_arguments: str | None = "userId: $userId",
    operation_name: str = "AccountIdentifiers",
) -> GraphQLRequest:
    """Scaffold a linked billing accounts query.

    This request targets the user-cu-uwp-gql GraphQL endpoint.
    """

    return StandardQuery(
        operation_name=operation_name,
        root_field="user",
        selection_set=selection_set,
        variables=variables,
        variable_definitions=variable_definitions,
        field_arguments=field_arguments,
        endpoint=LINKED_BILLING_ENDPOINT,
    ).to_request()


def billing_account_info_request(
    *,
    selection_set: str = BILLING_ACCOUNT_INFO_SELECTION_SET,
    variables: Mapping[str, Any] | None = None,
    variable_definitions: str | Sequence[str] | None = "$accountNumber: String!",
    field_arguments: str | None = "accountNumber: $accountNumber",
    operation_name: str = "OpowerAccount",
) -> GraphQLRequest:
    """Scaffold a billing account information query.

    This request targets the billingaccount-cu-uwp-gql GraphQL endpoint.
    """

    return StandardQuery(
        operation_name=operation_name,
        root_field="billingAccount",
        selection_set=selection_set,
        variables=variables,
        variable_definitions=variable_definitions,
        field_arguments=field_arguments,
        endpoint=BILLING_ACCOUNT_INFO_ENDPOINT,
    ).to_request()


def energy_usage_costs_request(
    *,
    selection_set: str = ENERGY_USAGE_COSTS_SELECTION_SET,
    variables: Mapping[str, Any] | None = None,
    variable_definitions: str | Sequence[str] | None = (
        "$accountNumber: String!",
        "$date: Date!",
        "$companyCode: CompanyCodeValue!",
    ),
    field_arguments: str | None = (
        "accountNumber: $accountNumber, date: $date, companyCode: $companyCode"
    ),
    operation_name: str = "EnergyUsageCosts",
) -> GraphQLRequest:
    """Scaffold an energy usage costs query.

    This request targets the energyusage-cu-uwp-gql GraphQL endpoint.
    """
    return StandardQuery(
        operation_name=operation_name,
        root_field="energyUsageCosts",
        selection_set=selection_set,
        variables=variables,
        variable_definitions=variable_definitions,
        field_arguments=field_arguments,
        endpoint=ENERGY_USAGE_ENDPOINT,
    ).to_request()


def energy_usages_request(
    *,
    selection_set: str = ENERGY_USAGES_SELECTION_SET,
    variables: Mapping[str, Any] | None = None,
    variable_definitions: str | Sequence[str] | None = (
        "$accountNumber: String!",
        "$from: Int!",
        "$first: Int!",
    ),
    field_arguments: str | None = (
        "accountNumber: $accountNumber, "
        "where: {usageYearMonth: {gte: $from}}, "
        "order: [{usageYearMonth: DESC}], "
        "first: $first"
    ),
    operation_name: str = "EnergyUsages",
) -> GraphQLRequest:
    """Scaffold an energy usages query.

    This request targets the energyusage-cu-uwp-gql GraphQL endpoint.
    """
    return StandardQuery(
        operation_name=operation_name,
        root_field="energyUsages",
        selection_set=selection_set,
        variables=variables,
        variable_definitions=variable_definitions,
        field_arguments=field_arguments,
        endpoint=ENERGY_USAGE_ENDPOINT,
    ).to_request()


def _normalize_variable_definitions(value: str | Sequence[str] | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    parts = [item.strip() for item in value if item.strip()]
    return ", ".join(parts) if parts else None
