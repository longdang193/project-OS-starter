from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]


def test_module_validate_reports_consumer_policy() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "harness_core.cli", "validate", "--repo-root", str(ROOT)],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"errors": [], "status": "valid"}
