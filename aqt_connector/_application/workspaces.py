from aqt_connector._arnica_app import ArnicaApp
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.response_bodies.workspaces import Workspace


def get_workspaces(app: ArnicaApp, *, api_token: str | None = None) -> list[Workspace]:
    """Get the workspaces available to the user.

    Args:
        app (ArnicaApp): the application instance.
        api_token (str | None, optional): a static API token to use for authentication. This will be used
            in place of any token retrieved when logging in. Defaults to None.

    Raises:
        NotAuthenticatedError: if the user is not authenticated and no access token is available.
        RequestError: If there is a network-related error during the request.
        UnknownServerError: If the Arnica API encounters an internal error or returns an invalid response.
        RuntimeError: For any other unexpected errors.

    Returns:
        list[Workspace]: the workspaces available to the user.
    """
    token = api_token or app.auth_service.get_or_refresh_access_token(app.config.store_access_token)
    if not token:
        raise NotAuthenticatedError("User not authenticated. Please log in.")
    return app.workspace_service.get_workspaces(token)
