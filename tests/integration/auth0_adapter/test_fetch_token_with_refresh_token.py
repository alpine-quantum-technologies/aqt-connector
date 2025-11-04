import pytest
from playwright.sync_api import Page

from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter, AuthenticationConfig
from aqt_connector.exceptions import AuthenticationError
from tests.integration.auth0_adapter.helpers import (
    TEST_CLIENT_ID,
    TEST_TENANT_URL,
    log_in_device_flow,
    start_device_code_flow,
)


def test_it_returns_new_access_and_refresh_tokens(page: Page) -> None:
    """It should return new access and refresh tokens when given a valid refresh token."""
    device_code_data = start_device_code_flow()
    log_in_device_flow(page, device_code_data)
    config = AuthenticationConfig(issuer=TEST_TENANT_URL, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)
    tokens = auth_adapter.fetch_token_with_device_code(device_code_data[2])
    assert tokens is not None
    existing_refresh_token = tokens.refresh_token

    config = AuthenticationConfig(issuer=TEST_TENANT_URL, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)
    new_tokens = auth_adapter.fetch_token_with_refresh_token(existing_refresh_token)

    assert new_tokens.access_token is not None
    assert new_tokens.refresh_token != existing_refresh_token


def test_it_raises_exception_on_invalid_refresh_token() -> None:
    """It should raise an AuthenticationError when given an invalid refresh token."""
    config = AuthenticationConfig(issuer=TEST_TENANT_URL, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)

    with pytest.raises(AuthenticationError):
        auth_adapter.fetch_token_with_refresh_token("invalid_refresh_token")
