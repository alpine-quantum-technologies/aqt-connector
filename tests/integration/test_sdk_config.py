import os

from aqt_connector._sdk_config import ArnicaConfig


def test_it_loads_config_from_the_config_file(tmp_path) -> None:
    p = tmp_path / "config"
    p.write_text('default.client_id = "JOEISTHEBEST"')

    config = ArnicaConfig(tmp_path)

    assert config.client_id == "JOEISTHEBEST"


def test_it_loads_config_from_env_variables(monkeypatch, tmp_path) -> None:
    expected_value = "JOEISTHEBEST"
    monkeypatch.setenv("AQT_CLIENT_ID", expected_value)

    config = ArnicaConfig(tmp_path)

    assert config.client_id == expected_value


def test_it_removes_aqt_prefix_from_env_var_names(monkeypatch, tmp_path) -> None:
    for k in os.environ:
        monkeypatch.delenv(k)
    monkeypatch.setenv("AQT_STORE_ACCESS_TOKEN", "true")

    config = ArnicaConfig(tmp_path)

    assert config.store_access_token is True


def test_env_config_overwrites_file_config(tmp_path, monkeypatch) -> None:
    p = tmp_path / "config"
    p.write_text('default.client_id = "JOEISNOTTHEBEST"')
    expected_value = "JOEISTHEBEST"
    monkeypatch.setenv("AQT_CLIENT_ID", expected_value)

    config = ArnicaConfig(tmp_path)

    assert config.client_id == expected_value
