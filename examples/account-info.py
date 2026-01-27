"""Example that fetches billing account information for the primary account."""

from __future__ import annotations

import argparse
import asyncio
import json

import aiohttp

from aionatgrid import NationalGridClient, NationalGridConfig
from aionatgrid.helpers import create_cookie_jar


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch billing account information")
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
            # First, get linked billing accounts
            print("Fetching linked billing accounts...")
            accounts = await client.get_linked_accounts()

            if not accounts:
                print("No linked billing accounts found.")
                return

            # Use the first (primary) billing account
            billing_account_id = accounts[0]["billingAccountId"]
            print(f"Found {len(accounts)} linked account(s).")
            print(f"Primary billing account ID: {billing_account_id}")
            print()

            # Now fetch detailed information for the primary account
            print("Fetching billing account information...")
            billing_account = await client.get_billing_account(billing_account_id)

            print("Billing Account Information:")
            pretty_print(billing_account)


if __name__ == "__main__":
    asyncio.run(main())
