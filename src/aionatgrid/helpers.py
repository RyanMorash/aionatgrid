"""Helper functions."""

import aiohttp


def create_cookie_jar() -> aiohttp.CookieJar:
    """Create a cookie jar configured for Azure AD B2C authentication.

    Azure AD B2C requires cookies without quoting. Use this function when
    providing your own aiohttp.ClientSession to NationalGridClient.

    Example::

        from aionatgrid import NationalGridClient, NationalGridConfig, create_cookie_jar

        cookie_jar = create_cookie_jar()
        async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
            client = NationalGridClient(config=config, session=session)
            accounts = await client.get_linked_accounts()

    Returns:
        An aiohttp.CookieJar with quote_cookie=False for Azure AD B2C compatibility.
    """
    return aiohttp.CookieJar(quote_cookie=False)
