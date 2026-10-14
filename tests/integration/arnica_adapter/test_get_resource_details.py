from __future__ import annotations

from datetime import datetime

import httpx
import pytest

from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.exceptions import NotAuthenticatedError, RequestError, ResourceIDError, UnknownServerError
from aqt_connector.models.arnica.resources import ResourceStatus, ResourceType
from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails
from tests.integration.arnica_adapter.conftest import ArnicaAdapterFactory

resource_id = "resource_a"


@pytest.mark.simulated
def test_it_gets_resource_details_successfully(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should send the resource-details request and return the parsed response."""
    expected_details = _resource_details()

    def assert_resource_request(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/v1/resources/{resource_id}"
        assert request.headers["Authorization"] == "Bearer dummy_token"
        return httpx.Response(status_code=200, json=expected_details.model_dump(mode="json"))

    arnica_adapter = make_arnica_adapter(assert_resource_request)
    details = arnica_adapter.get_resource_details("dummy_token", resource_id)

    assert details == expected_details


@pytest.mark.simulated
def test_it_closes_an_injected_http_client() -> None:
    """It should close an injected HTTP client when the adapter closes."""
    http_client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status_code=200)))
    arnica_adapter = ArnicaAdapter(base_url="https://arnica.example.com", http_client=http_client)

    arnica_adapter.close()

    assert http_client.is_closed


@pytest.mark.simulated
def test_it_raises_not_authenticated_error_on_401(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise NotAuthenticatedError when Arnica responds with 401 Unauthorized."""
    arnica_adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=401))
    with pytest.raises(NotAuthenticatedError):
        arnica_adapter.get_resource_details("invalid_token", resource_id)


@pytest.mark.simulated
def test_it_raises_resource_id_error_on_403(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise ResourceIDError when Arnica responds with 403 Forbidden."""
    arnica_adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=403))
    with pytest.raises(ResourceIDError):
        arnica_adapter.get_resource_details("dummy_token", resource_id)


@pytest.mark.simulated
def test_it_raises_value_error_on_422(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise ValueError when Arnica responds with 422 Unprocessable Entity."""
    arnica_adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=422))
    with pytest.raises(ValueError):
        arnica_adapter.get_resource_details("dummy_token", resource_id)


@pytest.mark.simulated
def test_it_raises_unknown_server_error_on_500(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise UnknownServerError when Arnica responds with 500 Internal Server Error."""
    arnica_adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=500))
    with pytest.raises(UnknownServerError):
        arnica_adapter.get_resource_details("dummy_token", resource_id)


@pytest.mark.simulated
def test_it_raises_network_error_on_request_error(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise RequestError when a network error occurs during the request."""

    def raise_connect_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection error", request=request)

    arnica_adapter = make_arnica_adapter(raise_connect_error)
    with pytest.raises(RequestError):
        arnica_adapter.get_resource_details("dummy_token", resource_id)


@pytest.mark.simulated
def test_it_raises_runtime_error_on_unexpected_status_code(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise RuntimeError when an unexpected status code is returned."""
    arnica_adapter = make_arnica_adapter(lambda request: httpx.Response(status_code=418))
    with pytest.raises(RuntimeError):
        arnica_adapter.get_resource_details("dummy_token", resource_id)


@pytest.mark.simulated
def test_it_raises_unknown_server_error_on_validation_failure(make_arnica_adapter: ArnicaAdapterFactory) -> None:
    """It should raise UnknownServerError when response validation fails."""
    arnica_adapter = make_arnica_adapter(
        lambda request: httpx.Response(status_code=200, json={"invalid_field": "invalid_value"})
    )
    with pytest.raises(UnknownServerError):
        arnica_adapter.get_resource_details("dummy_token", resource_id)


def _resource_details() -> ResourceDetails:
    return ResourceDetails(
        id=resource_id,
        name="Resource A",
        type=ResourceType.SIMULATOR,
        status=ResourceStatus.ONLINE,
        available_qubits=5,
        status_updated_at=datetime(2026, 1, 1),
    )
