import urllib.parse
from typing import Union

import httpx

from aqt_connector._data_types import DeviceCodeData, OfflineAccessTokens
from aqt_connector._sdk_config import AuthenticationConfig
from aqt_connector.exceptions import AuthenticationError


class Auth0Adapter:
    """Provides authentication with Auth0.

    Attributes:
        tenant_url (str): the URL of the auth provider tenant.
        device_client_id (str): the device client ID for the application.
        audience (str): the audience for the application.
    """

    def __init__(self, config: AuthenticationConfig) -> None:
        """Initialises the instance with the given attributes.

        Args:
            config (AuthenticationConfig): configuration for the Auth0 tenant.
        """
        self.tenant_url = config.issuer
        self.device_client_id = config.device_client_id
        self.audience = config.audience
        self._http_client = httpx.Client()

    def fetch_token_with_client_credentials(self, client_id: str, client_secret: str) -> str:
        """Fetches an access token using the client credentials flow.

        Args:
            client_id (str): the client ID.
            client_secret (str): the client secret.

        Raises:
            AuthenticationError: when authentication was unsuccessful.

        Returns:
            str: the resulting access token.
        """
        token_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": self.audience,
            "grant_type": "client_credentials",
        }
        token_response = self._http_client.post(
            urllib.parse.urljoin(self.tenant_url, "/oauth/token"), json=token_payload
        )
        token_data = token_response.json()
        if token_response.status_code == 200:
            return token_data["access_token"]
        raise AuthenticationError

    def fetch_token_with_device_code(self, device_code: str) -> Union[OfflineAccessTokens, None]:
        """Fetches an access token with a device code.

        Fetches an access token with a device code, once the user has logged in.

        Args:
            device_code (str): the device code.

        Raises:
            AuthenticationError: when the access token could not be retrieved. This does not
            indicate that authorization is still pending.

        Returns:
            OfflineAccessTokens | None: the resulting access token and refresh token once the user has successfully
            authenticated themselves, otherwise None.
        """
        token_payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": self.device_client_id,
        }
        token_response = self._http_client.post(
            urllib.parse.urljoin(self.tenant_url, "/oauth/token"), data=token_payload
        )
        token_data = token_response.json()

        if token_response.status_code == 200:
            return OfflineAccessTokens(
                access_token=token_data["id_token"],
                refresh_token=token_data["refresh_token"],
            )

        if token_data["error"] not in ("authorization_pending", "slow_down"):
            print(token_data)
            raise AuthenticationError(token_data["error_description"])

        return None

    def fetch_device_code(self) -> DeviceCodeData:
        """Fetches a device code.

        Fetches a device code that the user can use to log in with the device flow.

        Raises:
            AuthenticationError: when a device code could not be retrieved.

        Returns:
            DeviceCodeData: the information required for the user to authenticate themselves, and
            to request the resulting access token.
        """
        device_code_payload = {
            "client_id": self.device_client_id,
            "scope": "openid profile offline_access",
        }
        device_code_response = self._http_client.post(
            urllib.parse.urljoin(self.tenant_url, "/oauth/device/code"), data=device_code_payload
        )
        if device_code_response.status_code != 200:
            raise AuthenticationError

        device_code_data = device_code_response.json()
        return DeviceCodeData(
            verification_uri_complete=device_code_data["verification_uri_complete"],
            user_code=device_code_data["user_code"],
            device_code=device_code_data["device_code"],
            interval=device_code_data["interval"],
        )

    def fetch_token_with_refresh_token(self, refresh_token: str) -> OfflineAccessTokens:
        """Fetches an access token using a refresh token.

        Args:
            refresh_token (str): the refresh token.

        Raises:
            AuthenticationError: when authentication was unsuccessful.

        Returns:
            OfflineAccessTokens: the resulting access token and the next refresh token.
        """
        token_payload = {
            "client_id": self.device_client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        token_response = self._http_client.post(
            urllib.parse.urljoin(self.tenant_url, "/oauth/token"), data=token_payload
        )
        if token_response.status_code != 200:
            error = token_response.json()
            raise AuthenticationError(error.get("error_description", "Failed to refresh token."))

        token_data = token_response.json()
        return OfflineAccessTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
        )
