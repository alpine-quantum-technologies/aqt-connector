import os
import stat
from pathlib import Path

import pytest

from aqt_connector._infrastructure.token_repository import TokenRepository


@pytest.mark.skipif(os.name != "posix", reason="POSIX file permissions")
@pytest.mark.parametrize("token_name", ["access_token", "refresh_token"])
def test_newly_saved_tokens_are_only_accessible_to_the_owner(tmp_path: Path, token_name: str) -> None:
    """New token files should have owner-only permissions."""
    token_path = tmp_path / token_name

    token_repo = TokenRepository(tmp_path)
    getattr(token_repo, f"save_{token_name}")("new-token")

    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
    assert token_path.read_text() == "new-token"


@pytest.mark.skipif(os.name != "posix", reason="POSIX file permissions")
@pytest.mark.parametrize("token_name", ["access_token", "refresh_token"])
def test_existing_tokens_are_only_accessible_to_the_owner(tmp_path: Path, token_name: str) -> None:
    """Overwritten token files should have owner-only permissions."""
    token_path = tmp_path / token_name
    token_path.write_text("old-token")
    token_path.chmod(0o644)

    token_repo = TokenRepository(tmp_path)
    getattr(token_repo, f"save_{token_name}")("new-token")

    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
    assert token_path.read_text() == "new-token"


def test_it_saves_the_token_to_the_app_dir(tmp_path: Path) -> None:
    """It should save an access token to the application directory."""
    expected_token = "eydkgjlksjdöflksaefk=="

    token_repo = TokenRepository(tmp_path)
    token_repo.save_access_token(expected_token)

    token_path = tmp_path / "access_token"
    assert token_path.read_text() == expected_token


def test_it_overwrites_an_existing_token(tmp_path: Path) -> None:
    """It should overwrite an existing access token file."""
    p = tmp_path / "access_token"
    p.write_text("eyskljdalksjdaslkjdalknmdwmad")
    expected_token = "eydkgjlksjdöflksaefk=="

    token_repo = TokenRepository(tmp_path)
    token_repo.save_access_token(expected_token)

    token_path = tmp_path / "access_token"
    assert token_path.read_text() == expected_token


def test_it_reads_the_token_when_stored(tmp_path: Path) -> None:
    """It should read an access token when it is already stored on disk."""
    expected_token = "eyaysdasdadwada08sd7a782"
    p = tmp_path / "access_token"
    p.write_text(expected_token)

    token_repo = TokenRepository(tmp_path)
    token = token_repo.load_access_token()

    assert token == expected_token


def test_it_returns_none_if_the_token_doesnt_exist(tmp_path: Path) -> None:
    """It should return None when no access token file exists."""
    token_repo = TokenRepository(tmp_path)
    token = token_repo.load_access_token()

    assert token is None


def test_it_saves_the_refresh_token_to_the_app_dir(tmp_path: Path) -> None:
    """It should save a refresh token to the application directory."""
    expected_token = "refresh-token-example-123"

    token_repo = TokenRepository(tmp_path)
    token_repo.save_refresh_token(expected_token)

    token_path = tmp_path / "refresh_token"
    assert token_path.read_text() == expected_token


def test_it_overwrites_an_existing_refresh_token(tmp_path: Path) -> None:
    """It should overwrite an existing refresh token file."""
    p = tmp_path / "refresh_token"
    p.write_text("old-refresh-token")
    expected_token = "refresh-token-example-123"

    token_repo = TokenRepository(tmp_path)
    token_repo.save_refresh_token(expected_token)

    token_path = tmp_path / "refresh_token"
    assert token_path.read_text() == expected_token


def test_it_reads_the_refresh_token_when_stored(tmp_path: Path) -> None:
    """It should read a refresh token when it is already stored on disk."""
    expected_token = "another-refresh-token"
    p = tmp_path / "refresh_token"
    p.write_text(expected_token)

    token_repo = TokenRepository(tmp_path)
    token = token_repo.load_refresh_token()

    assert token == expected_token


def test_it_returns_none_if_the_refresh_token_doesnt_exist(tmp_path: Path) -> None:
    """It should return None when no refresh token file exists."""
    token_repo = TokenRepository(tmp_path)
    token = token_repo.load_refresh_token()

    assert token is None
