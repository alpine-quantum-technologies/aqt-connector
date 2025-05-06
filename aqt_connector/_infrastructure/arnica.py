"""Schemas for the AQT ARNICA API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from aqt_connector._domain.models.jobs import BasicJobMetadata, JobType, QuantumCircuits, RRQueued


class BaseSchema(BaseModel):
    """Base schema with serialization config."""

    model_config = ConfigDict(from_attributes=True)


class SubmitJobRequest(BaseSchema):
    """Request body schema for the submit job endpoint."""

    job_type: Literal[JobType.QUANTUM_CIRCUIT] = JobType.QUANTUM_CIRCUIT
    label: str | None = None
    payload: QuantumCircuits


class SubmitJobResponse(BaseSchema):
    """Response body schema for the submit job endpoint."""

    job: BasicJobMetadata
    response: RRQueued = RRQueued()
