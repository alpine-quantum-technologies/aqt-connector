import sys
from typing import Optional, TextIO, Union

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig, log_in
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.oidc_service import OIDCService


class OIDCContextAlwaysAuthenticates(OIDCService):
    def __init__(self) -> None:
        self.client_access_token = "this-is-the-client-token"
        self.device_access_token = "this-is-the-device-token"
        self.used_credentials: Optional[tuple[str, str]] = None

    def authenticate_with_client_credentials(self, client_credentials) -> str:
        self.used_credentials = client_credentials
        return self.client_access_token

    def authenticate_device(self, *, out: TextIO = sys.stdout) -> str:
        return self.device_access_token


class AuthenticatedAuthContext(AuthService):
    def __init__(self) -> None:
        self.stored_access_token = "this-is-the-existing-token"

    def save_access_token(self, access_token: str) -> None:
        self.stored_access_token = access_token

    def get_access_token(self) -> Union[str, None]:
        return self.stored_access_token


class UnauthenticatedAuthContext(AuthService):
    def __init__(self) -> None:
        self.stored_access_token: Union[str, None] = None

    def get_access_token(self) -> Union[str, None]:
        return self.stored_access_token

    def save_access_token(self, access_token: str) -> None:
        self.stored_access_token = access_token


def test_it_returns_a_stored_valid_access_token() -> None:
    app = ArnicaApp(ArnicaConfig())
    app.auth_context = AuthenticatedAuthContext()
    app.oidc_context = OIDCContextAlwaysAuthenticates()

    access_token = log_in(app)

    assert access_token == app.auth_context.stored_access_token


def test_it_authenticates_with_client_credentials_when_set() -> None:
    config = ArnicaConfig()
    config.client_id = "client-id"
    config.client_secret = "snape_kills_dumbledore"
    app = ArnicaApp(config)
    app.auth_context = UnauthenticatedAuthContext()
    app.oidc_context = OIDCContextAlwaysAuthenticates()

    access_token = log_in(app)

    assert app.oidc_context.used_credentials == (config.client_id, config.client_secret)
    assert access_token == app.oidc_context.client_access_token


def test_it_authenticates_device_when_client_credentials_not_set() -> None:
    app = ArnicaApp(ArnicaConfig())
    app.auth_context = UnauthenticatedAuthContext()
    app.oidc_context = OIDCContextAlwaysAuthenticates()

    access_token = log_in(app)

    assert app.oidc_context.used_credentials is None
    assert access_token == app.oidc_context.device_access_token


@pytest.mark.parametrize("store_access_token", (True, False))
def test_it_respects_store_access_token_config(store_access_token: bool) -> None:
    config = ArnicaConfig()
    config.store_access_token = store_access_token
    app = ArnicaApp(config)
    app.auth_context = UnauthenticatedAuthContext()
    app.oidc_context = OIDCContextAlwaysAuthenticates()

    log_in(app)

    assert (app.auth_context.stored_access_token == app.oidc_context.device_access_token) == store_access_token
