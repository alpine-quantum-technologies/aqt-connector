from enum import Enum


class JobStatus(str, Enum):
    """Status of a job."""

    CANCELLED = "cancelled"
    ERROR = "error"
    FINISHED = "finished"
    ONGOING = "ongoing"
    QUEUED = "queued"


class JobType(str, Enum):
    """Possible Arnica job types."""

    QUANTUM_CIRCUIT = "quantum_circuit"
