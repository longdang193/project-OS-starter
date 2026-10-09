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


def test_classify_admission_owns_exclusive_state_and_supplied_capacity() -> None:
    from scripts.project_os_runtime.admission import AdmissionResult, classify_admission

    assert classify_admission(
        "lane-a", capacity_available=False, capacity_reason="capacity limit 2"
    ) == AdmissionResult("lane-a", "DEFERRED", "capacity limit 2")
    assert classify_admission(
        "lane-a", conflict_reason="write conflict"
    ) == AdmissionResult("lane-a", "BLOCKED", "write conflict")
    assert classify_admission("lane-a", duplicate_id=True, capacity_available=False).state == "REJECTED"


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


def _acceptance_inputs() -> dict[str, dict[str, object]]:
    return {
        "controller": {
            "identity": "codex-lead-1",
            "authority": "cos",
            "plan_identity": "plan-1",
            "task_id": "Task 1",
        },
        "task": {
            "task_id": "Task 1",
            "plan_identity": "plan-1",
            "required_proof": "artifact proof",
            "required_conditions": {"required artifact exists": "artifact proof"},
            "evidence": "docs/evidence.md",
            "state": "active",
        },
        "evidence": {
            "publication_valid": True,
            "task_completed": True,
            "task_identity_matches": True,
        },
        "artifact_conditions": {"required artifact exists": True},
        "git": {
            "repository_identity": "project-OS-starter",
            "plan_identity": "plan-1",
            "head_matches": True,
            "write_scope_matches": True,
        },
        "verification": {"passed": True},
        "settlement": {"settlement_proven": True, "resource_settled": True},
    }


def test_cos_acceptance_rejects_false_artifact_and_keeps_dependent_pending() -> None:
    from scripts.project_os_runtime.acceptance import (
        authorize_dependent_transition,
        evaluate_acceptance,
    )

    inputs = _acceptance_inputs()
    inputs["artifact_conditions"] = {"required artifact exists": False}

    decision = evaluate_acceptance(**inputs)
    transition = authorize_dependent_transition(
        decision,
        completed_task_id="Task 1",
        dependent_task={"task_id": "Task 2", "plan_identity": "plan-1", "state": "pending", "dependencies": ["Task 1"]},
        dependency_states={"Task 1": "active"},
    )

    assert decision["decision"] == "FAIL"
    assert transition["authorized"] is False
    assert transition["next_state"] == "pending"


def test_cos_acceptance_passes_and_authorizes_only_ready_dependent() -> None:
    from scripts.project_os_runtime.acceptance import (
        authorize_dependent_transition,
        evaluate_acceptance,
    )

    inputs = _acceptance_inputs()
    decision = evaluate_acceptance(**inputs)
    transition = authorize_dependent_transition(
        decision,
        completed_task_id="Task 1",
        dependent_task={"task_id": "Task 2", "plan_identity": "plan-1", "state": "pending", "dependencies": ["Task 1"]},
        dependency_states={"Task 1": "completed"},
    )

    assert decision["decision"] == "PASS"
    assert decision["task_transition"]["next_state"] == "completed"
    assert transition["authorized"] is True
    assert transition["next_state"] == "active"


def test_cos_acceptance_blocks_git_evidence_from_another_plan() -> None:
    from scripts.project_os_runtime.acceptance import evaluate_acceptance

    inputs = _acceptance_inputs()
    inputs["git"]["plan_identity"] = "unrelated-plan"

    decision = evaluate_acceptance(**inputs)

    assert decision["decision"] == "BLOCKED"
    assert "Git and task plan binding mismatch" in decision["reasons"]


def test_cos_acceptance_rejects_transition_for_unrelated_completed_task() -> None:
    from scripts.project_os_runtime.acceptance import (
        authorize_dependent_transition,
        evaluate_acceptance,
    )

    decision = evaluate_acceptance(**_acceptance_inputs())
    transition = authorize_dependent_transition(
        decision,
        completed_task_id="Task 99",
        dependent_task={"task_id": "Task 2", "plan_identity": "plan-1", "state": "pending", "dependencies": ["Task 99"]},
        dependency_states={"Task 99": "completed"},
    )

    assert transition["authorized"] is False
    assert transition["next_state"] == "pending"
    assert transition["reason"] == "accepted task does not match completed task"


def test_cos_acceptance_rejects_cross_plan_dependent_transition() -> None:
    from scripts.project_os_runtime.acceptance import (
        authorize_dependent_transition,
        evaluate_acceptance,
    )

    decision = evaluate_acceptance(**_acceptance_inputs())
    transition = authorize_dependent_transition(
        decision,
        completed_task_id="Task 1",
        dependent_task={"task_id": "Task 2", "plan_identity": "plan-2", "state": "pending", "dependencies": ["Task 1"]},
        dependency_states={"Task 1": "completed"},
    )

    assert transition["authorized"] is False
    assert transition["next_state"] == "pending"
    assert transition["reason"] == "accepted and dependent task plan binding mismatch"


def test_cos_acceptance_blocks_missing_controller_binding() -> None:
    from scripts.project_os_runtime.acceptance import evaluate_acceptance

    inputs = _acceptance_inputs()
    inputs["controller"] = {"identity": "", "authority": "cos"}

    decision = evaluate_acceptance(**inputs)

    assert decision["decision"] == "BLOCKED"
    assert "controller identity" in decision["reasons"]
    assert decision["task_transition"]["next_state"] == "active"


def test_cos_acceptance_blocks_unsettled_resources() -> None:
    from scripts.project_os_runtime.acceptance import evaluate_acceptance

    inputs = _acceptance_inputs()
    inputs["settlement"] = {"settlement_proven": True, "resource_settled": False}

    decision = evaluate_acceptance(**inputs)

    assert decision["decision"] == "BLOCKED"
    assert "resource settlement" in decision["reasons"]


@pytest.mark.parametrize("state", [None, "pending", "blocked", "completed"])
def test_cos_acceptance_requires_active_task_state(state: str | None) -> None:
    from scripts.project_os_runtime.acceptance import evaluate_acceptance

    inputs = _acceptance_inputs()
    if state is None:
        inputs["task"].pop("state")
    else:
        inputs["task"]["state"] = state

    decision = evaluate_acceptance(**inputs)

    assert decision["decision"] == "BLOCKED"
    assert "task state eligibility" in decision["reasons"]


def test_cos_acceptance_blocks_caller_supplied_subset_of_plan_conditions() -> None:
    from scripts.project_os_runtime.acceptance import evaluate_acceptance

    inputs = _acceptance_inputs()
    inputs["task"]["required_conditions"] = {
        "required artifact exists": "artifact proof",
        "verification recorded": "verification proof",
    }

    decision = evaluate_acceptance(**inputs)

    assert decision["decision"] == "BLOCKED"
    assert "artifact condition coverage" in decision["reasons"]


def test_cos_acceptance_blocks_missing_canonical_condition_set() -> None:
    from scripts.project_os_runtime.acceptance import evaluate_acceptance

    inputs = _acceptance_inputs()
    inputs["task"].pop("required_conditions")

    decision = evaluate_acceptance(**inputs)

    assert decision["decision"] == "BLOCKED"
    assert "required condition set" in decision["reasons"]


def test_cos_acceptance_blocks_non_mapping_artifact_conditions() -> None:
    from scripts.project_os_runtime.acceptance import evaluate_acceptance

    inputs = _acceptance_inputs()
    inputs["artifact_conditions"] = []  # type: ignore[assignment]

    decision = evaluate_acceptance(**inputs)

    assert decision["decision"] == "BLOCKED"
    assert "artifact condition type" in decision["reasons"]


def test_cos_acceptance_rejects_minimal_pass_decision() -> None:
    from scripts.project_os_runtime.acceptance import authorize_dependent_transition

    transition = authorize_dependent_transition(
        {"decision": "PASS"},
        completed_task_id="Task 1",
        dependent_task={
            "task_id": "Task 2",
            "plan_identity": "plan-1",
            "state": "pending",
            "dependencies": ["Task 1"],
        },
        dependency_states={"Task 1": "completed"},
    )

    assert transition["authorized"] is False
    assert transition["next_state"] == "pending"
    assert transition["reason"] == "acceptance decision incomplete"


def test_cos_acceptance_rejects_inconsistent_transition_proof() -> None:
    from scripts.project_os_runtime.acceptance import (
        authorize_dependent_transition,
        evaluate_acceptance,
    )

    decision = evaluate_acceptance(**_acceptance_inputs())
    decision["task_transition"]["next_state"] = "active"

    transition = authorize_dependent_transition(
        decision,
        completed_task_id="Task 1",
        dependent_task={
            "task_id": "Task 2",
            "plan_identity": "plan-1",
            "state": "pending",
            "dependencies": ["Task 1"],
        },
        dependency_states={"Task 1": "completed"},
    )

    assert transition["authorized"] is False
    assert transition["next_state"] == "pending"
    assert transition["reason"] == "acceptance decision incomplete"


def test_cos_acceptance_rejects_repeated_source_completion() -> None:
    from scripts.project_os_runtime.acceptance import (
        authorize_dependent_transition,
        evaluate_acceptance,
    )

    inputs = _acceptance_inputs()
    inputs["task"]["state"] = "completed"
    decision = evaluate_acceptance(**inputs)

    transition = authorize_dependent_transition(
        decision,
        completed_task_id="Task 1",
        dependent_task={
            "task_id": "Task 2",
            "plan_identity": "plan-1",
            "state": "pending",
            "dependencies": ["Task 1"],
        },
        dependency_states={"Task 1": "completed"},
    )

    assert decision["decision"] == "BLOCKED"
    assert transition["authorized"] is False
    assert transition["next_state"] == "pending"
