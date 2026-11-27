from typing import Any, Literal, final

from pydantic import Field, ValidationError, field_validator
from pydantic.types import NonNegativeInt

from aqt_connector.models.common.operations import AbstractGate, SingleQubitGate


class GateR(SingleQubitGate):
    r"""### A single-qubit rotation around an arbitrary axis on the Bloch sphere's equatorial plane.

    Details can be found in the description of `GateR` in https://arnica.aqt.eu/api/v1/docs
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "R"
        super().__init__(**data)

    phi: float = Field(ge=0.0, le=2.0)
    theta: float = Field(ge=0.0, le=1.0)
    operation: Literal["R"]


class GateRXX(AbstractGate):
    r"""### A two-qubit entangling gate of Mølmer-Sørensen-type.

    Details can be found in the description of `GateRXX` in https://arnica.aqt.eu/api/v1/docs
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "RXX"
        super().__init__(**data)

    qubits: list[NonNegativeInt] = Field(min_length=2, max_length=2)
    theta: float = Field(ge=0.0, le=0.5)
    operation: Literal["RXX"]

    @field_validator("qubits")
    @classmethod
    def validate_qubits_unique(cls, v: list[NonNegativeInt]) -> list[NonNegativeInt]:
        """Constraint unique_items does not work for Tuple, therefore we are using a custom validator."""
        if v[0] == v[1]:
            raise ValidationError("addressed qubits must be unique")
        return v

    @final
    def get_qubits(self) -> set[int]:
        return set(self.qubits)
