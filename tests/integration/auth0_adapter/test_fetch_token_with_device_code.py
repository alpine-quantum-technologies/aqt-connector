import os
from typing import Final

import httpx
import pytest
from playwright.sync_api import Page, expect

from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter, AuthenticationConfig
from aqt_connector.exceptions import AuthenticationError

TEST_TENANT_DOMAIN: Final = os.getenv("AUTH0_TEST_TENANT_DOMAIN", "")
TEST_CLIENT_ID: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_CLIENT_ID", "")
TEST_USER_EMAIL: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_USER_EMAIL", "")
TEST_USER_PASSWORD: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_USER_PASSWORD", "")


def start_device_code_flow() -> tuple[str, str, str]:
    response = httpx.post(
        f"{TEST_TENANT_DOMAIN}/oauth/device/code",
        data={
            "client_id": TEST_CLIENT_ID,
            "scope": "openid profile",
        },
    ).raise_for_status()
    data = response.json()
    return (data["verification_uri_complete"], data["user_code"], data["device_code"])


def test_it_returns_none_if_authorization_pending() -> None:
    (_, _, device_code) = start_device_code_flow()

    config = AuthenticationConfig(issuer=TEST_TENANT_DOMAIN, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)
    token = auth_adapter.fetch_token_with_device_code(device_code)

    assert token is None


def test_it_returns_access_token_when_authorization_complete(page: Page) -> None:
    (verification_uri, user_code, device_code) = start_device_code_flow()
    page.goto(verification_uri)
    expect(page.get_by_label("secure code")).to_have_value(user_code)
    page.get_by_role("button", name="confirm").click()
    page.get_by_label("email address").fill(TEST_USER_EMAIL)
    page.get_by_label("password").fill(TEST_USER_PASSWORD)
    page.get_by_role("button", name="continue").click()
    expect(page.get_by_role("presentation")).to_have_text("Congratulations, you're all set!")

    config = AuthenticationConfig(issuer=TEST_TENANT_DOMAIN, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)
    token = auth_adapter.fetch_token_with_device_code(device_code)

    assert token is not None


def test_it_raises_exception_on_other_error() -> None:
    config = AuthenticationConfig(issuer=TEST_TENANT_DOMAIN, device_client_id=TEST_CLIENT_ID)
    auth_adapter = Auth0Adapter(config)

    with pytest.raises(AuthenticationError):
        auth_adapter.fetch_token_with_device_code("not_a_device_code")
