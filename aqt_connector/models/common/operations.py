"""AQT-connector models for quantum operations."""

from abc import ABC, abstractmethod
from math import inf
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    final,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from pydantic.types import NonNegativeInt, conint

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


class Measure(AbstractOperation):
    """Measurement operation.

    The MEASURE operation instructs the resource
    to perform a projective measurement of all qubits.
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "MEASURE"
        super().__init__(**data)

    operation: Literal["MEASURE"]
