import os
from urllib.parse import urljoin

import httpx
import pytest


@pytest.fixture(scope="session")
def arnica_base_url() -> str:
    """Provides the Arnica base URL for integration tests."""
    return _get_env_var("ARNICA_SANDBOX_BASE_URL")


@pytest.fixture(scope="session")
def auth_token() -> str:
    """Provides a valid Auth0 token for integration tests."""
    client_id = _get_env_var("ARNICA_CLIENT_ID")
    client_secret = _get_env_var("ARNICA_CLIENT_SECRET")
    tenant_url = _get_env_var("ARNICA_AUTH_TENANT_URL")
    audience = _get_env_var("ARNICA_SANDBOX_BASE_URL")

    token_request_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials",
    }
    http_client = httpx.Client()
    token_response = http_client.post(urljoin(tenant_url, "/oauth/token"), json=token_request_payload)
    token_response.raise_for_status()
    token_data = token_response.json()
    return token_data["access_token"]


def _get_env_var(name: str) -> str:
    """Get environment variable or raise an assertion error if not set."""
    value = os.getenv(name)
    assert value is not None, f"{name} must be set in environment variables"
    return value
