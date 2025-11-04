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


def test_it_returns_none_if_authorization_pending() -> None:
    """It should return None if the user has not yet completed the device code flow."""
    (_, _, device_code) = start_device_code_flow()

    config = AuthenticationConfig(issuer=TEST_TENANT_URL, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)
    token = auth_adapter.fetch_token_with_device_code(device_code)

    assert token is None


def test_it_fetches_access_token_when_authorization_complete(page: Page) -> None:
    """It should return an access token once the user has completed the device code flow."""
    device_code_data = start_device_code_flow()
    log_in_device_flow(page, device_code_data)

    config = AuthenticationConfig(issuer=TEST_TENANT_URL, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)
    token = auth_adapter.fetch_token_with_device_code(device_code_data[2])

    assert token is not None


def test_it_raises_exception_on_other_error() -> None:
    """It should raise an AuthenticationError if the device code is invalid."""
    config = AuthenticationConfig(issuer=TEST_TENANT_URL, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)

    with pytest.raises(AuthenticationError):
        auth_adapter.fetch_token_with_device_code("not_a_device_code")
