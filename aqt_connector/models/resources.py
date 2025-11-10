"""ARNICA resource models."""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, model_validator
from typing_extensions import Self


class ResourceType(str, Enum):
    """Type of an ARNICA quantum resource."""

    SIMULATOR = "simulator"
    DEVICE = "device"


class ResourceStatus(str, Enum):
    """Status of an ARNICA quantum resource."""

    ONLINE = "online"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class GateFidelity(BaseModel):
    """**Gate fidelity**

    Specifies the gate fidelity with a value between 0 and 100 and an additional
    uncertainty value. The sum of these two values cannot exceed 100.
    """  # noqa: D415

    value: float = Field(ge=0, le=100)
    uncertainty: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.value + self.uncertainty > 100:
            raise ValueError("Value plus uncertainty > 100%")
        return self


def keys_are_contiguous(fidelity_dict: dict[str, GateFidelity]) -> dict[str, GateFidelity]:
    for i, key in enumerate(fidelity_dict.keys()):
        if key != str(i):
            raise ValueError("Keys are not contiguous!")
    return fidelity_dict


class PositiveFloatValueWithUncertainty(BaseModel):
    value: float = Field(gt=0)
    uncertainty: float = Field(ge=0)

class Characterisation(BaseModel):
    """Characterisation data describing a resources properties.

    Details can be found in the description of the Characterisation schema in https://arnica.aqt.eu/api/v1/docs

    Attributes:
        single_qubit_gate_fidelity: The single-qubit gate fidelity for each qubit.
        mean_two_qubit_gate_fidelity: The mean two-qubit gate fidelity.
        spam_fidelity_lower_bound: The SPAM fidelity (lower bound).
        t2_coherence_time_s: T2 coherence time (no Spin Echo) in seconds.
        t1_s: T1 in seconds. Literature value from https://doi.org/10.1103/PhysRevA.62.032503.
        readout_time_micros: The duration of detecting the ion state in microseconds.
        single_qubit_gate_duration_micros: Average duration to execute a single-qubit gate in microseconds.
        two_qubit_gate_duration_micros: Average duration to execute a two-qubit gate in microseconds.
        updated_at: Timestamp when this was last updated.
    """

    single_qubit_gate_fidelity: Annotated[dict[str, GateFidelity], AfterValidator(keys_are_contiguous)]
    mean_two_qubit_gate_fidelity: GateFidelity
    spam_fidelity_lower_bound: float = Field(..., ge=0, le=100, )
    t2_coherence_time_s: PositiveFloatValueWithUncertainty
    t1_s: PositiveFloatValueWithUncertainty
    readout_time_micros: float = Field(ge=0)
    single_qubit_gate_duration_micros: float = Field(ge=0)
    two_qubit_gate_duration_micros: float = Field(ge=0)
    updated_at: datetime
