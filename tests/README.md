# Harness Test Suite

Run deterministic tests with:

```bash
pytest tests/ -v
```

The default suite does not call OpenRouter and does not need network access.

## Files

`fake_llm_client.py` provides a scripted `FakeLLMClient` with the same `.chat(messages, tools)` shape as the real model client. Orchestrator tests use it so behavior is repeatable.

`test_sandbox.py` protects filesystem and command isolation: read/write round-trips, nested directory creation, path traversal rejection, command cwd, command timeouts, and directory listing behavior.

`test_transcript.py` protects context management: long tool result truncation, old tool result compaction, and preserving system/user messages.

`test_verifier.py` protects independent verification: successful shell commands pass, failing commands surface exit code and stderr.

`test_orchestrator.py` protects the agent loop: success with independent verification, false completion rejection, stalled responses, repeated-call loop detection, malformed JSON resilience, max-turn limits, model-driven sandbox escape blocking, multi-tool extraction from printed JSON, and allowing `task_complete` after work done in a previous turn.

`test_cli.py` protects interactive/session behavior: `/cwd` changes the sandbox used by subsequent tasks, missing verification reaches the explicit human fallback, and `.qwenagent-session.json` round-trips settings.

`test_live_smoke.py` is skipped by default. Run it manually when `OPENROUTER_API_KEY` is set:

```bash
RUN_LIVE_SMOKE=1 python3 -m pytest tests/test_live_smoke.py -v
```

Set `LIVE_SMOKE_MODEL=<model-name>` to test a model other than the default Nemotron model.
