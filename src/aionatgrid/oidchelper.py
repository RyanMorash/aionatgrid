"""OIDC Login Helper and its constituent functions."""

import base64
import hashlib
import json
import logging
import re
import secrets
from typing import Any, TypedDict
from urllib.parse import parse_qs, urlparse

import aiohttp
import jwt
from jwt import PyJWKClient

from .exceptions import CannotConnectError, InvalidAuthError

_LOGGER = logging.getLogger(__name__)


async def async_auth_oidc(
    session: aiohttp.ClientSession,
    username: str,
    password: str,
    base_url: str,
    tenant_id: str,
    policy: str,
    client_id: str,
    redirect_uri: str,
    scope_auth: str,
    scope_access: str,
    self_asserted_endpoint: str,
    policy_confirm_endpoint: str,
    login_data: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> tuple[str, int] | tuple[None, None]:
    """Perform the login process and return an access token with expiry time.

    Args:
        timeout: Request timeout in seconds for authentication requests (default: 30.0)

    Returns:
        Tuple of (access_token, expires_in_seconds) on success, (None, None) on failure.
    """
    try:
        code_verifier = _generate_code_verifier()
        code_challenge = _generate_code_challenge(code_verifier)
        _LOGGER.debug("Generated PKCE code verifier and challenge")
        config = await _get_config(session, base_url, tenant_id, policy, timeout=timeout)
        _LOGGER.debug("Retrieved OAuth configuration")
        auth_code, sub_value = await _get_auth(
            session,
            config,
            code_challenge,
            username,
            password,
            client_id,
            redirect_uri,
            scope_auth,
            policy,
            self_asserted_endpoint,
            policy_confirm_endpoint,
            timeout,
        )
        if sub_value and login_data is not None:
            login_data["sub"] = sub_value
        if auth_code is None:
            _LOGGER.error("Failed to obtain authorization code")
            raise CannotConnectError("Failed to obtain authorization code")
        _LOGGER.debug("Obtained authorization code")

        tokens = await _get_access(
            session,
            config,
            auth_code,
            code_verifier,
            client_id,
            redirect_uri,
            scope_access,
            timeout,
        )

        if tokens and "access_token" in tokens:
            _LOGGER.debug("Successfully obtained access token")
            # Default to 3600 seconds (1 hour) if not provided
            expires_in = tokens.get("expires_in", 3600)
            return tokens["access_token"], expires_in
        _LOGGER.error("Failed to obtain access token")
        raise CannotConnectError("Failed to obtain access token")

    except aiohttp.ClientError as err:
        _LOGGER.exception("Connection error during login")
        raise CannotConnectError(f"Connection error: {err}") from err


class ConfigDict(TypedDict):
    """Dictionary to store configuration details for OAuth."""

    authorization_endpoint: str
    issuer: str
    token_endpoint: str
    jwks_uri: str


class TokenDict(TypedDict, total=False):
    """Dictionary to store OAuth tokens."""

    access_token: str
    expires_in: int  # Token lifetime in seconds


def _generate_code_verifier() -> str:
    """Generate a code verifier for PKCE."""
    return secrets.token_urlsafe(32)


def _generate_code_challenge(code_verifier: str) -> str:
    """Generate a code challenge for PKCE."""
    code_challenge_digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(code_challenge_digest).decode("utf-8").rstrip("=")


async def _get_config(
    session: aiohttp.ClientSession, base_url: str, tenant_id: str, policy: str, timeout: float
) -> ConfigDict:
    """Get the configuration from the server."""
    config_url = f"{base_url}/{tenant_id}/{policy}/v2.0/.well-known/openid-configuration"
    _LOGGER.debug("Fetching OAuth configuration from: %s", config_url)
    config_text, _, status = await _fetch(session, config_url, timeout)
    if status != 200 or not config_text:
        _LOGGER.error("Failed to get configuration. Status: %s", status)
        raise CannotConnectError("Failed to get configuration")
    config: ConfigDict = json.loads(config_text)
    return config


async def _get_auth(
    session: aiohttp.ClientSession,
    config: ConfigDict,
    code_challenge: str,
    username: str,
    password: str,
    client_id: str,
    redirect_uri: str,
    scope_auth: str,
    policy: str,
    self_asserted_endpoint: str,
    policy_confirm_endpoint: str,
    timeout: float,
) -> tuple[str | None, str | None]:
    """Get the authorization code."""
    auth_params = {
        "client_id": client_id,
        "response_type": "code id_token",
        "response_mode": "query",
        "nonce": secrets.token_urlsafe(16),
        "redirect_uri": redirect_uri,
        "scope": scope_auth,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    _LOGGER.debug("Requesting authorization code")
    auth_content, final_url, status = await _fetch(
        session, config["authorization_endpoint"], timeout, params=auth_params
    )
    if status != 200 or not auth_content:
        _LOGGER.error("Failed to get authorization. Status: %s", status)
        raise CannotConnectError("Failed to get authorization")

    settings = _extract_settings(auth_content)
    if not settings:
        _LOGGER.debug("No settings extracted, checking for direct authorization code")
        return _extract_auth_result(final_url, redirect_uri, config, client_id)

    _LOGGER.debug("Posting credentials")
    await _post_credentials(
        session,
        config["issuer"],
        settings,
        username,
        password,
        policy,
        self_asserted_endpoint,
        timeout,
    )
    _LOGGER.debug("Confirming sign-in")
    return await _confirm_signin(
        session,
        config["issuer"],
        settings,
        policy,
        policy_confirm_endpoint,
        redirect_uri,
        config,
        client_id,
        timeout,
    )


async def _get_access(
    session: aiohttp.ClientSession,
    config: ConfigDict,
    auth_code: str,
    code_verifier: str,
    client_id: str,
    redirect_uri: str,
    scope_access: str,
    timeout: float,
) -> TokenDict | None:
    """Get the access token."""
    token_data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
        "scope": scope_access,
    }
    _LOGGER.debug("Requesting access token")
    token_content, _, status = await _fetch(
        session, config["token_endpoint"], timeout, method="POST", data=token_data
    )
    if status != 200 or not token_content:
        _LOGGER.error("Failed to get access token. Status: %s", status)
        raise CannotConnectError("Failed to get access token")
    tokens: TokenDict = json.loads(token_content)
    return tokens


async def _fetch(
    session: aiohttp.ClientSession, url: str, timeout: float, **kwargs: Any
) -> tuple[str | None, str | None, int]:
    """Fetch data from a URL."""
    method = kwargs.pop("method", "GET")
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    try:
        _LOGGER.debug("Fetching URL: %s, Method: %s", url, method)
        async with session.request(method, url, timeout=timeout_obj, **kwargs) as response:
            content = await response.text()
            _LOGGER.debug("Fetch completed. Status: %s", response.status)
            return content, str(response.url), response.status
    except aiohttp.ClientError:
        _LOGGER.exception("Network error occurred")
        raise CannotConnectError("Network error occurred")


def _extract_settings(auth_content: str) -> dict[str, Any] | None:
    """Extract settings from the authorization content using multiple strategies."""
    _LOGGER.debug("Extracting settings from authorization content")

    # Strategy 1: String slicing (original method, fastest)
    settings_start = auth_content.find("var SETTINGS = ")
    if settings_start != -1:
        settings_end = auth_content.find(";", settings_start)
        if settings_end != -1:
            settings_json = auth_content[settings_start + 15 : settings_end].strip()
            try:
                settings: dict[str, Any] = json.loads(settings_json)
                _LOGGER.debug("Settings extracted via string slicing")
                return settings
            except json.JSONDecodeError:
                _LOGGER.warning("String slicing extracted invalid JSON, trying regex")

    # Strategy 2: Regex pattern matching (more robust fallback)
    # Matches: var SETTINGS = {...}; or var SETTINGS={...};
    pattern = r"var\s+SETTINGS\s*=\s*(\{[^;]+\})\s*;"
    match = re.search(pattern, auth_content)
    if match:
        settings_json = match.group(1).strip()
        try:
            settings = json.loads(settings_json)
            _LOGGER.debug("Settings extracted via regex")
            return settings
        except json.JSONDecodeError:
            _LOGGER.exception("Failed to parse settings JSON from regex match")

    _LOGGER.warning("Could not extract settings from authorization content")
    return None


async def _post_credentials(
    session: aiohttp.ClientSession,
    issuer: str,
    settings: dict[str, Any],
    username: str,
    password: str,
    policy: str,
    self_asserted_endpoint: str,
    timeout: float,
) -> None:
    """Post credentials to the server."""
    base_url = issuer.rsplit("/", 2)[0]
    _LOGGER.debug("Posting credentials to %s", base_url)
    _, _, status = await _fetch(
        session,
        f"{base_url}/{policy}/{self_asserted_endpoint}",
        timeout,
        method="POST",
        data={
            "tx": settings["transId"],
            "p": policy,
            "request_type": "RESPONSE",
            "signInName": username,
            "password": password,
        },
        headers={"X-CSRF-TOKEN": settings["csrf"]},
    )
    if status != 200:
        _LOGGER.error("Failed to post credentials. Status: %s", status)
        raise InvalidAuthError("Invalid username or password")
    _LOGGER.debug("Credentials posted successfully")


async def _confirm_signin(
    session: aiohttp.ClientSession,
    issuer: str,
    settings: dict[str, Any],
    policy: str,
    policy_confirm_endpoint: str,
    redirect_uri: str,
    config: ConfigDict,
    client_id: str,
    timeout: float,
) -> tuple[str | None, str | None]:
    """Confirm the sign-in process."""
    base_url = issuer.rsplit("/", 2)[0]
    _LOGGER.debug("Confirming sign-in at %s", base_url)
    _, final_url, status = await _fetch(
        session,
        f"{base_url}/{policy}/{policy_confirm_endpoint}",
        timeout,
        params={
            "rememberMe": "false",
            "csrf_token": settings["csrf"],
            "tx": settings["transId"],
            "p": policy,
        },
        allow_redirects=True,
    )
    if status != 200:
        _LOGGER.error("Failed to confirm signin. Status: %s", status)
        if status == 403:
            raise InvalidAuthError("Invalid username or password")
        raise CannotConnectError("Failed to confirm signin")
    if final_url:
        auth_code, sub_value = _extract_auth_result(final_url, redirect_uri, config, client_id)
        if auth_code:
            _LOGGER.debug("Sign-in confirmed, authorization code obtained")
        else:
            parsed_params = _parse_redirect_params(final_url)
            if "error" in parsed_params:
                _LOGGER.error(
                    "Sign-in failed with error: %s, %s",
                    parsed_params.get("error"),
                    parsed_params.get("error_description"),
                )
                raise InvalidAuthError("Sign-in failed")
            _LOGGER.warning("Sign-in confirmed, but no authorization code found")
        return auth_code, sub_value
    _LOGGER.warning("Sign-in confirmation did not result in a final URL")
    return None, None


def _extract_auth_result(
    final_url: str | None, redirect_uri: str, config: ConfigDict, client_id: str
) -> tuple[str | None, str | None]:
    if not final_url or not final_url.startswith(redirect_uri):
        return None, None
    parsed_params = _parse_redirect_params(final_url)
    auth_code = parsed_params.get("code", [None])[0]
    id_token = parsed_params.get("id_token", [None])[0]
    sub_value = _extract_sub_from_id_token(id_token, config, client_id) if id_token else None
    return auth_code, sub_value


def _parse_redirect_params(final_url: str) -> dict[str, list[str]]:
    parsed = urlparse(final_url)
    fragment = parsed.fragment
    query = parsed.query
    if fragment:
        return parse_qs(fragment)
    return parse_qs(query)


def _extract_sub_from_id_token(
    id_token: str | None, config: ConfigDict, client_id: str
) -> str | None:
    """Extract and verify the sub claim from an id_token with proper signature validation."""
    if not id_token:
        return None

    try:
        # Use PyJWKClient to fetch and cache the signing keys from the JWKS endpoint
        jwks_client = PyJWKClient(config["jwks_uri"])
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)

        # Verify the token signature and validate claims
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=config["issuer"],
            audience=client_id,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )

        sub_value = claims.get("sub")
        if sub_value:
            _LOGGER.debug("Extracted and verified sub from id_token")
            return str(sub_value)
        else:
            _LOGGER.warning("sub claim not found in verified id_token")
            return None

    except jwt.ExpiredSignatureError:
        _LOGGER.error("id_token has expired")
        return None
    except jwt.InvalidTokenError as e:
        _LOGGER.error("id_token validation failed: %s", e)
        return None
    except Exception as e:
        _LOGGER.exception("Unexpected error validating id_token: %s", e)
        return None
