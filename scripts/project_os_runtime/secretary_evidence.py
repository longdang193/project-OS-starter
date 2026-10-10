from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, Mapping


CURRENT = "CURRENT"
MISSING = "MISSING"
STALE = "STALE"
EvidenceStatus = Literal["CURRENT", "MISSING", "STALE"]


@dataclass(frozen=True)
class EvidenceSnapshot:
    status: EvidenceStatus
    repository_identity: str | None
    workstream: str | None
    plan_identity: str | None
    plan_revision: str | None
    git_revision: str | None
    task_id: str | None
    task_state: str | None
    accepted_prerequisite_refs: tuple[str, ...]
    worker_result_ref: str | None
    settlement_receipt_ref: str | None
    acceptance_proof_ref: str | None
    project_consequence: str | None
    next_action: str | None
    reasons: tuple[str, ...]
    sources: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["accepted_prerequisite_refs"] = list(self.accepted_prerequisite_refs)
        value["reasons"] = list(self.reasons)
        value["sources"] = dict(self.sources)
        return value


def build_evidence_snapshot(
    *,
    plan: Mapping[str, Any],
    git: Mapping[str, Any],
    worker: Mapping[str, Any],
    settlement: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> EvidenceSnapshot:
    values = {
        "repository_identity": plan.get("repository_identity"),
        "workstream": plan.get("workstream"),
        "plan_identity": plan.get("plan_identity"),
        "plan_revision": plan.get("plan_revision"),
        "git_revision": git.get("git_revision"),
        "task_id": worker.get("task_id"),
        "task_state": plan.get("task_state"),
        "attempt_id": worker.get("attempt_id") or settlement.get("attempt_id"),
        "checkpoint": plan.get("checkpoint"),
        "worker_result_ref": worker.get("result_ref"),
        "settlement_receipt_ref": settlement.get("receipt_ref"),
        "acceptance_proof_ref": acceptance.get("proof_ref"),
        "project_consequence": next_action.get("project_consequence"),
        "next_action": next_action.get("action"),
    }
    reasons: list[str] = []
    source_fields = {
        "plan": plan.get("source_ref"),
        "git": git.get("source_ref"),
        "worker": worker.get("result_ref"),
        "settlement": settlement.get("receipt_ref"),
        "acceptance": acceptance.get("proof_ref"),
        "policy": next_action.get("policy_ref"),
    }
    for name, value in values.items():
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"missing {name}")
    for name, value in source_fields.items():
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"missing {name} source")

    if git.get("repository_identity") != plan.get("repository_identity"):
        reasons.append("repository identity mismatch")
    if git.get("plan_identity") != plan.get("plan_identity"):
        reasons.append("Plan identity mismatch")
    if git.get("plan_revision") != plan.get("plan_revision"):
        reasons.append("Plan revision mismatch")
    if not isinstance(plan.get("git_revision"), str) or not plan.get("git_revision"):
        reasons.append("missing plan git revision")
    elif git.get("git_revision") != plan.get("git_revision"):
        reasons.append("Git revision mismatch")
    if worker.get("repository_identity") != plan.get("repository_identity"):
        reasons.append("Worker repository binding mismatch")
    if worker.get("plan_identity") != plan.get("plan_identity"):
        reasons.append("Worker Plan binding mismatch")
    if worker.get("plan_revision") != plan.get("plan_revision"):
        reasons.append("Worker Plan revision mismatch")
    if worker.get("task_id") != plan.get("task_id"):
        reasons.append("Worker task binding mismatch")
    authoritative_attempt_id = worker.get("attempt_id") or settlement.get("attempt_id")
    for source_name, source in (("worker", worker), ("settlement", settlement), ("acceptance", acceptance)):
        for field in (
            "repository_identity",
            "workstream",
            "plan_identity",
            "plan_revision",
            "git_revision",
            "task_id",
            "attempt_id",
            "checkpoint",
        ):
            expected = authoritative_attempt_id if field == "attempt_id" else plan.get(field)
            if source.get(field) != expected:
                reasons.append(f"{source_name} {field} binding mismatch")
    if worker.get("publication_valid") is not True:
        reasons.append("Worker publication unavailable")
    if settlement.get("settled") is not True or settlement.get("settlement_proven") is not True or settlement.get("resource_settled") is not True:
        reasons.append("settlement unavailable")
    if acceptance.get("decision") != "PASS":
        reasons.append("acceptance unavailable")
    if acceptance.get("task_id") != plan.get("task_id"):
        reasons.append("acceptance task binding mismatch")
    if acceptance.get("plan_identity") != plan.get("plan_identity"):
        reasons.append("acceptance Plan binding mismatch")
    if next_action.get("authorized") is not True:
        reasons.append("next action is not authorized")

    unique_reasons = tuple(dict.fromkeys(reasons))
    status = CURRENT
    if unique_reasons:
        missing_evidence = any(
            reason.startswith("missing ") or reason.endswith("unavailable")
            for reason in unique_reasons
        )
        stale_markers = (
            "mismatch",
            "revision",
            "stale",
        )
        status = (
            MISSING
            if missing_evidence
            else STALE
            if any(any(marker in reason for marker in stale_markers) for reason in unique_reasons)
            else MISSING
        )
    return EvidenceSnapshot(
        status=status,
        repository_identity=values["repository_identity"] if isinstance(values["repository_identity"], str) else None,
        workstream=values["workstream"] if isinstance(values["workstream"], str) else None,
        plan_identity=values["plan_identity"] if isinstance(values["plan_identity"], str) else None,
        plan_revision=values["plan_revision"] if isinstance(values["plan_revision"], str) else None,
        git_revision=values["git_revision"] if isinstance(values["git_revision"], str) else None,
        task_id=values["task_id"] if isinstance(values["task_id"], str) else None,
        task_state=values["task_state"] if isinstance(values["task_state"], str) else None,
        accepted_prerequisite_refs=tuple(sorted(str(item) for item in plan.get("accepted_prerequisites", ()) if str(item).strip())),
        worker_result_ref=values["worker_result_ref"] if isinstance(values["worker_result_ref"], str) else None,
        settlement_receipt_ref=values["settlement_receipt_ref"] if isinstance(values["settlement_receipt_ref"], str) else None,
        acceptance_proof_ref=values["acceptance_proof_ref"] if isinstance(values["acceptance_proof_ref"], str) else None,
        project_consequence=values["project_consequence"] if isinstance(values["project_consequence"], str) else None,
        next_action=values["next_action"] if isinstance(values["next_action"], str) else None,
        reasons=unique_reasons,
        sources=tuple(sorted((name, value) for name, value in source_fields.items() if isinstance(value, str) and value.strip())),
    )


__all__ = ["CURRENT", "MISSING", "STALE", "EvidenceSnapshot", "build_evidence_snapshot"]
