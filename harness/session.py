"""Persist interactive CLI settings next to the active project."""

from __future__ import annotations

import json
from pathlib import Path

from .config import DEFAULT_MODEL, LEGACY_DEFAULT_MODELS

SESSION_FILE = ".qwenagent-session.json"


def _session_path(project_dir: str | Path) -> Path:
    return Path(project_dir).expanduser().resolve() / SESSION_FILE


def load_session(project_dir: str | Path) -> dict:
    path = _session_path(project_dir)
    defaults = {
        "sandbox_root": str(Path(project_dir).expanduser().resolve()),
        "verify_command": None,
        "model": DEFAULT_MODEL,
    }
    if not path.exists():
        return defaults

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return defaults

    if not isinstance(data, dict):
        return defaults


    loaded = {**defaults, **{key: data[key] for key in defaults if key in data}}
    if loaded.get("model") in LEGACY_DEFAULT_MODELS:
        loaded["model"] = DEFAULT_MODEL
    return loaded


def save_session(project_dir: str | Path, **fields) -> None:
    path = _session_path(project_dir)
    current = load_session(project_dir)
    current.update({key: value for key, value in fields.items() if value is not None or key in current})
    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
