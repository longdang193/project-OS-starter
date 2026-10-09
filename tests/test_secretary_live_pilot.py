import subprocess
import sys
from pathlib import Path

from scripts.secretary_live_pilot import (
    account_interrupted,
    admit_pilot,
    compare_records,
    prepare_manifest,
)


def record(pair_id, arm, *, accepted=True, correct=True, cost=1.0):
    return {
        "pair_id": pair_id,
        "arm": arm,
        "attempt_id": f"{arm}-{pair_id}",
        "run_id": f"run-{arm}-{pair_id}",
        "workload_digest": "workload-1",
        "correctness": correct,
        "acceptance": "accepted" if accepted else "rejected",
        "cost": cost,
        "coordination_turns": 1,
        "human_interventions": 0,
    }


def test_prepare_manifest_freezes_workload_identity() -> None:
    manifest = prepare_manifest(
        task_id="task-1", plan_revision="plan-1", workload={"dependency": "cross-workstream"}
    )
    assert manifest["task_id"] == "task-1"
    assert len(manifest["workload_digest"]) == 64


def test_compare_records_uses_all_valid_pairs_and_failure_inclusive_totals() -> None:
    result = compare_records(
        [
            record("1", "baseline"),
            record("1", "candidate", cost=0.5),
            record("2", "baseline", accepted=False, correct=False, cost=10),
            record("2", "candidate", accepted=False, correct=False, cost=2),
        ],
        minimum_valid_pairs=1,
    )
    assert result["status"] == "NO_MEASURED_BENEFIT"
    assert result["eligible_pairs"] == 1
    assert result["arms"]["baseline"]["total_cost"] == 11.0
    assert result["arms"]["candidate"]["total_cost"] == 2.5
    assert result["arms"]["baseline"]["cost_per_accepted_outcome"] == 11.0


def test_compare_records_reports_unknown_cost_and_zero_acceptance() -> None:
    result = compare_records(
        [record("1", "baseline", accepted=False, correct=False, cost=None)],
        minimum_valid_pairs=1,
    )
    assert result["status"] == "INCONCLUSIVE"
    assert result["arms"]["baseline"]["total_cost"] == "unknown"
    assert result["arms"]["baseline"]["cost_per_accepted_outcome"] is None


def test_valid_pairs_with_unknown_cost_stay_inconclusive() -> None:
    result = compare_records(
        [
            record("1", "baseline", cost=None),
            record("1", "candidate", cost=None),
            record("2", "baseline", cost=None),
            record("2", "candidate", cost=None),
            record("3", "baseline", cost=None),
            record("3", "candidate", cost=None),
        ],
        minimum_valid_pairs=3,
    )
    assert result["status"] == "INCONCLUSIVE"
    assert all(item["candidate_minus_baseline_cost"] == "unknown" for item in result["paired_deltas"])


def test_blocked_smoke_admits_no_trial() -> None:
    smoke = {
        "schema": "project-os.secretary-live-receipt.v1",
        "status": "BLOCKED_CAPABILITY",
        "task_id": "task-1",
        "plan_revision": "plan-1",
        "attempt_id": "attempt-1",
        "run_id": "run-1",
        "provider": "9router",
        "model": "combo-high",
        "timestamps": {"entry_at": "2026-10-09T10:00:00Z", "exit_at": "2026-10-09T10:00:01Z"},
        "completion": {"observed": False, "operation": "secretary_smoke"},
        "provenance": {"source_type": "runtime", "producer": "secretary-live-runtime", "source_ref": "capability-check", "observed": True},
        "metrics": {"cos_turns": 0, "secretary_turns": 0, "human_interventions": 0, "token_usage": None, "cost": None},
        "outcomes": {"publication": "not_run", "settlement": "unresolved", "acceptance": "not_run"},
    }
    decision = admit_pilot(smoke)
    assert decision == {"admitted": False, "status": "BLOCKED_CAPABILITY", "trials_started": 0}


def test_interrupted_attempt_stays_accounted_without_duplicate_launch() -> None:
    result = account_interrupted(record("1", "candidate", accepted=False, correct=False, cost=3.0))
    assert result["outcome"] == "interrupted"
    assert result["attempt_id"] == "candidate-1"
    assert result["accounted"] is True
    assert result["duplicate_launch"] is False


def test_pilot_help_works_when_invoked_as_script() -> None:
    script = Path(__file__).parents[1] / "scripts" / "secretary_live_pilot.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
