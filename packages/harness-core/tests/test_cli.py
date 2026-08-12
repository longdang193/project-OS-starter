from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from harness_core import managed


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


def test_module_identity_reports_policy_schema() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "harness_core.cli", "--identity"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["policy_schema_version"] == 11


def test_recover_stranded_cli_loads_explicit_evidence(monkeypatch, tmp_path: Path) -> None:
    evidence_path = tmp_path / "external-failure.json"
    evidence = {
        "version": 1,
        "source": "host",
        "code": "terminal_recording_failed",
        "run_id": "stranded-run",
        "attempt_id": "attempt-1",
        "detail": "terminal recording failed",
        "observed_at": "2026-08-08T19:54:03+00:00",
    }
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    captured: dict[str, object] = {}

    def recover(root: Path, run_id: str, attempt_id: str, reason: str, external_failure: dict[str, object]) -> dict[str, str]:
        captured.update({"root": root, "run_id": run_id, "attempt_id": attempt_id, "reason": reason, "external_failure": external_failure})
        return {"state": "awaiting_decision"}

    monkeypatch.setattr(managed, "recover_stranded_run", recover)

    assert managed.main([
        "--repo-root", str(tmp_path),
        "recover-stranded",
        "--run-id", "stranded-run",
        "--attempt-id", "attempt-1",
        "--reason", "host terminal recording failed",
        "--evidence", str(evidence_path),
    ]) == 0
    assert captured["root"] == tmp_path.resolve()
    assert captured["external_failure"] == evidence
