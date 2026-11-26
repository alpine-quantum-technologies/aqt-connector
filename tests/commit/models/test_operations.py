import pytest
from pydantic import ValidationError

from aqt_connector.models.operations import GateRXX


def test_it_rejects_duplicate_qubits_during_model_validation() -> None:
    """It should expose duplicate qubits as a Pydantic validation error."""
    with pytest.raises(ValidationError, match="addressed qubits must be unique"):
        GateRXX(qubits=[0, 0], theta=0)


def test_duplicate_qubit_validator_raises_value_error_when_called_directly() -> None:
    """It should raise ValueError when the validator is called directly."""
    with pytest.raises(ValueError, match="addressed qubits must be unique"):
        GateRXX.validate_qubits_unique([0, 0])
