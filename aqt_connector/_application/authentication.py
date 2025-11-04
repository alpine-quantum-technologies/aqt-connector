"""Provides entry points for authentication and session management."""

import sys
from typing import TextIO, Union

from aqt_connector._arnica_app import ArnicaApp


def log_in(
    app: ArnicaApp,
    *,
    stdout: TextIO = sys.stdout,
) -> str:
    """Logs a user in.

    Args:
        app (ArnicaApp): the application instance.
        stdout (TextIO, optional): the text stream to send output to. Defaults to sys.stdout.

    Returns:
        str: the user's access token.
    """
    existing_valid_token = app.auth_service.get_or_refresh_access_token(app.config.store_access_token)
    if existing_valid_token:
        stdout.write("Already authenticated!\n")
        return existing_valid_token

    if app.config.client_id and app.config.client_secret:
        access_token = app.oidc_service.authenticate_with_client_credentials(
            (app.config.client_id, app.config.client_secret)
        )
    else:
        access_token, _ = app.oidc_service.authenticate_device()

    if app.config.store_access_token:
        app.auth_service.save_access_token(access_token)

    return access_token


def get_access_token(app: ArnicaApp) -> Union[str, None]:
    """Gets an access token for the current user session.

    Args:
        app (ArnicaApp): the application instance.

    Returns:
        str | None: the access token if the user has an active session, otherwise None.
    """
    return app.auth_service.get_or_refresh_access_token(store=app.config.store_access_token)
