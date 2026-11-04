from uuid import UUID, uuid4

import httpx
import pytest

from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.exceptions import (
    InvalidJobIDError,
    JobExpiredError,
    JobNotFoundError,
    NotAuthenticatedError,
    RequestError,
    UnknownServerError,
)
from aqt_connector.models.arnica.response_bodies.jobs import RRQueued
from tests.integration.arnica_adapter.conftest import ArnicaAdapterFactory

queued_job_id = UUID("98d265ec-99fb-4edd-90d0-3d745307bf7b")
expired_job_id = UUID("64db2fca-4857-4463-90c4-45cbdf0d59d8")


def test_it_fetches_job_state_successfully(arnica_adapter: ArnicaAdapter, auth_token: str) -> None:
    """It should return the job's state."""
    state = arnica_adapter.fetch_job_state(auth_token, job_id=queued_job_id)

    assert state == RRQueued()


def test_it_raises_not_authenticated_error_on_401(arnica_adapter: ArnicaAdapter) -> None:
    """It should raise NotAuthenticatedError when Arnica responds with 401 Unauthorized."""
    with pytest.raises(NotAuthenticatedError):
        arnica_adapter.fetch_job_state("invalid_token", job_id=queued_job_id)


def test_it_raises_job_not_found_error_on_404(arnica_adapter: ArnicaAdapter, auth_token: str) -> None:
    """It should raise JobNotFoundError when Arnica responds with 404 Not Found."""
    with pytest.raises(JobNotFoundError):
        arnica_adapter.fetch_job_state(auth_token, job_id=uuid4())


def test_it_raises_job_expired_error_on_410(arnica_adapter: ArnicaAdapter, auth_token: str) -> None:
    """It should raise JobExpiredError when Arnica responds with 410 Gone."""
    with pytest.raises(JobExpiredError):
        arnica_adapter.fetch_job_state(auth_token, job_id=expired_job_id)


@pytest.mark.simulated
def test_it_raises_invalid_job_id_error_on_422(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise InvalidJobIDError when Arnica responds with 422 Unprocessable Entity."""
    arnica_adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=422))

    with pytest.raises(InvalidJobIDError):
        arnica_adapter.fetch_job_state("dummy_token", job_id=uuid4())


@pytest.mark.simulated
def test_it_raises_unknown_server_error_on_500(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise InvalidJobIDError when Arnica responds with 422 Unprocessable Entity."""
    arnica_adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=500))

    with pytest.raises(UnknownServerError):
        arnica_adapter.fetch_job_state("dummy_token", job_id=uuid4())


@pytest.mark.simulated
def test_it_raises_network_error_on_request_error(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise NetworkError when a network error occurs during the request."""

    def raise_connect_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection error", request=request)

    arnica_adapter = make_arnica_adapter(raise_connect_error)

    with pytest.raises(RequestError):
        arnica_adapter.fetch_job_state("dummy_token", job_id=uuid4())


@pytest.mark.simulated
def test_it_raises_runtime_error_on_unexpected_status_code(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise RuntimeError when an unexpected status code is returned."""

    def return_teapot(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=418)

    arnica_adapter = make_arnica_adapter(return_teapot)

    with pytest.raises(RuntimeError):
        arnica_adapter.fetch_job_state("dummy_token", job_id=uuid4())


@pytest.mark.simulated
def test_it_raises_unknown_server_error_on_validation_failure(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise UnknownServerError when response validation fails."""

    def return_malformed_response(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"invalid_field": "invalid_value"},
        )

    arnica_adapter = make_arnica_adapter(return_malformed_response)

    with pytest.raises(UnknownServerError):
        arnica_adapter.fetch_job_state("dummy_token", job_id=uuid4())
