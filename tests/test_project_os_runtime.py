from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from scripts.project_os_runtime import PreparedLane, prepare_lane


def _descriptor() -> dict[str, object]:
    return {
        "lane_id": "lane-1",
        "repository_identity": "repo",
        "plan_identity": "plan",
        "task": "run tests",
        "executor": "deepagents",
        "profile": "normal",
        "worktree": "C:/repo",
        "expected_base": "a" * 40,
        "session": "default",
        "pane": "w1:p1",
        "allowed_write_set": ["scripts"],
        "dependencies": [],
        "dependency_ready": True,
        "fixed_contracts": [],
        "mutable_resources": [],
        "grant_turns": "native",
        "grant_wall_clock_seconds": "native",
        "grant_child_agents": "deny",
        "mcp_select": [],
        "remaining_authorized_task_allowance": 900,
    }


def test_prepare_lane_normalizes_identity_grant_and_capabilities() -> None:
    lane = prepare_lane(_descriptor())

    assert isinstance(lane, PreparedLane)
    assert lane.assignment_id
    assert lane.task_sha256 == lane.task_hash
    assert lane.grant["turns"]["effective"] == "native"
    assert lane.capabilities["effective"] == ("git", "py")


def test_prepare_lane_is_frozen() -> None:
    lane = prepare_lane(_descriptor())

    with pytest.raises(FrozenInstanceError):
        lane.lane_id = "other"  # type: ignore[misc]


def test_admission_result_is_immutable_and_states_are_disjoint() -> None:
    from scripts.project_os_runtime.admission import (
        ADMISSION_STATES,
        AdmissionResult,
        validate_admission_results,
    )

    result = AdmissionResult("lane-a", "ADMITTED", "ready")

    assert ADMISSION_STATES == {"ADMITTED", "DEFERRED", "BLOCKED", "REJECTED"}
    assert validate_admission_results([result]) == (result,)
    with pytest.raises(FrozenInstanceError):
        result.state = "BLOCKED"  # type: ignore[misc]
    with pytest.raises(ValueError, match="one state"):
        validate_admission_results([result, AdmissionResult("lane-a", "BLOCKED", "conflict")])


def test_settlement_decision_reads_lifecycle_receipt_without_capability_or_acceptance() -> None:
    from scripts.project_os_runtime.attempt import settlement_decision

    receipt = {
        "worker": {"state": "exited", "exit_code": 1, "descendant_state": "terminated"},
        "cleanup": {"state": "removed"},
        "recovery_required": False,
        "capability_state": "unavailable",
    }

    decision = settlement_decision(receipt)

    assert decision["resource_settled"] is True
    assert decision["settlement_proven"] is True
    assert decision["reason"] == "settled"


def test_settlement_decision_rejects_missing_normalized_recovery_evidence() -> None:
    from scripts.project_os_runtime.attempt import settlement_decision

    decision = settlement_decision({
        "state": "confirmed",
        "worker_state": "exited",
        "descendant_state": "terminated",
        "cleanup_state": "removed",
    })

    assert decision["resource_settled"] is False
    assert decision["reason"] == "settlement evidence incomplete"


def test_settlement_decision_keeps_cleanup_uncertainty_occupied() -> None:
    from scripts.project_os_runtime.attempt import settlement_decision

    decision = settlement_decision({
        "worker": {"state": "exited", "descendant_state": "terminated"},
        "cleanup": {"state": "unverified"},
        "recovery_required": False,
    })

    assert decision["resource_settled"] is False
    assert decision["reason"] == "cleanup unsettled"


def test_settlement_decision_accepts_flat_lifecycle_receipt() -> None:
    from scripts.project_os_runtime.attempt import settlement_decision

    decision = settlement_decision({
        "state": "confirmed",
        "worker_state": "exited",
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "recovery_required": False,
    })

    assert decision["resource_settled"] is True


def test_settlement_decision_does_not_read_presentation_execution() -> None:
    from scripts.project_os_runtime.attempt import settlement_decision

    decision = settlement_decision({
        "execution": {"state": "completed", "descendant_state": "terminated"},
        "cleanup": {"state": "removed"},
    })

    assert decision["resource_settled"] is False
