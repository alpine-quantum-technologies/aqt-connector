"""ARNICA models for jobs."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of an ARNICA job.
    
    Possible values are:
        - CANCELLED: The job was cancelled
        - ERROR: The job processing failed
        - FINISHED: The job was processed successfully
        - ONGOING: The job is being processed
        - QUEUED: The job is in the queue and waiting to be processed
    """

    CANCELLED = "cancelled"
    ERROR = "error"
    FINISHED = "finished"
    ONGOING = "ongoing"
    QUEUED = "queued"


class JobType(str, Enum):
    """ARNICA job types.
    
    Possible values are:
        - QUANTUM_CIRCUIT: A job containing a list of quantum circuits
    """

    QUANTUM_CIRCUIT = "quantum_circuit"

class StatusChange(BaseModel):
    """Model for a job status change."""

    new_status: JobStatus
    timestamp: datetime

class BasicJobMetadata(BaseModel):
    """Metadata for a user-submitted job."""

    job_id: uuid.UUID = Field(description="Id that uniquely identifies the job. This is used to request results.")
    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: Union[str, None] = None
    resource_id: str
    workspace_id: str