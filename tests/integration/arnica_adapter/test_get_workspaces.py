import httpx
import pytest

from aqt_connector.exceptions import NotAuthenticatedError, RequestError, UnknownServerError
from aqt_connector.models.arnica.resources import ResourceType
from aqt_connector.models.arnica.response_bodies.resources import WorkspaceResource
from aqt_connector.models.arnica.response_bodies.workspaces import Workspace
from tests.integration.arnica_adapter.conftest import ArnicaAdapterFactory


@pytest.mark.simulated
def test_it_gets_workspaces_successfully(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should request workspaces with bearer authentication and parse the response."""
    expected_workspaces = _workspaces()

    def assert_request(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/workspaces"
        assert request.headers["Authorization"] == "Bearer dummy_token"
        return httpx.Response(
            status_code=200, json=[workspace.model_dump(mode="json") for workspace in expected_workspaces]
        )

    workspaces = make_arnica_adapter(assert_request).get_workspaces("dummy_token")

    assert workspaces == expected_workspaces


@pytest.mark.simulated
def test_it_accepts_empty_workspace_list(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should return an empty list when no workspaces are available."""
    adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=200, json=[]))

    assert adapter.get_workspaces("dummy_token") == []


@pytest.mark.simulated
def test_it_raises_not_authenticated_error_on_401(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise NotAuthenticatedError when the API returns 401 Unauthorized."""
    adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=401))

    with pytest.raises(NotAuthenticatedError):
        adapter.get_workspaces("invalid_token")


@pytest.mark.simulated
def test_it_raises_unknown_server_error_on_500(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise UnknownServerError when the API returns 500 Internal Server Error."""
    adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=500))

    with pytest.raises(UnknownServerError):
        adapter.get_workspaces("dummy_token")


@pytest.mark.simulated
def test_it_raises_network_error_on_request_error(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise RequestError when a network error occurs."""

    def raise_connect_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection error", request=request)

    adapter = make_arnica_adapter(raise_connect_error)

    with pytest.raises(RequestError):
        adapter.get_workspaces("dummy_token")


@pytest.mark.simulated
@pytest.mark.parametrize(
    "body",
    [
        [{"id": "workspace_a"}],
        [
            {
                "id": "workspace_a",
                "accepting_job_submissions": True,
                "jobs_being_processed": False,
                "resources": [{"id": "device_a", "name": "Device A", "type": "invalid"}],
            }
        ],
    ],
)
def test_it_raises_unknown_server_error_on_invalid_response(
    make_arnica_adapter: ArnicaAdapterFactory, body: object
) -> None:
    """It should raise UnknownServerError when workspace data is invalid."""
    adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=200, json=body))

    with pytest.raises(UnknownServerError):
        adapter.get_workspaces("dummy_token")


@pytest.mark.simulated
def test_it_raises_unknown_server_error_on_malformed_json(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise UnknownServerError when the response contains malformed JSON."""
    adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=200, content=b"not-json"))

    with pytest.raises(UnknownServerError):
        adapter.get_workspaces("dummy_token")


@pytest.mark.simulated
def test_it_raises_runtime_error_on_unexpected_status(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise RuntimeError when the API returns an unexpected status."""
    adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=418))

    with pytest.raises(RuntimeError):
        adapter.get_workspaces("dummy_token")


def _workspaces() -> list[Workspace]:
    return [
        Workspace(
            id="workspace_a",
            accepting_job_submissions=True,
            jobs_being_processed=False,
            resources=[WorkspaceResource(id="device_a", name="Device A", type=ResourceType.DEVICE)],
        ),
        Workspace(id="workspace_b", accepting_job_submissions=False, jobs_being_processed=True, resources=[]),
    ]
