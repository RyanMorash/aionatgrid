"""Runnable example that fetches current system frequency."""

from __future__ import annotations

import asyncio
import json

from aionatgrid import GraphQLRequest, NationalGridClient, NationalGridConfig

QUERY = """
query CurrentFrequency {
  currentFrequency {
    timestamp
    value
    units
  }
}
"""


def pretty_print(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


async def main() -> None:
    config = NationalGridConfig.from_env()
    request = GraphQLRequest(query=QUERY)

    async with NationalGridClient(config=config) as client:
        response = await client.execute(request)

    if response.errors:
        print("GraphQL errors encountered:")
        pretty_print(response.errors)
        return

    pretty_print(response.data)


if __name__ == "__main__":
    asyncio.run(main())
