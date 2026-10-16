from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.benchmark_operational_comparison import (
    load_json,
    sha256_json,
    summarize,
    validate_rows,
)


ROOT = Path(__file__).parents[1]
PROTOCOL_PATH = ROOT / "artifacts/runtime-observation/2026-10-16-topology-economics-protocol.json"


def _protocol() -> dict:
    return load_json(PROTOCOL_PATH)


def _row(protocol: dict, trial_id: str, *, status: str = "observed", **overrides):
    arm, condition, repetition_text = trial_id.split(":")
    order_index = protocol["trial_design"]["order"].index(trial_id)
    row = {
        "schema": "topology-economics-row/v1",
        "protocol_id": protocol["protocol_id"],
        "protocol_digest": protocol["protocol_digest"],
        "trial_id": trial_id,
        "order_index": order_index,
        "arm": arm,
        "condition": condition,
        "repetition": int(repetition_text),
        "status": status,
        "source_producer": "test-producer",
        "source_digest": sha256_json({"trial_id": trial_id, "status": status}),
        "run_identity": f"run-{order_index}",
        "base_identity": protocol["base_revision"],
        "workload_digest": protocol["workload"]["workload_digest"],
        "final_artifact_digest": protocol["workload"]["final_artifact_digest"],
        "acceptance_criteria_digest": protocol["workload"]["acceptance_criteria_digest"],
        "verification_commands_digest": protocol["workload"]["verification_commands_digest"],
        "configuration_digest": protocol["workload"]["configuration_digest"],
        "attempted": True,
        "stage_timestamps": [
            {"stage": "admission", "started_at_ms": 0, "ended_at_ms": 1},
            {"stage": "execution", "started_at_ms": 1, "ended_at_ms": 101},
        ],
        "metrics": {
            name: {"status": "observed", "value": 1.0}
            for name in protocol["metric_names"]
        },
        "lifecycle": {
            "accepted_outcome": "accepted",
            "review": "not_required",
            "integration": "not_required",
            "retirement": "confirmed",
            "cleanup": "removed",
            "reconciliation": "confirmed",
        },
        "capability_state": "confirmed",
        "useful_intervals_ms": [[0, 100]],
    }
    row["metrics"]["accepted_outcome_wall_time_ms"] = {"status": "observed", "value": 100.0}
    row.update(overrides)
    return row


def test_protocol_is_self_consistent() -> None:
    protocol = _protocol()
    result = validate_rows(protocol, [])
    assert result["protocol_errors"] == []
    assert result["missing_trials"] == sorted(protocol["trial_design"]["order"])


def test_blocked_rows_preserve_unavailable_metrics_without_false_success() -> None:
    protocol = _protocol()
    rows = []
    for trial_id in protocol["trial_design"]["order"]:
        row = _row(protocol, trial_id, status="BLOCKED_CAPABILITY")
        row["attempted"] = False
        row["capability_state"] = "blocked"
        row["lifecycle"] = {
            "accepted_outcome": "not_observed",
            "review": "not_started",
            "integration": "not_started",
            "retirement": "not_started",
            "cleanup": "not_applicable",
            "reconciliation": "not_required",
        }
        row["stage_timestamps"] = [{"stage": "admission", "started_at_ms": None, "ended_at_ms": None}]
        row["metrics"] = {
            name: {"status": "blocked", "value": None, "reason": "capability unavailable"}
            for name in protocol["metric_names"]
        }
        rows.append(row)
    result = validate_rows(protocol, rows)
    assert result["valid"] is True
    summary = summarize(protocol, rows)
    assert summary["observed_row_count"] == 0
    assert summary["status_counts"]["BLOCKED_CAPABILITY"] == 18
    assert summary["arms"]["direct_controller"]["cold"]["wall_time_ms"]["status"] == "unavailable"


def test_mixed_base_and_duplicate_rows_are_rejected() -> None:
    protocol = _protocol()
    row = _row(protocol, protocol["trial_design"]["order"][0])
    duplicate = dict(row)
    duplicate["_line"] = 2
    row["base_identity"] = "wrong-base"
    result = validate_rows(protocol, [row, duplicate])
    assert result["valid"] is False
    assert any("base_identity" in error for item in result["invalid_rows"] for error in item["errors"])
    assert any("duplicate trial_id" in error for item in result["invalid_rows"] for error in item["errors"])


def test_overlapping_intervals_are_not_double_counted() -> None:
    protocol = _protocol()
    first = _row(protocol, "cos_two_lane:cold:2")
    first["useful_intervals_ms"] = [[0, 200], [100, 300]]
    second = _row(protocol, "cos_two_lane:cold:3")
    second["useful_intervals_ms"] = [[300, 350]]
    summary = summarize(protocol, [first, second])
    aggregate = summary["arms"]["cos_two_lane"]["cold"]
    assert aggregate["useful_interval_sum_ms"] == 450.0
    assert aggregate["useful_interval_union_ms"] == 350.0
    assert aggregate["wall_time_ms"]["observed_count"] == 2


def test_interval_union_is_calculated_per_trial_clock() -> None:
    protocol = _protocol()
    first = _row(protocol, "cos_two_lane:cold:2")
    first["useful_intervals_ms"] = [[0, 100]]
    second = _row(protocol, "cos_two_lane:cold:3")
    second["useful_intervals_ms"] = [[0, 100]]
    summary = summarize(protocol, [first, second])
    assert summary["arms"]["cos_two_lane"]["cold"]["useful_interval_union_ms"] == 200.0


def test_invalid_intervals_are_rejected() -> None:
    protocol = _protocol()
    row = _row(protocol, protocol["trial_design"]["order"][0])
    row["useful_intervals_ms"] = [[100, 0]]
    result = validate_rows(protocol, [row])
    assert result["valid"] is False
    assert any("ends before it starts" in error for item in result["invalid_rows"] for error in item["errors"])


def test_rejected_or_unsettled_rows_do_not_count_as_observed() -> None:
    protocol = _protocol()
    row = _row(protocol, protocol["trial_design"]["order"][0])
    row["lifecycle"].update({
        "accepted_outcome": "rejected",
        "review": "failed",
        "cleanup": "unresolved",
        "reconciliation": "pending",
    })
    row["capability_state"] = "blocked"
    result = validate_rows(protocol, [row])
    assert result["valid"] is False
    assert any("accepted lifecycle" in error for item in result["invalid_rows"] for error in item["errors"])
    assert summarize(protocol, [row])["observed_row_count"] == 0


def test_cli_validate_and_summarize(tmp_path: Path) -> None:
    protocol = _protocol()
    rows = [_row(protocol, trial_id, status="BLOCKED_CAPABILITY") for trial_id in protocol["trial_design"]["order"]]
    for row in rows:
        row["attempted"] = False
        row["capability_state"] = "blocked"
        row["stage_timestamps"] = [{"stage": "admission", "started_at_ms": None, "ended_at_ms": None}]
        row["lifecycle"] = {
            "accepted_outcome": "not_observed",
            "review": "not_started",
            "integration": "not_started",
            "retirement": "not_started",
            "cleanup": "not_applicable",
            "reconciliation": "not_required",
        }
        row["metrics"] = {
            name: {"status": "blocked", "value": None, "reason": "capability unavailable"}
            for name in protocol["metric_names"]
        }
    raw = tmp_path / "rows.jsonl"
    raw.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    summary_path = tmp_path / "summary.json"
    validate = subprocess.run(
        [sys.executable, "scripts/benchmark_operational_comparison.py", "validate", "--protocol", str(PROTOCOL_PATH), "--input", str(raw)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode == 0, validate.stderr
    assert json.loads(validate.stdout)["valid"] is True
    summarized = subprocess.run(
        [sys.executable, "scripts/benchmark_operational_comparison.py", "summarize", "--protocol", str(PROTOCOL_PATH), "--input", str(raw), "--output", str(summary_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert summarized.returncode == 0, summarized.stderr
    assert json.loads(summary_path.read_text(encoding="utf-8"))["observed_row_count"] == 0


def test_cli_fails_for_invalid_evidence(tmp_path: Path) -> None:
    protocol = _protocol()
    rows = [_row(protocol, trial_id) for trial_id in protocol["trial_design"]["order"]]
    rows[0]["base_identity"] = "wrong-base"
    raw = tmp_path / "invalid.jsonl"
    raw.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    summary_path = tmp_path / "summary.json"
    validate = subprocess.run(
        [sys.executable, "scripts/benchmark_operational_comparison.py", "validate", "--protocol", str(PROTOCOL_PATH), "--input", str(raw)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode == 1
    summarized = subprocess.run(
        [sys.executable, "scripts/benchmark_operational_comparison.py", "summarize", "--protocol", str(PROTOCOL_PATH), "--input", str(raw), "--output", str(summary_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert summarized.returncode == 1
