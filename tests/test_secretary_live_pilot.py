from __future__ import annotations

from pathlib import Path
import hashlib
import subprocess
import sys

import pytest

from scripts.secretary_live_pilot import (
    PilotReceiptError,
    compare_records,
    prepare_manifest,
    validate_receipt,
)
from scripts.project_os_runtime.secretary_receipts import build_live_receipt


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


def _receipt(
    tmp_path: Path,
    pair_id: str,
    arm: str,
    *,
    interventions: int,
    completion: int,
    model: str = "combo-high",
    token_usage: object = "unknown",
    cost: object = "unknown",
) -> dict[str, object]:
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
        "token_usage": token_usage,
        "cost": cost,
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
        "model": model,
        "timestamps": timestamps,
        "metrics": metrics,
    }
    task_result = {"producer": "dcode-project", **common, "publication_valid": True}
    settlement = {"producer": "project_os_runtime.attempt", **common, "settled": True, "settlement_proven": True, "resource_settled": True}
    acceptance = {"producer": "cos", **common, "decision": "PASS"}
    refs = {}
    for name, value in {"launch": launch, "task_result": task_result, "settlement": settlement, "acceptance": acceptance}.items():
        path = tmp_path / f"{run_id}-{name}.json"
        value["source_ref"] = str(path)
        value["source_digest"] = hashlib.sha256(
            __import__("json").dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        path.write_text(__import__("json").dumps(value), encoding="utf-8")
        refs[name] = str(path)
    return {
        **common,
        "provider": "9router",
        "model": model,
        "timestamps": timestamps,
        "metrics": metrics,
        "source_refs": refs,
    }


def _live_source_proof(receipt: dict[str, object], name: str) -> tuple[str, str]:
    refs = receipt["source_refs"]
    if isinstance(refs, dict) and name in refs:
        path = Path(refs[name])
        return str(path), hashlib.sha256(path.read_bytes()).hexdigest()
    source_ref = f"runtime://{name}/{receipt['run_id']}"
    return source_ref, hashlib.sha256(source_ref.encode()).hexdigest()


def test_validate_receipt_requires_producer_owned_sources(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(tmp_path, "pair-1", "baseline", interventions=1, completion=100)

    normalized = validate_receipt(receipt, manifest)

    assert normalized["valid"] is True
    assert normalized["evidence_provenance"] == "live-attributed"
    assert len(normalized["source_digests"]) == 4


def test_validate_receipt_accepts_structured_economics(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(
        tmp_path,
        "pair-1",
        "candidate",
        interventions=0,
        completion=100,
        model="glm/glm-4.7",
        token_usage={
            "input_tokens": 883,
            "output_tokens": 6,
            "total_tokens": 889,
            "source": "response.usage",
            "confidence": "observed",
        },
        cost={
            "value": 0.000543,
            "kind": "estimated",
            "currency": "USD",
            "pricing_source": "published-rate-card",
            "pricing_effective_date": "2026-10-09",
            "model": "glm/glm-4.7",
            "model_resolution": "exact",
        },
    )

    normalized = validate_receipt(receipt, manifest)

    assert normalized["metrics"]["token_usage"]["total_tokens"] == 889
    assert normalized["metrics"]["cost"]["kind"] == "estimated"


def test_validate_receipt_rejects_outer_settlement_and_acceptance_without_live_receipt(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(tmp_path, "pair-1", "baseline", interventions=1, completion=100)
    launch_path = Path(receipt["source_refs"]["launch"])
    launch = __import__("json").loads(launch_path.read_text(encoding="utf-8"))
    for field, value in (("settlement_proven", False), ("acceptance_decision", "FAIL")):
        receipt["metrics"][field] = value
        launch["metrics"] = dict(receipt["metrics"])
        launch_without_digest = {key: item for key, item in launch.items() if key != "source_digest"}
        launch["source_digest"] = hashlib.sha256(
            __import__("json").dumps(launch_without_digest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        launch_path.write_text(__import__("json").dumps(launch), encoding="utf-8")
        with pytest.raises(PilotReceiptError, match=rf"receipt metrics\.{field} mismatch"):
            validate_receipt(receipt, manifest)
        del receipt["metrics"][field]
        launch["metrics"] = dict(receipt["metrics"])
        launch_without_digest = {key: item for key, item in launch.items() if key != "source_digest"}
        launch["source_digest"] = hashlib.sha256(
            __import__("json").dumps(launch_without_digest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        launch_path.write_text(__import__("json").dumps(launch), encoding="utf-8")


def test_validate_receipt_accepts_bound_live_secretary_receipt(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(tmp_path, "pair-1", "candidate", interventions=0, completion=100)
    common = {field: receipt[field] for field in (
        "pair_id", "arm", "run_id", "attempt_id", "task_id", "plan_revision",
        "repository_identity", "plan_identity", "git_revision", "worktree",
        "workstream", "checkpoint",
    )}
    receipt["live_receipt"] = build_live_receipt(
        binding=common,
        runtime={"provider": "9router", "model": "combo-high", "controller_id": receipt["controller_id"], "session_id": receipt["session_id"]},
        timestamps={
            "run_started": "2026-10-08T10:00:00+00:00",
            "cos_entry": "2026-10-08T10:00:01+00:00",
            "secretary_entry": "2026-10-08T10:00:02+00:00",
            "worker_entry": "2026-10-08T10:00:03+00:00",
            "publication": "2026-10-08T10:00:40+00:00",
            "settlement": "2026-10-08T10:00:50+00:00",
            "acceptance": "2026-10-08T10:01:00+00:00",
            "secretary_exit": "2026-10-08T10:01:05+00:00",
            "cos_exit": "2026-10-08T10:01:08+00:00",
            "run_finished": "2026-10-08T10:01:10+00:00",
        },
        metrics={
            "cos_turns": 0,
            "secretary_turns": 1,
            "human_interventions": 0,
            "publication_success": True,
            "settlement_proven": True,
            "acceptance_decision": "PASS",
            "token_usage": "unknown",
            "cost": "unknown",
        },
        sources={
            name: {
                "producer": producer,
                    "source_ref": _live_source_proof(receipt, name)[0],
                    "source_digest": _live_source_proof(receipt, name)[1],
                **common,
                "provider": "9router",
                "model": "combo-high",
                "controller_id": receipt["controller_id"],
                "session_id": receipt["session_id"],
            }
            for name, producer in {
                "launch": "herdr_main_launcher",
                "secretary": "secretary_live_runtime",
                "task_result": "dcode-project",
                "settlement": "project_os_runtime.attempt",
                "acceptance": "cos",
            }.items()
        },
    )

    normalized = validate_receipt(receipt, manifest)

    assert normalized["live_receipt"]["valid"] is True
    launch_path = Path(receipt["source_refs"]["launch"])
    for field, value in (("settlement_proven", False), ("acceptance_decision", "FAIL")):
        receipt["metrics"][field] = value
        launch = __import__("json").loads(launch_path.read_text(encoding="utf-8"))
        launch["metrics"] = dict(receipt["metrics"])
        launch_without_digest = {key: item for key, item in launch.items() if key != "source_digest"}
        launch["source_digest"] = hashlib.sha256(
            __import__("json").dumps(launch_without_digest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        launch_path.write_text(__import__("json").dumps(launch), encoding="utf-8")
        with pytest.raises(PilotReceiptError, match="metrics.*mismatch"):
            validate_receipt(receipt, manifest)
        del receipt["metrics"][field]
        launch["metrics"] = dict(receipt["metrics"])
        launch_without_digest = {key: item for key, item in launch.items() if key != "source_digest"}
        launch["source_digest"] = hashlib.sha256(
            __import__("json").dumps(launch_without_digest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        launch_path.write_text(__import__("json").dumps(launch), encoding="utf-8")
    receipt["live_receipt"]["metrics"]["publication_success"] = False

    with pytest.raises(PilotReceiptError, match="live receipt metrics.publication_success"):
        validate_receipt(receipt, manifest)


@pytest.mark.parametrize("field", ["model", "controller_id", "session_id", "workstream", "checkpoint"])
def test_validate_receipt_rejects_live_receipt_identity_mismatch(tmp_path: Path, field: str) -> None:
    manifest = _manifest(tmp_path)
    receipt = _receipt(tmp_path, "pair-1", "candidate", interventions=0, completion=100)
    common = {name: receipt[name] for name in (
        "pair_id", "arm", "run_id", "attempt_id", "task_id", "plan_revision",
        "repository_identity", "plan_identity", "git_revision", "worktree",
        "workstream", "checkpoint",
    )}
    receipt["live_receipt"] = build_live_receipt(
        binding=common,
        runtime={
            "provider": "9router",
            "model": receipt["model"],
            "controller_id": receipt["controller_id"],
            "session_id": receipt["session_id"],
        },
        timestamps={
            "run_started": "2026-10-08T10:00:00+00:00",
            "cos_entry": "2026-10-08T10:00:01+00:00",
            "secretary_entry": "2026-10-08T10:00:02+00:00",
            "worker_entry": "2026-10-08T10:00:03+00:00",
            "publication": "2026-10-08T10:00:40+00:00",
            "settlement": "2026-10-08T10:00:50+00:00",
            "acceptance": "2026-10-08T10:01:00+00:00",
            "secretary_exit": "2026-10-08T10:01:05+00:00",
            "cos_exit": "2026-10-08T10:01:08+00:00",
            "run_finished": "2026-10-08T10:01:10+00:00",
        },
        metrics={
            "cos_turns": 0,
            "secretary_turns": 1,
            "human_interventions": 0,
            "publication_success": True,
            "settlement_proven": True,
            "acceptance_decision": "PASS",
            "token_usage": "unknown",
            "cost": "unknown",
        },
        sources={
            name: {
                "producer": producer,
                    "source_ref": _live_source_proof(receipt, name)[0],
                    "source_digest": _live_source_proof(receipt, name)[1],
                **common,
                "provider": "9router",
                "model": receipt["model"],
                "controller_id": receipt["controller_id"],
                "session_id": receipt["session_id"],
            }
            for name, producer in {
                "launch": "herdr_main_launcher",
                "secretary": "secretary_live_runtime",
                "task_result": "dcode-project",
                "settlement": "project_os_runtime.attempt",
                "acceptance": "cos",
            }.items()
        },
    )
    receipt["live_receipt"][field] = "mismatch"

    with pytest.raises(PilotReceiptError, match=f"{field} mismatch"):
        validate_receipt(receipt, manifest)


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
    assert result["token_usage_comparison"] == {"status": "unknown", "pairs": 0}
    assert result["estimated_cost_comparison"] == {"status": "unknown", "pairs": 0}


def test_compare_records_measures_tokens_and_estimated_cost(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    records = []
    for pair_number in range(1, 4):
        for arm, interventions, completion, input_tokens, output_tokens, cost in (
            ("baseline", 1, 100, 100, 10, 0.000082),
            ("candidate", 0, 105, 80, 8, 0.000066),
        ):
            cache_read_tokens = 20 if arm == "baseline" else 10
            records.append(
                validate_receipt(
                    _receipt(
                        tmp_path,
                        f"pair-{pair_number}",
                        arm,
                        interventions=interventions,
                        completion=completion,
                        model="glm/glm-4.7",
                        token_usage={
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": input_tokens + output_tokens,
                            "cache_read_input_tokens": cache_read_tokens,
                            "source": "response.usage",
                            "confidence": "observed",
                        },
                        cost={
                            "value": cost,
                            "kind": "estimated",
                            "currency": "USD",
                            "pricing_source": "published-rate-card",
                            "pricing_effective_date": "2026-10-09",
                            "model": "glm/glm-4.7",
                            "model_resolution": "exact",
                        },
                    ),
                    manifest,
                )
            )

    result = compare_records(records, manifest)

    assert result["token_usage_comparison"] == {
        "status": "measured",
        "pairs": 3,
        "baseline_median": {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110, "cache_read_input_tokens": 20, "cache_write_input_tokens": 0},
        "candidate_median": {"input_tokens": 80, "output_tokens": 8, "total_tokens": 88, "cache_read_input_tokens": 10, "cache_write_input_tokens": 0},
        "delta": {"input_tokens": -20, "output_tokens": -2, "total_tokens": -22, "cache_read_input_tokens": -10, "cache_write_input_tokens": 0},
    }
    assert result["estimated_cost_comparison"] == {
        "status": "estimated",
        "pairs": 3,
        "currency": "USD",
        "baseline_median": 0.000082,
        "candidate_median": 0.000066,
        "delta": -0.000016,
    }


def test_compare_records_rejects_mixed_cost_currencies(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    records = []
    for pair_number, currency in ((1, "USD"), (2, "EUR"), (3, "USD")):
        for arm, interventions, completion in (("baseline", 1, 100), ("candidate", 0, 105)):
            records.append(
                validate_receipt(
                    _receipt(
                        tmp_path,
                        f"pair-{pair_number}",
                        arm,
                        interventions=interventions,
                        completion=completion,
                        model="glm/glm-4.7",
                        cost={
                            "value": 0.0001,
                            "kind": "estimated",
                            "currency": currency,
                            "pricing_source": "published-rate-card",
                            "pricing_effective_date": "2026-10-09",
                            "model": "glm/glm-4.7",
                            "model_resolution": "exact",
                        },
                    ),
                    manifest,
                )
            )

    result = compare_records(records, manifest)

    assert result["estimated_cost_comparison"] == {
        "status": "unknown",
        "pairs": 3,
        "reason": "mixed_currency",
    }


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


def test_pilot_script_supports_direct_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-B", "scripts/secretary_live_pilot.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "prepare" in result.stdout
