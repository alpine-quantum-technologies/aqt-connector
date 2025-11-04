import os
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import tomli

DEFAULT_APP_DIR = Path.home() / ".aqt"


@dataclass
class AuthenticationConfig:
    audience: str = "https://arnica.aqt.eu/api"
    issuer: str = "https://arnica.eu.auth0.com/"
    jwks_url: str = "https://arnica.eu.auth0.com/.well-known/jwks.json"
    device_client_id: str = "HvaMEfNSq30OoxjqDyRWIRkBfJwJywyi"


class ArnicaConfig:
    """Configuration for the SDK.

    Attributes:
        arnica_url (str): the base URL of the Arnica API. Defaults to "https://arnica.aqt.eu/api".
        client_id (str | None): the ID to use for authentication with client credentials. Defaults to None.
        client_secret (str | None): the secret to use for authentication with client credentials. Defaults to None.
        store_access_token (bool): when True, the access token will be persisted to disk. Defaults to True.
        oidc_config (AuthenticationConfig): configuration for the OIDC provider.
    """

    def __init__(self, app_dir=DEFAULT_APP_DIR) -> None:
        """Initializes the configuration.

        Args:
            app_dir (Path): the directory where the application will store its config and cache files. Defaults to
                `Path.home() / .aqt`.
        """
        self._app_dir = app_dir
        self.arnica_url = "https://arnica.aqt.eu/api"
        self.client_id: Union[str, None] = None
        self.client_secret: Union[str, None] = None
        self.store_access_token = True
        self.oidc_config = AuthenticationConfig()

        self._read_config()

    def _read_config(self) -> None:
        """Reads config from the host system."""
        config: dict[str, str] = {}
        config = self._add_file_config(config, self._app_dir / "config")
        config = self._add_env_config(config)

        self.arnica_url = config.get("arnica_url", "https://arnica.aqt.eu/api")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.store_access_token = bool(config.get("store_access_token", "true"))

    def _add_file_config(self, config: dict[str, str], config_filepath: Path) -> dict[str, str]:
        try:
            with open(config_filepath, mode="rb") as f:
                file_config = tomli.load(f)
        except FileNotFoundError:
            return config
        except tomli.TOMLDecodeError as e:
            print(
                f"Config file at {config_filepath} is badly formed and is being ignored:",
                e,
            )
            return config

        new_config = file_config.get("default", file_config)
        return deepcopy(config) | new_config

    def _add_env_config(self, config: dict[str, str]) -> dict[str, str]:
        _config = deepcopy(config)
        for env_key, value in os.environ.items():
            if not re.search(r"^AQT_", env_key):
                continue
            config_key = re.sub(r"^AQT_", "", env_key).lower()
            _config[config_key] = value

        return _config
