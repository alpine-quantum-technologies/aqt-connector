from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from aqt_connector._models.circuits import QuantumCircuit


class JobStatus(StrEnum):
    """Status of a job."""

    CANCELLED = "cancelled"
    ERROR = "error"
    FINISHED = "finished"
    ONGOING = "ongoing"
    QUEUED = "queued"


class JobType(StrEnum):
    """Possible Arnica job types."""

    QUANTUM_CIRCUIT = "quantum_circuit"


class StatusChange(BaseModel):
    """Schema for a job status change."""

    new_status: JobStatus
    timestamp: datetime


class QuantumCircuits(BaseModel):
    """Payload of a SubmitJobRequest with job_type 'quantum_circuit'."""

    circuits: list[QuantumCircuit] = Field(min_length=1, max_length=50)


class QuantumCircuitJobSubmission(BaseModel):
    """A Quantum Circuit job submission."""

    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: str | None = None
    payload: QuantumCircuits


class BasicJobMetadata(BaseModel):
    """Metadata for a user-submitted job."""

    job_id: UUID = Field(description="Id that uniquely identifies the job. This is used to request results.")
    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: str | None = None
    resource_id: str
    workspace_id: str


class BaseResponse(BaseModel):
    """Base schema for job result metadata."""

    status: JobStatus
    timing_data: list[StatusChange] | None = None


class RRQueued(BaseResponse):
    """Metadata for a queued job."""

    status: Literal[JobStatus.QUEUED] = JobStatus.QUEUED


class SubmitJobResponse(BaseModel):
    """Response body schema for the submit job endpoint."""

    job: BasicJobMetadata
    response: RRQueued = RRQueued()
