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
            accounts = await client.get_linked_accounts()

            if not accounts:
                print("No linked billing accounts found.")
                return

            account_number = accounts[0]["billingAccountId"]
            print(f"Using account: {account_number}")
            print()

            # Fetch billing account info to get the region (used as companyCode)
            print("Fetching billing account info...")
            billing_account = await client.get_billing_account(account_number)
            region = billing_account.get("region")
            print(f"Account region: {region}")
            print()

            # Fetch energy usage costs for the current month
            print("Fetching energy usage costs...")
            today = date.today()
            costs = await client.get_energy_usage_costs(account_number, today, region)

            print("Energy Usage Costs:")
            pretty_print(costs)
            print()

            # Fetch historical energy usages (last 12 months)
            print("Fetching historical energy usages...")
            # usageYearMonth is an integer in YYYYMM format
            from_month = (today.year - 1) * 100 + today.month
            usages = await client.get_energy_usages(account_number, from_month, first=12)

            print("Historical Energy Usages:")
            pretty_print(usages)


if __name__ == "__main__":
    asyncio.run(main())
