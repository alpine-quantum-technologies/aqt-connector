from enum import StrEnum


class JobStatusPublic(StrEnum):
    """Status of a job for the public API."""

    CANCELLED = "cancelled"
    ERROR = "error"
    FINISHED = "finished"
    ONGOING = "ongoing"
    QUEUED = "queued"


class JobType(StrEnum):
    """Possible Arnica job types."""

    QUANTUM_CIRCUIT = "quantum_circuit"
