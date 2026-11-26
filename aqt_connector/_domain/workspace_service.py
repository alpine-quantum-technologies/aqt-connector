from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.models.arnica.response_bodies.workspaces import Workspace


class WorkspaceService:
    def __init__(self, arnica: ArnicaAdapter) -> None:
        """Initialises the WorkspaceService with the given ArnicaAdapter.

        Args:
            arnica (ArnicaAdapter): The Arnica adapter to use for fetching workspaces.
        """
        self.arnica = arnica

    def get_workspaces(self, token: str) -> list[Workspace]:
        """Gets the workspaces available to the user using the provided token.

        Args:
            token (str): The authentication token to use.

        Returns:
            list[Workspace]: The workspaces available to the user.
        """
        return self.arnica.get_workspaces(token)
