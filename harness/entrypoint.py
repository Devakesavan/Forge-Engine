"""Command-line entry point for FORGE."""

from __future__ import annotations

import argparse
from pathlib import Path

from .cli import main as cli_main
from .config import DEFAULT_BASE_URL, DEFAULT_MODEL
from .orchestrator import run


DEFAULT_TASK = "Fix the bug in calc.py so the pytest suite passes."
DEFAULT_SANDBOX_ROOT = str(Path(__file__).resolve().parents[1] / "sandbox_project")
DEFAULT_VERIFY_COMMAND = "pytest"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FORGE, the AI harness engine.")
    parser.add_argument("--task", help="Run one task non-interactively and exit.")
    parser.add_argument("--verify", help="Verification command for one-shot mode.")
    parser.add_argument("--sandbox", default=DEFAULT_SANDBOX_ROOT, help="Sandbox root for one-shot mode.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model name.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenAI-compatible API base URL.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if not args.task:
        cli_main()
        return

    result = run(
        args.task or DEFAULT_TASK,
        args.sandbox,
        args.verify or DEFAULT_VERIFY_COMMAND,
        base_url=args.base_url,
        model=args.model,
    )
    print(result)
