"""Maintain bounded OpenAI-style conversation history for the model."""

from __future__ import annotations


MAX_TOOL_RESULT_CHARS = 4000


def cap_tool_result(content: str, limit: int = MAX_TOOL_RESULT_CHARS) -> str:
    if len(content) <= limit:
        return content
    return content[:limit] + f"\n...[truncated {len(content) - limit} characters]"


class Transcript:
    """OpenAI message list with compaction for old tool outputs."""

    def __init__(self, task: str, recent_tool_turns: int = 4):
        self.recent_tool_turns = recent_tool_turns
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are a coding agent. You MUST use the available tools (read_file, "
                    "write_file, list_files, run_command) to inspect and edit files in order to "
                    "complete the task. Do NOT call task_complete until you have actually created "
                    "or modified files using write_file, or executed commands using run_command. "
                    "Acknowledging or summarizing the task is not completion. "
                    "All paths are relative to the sandbox root. When you believe the task "
                    "is done, call task_complete with a concise summary. Shell commands run "
                    "non-interactively, so use flags or environment variables such as --yes, "
                    "-y, or CI=1 when a command might otherwise prompt for input."
                ),
            },
            {"role": "user", "content": task},
        ]

    def append_assistant(self, message: dict) -> None:
        stored = {"role": "assistant", "content": message.get("content") or ""}
        if message.get("tool_calls"):
            stored["tool_calls"] = message["tool_calls"]
        self.messages.append(stored)

    def append_tool(self, tool_call_id: str, content: str, turn: int) -> None:
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": cap_tool_result(content),
                "_turn": turn,
            }
        )

    def append_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def compact(self, current_turn: int) -> None:
        cutoff = current_turn - self.recent_tool_turns
        for message in self.messages:
            if message.get("role") == "tool" and message.get("_turn", current_turn) < cutoff:
                message["content"] = "[older tool result compacted to save context]"

    def for_api(self) -> list[dict]:
        clean = []
        for message in self.messages:
            clean.append({key: value for key, value in message.items() if not key.startswith("_")})
        return clean
