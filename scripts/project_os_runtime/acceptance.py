"""Native CoS acceptance decisions over existing plan and runtime evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


ACCEPTANCE_DECISIONS = frozenset({"PASS", "FAIL", "BLOCKED"})
ACCEPTANCE_AUTHORITY = "cos"


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
    if controller.get("task_id") != task.get("task_id"):
        reasons.append("controller and task identity mismatch")
    if not artifact_conditions:
        reasons.append("artifact conditions")
    elif any(not isinstance(value, bool) for value in artifact_conditions.values()):
        reasons.append("artifact condition type")

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
    current_state = task.get("state")
    task_transition = {
        "authorized": decision == "PASS",
        "current_state": current_state,
        "next_state": "completed" if decision == "PASS" else current_state,
    }
    return {
        "decision": decision,
        "reasons": reasons or ["acceptance criteria satisfied"],
        "controller": {
            "identity": controller.get("identity"),
            "authority": controller.get("authority"),
        },
        "task": {
            "task_id": task.get("task_id"),
            "plan_identity": task.get("plan_identity"),
        },
        "task_transition": task_transition,
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
        "current_state": current_state,
        "next_state": "active",
        "reason": "accepted dependency permits advancement",
    }


__all__ = [
    "ACCEPTANCE_AUTHORITY",
    "ACCEPTANCE_DECISIONS",
    "authorize_dependent_transition",
    "evaluate_acceptance",
]
