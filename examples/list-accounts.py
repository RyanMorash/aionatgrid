import argparse
import asyncio

import aiohttp

from aionatgrid import NationalGridClient, NationalGridConfig
from aionatgrid.helpers import create_cookie_jar


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List linked billing accounts")
    parser.add_argument("--username", required=True, help="National Grid username")
    parser.add_argument("--password", required=True, help="National Grid password")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    config = NationalGridConfig(username=args.username, password=args.password)
    cookie_jar = create_cookie_jar()
    async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
        async with NationalGridClient(config=config, session=session) as client:
            accounts = await client.get_linked_accounts()
            print(f"Found {len(accounts)} linked billing account(s):")
            for account in accounts:
                print(f"  - {account['billingAccountId']}")


if __name__ == "__main__":
    asyncio.run(main())
