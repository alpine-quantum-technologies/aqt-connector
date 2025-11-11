from uuid import UUID

from aqt_connector.models.arnica.response_bodies.jobs import JobState


class JobService:
    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        raise NotImplementedError
