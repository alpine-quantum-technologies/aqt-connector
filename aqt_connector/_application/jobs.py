import sys
from typing import Optional, TextIO
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


def wait_for_final_state(
    app: ArnicaApp,
    job_id: UUID,
    *,
    api_token: Optional[str] = None,
    query_interval_seconds: float = 1.0,
    max_attempts: int = 600,
    out: TextIO = sys.stdout,
) -> JobState:  # TODO: narrow down type to finished states only
    """Wait for a job to reach a final state.

    Polls the job state until it reaches a finished state or the maximum number of attempts is reached. A finished
    state includes jobs that have succeeded, failed, or been cancelled.

    Args:
        app (ArnicaApp): the application instance.
        job_id (UUID): the unique identifier of the job.
        api_token (str | None, optional): a static API token to use for authentication. This will be used
            in place of any token retrieved when logging in. Defaults to None.
        query_interval_seconds (float, optional): The base interval between job state queries. Defaults to 1.0.
        max_attempts (int, optional): The maximum number of attempts to query the job state. Defaults to 600.
        out (TextIO, optional): text stream to send output to. Defaults to sys.stdout.

    Raises:
        NotAuthenticatedError: if the user is not authenticated and no access token is available.
        NotAuthenticatedError: If the provided token is invalid or expired.
        JobNotFoundError: If the job with the specified ID does not exist.
        InvalidJobIDError: If the provided job ID is not valid.
        UnknownServerError: If the Arnica API encounters an internal error.
        RuntimeError: For any other unexpected errors.
        TimeoutError: If the maximum wait time is exceeded.

    Returns:
        JobState: the final state of the job.
    """
    token = api_token or app.auth_service.get_or_refresh_access_token(app.config.store_access_token)
    if not token:
        raise NotAuthenticatedError("User not authenticated. Please log in.")

    # User-managed token provided, don't attempt to refresh
    if api_token:
        return app.job_service.wait_for_result(
            token,
            job_id,
            query_interval_seconds=query_interval_seconds,
            max_attempts=max_attempts,
            out=out,
        )

    # Token to refresh as needed
    while True:
        try:
            return app.job_service.wait_for_result(
                token,
                job_id,
                query_interval_seconds=query_interval_seconds,
                max_attempts=max_attempts,
                out=out,
            )
        except NotAuthenticatedError:
            refreshed = app.auth_service.get_or_refresh_access_token(app.config.store_access_token)
            if not refreshed or refreshed == token:
                raise
            token = refreshed
