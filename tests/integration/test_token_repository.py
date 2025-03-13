from pathlib import Path

from aqt_connector.infrastructure.token_repository import TokenRepository


def test_it_saves_the_token_to_the_app_dir(tmp_path: Path) -> None:
    expected_token = "eydkgjlksjdöflksaefk=="

    token_repo = TokenRepository(tmp_path)
    token_repo.save(expected_token)

    token_path = tmp_path / "access_token"
    assert token_path.read_text() == expected_token


def test_it_overwrites_an_existing_token(tmp_path: Path) -> None:
    p = tmp_path / "access_token"
    p.write_text("eyskljdalksjdaslkjdalknmdwmad")
    expected_token = "eydkgjlksjdöflksaefk=="

    token_repo = TokenRepository(tmp_path)
    token_repo.save(expected_token)

    token_path = tmp_path / "access_token"
    assert token_path.read_text() == expected_token


def test_it_reads_the_token_when_stored(tmp_path: Path) -> None:
    expected_token = "eyaysdasdadwada08sd7a782"
    p = tmp_path / "access_token"
    p.write_text(expected_token)

    token_repo = TokenRepository(tmp_path)
    token = token_repo.load()

    assert token == expected_token


def test_it_returns_none_if_the_token_doesnt_exist(tmp_path: Path) -> None:
    token_repo = TokenRepository(tmp_path)
    token = token_repo.load()

    assert token is None
