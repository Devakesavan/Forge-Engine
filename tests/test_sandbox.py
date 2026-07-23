from pathlib import Path

import pytest

from harness.sandbox import Sandbox, SandboxError


def test_write_file_then_read_file_round_trips(tmp_path):
    sandbox = Sandbox(tmp_path)

    assert sandbox.write_file("hello.txt", "hello world") == "Wrote 11 characters to hello.txt"

    assert sandbox.read_file("hello.txt") == "hello world"


def test_write_file_creates_parent_directories(tmp_path):
    sandbox = Sandbox(tmp_path)

    sandbox.write_file("nested/path/file.txt", "content")

    assert (tmp_path / "nested" / "path" / "file.txt").read_text(encoding="utf-8") == "content"


def test_path_traversal_is_blocked_and_does_not_touch_outside_files(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    sandbox = Sandbox(root)

    with pytest.raises(SandboxError):
        sandbox.read_file("../outside.txt")
    assert outside.read_text(encoding="utf-8") == "secret"

    with pytest.raises(SandboxError):
        sandbox.write_file("../../etc/passwd", "x")
    assert not (tmp_path / "etc" / "passwd").exists()

    absolute = tmp_path / "absolute-outside.txt"
    with pytest.raises(SandboxError):
        sandbox.write_file(str(absolute), "x")
    assert not absolute.exists()


def test_run_command_executes_with_sandbox_root_as_cwd(tmp_path):
    sandbox = Sandbox(tmp_path)

    result = sandbox.run_command("pwd")

    assert result["exit_code"] == 0
    assert Path(result["stdout"].strip()).resolve() == tmp_path.resolve()


def test_run_command_timeout_returns_error_result_not_exception(tmp_path):
    sandbox = Sandbox(tmp_path, command_timeout=1)

    result = sandbox.run_command("sleep 5")

    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"]


def test_list_files_reflects_written_files(tmp_path):
    sandbox = Sandbox(tmp_path)
    sandbox.write_file("a.txt", "a")
    sandbox.write_file("dir/b.txt", "b")

    listing = sandbox.list_files(".").splitlines()

    assert "a.txt" in listing
    assert "dir/" in listing
