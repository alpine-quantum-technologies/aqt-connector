import sys
from typing import Optional, TextIO, Union

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig, log_in
from aqt_connector._data_types import OfflineAccessTokens
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.oidc_service import OIDCService


class OIDCServiceAlwaysAuthenticates(OIDCService):
    def __init__(self) -> None:
        self.client_access_token = "this-is-the-client-token"
        self.device_access_token = "this-is-the-device-token"
        self.refresh_token = "this-is-the-refresh-token"
        self.used_credentials: Optional[tuple[str, str]] = None

    def authenticate_with_client_credentials(self, client_credentials) -> str:
        self.used_credentials = client_credentials
        return self.client_access_token

    def authenticate_device(self, *, out: TextIO = sys.stdout) -> OfflineAccessTokens:
        return OfflineAccessTokens(access_token=self.device_access_token, refresh_token=self.refresh_token)


class AuthenticatedAuthService(AuthService):
    def __init__(self) -> None:
        self.stored_access_token = "this-is-the-existing-token"

    def save_access_token(self, access_token: str) -> None:
        self.stored_access_token = access_token

    def get_or_refresh_access_token(self, store: bool) -> Union[str, None]:
        return self.stored_access_token


class UnauthenticatedAuthService(AuthService):
    def __init__(self) -> None:
        self.stored_access_token: Union[str, None] = None

    def get_or_refresh_access_token(self, store: bool) -> Union[str, None]:
        return self.stored_access_token

    def save_access_token(self, access_token: str) -> None:
        self.stored_access_token = access_token


def test_it_returns_a_stored_valid_access_token() -> None:
    """It should return a stored valid access token."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthenticatedAuthService()
    app.oidc_service = OIDCServiceAlwaysAuthenticates()

    access_token = log_in(app)

    assert access_token == app.auth_service.stored_access_token


@pytest.mark.parametrize("store_access_token", [True, False])
def test_it_stores_refreshed_access_token_if_configured(store_access_token: bool) -> None:
    """It should store the refreshed access token if configured to do so."""

    class AuthServiceDummy(AuthService):
        def __init__(self):
            self.stored = False

        def get_or_refresh_access_token(self, store: bool) -> Union[str, None]:
            self.stored = store
            return "newaccesstoken"

    config = ArnicaConfig()
    config.store_access_token = store_access_token
    app = ArnicaApp(config)
    app.auth_service = AuthServiceDummy()

    log_in(app)

    assert app.auth_service.stored is store_access_token


def test_it_authenticates_with_client_credentials_when_set() -> None:
    """It should authenticate using client credentials when they are set."""
    config = ArnicaConfig()
    config.client_id = "client-id"
    config.client_secret = "snape_kills_dumbledore"
    app = ArnicaApp(config)
    app.auth_service = UnauthenticatedAuthService()
    app.oidc_service = OIDCServiceAlwaysAuthenticates()

    access_token = log_in(app)

    assert app.oidc_service.used_credentials == (config.client_id, config.client_secret)
    assert access_token == app.oidc_service.client_access_token


def test_it_authenticates_device_when_client_credentials_not_set() -> None:
    """It should authenticate using the device flow when client credentials are not set."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = UnauthenticatedAuthService()
    app.oidc_service = OIDCServiceAlwaysAuthenticates()

    access_token = log_in(app)

    assert app.oidc_service.used_credentials is None
    assert access_token == app.oidc_service.device_access_token


@pytest.mark.parametrize("store_access_token", (True, False))
def test_it_respects_store_access_token_config(store_access_token: bool) -> None:
    """It should only store the access token if configured to do so."""
    config = ArnicaConfig()
    config.store_access_token = store_access_token
    app = ArnicaApp(config)
    app.auth_service = UnauthenticatedAuthService()
    app.oidc_service = OIDCServiceAlwaysAuthenticates()

    log_in(app)

    assert (app.auth_service.stored_access_token == app.oidc_service.device_access_token) == store_access_token
