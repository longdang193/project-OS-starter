"""Native CoS acceptance decisions over existing plan and runtime evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
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
        for field in RELEASE_BINDING_FIELDS[:-1]:
            if canonical_consequence.get(field) != binding.get(field):
                reasons.append(f"canonical {field} binding")
    if recovery_required:
        reasons.append("recovery required")
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


def release_authorized_evidence(
    decision: Mapping[str, Any],
    *,
    binding: Mapping[str, Any],
    canonical_consequence: Mapping[str, Any],
    required_consumers: Sequence[str],
    consumer_releases: Mapping[str, Mapping[str, Any]],
    retention: Mapping[str, Mapping[str, Any]],
    evidence_paths: Mapping[str, Path],
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
        recovery_required=recovery_required,
    )
    if not result["authorized"]:
        return result
    evidence_ref = binding.get("evidence_ref")
    path = evidence_paths.get(evidence_ref) if isinstance(evidence_ref, str) else None
    if not isinstance(path, Path) or not path.is_file() or path.is_symlink():
        recorded_resources = release_record.get("resources") if isinstance(release_record, Mapping) else None
        recorded_resource = recorded_resources.get(evidence_ref) if isinstance(recorded_resources, Mapping) else None
        if (
            isinstance(release_record, Mapping)
            and release_record.get("authorized") is True
            and release_record.get("binding") == dict(binding)
            and set(recorded_resources or ()) == {evidence_ref}
            and isinstance(recorded_resource, Mapping)
            and recorded_resource.get("state") in {"removed", "already_absent"}
        ):
            return {
                **result,
                "payload_released": True,
                "resources": {evidence_ref: dict(recorded_resource)},
            }
        if isinstance(release_record, Mapping) and release_record.get("authorized") is True:
            return {
                **result,
                "authorized": False,
                "reasons": ["durable release record incomplete"],
            }
        return {
            **result,
            "authorized": False,
            "reasons": ["exact evidence path unavailable"],
        }
    resources: dict[str, dict[str, Any]] = {}
    try:
        path.unlink()
    except FileNotFoundError:
        resources[evidence_ref] = {"state": "already_absent"}
    except OSError as exc:
        resources[evidence_ref] = {"state": "unverified", "detail": str(exc)}
    else:
        resources[evidence_ref] = {"state": "removed"}
    failed = [name for name, state in resources.items() if state["state"] == "unverified"]
    if failed:
        return {
            **result,
            "authorized": False,
            "reasons": [f"evidence disposal failed: {name}" for name in failed],
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
