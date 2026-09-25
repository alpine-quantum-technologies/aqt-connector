import pytest
from pydantic import ValidationError

from aqt_connector.models.resources import TwoQubitGateFidelity


def test_it_accepts_ordered_qubit_indices() -> None:
    """It should accept qubit indices that are in ascending order."""
    fidelity = TwoQubitGateFidelity(value=99, uncertainty=1, qubits=(0, 1))

    assert fidelity.qubits == (0, 1)


def test_it_rejects_unordered_qubit_indices() -> None:
    """It should reject qubit indices that are not in ascending order."""
    with pytest.raises(ValidationError, match="Qubit indices are not ordered!"):
        TwoQubitGateFidelity(value=99, uncertainty=1, qubits=(1, 0))


@pytest.mark.parametrize("qubits", [(-1, 0), (0, -1)])
def test_it_rejects_negative_qubit_indices(qubits: tuple[int, int]) -> None:
    """It should reject qubit indices that are negative."""
    with pytest.raises(ValidationError, match="Qubit indices cannot be negative!"):
        TwoQubitGateFidelity(value=99, uncertainty=1, qubits=qubits)


def test_it_rejects_equal_qubit_indices() -> None:
    """It should reject qubit indices that are equal."""
    with pytest.raises(ValidationError, match="Qubit indices are equal!"):
        TwoQubitGateFidelity(value=99, uncertainty=1, qubits=(0, 0))
