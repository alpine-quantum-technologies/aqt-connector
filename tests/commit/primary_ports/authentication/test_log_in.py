import sys
from typing import TextIO

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig, log_in
from aqt_connector._data_types import OfflineAccessTokens
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector.exceptions import AuthenticationError


class OIDCServiceAlwaysAuthenticates(OIDCService):
    def __init__(self) -> None:
        self.client_access_token = "this-is-the-client-token"
        self.device_access_token = "this-is-the-device-token"
        self.refresh_token = "this-is-the-refresh-token"
        self.used_credentials: tuple[str, str] | None = None
        self.device_authentication_calls = 0

    def authenticate_with_client_credentials(self, client_credentials) -> str:
        self.used_credentials = client_credentials
        return self.client_access_token

    def authenticate_device(self, *, out: TextIO = sys.stdout) -> OfflineAccessTokens:
        self.device_authentication_calls += 1
        return OfflineAccessTokens(access_token=self.device_access_token, refresh_token=self.refresh_token)


class AuthenticatedAuthService(AuthService):
    def __init__(self) -> None:
        self.stored_access_token = "this-is-the-existing-token"
        self.stored_refresh_token: str | None = None

    def save_access_token(self, access_token: str) -> None:
        self.stored_access_token = access_token

    def save_refresh_token(self, refresh_token: str) -> None:
        self.stored_refresh_token = refresh_token

    def get_or_refresh_access_token(self, store: bool) -> str | None:
        return self.stored_access_token


class UnauthenticatedAuthService(AuthService):
    def __init__(self) -> None:
        self.stored_access_token: str | None = None
        self.stored_refresh_token: str | None = None

    def get_or_refresh_access_token(self, store: bool) -> str | None:
        return self.stored_access_token

    def save_access_token(self, access_token: str) -> None:
        self.stored_access_token = access_token

    def save_refresh_token(self, refresh_token: str) -> None:
        self.stored_refresh_token = refresh_token


class RejectedRefreshAuthService(UnauthenticatedAuthService):
    def get_or_refresh_access_token(self, store: bool) -> str | None:
        raise AuthenticationError("refresh token rejected")


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

        def get_or_refresh_access_token(self, store: bool) -> str | None:
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
    assert (app.auth_service.stored_refresh_token == app.oidc_service.refresh_token) == store_access_token


def test_it_does_not_store_refresh_token_for_client_credentials() -> None:
    """It should not store a refresh token for the client credentials flow."""
    config = ArnicaConfig()
    config.client_id = "client-id"
    config.client_secret = "client-secret"
    app = ArnicaApp(config)
    app.auth_service = UnauthenticatedAuthService()
    app.oidc_service = OIDCServiceAlwaysAuthenticates()

    log_in(app)

    assert app.auth_service.stored_access_token == app.oidc_service.client_access_token
    assert app.auth_service.stored_refresh_token is None


def test_it_starts_device_login_if_stored_refresh_token_is_rejected() -> None:
    """It should replace both stored tokens after a rejected refresh token."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = RejectedRefreshAuthService()
    app.auth_service.stored_access_token = "expired-access-token"
    app.auth_service.stored_refresh_token = "rejected-refresh-token"
    app.oidc_service = OIDCServiceAlwaysAuthenticates()

    access_token = log_in(app)

    assert access_token == app.oidc_service.device_access_token
    assert app.auth_service.stored_access_token == app.oidc_service.device_access_token
    assert app.auth_service.stored_refresh_token == app.oidc_service.refresh_token


def test_it_uses_client_credentials_if_stored_refresh_token_is_rejected() -> None:
    """It should use configured client credentials after a rejected refresh token."""
    config = ArnicaConfig()
    config.client_id = "client-id"
    config.client_secret = "client-secret"
    app = ArnicaApp(config)
    app.auth_service = RejectedRefreshAuthService()
    app.oidc_service = OIDCServiceAlwaysAuthenticates()

    access_token = log_in(app)

    assert app.oidc_service.used_credentials == (config.client_id, config.client_secret)
    assert access_token == app.oidc_service.client_access_token
    assert app.auth_service.stored_access_token == app.oidc_service.client_access_token
    assert app.auth_service.stored_refresh_token is None


def test_it_propagates_fresh_authentication_failure_after_rejected_refresh() -> None:
    """It should propagate authentication failures from a fresh login."""

    class OIDCServiceFailingDeviceAuthentication(OIDCServiceAlwaysAuthenticates):
        def authenticate_device(self, *, out: TextIO = sys.stdout) -> OfflineAccessTokens:
            raise AuthenticationError("fresh authentication failed")

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = RejectedRefreshAuthService()
    app.oidc_service = OIDCServiceFailingDeviceAuthentication()

    with pytest.raises(AuthenticationError, match="fresh authentication failed"):
        log_in(app)


def test_it_propagates_unrelated_error_from_token_lookup() -> None:
    """It should only recover from authentication failures during token lookup."""

    class AuthServiceFailingTokenLookup(UnauthenticatedAuthService):
        def get_or_refresh_access_token(self, store: bool) -> str | None:
            raise RuntimeError("token storage failed")

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceFailingTokenLookup()
    app.oidc_service = OIDCServiceAlwaysAuthenticates()

    with pytest.raises(RuntimeError, match="token storage failed"):
        log_in(app)

    assert app.oidc_service.device_authentication_calls == 0
