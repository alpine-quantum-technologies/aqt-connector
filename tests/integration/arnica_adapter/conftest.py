import os
from collections.abc import Callable, Generator
from urllib.parse import urljoin

import httpx
import pytest

from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter

ResponseHandler = Callable[[httpx.Request], httpx.Response]
ArnicaAdapterFactory = Callable[[ResponseHandler], ArnicaAdapter]
SIMULATED_BASE_URL = "https://arnica.example.com"


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
    with httpx.Client() as http_client:
        token_response = http_client.post(urljoin(tenant_url, "/oauth/token"), json=token_request_payload)
        token_response.raise_for_status()
        token_data = token_response.json()
    return token_data["access_token"]


@pytest.fixture
def arnica_adapter(arnica_base_url: str) -> Generator[ArnicaAdapter, None, None]:
    """Provides a live Arnica adapter and closes its client after each test."""
    adapter = ArnicaAdapter(base_url=arnica_base_url)
    try:
        yield adapter
    finally:
        adapter.close()


@pytest.fixture
def make_arnica_adapter() -> Generator[ArnicaAdapterFactory, None, None]:
    """Provides mock-transport Arnica adapters and closes them after each test."""
    adapters: list[ArnicaAdapter] = []

    def _factory(handler: ResponseHandler) -> ArnicaAdapter:
        adapter = ArnicaAdapter(
            base_url=SIMULATED_BASE_URL,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        adapters.append(adapter)
        return adapter

    try:
        yield _factory
    finally:
        for adapter in adapters:
            adapter.close()


def _get_env_var(name: str) -> str:
    """Get environment variable or raise an assertion error if not set."""
    value = os.getenv(name)
    assert value is not None, f"{name} must be set in environment variables"
    return value
