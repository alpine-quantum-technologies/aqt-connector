import pytest

from aqt_connector import ArnicaApp, ArnicaConfig
from aqt_connector._application.workspaces import get_workspaces
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.workspace_service import WorkspaceService
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.resources import ResourceType
from aqt_connector.models.arnica.response_bodies.resources import WorkspaceResource
from aqt_connector.models.arnica.response_bodies.workspaces import Workspace


class AuthServiceSpy(AuthService):
    def __init__(self) -> None:
        self.was_token_fetched = False
        self.was_token_stored = False
        self.fetched_token: str | None = "thisisthetoken"

    def get_or_refresh_access_token(self, store: bool, *, force_refresh: bool = False) -> str | None:
        self.was_token_fetched = True
        self.was_token_stored = store
        return self.fetched_token


class WorkspaceServiceSpy(WorkspaceService):
    def __init__(self) -> None:
        self.given_token: str | None = None
        self.returned_workspaces = [
            Workspace(
                id="workspace_a",
                accepting_job_submissions=True,
                jobs_being_processed=False,
                resources=[WorkspaceResource(id="device_a", name="Device A", type=ResourceType.DEVICE)],
            )
        ]

    def get_workspaces(self, token: str) -> list[Workspace]:
        self.given_token = token
        return self.returned_workspaces


@pytest.fixture
def app():
    application = ArnicaApp(ArnicaConfig())
    try:
        yield application
    finally:
        application.close()


def test_it_gets_or_refreshes_token(app: ArnicaApp) -> None:
    """It should get or refresh the access token before requesting workspaces."""
    app.auth_service = AuthServiceSpy()
    app.workspace_service = WorkspaceServiceSpy()

    get_workspaces(app)

    assert app.auth_service.was_token_fetched
    assert app.auth_service.was_token_stored is app.config.store_access_token


def test_it_uses_fetched_token_to_request_workspaces(app: ArnicaApp) -> None:
    """It should use the fetched access token to request workspaces."""
    app.auth_service = AuthServiceSpy()
    app.workspace_service = WorkspaceServiceSpy()

    get_workspaces(app)

    assert app.workspace_service.given_token == app.auth_service.fetched_token


def test_it_uses_provided_api_token(app: ArnicaApp) -> None:
    """It should use a provided API token instead of fetching one."""
    app.auth_service = AuthServiceSpy()
    app.workspace_service = WorkspaceServiceSpy()

    get_workspaces(app, api_token="provided_api_token")

    assert app.workspace_service.given_token == "provided_api_token"
    assert not app.auth_service.was_token_fetched


def test_it_raises_if_not_authenticated(app: ArnicaApp) -> None:
    """It should raise NotAuthenticatedError when no access token is available."""
    app.auth_service = AuthServiceSpy()
    app.auth_service.fetched_token = None
    service = WorkspaceServiceSpy()
    app.workspace_service = service

    with pytest.raises(NotAuthenticatedError, match="User not authenticated. Please log in."):
        get_workspaces(app)

    assert service.given_token is None


def test_it_returns_workspaces(app: ArnicaApp) -> None:
    """It should return the workspaces fetched from the service."""
    app.auth_service = AuthServiceSpy()
    app.workspace_service = WorkspaceServiceSpy()

    workspaces = get_workspaces(app)

    assert workspaces is app.workspace_service.returned_workspaces
