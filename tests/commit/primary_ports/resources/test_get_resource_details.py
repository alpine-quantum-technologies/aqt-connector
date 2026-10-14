from datetime import datetime

import pytest

from aqt_connector import ArnicaApp, ArnicaConfig
from aqt_connector._application.resources import get_resource_details
from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.resource_service import ResourceService
from aqt_connector.exceptions import NotAuthenticatedError
from aqt_connector.models.arnica.resources import ResourceStatus, ResourceType
from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails


class AuthServiceSpy(AuthService):
    """A spy for the AuthService to track method calls and parameters."""

    def __init__(self) -> None:
        self.was_token_fetched = False
        self.was_token_stored = False
        self.fetched_token: str | None = "thisisthetoken"

    def get_or_refresh_access_token(self, store: bool) -> str | None:
        self.was_token_fetched = True
        self.was_token_stored = store
        return self.fetched_token


class ResourceServiceSpy(ResourceService):
    """A spy for the ResourceService to track method calls and parameters."""

    def __init__(self) -> None:
        self.given_token: str | None = None
        self.requested_resource_id: str | None = None
        self.returned_details = ResourceDetails(
            id="resource_a",
            name="Resource A",
            type=ResourceType.SIMULATOR,
            status=ResourceStatus.ONLINE,
            available_qubits=5,
            status_updated_at=datetime(2026, 1, 1),
        )

    def get_resource_details(self, token: str, resource_id: str) -> ResourceDetails:
        self.given_token = token
        self.requested_resource_id = resource_id
        return self.returned_details


def test_it_gets_or_refreshes_token() -> None:
    """It should get or refresh the access token before requesting resource details."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.resource_service = ResourceServiceSpy()

    get_resource_details(app, "resource_a")

    assert app.auth_service.was_token_fetched
    assert app.auth_service.was_token_stored is app.config.store_access_token


def test_it_uses_fetched_token_to_request_resource_details() -> None:
    """It should use the fetched access token to request resource details."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.resource_service = ResourceServiceSpy()

    get_resource_details(app, "resource_a")

    assert app.resource_service.given_token == app.auth_service.fetched_token


def test_it_uses_provided_api_token() -> None:
    """It should use a provided API token instead of fetching one."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.resource_service = ResourceServiceSpy()

    provided_token = "provided_api_token"
    get_resource_details(app, "resource_a", api_token=provided_token)

    assert app.resource_service.given_token == provided_token
    assert not app.auth_service.was_token_fetched


def test_it_raises_if_not_authenticated() -> None:
    """It should raise NotAuthenticatedError if no access token is available."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.auth_service.fetched_token = None
    app.resource_service = ResourceServiceSpy()

    with pytest.raises(NotAuthenticatedError, match="User not authenticated. Please log in."):
        get_resource_details(app, "resource_a")


def test_it_requests_correct_resource_details() -> None:
    """It should request details for the correct resource ID."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.resource_service = ResourceServiceSpy()

    get_resource_details(app, "resource_a")

    assert app.resource_service.requested_resource_id == "resource_a"


def test_it_returns_resource_details() -> None:
    """It should return the details fetched from the resource service."""
    app = ArnicaApp(ArnicaConfig())
    app.auth_service = AuthServiceSpy()
    app.resource_service = ResourceServiceSpy()

    details = get_resource_details(app, "resource_a")

    assert details is app.resource_service.returned_details
