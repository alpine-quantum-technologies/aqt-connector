import os
from typing import Final

import pytest

from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter, AuthenticationConfig
from aqt_connector.exceptions import AuthenticationError

TEST_TENANT_URL: Final = os.getenv("AUTH0_TEST_TENANT_URL", "")
TEST_AUDIENCE: Final = os.getenv("AUTH0_TEST_CLIENT_CREDENTIALS_AUDIENCE", "")
TEST_CLIENT_ID: Final = os.getenv("AUTH0_TEST_CLIENT_CREDENTIALS_CLIENT_ID", "")
TEST_CLIENT_SECRET: Final = os.getenv("AUTH0_TEST_CLIENT_CREDENTIALS_CLIENT_SECRET", "")


def test_it_fetches_the_access_token() -> None:
    config = AuthenticationConfig(issuer=TEST_TENANT_URL, audience=TEST_AUDIENCE)
    auth_adapter = Auth0Adapter(config)

    assert auth_adapter.fetch_token_with_client_credentials(TEST_CLIENT_ID, TEST_CLIENT_SECRET)


def test_it_raises_authentication_error_on_error() -> None:
    config = AuthenticationConfig(issuer=TEST_TENANT_URL, audience=TEST_AUDIENCE)
    auth_adapter = Auth0Adapter(config)

    with pytest.raises(AuthenticationError):
        auth_adapter.fetch_token_with_client_credentials("client_id", "not_the_secret")
