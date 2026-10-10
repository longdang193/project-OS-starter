"""Native CoS acceptance decisions over existing plan and runtime evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any

from .reconciliation import ReconciliationInput, reconcile


ACCEPTANCE_DECISIONS = frozenset({"PASS", "FAIL", "BLOCKED"})
ACCEPTANCE_AUTHORITY = "cos"
ELIGIBLE_TASK_STATE = "active"
RELEASE_BINDING_FIELDS = (
    "plan_ref",
    "task_id",
    "assignment_id",
    "attempt_id",
    "candidate_sha",
    "acceptance_checkpoint_sha",
    "evidence_ref",
)


def _missing_text(mapping: Mapping[str, Any], field: str, label: str) -> str | None:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        return label
    return None


def _required_bool(mapping: Mapping[str, Any], field: str, label: str) -> tuple[str | None, bool | None]:
    value = mapping.get(field)
    if not isinstance(value, bool):
        return label, None
    return None, value


def evaluate_acceptance(
    *,
    controller: Mapping[str, Any],
    task: Mapping[str, Any],
    evidence: Mapping[str, Any],
    artifact_conditions: Mapping[str, Any],
    git: Mapping[str, Any],
    verification: Mapping[str, Any],
    settlement: Mapping[str, Any],
    attempt_id: str | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    for mapping, fields in (
        (controller, (("identity", "controller identity"), ("plan_identity", "controller plan binding"), ("task_id", "controller task binding"))),
        (task, (("task_id", "task identity"), ("plan_identity", "task plan binding"), ("required_proof", "required proof"), ("evidence", "task evidence reference"))),
        (git, (("repository_identity", "Git repository binding"), ("plan_identity", "Git plan binding"))),
    ):
        for field, label in fields:
            missing = _missing_text(mapping, field, label)
            if missing:
                reasons.append(missing)
    if controller.get("authority") != ACCEPTANCE_AUTHORITY:
        reasons.append("CoS acceptance authority")
    if controller.get("plan_identity") != task.get("plan_identity"):
        reasons.append("controller and task plan binding mismatch")
    if git.get("plan_identity") != task.get("plan_identity"):
        reasons.append("Git and task plan binding mismatch")
    if controller.get("task_id") != task.get("task_id"):
        reasons.append("controller and task identity mismatch")
    required_conditions = task.get("required_conditions")
    required_condition_ids: set[str] = set()
    if not isinstance(required_conditions, Mapping) or not required_conditions:
        reasons.append("required condition set")
    else:
        required_condition_ids = {
            condition_id
            for condition_id in required_conditions
            if isinstance(condition_id, str) and condition_id.strip()
        }
        if len(required_condition_ids) != len(required_conditions):
            reasons.append("required condition set")

    if not isinstance(artifact_conditions, Mapping) or any(
        not isinstance(value, bool) for value in artifact_conditions.values()
    ):
        reasons.append("artifact condition type")
    elif set(artifact_conditions) != required_condition_ids:
        reasons.append("artifact condition coverage")

    if task.get("state") != ELIGIBLE_TASK_STATE:
        reasons.append("task state eligibility")

    false_checks: list[str] = []
    for mapping, fields in (
        (evidence, (("publication_valid", "Worker publication"), ("task_completed", "task completion"), ("task_identity_matches", "task identity"))),
        (git, (("head_matches", "Git checkpoint"), ("write_scope_matches", "Git write scope"))),
        (verification, (("passed", "verification"),)),
    ):
        for field, label in fields:
            missing, value = _required_bool(mapping, field, label)
            if missing:
                reasons.append(missing)
            elif value is False:
                false_checks.append(label)
    for field, label in (("settlement_proven", "settlement proof"), ("resource_settled", "resource settlement")):
        missing, value = _required_bool(settlement, field, label)
        if missing or value is False:
            reasons.append(missing or label)
    if isinstance(artifact_conditions, Mapping):
        false_checks.extend(
            f"artifact condition: {name}"
            for name, value in artifact_conditions.items()
            if value is False
        )

    if reasons:
        decision = "BLOCKED"
    elif false_checks:
        decision = "FAIL"
        reasons = false_checks
    else:
        decision = "PASS"
    reconciliation = reconcile(
        ReconciliationInput(
            phase="accept",
            facts={
            "verification_current": verification.get("passed") is True,
            "candidate_unchanged": git.get("head_matches") is True,
            "acceptance_criteria_evaluable": bool(artifact_conditions),
            "cos_pass": decision == "PASS",
            "checkpoint_sha": git.get("checkpoint_sha"),
            "lane_head_sha": git.get("lane_head_sha"),
            },
        )
    )
    current_state = task.get("state")
    task_transition = {
        "authorized": decision == "PASS",
        "current_state": current_state,
        "next_state": "completed" if decision == "PASS" else current_state,
    }
    acceptance_proof = {
        "task_id": task.get("task_id"),
        "plan_identity": task.get("plan_identity"),
        "task_state": current_state,
        "attempt_id": attempt_id or task.get("attempt_id"),
        "checkpoint_sha": git.get("checkpoint_sha"),
        "repository_identity": git.get("repository_identity"),
        "required_conditions": dict(required_conditions) if isinstance(required_conditions, Mapping) else {},
        "artifact_conditions": dict(artifact_conditions) if isinstance(artifact_conditions, Mapping) else {},
        "freshness": {
            "head_matches": git.get("head_matches"),
            "write_scope_matches": git.get("write_scope_matches"),
        },
        "git": {
            "repository_identity": git.get("repository_identity"),
            "plan_identity": git.get("plan_identity"),
            "candidate_sha": git.get("lane_head_sha"),
            "acceptance_checkpoint_sha": git.get("checkpoint_sha"),
            "assignment_id": git.get("assignment_id"),
            "attempt_id": git.get("attempt_id"),
        },
        "settlement": {
            "settlement_proven": settlement.get("settlement_proven"),
            "resource_settled": settlement.get("resource_settled"),
        },
    }
    return {
        "decision": decision,
        "reasons": reasons or ["acceptance criteria satisfied"],
        "controller": {
            "identity": controller.get("identity"),
            "authority": controller.get("authority"),
            "plan_identity": controller.get("plan_identity"),
            "task_id": controller.get("task_id"),
        },
        "task": {
            "task_id": task.get("task_id"),
            "plan_identity": task.get("plan_identity"),
        },
        "task_transition": task_transition,
        "acceptance_proof": acceptance_proof,
        "reconciliation": reconciliation.to_dict(),
    }


def authorize_evidence_release(
    decision: Mapping[str, Any],
    *,
    binding: Mapping[str, Any],
    canonical_consequence: Mapping[str, Any],
    required_consumers: Sequence[str],
    consumer_releases: Mapping[str, Mapping[str, Any]],
    retention: Mapping[str, Mapping[str, Any]],
    retirement_proof: Mapping[str, Any] | None = None,
    recovery_required: bool = False,
) -> dict[str, Any]:
    reasons: list[str] = []
    if decision.get("decision") != "PASS":
        reasons.append("CoS acceptance")
    controller = decision.get("controller")
    if not isinstance(controller, Mapping) or controller.get("authority") != ACCEPTANCE_AUTHORITY:
        reasons.append("CoS release authority")
    accepted_task = decision.get("task")
    if not isinstance(accepted_task, Mapping):
        reasons.append("accepted task")
    elif accepted_task.get("task_id") != binding.get("task_id"):
        reasons.append("task binding")
    proof = decision.get("acceptance_proof")
    if not isinstance(proof, Mapping):
        reasons.append("acceptance proof")
    else:
        if proof.get("task_id") != binding.get("task_id"):
            reasons.append("acceptance task binding")
        if proof.get("plan_identity") != binding.get("plan_ref"):
            reasons.append("acceptance plan binding")
        task_transition = decision.get("task_transition")
        if (
            not isinstance(task_transition, Mapping)
            or task_transition.get("authorized") is not True
            or task_transition.get("current_state") != "active"
            or task_transition.get("next_state") != "completed"
        ):
            reasons.append("task transition")
        freshness = proof.get("freshness")
        if (
            not isinstance(freshness, Mapping)
            or freshness.get("head_matches") is not True
            or freshness.get("write_scope_matches") is not True
        ):
            reasons.append("acceptance freshness")
        required_conditions = proof.get("required_conditions")
        artifact_conditions = proof.get("artifact_conditions")
        if (
            not isinstance(required_conditions, Mapping)
            or not required_conditions
            or not isinstance(artifact_conditions, Mapping)
            or not artifact_conditions
            or set(required_conditions) != set(artifact_conditions)
            or any(value is not True for value in artifact_conditions.values())
        ):
            reasons.append("acceptance condition coverage")
        settlement = proof.get("settlement")
        if (
            not isinstance(settlement, Mapping)
            or settlement.get("settlement_proven") is not True
            or settlement.get("resource_settled") is not True
        ):
            reasons.append("acceptance settlement")
        git = proof.get("git")
        if not isinstance(git, Mapping):
            reasons.append("canonical Git proof")
        else:
            if git.get("plan_identity") != binding.get("plan_ref"):
                reasons.append("plan binding")
            if git.get("candidate_sha") != binding.get("candidate_sha"):
                reasons.append("candidate binding")
            if git.get("acceptance_checkpoint_sha") != binding.get("acceptance_checkpoint_sha"):
                reasons.append("acceptance checkpoint binding")
            if git.get("assignment_id") != binding.get("assignment_id"):
                reasons.append("assignment binding")
            if git.get("attempt_id") != binding.get("attempt_id"):
                reasons.append("attempt binding")
    for field in RELEASE_BINDING_FIELDS:
        value = binding.get(field)
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"missing {field}")
    if not isinstance(canonical_consequence, Mapping):
        reasons.append("canonical consequence")
    else:
        if canonical_consequence.get("authorized") is not True:
            reasons.append("canonical consequence")
        if (
            canonical_consequence.get("owner") != "git"
            or canonical_consequence.get("checkpoint_verified") is not True
            or not isinstance(canonical_consequence.get("commit_sha"), str)
            or not canonical_consequence.get("commit_sha", "").strip()
            or not isinstance(canonical_consequence.get("coordination_ref"), str)
            or not canonical_consequence.get("coordination_ref", "").strip()
            or not isinstance(canonical_consequence.get("plan_path"), str)
            or not canonical_consequence.get("plan_path", "").strip()
            or not isinstance(canonical_consequence.get("expected_plan_revision"), str)
            or not canonical_consequence.get("expected_plan_revision", "").strip()
        ):
            reasons.append("verified Git checkpoint")
        for field in RELEASE_BINDING_FIELDS[:-1]:
            if canonical_consequence.get(field) != binding.get(field):
                reasons.append(f"canonical {field} binding")
    if recovery_required:
        reasons.append("recovery required")
    if not isinstance(retirement_proof, Mapping) or retirement_proof.get("retirement_complete") is not True:
        reasons.append("retirement proof")
    else:
        for field in ("plan_ref", "task_id", "assignment_id", "attempt_id"):
            if retirement_proof.get(field) != binding.get(field):
                reasons.append(f"retirement {field} binding")
    if (
        not isinstance(required_consumers, Sequence)
        or isinstance(required_consumers, (str, bytes))
        or not required_consumers
        or any(not isinstance(consumer, str) or not consumer.strip() for consumer in required_consumers)
        or len(set(required_consumers)) != len(required_consumers)
    ):
        reasons.append("required consumers")
        required_consumers = ()
    if not isinstance(consumer_releases, Mapping):
        reasons.append("consumer release evidence")
        consumer_releases = {}
    elif set(consumer_releases) != set(required_consumers):
        reasons.append("consumer inventory binding")
    if not isinstance(retention, Mapping):
        reasons.append("retention evidence")
        retention = {}
    for consumer in required_consumers:
        release = consumer_releases.get(consumer)
        policy = retention.get(consumer)
        if not isinstance(release, Mapping) or release.get("authorized") is not True:
            reasons.append(f"consumer release: {consumer}")
        elif (
            release.get("consumer") != consumer
            or any(release.get(field) != binding.get(field) for field in RELEASE_BINDING_FIELDS)
        ):
            reasons.append(f"consumer binding: {consumer}")
        if not isinstance(policy, Mapping) or not isinstance(policy.get("policy_ref"), str) or not policy.get("policy_ref"):
            reasons.append(f"retention policy: {consumer}")
        elif (
            policy.get("expired") is not True
            or policy.get("consumer") != consumer
            or policy.get("evidence_ref") != binding.get("evidence_ref")
        ):
            reasons.append(f"retention active: {consumer}")
    return {
        "authorized": not reasons,
        "reasons": reasons or ["evidence release authorized"],
        "payload_released": False,
        "tombstone_released": False,
        "binding": dict(binding),
    }


def _release_resource_check(
    resource: Mapping[str, Any],
    *,
    binding: Mapping[str, Any],
    evidence_ref: str,
    attempt_guard: Mapping[str, Any],
    path: Path,
) -> tuple[str | None, os.stat_result | None]:
    if resource.get("attempt_id") != binding.get("attempt_id"):
        return "attempt binding mismatch", None
    if resource.get("evidence_ref") != evidence_ref:
        return "evidence reference binding mismatch", None
    attempt_root = resource.get("attempt_root")
    relative_path = resource.get("relative_path")
    digest = resource.get("content_sha256") or resource.get("artifact_digest")
    if not all(isinstance(value, str) and value.strip() for value in (attempt_root, relative_path, digest)):
        return "physical release binding missing", None
    root = Path(attempt_root)
    relative = Path(relative_path)
    if not root.is_absolute() or relative.is_absolute() or ".." in relative.parts:
        return "physical release binding invalid", None
    def has_link_or_reparse(value: Path) -> bool:
        if value.is_symlink():
            return True
        try:
            attributes = getattr(os.lstat(value), "st_file_attributes", 0)
        except OSError:
            return False
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))

    if has_link_or_reparse(root) or not root.is_dir():
        return "attempt root binding mismatch", None
    guarded_root = attempt_guard.get("worktree")
    if isinstance(guarded_root, str) and guarded_root:
        if root.resolve(strict=True) != Path(guarded_root).resolve(strict=True):
            return "attempt root binding mismatch", None
    expected_path = root / relative
    parent = root
    for component in relative.parts[:-1]:
        parent = parent / component
        if parent.exists() and has_link_or_reparse(parent):
            return "evidence path traverses link or reparse point", None
    if has_link_or_reparse(path):
        return "evidence path is symlink", None
    try:
        resolved_root = root.resolve(strict=True)
        resolved_path = path.resolve(strict=False)
        if resolved_path != expected_path.resolve(strict=False):
            return "evidence path binding mismatch", None
        resolved_path.relative_to(resolved_root)
    except OSError:
        return "evidence path binding mismatch", None
    except ValueError:
        return "evidence path outside attempt root", None
    if not path.exists():
        return None, None
    if not path.is_file():
        return "evidence artifact type mismatch", None
    try:
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "evidence artifact unreadable", None
    if actual_digest != digest:
        return "evidence artifact digest mismatch", None
    for field in ("producer", "schema"):
        expected = resource.get(field)
        if expected is None:
            continue
        if not isinstance(expected, str) or not expected.strip():
            return f"{field} identity invalid", None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return "artifact identity unavailable", None
        if not isinstance(payload, Mapping) or payload.get(field) != expected:
            return f"{field} identity mismatch", None
    try:
        verified_stat = os.stat(path, follow_symlinks=False)
    except OSError:
        return "evidence artifact unavailable", None
    return None, verified_stat


def _same_file_identity(first: os.stat_result, second: os.stat_result) -> bool:
    return (first.st_dev, first.st_ino) == (second.st_dev, second.st_ino)


def _unlink_verified_file(path: Path, verified_stat: os.stat_result, expected_digest: str) -> str | None:
    if os.name == "nt":
        import ctypes
        import ctypes.wintypes
        import msvcrt

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel32.CreateFileW
        create_file.argtypes = [
            ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.LPVOID,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.HANDLE,
        ]
        create_file.restype = ctypes.wintypes.HANDLE
        set_file_information = kernel32.SetFileInformationByHandle
        set_file_information.argtypes = [
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.INT,
            ctypes.wintypes.LPVOID,
            ctypes.wintypes.DWORD,
        ]
        set_file_information.restype = ctypes.wintypes.BOOL
        handle = kernel32.CreateFileW(
            str(path),
            0x80000000 | 0x00010000 | 0x00000080,
            0x00000001 | 0x00000002 | 0x00000004,
            None,
            3,
            0x00000080,
            None,
        )
        if handle == ctypes.wintypes.HANDLE(-1).value:
            return "evidence artifact unavailable"
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | getattr(os, "O_BINARY", 0))
        try:
            if not _same_file_identity(os.fstat(fd), verified_stat):
                return "evidence artifact changed"
            if _digest_for_fd(fd) != expected_digest:
                return "evidence artifact changed"
            disposition = ctypes.c_byte(1)
            if not set_file_information(
                msvcrt.get_osfhandle(fd),
                4,
                ctypes.byref(disposition),
                ctypes.sizeof(disposition),
            ):
                return "evidence disposal failed"
            return None
        finally:
            os.close(fd)
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    except OSError:
        return "evidence artifact unavailable"
    try:
        if not _same_file_identity(os.fstat(fd), verified_stat):
            return "evidence artifact changed"
        if _digest_for_fd(fd) != expected_digest:
            return "evidence artifact changed"
        path.unlink()
    except FileNotFoundError:
        return "already absent"
    except OSError:
        return "evidence disposal failed"
    finally:
        os.close(fd)
    return None


def _digest_for_fd(fd: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while chunk := os.read(fd, 1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def release_authorized_evidence(
    decision: Mapping[str, Any],
    *,
    binding: Mapping[str, Any],
    canonical_consequence: Mapping[str, Any],
    required_consumers: Sequence[str],
    consumer_releases: Mapping[str, Mapping[str, Any]],
    retention: Mapping[str, Mapping[str, Any]],
    evidence_paths: Mapping[str, Path],
    retirement_proof: Mapping[str, Any] | None = None,
    recovery_required: bool = False,
    release_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result = authorize_evidence_release(
        decision,
        binding=binding,
        canonical_consequence=canonical_consequence,
        required_consumers=required_consumers,
        consumer_releases=consumer_releases,
        retention=retention,
        retirement_proof=retirement_proof,
        recovery_required=recovery_required,
    )
    if not result["authorized"]:
        return result
    evidence_ref = binding.get("evidence_ref")
    recorded_resources = release_record.get("resources") if isinstance(release_record, Mapping) else None
    recorded_resource = recorded_resources.get(evidence_ref) if isinstance(recorded_resources, Mapping) else None
    attempt_guard = release_record.get("attempt_guard") if isinstance(release_record, Mapping) else None
    if (
        not isinstance(release_record, Mapping)
        or release_record.get("authorized") is not True
        or release_record.get("binding") != dict(binding)
        or set(recorded_resources or ()) != {evidence_ref}
        or not isinstance(recorded_resource, Mapping)
        or recorded_resource.get("state") not in {"pending", "removed", "already_absent"}
        or not isinstance(attempt_guard, Mapping)
        or attempt_guard.get("release_authorized") is not True
        or attempt_guard.get("release_state") not in {"pending", "released"}
    ):
        return {
            **result,
            "authorized": False,
            "reasons": ["durable release authorization required"],
        }
    if recorded_resource.get("state") in {"removed", "already_absent"}:
        return {
            **result,
            "payload_released": True,
            "resources": {evidence_ref: dict(recorded_resource)},
        }
    path = evidence_paths.get(evidence_ref) if isinstance(evidence_ref, str) else None
    if not isinstance(path, Path):
        return {
            **result,
            "authorized": False,
            "reasons": ["binding_mismatch: exact evidence path unavailable"],
            "resources": {evidence_ref: {**dict(recorded_resource), "state": "unverified"}},
        }
    mismatch, verified_stat = _release_resource_check(
        recorded_resource,
        binding=binding,
        evidence_ref=evidence_ref,
        attempt_guard=attempt_guard,
        path=path,
    )
    if mismatch is not None:
        return {
            **result,
            "authorized": False,
            "reasons": [f"binding_mismatch: {mismatch}"],
            "resources": {
                evidence_ref: {**dict(recorded_resource), "state": "unverified", "reason": mismatch}
            },
        }
    if mismatch is not None:
        return {
            **result,
            "authorized": False,
            "reasons": [f"binding_mismatch: {mismatch}"],
            "resources": {
                evidence_ref: {**dict(recorded_resource), "state": "unverified", "reason": mismatch}
            },
        }
    if not path.exists():
        return {
            **result,
            "payload_released": True,
            "resources": {evidence_ref: {**dict(recorded_resource), "state": "already_absent"}},
        }
    if verified_stat is None:
        return {
            **result,
            "authorized": False,
            "reasons": ["binding_mismatch: evidence artifact identity unavailable"],
            "resources": {evidence_ref: {**dict(recorded_resource), "state": "unverified"}},
        }
    if not path.is_file() or path.is_symlink():
        if (
            isinstance(path, Path)
            and not path.is_symlink()
            and not path.exists()
            and recorded_resource.get("state") == "pending"
        ):
            return {
                **result,
                "payload_released": True,
                "resources": {evidence_ref: {"state": "already_absent"}},
            }
        return {
            **result,
            "authorized": False,
            "reasons": ["binding_mismatch: exact evidence path unavailable"],
            "resources": {evidence_ref: {**dict(recorded_resource), "state": "unverified"}},
        }
    resources: dict[str, dict[str, Any]] = {}
    expected_digest = recorded_resource.get("content_sha256") or recorded_resource.get("artifact_digest")
    unlink_error = _unlink_verified_file(path, verified_stat, str(expected_digest))
    if unlink_error == "already absent":
        resources[evidence_ref] = {"state": "already_absent"}
    elif unlink_error is None:
        resources[evidence_ref] = {"state": "removed"}
    else:
        resources[evidence_ref] = {
            "state": "unverified",
            "reason": "replacement_detected" if unlink_error == "evidence artifact changed" else unlink_error,
        }
    failed = [name for name, state in resources.items() if state["state"] == "unverified"]
    if failed:
        return {
            **result,
            "authorized": False,
            "reasons": [f"{resources[name].get('reason', 'evidence disposal failed')}: {name}" for name in failed],
            "resources": resources,
        }
    return {
        **result,
        "payload_released": True,
        "resources": resources,
    }


def authorize_dependent_transition(
    decision: Mapping[str, Any],
    *,
    completed_task_id: str,
    dependent_task: Mapping[str, Any],
    dependency_states: Mapping[str, str],
) -> dict[str, Any]:
    current_state = dependent_task.get("state")
    dependencies = dependent_task.get("dependencies")
    if not isinstance(dependencies, Sequence) or isinstance(dependencies, (str, bytes)):
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "dependent task dependencies unavailable",
        }
    if decision.get("decision") != "PASS":
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "acceptance did not pass",
        }
    controller = decision.get("controller")
    accepted_task = decision.get("task")
    task_transition = decision.get("task_transition")
    proof = decision.get("acceptance_proof")
    if not all(isinstance(value, Mapping) for value in (controller, accepted_task, task_transition, proof)):
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "acceptance decision incomplete",
        }
    if controller.get("authority") != ACCEPTANCE_AUTHORITY or _missing_text(controller, "identity", "controller identity") is not None:
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "acceptance decision incomplete",
        }
    accepted_task_id = accepted_task.get("task_id") if isinstance(accepted_task, Mapping) else None
    if accepted_task_id != completed_task_id:
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "accepted task does not match completed task",
        }
    accepted_plan_identity = accepted_task.get("plan_identity") if isinstance(accepted_task, Mapping) else None
    dependent_plan_identity = dependent_task.get("plan_identity")
    if (
        not isinstance(accepted_plan_identity, str)
        or not accepted_plan_identity.strip()
        or not isinstance(dependent_plan_identity, str)
        or not dependent_plan_identity.strip()
        or accepted_plan_identity != dependent_plan_identity
    ):
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "accepted and dependent task plan binding mismatch",
        }
    if (
        task_transition.get("authorized") is not True
        or task_transition.get("current_state") != ELIGIBLE_TASK_STATE
        or task_transition.get("next_state") != "completed"
        or proof.get("task_id") != accepted_task_id
        or proof.get("plan_identity") != accepted_plan_identity
        or proof.get("task_state") != ELIGIBLE_TASK_STATE
    ):
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "acceptance decision incomplete",
        }
    required_conditions = proof.get("required_conditions")
    artifact_conditions = proof.get("artifact_conditions")
    freshness = proof.get("freshness")
    settlement = proof.get("settlement")
    if (
        not isinstance(required_conditions, Mapping)
        or not required_conditions
        or not isinstance(artifact_conditions, Mapping)
        or set(artifact_conditions) != set(required_conditions)
        or any(value is not True for value in artifact_conditions.values())
        or not isinstance(freshness, Mapping)
        or freshness.get("head_matches") is not True
        or freshness.get("write_scope_matches") is not True
        or not isinstance(settlement, Mapping)
        or settlement.get("settlement_proven") is not True
        or settlement.get("resource_settled") is not True
    ):
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "acceptance decision incomplete",
        }
    if completed_task_id not in dependencies:
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "accepted task is not a dependency",
        }
    if any(dependency_states.get(str(task_id)) != "completed" for task_id in dependencies):
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "dependent prerequisites incomplete",
        }
    if current_state != "pending":
        return {
            "authorized": False,
            "current_state": current_state,
            "next_state": current_state,
            "reason": "dependent task is not pending",
        }
    return {
        "authorized": True,
        "task_id": dependent_task.get("task_id"),
        "plan_identity": dependent_task.get("plan_identity"),
        "current_state": current_state,
        "next_state": "active",
        "reason": "accepted dependency permits advancement",
    }


__all__ = [
    "ACCEPTANCE_AUTHORITY",
    "ACCEPTANCE_DECISIONS",
    "authorize_evidence_release",
    "release_authorized_evidence",
    "authorize_dependent_transition",
    "evaluate_acceptance",
]
