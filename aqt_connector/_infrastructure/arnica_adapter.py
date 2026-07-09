from uuid import UUID

import httpx
from pydantic import ValidationError

from aqt_connector.exceptions import (
    InvalidJobIDError,
    JobNotFoundError,
    NotAuthenticatedError,
    RequestError,
    ResourceIDError,
    UnknownServerError,
    WorkspaceIDError,
)
from aqt_connector.models.arnica.request_bodies.jobs import QuantumCircuits, SubmitJobRequest
from aqt_connector.models.arnica.response_bodies.jobs import JobState, ResultResponse, SubmitJobResponse


class ArnicaAdapter:
    """Adapter for interacting with the Arnica API."""

    def __init__(self, base_url: str) -> None:
        """Initialises the ArnicaAdapter with the given base URL.

        Args:
            base_url (str): The base URL of the Arnica API.
        """
        self._base_url = base_url
        self._http_client = httpx.Client()

    def close(self) -> None:
        """Closes the underlying HTTP client and releases its connection pool."""
        self._http_client.close()

    def submit_job(
        self, token: str, workspace_id: str, resource_id: str, circuits: QuantumCircuits, *, label: str | None = None
    ) -> SubmitJobResponse:
        """Submits a quantum job to the Arnica API.

        Args:
            token (str): The authentication token to access the Arnica API.
            workspace_id (str): The unique identifier of the workspace.
            resource_id (str): The unique identifier of the resource.
            circuits (QuantumCircuits): The quantum circuits to be submitted.
            label (str | None, optional): An optional label for the job. Defaults to None

        Raises:
            RequestError: If there is a network-related error during the request.
            NotAuthenticatedError: If the provided token is invalid or expired.
            WorkspaceIDError: If the provided workspace ID is invalid.
            ResourceIDError: If the provided resource ID is invalid.
            ValueError: If the request data is invalid.
            UnknownServerError: If the Arnica API encounters an internal error.
            RuntimeError: For any other unexpected errors.

        Returns:
            SubmitJobResponse: Metadata about the submitted job, including its unique ID.
        """
        endpoint_url = f"{self._base_url}/v1/submit/{workspace_id}/{resource_id}"

        request_data = SubmitJobRequest(label=label, payload=circuits)

        try:
            response = self._http_client.post(
                endpoint_url,
                headers={"Authorization": f"Bearer {token}"},
                json=request_data.model_dump(),
            )
            response.raise_for_status()
            return SubmitJobResponse.model_validate_json(response.text)

        except httpx.RequestError as exc:
            raise RequestError from exc

        except httpx.HTTPStatusError as exc:
            exception_map = {
                401: NotAuthenticatedError,
                403: WorkspaceIDError,
                404: ResourceIDError,
                422: ValueError,
                500: UnknownServerError,
            }
            if exc.response.status_code in exception_map:
                raise exception_map[exc.response.status_code] from exc
            raise RuntimeError from exc

        except ValidationError as exc:
            raise UnknownServerError from exc

    def fetch_job_state(self, token: str, job_id: UUID) -> JobState:
        """Fetches the state of a job from the Arnica API.

        Args:
            token (str): The authentication token to access the Arnica API.
            job_id (UUID): The unique identifier of the job to fetch.

        Raises:
            RequestError: If there is a network-related error during the request.
            NotAuthenticatedError: If the provided token is invalid or expired.
            JobNotFoundError: If the job with the specified ID does not exist.
            InvalidJobIDError: If the provided job ID is not valid.
            UnknownServerError: If the Arnica API encounters an internal error.
            RuntimeError: For any other unexpected errors.

        Returns:
            JobState: The current state of the job.
        """
        endpoint_url = f"{self._base_url}/v1/result/{job_id}"

        try:
            response = self._http_client.get(endpoint_url, headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            result = ResultResponse.model_validate_json(response.text)

        except httpx.RequestError as exc:
            raise RequestError from exc

        except httpx.HTTPStatusError as exc:
            exception_map = {
                401: NotAuthenticatedError,
                403: NotAuthenticatedError,
                404: JobNotFoundError,
                422: InvalidJobIDError,
                500: UnknownServerError,
            }
            if exc.response.status_code in exception_map:
                raise exception_map[exc.response.status_code] from exc
            raise RuntimeError from exc

        except ValidationError as exc:
            raise UnknownServerError from exc

        return result.response
