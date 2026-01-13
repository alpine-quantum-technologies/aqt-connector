import random
import sys
import time
from collections.abc import Callable
from typing import TextIO, cast
from uuid import UUID

from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.exceptions import RequestError
from aqt_connector.models.arnica.response_bodies.jobs import FinalJobState, JobState


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

        Raises:
            RequestError: If there is a network-related error during the request.
            NotAuthenticatedError: If the provided token is invalid or expired.
            JobNotFoundError: If the job with the specified ID does not exist.
            InvalidJobIDError: If the provided job ID is not valid.
            UnknownServerError: If the Arnica API encounters an internal error.
            RuntimeError: For any other unexpected errors.
        """
        return self.arnica.fetch_job_state(token, job_id)

    def wait_for_result(
        self,
        token: str,
        job_id: UUID,
        *,
        query_interval_seconds: float = 1.0,
        wait: Callable[[float], None] = time.sleep,
        max_attempts: int = 600,  # 10 minutes (average)
        out: TextIO = sys.stdout,
    ) -> FinalJobState:
        """Waits for the job with the given ID to complete and returns its final state.

        The endpoint is queried repeatedly until the job reaches a finished state or the maximum
        number of attempts is reached. Between each query, the function waits for a jittered duration
        based on the specified query interval.

        Args:
            token (str): The authentication token to use.
            job_id (UUID): The ID of the job to wait for.
            query_interval_seconds (float, optional): The base interval between job state queries. Defaults to 1.0.
            wait (callable, optional): A callable that takes a duration in seconds to wait. Defaults to time.sleep.
            max_attempts (int, optional): The maximum number of attempts to query the job state. Defaults to 600.
            out (TextIO, optional): text stream to send output to. Defaults to sys.stdout.

        Raises:
            NotAuthenticatedError: If the provided token is invalid or expired.
            JobNotFoundError: If the job with the specified ID does not exist.
            InvalidJobIDError: If the provided job ID is not valid.
            UnknownServerError: If the Arnica API encounters an internal error.
            RuntimeError: For any other unexpected errors.
            TimeoutError: If the job does not complete within the maximum number of attempts.

        Returns:
            JobState: The final state of the job once it has completed.
        """
        attempts = 0
        while True:
            attempts += 1
            try:
                job_state = self.arnica.fetch_job_state(token, job_id)
                if job_state.is_finished():
                    return cast(FinalJobState, job_state)

            except RequestError as err:
                out.write(f"Transient ({type(err).__name__}) error encountered while fetching job state: {err}.\n")

            if attempts == max_attempts:
                raise TimeoutError(f"Timed out after {attempts} attempts waiting for job to finish.")

            wait(
                random.uniform(
                    query_interval_seconds - query_interval_seconds * 0.5,
                    query_interval_seconds + query_interval_seconds * 0.5,
                )
            )
