"""ARNICA API request bodies for jobs."""

from typing import Literal, Union

from pydantic import BaseModel, Field

from aqt_connector.models import BaseModelSerialisable
from aqt_connector.models.arnica.jobs import JobType
from aqt_connector.models.circuits import QuantumCircuit


class SubmitJobRequest(BaseModelSerialisable):
    """Request body model for the submit job endpoint."""

    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: Union[str, None] = None
    payload: "QuantumCircuits"


class QuantumCircuits(BaseModel):
    """Payload of a SubmitJobRequest with job_type 'quantum_circuit'."""

    circuits: list[QuantumCircuit] = Field(min_length=1, max_length=50)
