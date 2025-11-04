"""Workspace schemas for the ARNICA API."""

from aqt_connector.arnica_api_schemas import BaseSchema
from aqt_connector.arnica_api_schemas.resources import WorkspaceResource


class Workspace(BaseSchema):
    """Schema for a workspace."""

    id: str
    accepting_job_submissions: bool
    jobs_being_processed: bool
    resources: list[WorkspaceResource]