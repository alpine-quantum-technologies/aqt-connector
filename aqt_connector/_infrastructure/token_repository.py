from pathlib import Path
from typing import Union


class TokenRepository:
    """Stores access tokens on disk.

    Attributes:
        filepath (Path): the filepath where the access token is stored.
    """

    def __init__(self, app_dir: Path) -> None:
        """Initialises the instance to manage the access token at the given filepath.

        Args:
            app_dir (Path): the storage location of the access token.
        """
        self.filepath = app_dir / "access_token"

    def save(self, token: str) -> None:
        """Saves an access token to disk.

        Args:
            token (str): the access token.
        """
        with open(self.filepath, "w") as f:
            f.write(token)

    def load(self) -> Union[str, None]:
        """Loads an access token from disk.

        Returns:
            str | None: the access token when one exists in the store, otherwise None.
        """
        try:
            with open(self.filepath) as f:
                return f.read()
        except FileNotFoundError:
            return None
