import sys
import time
from typing import TextIO

import qrcode  # type: ignore

from aqt_connector._data_types import DeviceCodeData, OfflineAccessTokens
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter
from aqt_connector.exceptions import TokenValidationError


class OIDCService:
    """Authenticates with OIDC."""

    def __init__(
        self,
        auth_adapter: Auth0Adapter,
        access_token_verifier: AccessTokenVerifier,
    ) -> None:
        """Iniialises the instance with the given auth provider adapter and access token verifier.

        Args:
            auth_adapter (Auth0Adapter): the auth provider adapter.
            access_token_verifier (AccessTokenVerifier): the access token verifier.
        """
        self._auth_adapter = auth_adapter
        self._token_verifier = access_token_verifier

    def authenticate_with_client_credentials(
        self,
        client_credentials: tuple[str, str],
    ) -> str:
        """Authenticates with the OIDC client credentials flow.

        Args:
            client_credentials (tuple[str, str]): a tuple containing the client id and client
                secret.

        Raises:
            AuthenticationError: when authentication failed.
            TokenValidationError: when authentication succeeded, but the retrieved access token
                is invalid.

        Returns:
            str: the resulting access token.
        """
        access_token = self._auth_adapter.fetch_token_with_client_credentials(
            client_credentials[0], client_credentials[1]
        )

        if not self._token_verifier.verify_access_token(access_token):
            raise TokenValidationError

        return access_token

    def authenticate_device(self, *, out: TextIO = sys.stdout) -> OfflineAccessTokens:
        """Authenticates with the OIDC device flow.

        Args:
            out (TextIO, optional): text stream to send output to. Defaults to sys.stdout.

        Raises:
            AuthenticationError: when authentication failed.
            TokenValidationError: when authentication succeeded, but the retrieved access token
                is invalid.

        Returns:
            OfflineAccessTokens: the resulting access token and the next refresh token.
        """
        device_code_data = self._start_device_flow(out)
        tokens = self._poll_for_token(device_code_data)

        if not self._token_verifier.verify_access_token(tokens.access_token):
            raise TokenValidationError

        return tokens

    def authenticate_with_refresh_token(self, refresh_token: str) -> OfflineAccessTokens:
        """Authenticates with a refresh token.

        Args:
            refresh_token (str): the refresh token.

        Raises:
            AuthenticationError: when authentication failed.
            TokenValidationError: when authentication succeeded, but the retrieved access token
                is invalid.

        Returns:
            OfflineAccessTokens: the resulting access token and the next refresh token.
        """
        tokens = self._auth_adapter.fetch_token_with_refresh_token(refresh_token)

        if not self._token_verifier.verify_access_token(tokens.access_token):
            raise TokenValidationError

        return tokens

    def _start_device_flow(self, out: TextIO) -> DeviceCodeData:
        device_code_data = self._auth_adapter.fetch_device_code()
        out.write(
            f"""1. On your computer or mobile device navigate to: 
            {device_code_data.verification_uri_complete}, or scan:\n"""
        )
        qr = qrcode.QRCode()
        qr.add_data(device_code_data.verification_uri_complete)
        qr.print_ascii(out=out)
        out.write(f"2. Verify the following code: {device_code_data.user_code}\n")
        return device_code_data

    def _poll_for_token(
        self,
        device_code_data: DeviceCodeData,
    ) -> OfflineAccessTokens:
        while True:
            tokens = self._auth_adapter.fetch_token_with_device_code(device_code_data.device_code)
            if tokens is not None:
                return tokens
            else:
                time.sleep(device_code_data.interval)
