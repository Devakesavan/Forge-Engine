"""Restrict all filesystem and shell access to one project root."""

from __future__ import annotations

import subprocess
from pathlib import Path


class SandboxError(Exception):
    """Raised when an operation attempts to escape the sandbox."""


class Sandbox:
    """Filesystem and command runner confined to a single root directory."""

    def __init__(self, root: str | Path, command_timeout: int = 30):
        self.root = Path(root).expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise SandboxError(f"Sandbox root is not a directory: {self.root}")
        self.command_timeout = command_timeout

    def _text(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    def _resolve(self, rel_path: str | Path) -> Path:
        path = Path(rel_path)
        if path.is_absolute():
            raise SandboxError(f"Absolute paths are not allowed: {rel_path}")

        resolved = (self.root / path).resolve(strict=False)
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise SandboxError(f"Path escapes sandbox: {rel_path}") from exc
        return resolved

    def read_file(self, rel_path: str) -> str:
        path = self._resolve(rel_path)
        if not path.is_file():
            raise SandboxError(f"Not a file: {rel_path}")
        return path.read_text(encoding="utf-8")

    def write_file(self, rel_path: str, content: str) -> str:
        path = self._resolve(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to {rel_path}"

    def list_files(self, rel_path: str = ".") -> str:
        path = self._resolve(rel_path)
        if not path.exists():
            raise SandboxError(f"Path does not exist: {rel_path}")
        if path.is_file():
            return rel_path

        entries = []
        for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            child.relative_to(self.root)
            suffix = "/" if child.is_dir() else ""
            entries.append(f"{child.relative_to(self.root)}{suffix}")
        return "\n".join(entries)

    def run_command(self, command: str) -> dict[str, int | str]:
        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=self.command_timeout,
            )
            return {
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "exit_code": -1,
                "stdout": self._text(exc.stdout),
                "stderr": f"Command timed out after {self.command_timeout} seconds: {command}",
            }
