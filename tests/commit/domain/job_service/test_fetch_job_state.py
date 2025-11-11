from uuid import UUID, uuid4

from aqt_connector._domain.job_service import JobService
from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.models.arnica.response_bodies.jobs import JobState, RRQueued


class ArnicaAdapterSpy(ArnicaAdapter):
    """A spy for the ArnicaAdapter to be used in tests."""

    def __init__(self) -> None:
        self.fetch_job_state_called_with: list[tuple[str, UUID]] = []
        self.returned_state = RRQueued()

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        self.fetch_job_state_called_with.append((token, job_id))
        return self.returned_state


def test_it_passes_given_parameters() -> None:
    """It should pass the given parameters to the adapter."""
    adapter_spy = ArnicaAdapterSpy()
    service = JobService(adapter_spy)

    token = "some-token"
    job_id = uuid4()
    service.fetch_job_state(token, job_id)

    assert adapter_spy.fetch_job_state_called_with == [(token, job_id)]


def test_it_returns_adapter_result() -> None:
    """It should return whatever the adapter returns."""
    adapter_spy = ArnicaAdapterSpy()
    service = JobService(adapter_spy)

    actual_state = service.fetch_job_state("some-token", uuid4())

    assert actual_state is adapter_spy.returned_state
