"""Tests for TypedDict models and extraction helpers."""

from __future__ import annotations

import pytest

from aionatgrid.exceptions import DataExtractionError
from aionatgrid.extractors import (
    extract_billing_account,
    extract_energy_usage_costs,
    extract_energy_usages,
    extract_linked_accounts,
)
from aionatgrid.graphql import GraphQLResponse


class TestExtractLinkedAccounts:
    """Tests for extract_linked_accounts."""

    def test_extracts_accounts_successfully(self) -> None:
        """Successfully extracts account links from valid response."""
        response = GraphQLResponse(
            data={
                "user": {
                    "accountLinks": {
                        "totalCount": 2,
                        "nodes": [
                            {"accountLinkId": "link-1", "billingAccountId": "acct-001"},
                            {"accountLinkId": "link-2", "billingAccountId": "acct-002"},
                        ],
                    }
                }
            }
        )

        accounts = extract_linked_accounts(response)

        assert len(accounts) == 2
        assert accounts[0]["accountLinkId"] == "link-1"
        assert accounts[0]["billingAccountId"] == "acct-001"
        assert accounts[1]["accountLinkId"] == "link-2"
        assert accounts[1]["billingAccountId"] == "acct-002"

    def test_returns_empty_list_for_no_accounts(self) -> None:
        """Returns empty list when no accounts exist."""
        response = GraphQLResponse(
            data={
                "user": {
                    "accountLinks": {
                        "totalCount": 0,
                        "nodes": [],
                    }
                }
            }
        )

        accounts = extract_linked_accounts(response)

        assert accounts == []

    def test_raises_on_graphql_errors(self) -> None:
        """Raises ValueError when response contains GraphQL errors."""
        response = GraphQLResponse(
            data=None,
            errors=[{"message": "Unauthorized", "extensions": {"code": "UNAUTHENTICATED"}}],
        )

        with pytest.raises(ValueError, match="GraphQL errors encountered"):
            extract_linked_accounts(response)

    def test_raises_on_null_data(self) -> None:
        """Raises DataExtractionError when data is null."""
        response = GraphQLResponse(data=None)

        with pytest.raises(DataExtractionError, match="Response data is null"):
            extract_linked_accounts(response)

    def test_raises_on_missing_user(self) -> None:
        """Raises DataExtractionError when user field is missing."""
        response = GraphQLResponse(data={"other": "value"})

        with pytest.raises(DataExtractionError, match="Missing 'user' field"):
            extract_linked_accounts(response)

    def test_raises_on_missing_account_links(self) -> None:
        """Raises DataExtractionError when accountLinks is missing."""
        response = GraphQLResponse(data={"user": {"other": "value"}})

        with pytest.raises(DataExtractionError, match="Missing 'accountLinks' field"):
            extract_linked_accounts(response)

    def test_raises_on_missing_nodes(self) -> None:
        """Raises DataExtractionError when nodes is missing."""
        response = GraphQLResponse(data={"user": {"accountLinks": {"totalCount": 0}}})

        with pytest.raises(DataExtractionError, match="Missing 'nodes' field"):
            extract_linked_accounts(response)


class TestExtractBillingAccount:
    """Tests for extract_billing_account."""

    def test_extracts_billing_account_successfully(self) -> None:
        """Successfully extracts billing account from valid response."""
        response = GraphQLResponse(
            data={
                "billingAccount": {
                    "region": "Massachusetts",
                    "regionAbbreviation": "MA",
                    "type": "RESIDENTIAL",
                    "fuelTypes": [{"type": "ELECTRIC"}],
                    "status": "ACTIVE",
                    "serviceAddress": {"serviceAddressCompressed": "123 Main St"},
                    "customerInfo": {"customerType": "RESIDENTIAL"},
                    "customerNumber": "CUST-001",
                    "premiseNumber": "PREM-001",
                    "meter": {
                        "nodes": [
                            {
                                "isSmartMeter": True,
                                "hasAmiSmartMeter": True,
                                "deviceCode": "AMI",
                                "fuelType": "ELECTRIC",
                                "meterPointTypeCode": "E",
                                "meterPointNumber": "MP-001",
                                "servicePointNumber": "SP-001",
                                "meterNumber": "M-001",
                            }
                        ]
                    },
                }
            }
        )

        account = extract_billing_account(response)

        assert account["region"] == "Massachusetts"
        assert account["regionAbbreviation"] == "MA"
        assert account["status"] == "ACTIVE"
        assert account["premiseNumber"] == "PREM-001"
        assert len(account["meter"]["nodes"]) == 1
        assert account["meter"]["nodes"][0]["isSmartMeter"] is True

    def test_raises_on_graphql_errors(self) -> None:
        """Raises ValueError when response contains GraphQL errors."""
        response = GraphQLResponse(
            data=None,
            errors=[{"message": "Not found", "extensions": {"code": "NOT_FOUND"}}],
        )

        with pytest.raises(ValueError, match="GraphQL errors encountered"):
            extract_billing_account(response)

    def test_raises_on_null_data(self) -> None:
        """Raises DataExtractionError when data is null."""
        response = GraphQLResponse(data=None)

        with pytest.raises(DataExtractionError, match="Response data is null"):
            extract_billing_account(response)

    def test_raises_on_missing_billing_account(self) -> None:
        """Raises DataExtractionError when billingAccount is missing."""
        response = GraphQLResponse(data={"other": "value"})

        with pytest.raises(DataExtractionError, match="Missing 'billingAccount' field"):
            extract_billing_account(response)


class TestExtractEnergyUsageCosts:
    """Tests for extract_energy_usage_costs."""

    def test_extracts_energy_costs_successfully(self) -> None:
        """Successfully extracts energy costs from valid response."""
        response = GraphQLResponse(
            data={
                "energyUsageCosts": {
                    "nodes": [
                        {
                            "date": "2024-01-15",
                            "fuelType": "ELECTRIC",
                            "amount": 125.50,
                            "month": "January",
                        },
                        {
                            "date": "2024-02-15",
                            "fuelType": "ELECTRIC",
                            "amount": 98.75,
                            "month": "February",
                        },
                    ]
                }
            }
        )

        costs = extract_energy_usage_costs(response)

        assert len(costs) == 2
        assert costs[0]["date"] == "2024-01-15"
        assert costs[0]["amount"] == 125.50
        assert costs[1]["amount"] == 98.75

    def test_returns_empty_list_for_no_costs(self) -> None:
        """Returns empty list when no costs exist."""
        response = GraphQLResponse(data={"energyUsageCosts": {"nodes": []}})

        costs = extract_energy_usage_costs(response)

        assert costs == []

    def test_raises_on_null_data(self) -> None:
        """Raises DataExtractionError when data is null."""
        response = GraphQLResponse(data=None)

        with pytest.raises(DataExtractionError, match="Response data is null"):
            extract_energy_usage_costs(response)

    def test_raises_on_missing_energy_usage_costs(self) -> None:
        """Raises DataExtractionError when energyUsageCosts is missing."""
        response = GraphQLResponse(data={"other": "value"})

        with pytest.raises(DataExtractionError, match="Missing 'energyUsageCosts' field"):
            extract_energy_usage_costs(response)

    def test_raises_on_missing_nodes(self) -> None:
        """Raises DataExtractionError when nodes is missing."""
        response = GraphQLResponse(data={"energyUsageCosts": {}})

        with pytest.raises(DataExtractionError, match="Missing 'nodes' field"):
            extract_energy_usage_costs(response)


class TestExtractEnergyUsages:
    """Tests for extract_energy_usages."""

    def test_extracts_energy_usages_successfully(self) -> None:
        """Successfully extracts energy usages from valid response."""
        response = GraphQLResponse(
            data={
                "energyUsages": {
                    "nodes": [
                        {"usage": 450.5, "usageType": "ACTUAL", "usageYearMonth": 202401},
                        {"usage": 380.2, "usageType": "ACTUAL", "usageYearMonth": 202402},
                    ]
                }
            }
        )

        usages = extract_energy_usages(response)

        assert len(usages) == 2
        assert usages[0]["usage"] == 450.5
        assert usages[0]["usageYearMonth"] == 202401
        assert usages[1]["usage"] == 380.2

    def test_returns_empty_list_for_no_usages(self) -> None:
        """Returns empty list when no usages exist."""
        response = GraphQLResponse(data={"energyUsages": {"nodes": []}})

        usages = extract_energy_usages(response)

        assert usages == []

    def test_raises_on_null_data(self) -> None:
        """Raises DataExtractionError when data is null."""
        response = GraphQLResponse(data=None)

        with pytest.raises(DataExtractionError, match="Response data is null"):
            extract_energy_usages(response)

    def test_raises_on_missing_energy_usages(self) -> None:
        """Raises DataExtractionError when energyUsages is missing."""
        response = GraphQLResponse(data={"other": "value"})

        with pytest.raises(DataExtractionError, match="Missing 'energyUsages' field"):
            extract_energy_usages(response)

    def test_raises_on_missing_nodes(self) -> None:
        """Raises DataExtractionError when nodes is missing."""
        response = GraphQLResponse(data={"energyUsages": {}})

        with pytest.raises(DataExtractionError, match="Missing 'nodes' field"):
            extract_energy_usages(response)


class TestDataExtractionErrorAttributes:
    """Tests for DataExtractionError attributes."""

    def test_error_contains_path(self) -> None:
        """Verify error stores the path that failed."""
        response = GraphQLResponse(data={"user": {}})

        with pytest.raises(DataExtractionError) as exc_info:
            extract_linked_accounts(response)

        assert exc_info.value.path == "data.user.accountLinks"

    def test_error_contains_response_data(self) -> None:
        """Verify error stores the response data."""
        data = {"user": {"other": "value"}}
        response = GraphQLResponse(data=data)

        with pytest.raises(DataExtractionError) as exc_info:
            extract_linked_accounts(response)

        assert exc_info.value.response_data == data

    def test_error_str_includes_path(self) -> None:
        """Verify error string representation includes path."""
        response = GraphQLResponse(data={"user": {}})

        with pytest.raises(DataExtractionError) as exc_info:
            extract_linked_accounts(response)

        error_str = str(exc_info.value)
        assert "Path: data.user.accountLinks" in error_str
