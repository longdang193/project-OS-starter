"""Controller-owned handoff from observed evidence to CoS acceptance."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
from typing import Any

from .acceptance import (
    ACCEPTANCE_AUTHORITY,
    authorize_dependent_transition,
    evaluate_acceptance,
    validate_acceptance_decision,
)
from .plan_preparation import apply_accepted_plan_transitions, load_plan


def inspect_artifact(
    path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Inspect a controller-visible artifact without trusting worker claims."""

    artifact_path = Path(path)
    observation: dict[str, Any] = {
        "path": str(artifact_path),
        "exists": artifact_path.is_file(),
        "expected_sha256": expected_sha256,
    }
    if not artifact_path.is_file():
        observation.update({"sha256": None, "matches": False})
        return observation
    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    observation.update({
        "sha256": digest,
        "matches": expected_sha256 is None or digest == expected_sha256,
    })
    return observation


def _write_record(path: str | Path, record: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)


def _read_record(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("acceptance handoff record must be an object")
    return value


def _artifact_observations(
    artifact_specs: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, bool]]:
    observations: dict[str, Any] = {}
    conditions: dict[str, bool] = {}
    for condition_id, specification in artifact_specs.items():
        if not isinstance(condition_id, str) or not condition_id.strip():
            raise ValueError("artifact condition id must be non-empty")
        if not isinstance(specification, Mapping):
            raise ValueError(f"artifact specification is not an object: {condition_id}")
        path = specification.get("path")
        if not isinstance(path, (str, Path)) or not str(path).strip():
            raise ValueError(f"artifact path is missing: {condition_id}")
        expected_sha256 = specification.get("expected_sha256")
        if expected_sha256 is not None and (
            not isinstance(expected_sha256, str) or len(expected_sha256) != 64
        ):
            raise ValueError(f"artifact expected_sha256 is invalid: {condition_id}")
        observation = inspect_artifact(path, expected_sha256=expected_sha256)
        observations[condition_id] = observation
        conditions[condition_id] = observation["matches"] is True
    return observations, conditions


def _binding_value(binding: Mapping[str, Any], field: str) -> str:
    value = binding.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"acceptance binding is missing {field}")
    return value


def _build_git_proof(
    binding: Mapping[str, Any],
    plan_identity: str,
    git_proof: Mapping[str, Any] | None,
) -> dict[str, Any]:
    candidate_sha = _binding_value(binding, "candidate_sha")
    checkpoint_sha = _binding_value(binding, "acceptance_checkpoint_sha")
    result = {
        "repository_identity": _binding_value(binding, "repository_identity"),
        "plan_identity": plan_identity,
        "lane_head_sha": candidate_sha,
        "checkpoint_sha": checkpoint_sha,
        "acceptance_checkpoint_sha": checkpoint_sha,
        "assignment_id": _binding_value(binding, "assignment_id"),
        "attempt_id": _binding_value(binding, "attempt_id"),
        "head_matches": None,
        "write_scope_matches": None,
    }
    if git_proof is not None:
        result.update(dict(git_proof))
    return result


def _record(
    *,
    source: str | Path,
    binding: Mapping[str, Any],
    decision: Mapping[str, Any],
    artifact_observations: Mapping[str, Any],
    transitions: Sequence[Mapping[str, str]],
    dependent_transition: Mapping[str, Any] | None,
    evidence_release: Mapping[str, Any] | None,
    result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "schema": "cos-acceptance-handoff/v1",
        "source": str(source),
        "binding": dict(binding),
        "decision": dict(decision),
        "artifact_observations": dict(artifact_observations),
        "transitions": [dict(item) for item in transitions],
        "dependent_transition": dict(dependent_transition) if dependent_transition is not None else None,
        "evidence_release": dict(evidence_release) if evidence_release is not None else None,
    }
    if result is not None:
        record["result"] = dict(result)
    return record


def handoff_acceptance(
    source: str | Path,
    *,
    controller_identity: str,
    task_id: str,
    binding: Mapping[str, Any],
    required_conditions: Mapping[str, Any],
    evidence: Mapping[str, Any],
    artifact_specs: Mapping[str, Mapping[str, Any]],
    verification: Mapping[str, Any],
    git_proof: Mapping[str, Any] | None = None,
    dependent_task: Mapping[str, Any] | None = None,
    dependency_states: Mapping[str, str] | None = None,
    evidence_release: Mapping[str, Any] | None = None,
    record_path: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate and, only on validated PASS, apply the existing Plan consequence."""

    graph = load_plan(source)
    task = graph.tasks.get(task_id)
    if task is None:
        raise ValueError(f"acceptance task is not in the Plan: {task_id}")
    attempt_id = _binding_value(binding, "attempt_id")
    normalized_binding = {
        **dict(binding),
        "attempt_id": attempt_id,
        "plan_identity": graph.plan_identity,
        "task_id": task_id,
    }
    normalized_git = _build_git_proof(binding, graph.plan_identity, git_proof)
    artifact_observations, artifact_conditions = _artifact_observations(artifact_specs)
    decision = evaluate_acceptance(
        controller={
            "identity": controller_identity,
            "authority": ACCEPTANCE_AUTHORITY,
            "plan_identity": graph.plan_identity,
            "task_id": task_id,
        },
        task={
            "task_id": task.task_id,
            "plan_identity": graph.plan_identity,
            "attempt_id": attempt_id,
            "required_proof": task.required_proof,
            "required_conditions": dict(required_conditions),
            "evidence": task.evidence,
            "state": task.state,
        },
        evidence=dict(evidence),
        artifact_conditions=artifact_conditions,
        git=normalized_git,
        verification=dict(verification),
        attempt_id=attempt_id,
    )
    validation_reasons = validate_acceptance_decision(
        decision,
        expected_task_id=task_id,
        expected_plan_identity=graph.plan_identity,
        expected_candidate_sha=_binding_value(binding, "candidate_sha"),
        expected_acceptance_checkpoint_sha=_binding_value(binding, "acceptance_checkpoint_sha"),
        expected_assignment_id=_binding_value(binding, "assignment_id"),
        expected_attempt_id=attempt_id,
    )
    dependent_transition = None
    transitions: list[Mapping[str, str]] = [
        {"task_id": task_id, "expected_state": "active", "next_state": "completed"},
    ]
    if decision.get("decision") == "PASS" and not validation_reasons and dependent_task is not None:
        dependent_transition = authorize_dependent_transition(
            decision,
            completed_task_id=task_id,
            dependent_task=dependent_task,
            dependency_states=dependency_states or {},
        )
        if dependent_transition.get("authorized") is True:
            transitions.append({
                "task_id": str(dependent_transition["task_id"]),
                "expected_state": "pending",
                "next_state": "active",
            })
    record = _record(
        source=source,
        binding=normalized_binding,
        decision=decision,
        artifact_observations=artifact_observations,
        transitions=transitions,
        dependent_transition=dependent_transition,
        evidence_release=evidence_release,
    )
    if record_path is not None:
        _write_record(record_path, record)
    if decision.get("decision") != "PASS" or validation_reasons:
        return {
            "authorized": False,
            "decision": decision,
            "validation_reasons": list(validation_reasons),
            "artifact_observations": artifact_observations,
            "reason": "acceptance decision incomplete",
        }
    if dependent_task is not None and dependent_transition is not None and dependent_transition.get("authorized") is not True:
        return {
            "authorized": False,
            "decision": decision,
            "validation_reasons": list(dependent_transition.get("validation_reasons", [])),
            "artifact_observations": artifact_observations,
            "reason": dependent_transition.get("reason", "dependent transition rejected"),
        }
    result = apply_accepted_plan_transitions(
        source,
        decision,
        transitions,
        dependent_transition=dependent_transition,
        evidence_release=evidence_release,
        expected_revision=graph.plan_revision,
    )
    if record_path is not None:
        _write_record(
            record_path,
            _record(
                source=source,
                binding=normalized_binding,
                decision=decision,
                artifact_observations=artifact_observations,
                transitions=transitions,
                dependent_transition=dependent_transition,
                evidence_release=evidence_release,
                result=result,
            ),
        )
    return {
        "authorized": result.get("authorized") is True,
        "decision": decision,
        "validation_reasons": [],
        "artifact_observations": artifact_observations,
        "result": result,
    }


def replay_acceptance(source: str | Path, record_path: str | Path) -> dict[str, Any]:
    """Reapply a persisted PASS using current Plan revision and existing replay guards."""

    record = _read_record(record_path)
    decision = record.get("decision")
    binding = record.get("binding")
    transitions = record.get("transitions")
    if not isinstance(decision, Mapping) or not isinstance(binding, Mapping) or not isinstance(transitions, list):
        return {"authorized": False, "reason": "acceptance handoff record is incomplete"}
    if decision.get("decision") != "PASS":
        return {"authorized": False, "reason": "persisted acceptance did not pass"}
    graph = load_plan(source)
    validation_reasons = validate_acceptance_decision(
        decision,
        expected_task_id=str(binding.get("task_id")),
        expected_plan_identity=graph.plan_identity,
        expected_candidate_sha=binding.get("candidate_sha"),
        expected_acceptance_checkpoint_sha=binding.get("acceptance_checkpoint_sha"),
        expected_assignment_id=binding.get("assignment_id"),
        expected_attempt_id=binding.get("attempt_id"),
    )
    if validation_reasons:
        return {"authorized": False, "reason": "acceptance decision incomplete", "validation_reasons": list(validation_reasons)}
    result = apply_accepted_plan_transitions(
        source,
        decision,
        transitions,
        dependent_transition=record.get("dependent_transition"),
        evidence_release=record.get("evidence_release"),
        expected_revision=graph.plan_revision,
    )
    updated = {**record, "result": result}
    _write_record(record_path, updated)
    return result


__all__ = ["handoff_acceptance", "inspect_artifact", "replay_acceptance"]
