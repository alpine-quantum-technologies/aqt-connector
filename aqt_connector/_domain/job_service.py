from uuid import UUID

from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.models.arnica.response_bodies.jobs import JobState


class JobService:
    def __init__(self, arnica: ArnicaAdapter) -> None:
        """Initialises the JobService with the given ArnicaAdapter.

        Args:
            arnica (ArnicaAdapter): The Arnica adapter to use for fetching job states.
        """
        self.arnica = arnica

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        """Fetches the state of a job with the given ID using the provided token.

        Args:
            token (str): The authentication token to use.
            job_id (UUID): The ID of the job to fetch the state for.
        """
        return self.arnica.fetch_job_state(token, job_id)
