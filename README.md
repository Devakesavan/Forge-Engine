<p align="center">
  <a href="https://pypi.org/project/forge-engine/"><img src="https://img.shields.io/pypi/v/forge-engine?color=blue" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-purple" alt="license">
</p>

# FORGE Engine

**FORGE** is a terminal-based AI coding-agent harness that lets LLMs autonomously work on software tasks inside a sandboxed environment. It gives the model a fixed set of tools — read, write, list, and run commands — then independently **verifies completion** rather than trusting the model's own claim.

Works with any OpenAI-compatible API (OpenRouter, Ollama, local LLMs, etc.).

Available on **PyPI**: [forge-engine](https://pypi.org/project/forge-engine/)

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
- **DockerHub to EC2 Deployment** — When explicitly requested, builds a Docker image, pushes it to Docker Hub, launches EC2, and runs the container.

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
| `harness/tools.py` | Tool definitions and dispatch (read, write, list, run, complete, deploy) |
| `harness/sandbox.py` | Path and command confinement to a project root |
| `harness/ec2_deployer.py` | Docker Hub image deployment to AWS EC2 |
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

## AWS EC2 Deployment

FORGE can deploy a Dockerized app to AWS EC2 when the prompt explicitly asks for AWS or EC2 deployment.

Deployment does **not** run for normal coding prompts. The `deploy_dockerhub_to_ec2` tool is blocked unless the current task contains deployment intent such as `deploy this app to AWS EC2`.

### Deployment Architecture

```text
User app
  ↓
Model creates Dockerfile
  ↓
Harness builds local Docker image
  ↓
Harness tags image as username/app-name:tag
  ↓
Harness logs in to Docker Hub
  ↓
Harness pushes image
  ↓
Harness launches EC2
  ↓
EC2 user-data installs Docker
  ↓
EC2 pulls username/app-name:tag
  ↓
EC2 runs docker run -p host_port:container_port
  ↓
Harness returns http://PUBLIC_IP:PORT
```

### Required Local Setup

Install Docker locally and make sure the Docker daemon is running.

#### Configure once with `forge configure`

Instead of exporting variables every session, configure everything once:

```bash
forge configure
```

This interactively prompts for and persists:

- Docker Hub username and access token
- AWS default region
- Default EC2 instance type
- Security group name

Settings are saved to `~/.config/forge/config.json` (override the location with `FORGE_CONFIG_DIR`). The token is stored in plain text locally, so protect the file:

```bash
chmod 600 ~/.config/forge/config.json
```

Environment variables still take precedence over saved settings, which is useful for CI:

```bash
export DOCKERHUB_USERNAME="your-dockerhub-username"
export DOCKERHUB_TOKEN="your-dockerhub-access-token"
```

#### AWS credentials

AWS credentials are handled by the standard AWS tooling — no exports needed:

```bash
aws configure
```

boto3 automatically reads `~/.aws/credentials` and `~/.aws/config`, so once you have run `aws configure` you are done. `forge configure` only stores the FORGE-side defaults such as the deployment region.

The Docker Hub repository must already exist and should be public for the first version, so EC2 can pull it without receiving registry credentials.

### Example Prompt

```text
Dockerize this app and deploy it to AWS EC2 using Docker Hub repo devakesavan/my-app on port 3000.
```

FORGE will expect or create a `Dockerfile`, build the image locally, push it to Docker Hub, create an EC2 instance, and return output like:

```text
Deployment successful.
Image: devakesavan/my-app:latest
Instance ID: i-0123456789abcdef0
Public IP: 13.232.44.21
URL: http://13.232.44.21:3000
Terminate command: aws ec2 terminate-instances --instance-ids i-0123456789abcdef0 --region ap-south-1
```

### Guardrails

- Deployment is opt-in through explicit AWS/EC2 deployment prompts.
- Only `t2.micro` and `t3.micro` instance types are allowed by default.
- Only common app ports are allowed by default: `80`, `3000`, `5000`, `8000`, `8080`.
- AWS and Docker Hub secrets are never sent to the model.
- EC2 instances cost money until stopped or terminated; FORGE prints a terminate command after deployment.

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
