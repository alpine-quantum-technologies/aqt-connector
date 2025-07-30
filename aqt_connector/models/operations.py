"""ARNICA Quantum Operation Models."""

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
    r"""### A single-qubit rotation rotation around the Bloch sphere's z-axis.

    The Rz-gate on qubit j with pulse area θ in units of π is defined as
        $$
        U_{\mathrm{R_z}}^j(\theta) =
        \exp\left( -\mathrm{i} \theta \frac{\pi}{2} \sigma_z^j \right) =
        \begin{pmatrix}
        \cos(\theta \frac{\pi}{2}) -\mathrm{i}\sin(\theta \frac{\pi}{2}) && 0 \\
        0 && \cos(\theta \frac{\pi}{2}) +\mathrm{i}\sin(\theta \frac{\pi}{2})
        \end{pmatrix}
        $$
    with the Pauli matrix
        $$
        \sigma_z =
        \begin{pmatrix}
        1 & 0 \\ 0 & -1
        \end{pmatrix}.
        $$

    **Examples:**
        $$
        \begin{align*}
        U_{\mathrm{R_z}}^j(1)\frac{1}{\sqrt{2}}\left( \ket{0_j} + \ket{1_j}\right) &=
        \frac{1}{\sqrt{2}}\left (\ket{0_j} - \ket{1_j} \right ) \\
        U_{\mathrm{R_z}}^j(0.5)\frac{1}{\sqrt{2}}\left (\ket{0_j} + \ket{1_j} \right) &=
        \frac{1}{\sqrt{2}}\left (\ket{0_j} +\mathrm{i}\ket{1_j} \right )
        \end{align*}
        $$
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "RZ"
        super().__init__(**data)

    phi: float = Field(gt=-inf, lt=inf)
    operation: Literal["RZ"]


class GateR(SingleQubitGate):
    r"""### A single-qubit rotation around an arbitrary axis on the Bloch sphere's equatorial plane.

    The R-gate on qubit j with pulse area θ and mixing angle φ, both in units of π, is defined as
        $$
        U_{\mathrm{R}}^j(\theta,\varphi) =
        \exp\left( -\mathrm{i} \theta \frac{\pi}{2}
        \left[\sin(\varphi \pi)\sigma_y^j + \cos(\varphi \pi)\sigma_x^j \right] \right) =
        \begin{pmatrix}
        \cos(\theta \frac{\pi}{2}) && -\mathrm{i} e^{-\mathrm{i} \varphi \pi}\sin(\theta \frac{\pi}{2})\\
        -\mathrm{i} e^{\mathrm{i} \varphi \pi}\sin(\theta \frac{\pi}{2}) && \cos(\theta \frac{\pi}{2})
        \end{pmatrix}
        $$
    with the Pauli matrices
        $$
        \sigma_x =
        \begin{pmatrix}
        0 & 1 \\ 1 & 0
        \end{pmatrix} ,
        \sigma_y =
        \begin{pmatrix}
        0 & -\mathrm{i} \\ \mathrm{i} & 0
        \end{pmatrix}.
        $$

    **Examples:**
        $$
        \begin{align*}
        U_{\mathrm{R}}^j(0.5, 0) \ket{0_j} &=
        \frac{1}{\sqrt{2}}\left (\ket{0_j} - \mathrm{i}\ket{1_j} \right )\\
        U_{\mathrm{R}}^j(0.5, 0.5) \ket{0_j} &=
        \frac{1}{\sqrt{2}}\left (\ket{0_j} + \ket{1_j} \right )
        \end{align*}
        $$
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "R"
        super().__init__(**data)

    phi: float = Field(ge=0.0, le=2.0)
    theta: float = Field(ge=0.0, le=1.0)
    operation: Literal["R"]


class GateRXX(AbstractGate):
    r"""### A two-qubit entangling gate of Mølmer-Sørensen-type.

    The MS-gate on qubits j and k with pulse area θ in units of π is defined as
        $$
        \begin{aligned}
        U_{\mathrm{MS}}^{j,k} \left (\theta \right) & =
        e^{\mathrm{i}\theta\frac{\pi}{2}}\exp{\left(-\mathrm{i} \theta \pi {S_x}^2 \right) }
        = \begin{pmatrix}
        \cos(\theta \frac{\pi}{2}) & 0 & 0 && -\mathrm{i}\sin(\theta \frac{\pi}{2}) \\
        0 & \cos(\theta \frac{\pi}{2}) & -\mathrm{i}\sin(\theta \frac{\pi}{2}) && 0 \\
        0 & -\mathrm{i}\sin(\theta\frac{\pi}{2}) & \cos(\theta \frac{\pi}{2}) && 0 \\
        -\mathrm{i}\sin(\theta \frac{\pi}{2}) & 0 & 0 && \cos(\theta \frac{\pi}{2})
        \end{pmatrix}
        \end{aligned}
        $$
    with
        $$
        S_x =\frac{1}{2}\left (\sigma_x^j + \sigma_x^k \right)
        $$
    and the Pauli matrix
        $$
        \sigma_x =
        \begin{pmatrix}
        0 & 1 \\ 1 & 0
        \end{pmatrix}.
        $$

    A fully-entangling gate between qubit 0 and qubit 1 therefore is
        $$
        U_{\mathrm{MS}}^{0,1} \left (0.5 \right) = \frac{1}{\sqrt{2}}
        \begin{pmatrix}
        1 && 0 && 0 && -\mathrm{i} \\ 0 && 1 && -\mathrm{i} && 0 \\
        0 && -\mathrm{i} && 1 && 0 \\ -\mathrm{i} && 0 && 0 && 1
        \end{pmatrix}
        $$

    **Examples:**
        $$
        \begin{align*}
        U_{\mathrm{MS}}^{j,k}(0.5) \ket{0_j0_k} &=
        \frac{1}{\sqrt{2}}\left (\ket{0_j0_k} -\mathrm{i} \ket{1_j1_k} \right ) \\
        U_{\mathrm{MS}}^{j,k}(0.5) \ket{1_j1_k} &=
        \frac{1}{\sqrt{2}}\left ( -\mathrm{i}\ket{0_j0_k} + \ket{1_j1_k} \right )
        \end{align*}
        $$
    """

    def __init__(self, **data: Any) -> None:
        data["operation"] = "RXX"
        super().__init__(**data)

    # constraint unique_items does not work for Tuple
    # We are using a custom validator, but the constraint is not part of
    # the OpenApi spec.
    qubits: list[NonNegativeInt] = Field(min_length=2, max_length=2)
    theta: float = Field(ge=0.0, le=0.5)
    operation: Literal["RXX"]

    @field_validator("qubits")
    @classmethod
    def validate_qubits_unique(cls, v: list[NonNegativeInt]) -> list[NonNegativeInt]:
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
