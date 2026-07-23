import os
import shutil
from pathlib import Path

import pytest

from harness.config import DEFAULT_MODEL
from harness.orchestrator import run


@pytest.mark.skipif(os.environ.get("RUN_LIVE_SMOKE") != "1", reason="set RUN_LIVE_SMOKE=1 to run live model smoke test")
def test_live_model_can_fix_sample_project(tmp_path):
    source = Path(__file__).resolve().parents[1] / "sandbox_project"
    sandbox = tmp_path / "sandbox_project"
    shutil.copytree(source, sandbox)

    result = run(
        "Fix the bug in calc.py so the pytest suite passes.",
        str(sandbox),
        "python -m pytest -q",
        model=os.environ.get("LIVE_SMOKE_MODEL", DEFAULT_MODEL),
    )

    assert result["status"] == "success"
    assert result["verification"]["passed"] is True
    assert "return a * b" in (sandbox / "calc.py").read_text(encoding="utf-8")
