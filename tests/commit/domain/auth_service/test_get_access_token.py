from typing import Union

from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.token_repository import TokenRepository
from aqt_connector.exceptions import TokenValidationError


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

    def load_access_token(self) -> Union[str, None]:
        return None


class NonEmptyTokenRepository(TokenRepository):
    def __init__(self) -> None:
        self.saved_token: str = "this_is_the_stored_token"

    def load_access_token(self) -> Union[str, None]:
        return self.saved_token


class OIDCDummy(OIDCService):
    def __init__(self) -> None: ...


def test_it_returns_none_if_no_token_stored() -> None:
    context = AuthService(AccessTokenVerifierAlwaysVerifies(), EmptyTokenRepository(), OIDCDummy())

    loaded_token = context.get_access_token()

    assert loaded_token is None


def test_it_gets_a_valid_token_when_stored() -> None:
    """When a valid token is stored it should be returned."""
    token_repo = NonEmptyTokenRepository()
    context = AuthService(AccessTokenVerifierAlwaysVerifies(), token_repo, OIDCDummy())

    loaded_token = context.get_access_token()

    assert loaded_token == token_repo.saved_token


def test_it_doesnt_get_invalid_stored_tokens() -> None:
    """If the stored token is invalid, it should not be returned."""
    context = AuthService(AccessTokenVerifierAlwaysRejects(), NonEmptyTokenRepository(), OIDCDummy())

    loaded_token = context.get_access_token()

    assert loaded_token is None
