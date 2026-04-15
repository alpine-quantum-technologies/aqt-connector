"""Acceptance tests for job management use cases."""

from __future__ import annotations

import uuid

import pytest
from pytest_httpserver import HTTPServer

from aqt_connector import fetch_job_state, wait_for_final_state
from aqt_connector._arnica_app import ArnicaApp
from aqt_connector.exceptions import JobNotFoundError, NotAuthenticatedError
from aqt_connector.models.arnica.response_bodies.jobs import RRFinished, RRQueued
from tests.acceptance.conftest import JWTFactory, job_state_response_json

A_JOB_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_fetch_queued_job_returns_queued_state(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """fetch_job_state returns a queued state for a job that is waiting to run.

    The test server also verifies the library sends ``Authorization: Bearer <token>``.
    """
    api_token = make_jwt()

    arnica_server.expect_ordered_request(
        f"/v1/result/{A_JOB_ID}",
        method="GET",
        headers={"Authorization": f"Bearer {api_token}"},
    ).respond_with_data(
        job_state_response_json(A_JOB_ID, RRQueued()),
        content_type="application/json",
    )

    state = fetch_job_state(arnica_app, A_JOB_ID, api_token=api_token)

    assert isinstance(state, RRQueued)


def test_fetch_finished_job_returns_results(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """fetch_job_state returns the measurement results for a completed job."""
    api_token = make_jwt()
    expected_result = {0: [[0, 1], [1, 0]]}

    arnica_server.expect_ordered_request(
        f"/v1/result/{A_JOB_ID}",
        method="GET",
        headers={"Authorization": f"Bearer {api_token}"},
    ).respond_with_data(
        job_state_response_json(A_JOB_ID, RRFinished(result=expected_result)),
        content_type="application/json",
    )

    state = fetch_job_state(arnica_app, A_JOB_ID, api_token=api_token)

    assert isinstance(state, RRFinished)
    assert state.result == expected_result


def test_fetch_job_state_raises_not_authenticated_when_no_token(arnica_app: ArnicaApp) -> None:
    """fetch_job_state raises NotAuthenticatedError when no token is available."""
    with pytest.raises(NotAuthenticatedError):
        fetch_job_state(arnica_app, A_JOB_ID)


def test_fetch_unknown_job_raises_job_not_found(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """fetch_job_state raises JobNotFoundError when the API returns 404."""
    unknown_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    api_token = make_jwt()

    arnica_server.expect_ordered_request(f"/v1/result/{unknown_id}", method="GET").respond_with_data("", status=404)

    with pytest.raises(JobNotFoundError):
        fetch_job_state(arnica_app, unknown_id, api_token=api_token)


def test_wait_for_final_state_polls_until_job_finishes(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """wait_for_final_state keeps polling until the job reaches a final state."""
    api_token = make_jwt()
    expected_result = {0: [[1], [0]]}
    finished = RRFinished(result=expected_result)

    queued_body = job_state_response_json(A_JOB_ID, RRQueued())
    finished_body = job_state_response_json(A_JOB_ID, finished)

    for body in [queued_body, queued_body, finished_body]:
        arnica_server.expect_ordered_request(f"/v1/result/{A_JOB_ID}", method="GET").respond_with_data(
            body, content_type="application/json"
        )

    final_state = wait_for_final_state(arnica_app, A_JOB_ID, api_token=api_token, query_interval_seconds=0)

    assert isinstance(final_state, RRFinished)
    assert final_state.result == expected_result


def test_wait_for_final_state_raises_timeout_when_max_attempts_exceeded(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """wait_for_final_state raises TimeoutError after exhausting max attempts."""
    api_token = make_jwt()
    queued_body = job_state_response_json(A_JOB_ID, RRQueued())

    # Persistent handler - serves any number of calls without being "consumed"
    arnica_server.expect_request(f"/v1/result/{A_JOB_ID}", method="GET").respond_with_data(
        queued_body, content_type="application/json"
    )

    with pytest.raises(TimeoutError):
        wait_for_final_state(arnica_app, A_JOB_ID, api_token=api_token, query_interval_seconds=0, max_attempts=2)
