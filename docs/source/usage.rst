Usage Guide
===========

All examples below assume you have created a client as shown in
:doc:`getting-started`.

Listing Linked Accounts
-----------------------

Retrieve the billing accounts linked to your National Grid login:

.. code-block:: python

   accounts = await client.get_linked_accounts()
   for account in accounts:
       print(account["billingAccountId"])

Each item is an :class:`~aionatgrid.models.AccountLink` TypedDict.

Billing Account Details
-----------------------

Get detailed information for a specific account:

.. code-block:: python

   account = await client.get_billing_account("1234567890")
   print(account["region"])          # e.g. "NECO"
   print(account["premiseNumber"])
   print(account["meter"]["nodes"])  # list of meters

Returns a :class:`~aionatgrid.models.BillingAccount` TypedDict.

Energy Usage Costs
------------------

Fetch energy usage costs for a billing period:

.. code-block:: python

   from datetime import date

   costs = await client.get_energy_usage_costs(
       account_number="1234567890",
       query_date=date.today(),
       company_code="NECO",  # use the region from billing account info
   )
   for cost in costs:
       print(cost)

The ``company_code`` parameter corresponds to the ``region`` field from
:meth:`~aionatgrid.NationalGridClient.get_billing_account`.

Historical Energy Usages
------------------------

Retrieve monthly energy usage history:

.. code-block:: python

   # from_month is YYYYMM integer format
   usages = await client.get_energy_usages(
       account_number="1234567890",
       from_month=202401,
       first=12,  # number of months
   )
   for usage in usages:
       print(usage)

Interval Reads (Smart Meters)
-----------------------------

For accounts with AMI smart meters, you can fetch granular interval reads:

.. code-block:: python

   from datetime import datetime, timedelta

   # Get the last 24 hours of reads
   reads = await client.get_interval_reads(
       premise_number="12345",
       service_point_number="67890",
       start_datetime=datetime.now() - timedelta(hours=24),
   )
   for read in reads:
       print(read)

.. note::

   Interval reads require an AMI smart meter. Check
   ``meter["hasAmiSmartMeter"]`` from the billing account info response.

Configuration
-------------

Customize client behavior via :class:`~aionatgrid.NationalGridConfig`:

.. code-block:: python

   from aionatgrid import NationalGridConfig, RetryConfig

   config = NationalGridConfig(
       username="user@example.com",
       password="secret",
       timeout=60.0,
       retry_config=RetryConfig(
           max_attempts=5,
           initial_delay=2.0,
       ),
   )

See :class:`~aionatgrid.RetryConfig` for all retry options.

Error Handling
--------------

The client raises specific exceptions for different failure modes:

.. code-block:: python

   from aionatgrid import (
       GraphQLError,
       RestAPIError,
       DataExtractionError,
       RetryExhaustedError,
       InvalidAuthError,
   )

   try:
       accounts = await client.get_linked_accounts()
   except InvalidAuthError:
       print("Bad credentials")
   except GraphQLError as err:
       print(f"GraphQL failed: {err.endpoint}, status={err.status}")
   except RetryExhaustedError as err:
       print(f"Gave up after {err.attempts} attempts")

See :doc:`exceptions` for the full hierarchy.
