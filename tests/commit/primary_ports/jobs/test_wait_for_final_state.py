import sys
import time
from collections.abc import Callable
from typing import TextIO, cast
from uuid import UUID, uuid4

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig
from aqt_connector._application.jobs import wait_for_final_state
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.job_service import JobService
from aqt_connector.exceptions import InvalidJobIDError, JobNotFoundError, NotAuthenticatedError, UnknownServerError
from aqt_connector.models.arnica.response_bodies.jobs import (
    FinalJobState,
    JobState,
    NonFinalJobState,
    RRCancelled,
    RROngoing,
    RRQueued,
)
from tests.commit.domain.stdout_spy import StdoutSpy


class AuthServiceSpy(AuthService):
    """A spy for the AuthService to track method calls and parameters."""

    def __init__(self) -> None:
        self.token_fetch_count = 0
        self.force_refresh_count = 0
        self.was_token_stored = False
        self.fetched_token: str | None = "thisisthetoken"
        self.refreshed_token: str | None = "this-is-the-refreshed-token"

    def get_or_refresh_access_token(self, store: bool, *, force_refresh: bool = False) -> str | None:
        self.token_fetch_count += 1
        self.was_token_stored = store
        if force_refresh:
            self.force_refresh_count += 1
            return self.refreshed_token
        return self.fetched_token


class JobServiceSpy(JobService):
    """A spy for the JobService to track method calls and parameters."""

    def __init__(self) -> None:
        self.given_token: str | None = None
        self.requested_job_id: UUID | None = None
        self.given_query_interval_seconds: float | None = None
        self.given_max_attempts: int | None = None
        self.given_out: TextIO | None = None
        self.refresh_callback: Callable[[], str | None] | None = None
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
        report_state: Callable[[NonFinalJobState], None] | None = None,
        refresh_token: Callable[[], str | None] | None = None,
    ) -> FinalJobState:
        self.given_token = token
        self.requested_job_id = job_id
        self.given_query_interval_seconds = query_interval_seconds
        self.given_max_attempts = max_attempts
        self.given_out = out
        self.refresh_callback = refresh_token
        return cast(FinalJobState, self.returned_state)


def test_it_gets_or_refreshes_token_before_requesting_job_state() -> None:
    """It should get or refresh the access token before requesting the job state."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    wait_for_final_state(app, uuid4())

    assert app.auth_service.token_fetch_count == 1
    assert app.auth_service.was_token_stored is app.config.store_access_token


def test_it_uses_fetched_token_to_request_job_state() -> None:
    """It should use the fetched access token to request the job state."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    wait_for_final_state(app, uuid4())

    assert app.job_service.given_token == app.auth_service.fetched_token


def test_it_uses_provided_api_token_and_does_not_fetch_one() -> None:
    """It should use a provided API token to request the job state instead of fetching one."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    provided_token = "provided_api_token"
    wait_for_final_state(app, uuid4(), api_token=provided_token)

    assert app.job_service.given_token == provided_token
    assert app.auth_service.token_fetch_count == 0


def test_it_raises_if_no_token_available_initially() -> None:
    """It should raise NotAuthenticatedError if no access token is available."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.auth_service.fetched_token = None  # simulate no token available
    app.job_service = JobServiceSpy()

    with pytest.raises(NotAuthenticatedError, match="User not authenticated. Please log in."):
        wait_for_final_state(app, uuid4())


@pytest.mark.parametrize("max_attempts", [0, -1])
def test_it_rejects_invalid_max_attempts_before_authentication(max_attempts: int) -> None:
    """It should reject invalid max attempts before attempting authentication."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    with pytest.raises(ValueError, match="max_attempts must be at least 1"):
        wait_for_final_state(app, uuid4(), max_attempts=max_attempts)

    assert app.auth_service.token_fetch_count == 0
    assert app.job_service.requested_job_id is None


@pytest.mark.parametrize("query_interval_seconds", [-0.1, float("nan"), float("inf"), float("-inf")])
def test_it_rejects_invalid_polling_intervals_before_authentication(query_interval_seconds: float) -> None:
    """It should reject an invalid polling interval before attempting authentication."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    with pytest.raises(ValueError, match="query_interval_seconds must be finite and non-negative"):
        wait_for_final_state(app, uuid4(), query_interval_seconds=query_interval_seconds)

    assert app.auth_service.token_fetch_count == 0
    assert app.job_service.requested_job_id is None


def test_passes_query_interval_max_attempts_and_out_to_job_service() -> None:
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


def test_it_returns_job_state_from_job_service() -> None:
    """It should return the job state fetched from the job service."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    job_state = wait_for_final_state(app, uuid4())

    assert job_state is app.job_service.returned_state


def test_it_passes_forced_refresh_callback_for_managed_token() -> None:
    """Managed polling should receive a callback that forces refresh through AuthService."""

    class JobServiceDouble(JobService):
        def __init__(self) -> None:
            pass

        def wait_for_result(
            self,
            token: str,
            job_id: UUID,
            *,
            query_interval_seconds: float = 1.0,
            wait: Callable[[float], None] = time.sleep,
            max_attempts: int = 600,
            out: TextIO = sys.stdout,
            report_state: Callable[[NonFinalJobState], None] | None = None,
            refresh_token: Callable[[], str | None] | None = None,
        ) -> FinalJobState:
            self.refresh_callback = refresh_token
            return RRCancelled()

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceDouble()

    final_state = wait_for_final_state(app, uuid4())

    assert final_state == RRCancelled()
    assert app.job_service.refresh_callback is not None
    assert app.job_service.refresh_callback() == app.auth_service.refreshed_token
    assert app.auth_service.force_refresh_count == 1


def test_it_does_not_attempt_refresh_when_static_api_token_and_not_authenticated_error_occurs() -> None:
    """It should not attempt to refresh the token when a user-managed API token is provided."""

    class JobServiceDouble(JobServiceSpy):
        def wait_for_result(
            self,
            token: str,
            job_id: UUID,
            *,
            query_interval_seconds: float = 1.0,
            wait: Callable[[float], None] = time.sleep,
            max_attempts: int = 600,
            out: TextIO = sys.stdout,
            report_state: Callable[[NonFinalJobState], None] | None = None,
            refresh_token: Callable[[], str | None] | None = None,
        ) -> FinalJobState:
            self.received_refresh_callback = refresh_token
            raise NotAuthenticatedError

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceDouble()

    with pytest.raises(NotAuthenticatedError):
        wait_for_final_state(app, uuid4(), api_token="provided_token")

    assert app.auth_service.token_fetch_count == 0
    assert app.job_service.received_refresh_callback is None


@pytest.mark.parametrize(
    "exception_type",
    [
        JobNotFoundError,
        InvalidJobIDError,
        UnknownServerError,
        RuntimeError,
        TimeoutError,
    ],
)
def test_it_propagates_other_exceptions_from_job_service(exception_type: type[Exception]) -> None:
    """It should propagate exceptions from the job service other than NotAuthenticatedError."""

    class JobServiceDouble(JobServiceSpy):
        def wait_for_result(
            self,
            token: str,
            job_id: UUID,
            *,
            query_interval_seconds: float = 1.0,
            wait: Callable[[float], None] = time.sleep,
            max_attempts: int = 600,
            out: TextIO = sys.stdout,
            report_state: Callable[[NonFinalJobState], None] | None = None,
            refresh_token: Callable[[], str | None] | None = None,
        ) -> FinalJobState:
            raise exception_type()

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceDouble()

    with pytest.raises(exception_type):
        wait_for_final_state(app, uuid4())


@pytest.mark.parametrize("api_token", ["I am a token", None])
def test_it_passes_report_state_callable_to_job_service(api_token: str | None) -> None:
    """It should pass the report_state callable to the job service."""

    expected_state = RROngoing(finished_count=1)

    class JobServiceDouble(JobServiceSpy):
        def wait_for_result(
            self,
            token: str,
            job_id: UUID,
            *,
            query_interval_seconds: float = 1.0,
            wait: Callable[[float], None] = time.sleep,
            max_attempts: int = 600,
            out: TextIO = sys.stdout,
            report_state: Callable[[NonFinalJobState], None] | None = None,
            refresh_token: Callable[[], str | None] | None = None,
        ) -> FinalJobState:
            self.refresh_callback = refresh_token
            self.passed_callable = report_state
            if report_state:
                report_state(expected_state)
            return RRCancelled()

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceDouble()

    reported_state = None

    def test_function(state: JobState) -> None:
        nonlocal reported_state
        reported_state = state

    wait_for_final_state(app, uuid4(), report_state=test_function, api_token=api_token)

    assert app.job_service.passed_callable == test_function
    assert reported_state is expected_state
