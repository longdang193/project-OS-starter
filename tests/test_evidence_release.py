from pathlib import Path

from scripts.project_os_runtime.results import publish_task_result, release_attempt_evidence


def _payload(*, accepted: bool, checkpoint_sha: str) -> dict:
    return {
        "schema": "dcode-project.task-result.v1",
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
        "task_sha256": "a" * 64,
        "grant_digest": "b" * 64,
        "producer": "dcode-project",
        "status": "completed",
        "progress": {},
        "checkpoint": {"sha": checkpoint_sha},
        "remaining_work": [],
        "verification": {"references": ["tests/test_evidence_release.py"]},
        "continuation": {"requested": False},
        "accepted": accepted,
    }


def _acceptance_decision() -> dict:
    return {
        "decision": "PASS",
        "controller": {"authority": "cos"},
        "acceptance_proof": {
            "plan_identity": "plan-1",
            "task_id": "Task 1",
            "attempt_id": "attempt-1",
            "checkpoint_sha": "c",
            "repository_identity": "repo",
        },
    }


def test_release_requires_exact_acceptance(tmp_path: Path):
    publish_task_result(tmp_path / "task-result.json", _payload(accepted=False, checkpoint_sha="c"))

    result = release_attempt_evidence(tmp_path, "assignment-1", "attempt-1", "c")

    assert result["state"] == "preserved"
    assert (tmp_path / "task-result.json").exists()


def test_release_is_idempotent_after_exact_acceptance(tmp_path: Path):
    publish_task_result(tmp_path / "task-result.json", _payload(accepted=True, checkpoint_sha="c"))
    (tmp_path / "result.json").write_text("{}", encoding="utf-8")

    result = release_attempt_evidence(
        tmp_path, "assignment-1", "attempt-1", "c",
        expected_plan_identity="plan-1",
        expected_task_id="Task 1",
        expected_repository_identity="repo",
        acceptance_decision=_acceptance_decision(),
    )
    retry = release_attempt_evidence(
        tmp_path, "assignment-1", "attempt-1", "c",
        expected_plan_identity="plan-1",
        expected_task_id="Task 1",
        expected_repository_identity="repo",
        acceptance_decision=_acceptance_decision(),
    )

    assert result["state"] == "removed"
    assert retry["state"] == "preserved"


def test_release_preserves_worker_claim_without_canonical_acceptance(tmp_path: Path):
    publish_task_result(tmp_path / "task-result.json", _payload(accepted=True, checkpoint_sha="c"))

    result = release_attempt_evidence(tmp_path, "assignment-1", "attempt-1", "c")

    assert result["state"] == "preserved"
    assert (tmp_path / "task-result.json").exists()


def test_release_preserves_cross_plan_acceptance_proof(tmp_path: Path):
    publish_task_result(tmp_path / "task-result.json", _payload(accepted=True, checkpoint_sha="c"))
    decision = _acceptance_decision()
    decision["acceptance_proof"]["plan_identity"] = "other-plan"

    result = release_attempt_evidence(
        tmp_path, "assignment-1", "attempt-1", "c",
        expected_plan_identity="plan-1",
        expected_task_id="Task 1",
        expected_repository_identity="repo",
        acceptance_decision=decision,
    )

    assert result["state"] == "preserved"
    assert (tmp_path / "task-result.json").exists()


def test_release_preserves_cross_task_and_repository_acceptance_proof(tmp_path: Path):
    publish_task_result(tmp_path / "task-result.json", _payload(accepted=True, checkpoint_sha="c"))
    decision = _acceptance_decision()
    decision["acceptance_proof"].update(task_id="Task 2", repository_identity="other-repo")

    result = release_attempt_evidence(
        tmp_path, "assignment-1", "attempt-1", "c",
        expected_plan_identity="plan-1",
        expected_task_id="Task 1",
        expected_repository_identity="repo",
        acceptance_decision=decision,
    )

    assert result["state"] == "preserved"
    assert (tmp_path / "task-result.json").exists()
