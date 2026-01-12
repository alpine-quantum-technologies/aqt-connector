import sys
import time
from collections.abc import Callable
from typing import Optional, TextIO
from uuid import UUID, uuid4

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig
from aqt_connector._application.jobs import wait_for_final_state
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.job_service import JobService
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.response_bodies.jobs import JobState, RRQueued
from tests.commit.domain.stdout_spy import StdoutSpy


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
        self.given_query_interval_seconds: Optional[float] = None
        self.given_max_attempts: Optional[int] = None
        self.given_out: Optional[TextIO] = None
        self.returned_state = RRQueued()

    def wait_for_result(
        self,
        token: str,
        job_id: UUID,
        *,
        query_interval_seconds: float = 1.0,
        wait: Callable[[float], None] = time.sleep,
        max_attempts: int = 600,
        out: TextIO = sys.stdout,
    ) -> JobState:
        self.given_token = token
        self.requested_job_id = job_id
        self.given_query_interval_seconds = query_interval_seconds
        self.given_max_attempts = max_attempts
        self.given_out = out
        return self.returned_state


def test_it_gets_or_refreshes_token() -> None:
    """It should get or refresh the access token before requesting the job state."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    wait_for_final_state(app, uuid4())

    assert app.auth_service.was_token_fetched
    assert app.auth_service.was_token_stored is app.config.store_access_token


def test_it_uses_fetched_token_to_request_job_state() -> None:
    """It should use the fetched access token to request the job state."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    wait_for_final_state(app, uuid4())

    assert app.job_service.given_token == app.auth_service.fetched_token


def test_it_uses_provided_api_token() -> None:
    """It should use a provided API token to request the job state instead of fetching one."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    provided_token = "provided_api_token"
    wait_for_final_state(app, uuid4(), api_token=provided_token)

    assert app.job_service.given_token == provided_token
    assert not app.auth_service.was_token_fetched


def test_it_raises_if_not_authenticated() -> None:
    """It should raise NotAuthenticatedError if no access token is available."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.auth_service.fetched_token = None  # simulate no token available
    app.job_service = JobServiceSpy()

    with pytest.raises(NotAuthenticatedError, match="User not authenticated. Please log in."):
        wait_for_final_state(app, uuid4())


def test_fetches_job_state_with_correct_parameters() -> None:
    """It should request the job state with the correct parameters."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    job_id = uuid4()
    query_interval_seconds = 2.0
    max_attempts = 300
    stdout = StdoutSpy()
    wait_for_final_state(
        app, job_id, query_interval_seconds=query_interval_seconds, max_attempts=max_attempts, out=stdout
    )

    assert app.job_service.requested_job_id == job_id
    assert app.job_service.given_query_interval_seconds == query_interval_seconds
    assert app.job_service.given_max_attempts == max_attempts
    assert app.job_service.given_out is stdout


def test_it_returns_job_state() -> None:
    """It should return the job state fetched from the job service."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    job_state = wait_for_final_state(app, uuid4())

    assert job_state is app.job_service.returned_state
