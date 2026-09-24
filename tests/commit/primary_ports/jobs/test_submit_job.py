from __future__ import annotations

from uuid import uuid4

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig
from aqt_connector._application.jobs import submit_job
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.job_service import JobService
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.jobs import BasicJobMetadata, JobType
from aqt_connector.models.arnica.request_bodies.jobs import QuantumCircuits
from aqt_connector.models.arnica.response_bodies.jobs import SubmitJobResponse
from aqt_connector.models.circuits import Circuit, Measure, OperationModel, QuantumCircuit
from aqt_connector.models.operations import GateRZ


class AuthServiceSpy(AuthService):
    """A spy for the AuthService to track method calls and parameters."""

    def __init__(self) -> None:
        self.was_token_fetched = False
        self.was_token_stored = False
        self.fetched_token = "thisisthetoken"

    def get_or_refresh_access_token(self, store: bool) -> str | None:
        self.was_token_fetched = True
        self.was_token_stored = store
        return self.fetched_token


class JobServiceSpy(JobService):
    """A spy for the JobService to track method calls and parameters."""

    def __init__(self) -> None:
        self.given_token: str | None = None
        self.requested_workspace_id: str | None = None
        self.requested_resource_id: str | None = None
        self.requested_circuits: QuantumCircuits | None = None
        self.given_label: str | None = None
        self.returned_response = SubmitJobResponse(
            job=BasicJobMetadata(
                job_id=uuid4(),
                job_type=JobType.QUANTUM_CIRCUIT,
                resource_id="resource_a",
                workspace_id="workspace",
            )
        )

    def submit_job(
        self,
        token: str,
        workspace_id: str,
        resource_id: str,
        circuits: QuantumCircuits,
        *,
        label: str | None = None,
    ) -> SubmitJobResponse:
        self.given_token = token
        self.requested_workspace_id = workspace_id
        self.requested_resource_id = resource_id
        self.requested_circuits = circuits
        self.given_label = label
        return self.returned_response


def test_it_gets_or_refreshes_token() -> None:
    """It should get or refresh the access token before submitting the job."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    submit_job(app, "workspace", "resource_a", _quantum_circuits())

    assert app.auth_service.was_token_fetched
    assert app.auth_service.was_token_stored is app.config.store_access_token


def test_it_uses_fetched_token_to_submit_job() -> None:
    """It should use the fetched access token to submit the job."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    circuits = _quantum_circuits()
    submit_job(app, "workspace", "resource_a", circuits)

    assert app.job_service.given_token == app.auth_service.fetched_token
    assert app.job_service.requested_workspace_id == "workspace"
    assert app.job_service.requested_resource_id == "resource_a"
    assert app.job_service.requested_circuits is circuits
    assert app.job_service.given_label is None


def test_it_uses_provided_api_token() -> None:
    """It should use a provided API token instead of fetching one."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    provided_token = "provided_api_token"
    circuits = _quantum_circuits()
    submit_job(app, "workspace", "resource_a", circuits, api_token=provided_token)

    assert app.job_service.given_token == provided_token
    assert not app.auth_service.was_token_fetched


def test_it_passes_label_to_job_service() -> None:
    """It should pass the provided label to the job service."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    circuits = _quantum_circuits()
    submit_job(app, "workspace", "resource_a", circuits, label="Example computation")

    assert app.job_service.given_label == "Example computation"


def test_it_raises_if_not_authenticated() -> None:
    """It should raise NotAuthenticatedError if no access token is available."""

    class UnauthenticatedAuthService(AuthServiceSpy):
        def get_or_refresh_access_token(self, store: bool) -> str | None:
            return None  # Simulate no token available

    app = ArnicaApp(ArnicaConfig())
    app.auth_service = UnauthenticatedAuthService()
    app.job_service = JobServiceSpy()

    with pytest.raises(NotAuthenticatedError, match="User not authenticated. Please log in."):
        submit_job(app, "workspace", "resource_a", _quantum_circuits())


def test_it_returns_submit_job_response() -> None:
    """It should return the response from the job service."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.job_service = JobServiceSpy()

    response = submit_job(app, "workspace", "resource_a", _quantum_circuits())

    assert response is app.job_service.returned_response


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
