"""Command-line entry point for FORGE."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

from .cli import main as cli_main
from .config import DEFAULT_BASE_URL, DEFAULT_MAX_TOKENS, DEFAULT_MODEL, MAX_TOKENS_ENV
from .orchestrator import run
from .settings import CONFIG_FILE, dockerhub_credentials, load_settings, save_settings


DEFAULT_TASK = "Fix the bug in calc.py so the pytest suite passes."
DEFAULT_SANDBOX_ROOT = str(Path(__file__).resolve().parents[1] / "sandbox_project")
DEFAULT_VERIFY_COMMAND = "pytest"


def _configure_interactive() -> int:
    """Prompt once and persist Docker Hub + deployment defaults."""
    print(f"FORGE configuration will be saved to {CONFIG_FILE}\n")
    print("(Leave a field empty to keep its current value.)")

    current = load_settings()
    username, token = dockerhub_credentials()

    new_username = input(f"Docker Hub username [{username or 'not set'}]: ").strip() or username or ""
    new_token = getpass.getpass(f"Docker Hub token [{'(set)' if token else 'not set'}]: ").strip() or token or ""
    new_region = input(f"AWS default region [{current.get('aws_default_region') or 'ap-south-1'}]: ").strip() or current.get("aws_default_region") or ""
    new_instance = input(f"Default EC2 instance type [{current.get('default_instance_type') or 't3.micro'}]: ").strip() or current.get("default_instance_type") or ""
    new_group = input(f"Security group name [{current.get('security_group_name') or 'forge-engine-deploy-sg'}]: ").strip() or current.get("security_group_name") or ""

    save_settings(
        {
            "dockerhub_username": new_username,
            "dockerhub_token": new_token,
            "aws_default_region": new_region,
            "default_instance_type": new_instance,
            "security_group_name": new_group,
        }
    )
    print(f"\nSaved configuration to {CONFIG_FILE}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FORGE, the AI harness engine.")
    parser.add_argument("--task", help="Run one task non-interactively and exit.")
    parser.add_argument("--verify", help="Verification command for one-shot mode.")
    parser.add_argument("--sandbox", default=DEFAULT_SANDBOX_ROOT, help="Sandbox root for one-shot mode.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model name.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenAI-compatible API base URL.")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.environ.get(MAX_TOKENS_ENV, DEFAULT_MAX_TOKENS)),
        help="Maximum output tokens per LLM request (default: 2048, env: FORGE_MAX_TOKENS).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    if argv == ["configure"]:
        raise SystemExit(_configure_interactive())

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
        max_tokens=args.max_tokens,
    )
    print(result)
