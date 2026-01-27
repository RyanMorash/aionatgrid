import asyncio

import aiohttp

from aionatgrid import NationalGridClient, NationalGridConfig
from aionatgrid.helpers import create_cookie_jar


async def main() -> None:
    config = NationalGridConfig.from_env()
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
