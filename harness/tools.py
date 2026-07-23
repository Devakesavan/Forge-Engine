"""Expose the fixed set of model-callable tools for the agent loop."""

from __future__ import annotations

import json

from .sandbox import SandboxError


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file from the sandbox.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a UTF-8 text file inside the sandbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a sandbox directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "default": "."}},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command with the sandbox root as cwd.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Request independent verification of the completed task.",
            "parameters": {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
                "additionalProperties": False,
            },
        },
    },
]


def dispatch_tool(sandbox, name: str, args: dict) -> str:
    """Route a validated tool call to the sandbox and return text for the model."""
    try:
        if name == "read_file":
            return sandbox.read_file(args["path"])
        if name == "write_file":
            return sandbox.write_file(args["path"], args["content"])
        if name == "list_files":
            return sandbox.list_files(args.get("path", "."))
        if name == "run_command":
            return json.dumps(sandbox.run_command(args["command"]), indent=2)
        if name == "task_complete":
            return f"Task completion requested: {args.get('summary', '')}"
        return f"ERROR: unknown tool: {name}"
    except (KeyError, TypeError) as exc:
        return f"ERROR: invalid arguments for {name}: {exc}"
    except SandboxError as exc:
        return f"ERROR: sandbox violation: {exc}"
    except Exception as exc:  # Keep model mistakes inside the loop, not the harness.
        return f"ERROR: tool {name} failed: {type(exc).__name__}: {exc}"
