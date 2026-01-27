import argparse
import asyncio

import aiohttp

from aionatgrid import NationalGridClient, NationalGridConfig
from aionatgrid.helpers import create_cookie_jar


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch interval reads")
    parser.add_argument("--username", required=True, help="National Grid username")
    parser.add_argument("--password", required=True, help="National Grid password")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    config = NationalGridConfig(username=args.username, password=args.password)
    cookie_jar = create_cookie_jar()
    async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
        async with NationalGridClient(config=config, session=session) as client:
            response = await client.request_rest(
                "GET",
                "/amiadapter-cu-uwp-sys/v1/interval/reads/{ACCOUNT}/{METER}",
                params={"StartDateTime": "{YYYY}-{MM}-{DD} {TIME}"},
            )
            print(response.status, response.data)


if __name__ == "__main__":
    asyncio.run(main())
