"""Provides entry points for authentication and session management."""

import sys
from typing import TextIO

from aqt_connector._arnica_app import ArnicaApp
from aqt_connector.exceptions import AuthenticationError


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
    try:
        existing_valid_token = app.auth_service.get_or_refresh_access_token(app.config.store_access_token)
    except AuthenticationError:
        existing_valid_token = None

    if existing_valid_token:
        stdout.write("Already authenticated!\n")
        return existing_valid_token

    if app.config.client_id and app.config.client_secret:
        access_token = app.oidc_service.authenticate_with_client_credentials(
            (app.config.client_id, app.config.client_secret)
        )
        refresh_token = None
    else:
        tokens = app.oidc_service.authenticate_device(out=stdout)
        access_token = tokens.access_token
        refresh_token = tokens.refresh_token

    if app.config.store_access_token:
        app.auth_service.save_access_token(access_token)
        if refresh_token:
            app.auth_service.save_refresh_token(refresh_token)

    return access_token


def get_access_token(app: ArnicaApp) -> str | None:
    """Gets an access token for the current user session.

    Args:
        app (ArnicaApp): the application instance.

    Returns:
        str | None: the access token if the user has an active session, otherwise None.
    """
    return app.auth_service.get_or_refresh_access_token(store=app.config.store_access_token)
