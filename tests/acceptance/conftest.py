"""Shared fixtures for acceptance tests.

All external calls made by the real library code are routed to two lightweight
local HTTP servers started by pytest — a fake Auth0 server and a fake Arnica
API.
"""

from __future__ import annotations

import json
import time
from collections.abc import Generator
from pathlib import Path
from uuid import UUID

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from pytest_httpserver import HTTPServer
from typing_extensions import Protocol

from aqt_connector import ArnicaApp, ArnicaConfig
from aqt_connector.models.arnica.jobs import BasicJobMetadata
from aqt_connector.models.arnica.response_bodies.jobs import JobState, ResultResponse

TEST_KID = "acceptance-test-key"
TEST_DEVICE_CLIENT_ID = "test-device-client-id"


class JWTFactory(Protocol):
    def __call__(self, audience: str = ...) -> str: ...


@pytest.fixture(scope="session")
def rsa_private_key() -> rsa.RSAPrivateKey:
    """RSA-2048 key pair shared across all tests in the session."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def jwks_document(rsa_private_key: rsa.RSAPrivateKey) -> dict:
    """JWKS document exposing the public half of the test RSA key.

    Produced via PyJWT so it round-trips with auth0-python's
    ``JwksFetcher._parse_jwks``, which also uses ``RSAAlgorithm.from_jwk``.
    """
    public_key = rsa_private_key.public_key()
    jwk = json.loads(pyjwt.algorithms.RSAAlgorithm.to_jwk(public_key))
    jwk.update({"kid": TEST_KID, "use": "sig", "alg": "RS256"})
    return {"keys": [jwk]}


@pytest.fixture()
def auth_server(jwks_document: dict) -> Generator[HTTPServer, None, None]:
    """Minimal fake Auth0 server.

    Permanently serves ``/.well-known/jwks.json`` so that
    ``AccessTokenVerifier`` can validate any token minted by ``make_jwt``.
    Individual tests may register additional routes (e.g. ``/oauth/token``)
    before exercising the library.
    """
    server = HTTPServer(host="127.0.0.1")
    server.start()
    server.expect_request("/.well-known/jwks.json").respond_with_json(jwks_document)
    yield server
    try:
        server.check_assertions()
    finally:
        server.stop()


@pytest.fixture()
def arnica_server() -> Generator[HTTPServer, None, None]:
    """Minimal fake Arnica REST API server.

    Individual tests register routes (e.g. ``/v1/result/{job_id}``) before
    exercising the library.
    """
    server = HTTPServer(host="127.0.0.1")
    server.start()
    yield server
    try:
        server.check_assertions()
    finally:
        server.stop()


@pytest.fixture()
def make_jwt(rsa_private_key: rsa.RSAPrivateKey, auth_server: HTTPServer) -> JWTFactory:
    """Factory that mints RS256 JWTs compatible with the local test servers.

    Tokens are signed with ``rsa_private_key``, whose public counterpart is
    served at ``auth_server``'s JWKS endpoint, so ``AccessTokenVerifier``
    accepts them without any modification to the library code.

    Usage::

        token = make_jwt()                            # aud = TEST_DEVICE_CLIENT_ID
        token = make_jwt(audience="http://...")       # custom audience
    """
    issuer = f"http://127.0.0.1:{auth_server.port}/"

    def _factory(audience: str = TEST_DEVICE_CLIENT_ID) -> str:
        now = int(time.time())
        return pyjwt.encode(
            {
                "iss": issuer,
                "sub": "acceptance-test|user",
                "aud": audience,
                "iat": now,
                "exp": now + 3600,
            },
            rsa_private_key,
            algorithm="RS256",
            headers={"kid": TEST_KID},
        )

    return _factory


@pytest.fixture()
def arnica_app(auth_server: HTTPServer, arnica_server: HTTPServer, tmp_path: Path) -> Generator[ArnicaApp, None, None]:
    """``ArnicaApp`` whose external calls are routed to the local test servers.

    All production library code (application, domain, infrastructure) runs
    unchanged; only the server URLs inside ``ArnicaConfig`` are overridden so
    that outbound HTTP connects to the in-process test servers instead of the
    real Auth0 and Arnica services.
    """
    issuer = f"http://127.0.0.1:{auth_server.port}/"
    arnica_base = f"http://127.0.0.1:{arnica_server.port}"

    config = ArnicaConfig(app_dir=tmp_path)
    config.arnica_url = arnica_base
    config.oidc_config.issuer = issuer
    config.oidc_config.jwks_url = f"http://127.0.0.1:{auth_server.port}/.well-known/jwks.json"
    config.oidc_config.audience = arnica_base
    config.oidc_config.device_client_id = TEST_DEVICE_CLIENT_ID

    with ArnicaApp(config) as app:
        yield app


def job_state_response_json(job_id: UUID, state: JobState) -> str:
    """Serialise a ``JobState`` into the JSON body the Arnica API would return.

    Uses the library's own Pydantic models to guarantee the exact wire format.
    """
    metadata = BasicJobMetadata(
        job_id=job_id,
        resource_id="test-resource",
        workspace_id="test-workspace",
    )
    return ResultResponse(job=metadata, response=state).model_dump_json()
