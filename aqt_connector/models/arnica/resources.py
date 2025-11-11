"""ARNICA models for resources."""

from enum import Enum


class ResourceType(str, Enum):
    """Type of an ARNICA quantum resource.

    The possible values are:
        - SIMULATOR: Service that simulates the behaviour of a quantum computer
        - DEVICE: A physical quantum computer
    """

    SIMULATOR = "simulator"
    DEVICE = "device"


class ResourceStatus(str, Enum):
    """Status of an ARNICA quantum resource.

    The possible values are:
        - MAINTENANCE: The resource is under maintenance
        - OFFLINE: The resource is offline
        - ONLINE: The resource is online
        - UNAVAILABLE: The status of the resource is currently not available to the user
    """

    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    ONLINE = "online"
    UNAVAILABLE = "unavailable"
