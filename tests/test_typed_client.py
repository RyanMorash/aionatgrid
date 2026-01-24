"""Tests for typed convenience methods on NationalGridClient."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import aiohttp
import pytest

from aionatgrid.client import NationalGridClient
from aionatgrid.config import NationalGridConfig
from aionatgrid.exceptions import DataExtractionError


class _DummyResponse:
    """Mock response for GraphQL requests."""

    def __init__(self, payload: dict[str, object]):
        self._payload = payload

    async def __aenter__(self) -> _DummyResponse:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:  # type: ignore[override]
        return False

    async def json(self, content_type: str | None = None) -> dict[str, object]:
        return self._payload

    def raise_for_status(self) -> None:
        return None


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp session."""
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False
    return session


@pytest.fixture
def config() -> NationalGridConfig:
    """Create a test configuration."""
    return NationalGridConfig(endpoint="https://example.test/graphql")


@pytest.mark.asyncio
async def test_get_linked_accounts_returns_typed_list(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify get_linked_accounts returns a properly typed list."""
    mock_session.post.return_value = _DummyResponse(
        {
            "data": {
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
        }
    )

    client = NationalGridClient(config=config, session=mock_session)
    accounts = await client.get_linked_accounts()

    assert len(accounts) == 2
    assert accounts[0]["accountLinkId"] == "link-1"
    assert accounts[0]["billingAccountId"] == "acct-001"
    assert accounts[1]["billingAccountId"] == "acct-002"


@pytest.mark.asyncio
async def test_get_billing_account_returns_typed_dict(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify get_billing_account returns a properly typed dict."""
    mock_session.post.return_value = _DummyResponse(
        {
            "data": {
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
        }
    )

    client = NationalGridClient(config=config, session=mock_session)
    account = await client.get_billing_account("acct-001")

    assert account["region"] == "Massachusetts"
    assert account["regionAbbreviation"] == "MA"
    assert account["status"] == "ACTIVE"
    assert account["premiseNumber"] == "PREM-001"
    assert account["meter"]["nodes"][0]["isSmartMeter"] is True


@pytest.mark.asyncio
async def test_get_billing_account_passes_account_number(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify get_billing_account passes the account number as a variable."""
    mock_session.post.return_value = _DummyResponse(
        {
            "data": {
                "billingAccount": {
                    "region": "MA",
                    "regionAbbreviation": "MA",
                    "type": "RESIDENTIAL",
                    "fuelTypes": [],
                    "status": "ACTIVE",
                    "serviceAddress": {"serviceAddressCompressed": "123 Main"},
                    "customerInfo": {"customerType": "RES"},
                    "customerNumber": "C001",
                    "premiseNumber": "P001",
                    "meter": {"nodes": []},
                }
            }
        }
    )

    client = NationalGridClient(config=config, session=mock_session)
    await client.get_billing_account("my-account-123")

    _, kwargs = mock_session.post.call_args
    payload = kwargs["json"]
    assert payload["variables"]["accountNumber"] == "my-account-123"


@pytest.mark.asyncio
async def test_get_energy_usage_costs_accepts_date_object(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify get_energy_usage_costs accepts a date object."""
    mock_session.post.return_value = _DummyResponse(
        {
            "data": {
                "energyUsageCosts": {
                    "nodes": [
                        {
                            "date": "2024-01-15",
                            "fuelType": "ELECTRIC",
                            "amount": 125.50,
                            "month": "January",
                        }
                    ]
                }
            }
        }
    )

    client = NationalGridClient(config=config, session=mock_session)
    costs = await client.get_energy_usage_costs(
        "acct-001",
        date(2024, 1, 15),
        "NECO",
    )

    assert len(costs) == 1
    assert costs[0]["amount"] == 125.50

    # Verify date was converted to ISO string
    _, kwargs = mock_session.post.call_args
    payload = kwargs["json"]
    assert payload["variables"]["date"] == "2024-01-15"


@pytest.mark.asyncio
async def test_get_energy_usage_costs_accepts_string_date(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify get_energy_usage_costs accepts a string date."""
    mock_session.post.return_value = _DummyResponse(
        {
            "data": {
                "energyUsageCosts": {
                    "nodes": [
                        {
                            "date": "2024-02-20",
                            "fuelType": "ELECTRIC",
                            "amount": 98.75,
                            "month": "February",
                        }
                    ]
                }
            }
        }
    )

    client = NationalGridClient(config=config, session=mock_session)
    costs = await client.get_energy_usage_costs(
        "acct-001",
        "2024-02-20",
        "KEDNE",
    )

    assert len(costs) == 1
    _, kwargs = mock_session.post.call_args
    payload = kwargs["json"]
    assert payload["variables"]["date"] == "2024-02-20"
    assert payload["variables"]["companyCode"] == "KEDNE"


@pytest.mark.asyncio
async def test_get_energy_usages_returns_typed_list(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify get_energy_usages returns a properly typed list."""
    mock_session.post.return_value = _DummyResponse(
        {
            "data": {
                "energyUsages": {
                    "nodes": [
                        {"usage": 450.5, "usageType": "ACTUAL", "usageYearMonth": 202401},
                        {"usage": 380.2, "usageType": "ACTUAL", "usageYearMonth": 202402},
                    ]
                }
            }
        }
    )

    client = NationalGridClient(config=config, session=mock_session)
    usages = await client.get_energy_usages("acct-001", 202401)

    assert len(usages) == 2
    assert usages[0]["usage"] == 450.5
    assert usages[0]["usageYearMonth"] == 202401


@pytest.mark.asyncio
async def test_get_energy_usages_passes_variables(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify get_energy_usages passes the correct variables."""
    mock_session.post.return_value = _DummyResponse(
        {"data": {"energyUsages": {"nodes": []}}}
    )

    client = NationalGridClient(config=config, session=mock_session)
    await client.get_energy_usages("acct-001", 202301, first=24)

    _, kwargs = mock_session.post.call_args
    payload = kwargs["json"]
    assert payload["variables"]["accountNumber"] == "acct-001"
    assert payload["variables"]["from"] == 202301
    assert payload["variables"]["first"] == 24


@pytest.mark.asyncio
async def test_typed_method_raises_on_graphql_errors(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify typed methods raise ValueError on GraphQL errors."""
    mock_session.post.return_value = _DummyResponse(
        {
            "data": None,
            "errors": [
                {"message": "Unauthorized", "extensions": {"code": "UNAUTHENTICATED"}}
            ],
        }
    )

    client = NationalGridClient(config=config, session=mock_session)

    with pytest.raises(ValueError, match="GraphQL errors encountered"):
        await client.get_linked_accounts()


@pytest.mark.asyncio
async def test_typed_method_raises_data_extraction_error(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify typed methods raise DataExtractionError on missing data."""
    mock_session.post.return_value = _DummyResponse(
        {"data": {"user": {}}}  # Missing accountLinks
    )

    client = NationalGridClient(config=config, session=mock_session)

    with pytest.raises(DataExtractionError, match="Missing 'accountLinks' field"):
        await client.get_linked_accounts()


@pytest.mark.asyncio
async def test_get_linked_accounts_returns_empty_list(
    mock_session: MagicMock, config: NationalGridConfig
) -> None:
    """Verify get_linked_accounts handles empty account list."""
    mock_session.post.return_value = _DummyResponse(
        {
            "data": {
                "user": {
                    "accountLinks": {
                        "totalCount": 0,
                        "nodes": [],
                    }
                }
            }
        }
    )

    client = NationalGridClient(config=config, session=mock_session)
    accounts = await client.get_linked_accounts()

    assert accounts == []
