from aqt_connector import ArnicaApp, ArnicaConfig, get_access_token
from aqt_connector.domain.auth_context import AuthContext


def test_it_gets_the_stored_access_token() -> None:
    class AuthContextDummy(AuthContext):
        def __init__(self):
            self.token = "thisisthestoredtoken"

        def get_access_token(self) -> str | None:
            return self.token

    app = ArnicaApp(ArnicaConfig())
    app.auth_context = AuthContextDummy()

    access_token = get_access_token(app)

    assert access_token == app.auth_context.token


def test_it_returns_none_if_no_stored_access_token() -> None:
    class AuthContextDummy(AuthContext):
        def __init__(self): ...

        def get_access_token(self) -> str | None:
            return None

    app = ArnicaApp(ArnicaConfig())
    app.auth_context = AuthContextDummy()

    access_token = get_access_token(app)

    assert access_token is None
