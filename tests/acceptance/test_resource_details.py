"""Acceptance tests for the resource details use case."""

from __future__ import annotations

from datetime import datetime

import pytest
from pytest_httpserver import HTTPServer

from aqt_connector import ArnicaApp, get_resource_details
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.resources import ResourceStatus, ResourceType
from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails
from tests.acceptance.conftest import JWTFactory

RESOURCE_ID = "resource_a"


def test_get_resource_details_returns_resource(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """get_resource_details returns the resource details from Arnica."""
    api_token = make_jwt()
    expected_details = ResourceDetails(
        id=RESOURCE_ID,
        name="Resource A",
        type=ResourceType.SIMULATOR,
        status=ResourceStatus.ONLINE,
        available_qubits=5,
        status_updated_at=datetime(2026, 1, 1),
    )

    arnica_server.expect_ordered_request(
        f"/v1/resources/{RESOURCE_ID}",
        method="GET",
        headers={"Authorization": f"Bearer {api_token}"},
    ).respond_with_data(expected_details.model_dump_json(), content_type="application/json")

    details = get_resource_details(arnica_app, RESOURCE_ID, api_token=api_token)

    assert details == expected_details


def test_get_resource_details_raises_not_authenticated_when_no_token(arnica_app: ArnicaApp) -> None:
    """get_resource_details raises NotAuthenticatedError when no access token is available."""
    with pytest.raises(NotAuthenticatedError):
        get_resource_details(arnica_app, RESOURCE_ID)
