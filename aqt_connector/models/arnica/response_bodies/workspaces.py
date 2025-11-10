"""ARNICA API response bodies for workspaces."""

from aqt_connector.models import BaseModelSerialisable
from aqt_connector.models.arnica.response_bodies.resources import WorkspaceResource


class Workspace(BaseModelSerialisable):
    """Model for an item in the workspace list response."""

    id: str
    accepting_job_submissions: bool
    jobs_being_processed: bool
    resources: list[WorkspaceResource]
