from pathlib import Path
import hashlib

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


def _attempt_guard(state: str = "pending", *, worktree: Path | None = None) -> dict[str, object]:
    guard = {"release_authorized": True, "release_state": state}
    if worktree is not None:
        guard["worktree"] = str(worktree.resolve())
    return guard


def _resource(
    tmp_path: Path,
    *,
    state: str = "pending",
    filename: str = "task-result.json",
    attempt_id: str = "attempt-1",
    digest: str | None = None,
) -> dict[str, object]:
    return {
        "state": state,
        "attempt_id": attempt_id,
        "evidence_ref": "task-result",
        "attempt_root": str(tmp_path.resolve()),
        "relative_path": filename,
        "content_sha256": digest or "0" * 64,
        "producer": "dcode-project",
        "schema": "dcode-project.task-result.v1",
    }


def _canonical_consequence(binding: dict[str, str] | None = None) -> dict[str, object]:
    current = _binding() if binding is None else binding
    return {
        "authorized": True,
        "owner": "git",
        "checkpoint_verified": True,
        "commit_sha": "commit-1",
        "coordination_ref": "coordination",
        "plan_path": "plan.md",
        "expected_plan_revision": "revision-1",
        **{key: value for key, value in current.items() if key != "evidence_ref"},
    }


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
    resource = _resource(
        tmp_path,
        digest=hashlib.sha256(task_result.read_bytes()).hexdigest() if create else None,
    )
    return release_authorized_evidence(
        _acceptance_decision() if decision is None else decision,
        binding=_binding(),
        canonical_consequence=_canonical_consequence(),
        required_consumers=["controller"],
        consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
        retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
        evidence_paths={"task-result": task_result, "result": result},
        retirement_proof=_retirement_proof() if retirement_proof is None else retirement_proof,
        release_record={
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": resource},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
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


def test_release_requires_verified_git_checkpoint(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    result = release_authorized_evidence(
        _acceptance_decision(),
        binding=_binding(),
        canonical_consequence={**_canonical_consequence(), "checkpoint_verified": False},
        required_consumers=["controller"],
        consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
        retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
        evidence_paths={"task-result": task_result},
        retirement_proof=_retirement_proof(),
        release_record={
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": _resource(tmp_path)},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )
    assert result["authorized"] is False
    assert "verified Git checkpoint" in result["reasons"]
    assert task_result.exists()


def test_release_requires_durable_authorization_record(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    result = release_authorized_evidence(
        _acceptance_decision(),
        binding=_binding(),
        canonical_consequence=_canonical_consequence(),
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
    assert retry["resources"]["task-result"]["state"] == "already_absent"


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
        "resources": {"task-result": _resource(tmp_path, state="removed")},
        "attempt_guard": _attempt_guard("released", worktree=tmp_path),
    }
    result = release_authorized_evidence(
        _acceptance_decision(),
        binding=_binding(),
        canonical_consequence=_canonical_consequence(),
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
        canonical_consequence=_canonical_consequence(),
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
        canonical_consequence=_canonical_consequence(),
        required_consumers=["controller"],
        consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
        retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
        evidence_paths={"task-result": tmp_path / "task-result.json"},
        retirement_proof=_retirement_proof(),
        release_record={
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": _resource(tmp_path)},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )

    assert result["payload_released"] is True
    assert result["resources"]["task-result"]["state"] == "already_absent"


def _invoke_release(
    tmp_path: Path,
    release_record: dict[str, object],
    *,
    evidence_path: Path | None = None,
    binding: dict[str, str] | None = None,
) -> dict[str, object]:
    current_binding = _binding() if binding is None else binding
    return release_authorized_evidence(
        _acceptance_decision(),
        binding=current_binding,
        canonical_consequence=_canonical_consequence(current_binding),
        required_consumers=["controller"],
        consumer_releases={
            "controller": {"authorized": True, "consumer": "controller", **current_binding}
        },
        retention={
            "controller": {
                "policy_ref": "retention-1",
                "expired": True,
                "consumer": "controller",
                "evidence_ref": "task-result",
            }
        },
        evidence_paths={"task-result": evidence_path or tmp_path / "task-result.json"},
        retirement_proof=_retirement_proof(),
        release_record=release_record,
    )


def test_terminal_removed_replay_does_not_touch_replacement(tmp_path: Path):
    replacement = tmp_path / "task-result.json"
    replacement.write_text("replacement", encoding="utf-8")
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": {"state": "removed"}},
            "attempt_guard": _attempt_guard("released"),
        },
        evidence_path=replacement,
    )
    assert result["payload_released"] is True
    assert result["resources"] == {"task-result": {"state": "removed"}}
    assert replacement.read_text(encoding="utf-8") == "replacement"


def test_terminal_already_absent_replay_does_not_touch_replacement(tmp_path: Path):
    replacement = tmp_path / "task-result.json"
    replacement.write_text("replacement", encoding="utf-8")
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": {"state": "already_absent"}},
            "attempt_guard": _attempt_guard("released"),
        },
        evidence_path=replacement,
    )
    assert result["payload_released"] is True
    assert result["resources"] == {"task-result": {"state": "already_absent"}}
    assert replacement.read_text(encoding="utf-8") == "replacement"


def test_pending_binding_mismatch_preserves_artifact(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    resource = _resource(tmp_path, digest=hashlib.sha256(task_result.read_bytes()).hexdigest())
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": resource},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
        evidence_path=tmp_path / "other.json",
    )
    assert result["authorized"] is False
    assert "binding_mismatch" in result["reasons"][0]
    assert task_result.exists()


def test_pending_digest_mismatch_preserves_artifact(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": _resource(tmp_path, digest="0" * 64)},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )
    assert result["authorized"] is False
    assert "digest mismatch" in result["reasons"][0]
    assert task_result.exists()


def test_pending_replacement_after_validation_preserves_artifact(
    monkeypatch, tmp_path: Path
):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    original = task_result.read_bytes()
    resource = _resource(tmp_path, digest=hashlib.sha256(original).hexdigest())
    original_read_bytes = Path.read_bytes
    reads = 0

    def replace_after_first_read(path: Path) -> bytes:
        nonlocal reads
        content = original_read_bytes(path)
        if path == task_result:
            reads += 1
            if reads == 1:
                path.write_text(
                    '{"producer": "dcode-project", "schema": "dcode-project.task-result.v1"}',
                    encoding="utf-8",
                )
        return content

    monkeypatch.setattr(Path, "read_bytes", replace_after_first_read)
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": resource},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )
    assert result["authorized"] is False
    assert "digest mismatch" in result["reasons"][0]
    assert task_result.read_text(encoding="utf-8").startswith('{"producer": "dcode-project"')


def test_pending_wrong_attempt_preserves_artifact(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {
                "task-result": _resource(
                    tmp_path,
                    attempt_id="attempt-2",
                    digest=hashlib.sha256(task_result.read_bytes()).hexdigest(),
                )
            },
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )
    assert result["authorized"] is False
    assert "attempt binding mismatch" in result["reasons"][0]
    assert task_result.exists()


def test_pending_out_of_root_binding_preserves_artifact(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    resource = _resource(tmp_path, digest=hashlib.sha256(task_result.read_bytes()).hexdigest())
    resource["relative_path"] = "../task-result.json"
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": resource},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )
    assert result["authorized"] is False
    assert "binding_mismatch" in result["reasons"][0]
    assert task_result.exists()


def test_pending_non_file_artifact_preserves_path(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    task_result.mkdir()
    resource = _resource(tmp_path)
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": resource},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )
    assert result["authorized"] is False
    assert "type mismatch" in result["reasons"][0]
    assert task_result.is_dir()


def test_pending_symlink_preserves_target(tmp_path: Path):
    target = tmp_path / "target.json"
    target.write_text("target", encoding="utf-8")
    link = tmp_path / "task-result.json"
    try:
        link.symlink_to(target)
    except OSError:
        import pytest

        pytest.skip("symlink creation unavailable")
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": _resource(tmp_path, digest=hashlib.sha256(target.read_bytes()).hexdigest())},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )
    assert result["authorized"] is False
    assert "symlink" in result["reasons"][0]
    assert target.exists()


def test_pending_parent_link_preserves_external_artifact(tmp_path: Path):
    root = tmp_path / "attempt"
    external = tmp_path / "external"
    root.mkdir()
    external.mkdir()
    target = external / "task-result.json"
    publish_task_result(target, _payload(accepted=True, checkpoint_sha="c"))
    nested = root / "nested"
    try:
        nested.symlink_to(external, target_is_directory=True)
    except OSError:
        import pytest

        pytest.skip("directory symlink creation unavailable")
    resource = _resource(
        root,
        filename="nested/task-result.json",
        digest=hashlib.sha256(target.read_bytes()).hexdigest(),
    )
    result = _invoke_release(
        root,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": resource},
            "attempt_guard": _attempt_guard(worktree=root),
        },
        evidence_path=nested / "task-result.json",
    )
    assert result["authorized"] is False
    assert "link or reparse point" in result["reasons"][0]
    assert target.exists()


def test_pending_producer_identity_mismatch_preserves_artifact(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    resource = _resource(tmp_path, digest=hashlib.sha256(task_result.read_bytes()).hexdigest())
    resource["producer"] = "other-producer"
    result = _invoke_release(
        tmp_path,
        {
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": resource},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )
    assert result["authorized"] is False
    assert "producer identity mismatch" in result["reasons"][0]
    assert task_result.exists()


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
