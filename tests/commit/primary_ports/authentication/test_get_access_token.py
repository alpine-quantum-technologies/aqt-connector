from typing import Union

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig, get_access_token
from aqt_connector._domain.auth_service import AuthService


def test_it_gets_an_available_access_token() -> None:
    """It should return the access token if one is available."""

    class AuthServiceDummy(AuthService):
        def __init__(self):
            self.token = "thisisthestoredtoken"

        def get_or_refresh_access_token(self, store: bool) -> Union[str, None]:
            return self.token

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceDummy()

    access_token = get_access_token(app)

    assert access_token == app.auth_service.token


def test_it_returns_none_if_no_access_token_available() -> None:
    """It should return None if no access token is available."""

    class AuthServiceDummy(AuthService):
        def __init__(self): ...

        def get_or_refresh_access_token(self, store: bool) -> Union[str, None]:
            return None

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceDummy()

    access_token = get_access_token(app)

    assert access_token is None


@pytest.mark.parametrize("store_access_token", [True, False])
def test_it_stores_access_token_if_configured(store_access_token: bool) -> None:
    """It should store the access token if configured to do so."""

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

    get_access_token(app)

    assert app.auth_service.stored is store_access_token
