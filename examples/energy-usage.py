"""Example that fetches energy usage costs and historical usage data."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date

import aiohttp

from aionatgrid import NationalGridClient, NationalGridConfig
from aionatgrid.helpers import create_cookie_jar


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch energy usage costs and historical data")
    parser.add_argument("--username", required=True, help="National Grid username")
    parser.add_argument("--password", required=True, help="National Grid password")
    return parser.parse_args()


def pretty_print(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


async def main() -> None:
    args = parse_args()
    config = NationalGridConfig(username=args.username, password=args.password)

    cookie_jar = create_cookie_jar()
    async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
        async with NationalGridClient(config=config, session=session) as client:
            # First, get linked billing accounts to obtain an account number
            print("Fetching linked billing accounts...")
            accounts_response = await client.linked_billing_accounts()

            if accounts_response.errors:
                print("Error fetching linked accounts:")
                pretty_print(accounts_response.errors)
                return

            data = accounts_response.data or {}
            account_links = (
                data.get("user", {}).get("accountLinks", {}).get("nodes", [])
            )

            if not account_links:
                print("No linked billing accounts found.")
                return

            primary_account = account_links[0]
            account_number = primary_account.get("billingAccountId")

            if not account_number:
                print("Primary account is missing billingAccountId.")
                return

            print(f"Using account: {account_number}")
            print()

            # Fetch billing account info to get the region (used as companyCode)
            print("Fetching billing account info...")
            info_response = await client.billing_account_info(
                variables={"accountNumber": account_number}
            )

            if info_response.errors:
                print("Error fetching billing account info:")
                pretty_print(info_response.errors)
                return

            billing_account = (info_response.data or {}).get("billingAccount", {})
            region = billing_account.get("region")
            print(f"Account region: {region}")
            print()

            # Fetch energy usage costs for the current month
            print("Fetching energy usage costs...")
            today = date.today()
            costs_response = await client.energy_usage_costs(
                variables={
                    "accountNumber": account_number,
                    "date": today.isoformat(),
                    "companyCode": region,
                }
            )

            if costs_response.errors:
                print("Error fetching energy usage costs:")
                pretty_print(costs_response.errors)
            else:
                print("Energy Usage Costs:")
                pretty_print(costs_response.data)
            print()

            # Fetch historical energy usages (last 12 months)
            print("Fetching historical energy usages...")
            # usageYearMonth is an integer in YYYYMM format
            from_month = (today.year - 1) * 100 + today.month
            usages_response = await client.energy_usages(
                variables={
                    "accountNumber": account_number,
                    "from": from_month,
                    "first": 12,
                }
            )

            if usages_response.errors:
                print("Error fetching energy usages:")
                pretty_print(usages_response.errors)
            else:
                print("Historical Energy Usages:")
                pretty_print(usages_response.data)


if __name__ == "__main__":
    asyncio.run(main())
