from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

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
FAILCLOSED_PATH = ROOT / "artifacts/runtime-observation/2026-10-17-live-stability-failclosed.jsonl"


def _protocol() -> dict:
    return load_json(PROTOCOL_PATH)


def _metrics(protocol: dict) -> dict:
    return {
        name: {"status": "observed", "value": 1.0}
        for name in protocol["metric_names"]
    }


def _owner_result(
    protocol: dict,
    *,
    producer: str = "test-owner",
    trial_id: str = "direct_controller:warm:2",
) -> dict:
    arm, condition, repetition = trial_id.split(":")
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
        "protocol_id": protocol["protocol_id"],
        "protocol_digest": protocol["protocol_digest"],
        "trial_id": trial_id,
        "arm": arm,
        "condition": condition,
        "repetition": int(repetition),
        **{
            field: protocol["workload"][field]
            for field in protocol["workload"]["matching_fields"]
        },
    }


def test_direct_record_is_valid_topology_evidence() -> None:
    protocol = _protocol()
    row = record_direct(protocol, _owner_result(protocol), trial_id="direct_controller:warm:2")
    result = validate_rows(protocol, [row])
    assert result["invalid_rows"] == []
    assert row["status"] == "observed"


def test_explicit_modes_bind_to_their_owner_arm() -> None:
    protocol = _protocol()
    worker = record_worker_result(protocol, _owner_result(protocol, trial_id="single_worker:warm:1"), trial_id="single_worker:warm:1")
    cos = record_cos_result(protocol, _owner_result(protocol, trial_id="cos_two_lane:warm:1"), trial_id="cos_two_lane:warm:1")
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


def test_owner_result_must_match_protocol_trial_and_workload() -> None:
    protocol = _protocol()
    mismatches = {
        "protocol_id": "wrong-protocol",
        "protocol_digest": "wrong-digest",
        "trial_id": "direct_controller:cold:1",
        "arm": "single_worker",
        "condition": "cold",
        "repetition": 3,
        "workload_digest": "wrong-workload",
        "final_artifact_digest": "wrong-artifact",
        "acceptance_criteria_digest": "wrong-acceptance",
        "verification_commands_digest": "wrong-verification",
        "configuration_digest": "wrong-configuration",
    }
    for field, value in mismatches.items():
        result = _owner_result(protocol)
        result[field] = value
        with pytest.raises(ValueError, match=field):
            record_direct(protocol, result, trial_id="direct_controller:warm:2")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("metrics", {}),
        ("stage_timestamps", "not-timestamps"),
        ("useful_intervals_ms", ["not-an-interval"]),
    ],
)
def test_observed_owner_result_rejects_malformed_evidence(field: str, value: object) -> None:
    protocol = _protocol()
    result = _owner_result(protocol)
    result[field] = value
    with pytest.raises(ValueError, match="owner result evidence is invalid"):
        record_direct(protocol, result, trial_id="direct_controller:warm:2")


def test_cli_rejects_malformed_owner_result_without_writing(tmp_path: Path) -> None:
    protocol = _protocol()
    owner_path = tmp_path / "owner.json"
    result = _owner_result(protocol)
    result["metrics"] = {}
    owner_path.write_text(json.dumps(result), encoding="utf-8")
    output = tmp_path / "rows.jsonl"
    from scripts.run_live_stability_probe import main

    with pytest.raises(ValueError, match="missing metric"):
        main([
            "record-direct",
            "--protocol",
            str(PROTOCOL_PATH),
            "--result",
            str(owner_path),
            "--trial-id",
            "direct_controller:warm:2",
            "--output",
            str(output),
        ])
    assert not output.exists()


def test_failclosed_evidence_is_bound_to_expected_tests() -> None:
    expected = {
        "stale_plan_revision": (
            "plan_preparation",
            "plan_revision_changed",
            "tests/test_plan_preparation.py::test_prepare_plan_lanes_rejects_plan_revision_changed_after_admission",
        ),
        "wrong_base_head": (
            "base_identity_guard",
            "base_drift_blocked",
            "tests/test_live_stability_probe.py::test_owner_identity_and_acceptance_are_validated",
        ),
        "attempt_receipt_mismatch": (
            "receipt_validation",
            "receipt_rejected",
            "tests/test_secretary_live_pilot.py::test_validate_receipt_rejects_live_receipt_identity_mismatch",
        ),
        "timeout_silence": (
            "observation_boundary",
            "timeout_not_retirement",
            "tests/test_secretary_live_runtime.py::test_observe_submitted_codex_retries_terminal_state_after_read_timeout",
        ),
        "execution_failure_retired": (
            "worker_lifecycle",
            "execution_failed_retirement_confirmed",
            "tests/test_secretary_live_runtime.py::test_run_normal_exception_preserves_owned_resource_after_verified_cleanup",
        ),
        "cleanup_failure": (
            "cleanup_reconciliation",
            "recovery_required",
            "tests/test_secretary_live_runtime.py::test_run_normal_exception_quarantines_when_cleanup_is_unproven",
        ),
    }
    rows = [json.loads(line) for line in FAILCLOSED_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert {row["probe_id"] for row in rows} == set(expected)
    for row in rows:
        owner, state, verification = expected[row["probe_id"]]
        assert row["expected_owner"] == owner
        assert row["observed_state"] == state
        assert row["verification"] == verification
        test_path, _, test_name = verification.partition("::")
        source = (ROOT / test_path).read_text(encoding="utf-8")
        assert f"def {test_name}(" in source
        assert row["retry_count"] == 0
        assert row["reuse_allowed"] is False
        assert row["unauthorized_completion"] is False


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


def test_direct_script_invocation_supports_help() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_live_stability_probe.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "record-direct" in completed.stdout
