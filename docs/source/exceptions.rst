Exceptions
==========

All API-related exceptions inherit from :class:`~aionatgrid.NationalGridError`.

Exception Hierarchy
-------------------

.. code-block:: text

   Exception
   ├── CannotConnectError
   ├── InvalidAuthError
   └── NationalGridError
       ├── GraphQLError
       ├── RestAPIError
       ├── RetryExhaustedError
       └── DataExtractionError

Reference
---------

.. autoclass:: aionatgrid.NationalGridError
   :members:

.. autoclass:: aionatgrid.GraphQLError
   :members:
   :undoc-members:

.. autoclass:: aionatgrid.RestAPIError
   :members:
   :undoc-members:

.. autoclass:: aionatgrid.RetryExhaustedError
   :members:
   :undoc-members:

.. autoclass:: aionatgrid.DataExtractionError
   :members:
   :undoc-members:

.. autoclass:: aionatgrid.CannotConnectError
   :members:

.. autoclass:: aionatgrid.InvalidAuthError
   :members:
