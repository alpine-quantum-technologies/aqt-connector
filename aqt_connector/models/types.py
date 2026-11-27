from typing import TypeAlias, TypeGuard

from pydantic import Field, RootModel

from aqt_connector.models.common.operations import AbstractGate, GateRZ, Measure
from aqt_connector.models.ibex.operations import GateR, GateRXX
from aqt_connector.models.lynx.operations import Barrier, GateRX, GateRZZ

Gate: TypeAlias = GateRZ | GateR | GateRXX | GateRX | GateRZZ
Operation: TypeAlias = Gate | Measure | Barrier


class OperationModel(RootModel[Operation]):
    """Model for the items in a Circuit.

    This extra wrapper is introduced to leverage the pydantic
    tagged-union parser.
    """

    root: Operation = Field(..., discriminator="operation")


def is_gate(operation: Operation) -> TypeGuard[Gate]:
    """Whether an operation is a quantum gate."""
    return isinstance(operation, AbstractGate)
