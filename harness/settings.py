"""Persistent FORGE settings stored in the user config directory."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .config import (
    DEFAULT_AWS_REGION,
    DEFAULT_EC2_INSTANCE_TYPE,
    DEFAULT_EC2_SECURITY_GROUP,
    DOCKERHUB_TOKEN_ENV,
    DOCKERHUB_USERNAME_ENV,
)

CONFIG_DIR = Path(os.environ.get("FORGE_CONFIG_DIR", Path.home() / ".config" / "forge"))
CONFIG_FILE = CONFIG_DIR / "config.json"

KEYS = {
    "dockerhub_username",
    "dockerhub_token",
    "aws_default_region",
    "default_instance_type",
    "security_group_name",
}


def load_settings() -> dict:
    """Read settings from the config file. Missing or corrupt files return empty dict."""
    try:
        payload = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {key: value for key, value in payload.items() if key in KEYS and isinstance(value, str) and value}


def save_settings(values: dict) -> None:
    """Merge and persist settings to the config file."""
    settings = load_settings()
    for key, value in values.items():
        if key in KEYS and isinstance(value, str) and value:
            settings[key] = value
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def dockerhub_credentials() -> tuple[str | None, str | None]:
    """Resolve Docker Hub credentials: env vars first, then persistent settings."""
    settings = load_settings()
    username = os.environ.get(DOCKERHUB_USERNAME_ENV) or settings.get("dockerhub_username")
    token = os.environ.get(DOCKERHUB_TOKEN_ENV) or settings.get("dockerhub_token")
    return username, token


def default_aws_region() -> str:
    """Resolve AWS region: FORGE settings, then AWS CLI config, then built-in default."""
    settings = load_settings()
    return settings.get("aws_default_region") or os.environ.get("AWS_DEFAULT_REGION") or DEFAULT_AWS_REGION


def default_instance_type() -> str:
    settings = load_settings()
    return settings.get("default_instance_type") or DEFAULT_EC2_INSTANCE_TYPE


def default_security_group() -> str:
    settings = load_settings()
    return settings.get("security_group_name") or DEFAULT_EC2_SECURITY_GROUP
