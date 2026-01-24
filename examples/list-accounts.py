import asyncio

from aionatgrid import NationalGridClient, NationalGridConfig


async def main() -> None:
    config = NationalGridConfig.from_env()
    async with NationalGridClient(config=config) as client:
        response = await client.linked_billing_accounts()
        print("Linked Billing Accounts Response:")
        print(response.data)


if __name__ == "__main__":
    asyncio.run(main())
