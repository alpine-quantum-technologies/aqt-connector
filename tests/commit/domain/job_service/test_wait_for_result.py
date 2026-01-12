from uuid import UUID, uuid4

import pytest

from aqt_connector._domain.job_service import JobService
from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.exceptions import (
    InvalidJobIDError,
    JobNotFoundError,
    NotAuthenticatedError,
    RequestError,
    UnknownServerError,
)
from aqt_connector.models.arnica.response_bodies.jobs import JobState, RRFinished, RRQueued
from tests.commit.domain.stdout_spy import StdoutSpy


class ArnicaAdapterSpy(ArnicaAdapter):
    """A spy for the ArnicaAdapter."""

    def __init__(self) -> None:
        self.fetch_job_state_called_with: list[tuple[str, UUID]] = []
        self.returned_state: JobState = RRFinished(result={0: [[0, 0]]})

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        self.fetch_job_state_called_with.append((token, job_id))
        return self.returned_state


class ArnicaAdapterFinishingSpy(ArnicaAdapterSpy):
    """A spy for the ArnicaAdapter that simulates a job finishing after several polls."""

    def __init__(self) -> None:
        super().__init__()
        self.queue_for_calls = 2

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        self.fetch_job_state_called_with.append((token, job_id))
        if len(self.fetch_job_state_called_with) <= self.queue_for_calls:
            return RRQueued()
        else:
            return RRFinished(result={0: [[0, 0]]})


class ArnicaAdapterWithTransientErrors(ArnicaAdapterSpy):
    """A double for the ArnicaAdapter that raises transient RequestError exceptions."""

    def __init__(self) -> None:
        super().__init__()
        self.error_for_calls = 1

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        self.fetch_job_state_called_with.append((token, job_id))
        if len(self.fetch_job_state_called_with) <= self.error_for_calls:
            raise RequestError("Simulated transient error")
        else:
            self.returned_state = RRFinished(result={0: [[0, 0]]})
            return self.returned_state


class ArnicaAdapterWithNonTransientErrors(ArnicaAdapterSpy):
    """A double for the ArnicaAdapter that raises non-transient errors."""

    def __init__(self) -> None:
        super().__init__()
        self.exception: type[Exception] = RuntimeError

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        raise self.exception()


def test_it_invokes_adapter_with_token_and_job_id() -> None:
    """It should invoke the adapter with the given token and job ID."""
    adapter_spy = ArnicaAdapterSpy()
    service = JobService(adapter_spy)

    token = "some-token"
    job_id = uuid4()
    service.wait_for_result(token, job_id)

    assert adapter_spy.fetch_job_state_called_with[0] == (token, job_id)


def test_it_returns_result_if_job_finished() -> None:
    """It should return the result if the job is finished."""
    adapter_spy = ArnicaAdapterSpy()
    service = JobService(adapter_spy)

    result = service.wait_for_result("some-token", uuid4())

    assert result is adapter_spy.returned_state


def test_it_continues_polling_until_finished() -> None:
    """It should continue polling until the job is finished."""
    adapter_spy = ArnicaAdapterFinishingSpy()
    service = JobService(adapter_spy)

    def wait_mock(duration: float) -> None: ...

    service.wait_for_result("some-token", uuid4(), wait=wait_mock)

    assert len(adapter_spy.fetch_job_state_called_with) == 3


def test_it_waits_between_polls() -> None:
    """It should wait between polls."""
    adapter_spy = ArnicaAdapterFinishingSpy()
    service = JobService(adapter_spy)

    wait_count = 0

    def wait_mock(duration: float) -> None:
        nonlocal wait_count
        wait_count += 1

    service.wait_for_result("some-token", uuid4(), wait=wait_mock)

    assert wait_count == 2


@pytest.mark.parametrize("query_interval_seconds", [1.0, 2.0, 5.0])
def test_it_jitters_wait_durations(query_interval_seconds: float) -> None:
    """It should jitter wait durations."""
    adapter_spy = ArnicaAdapterFinishingSpy()
    adapter_spy.queue_for_calls = 10
    service = JobService(adapter_spy)

    wait_durations: list[float] = []

    def wait_mock(duration: float) -> None:
        wait_durations.append(duration)

    service.wait_for_result("some-token", uuid4(), wait=wait_mock, query_interval_seconds=query_interval_seconds)

    assert len(wait_durations) == 10
    assert not all(duration == query_interval_seconds for duration in wait_durations)
    assert all(
        query_interval_seconds - query_interval_seconds * 0.5
        <= duration
        <= query_interval_seconds + query_interval_seconds * 0.5
        for duration in wait_durations
    )


def test_it_continues_polling_on_transient_request_errors() -> None:
    """It should continue polling on transient RequestError exceptions."""
    adapter_spy = ArnicaAdapterWithTransientErrors()
    adapter_spy.error_for_calls = 2
    stdout_spy = StdoutSpy()
    service = JobService(adapter_spy)

    def wait_mock(duration: float) -> None: ...

    result = service.wait_for_result("some-token", uuid4(), wait=wait_mock, out=stdout_spy)

    assert len(adapter_spy.fetch_job_state_called_with) == 3
    assert result is adapter_spy.returned_state
    assert len(stdout_spy.output) == 2
    assert all(
        output == "Transient (RequestError) error encountered while fetching job state: Simulated transient error.\n"
        for output in stdout_spy.output
    )


def test_it_raises_request_error_after_max_attempts() -> None:
    """It should raise TimeoutError after reaching max attempts."""
    adapter_spy = ArnicaAdapterWithTransientErrors()
    adapter_spy.error_for_calls = 5
    service = JobService(adapter_spy)

    def wait_mock(duration: float) -> None: ...

    with pytest.raises(TimeoutError, match="Timed out after 5 attempts waiting for job to finish."):
        service.wait_for_result("some-token", uuid4(), wait=wait_mock, max_attempts=5)

    assert len(adapter_spy.fetch_job_state_called_with) == 5


@pytest.mark.parametrize(
    "exception_type",
    [
        NotAuthenticatedError,
        JobNotFoundError,
        InvalidJobIDError,
        RuntimeError,
        UnknownServerError,
    ],
)
def test_it_raises_on_non_transient_errors(exception_type: type[Exception]) -> None:
    """It should raise on non-transient exceptions."""
    adapter_spy = ArnicaAdapterWithNonTransientErrors()
    adapter_spy.exception = exception_type
    service = JobService(adapter_spy)

    def wait_mock(duration: float) -> None: ...

    with pytest.raises(exception_type):
        service.wait_for_result("some-token", uuid4(), wait=wait_mock)
