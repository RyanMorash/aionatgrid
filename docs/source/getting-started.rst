Getting Started
===============

Requirements
------------

- Python 3.10+
- A National Grid online account (username and password)

Installation
------------

Install from source using `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: bash

   uv add aionatgrid

Or with pip:

.. code-block:: bash

   pip install aionatgrid

Quick Example
-------------

.. code-block:: python

   import asyncio
   import aiohttp
   from aionatgrid import NationalGridClient, NationalGridConfig
   from aionatgrid.helpers import create_cookie_jar

   async def main():
       config = NationalGridConfig(
           username="user@example.com",
           password="secret",
       )
       cookie_jar = create_cookie_jar()
       async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
           async with NationalGridClient(config=config, session=session) as client:
               accounts = await client.get_linked_accounts()
               for account in accounts:
                   print(account["billingAccountId"])

   asyncio.run(main())

The client authenticates automatically on the first API call and caches the
access token, refreshing it before expiration.
