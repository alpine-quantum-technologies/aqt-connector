from typing import Union

from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.token_repository import TokenRepository
from aqt_connector.exceptions import TokenValidationError


class AuthService:
    """Manages access tokens."""

    def __init__(self, access_token_verifier: AccessTokenVerifier, token_repository: TokenRepository) -> None:
        """Initialises the instance with the given access token verifier and token repository.

        Args:
            access_token_verifier (AccessTokenVerifier): the access token verifier.
            token_repository (TokenRepository): the token repository.
        """
        self._token_verifier = access_token_verifier
        self._token_repo = token_repository

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
