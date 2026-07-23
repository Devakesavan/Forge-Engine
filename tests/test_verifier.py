from harness.sandbox import Sandbox
from harness.verifier import verify


def test_verify_passes_for_zero_exit_command(tmp_path):
    result = verify(Sandbox(tmp_path), "sh -c 'printf ok'")

    assert result["passed"] is True
    assert result["exit_code"] == 0
    assert result["stdout"] == "ok"


def test_verify_fails_for_non_zero_exit_command(tmp_path):
    result = verify(Sandbox(tmp_path), "sh -c 'printf bad >&2; exit 7'")

    assert result["passed"] is False
    assert result["exit_code"] == 7
    assert result["stderr"] == "bad"
