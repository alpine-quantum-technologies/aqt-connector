from typing import Union

from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.token_repository import TokenRepository
from aqt_connector.exceptions import TokenValidationError


class AuthService:
    """Manages access tokens."""

    def __init__(
        self, access_token_verifier: AccessTokenVerifier, token_repository: TokenRepository, oidc_service: OIDCService
    ) -> None:
        """Initialises the instance with the given access token verifier and token repository.

        Args:
            access_token_verifier (AccessTokenVerifier): the access token verifier.
            token_repository (TokenRepository): the token repository.
            oidc_service (OIDCService): the OIDC service.
        """
        self._token_verifier = access_token_verifier
        self._token_repo = token_repository
        self._oidc_service = oidc_service

    def get_access_token(self) -> Union[str, None]:
        """Loads an access token if a valid one is stored.

        Returns:
            str | None: the access token, when a valid one is stored, otherwise None.
        """
        loaded_token = self._token_repo.load_access_token()
        if loaded_token is None:
            return None

        try:
            self._token_verifier.verify_access_token(loaded_token)
            return loaded_token
        except TokenValidationError:
            return None

    def save_access_token(self, access_token: str) -> None:
        """Stores an access token.

        Args:
            access_token (str): the access token to store.
        """
        self._token_repo.save_access_token(access_token)

    def get_or_refresh_access_token(self, store: bool) -> Union[str, None]:
        """Gets an access token for the current user session, or refreshes it.

        Args:
            store (bool): whether to store the access token.

        Returns:
            str | None: the access token if available, otherwise None.
        """
        if existing_token := self.get_access_token():
            return existing_token

        if refresh_token := self._token_repo.load_refresh_token():
            new_access_token, next_refresh_token = self._oidc_service.authenticate_with_refresh_token(refresh_token)
            if store:
                self.save_access_token(new_access_token)
                self._token_repo.save_refresh_token(next_refresh_token)
            return new_access_token

        return None
