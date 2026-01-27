aionatgrid
==========

Async Python client for the National Grid API, built on `aiohttp <https://docs.aiohttp.org/>`_.

**Features:**

- Async/await interface using ``aiohttp``
- Automatic OIDC authentication via Azure AD B2C
- Token caching with automatic refresh before expiration
- GraphQL and REST endpoint support
- Typed response models with extraction helpers
- Configurable retry with exponential backoff
- Connection pooling and session reuse

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   usage
   api
   exceptions
