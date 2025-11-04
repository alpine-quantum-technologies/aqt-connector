import os
from typing import Final

import httpx
from playwright.sync_api import Page, expect

TEST_TENANT_URL: Final = os.getenv("AUTH0_TEST_TENANT_URL", "")
TEST_CLIENT_ID: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_CLIENT_ID", "")
TEST_USER_EMAIL: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_USER_EMAIL", "")
TEST_USER_PASSWORD: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_USER_PASSWORD", "")


def start_device_code_flow() -> tuple[str, str, str]:
    """Starts the device code authorisation flow.

    Returns:
        tuple[str, str, str]: A tuple containing the verification URI, user code, and device code.
    """
    response = httpx.post(
        f"{TEST_TENANT_URL}/oauth/device/code",
        data={
            "client_id": TEST_CLIENT_ID,
            "scope": "openid profile offline_access",
        },
    ).raise_for_status()
    data = response.json()
    return (data["verification_uri_complete"], data["user_code"], data["device_code"])


def log_in_device_flow(page: Page, device_code_data: tuple[str, str, str]) -> None:
    """Logs in to the device code flow using the provided Playwright page.

    Args:
        page (Page): The Playwright page to use for authentication.
        device_code_data (tuple[str, str, str]): A tuple containing the verification URI, user code, and device code.
    """
    (verification_uri, user_code, device_code) = device_code_data
    page.goto(verification_uri)
    expect(page.get_by_label("secure code")).to_have_value(user_code)
    page.get_by_role("button", name="confirm").click()
    page.get_by_role("textbox", name="email address").fill(TEST_USER_EMAIL)
    page.get_by_role("textbox", name="password").fill(TEST_USER_PASSWORD)
    page.get_by_role("button", name="continue").click()
    expect(page.get_by_role("heading", name="Congratulations, you're all set!")).to_be_visible()
