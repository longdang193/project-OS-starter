import json
from pathlib import Path
import subprocess
import sys

from scripts.benchmark_dispatch import benchmark_dispatch


def test_dispatch_benchmark_reports_supported_bounded_dispatch(tmp_path):
    manifest = tmp_path / "lanes.json"
    manifest.write_text('{"lane_count": 3, "workload_seconds": 0}', encoding="utf-8")

    result = benchmark_dispatch(manifest, repetitions=1, mode="baseline")

    assert result["completed_per_run"] == 2
    assert result["max_concurrency"] == 2


def test_dispatch_benchmark_script_runs_directly(tmp_path: Path) -> None:
    manifest = tmp_path / "lanes.json"
    manifest.write_text(json.dumps({"lane_count": 2, "workload_seconds": 0}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/benchmark_dispatch.py",
            "run",
            "--manifest",
            str(manifest),
            "--repetitions",
            "1",
            "--mode",
            "baseline",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["completed_per_run"] == 2
