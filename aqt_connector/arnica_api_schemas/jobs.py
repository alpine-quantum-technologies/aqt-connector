"""Job schemas for the ARNICA API."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from aqt_connector.arnica_api_schemas import BaseSchema
from aqt_connector.models.circuits import QuantumCircuit
from aqt_connector.models.jobs import JobStatusPublic, JobType
from aqt_connector.models.operations import Bit


class StatusChange(BaseModel):
    """Schema for a job status change."""

    new_status: JobStatusPublic
    timestamp: datetime


class SubmitJobRequest(BaseSchema):
    """Request body schema for the submit job endpoint."""

    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: str | None = None
    payload: "QuantumCircuits"


class QuantumCircuits(BaseModel):
    """Payload of a SubmitJobRequest with job_type 'quantum_circuit'."""

    circuits: list[QuantumCircuit] = Field(min_length=1, max_length=50)


class BaseResponse(BaseModel):
    """Base schema for job result metadata."""

    status: JobStatusPublic
    timing_data: list[StatusChange] | None = None


class RRQueued(BaseResponse):
    """Metadata for a queued job."""

    status: Literal[JobStatusPublic.QUEUED] = JobStatusPublic.QUEUED


class RROngoing(BaseResponse):
    """Metadata for an ongoing job."""

    status: Literal[JobStatusPublic.ONGOING] = JobStatusPublic.ONGOING
    finished_count: int = Field(ge=0)


class RRFinished(BaseResponse):
    """Metadata for a finished job."""

    status: Literal[JobStatusPublic.FINISHED] = JobStatusPublic.FINISHED
    result: dict[int, list[list[Bit]]]


class RRError(BaseResponse):
    """Metadata for a failed job."""

    status: Literal[JobStatusPublic.ERROR] = JobStatusPublic.ERROR
    message: str


class RRCancelled(BaseResponse):
    """Metadata for a cancelled job."""

    status: Literal[JobStatusPublic.CANCELLED] = JobStatusPublic.CANCELLED


class BasicJobMetadata(BaseModel):
    """Metadata for a user-submitted job."""

    job_id: uuid.UUID = Field(description="Id that uniquely identifies the job. This is used to request results.")
    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: str | None = None
    resource_id: str
    workspace_id: str


class SubmitJobResponse(BaseSchema):
    """Response body schema for the submit job endpoint."""

    job: BasicJobMetadata
    response: RRQueued = RRQueued()


class ResultResponse(BaseSchema):
    """Response body schema for the request result endpoint."""

    job: BasicJobMetadata
    response: RRQueued | RROngoing | RRFinished | RRError | RRCancelled
