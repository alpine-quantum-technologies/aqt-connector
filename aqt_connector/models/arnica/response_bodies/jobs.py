"""ARNICA API response bodies for jobs."""

from typing import Literal, Union

from pydantic import BaseModel, Field
from typing_extensions import TypeAlias

from aqt_connector.models import BaseModelSerialisable
from aqt_connector.models.arnica.jobs import BasicJobMetadata, JobStatus, StatusChange
from aqt_connector.models.operations import Bit


class BaseResponse(BaseModel):
    """Base model for job result metadata."""

    status: JobStatus
    timing_data: Union[list[StatusChange], None] = None


class RRQueued(BaseResponse):  # type: ignore[override, unused-ignore]
    """Result metadata for a queued job."""

    status: Literal[JobStatus.QUEUED] = JobStatus.QUEUED


class RROngoing(BaseResponse):  # type: ignore[override, unused-ignore]
    """Result metadata for an ongoing job."""

    status: Literal[JobStatus.ONGOING] = JobStatus.ONGOING
    finished_count: int = Field(ge=0)


class RRFinished(BaseResponse):  # type: ignore[override, unused-ignore]
    """Result metadata for a finished job."""

    status: Literal[JobStatus.FINISHED] = JobStatus.FINISHED
    result: dict[int, list[list[Bit]]]


class RRError(BaseResponse):  # type: ignore[override, unused-ignore]
    """Result metadata for a failed job."""

    status: Literal[JobStatus.ERROR] = JobStatus.ERROR
    message: str


class RRCancelled(BaseResponse):  # type: ignore[override, unused-ignore]
    """Result metadata for a cancelled job."""

    status: Literal[JobStatus.CANCELLED] = JobStatus.CANCELLED


JobState: TypeAlias = Union[RRQueued, RROngoing, RRFinished, RRError, RRCancelled]


class SubmitJobResponse(BaseModelSerialisable):
    """Response body model for the submit job endpoint."""

    job: BasicJobMetadata
    response: RRQueued = RRQueued()


class ResultResponse(BaseModelSerialisable):
    """Response body model for the request result endpoint."""

    job: BasicJobMetadata
    response: JobState
