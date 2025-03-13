from aqt_connector.domain.auth_context import AuthContext
from aqt_connector.exceptions import TokenValidationError
from aqt_connector.infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector.infrastructure.token_repository import TokenRepository


class AccessTokenVerifierAlwaysVerifies(AccessTokenVerifier):
    def __init__(self): ...

    def verify_access_token(self, access_token):
        return access_token


class AccessTokenVerifierAlwaysRejects(AccessTokenVerifier):
    def __init__(self): ...

    def verify_access_token(self, access_token):
        raise TokenValidationError


class EmptyTokenRepository(TokenRepository):
    def __init__(self) -> None: ...

    def load(self) -> str | None:
        return None


class NonEmptyTokenRepository(TokenRepository):
    def __init__(self) -> None:
        self.saved_token: str = "this_is_the_stored_token"

    def load(self) -> str | None:
        return self.saved_token


def test_it_returns_none_if_no_token_stored() -> None:
    context = AuthContext(AccessTokenVerifierAlwaysVerifies(), EmptyTokenRepository())

    loaded_token = context.get_access_token()

    assert loaded_token is None


def test_it_gets_a_valid_token_when_stored() -> None:
    """When a valid token is stored it should be returned."""
    token_repo = NonEmptyTokenRepository()
    context = AuthContext(AccessTokenVerifierAlwaysVerifies(), token_repo)

    loaded_token = context.get_access_token()

    assert loaded_token == token_repo.saved_token


def test_it_doesnt_get_invalid_stored_tokens() -> None:
    """If the stored token is invalid, it should not be returned."""
    context = AuthContext(AccessTokenVerifierAlwaysRejects(), NonEmptyTokenRepository())

    loaded_token = context.get_access_token()

    assert loaded_token is None
