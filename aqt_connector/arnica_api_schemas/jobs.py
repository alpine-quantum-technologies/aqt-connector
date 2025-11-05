"""Job schemas for the ARNICA API."""

import uuid
from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, Field

from aqt_connector.arnica_api_schemas import BaseSchema
from aqt_connector.models.circuits import QuantumCircuit
from aqt_connector.models.jobs import JobStatus, JobType
from aqt_connector.models.operations import Bit


class StatusChange(BaseModel):
    """Schema for a job status change."""

    new_status: JobStatus
    timestamp: datetime


class SubmitJobRequest(BaseSchema):
    """Request body schema for the submit job endpoint."""

    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: Union[str, None] = None
    payload: "QuantumCircuits"


class QuantumCircuits(BaseModel):
    """Payload of a SubmitJobRequest with job_type 'quantum_circuit'."""

    circuits: list[QuantumCircuit] = Field(min_length=1, max_length=50)


class BaseResponse(BaseModel):
    """Base schema for job result metadata."""

    status: JobStatus
    timing_data: Union[list[StatusChange], None] = None


class RRQueued(BaseResponse):  # type: ignore[override, unused-ignore]
    """Metadata for a queued job."""

    status: Literal[JobStatus.QUEUED] = JobStatus.QUEUED


class RROngoing(BaseResponse):  # type: ignore[override, unused-ignore]
    """Metadata for an ongoing job."""

    status: Literal[JobStatus.ONGOING] = JobStatus.ONGOING
    finished_count: int = Field(ge=0)


class RRFinished(BaseResponse):  # type: ignore[override, unused-ignore]
    """Metadata for a finished job."""

    status: Literal[JobStatus.FINISHED] = JobStatus.FINISHED
    result: dict[int, list[list[Bit]]]


class RRError(BaseResponse):  # type: ignore[override, unused-ignore]
    """Metadata for a failed job."""

    status: Literal[JobStatus.ERROR] = JobStatus.ERROR
    message: str


class RRCancelled(BaseResponse):  # type: ignore[override, unused-ignore]
    """Metadata for a cancelled job."""

    status: Literal[JobStatus.CANCELLED] = JobStatus.CANCELLED


class BasicJobMetadata(BaseModel):
    """Metadata for a user-submitted job."""

    job_id: uuid.UUID = Field(description="Id that uniquely identifies the job. This is used to request results.")
    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: Union[str, None] = None
    resource_id: str
    workspace_id: str


class SubmitJobResponse(BaseSchema):
    """Response body schema for the submit job endpoint."""

    job: BasicJobMetadata
    response: RRQueued = RRQueued()


class ResultResponse(BaseSchema):
    """Response body schema for the request result endpoint."""

    job: BasicJobMetadata
    response: Union[RRQueued, RROngoing, RRFinished, RRError, RRCancelled]
