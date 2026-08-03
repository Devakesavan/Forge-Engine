"""Drive the agentic loop between the model API, tools, and verifier."""

from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os

import requests

from .config import API_KEY_ENV, DEFAULT_BASE_URL, DEFAULT_MODEL
from .llm_client import LocalLLMClient
from .sandbox import Sandbox
from .tools import TOOLS, dispatch_tool
from .transcript import Transcript, cap_tool_result
from .verifier import verify


MAX_TURNS = 40
CONSOLE_RESULT_CHARS = 1000
TOOL_NAMES = {tool["function"]["name"] for tool in TOOLS}


def _turn_signature(tool_calls: list[dict]) -> str:
    parts = []
    for call in tool_calls:
        function = call.get("function", {})
        parts.append(f"{function.get('name', '')}:{function.get('arguments') or '{}'}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _console_cap(text: str, limit: int = CONSOLE_RESULT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[console truncated {len(text) - limit} characters]"


def _plain_emit(event_type: str, data: dict) -> None:
    print(data.get("text", ""))


FAILURE_KEYWORDS = {"cannot", "cannot be", "fail", "failed", "not possible", "unable"}


def _is_failure_summary(summary: str) -> bool:
    lower = summary.lower()
    return any(kw in lower for kw in FAILURE_KEYWORDS)


def _detect_verify_command(sandbox: Sandbox) -> str | None:
    files = set(sandbox.list_files(".").splitlines())

    if "pytest.ini" in files:
        return "pytest"

    if "pyproject.toml" in files:
        content = sandbox.read_file("pyproject.toml")
        if "[tool.pytest" in content:
            return "pytest"

    if "package.json" in files:
        content = sandbox.read_file("package.json")
        try:
            package = json.loads(content)
        except json.JSONDecodeError:
            package = {}
        if isinstance(package.get("scripts"), dict) and "test" in package["scripts"]:
            return "npm test"

    if "Makefile" in files:
        content = sandbox.read_file("Makefile")
        if any(line.startswith("test:") for line in content.splitlines()):
            return "make test"

    return None


def _api_error_message(payload: dict) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or error)
    if error:
        return str(error)
    return str(payload)


def _chat_message(response: dict) -> dict:
    if "error" in response:
        raise requests.RequestException(_api_error_message(response))
    choices = response.get("choices")
    if not choices or not isinstance(choices, list):
        raise requests.RequestException(f"API response missing choices: {response}")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise requests.RequestException(f"API response missing message: {response}")
    return message


def _build_write_diff(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def _find_braced_object(text: str, start: int) -> str | None:
    depth = 0
    quote = ""
    triple_quote = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if quote:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if triple_quote and text.startswith(quote * 3, index):
                quote = ""
                triple_quote = False
                continue
            if not triple_quote and char == quote:
                quote = ""
                continue
            continue

        if text.startswith('"""', index) or text.startswith("'''", index):
            quote = char
            triple_quote = True
            continue
        if char in {'"', "'"}:
            quote = char
            triple_quote = False
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None


def _load_printed_tool_object(text: str) -> dict | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        try:
            value = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            return None
    return value if isinstance(value, dict) else None


def _extract_text_tool_call(content: str, turn: int) -> list[dict]:
    """Extract ALL printed tool-call objects from model text (not just the first)."""
    tool_calls: list[dict] = []
    seen: set[str] = set()
    for index, char in enumerate(content):
        if char != "{":
            continue
        candidate = _find_braced_object(content, index)
        if not candidate:
            continue
        value = _load_printed_tool_object(candidate)
        if value is None:
            continue

        name = value.get("name")
        arguments = value.get("arguments", {})
        if name in TOOL_NAMES and isinstance(arguments, dict):
            sig = f"{name}:{json.dumps(arguments, sort_keys=True)}"
            if sig not in seen:
                seen.add(sig)
                tool_calls.append(
                    {
                        "id": f"text-call-{turn}-{len(tool_calls)}",
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": json.dumps(arguments),
                        },
                    }
                )
    return tool_calls


def run(
    task: str,
    sandbox_root: str,
    test_command: str | None,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    max_tokens: int | None = None,
    transcript: Transcript | None = None,
    on_event=None,
    command_timeout: int = 300,
) -> dict:
    emit = (
        (lambda event_type, **data: on_event(event_type, data))
        if on_event
        else (lambda event_type, **data: _plain_emit(event_type, data))
    )
    sandbox = Sandbox(sandbox_root, command_timeout=command_timeout)
    client = LocalLLMClient(
        base_url=base_url,
        model=model,
        api_key=api_key or os.environ.get(API_KEY_ENV, ""),
        max_tokens=max_tokens,
    )
    if transcript is None:
        transcript = Transcript(task)
    else:
        transcript.append_user(task)
    repeated_signature = None
    repeated_count = 0
    last_summary = ""
    work_performed = False

    for turn in range(1, MAX_TURNS + 1):
        emit("turn_start", text=f"--- turn {turn} ---", turn=turn)
        transcript.compact(turn)
        try:
            response = client.chat(transcript.for_api(), TOOLS)
            message = _chat_message(response)
        except requests.RequestException as exc:
            result = {
                "status": "llm_error",
                "turns": turn,
                "error": f"{type(exc).__name__}: {exc}",
            }
            emit("llm_error", text=f"[llm error] {result['error']}", result=result)
            return result
        content = message.get("content") or ""
        if content:
            emit("model_text", text=f"[model] {content}", content=content)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls and content:
            tool_calls = _extract_text_tool_call(content, turn)
            if tool_calls:
                message = dict(message)
                message["tool_calls"] = tool_calls
                message["content"] = "[tool calls extracted from model text]"

        transcript.append_assistant(message)

        if not tool_calls:
            result = {"status": "stalled", "turns": turn, "last_message": content}
            emit("stalled", text=f"[stalled] no tool calls on turn {turn}", result=result)
            return result

        signature = _turn_signature(tool_calls)
        if signature == repeated_signature:
            repeated_count += 1
        else:
            repeated_signature = signature
            repeated_count = 1
        if repeated_count >= 3:
            result = {"status": "stuck", "turns": turn, "reason": "repeated identical tool calls"}
            emit("stuck", text="[stuck] repeated identical tool calls", result=result)
            return result

        saw_task_complete = False
        did_work = False
        for call in tool_calls:
            function = call.get("function", {})
            name = function.get("name", "")
            args_text = function.get("arguments") or "{}"
            emit("tool_call", text=f"[tool call] {name}({args_text})", name=name, arguments=args_text)

            try:
                args = json.loads(args_text)
                if not isinstance(args, dict):
                    raise ValueError("tool arguments must be a JSON object")
            except (json.JSONDecodeError, ValueError) as exc:
                result = f"ERROR: invalid JSON arguments for {name}: {exc}"
                transcript.append_tool(call.get("id", f"call-{turn}"), result, turn)
                emit("tool_result", text=f"[tool result] {result}", result=result)
                continue

            if name == "task_complete":
                saw_task_complete = True
                last_summary = args.get("summary", "")

            write_diff = ""
            if name == "write_file" and isinstance(args.get("path"), str) and isinstance(args.get("content"), str):
                try:
                    before = sandbox.read_file(args["path"])
                except Exception:
                    before = ""
                write_diff = _build_write_diff(args["path"], before, args["content"])

            result = dispatch_tool(sandbox, name, args)
            if name in {"write_file", "run_command"} and not result.startswith("ERROR:"):
                did_work = True
                work_performed = True
            capped = cap_tool_result(result)
            emit("tool_result", text=f"[tool result] {_console_cap(capped)}", result=capped)
            transcript.append_tool(call.get("id", f"call-{turn}"), capped, turn)
            if write_diff and not result.startswith("ERROR:"):
                emit(
                    "code_diff",
                    text=f"[code diff] {args['path']}\n{_console_cap(write_diff, 4000)}",
                    path=args["path"],
                    diff=write_diff,
                )

        if saw_task_complete and not (did_work or work_performed):
            emit(
                "tool_result",
                text="ERROR: task_complete called without doing any work. You must use write_file "
                      "or run_command to actually complete the task before calling task_complete.",
                result="ERROR: no work was done",
            )
            transcript.append_user(
                "Your previous turn attempted to call task_complete without doing any actual work. "
                "You MUST use write_file or run_command to complete the task before calling task_complete. "
                "Do not acknowledge or summarize the task — actually do it."
            )
            continue

        if saw_task_complete:
            verify_command = test_command or _detect_verify_command(sandbox)
            if verify_command is None:
                result = {
                    "status": "needs_verification",
                    "summary": last_summary,
                    "turns": turn,
                }
                emit(
                    "needs_verification",
                    text="[verifier] no verification command is set",
                    result=result,
                )
                return result

            emit(
                "verifier_start",
                text="[verifier] independently re-running verification command...",
                command=verify_command,
            )
            verification = verify(sandbox, verify_command)
            emit(
                "verifier_result",
                text=f"[verifier] {'passed' if verification['passed'] else 'failed'}",
                verification=verification,
            )
            if verification["passed"] and not _is_failure_summary(last_summary):
                result = {
                    "status": "success",
                    "summary": last_summary,
                    "verification": verification,
                }
                emit("success", text="[success] verification passed", result=result)
                return result
            if verification["passed"]:
                text = "[verifier] passed but agent claims failure — continuing"
            else:
                text = "[verifier] failed — continuing"
            emit("verifier_result", text=text, verification=verification)
            transcript.append_user(
                "Independent verification failed. Continue fixing the task.\n"
                + json.dumps(verification, indent=2)
            )

    result = {"status": "max_turns_exceeded", "turns": MAX_TURNS}
    emit("max_turns", text=f"[max turns] exceeded {MAX_TURNS} turns", result=result)
    return result
