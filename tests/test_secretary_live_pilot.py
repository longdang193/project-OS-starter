from __future__ import annotations

from pathlib import Path

import pytest

from scripts.secretary_live_pilot import (
    PilotReceiptError,
    compare_records,
    prepare_manifest,
    validate_receipt,
)


def _manifest(tmp_path: Path) -> dict[str, object]:
    path = tmp_path / "manifest.json"
    return prepare_manifest(
        path,
        repository_identity="repo-1",
        plan_identity="plan-1",
        plan_revision="rev-1",
        task_id="Task 4",
        workload_digest="workload-1",
        workstream="cross-workstream-1",
        git_revision="34d6e8d",
    )


def _receipt(tmp_path: Path, pair_id: str, arm: str, *, interventions: int, completion: int) -> dict[str, object]:
    run_id = f"{pair_id}-{arm}"
    assignment_id = f"assignment-{pair_id}"
    attempt_id = f"attempt-{pair_id}-{arm}"
    timestamps = {
        "run_started": "2026-10-08T10:00:00+00:00",
        "first_useful_worker": "2026-10-08T10:00:10+00:00",
        "publication": "2026-10-08T10:00:40+00:00",
        "settlement": "2026-10-08T10:00:50+00:00",
        "acceptance": "2026-10-08T10:01:00+00:00",
        "run_finished": "2026-10-08T10:01:10+00:00",
    }
    metrics = {
        "human_interventions": interventions,
        "management_turns": interventions + 1,
        "accepted_completion_seconds": completion,
        "manual_relay_seconds": 0,
        "correctness_gate": True,
        "publication_success": True,
        "duplicate_execution": False,
        "unauthorized_writes": False,
        "token_usage": "unknown",
        "cost": "unknown",
    }
    common = {
        "pair_id": pair_id,
        "arm": arm,
        "run_id": run_id,
        "assignment_id": assignment_id,
        "attempt_id": attempt_id,
        "task_id": "Task 4",
        "plan_identity": "plan-1",
        "plan_revision": "rev-1",
        "repository_identity": "repo-1",
        "workstream": "cross-workstream-1",
        "git_revision": "34d6e8d",
        "worktree": f"worktree-{pair_id}-{arm}",
        "controller_id": f"controller-{pair_id}",
        "session_id": f"session-{pair_id}-{arm}",
        "checkpoint": "rev-1:Task 4:workload-1",
    }
    launch = {
        "producer": "herdr_main_launcher",
        **common,
        "provider": "9router",
        "model": "combo-high",
        "timestamps": timestamps,
        "metrics": metrics,
    }
    task_result = {"producer": "dcode-project", **common, "publication_valid": True}
    settlement = {"producer": "project_os_runtime.attempt", **common, "settled": True, "settlement_proven": True, "resource_settled": True}
    acceptance = {"producer": "cos", **common, "decision": "PASS"}
    refs = {}
    for name, value in {"launch": launch, "task_result": task_result, "settlement": settlement, "acceptance": acceptance}.items():
        path = tmp_path / f"{run_id}-{name}.json"
        path.write_text(__import__("json").dumps(value), encoding="utf-8")
        refs[name] = str(path)
    return {
        **common,
        "provider": "9router",
        "model": "combo-high",
        "timestamps": timestamps,
        "metrics": metrics,
        "source_refs": refs,
    }


def test_validate_receipt_requires_producer_owned_sources(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(tmp_path, "pair-1", "baseline", interventions=1, completion=100)

    normalized = validate_receipt(receipt, manifest)

    assert normalized["valid"] is True
    assert normalized["evidence_provenance"] == "live-attributed"
    assert len(normalized["source_digests"]) == 4


def test_validate_receipt_rejects_relabelled_historical_evidence(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(tmp_path, "pair-1", "baseline", interventions=1, completion=100)
    receipt["run_id"] = "new-run"

    with pytest.raises(PilotReceiptError, match="run_id mismatch"):
        validate_receipt(receipt, manifest)


def test_validate_receipt_rejects_cross_attempt_replay(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(tmp_path, "pair-1", "baseline", interventions=1, completion=100)
    receipt["attempt_id"] = "attempt-other"

    with pytest.raises(PilotReceiptError, match="attempt_id mismatch"):
        validate_receipt(receipt, manifest)


def test_validate_receipt_rejects_unbound_controller_and_metrics(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(tmp_path, "pair-1", "baseline", interventions=1, completion=100)
    receipt["controller_id"] = "spoofed-controller"
    receipt["metrics"]["human_interventions"] = 0

    with pytest.raises(PilotReceiptError, match="mismatch|metrics are not producer-bound"):
        validate_receipt(receipt, manifest)


def test_compare_records_revalidates_source_digests_and_flags(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    record = validate_receipt(_receipt(tmp_path, "pair-1", "baseline", interventions=1, completion=100), manifest)
    record["valid"] = False
    source_path = Path(record["source_refs"]["launch"])
    source_path.write_text(source_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(PilotReceiptError, match="source digest mismatch|metrics are not producer-bound"):
        compare_records([record], manifest)


def test_compare_records_rejects_duplicate_run_or_attempt(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    first = validate_receipt(_receipt(tmp_path, "pair-1", "baseline", interventions=1, completion=100), manifest)
    second = validate_receipt(_receipt(tmp_path, "pair-2", "candidate", interventions=0, completion=100), manifest)
    second["run_id"] = first["run_id"]

    with pytest.raises(PilotReceiptError, match="run_id mismatch|duplicate run_id"):
        compare_records([first, second], manifest)


def test_compare_records_requires_three_valid_pairs_for_benefit_claim(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    records = []
    for pair_number in range(1, 4):
        for arm, interventions, completion in (("baseline", 1, 100), ("candidate", 0, 105)):
            records.append(validate_receipt(_receipt(tmp_path, f"pair-{pair_number}", arm, interventions=interventions, completion=completion), manifest))

    result = compare_records(records, manifest)

    assert result["classification"] == "VERIFIED_BENEFIT"
    assert result["valid_pairs"] == 3
    assert result["intervention_reduction"] == 1


def test_compare_records_reports_no_measured_benefit_when_threshold_fails(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    records = []
    for pair_number in range(1, 4):
        for arm, interventions, completion in (("baseline", 1, 100), ("candidate", 1, 120)):
            records.append(validate_receipt(_receipt(tmp_path, f"pair-{pair_number}", arm, interventions=interventions, completion=completion), manifest))

    assert compare_records(records, manifest)["classification"] == "NO_MEASURED_BENEFIT"


def test_compare_records_is_inconclusive_below_minimum_pairs(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    records = [
        validate_receipt(_receipt(tmp_path, "pair-1", arm, interventions=1 if arm == "baseline" else 0, completion=100), manifest)
        for arm in ("baseline", "candidate")
    ]

    result = compare_records(records, manifest)

    assert result["classification"] == "INCONCLUSIVE"
    assert result["valid_pairs"] == 1


def test_compare_records_stops_on_blocked_capability(tmp_path: Path) -> None:
    assert compare_records([], _manifest(tmp_path), capability_status="BLOCKED_CAPABILITY")["classification"] == "BLOCKED_CAPABILITY"
