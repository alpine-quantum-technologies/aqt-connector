from typing import Optional
from uuid import UUID

from aqt_connector._arnica_app import ArnicaApp
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.response_bodies.jobs import JobState


def fetch_job_state(app: ArnicaApp, job_id: UUID, *, api_token: Optional[str] = None) -> JobState:
    """Fetch the state of a job.

    Args:
        app (ArnicaApp): the application instance.
        job_id (UUID): the unique identifier of the job.
        api_token (str | None, optional): a static API token to use for authentication. This will be used
            in place of any token retrieved when logging in. Defaults to None.

    Raises:
        NotAuthenticatedError: if the user is not authenticated and no access token is available.
        RequestError: If there is a network-related error during the request.
        NotAuthenticatedError: If the provided token is invalid or expired.
        JobNotFoundError: If the job with the specified ID does not exist.
        InvalidJobIDError: If the provided job ID is not valid.
        UnknownServerError: If the Arnica API encounters an internal error.
        RuntimeError: For any other unexpected errors.

    Returns:
        JobState: the state of the job.
    """
    token = api_token or app.auth_service.get_or_refresh_access_token(app.config.store_access_token)
    if not token:
        raise NotAuthenticatedError("User not authenticated. Please log in.")
    return app.job_service.fetch_job_state(token, job_id)
