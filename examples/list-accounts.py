import argparse
import asyncio

import aiohttp

from aionatgrid import NationalGridClient, NationalGridConfig
from aionatgrid.helpers import create_cookie_jar


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List linked billing accounts")
    parser.add_argument("--username", help="National Grid username (or set NATIONALGRID_USERNAME)")
    parser.add_argument("--password", help="National Grid password (or set NATIONALGRID_PASSWORD)")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    config = NationalGridConfig.from_env()
    if args.username or args.password:
        config = config.with_overrides(
            username=args.username or config.username,
            password=args.password or config.password,
        )
    cookie_jar = create_cookie_jar()
    async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
        async with NationalGridClient(config=config, session=session) as client:
            response = await client.linked_billing_accounts()
            print("Linked Billing Accounts Response:")
            print(response.data)


if __name__ == "__main__":
    asyncio.run(main())
