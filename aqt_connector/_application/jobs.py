from uuid import UUID

from aqt_connector._arnica_app import ArnicaApp
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.response_bodies.jobs import JobState


def fetch_job_state(app: ArnicaApp, job_id: UUID) -> JobState:
    """Fetch the state of a job.

    Args:
        app (ArnicaApp): the application instance.
        job_id (UUID): the unique identifier of the job.

    Raises:
        NotAuthenticatedError: if the user is not authenticated and no access token is available.

    Returns:
        JobState: the state of the job.
    """
    token = app.auth_service.get_or_refresh_access_token(app.config.store_access_token)
    if not token:
        raise NotAuthenticatedError("User not authenticated. Please log in.")
    return app.job_service.fetch_job_state(token, job_id)
