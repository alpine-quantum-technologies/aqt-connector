from datetime import datetime

from aqt_connector._domain.resource_service import ResourceService
from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.models.arnica.resources import ResourceStatus, ResourceType
from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails


class ArnicaAdapterSpy(ArnicaAdapter):
    """A spy for the ArnicaAdapter to be used in tests."""

    def __init__(self) -> None:
        self.get_resource_details_called_with: list[tuple[str, str]] = []
        self.returned_details = ResourceDetails(
            id="resource_a",
            name="Resource A",
            type=ResourceType.SIMULATOR,
            status=ResourceStatus.ONLINE,
            available_qubits=5,
            status_updated_at=datetime(2026, 1, 1),
        )

    def get_resource_details(self, token: str, resource_id: str) -> ResourceDetails:
        self.get_resource_details_called_with.append((token, resource_id))
        return self.returned_details


def test_it_passes_given_parameters() -> None:
    """It should pass the given parameters to the adapter."""
    adapter_spy = ArnicaAdapterSpy()
    service = ResourceService(adapter_spy)

    service.get_resource_details("some-token", "resource_a")

    assert adapter_spy.get_resource_details_called_with == [("some-token", "resource_a")]


def test_it_returns_adapter_result() -> None:
    """It should return whatever the adapter returns."""
    adapter_spy = ArnicaAdapterSpy()
    service = ResourceService(adapter_spy)

    actual_details = service.get_resource_details("some-token", "resource_a")

    assert actual_details is adapter_spy.returned_details
