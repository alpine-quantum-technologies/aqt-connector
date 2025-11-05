"""Resource schemas for the ARNICA API."""

from datetime import datetime
from typing import Union

from aqt_connector.arnica_api_schemas import BaseSchema
from aqt_connector.models.resources import (
    Characterisation,
    ResourceStatus,
    ResourceType,
)


class ResourceDetails(BaseSchema):
    """Schema for the response of the public resource details endpoint."""

    id: str
    name: str
    type: ResourceType
    status: ResourceStatus
    available_qubits: int
    status_updated_at: datetime
    characterisation: Union[Characterisation, None] = None


class WorkspaceResource(BaseSchema):
    """Schema of a resource within a workspace."""

    id: str
    name: str
    type: ResourceType
