import builtins

from harness import cli
from harness.session import DEFAULT_MODEL, load_session, save_session

from tests.fake_llm_client import response, tool_call, FakeLLMClient
from harness import orchestrator

import json


def test_cwd_command_changes_sandbox_for_subsequent_task(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    captured_roots = []
    inputs = iter([f"/cwd {target}", "do something", "/exit"])

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    monkeypatch.setattr(cli, "_banner", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "_help", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "_print", lambda *args, **kwargs: None)

    def fake_run(task, sandbox_root, *args, **kwargs):
        captured_roots.append(sandbox_root)
        return {"status": "accepted_without_automated_verification"}

    monkeypatch.setattr(cli, "run", fake_run)

    cli.main()

    assert captured_roots == [str(target.resolve())]


def test_no_verify_command_reaches_human_fallback_result(tmp_path, monkeypatch):
    fake = FakeLLMClient(
        [
            response(
                tool_calls=[
                    tool_call("write_file", json.dumps({"path": "done.txt", "content": "ok"})),
                    tool_call("task_complete", json.dumps({"summary": "done"})),
                ]
            )
        ]
    )
    monkeypatch.setattr(orchestrator, "LocalLLMClient", lambda *args, **kwargs: fake)

    result = orchestrator.run("write a file", str(tmp_path), None)

    assert result["status"] == "needs_verification"


def test_session_file_round_trips_settings(tmp_path):
    save_session(tmp_path, sandbox_root="/tmp/sandbox", verify_command="pytest", model="model-a")

    loaded = load_session(tmp_path)

    assert loaded == {
        "sandbox_root": "/tmp/sandbox",
        "verify_command": "pytest",
        "model": "model-a",
    }


def test_load_session_defaults_when_no_file_exists(tmp_path):
    assert load_session(tmp_path) == {
        "sandbox_root": str(tmp_path.resolve()),
        "verify_command": None,
        "model": DEFAULT_MODEL,
    }
