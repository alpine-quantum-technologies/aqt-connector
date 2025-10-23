import os
from typing import Final

import httpx
from playwright.sync_api import Page, expect

from aqt_connector._data_types import OfflineAccessTokens
from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter, AuthenticationConfig

TEST_TENANT_DOMAIN: Final = os.getenv("AUTH0_TEST_TENANT_DOMAIN", "")
TEST_CLIENT_ID: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_CLIENT_ID", "")
TEST_USER_EMAIL: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_USER_EMAIL", "")
TEST_USER_PASSWORD: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_USER_PASSWORD", "")


def start_device_code_flow() -> tuple[str, str, str]:
    """Starts the device code authorisation flow.

    Returns:
        tuple[str, str, str]: A tuple containing the verification URI, user code, and device code.
    """
    response = httpx.post(
        f"{TEST_TENANT_DOMAIN}/oauth/device/code",
        data={
            "client_id": TEST_CLIENT_ID,
            "scope": "openid profile offline_access",
        },
    ).raise_for_status()
    data = response.json()
    return (data["verification_uri_complete"], data["user_code"], data["device_code"])


def authenticate_with_device_code(page: Page, device_code_data: tuple[str, str, str]) -> OfflineAccessTokens:
    """Authenticates with a device code.

    Args:
        page (Page): The Playwright page to use for authentication.
        device_code_data (tuple[str, str, str]): A tuple containing the verification URI, user code, and device code.

    Returns:
        OfflineAccessTokens: The offline access tokens obtained after authentication.
    """
    (verification_uri, user_code, device_code) = device_code_data
    page.goto(verification_uri)
    expect(page.get_by_label("secure code")).to_have_value(user_code)
    page.get_by_role("button", name="confirm").click()
    page.get_by_role("textbox", name="email address").fill(TEST_USER_EMAIL)
    page.get_by_role("textbox", name="password").fill(TEST_USER_PASSWORD)
    page.get_by_role("button", name="continue").click()
    expect(page.get_by_role("heading", name="Congratulations, you're all set!")).to_be_visible()

    config = AuthenticationConfig(issuer=TEST_TENANT_DOMAIN, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)
    tokens = auth_adapter.fetch_token_with_device_code(device_code)

    assert tokens is not None
    return tokens
