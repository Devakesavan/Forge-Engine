import pytest
from pathlib import Path

from harness import settings as settings_module
from harness.settings import dockerhub_credentials, load_settings, save_settings


def test_load_settings_returns_empty_for_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "CONFIG_FILE", tmp_path / "config.json")

    assert load_settings() == {}


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "CONFIG_FILE", tmp_path / "config.json")

    save_settings({"dockerhub_username": "devakesavan", "dockerhub_token": "tok-123"})
    assert load_settings() == {"dockerhub_username": "devakesavan", "dockerhub_token": "tok-123"}


def test_save_ignores_unknown_keys_and_empty_values(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "CONFIG_FILE", tmp_path / "config.json")

    save_settings({"dockerhub_username": "devakesavan", "evil_key": "x", "aws_default_region": ""})
    assert load_settings() == {"dockerhub_username": "devakesavan"}


def test_env_vars_take_precedence_over_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "CONFIG_FILE", tmp_path / "config.json")
    save_settings({"dockerhub_username": "from-config", "dockerhub_token": "token-config"})
    monkeypatch.setenv("DOCKERHUB_USERNAME", "from-env")
    monkeypatch.setenv("DOCKERHUB_TOKEN", "token-env")

    username, token = dockerhub_credentials()

    assert username == "from-env"
    assert token == "token-env"


def test_settings_used_when_env_vars_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "CONFIG_FILE", tmp_path / "config.json")
    save_settings({"dockerhub_username": "from-config", "dockerhub_token": "token-config"})
    monkeypatch.delenv("DOCKERHUB_USERNAME", raising=False)
    monkeypatch.delenv("DOCKERHUB_TOKEN", raising=False)

    username, token = dockerhub_credentials()

    assert username == "from-config"
    assert token == "token-config"


def test_corrupt_config_file_returns_empty(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(settings_module, "CONFIG_FILE", config_file)

    assert load_settings() == {}


def test_configure_command_saves_settings(tmp_path, monkeypatch, capsys):
    config_file = tmp_path / "forge" / "config.json"
    config_file.parent.mkdir(parents=True)
    monkeypatch.setattr(settings_module, "CONFIG_FILE", config_file)
    answers = iter(["devakesavan", "tok-123", "us-east-1", "t2.micro", "custom-sg"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr("getpass.getpass", lambda prompt: next(answers))

    from harness.entrypoint import main

    with pytest.raises(SystemExit) as exc_info:
        main(["configure"])

    assert exc_info.value.code == 0
    assert load_settings() == {
        "dockerhub_username": "devakesavan",
        "dockerhub_token": "tok-123",
        "aws_default_region": "us-east-1",
        "default_instance_type": "t2.micro",
        "security_group_name": "custom-sg",
    }
