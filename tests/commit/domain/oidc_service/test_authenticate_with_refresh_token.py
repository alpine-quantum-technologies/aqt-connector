from typing import Optional

import pytest

from aqt_connector._data_types import OfflineAccessTokens
from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter
from aqt_connector.exceptions import AuthenticationError, TokenValidationError


class AuthAdapterSpyReturnsTokens(Auth0Adapter):
    def __init__(self) -> None:
        self.returned = OfflineAccessTokens(access_token="access-abc", refresh_token="refresh-def")
        self.used_refresh: Optional[str] = None

    def fetch_token_with_refresh_token(self, refresh_token: str):
        self.used_refresh = refresh_token
        return self.returned


class AuthAdapterRaises(Auth0Adapter):
    def __init__(self) -> None: ...

    def fetch_token_with_refresh_token(self, refresh_token: str):
        raise AuthenticationError


class AccessTokenVerifierAlwaysVerifies(AccessTokenVerifier):
    def __init__(self) -> None: ...

    def verify_access_token(self, access_token: str):
        return access_token


class AccessTokenVerifierAlwaysRejects(AccessTokenVerifier):
    def __init__(self) -> None: ...

    def verify_access_token(self, access_token: str):
        raise TokenValidationError


def test_it_returns_access_and_refresh_token_on_success() -> None:
    """It should return access and refresh token on success."""
    auth_adapter = AuthAdapterSpyReturnsTokens()
    context = OIDCService(auth_adapter, AccessTokenVerifierAlwaysVerifies())

    tokens = context.authenticate_with_refresh_token("some-refresh")

    assert auth_adapter.used_refresh == "some-refresh"
    assert tokens.access_token == "access-abc"
    assert tokens.refresh_token == "refresh-def"


def test_it_raises_token_validation_error_when_token_invalid() -> None:
    """It should raise TokenValidationError when the retrieved access token is invalid."""
    auth_adapter = AuthAdapterSpyReturnsTokens()
    context = OIDCService(auth_adapter, AccessTokenVerifierAlwaysRejects())

    with pytest.raises(TokenValidationError):
        context.authenticate_with_refresh_token("some-refresh")


def test_it_raises_authentication_error_when_adapter_fails() -> None:
    """It should raise AuthenticationError when the adapter fails to authenticate."""
    context = OIDCService(AuthAdapterRaises(), AccessTokenVerifierAlwaysVerifies())

    with pytest.raises(AuthenticationError):
        context.authenticate_with_refresh_token("whatever")
