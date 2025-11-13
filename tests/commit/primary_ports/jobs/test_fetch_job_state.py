from typing import Optional
from uuid import UUID, uuid4

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig
from aqt_connector._application.jobs import fetch_job_state
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.job_service import JobService
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.response_bodies.jobs import JobState, RRQueued


class AuthServiceSpy(AuthService):
    """A spy for the AuthService to track method calls and parameters."""

    def __init__(self):
        self.was_token_fetched = False
        self.was_token_stored = False
        self.fetched_token = "thisisthetoken"

    def get_or_refresh_access_token(self, store: bool) -> Optional[str]:
        self.was_token_fetched = True
        self.was_token_stored = store
        return self.fetched_token


class JobServiceSpy(JobService):
    """A spy for the JobService to track method calls and parameters."""

    def __init__(self) -> None:
        self.given_token: Optional[str] = None
        self.requested_job_id: Optional[UUID] = None
        self.returned_state = RRQueued()

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        self.given_token = token
        self.requested_job_id = job_id
        return self.returned_state


def test_it_gets_or_refreshes_token() -> None:
    """It should get or refresh the access token before requesting the job state."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    fetch_job_state(app, uuid4())

    assert app.auth_service.was_token_fetched
    assert app.auth_service.was_token_stored is app.config.store_access_token


def test_it_uses_fetched_token_to_request_job_state() -> None:
    """It should use the fetched access token to request the job state."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    fetch_job_state(app, uuid4())

    assert app.job_service.given_token == app.auth_service.fetched_token


def test_it_uses_provided_api_token() -> None:
    """It should use a provided API token to request the job state instead of fetching one."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    provided_token = "provided_api_token"
    fetch_job_state(app, uuid4(), api_token=provided_token)

    assert app.job_service.given_token == provided_token
    assert not app.auth_service.was_token_fetched


def test_it_raises_if_not_authenticated() -> None:
    """It should raise NotAuthenticatedError if no access token is available."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.auth_service.fetched_token = None  # simulate no token available
    app.job_service = JobServiceSpy()

    with pytest.raises(NotAuthenticatedError, match="User not authenticated. Please log in."):
        fetch_job_state(app, uuid4())


def test_it_requests_correct_job_state() -> None:
    """It should request the job state for the correct job ID."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    job_id = uuid4()
    fetch_job_state(app, job_id)

    assert app.job_service.requested_job_id == job_id


def test_it_returns_job_state() -> None:
    """It should return the job state fetched from the job service."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    job_state = fetch_job_state(app, uuid4())

    assert job_state is app.job_service.returned_state
