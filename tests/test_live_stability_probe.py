from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.benchmark_operational_comparison import load_json, validate_rows
from scripts.run_live_stability_probe import (
    record_blocked,
    record_cos_result,
    record_direct,
    record_worker_result,
    write_row,
)


ROOT = Path(__file__).parents[1]
PROTOCOL_PATH = ROOT / "artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json"


def _protocol() -> dict:
    return load_json(PROTOCOL_PATH)


def _metrics(protocol: dict) -> dict:
    return {
        name: {"status": "observed", "value": 1.0}
        for name in protocol["metric_names"]
    }


def _owner_result(protocol: dict, *, producer: str = "test-owner") -> dict:
    return {
        "attempted": True,
        "base_identity": protocol["base_revision"],
        "capability_state": "confirmed",
        "lifecycle": {
            "accepted_outcome": "accepted",
            "review": "not_required",
            "integration": "not_required",
            "retirement": "confirmed",
            "cleanup": "removed",
            "reconciliation": "confirmed",
        },
        "metrics": _metrics(protocol),
        "run_identity": "run-1",
        "source_producer": producer,
        "stage_timestamps": [{"stage": "admission", "started_at_ms": 0, "ended_at_ms": 1}],
        "useful_intervals_ms": [[0, 1]],
    }


def test_direct_record_is_valid_topology_evidence() -> None:
    protocol = _protocol()
    row = record_direct(protocol, _owner_result(protocol), trial_id="direct_controller:warm:2")
    result = validate_rows(protocol, [row])
    assert result["invalid_rows"] == []
    assert row["status"] == "observed"


def test_explicit_modes_bind_to_their_owner_arm() -> None:
    protocol = _protocol()
    worker = record_worker_result(protocol, _owner_result(protocol), trial_id="single_worker:warm:1")
    cos = record_cos_result(protocol, _owner_result(protocol), trial_id="cos_two_lane:warm:1")
    assert worker["arm"] == "single_worker"
    assert cos["arm"] == "cos_two_lane"
    with pytest.raises(ValueError, match="arm mismatch"):
        record_worker_result(protocol, _owner_result(protocol), trial_id="direct_controller:warm:2")


def test_owner_identity_and_acceptance_are_validated() -> None:
    protocol = _protocol()
    result = _owner_result(protocol)
    result["base_identity"] = "wrong-base"
    with pytest.raises(ValueError, match="base_identity"):
        record_direct(protocol, result, trial_id="direct_controller:warm:2")

    result = _owner_result(protocol)
    result["lifecycle"]["accepted_outcome"] = "completed"
    with pytest.raises(ValueError, match="semantic acceptance"):
        record_direct(protocol, result, trial_id="direct_controller:warm:2")


def test_sanitization_drops_sensitive_owner_fields(tmp_path: Path) -> None:
    protocol = _protocol()
    result = _owner_result(protocol)
    result["secret"] = "do-not-write"
    result["token"] = "do-not-write"
    row = record_direct(protocol, result, trial_id="direct_controller:warm:2")
    output = tmp_path / "rows.jsonl"
    write_row(output, row)
    serialized = output.read_text(encoding="utf-8")
    assert "do-not-write" not in serialized
    assert "secret" not in serialized


def test_blocked_record_is_valid_and_has_unavailable_metrics() -> None:
    protocol = _protocol()
    row = record_blocked(protocol, trial_id="direct_controller:warm:2", reason="provider unavailable")
    result = validate_rows(protocol, [row])
    assert result["invalid_rows"] == []
    assert row["status"] == "BLOCKED_CAPABILITY"
    assert all(metric["status"] == "blocked" for metric in row["metrics"].values())


def test_cli_record_mode_writes_one_row(tmp_path: Path) -> None:
    protocol = _protocol()
    owner_path = tmp_path / "owner.json"
    owner_path.write_text(json.dumps(_owner_result(protocol)), encoding="utf-8")
    output = tmp_path / "rows.jsonl"
    from scripts.run_live_stability_probe import main

    assert main([
        "record-direct",
        "--protocol",
        str(PROTOCOL_PATH),
        "--result",
        str(owner_path),
        "--trial-id",
        "direct_controller:warm:2",
        "--output",
        str(output),
    ]) == 0
    assert len(output.read_text(encoding="utf-8").splitlines()) == 1
