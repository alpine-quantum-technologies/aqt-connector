"""Acceptance tests for job submission use cases."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pytest_httpserver import HTTPServer

from aqt_connector import ArnicaApp, submit_job
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.jobs import BasicJobMetadata, JobType
from aqt_connector.models.arnica.request_bodies.jobs import QuantumCircuits, SubmitJobRequest
from aqt_connector.models.arnica.response_bodies.jobs import SubmitJobResponse
from aqt_connector.models.circuits import Circuit, Measure, OperationModel, QuantumCircuit
from aqt_connector.models.operations import GateRZ
from tests.acceptance.conftest import JWTFactory


def test_submit_job_posts_valid_payload_and_returns_queued_response(
    arnica_app: ArnicaApp, arnica_server: HTTPServer, make_jwt: JWTFactory
) -> None:
    """submit_job sends the Arnica request body and returns the queued response."""
    api_token = make_jwt()
    workspace_id = "workspace"
    resource_id = "resource_a"
    circuits = _quantum_circuits()
    label = "Example computation"
    expected_response = _expected_response(workspace_id, resource_id, circuits, label=label)

    arnica_server.expect_ordered_request(
        f"/v1/submit/{workspace_id}/{resource_id}",
        method="POST",
        headers={"Authorization": f"Bearer {api_token}"},
        data=_expected_request(circuits, label=label),
    ).respond_with_data(
        expected_response.model_dump_json(),
        content_type="application/json",
    )

    result = submit_job(
        arnica_app,
        workspace_id,
        resource_id,
        circuits,
        label=label,
        api_token=api_token,
    )

    assert result == expected_response


def test_submit_job_raises_not_authenticated_when_no_token(arnica_app: ArnicaApp) -> None:
    """submit_job raises NotAuthenticatedError when no access token is available."""
    circuits = _quantum_circuits()

    with pytest.raises(NotAuthenticatedError):
        submit_job(arnica_app, "workspace", "resource_a", circuits)


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


def _expected_request(circuits: QuantumCircuits, *, label: str | None = None) -> str:
    return SubmitJobRequest(payload=circuits, label=label).model_dump_json()


def _expected_response(
    workspace_id: str, resource_id: str, circuits: QuantumCircuits, *, label: str | None = None
) -> SubmitJobResponse:
    return SubmitJobResponse(
        job=BasicJobMetadata(
            job_id=uuid4(),
            job_type=JobType.QUANTUM_CIRCUIT,
            label=label,
            resource_id=resource_id,
            workspace_id=workspace_id,
        )
    )
