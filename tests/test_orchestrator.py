import json

import requests

from harness import orchestrator
from harness.transcript import Transcript

from tests.fake_llm_client import FakeLLMClient, response, tool_call


def install_fake_client(monkeypatch, fake):
    monkeypatch.setattr(orchestrator, "LocalLLMClient", lambda *args, **kwargs: fake)


def make_python_project(root):
    (root / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (root / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )


def test_success_path_independently_verifies_fix(tmp_path, monkeypatch):
    make_python_project(tmp_path)
    fake = FakeLLMClient(
        [
            response(tool_calls=[tool_call("read_file", json.dumps({"path": "calc.py"}))]),
            response(
                tool_calls=[
                    tool_call("write_file", json.dumps({"path": "calc.py", "content": "def add(a, b):\n    return a + b\n"}))
                ]
            ),
            response(tool_calls=[tool_call("run_command", json.dumps({"command": "python3 -m pytest -q"}))]),
            response(tool_calls=[tool_call("task_complete", json.dumps({"summary": "fixed add"}))]),
        ]
    )
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("fix calc", str(tmp_path), "python3 -m pytest -q")

    assert result["status"] == "success"
    assert result["verification"]["passed"] is True


def test_false_completion_is_not_trusted_when_verification_fails(tmp_path, monkeypatch):
    transcript = Transcript("seed")
    fake = FakeLLMClient(
        [
            response(tool_calls=[tool_call("run_command", json.dumps({"command": "true"}))]),
            response(tool_calls=[tool_call("task_complete", json.dumps({"summary": "done"}))]),
            response(content="No more tool calls."),
        ]
    )
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("pretend this is done", str(tmp_path), "test -f fixed.txt", transcript=transcript)

    assert result["status"] != "success"
    assert any(
        message["role"] == "user" and "Independent verification failed" in message["content"]
        for message in transcript.messages
    )


def test_premature_task_complete_without_work_is_rejected(tmp_path, monkeypatch):
    transcript = Transcript("seed")
    fake = FakeLLMClient(
        [
            response(tool_calls=[tool_call("task_complete", json.dumps({"summary": "done"}))]),
            response(content="No tools."),
        ]
    )
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("create something", str(tmp_path), "true", transcript=transcript)

    assert result["status"] == "stalled"
    assert any("without doing any actual work" in message["content"] for message in transcript.messages)


def test_stalled_path_returns_stalled(tmp_path, monkeypatch):
    fake = FakeLLMClient([response(content="I have no tools to call.")])
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("do work", str(tmp_path), None)

    assert result["status"] == "stalled"


def test_stuck_path_stops_after_three_identical_tool_calls(tmp_path, monkeypatch):
    repeated = response(tool_calls=[tool_call("list_files", json.dumps({"path": "."}))])
    fake = FakeLLMClient([repeated, repeated, repeated])
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("loop", str(tmp_path), None)

    assert result == {"status": "stuck", "turns": 3, "reason": "repeated identical tool calls"}
    assert len(fake.calls) == 3


def test_malformed_json_does_not_crash_and_next_valid_call_can_succeed(tmp_path, monkeypatch):
    transcript = Transcript("seed")
    fake = FakeLLMClient(
        [
            response(tool_calls=[tool_call("write_file", '{"path": "broken.txt"')]),
            response(tool_calls=[tool_call("write_file", json.dumps({"path": "fixed.txt", "content": "ok"}))]),
            response(tool_calls=[tool_call("task_complete", json.dumps({"summary": "fixed"}))]),
        ]
    )
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("handle bad json", str(tmp_path), "test -f fixed.txt", transcript=transcript)

    assert result["status"] == "success"
    assert any("invalid JSON arguments" in message["content"] for message in transcript.messages)


def test_max_turns_path_stops_at_configured_limit(tmp_path, monkeypatch):
    fake = FakeLLMClient(
        [
            response(tool_calls=[tool_call("run_command", json.dumps({"command": f"printf {turn}"}))])
            for turn in range(orchestrator.MAX_TURNS)
        ]
    )
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("never finish", str(tmp_path), None)

    assert result == {"status": "max_turns_exceeded", "turns": orchestrator.MAX_TURNS}
    assert len(fake.calls) == orchestrator.MAX_TURNS


def test_model_sandbox_escape_attempt_is_blocked(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    transcript = Transcript("seed")
    fake = FakeLLMClient(
        [
            response(tool_calls=[tool_call("write_file", json.dumps({"path": "../outside.txt", "content": "x"}))]),
            response(content="No tools."),
        ]
    )
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("escape", str(root), None, transcript=transcript)

    assert result["status"] == "stalled"
    assert not outside.exists()
    assert any("sandbox violation" in message["content"] for message in transcript.messages)


def test_printed_text_tool_calls_extracts_all_calls_in_one_turn(tmp_path, monkeypatch):
    fake = FakeLLMClient(
        [
            response(
                content=(
                    '```json\n{"name": "write_file", "arguments": {"path": "a.txt", "content": "a"}}\n```\n'
                    '```json\n{"name": "write_file", "arguments": {"path": "b.txt", "content": "b"}}\n```\n'
                    '```json\n{"name": "task_complete", "arguments": {"summary": "wrote files"}}\n```'
                )
            )
        ]
    )
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("write two files", str(tmp_path), "test -f a.txt && test -f b.txt")

    assert result["status"] == "success"
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "a"
    assert (tmp_path / "b.txt").read_text(encoding="utf-8") == "b"


def test_task_complete_after_work_in_previous_turn_is_allowed(tmp_path, monkeypatch):
    fake = FakeLLMClient(
        [
            response(tool_calls=[tool_call("write_file", json.dumps({"path": "done.txt", "content": "ok"}))]),
            response(tool_calls=[tool_call("task_complete", json.dumps({"summary": "done"}))]),
        ]
    )
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("write then finish", str(tmp_path), "test -f done.txt")

    assert result["status"] == "success"


def test_extracted_text_tool_calls_do_not_store_full_model_text(tmp_path, monkeypatch):
    transcript = Transcript("seed")
    huge_content = (
        "Before" + ("x" * 20_000) +
        '```json\n{"name": "write_file", "arguments": {"path": "a.txt", "content": "a"}}\n```\n'
        '```json\n{"name": "task_complete", "arguments": {"summary": "done"}}\n```'
    )
    fake = FakeLLMClient([response(content=huge_content)])
    install_fake_client(monkeypatch, fake)

    result = orchestrator.run("write file", str(tmp_path), "test -f a.txt", transcript=transcript)

    assert result["status"] == "success"
    assistant_messages = [message for message in transcript.messages if message["role"] == "assistant"]
    assert assistant_messages[-1]["content"] == "[tool calls extracted from model text]"
    assert len(assistant_messages[-1]["content"]) < 100


class TimeoutClient:
    def chat(self, messages, tools, temperature: float = 0.2):
        raise requests.ReadTimeout("model API timed out")


class ErrorPayloadClient:
    def chat(self, messages, tools, temperature: float = 0.2):
        return {"error": {"message": "invalid api key"}}


def test_llm_request_timeout_returns_error_instead_of_crashing(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "LocalLLMClient", lambda *args, **kwargs: TimeoutClient())

    result = orchestrator.run("do work", str(tmp_path), None)

    assert result["status"] == "llm_error"
    assert result["turns"] == 1
    assert "ReadTimeout" in result["error"]


def test_llm_error_payload_returns_error_instead_of_crashing(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "LocalLLMClient", lambda *args, **kwargs: ErrorPayloadClient())

    result = orchestrator.run("do work", str(tmp_path), None)

    assert result["status"] == "llm_error"
    assert "invalid api key" in result["error"]
