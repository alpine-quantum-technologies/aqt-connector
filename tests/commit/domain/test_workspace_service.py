from aqt_connector._domain.workspace_service import WorkspaceService
from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.models.arnica.response_bodies.workspaces import Workspace


class ArnicaAdapterSpy(ArnicaAdapter):
    def __init__(self) -> None:
        self.get_workspaces_called_with: list[str] = []
        self.returned_workspaces = [
            Workspace(id="workspace_a", accepting_job_submissions=True, jobs_being_processed=False, resources=[])
        ]

    def get_workspaces(self, token: str) -> list[Workspace]:
        self.get_workspaces_called_with.append(token)
        return self.returned_workspaces


def test_it_passes_token_to_adapter() -> None:
    """It should pass the given token to the adapter."""
    adapter = ArnicaAdapterSpy()

    WorkspaceService(adapter).get_workspaces("some-token")

    assert adapter.get_workspaces_called_with == ["some-token"]


def test_it_returns_adapter_result() -> None:
    """It should return the workspaces returned by the adapter."""
    adapter = ArnicaAdapterSpy()

    workspaces = WorkspaceService(adapter).get_workspaces("some-token")

    assert workspaces is adapter.returned_workspaces
