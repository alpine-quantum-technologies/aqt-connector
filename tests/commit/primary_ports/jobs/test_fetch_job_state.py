from uuid import UUID, uuid4

import httpx
import pytest

from aqt_connector import ArnicaApp, ArnicaConfig
from aqt_connector._application.jobs import fetch_job_state, wait_for_final_state
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.job_service import JobService
from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.response_bodies.jobs import JobState, RRCancelled, RRQueued


class AuthServiceSpy(AuthService):
    """A spy for the AuthService to track method calls and parameters."""

    def __init__(self) -> None:
        self.was_token_fetched = False
        self.was_token_stored = False
        self.fetched_token: str | None = "thisisthetoken"
        self.refreshed_token: str | None = "this-is-the-refreshed-token"
        self.force_refresh_count = 0

    def get_or_refresh_access_token(self, store: bool, *, force_refresh: bool = False) -> str | None:
        self.was_token_fetched = True
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
        self.returned_state = RRQueued()

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        self.given_token = token
        self.requested_job_id = job_id
        return self.returned_state


def _app_rejecting_first_request(status_code: int) -> tuple[ArnicaApp, UUID, list[str], ArnicaAdapter]:
    job_id = uuid4()
    authorization_headers: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        authorization_headers.append(request.headers["Authorization"])
        if len(authorization_headers) == 1:
            return httpx.Response(status_code=status_code)
        return httpx.Response(
            status_code=200,
            json={
                "job": {"job_id": str(job_id), "resource_id": "resource", "workspace_id": "workspace"},
                "response": {"status": "cancelled"},
            },
        )

    adapter = ArnicaAdapter("https://example.test")
    adapter._http_client = httpx.Client(transport=httpx.MockTransport(respond))
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobService(adapter)
    return app, job_id, authorization_headers, adapter


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


@pytest.mark.parametrize("status_code", [401, 403])
def test_fetch_job_state_retries_http_401_or_403_with_refreshed_token(
    status_code: int,
) -> None:
    """Fetch should retry server 401/403 responses with the replacement bearer token."""
    app, job_id, authorization_headers, adapter = _app_rejecting_first_request(status_code)

    state = fetch_job_state(app, job_id)

    assert isinstance(state, RRCancelled)
    assert authorization_headers == ["Bearer thisisthetoken", "Bearer this-is-the-refreshed-token"]
    assert isinstance(app.auth_service, AuthServiceSpy)
    assert app.auth_service.force_refresh_count == 1
    adapter.close()


@pytest.mark.parametrize("status_code", [401, 403])
def test_wait_for_final_state_retries_http_401_or_403_with_refreshed_token(
    status_code: int,
) -> None:
    """Polling should retry server 401/403 responses with the replacement bearer token."""
    app, job_id, authorization_headers, adapter = _app_rejecting_first_request(status_code)

    state = wait_for_final_state(app, job_id, query_interval_seconds=0, max_attempts=1)

    assert isinstance(state, RRCancelled)
    assert authorization_headers == ["Bearer thisisthetoken", "Bearer this-is-the-refreshed-token"]
    assert isinstance(app.auth_service, AuthServiceSpy)
    assert app.auth_service.force_refresh_count == 1
    adapter.close()


@pytest.mark.parametrize("refreshed_token", [None, "thisisthetoken"])
def test_it_propagates_authentication_error_when_forced_refresh_cannot_replace_token(
    refreshed_token: str | None,
) -> None:
    """It should keep the original authentication failure if refresh cannot replace the rejected token."""

    class JobServiceRejectsToken(JobServiceSpy):
        def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
            raise NotAuthenticatedError

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.auth_service.refreshed_token = refreshed_token
    app.job_service = JobServiceRejectsToken()

    with pytest.raises(NotAuthenticatedError):
        fetch_job_state(app, uuid4())

    assert app.auth_service.force_refresh_count == 1


def test_it_does_not_refresh_a_rejected_static_api_token() -> None:
    """It should propagate server rejection for a caller-provided static token."""

    class JobServiceRejectsToken(JobServiceSpy):
        def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
            raise NotAuthenticatedError

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceRejectsToken()

    with pytest.raises(NotAuthenticatedError):
        fetch_job_state(app, uuid4(), api_token="static-token")

    assert app.auth_service.force_refresh_count == 0


def test_it_propagates_non_authentication_errors_without_refreshing() -> None:
    class JobServiceFails(JobServiceSpy):
        def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
            raise RuntimeError("server failure")

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceFails()

    with pytest.raises(RuntimeError, match="server failure"):
        fetch_job_state(app, uuid4())

    assert app.auth_service.force_refresh_count == 0
