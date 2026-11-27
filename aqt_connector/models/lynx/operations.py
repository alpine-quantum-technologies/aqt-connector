from typing import Any, Literal, final

from pydantic import Field, NonNegativeInt, ValidationError, field_validator

from aqt_connector.models.common.operations import AbstractGate, AbstractOperation, SingleQubitGate


class Barrier(AbstractOperation):
    """Barrier operation.

    The BARRIER operation instructs the resource
    to separate blocks of operations for further transpilation.
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "BARRIER"
        super().__init__(**data)

    operation: Literal["BARRIER"]


class GateRX(SingleQubitGate):
    r"""### A single-qubit rotation around the Bloch sphere's x-axis."""

    def __init__(self, **data: Any) -> None:
        data["operation"] = "RX"
        super().__init__(**data)

    theta: float = Field(ge=-1.0, le=1.0)
    operation: Literal["RX"]


class GateRZZ(AbstractGate):
    r"""### A two-qubit entangling ZZ-phase-gate."""

    def __init__(self, **data: Any) -> None:
        data["operation"] = "RZZ"
        super().__init__(**data)

    qubits: list[NonNegativeInt] = Field(min_length=2, max_length=2)
    theta: float = Field(ge=-0.5, le=0.5)
    operation: Literal["RZZ"]

    @field_validator("qubits")
    @classmethod
    def validate_qubits_unique(cls, v: list[NonNegativeInt]) -> list[NonNegativeInt]:
        """Constraint unique_items does not work for Tuple, therefore we are using a custom validator."""
        if v[0] == v[1]:
            msg = "addressed qubits must be unique"
            raise ValidationError(msg)
        return v

    @final
    def get_qubits(self) -> set[int]:
        return set(self.qubits)
