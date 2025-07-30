"""ARNICA Core Quantum Circuit Models."""

from collections.abc import Iterator

from pydantic import BaseModel, Field, RootModel, model_validator
from typing_extensions import Self

from aqt_connector.models.operations import Gate, Measure, OperationModel, is_gate


class Circuit(RootModel[list[OperationModel]]):
    """Json encoding of a quantum circuit."""

    root: list[OperationModel] = Field(..., min_length=1, max_length=2000)

    @model_validator(mode="after")
    def ensure_measurement_at_the_end(self) -> Self:
        """Accept exactly one `Measure` instruction as last operation in the circuit."""
        operations = self.root

        measurements_pos = [index for index, operation in enumerate(operations) if isinstance(operation.root, Measure)]

        if len(measurements_pos) != 1 or measurements_pos[0] != (len(operations) - 1):
            raise ValueError("Need exactly one `MEASURE` operation at the end of the circuit.")

        return self

    def gates(self) -> Iterator[Gate]:
        return iter(operation.root for operation in self.root if is_gate(operation.root))

    @property
    def number_of_qubits(self) -> int:
        """Number of qubits used by this circuit."""
        # The circuit consists only of one MEASURE operation
        if len(self.root) == 1:
            return 0
        qubits: set[int] = set()
        for gate in self.gates():
            qubits = qubits.union(gate.get_qubits())
        return max(qubits) + 1


class QuantumCircuit(BaseModel):
    """A quantum circuit-type job that can run on a computing resource."""

    repetitions: int = Field(ge=1, le=2000)
    """Number of repetitions of the circuit, for statistics sampling."""

    quantum_circuit: Circuit
    """Description of the circuit to execute on the computing resource."""

    number_of_qubits: int = Field(ge=1, le=20)
    """Number of qubits used in the circuit."""

    @model_validator(mode="after")
    def validate_number_of_qubits(self) -> Self:
        quantum_circuit = self.quantum_circuit
        if self.number_of_qubits >= quantum_circuit.number_of_qubits:
            return self
        raise ValueError(f"Operations address qubits outside of given quantum register of size {self.number_of_qubits}")
