from uuid import uuid4

from aqt_connector._domain.job_service import JobService
from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.models.arnica.jobs import BasicJobMetadata, JobType
from aqt_connector.models.arnica.request_bodies.jobs import QuantumCircuits
from aqt_connector.models.arnica.response_bodies.jobs import SubmitJobResponse
from aqt_connector.models.circuits import Circuit, Measure, OperationModel, QuantumCircuit
from aqt_connector.models.operations import GateRZ


class ArnicaAdapterSpy(ArnicaAdapter):
    """A spy for the ArnicaAdapter to be used in tests."""

    def __init__(self) -> None:
        self.submit_job_called_with: list[tuple[str, str, str, QuantumCircuits, str | None]] = []
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
        self.submit_job_called_with.append((token, workspace_id, resource_id, circuits, label))
        return self.returned_response


def test_it_passes_given_parameters() -> None:
    """It should pass the given parameters to the adapter."""
    adapter_spy = ArnicaAdapterSpy()
    service = JobService(adapter_spy)

    token = "some-token"
    workspace_id = "workspace"
    resource_id = "resource_a"
    circuits = _quantum_circuits()

    service.submit_job(token, workspace_id, resource_id, circuits)

    assert adapter_spy.submit_job_called_with == [(token, workspace_id, resource_id, circuits, None)]


def test_it_passes_label() -> None:
    """It should pass the provided label to the adapter."""
    adapter_spy = ArnicaAdapterSpy()
    service = JobService(adapter_spy)

    token = "some-token"
    workspace_id = "workspace"
    resource_id = "resource_a"
    circuits = _quantum_circuits()
    label = "Example computation"

    service.submit_job(token, workspace_id, resource_id, circuits, label=label)

    assert adapter_spy.submit_job_called_with == [(token, workspace_id, resource_id, circuits, label)]


def test_it_returns_adapter_result() -> None:
    """It should return whatever the adapter returns."""
    adapter_spy = ArnicaAdapterSpy()
    service = JobService(adapter_spy)

    actual_response = service.submit_job("some-token", "workspace", "resource_a", _quantum_circuits())

    assert actual_response is adapter_spy.returned_response


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
