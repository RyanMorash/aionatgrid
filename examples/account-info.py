"""Example that fetches billing account information for the primary account."""

from __future__ import annotations

import asyncio
import json

from aionatgrid import NationalGridClient, NationalGridConfig


def pretty_print(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


async def main() -> None:
    config = NationalGridConfig.from_env()

    async with NationalGridClient(config=config) as client:
        # First, get linked billing accounts
        print("Fetching linked billing accounts...")
        accounts_response = await client.linked_billing_accounts()

        if accounts_response.errors:
            print("Error fetching linked accounts:")
            pretty_print(accounts_response.errors)
            return

        # Extract the account links from the response
        data = accounts_response.data or {}
        account_links = data.get("user", {}).get("accountLinks", {}).get("nodes", [])

        if not account_links:
            print("No linked billing accounts found.")
            return

        # Use the first (primary) billing account
        primary_account = account_links[0]
        billing_account_id = primary_account.get("billingAccountId")

        print(f"Found {len(account_links)} linked account(s).")
        print(f"Primary billing account ID: {billing_account_id}")
        print()

        # Now fetch detailed information for the primary account
        print("Fetching billing account information...")
        info_response = await client.billing_account_info(
            variables={"accountNumber": billing_account_id}
        )

        if info_response.errors:
            print("Error fetching account info:")
            pretty_print(info_response.errors)
            return

        print("Billing Account Information:")
        pretty_print(info_response.data)


if __name__ == "__main__":
    asyncio.run(main())
