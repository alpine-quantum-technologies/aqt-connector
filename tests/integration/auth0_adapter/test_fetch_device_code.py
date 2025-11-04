import os
import re
from typing import Final
from urllib.parse import parse_qs, urlparse

import pytest

from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter, AuthenticationConfig
from aqt_connector.exceptions import AuthenticationError

TEST_TENANT_URL: Final = os.getenv("AUTH0_TEST_TENANT_URL", "")
TEST_CLIENT_ID: Final = os.getenv("AUTH0_TEST_DEVICE_FLOW_CLIENT_ID", "")


def test_it_fetches_the_device_code_data() -> None:
    config = AuthenticationConfig(
        issuer=TEST_TENANT_URL,
        device_client_id=TEST_CLIENT_ID,
    )
    auth_adapter = Auth0Adapter(config)

    device_code_data = auth_adapter.fetch_device_code()

    verification_url = urlparse(device_code_data.verification_uri_complete)
    expected_url = urlparse(TEST_TENANT_URL)
    assert verification_url.scheme == expected_url.scheme
    assert verification_url.hostname == expected_url.hostname
    assert parse_qs(verification_url.query)["user_code"][0] == device_code_data.user_code

    user_code_pattern = r"[BCDFGHJKLMNPQRSTVWXZ]{4}-[BCDFGHJKLMNPQRSTVWXZ]{4}"
    assert re.fullmatch(user_code_pattern, device_code_data.user_code)

    assert device_code_data.interval > 0


def test_it_raises_authentication_error_on_error() -> None:
    invalid_client_id = "this-is-not-a-valid-client-id"
    config = AuthenticationConfig(
        issuer=TEST_TENANT_URL,
        device_client_id=invalid_client_id,
    )
    auth_adapter = Auth0Adapter(config)

    with pytest.raises(AuthenticationError):
        auth_adapter.fetch_device_code()
