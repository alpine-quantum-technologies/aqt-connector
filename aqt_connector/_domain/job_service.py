import math
import random
import sys
import time
from collections.abc import Callable
from typing import TextIO, cast
from uuid import UUID

from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.exceptions import NotAuthenticatedError, RequestError
from aqt_connector.models.arnica.request_bodies.jobs import QuantumCircuits
from aqt_connector.models.arnica.response_bodies.jobs import (
    FinalJobState,
    JobState,
    NonFinalJobState,
    SubmitJobResponse,
)


class JobService:
    def __init__(self, arnica: ArnicaAdapter) -> None:
        """Initialises the JobService with the given ArnicaAdapter.

        Args:
            arnica (ArnicaAdapter): The Arnica adapter to use for fetching job states.
        """
        self.arnica = arnica

    def submit_job(
        self,
        token: str,
        workspace_id: str,
        resource_id: str,
        circuits: QuantumCircuits,
        *,
        label: str | None = None,
    ) -> SubmitJobResponse:
        """Submits a job to the Arnica API.

        Args:
            token (str): The authentication token to use.
            workspace_id (str): The ID of the workspace to submit the job to.
            resource_id (str): The ID of the resource to submit the job to.
            circuits (QuantumCircuits): The quantum circuits to submit as part of the job.
            label (str | None, optional): An optional label for the job. Defaults to None.

        Raises:
            RequestError: If there is a network-related error during the request.
            NotAuthenticatedError: If the provided token is invalid or expired.
            WorkspaceIDError: If the provided workspace ID is invalid.
            ResourceIDError: If the provided resource ID is invalid.
            ValueError: If the request data is invalid.
            UnknownServerError: If the Arnica API encounters an internal error.
            RuntimeError: For any other unexpected errors.

        Returns:
            SubmitJobResponse: Metadata about the submitted job, including its job ID.
        """
        return self.arnica.submit_job(token, workspace_id, resource_id, circuits, label=label)

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
        report_state: Callable[[NonFinalJobState], None] | None = None,
        refresh_token: Callable[[], str | None] | None = None,
    ) -> FinalJobState:
        """Waits for the job with the given ID to complete and returns its final state.

        The endpoint is queried repeatedly until the job reaches a finished state or the maximum
        number of attempts is reached. Between each query, the function waits for a jittered duration
        based on the specified query interval.

        Args:
            token (str): The authentication token to use.
            job_id (UUID): The ID of the job to wait for.
            query_interval_seconds (float, optional): The base interval between job state queries. Must be finite
                and non-negative; zero disables waiting between polls. Defaults to 1.0.
            wait (callable, optional): A callable that takes a duration in seconds to wait. Defaults to time.sleep.
            max_attempts (int, optional): The maximum number of attempts to query the job state. Must be at least 1.
                Defaults to 600.
            out (TextIO, optional): text stream to send output to. Defaults to sys.stdout.
            report_state (Callable[[NonFinalJobState], None], optional): Callable to report state.
            refresh_token (Callable[[], str | None] | None, optional): refreshes the token after server rejection.

        Raises:
            NotAuthenticatedError: If the provided token is invalid or expired.
            JobNotFoundError: If the job with the specified ID does not exist.
            InvalidJobIDError: If the provided job ID is not valid.
            UnknownServerError: If the Arnica API encounters an internal error.
            RuntimeError: For any other unexpected errors.
            TimeoutError: If the job does not complete within the maximum number of attempts.
            ValueError: If max_attempts is less than 1 or query_interval_seconds is negative or nonfinite.

        Returns:
            JobState: The final state of the job once it has completed.
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if not math.isfinite(query_interval_seconds) or query_interval_seconds < 0:
            raise ValueError("query_interval_seconds must be finite and non-negative")

        attempts = 0
        while True:
            attempts += 1
            job_state: JobState | None = None
            try:
                job_state = self.arnica.fetch_job_state(token, job_id)
            except NotAuthenticatedError:
                if refresh_token is None:
                    raise
                refreshed_token = refresh_token()
                if not refreshed_token or refreshed_token == token:
                    raise
                token = refreshed_token
                try:
                    job_state = self.arnica.fetch_job_state(token, job_id)
                except RequestError as err:
                    out.write(f"Transient ({type(err).__name__}) error encountered while fetching job state: {err}.\n")
            except RequestError as err:
                out.write(f"Transient ({type(err).__name__}) error encountered while fetching job state: {err}.\n")

            if job_state is not None:
                if job_state.is_finished():
                    return cast(FinalJobState, job_state)
                if report_state:
                    report_state(cast(NonFinalJobState, job_state))

            if attempts == max_attempts:
                raise TimeoutError(f"Timed out after {attempts} attempts waiting for job to finish.")

            wait(
                random.uniform(
                    query_interval_seconds * 0.5,
                    query_interval_seconds * 1.5,
                )
            )
