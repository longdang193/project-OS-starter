from __future__ import annotations

from scripts.project_os_runtime.secretary_evidence import CURRENT, MISSING, STALE, build_evidence_snapshot


def _facts() -> dict[str, dict[str, object]]:
    return {
        "plan": {
            "source_ref": "plan.md",
            "repository_identity": "repo-1",
            "workstream": "integration",
            "plan_identity": "plan-1",
            "plan_revision": "rev-1",
            "git_revision": "abc123",
            "task_id": "Task 4",
            "task_state": "active",
            "attempt_id": "attempt-1",
            "checkpoint": "checkpoint-1",
            "checkpoint_sha": "abc123",
            "dependencies_ready": True,
            "accepted_prerequisites": ["Task 2@rev-2"],
        },
        "git": {
            "source_ref": "git-receipt.json",
            "repository_identity": "repo-1",
            "plan_identity": "plan-1",
            "plan_revision": "rev-1",
            "git_revision": "abc123",
        },
        "worker": {
            "result_ref": "task-result.json",
            "repository_identity": "repo-1",
            "plan_identity": "plan-1",
            "plan_revision": "rev-1",
            "git_revision": "abc123",
            "task_id": "Task 4",
            "publication_valid": True,
            "workstream": "integration",
            "attempt_id": "attempt-1",
            "checkpoint": "checkpoint-1",
        },
        "settlement": {
            "receipt_ref": "settlement.json",
            "settled": True,
            "settlement_proven": True,
            "resource_settled": True,
            "repository_identity": "repo-1",
            "plan_identity": "plan-1",
            "plan_revision": "rev-1",
            "git_revision": "abc123",
            "task_id": "Task 4",
            "attempt_id": "attempt-1",
            "checkpoint": "checkpoint-1",
            "workstream": "integration",
        },
        "acceptance": {
            "proof_ref": "acceptance.json",
            "decision": "PASS",
            "task_id": "Task 4",
            "plan_identity": "plan-1",
            "repository_identity": "repo-1",
            "plan_revision": "rev-1",
            "git_revision": "abc123",
            "attempt_id": "attempt-1",
            "checkpoint": "checkpoint-1",
            "workstream": "integration",
            },
        "next_action": {
            "policy_ref": "policy.json",
            "project_consequence": "dependency released",
            "action": "notify dependent CoS",
            "authorized": True,
        },
    }


def test_build_evidence_snapshot_reconstructs_current_facts() -> None:
    snapshot = build_evidence_snapshot(**_facts())

    assert snapshot.status == CURRENT
    assert snapshot.plan_identity == "plan-1"
    assert snapshot.accepted_prerequisite_refs == ("Task 2@rev-2",)
    assert snapshot.to_dict()["sources"]["worker"] == "task-result.json"


def test_build_evidence_snapshot_marks_missing_facts_without_assuming_success() -> None:
    facts = _facts()
    facts["acceptance"] = {"decision": "PASS"}

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == MISSING
    assert "missing acceptance source" in snapshot.reasons
    assert "acceptance unavailable" not in snapshot.reasons


def test_build_evidence_snapshot_marks_identity_drift_stale() -> None:
    facts = _facts()
    facts["git"]["plan_revision"] = "rev-old"

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == STALE
    assert "Plan revision mismatch" in snapshot.reasons


def test_build_evidence_snapshot_rejects_unpublished_worker_and_unauthorized_action() -> None:
    facts = _facts()
    facts["worker"]["publication_valid"] = False
    facts["next_action"]["authorized"] = False

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == MISSING
    assert "Worker publication unavailable" in snapshot.reasons
    assert "next action is not authorized" in snapshot.reasons


def test_build_evidence_snapshot_rejects_stale_settlement_attempt() -> None:
    facts = _facts()
    facts["settlement"]["attempt_id"] = "attempt-old"

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == STALE
    assert "settlement attempt_id binding mismatch" in snapshot.reasons


def test_build_evidence_snapshot_rejects_git_revision_drift() -> None:
    facts = _facts()
    facts["acceptance"]["git_revision"] = "old-head"

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == STALE
    assert "acceptance git_revision binding mismatch" in snapshot.reasons


def test_build_evidence_snapshot_rejects_current_git_revision_drift() -> None:
    facts = _facts()
    facts["git"]["git_revision"] = "new-head"

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == STALE


def test_remote_reconciliation_does_not_clear_local_trust_failures() -> None:
    facts = _facts()
    facts["next_action"] = {**facts["next_action"], "authorized": False}
    snapshot = build_evidence_snapshot(
        **facts,
        remote={"available": True, "head_sha": facts["git"]["git_revision"], "checks_passed": True, "review_valid": True, "mergeable": True},
    )

    assert snapshot.status == MISSING
    assert "next action is not authorized" in snapshot.reasons
    assert "checkpoint differs from local lane head" not in snapshot.reasons


def test_build_evidence_snapshot_rejects_workstream_drift() -> None:
    facts = _facts()
    facts["worker"]["workstream"] = "other-workstream"

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == STALE
    assert "worker workstream binding mismatch" in snapshot.reasons
