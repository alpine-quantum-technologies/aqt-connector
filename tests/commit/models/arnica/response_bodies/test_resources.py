from datetime import datetime

import pytest
from pydantic import ValidationError

from aqt_connector.models.arnica.response_bodies.resources import CharacterisationResponse


def characterisation_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "single_qubit_gate_fidelity": {"0": {"value": 99, "uncertainty": 1}},
        "mean_two_qubit_gate_fidelity": {"value": 99, "uncertainty": 1},
        "spam_fidelity_lower_bound": 99,
        "t2_coherence_time_s": {"value": 1, "uncertainty": 0},
        "t1_s": {"value": 1, "uncertainty": 0},
        "readout_time_micros": 1,
        "single_qubit_gate_duration_micros": 1,
        "two_qubit_gate_duration_micros": 1,
        "updated_at": datetime(2026, 1, 1),
    }
    data.update(overrides)
    return data


def test_it_defaults_to_no_two_qubit_gate_fidelities() -> None:
    """It should default to no two-qubit gate fidelities."""
    response = CharacterisationResponse.model_validate(characterisation_data())

    assert response.two_qubit_gate_fidelity == []


def test_it_parses_two_qubit_gate_fidelities() -> None:
    """It should correctly parse two-qubit gate fidelities."""
    response = CharacterisationResponse.model_validate(
        characterisation_data(two_qubit_gate_fidelity=[{"value": 99, "uncertainty": 1, "qubits": [0, 1]}])
    )

    assert len(response.two_qubit_gate_fidelity) == 1
    assert response.two_qubit_gate_fidelity[0].qubits == (0, 1)


def test_it_rejects_invalid_two_qubit_gate_fidelities() -> None:
    """It should reject invalid two-qubit gate fidelities."""
    with pytest.raises(ValidationError, match="Qubit indices cannot be negative!"):
        CharacterisationResponse.model_validate(
            characterisation_data(two_qubit_gate_fidelity=[{"value": 99, "uncertainty": 1, "qubits": [-1, 0]}])
        )
