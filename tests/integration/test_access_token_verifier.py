import base64
import json
import os
from typing import Final

import httpx
import pytest

from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier, AccessTokenVerifierConfig
from aqt_connector.exceptions import TokenValidationError

TEST_TENANT_URL: Final = os.getenv("AUTH0_TEST_TENANT_URL", "")
TEST_AUDIENCE: Final = os.getenv("AUTH0_TEST_CLIENT_CREDENTIALS_AUDIENCE", "")
TEST_CLIENT_ID: Final = os.getenv("AUTH0_TEST_CLIENT_CREDENTIALS_CLIENT_ID", "")
TEST_CLIENT_SECRET: Final = os.getenv("AUTH0_TEST_CLIENT_CREDENTIALS_CLIENT_SECRET", "")


@pytest.fixture(scope="session")
def access_token() -> str:
    token_payload = {
        "client_id": TEST_CLIENT_ID,
        "client_secret": TEST_CLIENT_SECRET,
        "audience": TEST_AUDIENCE,
        "grant_type": "client_credentials",
    }
    token_response = httpx.post(f"{TEST_TENANT_URL}/oauth/token", json=token_payload).raise_for_status()
    token_data = token_response.json()
    return token_data["access_token"]


def test_it_verifies_the_access_token_if_token_has_any_allowed_audience(access_token: str) -> None:
    config = AccessTokenVerifierConfig(
        f"{TEST_TENANT_URL}/.well-known/jwks.json",
        f"{TEST_TENANT_URL}/",
        allowed_audiences=[TEST_AUDIENCE],
    )

    verifier = AccessTokenVerifier(config)

    assert verifier.verify_access_token(access_token)


def test_it_rejects_invalid_token(access_token: str) -> None:
    config = AccessTokenVerifierConfig(
        "https://arnica-testing.eu.auth0.com/.well-known/jwks.json",
        f"{TEST_TENANT_URL}/",
        allowed_audiences=[TEST_AUDIENCE],
    )

    (header, payload_e, sig) = access_token.split(".")
    payload_e += "=" * (-len(payload_e) % 4)
    payload_j = base64.urlsafe_b64decode(payload_e).decode()
    payload = json.loads(payload_j)
    payload["picture"] = "https://tinyurl.com/35nbecup"
    modified_access_token = f"{header}.{payload}.{sig}"

    verifier = AccessTokenVerifier(config)

    with pytest.raises(TokenValidationError):
        verifier.verify_access_token(modified_access_token)


def test_it_rejects_token_if_jwks_invalid(access_token: str) -> None:
    config = AccessTokenVerifierConfig(
        f"{TEST_TENANT_URL}/.well-known/openid-configuration",
        f"{TEST_TENANT_URL}/",
        allowed_audiences=[TEST_AUDIENCE],
    )

    verifier = AccessTokenVerifier(config)

    with pytest.raises(TokenValidationError):
        verifier.verify_access_token(access_token)


def test_it_rejects_token_if_key_not_in_jwks(access_token: str) -> None:
    config = AccessTokenVerifierConfig(
        "https://arnica.eu.auth0.com/.well-known/jwks.json",
        f"{TEST_TENANT_URL}/",
        allowed_audiences=[TEST_AUDIENCE],
    )

    verifier = AccessTokenVerifier(config)

    with pytest.raises(TokenValidationError):
        verifier.verify_access_token(access_token)


def test_it_rejects_token_with_no_allowed_audience(access_token: str) -> None:
    config = AccessTokenVerifierConfig(
        f"{TEST_TENANT_URL}/.well-known/jwks.json",
        f"{TEST_TENANT_URL}/",
        allowed_audiences=["https://arnica.aqt.eu/api"],
    )

    verifier = AccessTokenVerifier(config)

    with pytest.raises(TokenValidationError):
        verifier.verify_access_token(access_token)


def test_it_rejects_token_from_incorrect_issuer(access_token: str) -> None:
    config = AccessTokenVerifierConfig(
        f"{TEST_TENANT_URL}/.well-known/jwks.json",
        "https://arnica.eu.auth0.com",
        allowed_audiences=[TEST_AUDIENCE],
    )

    verifier = AccessTokenVerifier(config)

    with pytest.raises(TokenValidationError):
        verifier.verify_access_token(access_token)
