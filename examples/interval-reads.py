import asyncio

from aionatgrid import NationalGridClient, NationalGridConfig


async def main() -> None:
    config = NationalGridConfig.from_env()
    async with NationalGridClient(config=config) as client:
        response = await client.request_rest("GET", "/amiadapter-cu-uwp-sys/v1/interval/reads/{ACCOUNT}/{METER}", params={"StartDateTime": "{YYYY}-{MM}-{DD} {TIME}"})
        print(response.status, response.data)

if __name__ == "__main__":
    asyncio.run(main())