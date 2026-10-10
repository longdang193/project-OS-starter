from pathlib import Path

from scripts.project_os_runtime.acceptance import release_authorized_evidence
from scripts.project_os_runtime.results import publish_task_result


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


def _binding() -> dict[str, str]:
    return {
        "plan_ref": "plan-1",
        "task_id": "Task 1",
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
        "candidate_sha": "candidate-1",
        "acceptance_checkpoint_sha": "c",
        "evidence_ref": "task-result",
    }


def _acceptance_decision() -> dict:
    binding = _binding()
    return {
        "decision": "PASS",
        "controller": {"authority": "cos"},
        "task": {"task_id": binding["task_id"]},
        "task_transition": {"authorized": True, "current_state": "active", "next_state": "completed"},
        "acceptance_proof": {
            "plan_identity": binding["plan_ref"],
            "task_id": binding["task_id"],
            "attempt_id": binding["attempt_id"],
            "checkpoint_sha": binding["acceptance_checkpoint_sha"],
            "repository_identity": "repo",
            "freshness": {"head_matches": True, "write_scope_matches": True},
            "required_conditions": {"tests": True},
            "artifact_conditions": {"tests": True},
            "settlement": {"settlement_proven": True, "resource_settled": True},
            "git": {
                "plan_identity": binding["plan_ref"],
                "candidate_sha": binding["candidate_sha"],
                "acceptance_checkpoint_sha": binding["acceptance_checkpoint_sha"],
                "assignment_id": binding["assignment_id"],
                "attempt_id": binding["attempt_id"],
            },
        },
    }


def _retirement_proof() -> dict[str, object]:
    binding = _binding()
    return {
        "retirement_complete": True,
        **{field: binding[field] for field in ("plan_ref", "task_id", "assignment_id", "attempt_id")},
    }


def _attempt_guard(state: str = "pending") -> dict[str, object]:
    return {"release_authorized": True, "release_state": state}


def _release(
    tmp_path: Path,
    *,
    accepted: bool = True,
    decision: dict | None = None,
    create: bool = True,
    retirement_proof: dict | None = None,
):
    task_result = tmp_path / "task-result.json"
    result = tmp_path / "result.json"
    if create:
        publish_task_result(task_result, _payload(accepted=accepted, checkpoint_sha="c"))
        result.write_text("{}", encoding="utf-8")
    return release_authorized_evidence(
        _acceptance_decision() if decision is None else decision,
        binding=_binding(),
        canonical_consequence={"authorized": True, **{key: value for key, value in _binding().items() if key != "evidence_ref"}},
        required_consumers=["controller"],
        consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
        retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
        evidence_paths={"task-result": task_result, "result": result},
        retirement_proof=_retirement_proof() if retirement_proof is None else retirement_proof,
        release_record={
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": {"state": "pending"}},
            "attempt_guard": _attempt_guard(),
        },
    )


def test_release_requires_exact_acceptance(tmp_path: Path):
    result = _release(tmp_path, decision={})
    assert result["authorized"] is False
    assert (tmp_path / "task-result.json").exists()


def test_release_requires_retirement_proof(tmp_path: Path):
    result = _release(tmp_path, retirement_proof={})
    assert result["authorized"] is False
    assert "retirement proof" in result["reasons"]
    assert (tmp_path / "task-result.json").exists()


def test_release_requires_durable_authorization_record(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    result = release_authorized_evidence(
        _acceptance_decision(),
        binding=_binding(),
        canonical_consequence={"authorized": True, **{key: value for key, value in _binding().items() if key != "evidence_ref"}},
        required_consumers=["controller"],
        consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
        retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
        evidence_paths={"task-result": task_result},
        retirement_proof=_retirement_proof(),
    )
    assert result["authorized"] is False
    assert result["reasons"] == ["durable release authorization required"]
    assert task_result.exists()


def test_release_is_idempotent_after_exact_acceptance(tmp_path: Path):
    result = _release(tmp_path)
    retry = _release(tmp_path, create=False)
    assert result["payload_released"] is True
    assert retry["authorized"] is True
    assert retry["payload_released"] is True
    assert retry["resources"] == {"task-result": {"state": "already_absent"}}


def test_release_deletes_only_bound_evidence_path(tmp_path: Path):
    result = _release(tmp_path)
    assert result["payload_released"] is True
    assert not (tmp_path / "task-result.json").exists()
    assert (tmp_path / "result.json").exists()


def test_release_replay_requires_durable_complete_record(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    release_record = {
        "authorized": True,
        "binding": _binding(),
        "resources": {"task-result": {"state": "removed"}},
        "attempt_guard": _attempt_guard("released"),
    }
    result = release_authorized_evidence(
        _acceptance_decision(),
        binding=_binding(),
        canonical_consequence={"authorized": True, **{key: value for key, value in _binding().items() if key != "evidence_ref"}},
        required_consumers=["controller"],
        consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
        retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
        evidence_paths={"task-result": task_result, "foreign": tmp_path / "foreign.json"},
        retirement_proof=_retirement_proof(),
        release_record=release_record,
    )
    assert result["payload_released"] is True
    assert result["resources"] == release_record["resources"]


def test_release_replay_rejects_incomplete_durable_record(tmp_path: Path):
    result = release_authorized_evidence(
        _acceptance_decision(),
        binding=_binding(),
        canonical_consequence={"authorized": True, **{key: value for key, value in _binding().items() if key != "evidence_ref"}},
        required_consumers=["controller"],
        consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
        retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
        evidence_paths={"task-result": tmp_path / "task-result.json"},
        retirement_proof=_retirement_proof(),
        release_record={
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": {"state": "unverified"}},
            "attempt_guard": _attempt_guard(),
        },
    )
    assert result["authorized"] is False
    assert result["payload_released"] is False


def test_release_replay_recovers_after_disposal_before_final_record(tmp_path: Path):
    result = release_authorized_evidence(
        _acceptance_decision(),
        binding=_binding(),
        canonical_consequence={"authorized": True, **{key: value for key, value in _binding().items() if key != "evidence_ref"}},
        required_consumers=["controller"],
        consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
        retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
        evidence_paths={"task-result": tmp_path / "task-result.json"},
        retirement_proof=_retirement_proof(),
        release_record={
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": {"state": "pending"}},
            "attempt_guard": _attempt_guard(),
        },
    )

    assert result["payload_released"] is True
    assert result["resources"] == {"task-result": {"state": "already_absent"}}


def test_release_preserves_worker_claim_without_canonical_acceptance(tmp_path: Path):
    result = _release(tmp_path, decision={})
    assert result["authorized"] is False
    assert (tmp_path / "task-result.json").exists()


def test_release_preserves_cross_plan_acceptance_proof(tmp_path: Path):
    decision = _acceptance_decision()
    decision["acceptance_proof"]["plan_identity"] = "other-plan"
    result = _release(tmp_path, decision=decision)
    assert result["authorized"] is False
    assert (tmp_path / "task-result.json").exists()


def test_release_preserves_cross_task_and_repository_acceptance_proof(tmp_path: Path):
    decision = _acceptance_decision()
    decision["acceptance_proof"].update(task_id="Task 2", repository_identity="other-repo")
    result = _release(tmp_path, decision=decision)
    assert result["authorized"] is False
    assert (tmp_path / "task-result.json").exists()


def test_release_preserves_missing_canonical_bindings(tmp_path: Path):
    binding = _binding()
    binding["plan_ref"] = ""
    result = release_authorized_evidence(
        _acceptance_decision(),
        binding=binding,
        canonical_consequence={},
        required_consumers=["controller"],
        consumer_releases={},
        retention={},
        evidence_paths={},
    )
    assert result["authorized"] is False


def test_release_preserves_empty_checkpoint_binding(tmp_path: Path):
    result = _release(tmp_path)
    assert result["payload_released"] is True
