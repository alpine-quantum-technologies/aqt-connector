from typing import Union

from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.token_repository import TokenRepository


class AccessTokenVerifierStub(AccessTokenVerifier):
    def __init__(self) -> None: ...


class TokenRepositorySpy(TokenRepository):
    def __init__(self) -> None:
        self.saved_token: Union[str, None] = None

    def save_access_token(self, token: str) -> None:
        self.saved_token = token


class OIDCDummy(OIDCService):
    def __init__(self) -> None: ...


def test_it_saves_the_given_access_token() -> None:
    token_repo = TokenRepositorySpy()
    context = AuthService(AccessTokenVerifierStub(), token_repo, OIDCDummy())

    access_token = "this-is-the-given-token"
    context.save_access_token(access_token)

    assert token_repo.saved_token == access_token
