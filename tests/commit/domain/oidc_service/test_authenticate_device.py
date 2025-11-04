from io import StringIO
from typing import Optional, Union

import pytest

from aqt_connector._data_types import DeviceCodeData, OfflineAccessTokens
from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter
from aqt_connector.exceptions import AuthenticationError, TokenValidationError


class AuthAdapterSpyAlwaysAuthenticatesImmediately(Auth0Adapter):
    def __init__(self) -> None:
        self.device_access_token = "this-is-the-device-token"
        self.refresh_token = "this-is-the-refresh-token"
        self.device_code_data = DeviceCodeData(
            verification_uri_complete="https://arnica.aqt.eu/api",
            user_code="BLTT_HPNS",
            device_code="abcde12345",
            interval=5,
        )

    def fetch_token_with_device_code(self, device_code: str) -> Union[OfflineAccessTokens, None]:
        self.used_device_code = device_code
        return OfflineAccessTokens(
            access_token=self.device_access_token,
            refresh_token=self.refresh_token,
        )

    def fetch_device_code(self) -> DeviceCodeData:
        return self.device_code_data


class AuthAdapterPollingSpy(Auth0Adapter):
    def __init__(self) -> None:
        self.access_token = "this-is-the-device-token"
        self.refresh_token = "this-is-the-refresh-token"
        self.token_poll_count = 0

    def fetch_token_with_device_code(self, device_code: str) -> Union[OfflineAccessTokens, None]:
        self.token_poll_count += 1
        if self.token_poll_count > 2:
            return OfflineAccessTokens(
                access_token=self.access_token,
                refresh_token=self.refresh_token,
            )
        return None

    def fetch_device_code(self) -> DeviceCodeData:
        return DeviceCodeData(
            verification_uri_complete="https://arnica.aqt.eu/api",
            user_code="BLTT_HPNS",
            device_code="abcde12345",
            interval=0.1,
        )


class AuthAdapterNeverAuthenticates(Auth0Adapter):
    def __init__(self) -> None: ...

    def fetch_token_with_device_code(self, device_code: str) -> Union[OfflineAccessTokens, None]:
        raise AuthenticationError

    def fetch_device_code(self) -> DeviceCodeData:
        return DeviceCodeData(
            verification_uri_complete="https://arnica.aqt.eu/api",
            user_code="BLTT_HPNS",
            device_code="abcde12345",
            interval=5,
        )


class AccessTokenVerifierAlwaysVerifies(AccessTokenVerifier):
    def __init__(self): ...

    def verify_access_token(self, access_token):
        return access_token


class AccessTokenVerifierAlwaysRejects(AccessTokenVerifier):
    def __init__(self): ...

    def verify_access_token(self, access_token):
        raise TokenValidationError


class StdoutSpy(StringIO):
    def __init__(self, initial_value: Optional[str] = "", newline: Optional[str] = "\n") -> None:
        self.output: list[str] = []
        super().__init__(initial_value, newline)

    def write(self, s):
        self.output.append(s)
        return super().write(s)

    def writelines(self, lines):
        self.output += lines
        return super().writelines(lines)


def test_it_displays_the_verification_uri_and_user_code() -> None:
    """It should display the verification URI and user code."""
    auth_adapter = AuthAdapterSpyAlwaysAuthenticatesImmediately()
    context = OIDCService(
        auth_adapter,
        AccessTokenVerifierAlwaysVerifies(),
    )
    stdout_spy = StdoutSpy()

    context.authenticate_device(out=stdout_spy)

    assert any(auth_adapter.device_code_data.verification_uri_complete in output for output in stdout_spy.output)
    assert any(auth_adapter.device_code_data.user_code in output for output in stdout_spy.output)


def test_it_displays_a_qr_code_for_the_verification_uri() -> None:
    """It should display a QR code for the verification URI."""
    auth_adapter = AuthAdapterSpyAlwaysAuthenticatesImmediately()
    context = OIDCService(
        auth_adapter,
        AccessTokenVerifierAlwaysVerifies(),
    )
    stdout_spy = StdoutSpy()

    context.authenticate_device(out=stdout_spy)

    expected_qr_output = [
        line.replace(" ", "\xa0")
        for line in [
            "█▀▀▀▀▀█ █▄▄▀▀█  ▄ █▀▀▀▀▀█",
            "█ ███ █ ▀▀▀▀ █▄▀▀ █ ███ █",
            "█ ▀▀▀ █ ▀█▄█▀██ ▀ █ ▀▀▀ █",
            "▀▀▀▀▀▀▀ ▀▄▀ █▄█ ▀ ▀▀▀▀▀▀▀",
            "█▄ ▀██▀██▀ ▀  ██▀█ ▄█▄██▀",
            "▀█▀▀▄▀▀ ▀ ▄▀▄ ▄█ █▀▀▀█▄▄█",
            "██▀▄▄ ▀█▀▀▀ ▀▄ ▄▀ ▀▀▄  ▄▀",
            "█▀█▀▄ ▀▄█ ██▀▀▀▀▄▀ ▄▀██▀█",
            "▀ ▀   ▀▀▄██▄██▀▀█▀▀▀█ ██ ",
            "█▀▀▀▀▀█ ██ ▀▄▄ ▄█ ▀ █  ▄█",
            "█ ███ █ █▀▄█▀ ██▀██▀▀  ▄▄",
            "█ ▀▀▀ █   ▀██ █▀ █ ▄█▀███",
            "▀▀▀▀▀▀▀ ▀  ▀    ▀ ▀  ▀  ▀ ",
        ]
    ]

    output_lines = "".join(stdout_spy.output).split("\n")

    for i, output_line in enumerate(output_lines):
        if expected_qr_output[0] in output_line:
            offset = i
            break

    assert offset >= 0
    assert all(
        expected_qr_output[line_number] in output_lines[line_number + offset]
        for line_number, _ in enumerate(expected_qr_output)
    )


def test_it_polls_the_token_endpoint_until_id_token_available() -> None:
    """It should poll the token endpoint until the adapter returns OfflineAccessTokens."""
    auth_adapter = AuthAdapterPollingSpy()
    context = OIDCService(
        auth_adapter,
        AccessTokenVerifierAlwaysVerifies(),
    )

    retrieved_tokens = context.authenticate_device()

    assert retrieved_tokens.access_token == auth_adapter.access_token
    assert retrieved_tokens.refresh_token == auth_adapter.refresh_token


def test_it_raises_error_when_id_token_invalid() -> None:
    """It should raise TokenValidationError when the adapter returns a tuple but the access token is invalid."""
    context = OIDCService(
        AuthAdapterSpyAlwaysAuthenticatesImmediately(),
        AccessTokenVerifierAlwaysRejects(),
    )

    with pytest.raises(TokenValidationError):
        context.authenticate_device()


def test_it_raises_error_when_authentication_fails() -> None:
    """It should raise AuthenticationError when the adapter fails to authenticate."""
    context = OIDCService(
        AuthAdapterNeverAuthenticates(),
        AccessTokenVerifierAlwaysVerifies(),
    )

    with pytest.raises(AuthenticationError):
        context.authenticate_device()


def test_it_returns_tuple_when_adapter_returns_tokens() -> None:
    """It should return OfflineAccessTokens when the adapter returns OfflineAccessTokens."""

    class AuthAdapterReturnsTuple(Auth0Adapter):
        def __init__(self) -> None:
            self.returned = OfflineAccessTokens(access_token="id-token-xyz", refresh_token="refresh-token-xyz")

        def fetch_token_with_device_code(self, device_code: str):
            return self.returned

        def fetch_device_code(self) -> DeviceCodeData:
            return DeviceCodeData(
                verification_uri_complete="https://arnica.aqt.eu/api",
                user_code="BLTT_HPNS",
                device_code="abcde12345",
                interval=0.1,
            )

    adapter = AuthAdapterReturnsTuple()
    context = OIDCService(adapter, AccessTokenVerifierAlwaysVerifies())

    tokens = context.authenticate_device()

    assert tokens == OfflineAccessTokens(access_token="id-token-xyz", refresh_token="refresh-token-xyz")


def test_it_raises_token_validation_error_when_access_token_invalid() -> None:
    """It should raise TokenValidationError when the adapter returns a tuple but the access token is invalid."""

    class AuthAdapterReturnsTuple(Auth0Adapter):
        def __init__(self) -> None:
            self.returned = OfflineAccessTokens(access_token="id-token-xyz", refresh_token="refresh-token-xyz")

        def fetch_token_with_device_code(self, device_code: str):
            return self.returned

        def fetch_device_code(self) -> DeviceCodeData:
            return DeviceCodeData(
                verification_uri_complete="https://arnica.aqt.eu/api",
                user_code="BLTT_HPNS",
                device_code="abcde12345",
                interval=0.1,
            )

    adapter = AuthAdapterReturnsTuple()
    context = OIDCService(adapter, AccessTokenVerifierAlwaysRejects())

    with pytest.raises(TokenValidationError):
        context.authenticate_device()
