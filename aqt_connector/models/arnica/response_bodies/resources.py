"""ARNICA API response bodies for resources."""

from datetime import datetime
from typing import Union

from aqt_connector.models import BaseModelSerialisable
from aqt_connector.models.arnica.resources import ResourceStatus, ResourceType
from aqt_connector.models.resources import Characterisation


class ResourceDetails(BaseModelSerialisable):
    """Model for the response of the ARNICA resource details endpoint."""

    id: str
    name: str
    type: ResourceType
    status: ResourceStatus
    available_qubits: int
    status_updated_at: datetime
    characterisation: Union[Characterisation, None] = None


class WorkspaceResource(BaseModelSerialisable):
    """Model of a resource within a workspace."""

    id: str
    name: str
    type: ResourceType
