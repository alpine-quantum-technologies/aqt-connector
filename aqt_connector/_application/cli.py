from pathlib import Path
from typing import Annotated, Optional

import typer

from aqt_connector import ArnicaApp, ArnicaConfig, log_in
from aqt_connector.exceptions import AuthenticationError

APP_NAME = "aqt"

app = typer.Typer()


@app.command(name="log-in")
def log_in_command(
    client_id: Annotated[Optional[str], typer.Option(help="Client ID")] = None,
    client_secret: Annotated[Optional[str], typer.Option(help="Client secret")] = None,
    arnica_url: Annotated[Optional[str], typer.Option(help="The URL of the Arnica API")] = None,
):
    config = ArnicaConfig(Path(typer.get_app_dir(APP_NAME)))
    if arnica_url:
        config.arnica_url = arnica_url
    if client_id:
        config.client_id = client_id
    if client_secret:
        config.client_secret = client_secret

    arnica = ArnicaApp(config)

    try:
        log_in(arnica)
        print("Authentication complete")
    except AuthenticationError:
        typer.echo("Authentication failed! Please check your credentials and try again.")
