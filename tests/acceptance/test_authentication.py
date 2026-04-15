"""Acceptance tests for authentication use cases."""

from __future__ import annotations

import io
import json
from pathlib import Path

from typing_extensions import Protocol
from werkzeug import Request, Response

from aqt_connector import get_access_token, log_in
from aqt_connector._arnica_app import ArnicaApp
from tests.acceptance.conftest import TEST_DEVICE_CLIENT_ID


class JWTFactory(Protocol):
    def __call__(self, audience: str | None = None) -> str: ...


def test_already_authenticated_user_gets_stored_token(
    arnica_app: ArnicaApp, tmp_path: Path, make_jwt: JWTFactory
) -> None:
    """A user with a valid stored token receives it back without calling Auth0."""
    token = make_jwt()
    (tmp_path / "access_token").write_text(token)

    result = log_in(arnica_app, stdout=io.StringIO())

    assert result == token


def test_user_logs_in_with_client_credentials(arnica_app: ArnicaApp, auth_server, make_jwt: JWTFactory) -> None:
    """A user with client credentials configured is authenticated via the CC flow.

    The test server asserts the library sends a correct ``client_credentials``
    grant to ``POST /oauth/token``.
    """
    arnica_app.config.client_id = "my-client-id"
    arnica_app.config.client_secret = "my-client-secret"
    expected_token = make_jwt(audience=arnica_app.config.arnica_url)

    def token_handler(request: Request) -> Response:
        body = request.get_json()
        assert body["grant_type"] == "client_credentials"
        assert body["client_id"] == "my-client-id"
        assert body["client_secret"] == "my-client-secret"
        assert body["audience"] == arnica_app.config.arnica_url
        return Response(
            json.dumps({"access_token": expected_token, "token_type": "Bearer"}),
            content_type="application/json",
        )

    auth_server.expect_ordered_request("/oauth/token", method="POST").respond_with_handler(token_handler)

    result = log_in(arnica_app)

    assert result == expected_token


def test_user_logs_in_via_device_flow(arnica_app: ArnicaApp, auth_server, make_jwt: JWTFactory) -> None:
    """A user without client credentials is authenticated via the device flow.

    The test server asserts the library requests a device code and then polls
    ``POST /oauth/token`` with the correct device-code grant.
    """
    expected_token = make_jwt()

    auth_server.expect_ordered_request("/oauth/device/code", method="POST").respond_with_json(
        {
            "verification_uri_complete": "https://auth.example.com/activate?user_code=TEST-1234",
            "user_code": "TEST-1234",
            "device_code": "test-device-code",
            "interval": 0,
        }
    )

    def device_token_handler(request: Request) -> Response:
        assert request.form["grant_type"] == "urn:ietf:params:oauth:grant-type:device_code"
        assert request.form["device_code"] == "test-device-code"
        assert request.form["client_id"] == TEST_DEVICE_CLIENT_ID
        return Response(
            json.dumps(
                {
                    "id_token": expected_token,
                    "access_token": expected_token,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                }
            ),
            content_type="application/json",
        )

    auth_server.expect_ordered_request("/oauth/token", method="POST").respond_with_handler(device_token_handler)

    result = log_in(arnica_app, stdout=io.StringIO())

    assert result == expected_token


def test_access_token_is_stored_after_login_when_configured(
    arnica_app: ArnicaApp, auth_server, make_jwt: JWTFactory
) -> None:
    """An access token obtained via the CC flow is persisted so subsequent calls skip Auth0."""
    arnica_app.config.client_id = "persist-client-id"
    arnica_app.config.client_secret = "persist-client-secret"
    arnica_app.config.store_access_token = True
    expected_token = make_jwt(audience=arnica_app.config.arnica_url)

    auth_server.expect_ordered_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": expected_token, "token_type": "Bearer"}
    )

    log_in(arnica_app)

    assert get_access_token(arnica_app) == expected_token


def test_access_token_is_not_stored_when_storage_disabled(
    arnica_app: ArnicaApp, auth_server, make_jwt: JWTFactory
) -> None:
    """When storage is disabled the token is not available after logout."""
    arnica_app.config.client_id = "no-persist-client-id"
    arnica_app.config.client_secret = "no-persist-client-secret"
    arnica_app.config.store_access_token = False
    token = make_jwt(audience=arnica_app.config.arnica_url)

    auth_server.expect_ordered_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": token, "token_type": "Bearer"}
    )

    log_in(arnica_app)

    assert get_access_token(arnica_app) is None


def test_get_access_token_returns_none_when_unauthenticated(arnica_app: ArnicaApp) -> None:
    """get_access_token returns None when no token has been stored."""
    assert get_access_token(arnica_app) is None


def test_get_access_token_returns_stored_token(arnica_app: ArnicaApp, tmp_path: Path, make_jwt: JWTFactory) -> None:
    """get_access_token returns a valid token that was previously stored on disk."""
    token = make_jwt()
    (tmp_path / "access_token").write_text(token)

    assert get_access_token(arnica_app) == token
