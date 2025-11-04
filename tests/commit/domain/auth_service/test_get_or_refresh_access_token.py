from typing import Union

import pytest

from aqt_connector._data_types import OfflineAccessTokens
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

    def load_refresh_token(self) -> Union[str, None]:
        return None


class TokenRepositoryNoRefreshToken(TokenRepository):
    def __init__(self) -> None:
        self.saved_token: str = "this_is_the_stored_token"

    def load_access_token(self) -> Union[str, None]:
        return self.saved_token

    def load_refresh_token(self) -> Union[str, None]:
        return None


class TokenRepositoryWithRefreshToken(TokenRepository):
    def __init__(self) -> None:
        self.existing_access_token: str = "this_is_the_stored_token"
        self.existing_refresh_token: str = "this_is_the_stored_refresh_token"
        self.saved_access_token: Union[str, None] = None
        self.saved_refresh_token: Union[str, None] = None

    def load_access_token(self) -> Union[str, None]:
        return self.existing_access_token

    def save_access_token(self, token: str) -> None:
        self.saved_access_token = token

    def load_refresh_token(self) -> Union[str, None]:
        return self.existing_refresh_token

    def save_refresh_token(self, refresh_token: str) -> None:
        self.saved_refresh_token = refresh_token


class OIDCServiceAlwaysRefreshes(OIDCService):
    def __init__(self) -> None:
        self.given_refresh_token: Union[str, None] = None
        self.access_token = "this-is-the-new-access-token"
        self.next_refresh_token = "this-is-the-next-refresh-token"

    def authenticate_with_refresh_token(self, refresh_token: str) -> OfflineAccessTokens:
        self.given_refresh_token = refresh_token
        return OfflineAccessTokens(
            access_token=self.access_token,
            refresh_token=self.next_refresh_token,
        )


def test_it_returns_none_if_no_tokens_stored() -> None:
    """It should return none if no valid access tokens and no refresh token are stored."""
    auth_service = AuthService(
        AccessTokenVerifierAlwaysVerifies(), EmptyTokenRepository(), OIDCServiceAlwaysRefreshes()
    )

    loaded_token = auth_service.get_or_refresh_access_token(False)

    assert loaded_token is None


def test_it_gets_a_valid_token_when_stored() -> None:
    """It should return a valid token if one is stored."""
    token_repo = TokenRepositoryNoRefreshToken()
    auth_service = AuthService(AccessTokenVerifierAlwaysVerifies(), token_repo, OIDCServiceAlwaysRefreshes())

    loaded_token = auth_service.get_or_refresh_access_token(False)

    assert loaded_token == token_repo.saved_token


def test_it_doesnt_get_invalid_stored_tokens() -> None:
    """If the stored token is invalid and no refresh token is stored, it should not be returned."""
    auth_service = AuthService(
        AccessTokenVerifierAlwaysRejects(), TokenRepositoryNoRefreshToken(), OIDCServiceAlwaysRefreshes()
    )

    loaded_token = auth_service.get_or_refresh_access_token(False)

    assert loaded_token is None


def test_it_refreshes_invalid_access_token_when_refresh_token_stored() -> None:
    """If the stored token is invalid and a refresh token is stored, it should refresh the access token."""
    token_repo = TokenRepositoryWithRefreshToken()
    oidc_service = OIDCServiceAlwaysRefreshes()
    auth_service = AuthService(AccessTokenVerifierAlwaysRejects(), token_repo, oidc_service)

    loaded_token = auth_service.get_or_refresh_access_token(False)

    assert loaded_token == oidc_service.access_token
    assert oidc_service.given_refresh_token == token_repo.existing_refresh_token


@pytest.mark.parametrize("store", [True, False])
def test_it_respects_store_parameter_when_refreshing_token(store: bool) -> None:
    """It should store the refreshed access token only when the store parameter is true."""
    token_repo = TokenRepositoryWithRefreshToken()
    oidc_service = OIDCServiceAlwaysRefreshes()
    auth_service = AuthService(AccessTokenVerifierAlwaysRejects(), token_repo, oidc_service)

    _ = auth_service.get_or_refresh_access_token(store)

    if store:
        assert token_repo.saved_access_token == oidc_service.access_token
        assert token_repo.saved_refresh_token == oidc_service.next_refresh_token
    else:
        assert token_repo.saved_access_token is None
        assert token_repo.saved_refresh_token is None
