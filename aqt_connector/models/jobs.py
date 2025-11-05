from enum import Enum


class JobStatus(Enum):
    """Status of a job."""

    CANCELLED = "cancelled"
    ERROR = "error"
    FINISHED = "finished"
    ONGOING = "ongoing"
    QUEUED = "queued"


class JobType(Enum):
    """Possible Arnica job types."""

    QUANTUM_CIRCUIT = "quantum_circuit"
