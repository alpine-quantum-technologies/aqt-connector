from aqt_connector._arnica_app import ArnicaApp
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails


def get_resource_details(app: ArnicaApp, resource_id: str, *, api_token: str | None = None) -> ResourceDetails:
    """Get details for an Arnica resource.

    Args:
        app (ArnicaApp): the application instance.
        resource_id (str): the ID of the resource to query.
        api_token (str | None, optional): a static API token to use for authentication. This will be used
            in place of any token retrieved when logging in. Defaults to None.

    Raises:
        NotAuthenticatedError: if the user is not authenticated and no access token is available.
        RequestError: If there is a network-related error during the request.
        ResourceIDError: If the provided resource ID is invalid or unavailable.
        UnknownServerError: If the Arnica API encounters an internal error or returns an invalid response.
        ValueError: If the provided resource ID is invalid.
        RuntimeError: For any other unexpected errors.

    Returns:
        ResourceDetails: details about the requested resource.
    """
    token = api_token or app.auth_service.get_or_refresh_access_token(app.config.store_access_token)
    if not token:
        raise NotAuthenticatedError("User not authenticated. Please log in.")
    return app.resource_service.get_resource_details(token, resource_id)
