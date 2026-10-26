from pathlib import Path
import hashlib
import os
import pytest

from scripts.project_os_runtime import acceptance as acceptance_module
from scripts.project_os_runtime.acceptance import release_authorized_evidence
from scripts.project_os_runtime.results import (
    parse_task_result,
    prune_result_artifact_recovery,
    publish_task_result,
    settle_result_artifacts,
)


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
        "controller": {
            "identity": "native-cos",
            "authority": "cos",
            "plan_identity": binding["plan_ref"],
            "task_id": binding["task_id"],
        },
        "task": {
            "task_id": binding["task_id"],
            "plan_identity": binding["plan_ref"],
            "state": "active",
            "attempt_id": binding["attempt_id"],
        },
        "task_transition": {
            "authorized": True,
            "current_state": "active",
            "next_state": "completed",
            "accepted_candidate_sha": binding["candidate_sha"],
        },
        "acceptance_proof": {
            "plan_identity": binding["plan_ref"],
            "task_id": binding["task_id"],
            "task_state": "active",
            "attempt_id": binding["attempt_id"],
            "checkpoint_sha": binding["acceptance_checkpoint_sha"],
            "repository_identity": "repo",
            "freshness": {"head_matches": True, "write_scope_matches": True},
            "required_conditions": {"tests": True},
            "artifact_conditions": {"tests": True},
            "git": {
                "repository_identity": "repo",
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


def _result_artifact(
    tmp_path: Path,
    *,
    directory_name: str = "herdr-result-attempt-1-owned",
) -> tuple[Path, Path, dict]:
    directory = tmp_path / directory_name
    directory.mkdir()
    (directory / "result.json").write_text('{"state":"confirmed"}\n', encoding="utf-8")
    task_result_file = directory / "task-result.json"
    publish_task_result(task_result_file, _payload(accepted=True, checkpoint_sha="c"))
    task_result = parse_task_result(
        task_result_file,
        assignment_id="assignment-1",
        attempt_id="attempt-1",
        task_sha256="a" * 64,
        grant_digest="b" * 64,
    )
    return directory, task_result_file, task_result


def _settle_result_artifact(
    directory: Path,
    task_result: dict | None,
    *,
    tmp_path: Path,
    lifecycle_settled: bool = True,
) -> dict:
    return settle_result_artifacts(
        directory,
        attempt_id="attempt-1",
        assignment_id="assignment-1",
        task_sha256="a" * 64,
        grant_digest="b" * 64,
        receipt={"state": "confirmed"},
        task_result=task_result,
        lifecycle_settled=lifecycle_settled,
        no_continuation=True,
        temp_root=tmp_path,
        now=100.0,
    )


def test_settled_result_artifacts_are_removed_after_identity_and_lifecycle_proof(tmp_path: Path) -> None:
    directory, _, task_result = _result_artifact(tmp_path)

    result = _settle_result_artifact(directory, task_result, tmp_path=tmp_path)

    assert result["state"] == "removed"
    assert not directory.exists()


def test_settled_result_artifacts_wait_for_downstream_handoff(tmp_path: Path) -> None:
    directory, _, task_result = _result_artifact(tmp_path)

    pending = settle_result_artifacts(
        directory,
        attempt_id="attempt-1",
        assignment_id="assignment-1",
        task_sha256="a" * 64,
        grant_digest="b" * 64,
        receipt={"state": "confirmed"},
        task_result=task_result,
        lifecycle_settled=True,
        no_continuation=True,
        temp_root=tmp_path,
        now=100.0,
        handoff_confirmed=False,
    )

    assert pending["state"] == "pending_handoff"
    assert directory.exists()
    marker = directory / ".herdr-recovery.json"
    assert marker.is_file()
    assert __import__("json").loads(marker.read_text(encoding="utf-8"))["prunable"] is False

    settled = settle_result_artifacts(
        directory,
        attempt_id="attempt-1",
        assignment_id="assignment-1",
        task_sha256="a" * 64,
        grant_digest="b" * 64,
        receipt={"state": "confirmed"},
        task_result=task_result,
        lifecycle_settled=True,
        no_continuation=True,
        temp_root=tmp_path,
        now=100.0,
        handoff_confirmed=True,
    )

    assert settled["state"] == "removed"
    assert not directory.exists()


def test_unpublished_result_artifacts_are_marked_for_recovery(tmp_path: Path) -> None:
    directory = tmp_path / "herdr-result-attempt-1-unpublished"
    directory.mkdir()

    result = settle_result_artifacts(
        directory,
        attempt_id="attempt-1",
        assignment_id="assignment-1",
        task_sha256="a" * 64,
        grant_digest="b" * 64,
        receipt=None,
        task_result=None,
        lifecycle_settled=False,
        no_continuation=False,
        temp_root=tmp_path,
        now=100.0,
        handoff_confirmed=False,
    )

    assert result["state"] == "preserved"
    assert (directory / ".herdr-recovery.json").is_file()


def test_absent_result_artifacts_are_idempotently_settled(tmp_path: Path) -> None:
    directory = tmp_path / "herdr-result-attempt-1-already-absent"

    result = _settle_result_artifact(directory, None, tmp_path=tmp_path)

    assert result["state"] == "absent"


def test_foreign_result_directory_is_preserved(tmp_path: Path) -> None:
    directory, _, task_result = _result_artifact(
        tmp_path,
        directory_name="herdr-result-foreign-owned",
    )

    result = _settle_result_artifact(directory, task_result, tmp_path=tmp_path)

    assert result["state"] == "preserved"
    assert "ownership" in result["reason"]
    assert directory.exists()


def test_identity_mismatch_preserves_result_artifacts(tmp_path: Path) -> None:
    directory, task_result_file, _ = _result_artifact(tmp_path)
    mismatched = parse_task_result(
        task_result_file,
        assignment_id="assignment-2",
        attempt_id="attempt-1",
        task_sha256="a" * 64,
        grant_digest="b" * 64,
    )

    result = _settle_result_artifact(directory, mismatched, tmp_path=tmp_path)

    assert result["state"] == "preserved"
    assert "publication or identity" in result["reason"]
    assert directory.exists()


def test_unresolved_publication_is_retained_for_recovery(tmp_path: Path) -> None:
    directory, _, _ = _result_artifact(tmp_path)

    result = _settle_result_artifact(directory, None, tmp_path=tmp_path, lifecycle_settled=False)

    assert result["state"] == "preserved"
    assert directory.exists()
    assert (directory / ".herdr-recovery.json").exists()


def test_recovery_pruning_is_bounded_to_marked_result_directories(tmp_path: Path) -> None:
    first, _, first_result = _result_artifact(
        tmp_path,
        directory_name="herdr-result-attempt-1-first",
    )
    second, _, second_result = _result_artifact(
        tmp_path,
        directory_name="herdr-result-attempt-1-second",
    )
    _settle_result_artifact(first, None, tmp_path=tmp_path, lifecycle_settled=False)
    _settle_result_artifact(second, None, tmp_path=tmp_path, lifecycle_settled=False)
    for directory in (first, second):
        marker = directory / ".herdr-recovery.json"
        payload = __import__("json").loads(marker.read_text(encoding="utf-8"))
        payload["prunable"] = True
        marker.write_text(__import__("json").dumps(payload), encoding="utf-8")
    foreign = tmp_path / "herdr-result-foreign-unmarked"
    foreign.mkdir()
    (foreign / "keep.txt").write_text("keep", encoding="utf-8")

    result = prune_result_artifact_recovery(
        temp_root=tmp_path,
        max_age_seconds=1000,
        max_count=1,
        now=100.0,
    )

    assert result["removed"] == 1
    assert result["preserved"] == 1
    assert foreign.exists()
    assert first.exists() != second.exists()
    assert first_result["state"] == "confirmed"
    assert second_result["state"] == "confirmed"


def test_recovery_pruning_preserves_unresolved_markers(tmp_path: Path) -> None:
    first, _, _ = _result_artifact(tmp_path, directory_name="herdr-result-attempt-1-unresolved")
    second, _, _ = _result_artifact(tmp_path, directory_name="herdr-result-attempt-1-unresolved-2")
    _settle_result_artifact(first, None, tmp_path=tmp_path, lifecycle_settled=False)
    _settle_result_artifact(second, None, tmp_path=tmp_path, lifecycle_settled=False)

    result = prune_result_artifact_recovery(
        temp_root=tmp_path,
        max_age_seconds=0,
        max_count=1,
        now=100.0,
    )

    assert result["removed"] == 0
    assert first.exists()
    assert second.exists()


def test_recovery_pruning_skips_non_object_markers_without_aborting(tmp_path: Path) -> None:
    invalid = tmp_path / "herdr-result-invalid-marker"
    invalid.mkdir()
    (invalid / ".herdr-recovery.json").write_text("[]", encoding="utf-8")

    valid, _, _ = _result_artifact(tmp_path, directory_name="herdr-result-valid-marker")
    _settle_result_artifact(valid, None, tmp_path=tmp_path, lifecycle_settled=False)

    result = prune_result_artifact_recovery(
        temp_root=tmp_path,
        max_age_seconds=0,
        max_count=10,
        now=100.0,
    )

    assert result["state"] == "completed"
    assert invalid.exists()


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


def _runtime_settlement() -> dict[str, object]:
    return {
        "attempt_id": "attempt-1",
        "settlement_proven": True,
        "resource_settled": True,
    }


def _release(
    tmp_path: Path,
    *,
    accepted: bool = True,
    decision: dict | None = None,
    create: bool = True,
    retirement_proof: dict | None = None,
    runtime_settlement: dict | None = None,
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
        runtime_settlement=runtime_settlement or {
            "attempt_id": "attempt-1",
            "settlement_proven": True,
            "resource_settled": True,
        },
        release_record={
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": resource},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )


def test_release_uses_fresh_same_attempt_runtime_settlement(tmp_path: Path):
    decision = _acceptance_decision()
    assert "settlement" not in decision["acceptance_proof"]

    result = _release(
        tmp_path,
        decision=decision,
        runtime_settlement={
            "attempt_id": "attempt-1",
            "settlement_proven": True,
            "resource_settled": True,
        },
    )

    assert result["authorized"] is True


def test_release_requires_exact_acceptance(tmp_path: Path):
    result = _release(tmp_path, decision={})
    assert result["authorized"] is False
    assert (tmp_path / "task-result.json").exists()


def test_release_rejects_incomplete_common_acceptance_decision(tmp_path: Path):
    decision = _acceptance_decision()
    decision["controller"]["identity"] = ""

    result = _release(tmp_path, decision=decision)

    assert result["authorized"] is False
    assert "controller identity" in result["reasons"]
    assert (tmp_path / "task-result.json").exists()


def test_release_preserves_common_validation_reasons(tmp_path: Path):
    decision = _acceptance_decision()
    decision["acceptance_proof"]["repository_identity"] = "other-repository"

    result = _release(tmp_path, decision=decision)

    assert result["authorized"] is False
    assert result["validation_reasons"] == ["acceptance proof and Git repository binding mismatch"]
    assert "acceptance proof and Git repository binding mismatch" in result["reasons"]
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
        runtime_settlement=_runtime_settlement(),
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
        runtime_settlement=_runtime_settlement(),
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
        runtime_settlement=_runtime_settlement(),
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
        runtime_settlement=_runtime_settlement(),
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
        runtime_settlement=_runtime_settlement(),
        release_record={
            "authorized": True,
            "binding": _binding(),
            "resources": {"task-result": _resource(tmp_path)},
            "attempt_guard": _attempt_guard(worktree=tmp_path),
        },
    )

    assert result["payload_released"] is True
    assert result["resources"]["task-result"]["state"] == "already_absent"


def test_release_replay_removes_deterministic_quarantine_after_rename_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    resource = _resource(
        tmp_path,
        digest=hashlib.sha256(task_result.read_bytes()).hexdigest(),
    )
    quarantine_path = task_result.with_name(f".{task_result.name}.{resource['content_sha256']}.release")
    task_result.rename(quarantine_path)

    def release() -> dict:
        return release_authorized_evidence(
            _acceptance_decision(),
            binding=_binding(),
            canonical_consequence=_canonical_consequence(),
            required_consumers=["controller"],
            consumer_releases={"controller": {"authorized": True, "consumer": "controller", **_binding()}},
            retention={"controller": {"policy_ref": "retention-1", "expired": True, "consumer": "controller", "evidence_ref": "task-result"}},
            evidence_paths={"task-result": task_result},
            retirement_proof=_retirement_proof(),
        runtime_settlement=_runtime_settlement(),
            release_record={
                "authorized": True,
                "binding": _binding(),
                "resources": {"task-result": resource},
                "attempt_guard": _attempt_guard(worktree=tmp_path),
            },
        )

    assert not (tmp_path / "task-result.json").exists()
    second = release()

    assert second["payload_released"] is True
    assert second["resources"]["task-result"]["state"] == "removed"
    assert not quarantine_path.exists()


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
        runtime_settlement=_runtime_settlement(),
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
    assert "replacement_detected" in result["reasons"][0]
    assert task_result.read_text(encoding="utf-8").startswith('{"producer": "dcode-project"')


@pytest.mark.skipif(os.name == "nt", reason="Windows disposal holds an exclusive handle")
def test_pending_replacement_after_final_digest_preserves_artifact(monkeypatch, tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))
    original = task_result.read_bytes()
    resource = _resource(tmp_path, digest=hashlib.sha256(original).hexdigest())
    original_digest = acceptance_module._digest_for_fd
    replaced = False

    def replace_after_digest(fd: int) -> str:
        nonlocal replaced
        digest = original_digest(fd)
        if not replaced:
            replacement = task_result.with_name("replacement.json")
            replacement.write_text(
                '{"producer": "dcode-project", "schema": "dcode-project.task-result.v1"}',
                encoding="utf-8",
            )
            replacement.replace(task_result)
            replaced = True
        return digest

    monkeypatch.setattr(acceptance_module, "_digest_for_fd", replace_after_digest)
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
    assert "replacement_detected" in result["reasons"][0]
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


def test_legacy_worker_acceptance_cannot_authorize_evidence_release(tmp_path: Path):
    task_result = tmp_path / "task-result.json"
    publish_task_result(task_result, _payload(accepted=True, checkpoint_sha="c"))

    payload = parse_task_result(
        task_result,
        assignment_id="assignment-1",
        attempt_id="attempt-1",
        task_sha256="a" * 64,
        grant_digest="b" * 64,
    )

    result = _release(tmp_path, decision={})

    assert "accepted" not in payload
    assert result["authorized"] is False


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
        runtime_settlement=_runtime_settlement(),
    )
    assert result["authorized"] is False


def test_release_preserves_empty_checkpoint_binding(tmp_path: Path):
    result = _release(tmp_path)
    assert result["payload_released"] is True
