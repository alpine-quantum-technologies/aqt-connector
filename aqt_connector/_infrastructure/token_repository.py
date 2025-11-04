from pathlib import Path
from typing import Union


class TokenRepository:
    """Stores access and refresh tokens on disk.

    Attributes:
        access_token_path (Path): the filepath where the access token is stored.
        refresh_token_path (Path): the filepath where the refresh token is stored.
    """

    def __init__(self, app_dir: Path) -> None:
        """Initialises the instance to manage the access token at the given filepath.

        Args:
            app_dir (Path): the storage location of the access token.
        """
        self.access_token_path = app_dir / "access_token"
        self.refresh_token_path = app_dir / "refresh_token"

    def save_access_token(self, token: str) -> None:
        """Saves an access token to disk.

        Args:
            token (str): the access token.
        """
        self._save_token(self.access_token_path, token)

    def load_access_token(self) -> Union[str, None]:
        """Loads an access token from disk.

        Returns:
            str | None: the access token when one exists in the store, otherwise None.
        """
        return self._load_token(self.access_token_path)

    def save_refresh_token(self, refresh_token: str) -> None:
        """Saves a refresh token to disk.

        Args:
            refresh_token (str): the refresh token.
        """
        self._save_token(self.refresh_token_path, refresh_token)

    def load_refresh_token(self) -> Union[str, None]:
        """Loads a refresh token from disk.

        Returns:
            str | None: the refresh token when one exists in the store, otherwise None.
        """
        return self._load_token(self.refresh_token_path)

    def _save_token(self, path: Path, token: str) -> None:
        """Saves a token to disk at the specified path.

        Args:
            path (Path): the file path to save the token.
            token (str): the token to save.
        """
        with open(path, "w") as f:
            f.write(token)

    def _load_token(self, path: Path) -> Union[str, None]:
        """Loads a token from disk at the specified path.

        Args:
            path (Path): the file path to load the token from.

        Returns:
            str | None: the token if it exists, otherwise None.
        """
        try:
            with open(path) as f:
                return f.read()
        except FileNotFoundError:
            return None
