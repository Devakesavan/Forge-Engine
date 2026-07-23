"""Interactive shell for running multiple local-agent tasks in one session."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .config import API_KEY_ENV, DEFAULT_BASE_URL
from .orchestrator import run
from .sandbox import Sandbox, SandboxError
from .session import DEFAULT_MODEL, load_session, save_session
from .transcript import Transcript


BASE_URL = DEFAULT_BASE_URL

try:
    from rich.align import Align
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table

    console = Console()
except ImportError:  # pragma: no cover - depends on optional local package
    Align = None
    Console = None
    Markdown = None
    Panel = None
    Syntax = None
    Table = None
    console = None


HELP_ROWS = [
    ("/cwd <path>", "Change the active sandbox root."),
    ("/verify <command>", "Set the verification command."),
    ("/model <name>", "Swap the model for subsequent tasks."),
    ("/new-react <name>", "Scaffold a Vite React app."),
    ("/clear", "Reset the transcript for this session."),
    ("/help", "Show this help."),
    ("/exit or /quit", "Exit cleanly."),
]

FORGE_LOGO = """
███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
█████╗  ██║   ██║██████╔╝██║  ███╗█████╗
██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
""".strip("\n")


def _default_project_dir() -> Path:
    sample = Path.cwd() / "sandbox_project"
    return sample.resolve() if sample.is_dir() else Path.cwd().resolve()


def _print(text: str) -> None:
    if console:
        console.print(text)
    else:
        print(text)


def _print_logo() -> None:
    if console and Align:
        console.print()
        console.print(Align.center(f"[bold cyan]{FORGE_LOGO}[/bold cyan]", vertical="middle"))
        console.print(Align.center("[dim]AI harness engine[/dim]"))
        console.print()
        return

    width = shutil.get_terminal_size((100, 20)).columns
    print()
    for line in FORGE_LOGO.splitlines():
        print(line.center(width))
    print("AI harness engine".center(width))
    print()


def _print_result(result: dict) -> None:
    status = result.get("status", "unknown")
    turns = result.get("turns")
    status_line = f"Status: {status}"
    if turns is not None:
        status_line += f" ({turns} turn{'s' if turns != 1 else ''})"

    error = result.get("error") or ""
    suggestion = None
    if any(term in error.lower() for term in ("resourceexhausted", "rate limit", "request limit")):
        suggestion = "Suggestion: wait and retry, or switch to another OpenRouter model with /model <name>."

    if console and Panel:
        style = "green" if status == "success" else "yellow" if status in {"stalled", "needs_verification"} else "red"
        lines = [status_line]
        if result.get("summary"):
            lines.append(f"Summary: {result['summary']}")
        if result.get("error"):
            lines.append(f"Error: {result['error']}")
        if suggestion:
            lines.append(suggestion)
        if status == "stalled" and result.get("last_message"):
            lines.append("Reason: model answered directly without calling tools")
        verification = result.get("verification")
        if isinstance(verification, dict):
            lines.append(f"Verification: {'passed' if verification.get('passed') else 'failed'}")
        console.print(Panel("\n".join(lines), title="result", border_style=style))
        return

    print(status_line)
    if result.get("summary"):
        print(f"Summary: {result['summary']}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    if suggestion:
        print(suggestion)
    if status == "stalled" and result.get("last_message"):
        print("Reason: model answered directly without calling tools")


def _banner(sandbox_root: str, verify_command: str | None, model: str) -> None:
    verify = verify_command or "not set"
    _print_logo()
    if console and Panel:
        console.print(
            Panel.fit(
                f"Model: [cyan]{model}[/cyan]\n"
                f"Provider: [cyan]{BASE_URL}[/cyan]\n"
                f"Sandbox: [green]{sandbox_root}[/green]\n"
                f"Verify: [yellow]{verify}[/yellow]",
                title="harness engine",
            )
        )
    else:
        print("FORGE")
        print(f"Model: {model}")
        print(f"Provider: {BASE_URL}")
        print(f"Sandbox: {sandbox_root}")
        print(f"Verify: {verify}")
        print("Install rich with `pip install rich` for a nicer UI.")


def _help() -> None:
    if console and Table:
        table = Table(title="Slash Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Behavior")
        for command, behavior in HELP_ROWS:
            table.add_row(command, behavior)
        console.print(table)
    else:
        for command, behavior in HELP_ROWS:
            print(f"{command}: {behavior}")


def _make_renderer():
    status = {"spinner": None}

    def stop_spinner() -> None:
        spinner = status.get("spinner")
        if spinner is not None:
            spinner.stop()
            status["spinner"] = None

    def render_event(event_type: str, data: dict) -> None:
        if console:
            if event_type == "turn_start":
                stop_spinner()
                console.print(f"[bold]{data['text']}[/bold]")
                spinner = console.status("Waiting for model API...", spinner="dots")
                spinner.start()
                status["spinner"] = spinner
                return

            stop_spinner()
            text = data.get("text", "")
            if event_type == "model_text":
                content = data.get("content") or text
                if Markdown:
                    console.print(Panel(Markdown(content), title="model", border_style="blue"))
                else:
                    console.print(content, style="blue")
            elif event_type == "tool_call":
                console.print(text, style="magenta")
            elif event_type == "tool_result":
                console.print(text, style="green")
            elif event_type == "code_diff":
                console.print(f"[code diff] {data.get('path', '')}", style="bold cyan")
                if Syntax:
                    console.print(Syntax(data.get("diff", ""), "diff", theme="monokai", word_wrap=False))
                else:
                    console.print(data.get("diff", ""))
            elif event_type.startswith("verifier"):
                console.print(text, style="yellow")
            elif event_type in {"success"}:
                console.print(text, style="bold green")
            elif event_type in {"stalled", "stuck", "max_turns", "needs_verification", "llm_error"}:
                return
            else:
                console.print(text)
            return

        print(data.get("text", ""))

    render_event.stop_spinner = stop_spinner
    return render_event


def _new_transcript() -> Transcript:
    return Transcript("Interactive session started. Await the user's next task.")


def _scaffold_react_app(parent_root: str, name: str) -> tuple[bool, str]:
    if not name or name.startswith("-") or "/" in name or "\\" in name or name in {".", ".."}:
        return False, "Usage: /new-react <simple-folder-name>"

    sandbox = Sandbox(parent_root, command_timeout=300)
    try:
        sandbox.list_files(name)
        return False, f"{name} already exists. Choose another name or remove it first."
    except SandboxError:
        pass

    files = {
        f"{name}/package.json": """{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "react": "latest",
    "react-dom": "latest"
  },
  "devDependencies": {}
}
""",
        f"{name}/index.html": """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Cafe Landing Page</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
        f"{name}/src/main.jsx": """import React from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
""",
        f"{name}/src/App.jsx": """export default function App() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Neighborhood coffee house</p>
        <h1>Warm coffee, fresh plates, and a table near the window.</h1>
        <p className="hero-copy">
          A modern cafe landing page starter. Ask the agent to customize this
          copy, layout, menu, imagery, and styling for your brand.
        </p>
        <a className="button" href="mailto:hello@example.com">Plan a Visit</a>
      </section>
    </main>
  );
}
""",
        f"{name}/src/App.css": """* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #2a1c13;
  background: #f8efe4;
}

.page-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px;
}

.hero {
  width: min(960px, 100%);
  padding: clamp(40px, 8vw, 96px);
  border-radius: 36px;
  background: linear-gradient(135deg, #fff9f0, #e6c7a6);
  box-shadow: 0 24px 80px rgba(58, 35, 18, 0.18);
}

.eyebrow {
  margin: 0 0 16px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 0.78rem;
  font-weight: 800;
  color: #8b4c25;
}

h1 {
  max-width: 780px;
  margin: 0;
  font-size: clamp(2.8rem, 8vw, 6.8rem);
  line-height: 0.9;
  letter-spacing: -0.07em;
}

.hero-copy {
  max-width: 620px;
  margin: 28px 0;
  font-size: clamp(1rem, 2vw, 1.25rem);
  line-height: 1.7;
}

.button {
  display: inline-flex;
  padding: 14px 22px;
  border-radius: 999px;
  color: #fffaf3;
  background: #2a1c13;
  text-decoration: none;
  font-weight: 800;
}
""",
    }

    for path, content in files.items():
        sandbox.write_file(path, content)

    result = sandbox.run_command(f"cd {name} && npm install")
    if result["exit_code"] != 0:
        return False, f"Scaffolded {name}, but npm install failed:\n{result['stderr']}"
    return True, f"Created {name}, installed dependencies, and set verify command to npm run build."


def main() -> None:
    if not os.environ.get(API_KEY_ENV):
        _print(f"Warning: {API_KEY_ENV} is not set. OpenRouter requests will fail until it is configured.")

    project_dir = _default_project_dir()
    session = load_session(project_dir)
    sandbox_root = session["sandbox_root"]
    verify_command = session.get("verify_command")
    model = session.get("model") or DEFAULT_MODEL
    transcript = _new_transcript()

    _banner(sandbox_root, verify_command, model)
    _help()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not line:
            continue

        if line.startswith("/"):
            command, _, value = line.partition(" ")
            value = value.strip()

            if command in {"/exit", "/quit"}:
                return
            if command == "/help":
                _help()
                continue
            if command == "/clear":
                transcript = _new_transcript()
                _print("Transcript cleared.")
                continue
            if command == "/cwd":
                if not value:
                    _print("Usage: /cwd <path>")
                    continue
                try:
                    root = Path(value).expanduser().resolve(strict=True)
                    Sandbox(root)
                except (OSError, SandboxError) as exc:
                    _print(f"Could not use sandbox root: {exc}")
                    continue
                project_dir = root
                loaded = load_session(project_dir)
                sandbox_root = str(root)
                verify_command = loaded.get("verify_command")
                model = loaded.get("model") or model
                save_session(project_dir, sandbox_root=sandbox_root, verify_command=verify_command, model=model)
                transcript = _new_transcript()
                _banner(sandbox_root, verify_command, model)
                continue
            if command == "/verify":
                verify_command = value or None
                save_session(project_dir, sandbox_root=sandbox_root, verify_command=verify_command, model=model)
                _print(f"Verify command set to: {verify_command or 'not set'}")
                continue
            if command == "/model":
                if not value:
                    _print("Usage: /model <name>")
                    continue
                model = value
                save_session(project_dir, sandbox_root=sandbox_root, verify_command=verify_command, model=model)
                _print(f"Model set to: {model}")
                continue
            if command == "/new-react":
                ok, message = _scaffold_react_app(sandbox_root, value)
                _print(message)
                if ok:
                    root = (Path(sandbox_root) / value).resolve()
                    project_dir = root
                    sandbox_root = str(root)
                    verify_command = "npm run build"
                    save_session(project_dir, sandbox_root=sandbox_root, verify_command=verify_command, model=model)
                    transcript = _new_transcript()
                    nsandbox = Sandbox(sandbox_root)
                    try:
                        tree = nsandbox.list_files(".")
                        transcript.append_user(f"New Vite React project structure:\n{tree}")
                    except SandboxError:
                        pass
                    _banner(sandbox_root, verify_command, model)
                continue

            _print(f"Unknown command: {command}")
            continue

        renderer = _make_renderer()
        try:
            result = run(
                line,
                sandbox_root,
                verify_command,
                base_url=BASE_URL,
                model=model,
                transcript=transcript,
                on_event=renderer,
            )
        finally:
            if hasattr(renderer, "stop_spinner"):
                renderer.stop_spinner()

        if result.get("status") == "needs_verification":
            answer = input(
                "No verification command is set. What command should I run? "
                "(Enter to accept the agent's claim without automated verification) "
            ).strip()
            if answer.startswith("/verify "):
                answer = answer.partition(" ")[2].strip()
            if answer:
                verify_command = answer
                save_session(project_dir, sandbox_root=sandbox_root, verify_command=verify_command, model=model)
                renderer = _make_renderer()
                try:
                    result = run(
                        "Run the configured verification command and finish the previous task if it passes.",
                        sandbox_root,
                        verify_command,
                        base_url=BASE_URL,
                        model=model,
                        transcript=transcript,
                        on_event=renderer,
                    )
                finally:
                    if hasattr(renderer, "stop_spinner"):
                        renderer.stop_spinner()
            else:
                result = {
                    "status": "accepted_without_automated_verification",
                    "summary": result.get("summary", ""),
                }

        _print_result(result)


if __name__ == "__main__":
    main()
