<p align="center">
  <img src="https://img.shields.io/badge/forge--engine-0.1.0-blue" alt="version">
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-purple" alt="license">
</p>

# FORGE Engine

**FORGE** is a terminal-based AI coding-agent harness that lets LLMs autonomously work on software tasks inside a sandboxed environment. It gives the model a fixed set of tools — read, write, list, and run commands — then independently **verifies completion** rather than trusting the model's own claim.

Works with any OpenAI-compatible API (OpenRouter, Ollama, local LLMs, etc.).

---

## Installation

```bash
pip install forge-engine
```

Launch from any terminal:

```bash
forge
```

## Quick Start

```bash
# Set your API key (defaults to OpenRouter)
export OPENROUTER_API_KEY="your-api-key"

# Launch interactive mode
forge

# Or run a one-shot task with verification
forge --task "Fix the bug in calc.py" --verify pytest
```

### Using a Local Model

```bash
forge --base-url http://localhost:11434/v1 --model qwen2.5-coder:7b
```

---

## Features

- **Sandboxed Execution** — Confines all file and command operations to a project directory. Blocks path traversal and absolute paths.
- **Independent Verification** — Runs `pytest`, `npm test`, or any command to confirm the model's work is correct. The model cannot bypass verification.
- **Agentic Loop** — Up to 40 turns per task. The model iteratively reads, writes, runs commands, and decides when it's done.
- **Interactive CLI** — Rich terminal UI with live streaming, code diffs, and slash commands for managing sessions.
- **Session Persistence** — Saves sandbox root, verification command, and model selection per project.
- **One-Shot Mode** — Scriptable single-task execution with `--task` and `--verify` flags.
- **Model Agnostic** — Works with any OpenAI-compatible API: OpenRouter, Ollama, vLLM, or any custom endpoint.

---

## Slash Commands

| Command | Behavior |
|---|---|
| `/cwd <path>` | Change the active sandbox root to `<path>` |
| `/verify <command>` | Set the verification command (`pytest`, `npm test`, etc.) |
| `/model <name>` | Swap the LLM model without restarting |
| `/new-react <name>` | Scaffold a Vite React app with one command |
| `/clear` | Reset the session transcript (keeps settings) |
| `/help` | List all commands |
| `/exit` or `/quit` | Exit cleanly |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    forge CLI                         │
│        (interactive / one-shot mode)                 │
└──────────┬──────────────────────────┬───────────────┘
           │                          │
    ┌──────▼──────┐          ┌───────▼────────┐
    │ Orchestrator │          │  Sandbox       │
    │ (agent loop) │◄────────►│  (filesystem   │
    │              │          │   + commands)  │
    └──────┬───────┘          └────────────────┘
           │
    ┌──────▼───────┐
    │   LLM Client │────► OpenAI-compatible API
    │  (transcript)│      (OpenRouter / Ollama / etc.)
    └──────────────┘
```

| Module | Responsibility |
|---|---|
| `harness/orchestrator.py` | Agentic loop — manages turns, tool calls, guardrails |
| `harness/tools.py` | Tool definitions and dispatch (read, write, list, run, complete) |
| `harness/sandbox.py` | Path and command confinement to a project root |
| `harness/transcript.py` | Conversation history — compaction, trimming, metadata |
| `harness/verifier.py` | Runs a verification command and reports pass/fail |
| `harness/llm_client.py` | OpenAI-compatible chat-completions HTTP client |
| `harness/cli.py` | Interactive terminal UI with rich rendering |
| `harness/session.py` | Persists session state to `.qwenagent-session.json` |

---

## Verification Flow

1. Model calls `task_complete` → harness doesn't trust it
2. Verifier runs the configured command (`pytest`, `npm test`, etc.)
3. If verification passes → task is accepted
4. If verification fails → model gets the failure output and can try again
5. If no verification command is set → auto-detects `pytest`/`npm test`/`make test`, or prompts you

---

## Development

```bash
# Clone and install in editable mode
git clone https://github.com/Devakesavan/Forge-Engine.git
cd Forge-Engine
pip install -e .[test]

# Run tests
python3 -m pytest -q
```

---

## Contributing

Contributions are welcome. Please keep changes focused on one behavior at a time and ensure tests pass:

```bash
pip install -e .[test]
python3 -m pytest -q
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
