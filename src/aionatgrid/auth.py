"""Authentication helpers for the National Grid API."""

import logging
from typing import Any

import aiohttp

from .oidchelper import async_auth_oidc

_LOGGER = logging.getLogger(__name__)


class NationalGridAuth:
    """Base class for National Grid subsidiaries."""

    @staticmethod
    def timezone() -> str:
        """Return the timezone."""
        return "America/New_York"

    BASE_URL = "https://login.nationalgrid.com"
    TENANT_ID = "0e1366c5-731c-42b3-90d3-508039d9e70f"
    POLICY = "B2C_1A_UWP_NationalGrid_convert_merge_signin"
    CLIENT_ID = "36488660-e86a-4a0d-8316-3df49af8d06d"
    REDIRECT_URI = "https://myaccount.nationalgrid.com/auth-landing"
    APPLICATION_URI = f"{BASE_URL}/"
    SCOPE_AUTH = "openid profile offline_access"
    SCOPE_ACCESS = f"{CLIENT_ID} openid profile offline_access"
    SELF_ASSERTED_ENDPOINT = "SelfAsserted"
    POLICY_CONFIRM_ENDPOINT = "api/CombinedSigninAndSignup/confirmed"

    async def async_login(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        login_data: dict[str, Any],
    ) -> tuple[str, int] | tuple[None, None]:
        """Perform the login process and return an access token with expiry.

        Returns:
            Tuple of (access_token, expires_in_seconds) on success, (None, None) on failure.
        """
        _LOGGER.debug("Starting login process for National Grid")
        return await async_auth_oidc(
            session,
            username,
            password,
            NationalGridAuth.BASE_URL,
            NationalGridAuth.TENANT_ID,
            NationalGridAuth.POLICY,
            NationalGridAuth.CLIENT_ID,
            NationalGridAuth.REDIRECT_URI,
            NationalGridAuth.SCOPE_AUTH,
            NationalGridAuth.SCOPE_ACCESS,
            NationalGridAuth.SELF_ASSERTED_ENDPOINT,
            NationalGridAuth.POLICY_CONFIRM_ENDPOINT,
            login_data,
        )
