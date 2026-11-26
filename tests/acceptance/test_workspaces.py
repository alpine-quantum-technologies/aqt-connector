"""Acceptance tests for the workspace-list use case."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from aqt_connector import ArnicaApp, get_workspaces
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.resources import ResourceType
from aqt_connector.models.arnica.response_bodies.resources import WorkspaceResource
from aqt_connector.models.arnica.response_bodies.workspaces import Workspace
from tests.acceptance.conftest import JWTFactory

pytestmark = pytest.mark.simulated


def test_get_workspaces_returns_server_workspaces(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """It should return the workspaces received from Arnica."""
    api_token = make_jwt()
    expected = [
        Workspace(
            id="workspace_a",
            accepting_job_submissions=True,
            jobs_being_processed=False,
            resources=[WorkspaceResource(id="device_a", name="Device A", type=ResourceType.DEVICE)],
        ),
        Workspace(id="workspace_b", accepting_job_submissions=False, jobs_being_processed=True, resources=[]),
    ]
    arnica_server.expect_ordered_request(
        "/v1/workspaces", method="GET", headers={"Authorization": f"Bearer {api_token}"}
    ).respond_with_data(
        "[" + ",".join(workspace.model_dump_json() for workspace in expected) + "]",
        content_type="application/json",
    )

    assert get_workspaces(arnica_app, api_token=api_token) == expected


def test_get_workspaces_accepts_empty_list(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """It should return an empty list when no workspaces are available."""
    api_token = make_jwt()
    arnica_server.expect_ordered_request("/v1/workspaces", method="GET").respond_with_data(
        "[]", content_type="application/json"
    )

    assert get_workspaces(arnica_app, api_token=api_token) == []


def test_get_workspaces_uses_stored_token(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, tmp_path: Path, make_jwt: JWTFactory
) -> None:
    """It should authenticate with the stored access token."""
    api_token = make_jwt()
    (tmp_path / "access_token").write_text(api_token)
    arnica_server.expect_ordered_request(
        "/v1/workspaces", method="GET", headers={"Authorization": f"Bearer {api_token}"}
    ).respond_with_data("[]", content_type="application/json")

    assert get_workspaces(arnica_app) == []


def test_get_workspaces_raises_when_not_authenticated(arnica_app: ArnicaApp) -> None:
    """It should raise NotAuthenticatedError when no access token is available."""
    with pytest.raises(NotAuthenticatedError):
        get_workspaces(arnica_app)


def test_get_workspaces_raises_when_server_rejects_token(arnica_app: ArnicaApp, arnica_server: HTTPServer) -> None:
    """It should raise NotAuthenticatedError when Arnica rejects the token."""
    arnica_server.expect_ordered_request(
        "/v1/workspaces", method="GET", headers={"Authorization": "Bearer rejected-token"}
    ).respond_with_data("", status=401)

    with pytest.raises(NotAuthenticatedError):
        get_workspaces(arnica_app, api_token="rejected-token")
