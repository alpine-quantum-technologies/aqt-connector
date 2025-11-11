"""AQT-connector models for quantum operations."""

from abc import ABC, abstractmethod
from math import inf
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Literal,
    Union,
    final,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    ValidationError,
    field_validator,
)
from pydantic.types import NonNegativeInt, conint
from typing_extensions import TypeAlias, TypeGuard

if TYPE_CHECKING:
    Bit = int
else:
    Bit = conint(ge=0, le=1)


class AbstractOperation(ABC, BaseModel):
    """Abstract operation on the quantum register."""

    model_config = ConfigDict(extra="forbid")


class AbstractGate(AbstractOperation):
    """Abstract quantum gate."""

    @abstractmethod
    def get_qubits(self) -> set[int]:
        """The qubits addressed by this gate."""


class SingleQubitGate(AbstractGate):
    """Abstract single qubit rotation."""

    qubit: NonNegativeInt

    @final
    def get_qubits(self) -> set[int]:
        """The addressed qubits."""
        return {self.qubit}


class GateRZ(SingleQubitGate):
    r"""### A single-qubit rotation around the Bloch sphere's z-axis.

    Details can be found in the description of `GateRZ` in https://arnica.aqt.eu/api/v1/docs
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "RZ"
        super().__init__(**data)

    phi: float = Field(gt=-inf, lt=inf)
    operation: Literal["RZ"]


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


class Measure(AbstractOperation):
    """Measurement operation.

    The MEASURE operation instructs the resource
    to perform a projective measurement of all qubits.
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "MEASURE"
        super().__init__(**data)

    operation: Literal["MEASURE"]


Gate: TypeAlias = Union[GateRZ, GateR, GateRXX]
Operation: TypeAlias = Union[Gate, Measure]


class OperationModel(RootModel[Operation]):
    """Model for the items in a Circuit.

    This extra wrapper is introduced to leverage the pydantic
    tagged-union parser.
    """

    root: Operation = Field(..., discriminator="operation")


GATE_TYPES: Final[list[type[Gate]]] = [GateRZ, GateR, GateRXX]


def is_gate(operation: Operation) -> TypeGuard[Gate]:
    """Whether an operation is a quantum gate."""
    return isinstance(operation, AbstractGate)
