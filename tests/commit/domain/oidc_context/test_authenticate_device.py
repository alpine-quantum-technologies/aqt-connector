from io import StringIO

import pytest

from aqt_connector._data_types import DeviceCodeData
from aqt_connector._domain.oidc_context import OIDCContext
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier
from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter
from aqt_connector.exceptions import AuthenticationError, TokenValidationError


class AuthAdapterSpyAlwaysAuthenticatesImmediately(Auth0Adapter):
    def __init__(self) -> None:
        self.device_access_token = "this-is-the-device-token"
        self.device_code_data = DeviceCodeData(
            verification_uri_complete="https://arnica.aqt.eu/api",
            user_code="BLTT_HPNS",
            device_code="abcde12345",
            interval=5,
        )

    def fetch_token_with_device_code(self, device_code: str) -> str | None:
        self.used_device_code = device_code
        return self.device_access_token

    def fetch_device_code(self) -> DeviceCodeData:
        return self.device_code_data


class AuthAdapterPollingSpy(Auth0Adapter):
    def __init__(self) -> None:
        self.access_token = "this-is-the-device-token"
        self.token_poll_count = 0

    def fetch_token_with_device_code(self, device_code: str) -> str | None:
        self.token_poll_count += 1
        if self.token_poll_count > 2:
            return self.access_token
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

    def fetch_token_with_device_code(self, device_code: str) -> str | None:
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
    def __init__(self, initial_value: str | None = "", newline: str | None = "\n") -> None:
        self.output: list[str] = []
        super().__init__(initial_value, newline)

    def write(self, s):
        self.output.append(s)
        return super().write(s)

    def writelines(self, lines):
        self.output += lines
        return super().writelines(lines)


def test_it_displays_the_verification_uri_and_user_code() -> None:
    auth_adapter = AuthAdapterSpyAlwaysAuthenticatesImmediately()
    context = OIDCContext(
        auth_adapter,
        AccessTokenVerifierAlwaysVerifies(),
    )
    stdout_spy = StdoutSpy()

    context.authenticate_device(out=stdout_spy)

    assert any(auth_adapter.device_code_data.verification_uri_complete in output for output in stdout_spy.output)
    assert any(auth_adapter.device_code_data.user_code in output for output in stdout_spy.output)


def test_it_displays_a_qr_code_for_the_verification_uri() -> None:
    auth_adapter = AuthAdapterSpyAlwaysAuthenticatesImmediately()
    context = OIDCContext(
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
    auth_adapter = AuthAdapterPollingSpy()
    context = OIDCContext(
        auth_adapter,
        AccessTokenVerifierAlwaysVerifies(),
    )

    retrieved_token = context.authenticate_device()

    assert retrieved_token == auth_adapter.access_token


def test_it_raises_error_when_id_token_invalid() -> None:
    context = OIDCContext(
        AuthAdapterSpyAlwaysAuthenticatesImmediately(),
        AccessTokenVerifierAlwaysRejects(),
    )

    with pytest.raises(TokenValidationError):
        context.authenticate_device()


def test_it_raises_error_when_authentication_fails() -> None:
    context = OIDCContext(
        AuthAdapterNeverAuthenticates(),
        AccessTokenVerifierAlwaysVerifies(),
    )

    with pytest.raises(AuthenticationError):
        context.authenticate_device()
