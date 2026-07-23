"""Independently decide whether the agent's claimed completion is true."""

from __future__ import annotations


def verify(sandbox, test_command: str) -> dict:
    """Run the real verification command; the model's claim is not trusted."""
    result = sandbox.run_command(test_command)
    return {
        "passed": result["exit_code"] == 0,
        "exit_code": result["exit_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }
