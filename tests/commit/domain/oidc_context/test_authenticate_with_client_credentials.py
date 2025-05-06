from typing import Optional

import pytest

from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter
from aqt_connector.exceptions import AuthenticationError, TokenValidationError


class AuthAdapterSpyAlwaysAuthenticates(Auth0Adapter):
    def __init__(self) -> None:
        self.client_access_token = "this-is-the-client-token"
        self.used_credentials: Optional[tuple[str, str]] = None

    def fetch_token_with_client_credentials(self, client_id: str, client_secret: str) -> str:
        self.used_credentials = (client_id, client_secret)
        return self.client_access_token


class AuthAdapterNeverAuthenticates(Auth0Adapter):
    def __init__(self) -> None: ...

    def fetch_token_with_client_credentials(self, client_id: str, client_secret: str) -> str:
        raise AuthenticationError


class AccessTokenVerifierAlwaysVerifies(AccessTokenVerifier):
    def __init__(self): ...

    def verify_access_token(self, access_token):
        return access_token


class AccessTokenVerifierAlwaysRejects(AccessTokenVerifier):
    def __init__(self): ...

    def verify_access_token(self, access_token):
        raise TokenValidationError


def test_it_retrieves_token_with_the_given_credentials() -> None:
    auth_adapter = AuthAdapterSpyAlwaysAuthenticates()
    context = OIDCService(auth_adapter, AccessTokenVerifierAlwaysVerifies())
    credentials = ("client-id", "client-secret")

    retrieved_token = context.authenticate_with_client_credentials(credentials)

    assert auth_adapter.used_credentials == credentials
    assert retrieved_token == auth_adapter.client_access_token


def test_it_raises_token_validation_error_when_retrieved_token_invalid() -> None:
    context = OIDCService(AuthAdapterSpyAlwaysAuthenticates(), AccessTokenVerifierAlwaysRejects())

    with pytest.raises(TokenValidationError):
        context.authenticate_with_client_credentials(("client-id", "client-secret"))


def test_it_raises_authentication_error_when_authentication_fails() -> None:
    context = OIDCService(AuthAdapterNeverAuthenticates(), AccessTokenVerifierAlwaysVerifies())

    with pytest.raises(AuthenticationError):
        context.authenticate_with_client_credentials(("client-id", "client-secret"))
