API Reference
=============

Client
------

.. autoclass:: aionatgrid.NationalGridClient
   :members:
   :undoc-members:

Configuration
-------------

.. autoclass:: aionatgrid.NationalGridConfig
   :members:
   :undoc-members:

.. autoclass:: aionatgrid.RetryConfig
   :members:
   :undoc-members:

GraphQL Types
-------------

.. autoclass:: aionatgrid.GraphQLRequest
   :members:

.. autoclass:: aionatgrid.GraphQLResponse
   :members:

REST Types
----------

.. autoclass:: aionatgrid.RestRequest
   :members:

.. autoclass:: aionatgrid.RestResponse
   :members:

.. autoclass:: aionatgrid.RealtimeMeterInfo
   :members:

Query Builders
--------------

.. autoclass:: aionatgrid.StandardQuery
   :members:

.. autofunction:: aionatgrid.linked_billing_accounts_request

.. autofunction:: aionatgrid.billing_account_info_request

.. autofunction:: aionatgrid.energy_usage_costs_request

.. autofunction:: aionatgrid.energy_usages_request

.. autofunction:: aionatgrid.ami_energy_usages_request

.. autofunction:: aionatgrid.realtime_meter_info_request

Response Models
---------------

.. autoclass:: aionatgrid.AccountLink

.. autoclass:: aionatgrid.AccountLinksConnection

.. autoclass:: aionatgrid.BillingAccount

.. autoclass:: aionatgrid.CustomerInfo

.. autoclass:: aionatgrid.ServiceAddress

.. autoclass:: aionatgrid.Meter

.. autoclass:: aionatgrid.MeterConnection

.. autoclass:: aionatgrid.FuelType

.. autoclass:: aionatgrid.EnergyUsageCost

.. autoclass:: aionatgrid.EnergyUsageCostsConnection

.. autoclass:: aionatgrid.EnergyUsage

.. autoclass:: aionatgrid.EnergyUsagesConnection

.. autoclass:: aionatgrid.IntervalRead

Extraction Helpers
------------------

.. autofunction:: aionatgrid.extract_linked_accounts

.. autofunction:: aionatgrid.extract_billing_account

.. autofunction:: aionatgrid.extract_energy_usage_costs

.. autofunction:: aionatgrid.extract_energy_usages

.. autofunction:: aionatgrid.extract_interval_reads

Utilities
---------

.. autofunction:: aionatgrid.create_cookie_jar

.. autoclass:: aionatgrid.LoginData
