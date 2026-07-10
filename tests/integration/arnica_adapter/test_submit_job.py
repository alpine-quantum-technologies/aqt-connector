from __future__ import annotations

import json
from collections.abc import Callable
from uuid import uuid4

import httpx
import pytest

from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.exceptions import (
    NotAuthenticatedError,
    RequestError,
    ResourceIDError,
    UnknownServerError,
    WorkspaceIDError,
)
from aqt_connector.models.arnica.jobs import BasicJobMetadata, JobType
from aqt_connector.models.arnica.request_bodies.jobs import QuantumCircuits, SubmitJobRequest
from aqt_connector.models.arnica.response_bodies.jobs import SubmitJobResponse
from aqt_connector.models.circuits import Circuit, Measure, OperationModel, QuantumCircuit
from aqt_connector.models.operations import GateRZ

workspace_id = "workspace"
resource_id = "resource_a"
base_url = "https://arnica.example.com"


@pytest.mark.simulated
def test_it_submits_job_successfully() -> None:
    """It should send the submit-job request and return the queued response."""
    expected_response = _expected_response(workspace_id, resource_id, label="Example computation")

    def assert_submit_request(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"/v1/submit/{workspace_id}/{resource_id}"
        assert request.headers["Authorization"] == "Bearer dummy_token"
        assert json.loads(request.content) == _expected_request(label="Example computation")
        return httpx.Response(status_code=200, json=expected_response.model_dump(mode="json"))

    arnica_adapter = _adapter_with_transport(assert_submit_request)

    result = arnica_adapter.submit_job(
        "dummy_token",
        workspace_id,
        resource_id,
        _quantum_circuits(),
        label="Example computation",
    )

    assert result == expected_response


@pytest.mark.simulated
def test_it_raises_not_authenticated_error_on_401() -> None:
    """It should raise NotAuthenticatedError when Arnica responds with 401 Unauthorized."""
    arnica_adapter = _adapter_with_transport(lambda request: httpx.Response(status_code=401))

    with pytest.raises(NotAuthenticatedError):
        arnica_adapter.submit_job("invalid_token", workspace_id, resource_id, _quantum_circuits())


@pytest.mark.simulated
def test_it_raises_workspace_id_error_on_403() -> None:
    """It should raise WorkspaceIDError when Arnica responds with 403 Forbidden."""
    arnica_adapter = _adapter_with_transport(lambda request: httpx.Response(status_code=403))

    with pytest.raises(WorkspaceIDError):
        arnica_adapter.submit_job("dummy_token", workspace_id, resource_id, _quantum_circuits())


@pytest.mark.simulated
def test_it_raises_resource_id_error_on_404() -> None:
    """It should raise ResourceIDError when Arnica responds with 404 Not Found."""
    arnica_adapter = _adapter_with_transport(lambda request: httpx.Response(status_code=404))

    with pytest.raises(ResourceIDError):
        arnica_adapter.submit_job("dummy_token", workspace_id, resource_id, _quantum_circuits())


@pytest.mark.simulated
def test_it_raises_value_error_on_422() -> None:
    """It should raise ValueError when Arnica responds with 422 Unprocessable Entity."""
    arnica_adapter = _adapter_with_transport(lambda request: httpx.Response(status_code=422))

    with pytest.raises(ValueError):
        arnica_adapter.submit_job("dummy_token", workspace_id, resource_id, _quantum_circuits())


@pytest.mark.simulated
def test_it_raises_unknown_server_error_on_500() -> None:
    """It should raise UnknownServerError when Arnica responds with 500 Internal Server Error."""
    arnica_adapter = _adapter_with_transport(lambda request: httpx.Response(status_code=500))

    with pytest.raises(UnknownServerError):
        arnica_adapter.submit_job("dummy_token", workspace_id, resource_id, _quantum_circuits())


@pytest.mark.simulated
def test_it_raises_network_error_on_request_error() -> None:
    """It should raise RequestError when a network error occurs during the request."""

    def raise_connect_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection error", request=request)

    arnica_adapter = _adapter_with_transport(raise_connect_error)

    with pytest.raises(RequestError):
        arnica_adapter.submit_job("dummy_token", workspace_id, resource_id, _quantum_circuits())


@pytest.mark.simulated
def test_it_raises_runtime_error_on_unexpected_status_code() -> None:
    """It should raise RuntimeError when an unexpected status code is returned."""

    def return_teapot(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=418)

    arnica_adapter = _adapter_with_transport(return_teapot)

    with pytest.raises(RuntimeError):
        arnica_adapter.submit_job("dummy_token", workspace_id, resource_id, _quantum_circuits())


@pytest.mark.simulated
def test_it_raises_unknown_server_error_on_validation_failure() -> None:
    """It should raise UnknownServerError when response validation fails."""

    def return_malformed_response(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json={"invalid_field": "invalid_value"})

    arnica_adapter = _adapter_with_transport(return_malformed_response)

    with pytest.raises(UnknownServerError):
        arnica_adapter.submit_job("dummy_token", workspace_id, resource_id, _quantum_circuits())


def _quantum_circuits() -> QuantumCircuits:
    return QuantumCircuits(
        circuits=[
            QuantumCircuit(
                repetitions=5,
                quantum_circuit=Circuit(
                    root=[
                        OperationModel(root=GateRZ(qubit=0, phi=0.5)),
                        OperationModel(root=Measure()),
                    ]
                ),
                number_of_qubits=1,
            )
        ]
    )


def _expected_request(*, label: str | None = None) -> dict[str, object]:
    return SubmitJobRequest(payload=_quantum_circuits(), label=label).model_dump(mode="json")


def _expected_response(workspace_id: str, resource_id: str, *, label: str | None = None) -> SubmitJobResponse:
    return SubmitJobResponse(
        job=BasicJobMetadata(
            job_id=uuid4(),
            job_type=JobType.QUANTUM_CIRCUIT,
            label=label,
            resource_id=resource_id,
            workspace_id=workspace_id,
        )
    )


def _adapter_with_transport(handler: Callable[[httpx.Request], httpx.Response]) -> ArnicaAdapter:
    arnica_adapter = ArnicaAdapter(base_url=base_url)
    transport = httpx.MockTransport(handler)
    arnica_adapter._http_client = httpx.Client(transport=transport)
    return arnica_adapter
