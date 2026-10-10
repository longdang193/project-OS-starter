"""Pure reconciliation of current Plan, Git, GitHub, and runtime evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Mapping


REMOTE_EVIDENCE_UNAVAILABLE = "REMOTE_EVIDENCE_UNAVAILABLE"


@dataclass(frozen=True)
class LocalEvidence:
    repository_identity: str | None = None
    plan_ref: str | None = None
    plan_revision: str | None = None
    task_id: str | None = None
    task_state: str | None = None
    checkpoint_sha: str | None = None
    lane_head_sha: str | None = None
    dirty: bool = False
    working_tree_digest: str | None = None
    dependencies_ready: bool | None = None
    source_ref: str | None = None


@dataclass(frozen=True)
class RemotePrEvidence:
    available: bool = False
    pr_ref: str | None = None
    head_sha: str | None = None
    checks_passed: bool | None = None
    review_valid: bool | None = None
    mergeable: bool | None = None
    source_ref: str | None = None


@dataclass(frozen=True)
class RuntimeEvidence:
    attempt_id: str | None = None
    worker_terminal: bool | None = None
    task_result_published: bool | None = None
    acceptance_proven: bool | None = None
    settlement_proven: bool | None = None
    runtime_owner: str | None = None
    retirement_state: str | None = None
    source_ref: str | None = None


@dataclass(frozen=True)
class Contradiction:
    code: str
    detail: str


@dataclass(frozen=True)
class MissingEvidence:
    field: str
    reason: str


@dataclass(frozen=True)
class Eligibility:
    execution: bool
    verification: bool
    acceptance: bool
    integration: bool
    retirement: bool


@dataclass(frozen=True)
class EvidenceSnapshot:
    plan_ref: str | None
    task_id: str | None
    checkpoint_sha: str | None
    lane_head_sha: str | None
    attempt_id: str | None
    phase: str
    next_action: str
    eligible: Eligibility
    contradictions: tuple[Contradiction, ...]
    missing_evidence: tuple[MissingEvidence, ...]
    remote_status: str
    sources: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["eligible"] = asdict(self.eligible)
        value["contradictions"] = [asdict(item) for item in self.contradictions]
        value["missing_evidence"] = [asdict(item) for item in self.missing_evidence]
        value["sources"] = dict(self.sources)
        return value


def _coerce(value: object, cls: type[Any]) -> Any:
    if isinstance(value, cls):
        return value
    if not isinstance(value, Mapping):
        raise TypeError(f"expected {cls.__name__} or mapping")
    allowed = {item.name for item in fields(cls)}
    return cls(**{key: item for key, item in value.items() if key in allowed})


def reconcile(
    local: LocalEvidence | Mapping[str, Any],
    remote: RemotePrEvidence | Mapping[str, Any],
    runtime: RuntimeEvidence | Mapping[str, Any],
) -> EvidenceSnapshot:
    """Derive current eligibility without storing or trusting copied status."""

    local = _coerce(local, LocalEvidence)
    remote = _coerce(remote, RemotePrEvidence)
    runtime = _coerce(runtime, RuntimeEvidence)
    contradictions: list[Contradiction] = []
    missing: list[MissingEvidence] = []

    for name, value in (
        ("plan_ref", local.plan_ref),
        ("task_id", local.task_id),
        ("checkpoint_sha", local.checkpoint_sha),
        ("lane_head_sha", local.lane_head_sha),
        ("attempt_id", runtime.attempt_id),
    ):
        if not isinstance(value, str) or not value.strip():
            missing.append(MissingEvidence(name, "stable action reference is absent"))

    if local.dirty and not local.working_tree_digest:
        missing.append(MissingEvidence("working_tree_digest", "dirty candidate has no binding"))
    if remote.available and remote.head_sha != local.lane_head_sha:
        contradictions.append(Contradiction("PR_HEAD_MISMATCH", "remote PR head differs from local lane head"))
    if local.checkpoint_sha and local.lane_head_sha and local.checkpoint_sha != local.lane_head_sha:
        contradictions.append(Contradiction("CHECKPOINT_HEAD_MISMATCH", "checkpoint differs from local lane head"))
    if local.dependencies_ready is not True:
        missing.append(MissingEvidence("dependencies_ready", "task dependencies are not proven ready"))
    if not remote.available:
        remote_status = REMOTE_EVIDENCE_UNAVAILABLE
    else:
        remote_status = "CURRENT"
        if remote.checks_passed is None:
            missing.append(MissingEvidence("checks_passed", "remote checks were not observed"))
        if remote.review_valid is None:
            missing.append(MissingEvidence("review_valid", "remote review was not observed"))
        if remote.mergeable is None:
            missing.append(MissingEvidence("mergeable", "remote mergeability was not observed"))

    if local.task_state in {"completed", "accepted"}:
        phase = "Acceptance" if runtime.task_result_published else "Verification"
    elif runtime.worker_terminal:
        phase = "Verification"
    else:
        phase = "Execution"

    identity_ok = not contradictions and not missing
    execution = identity_ok and local.task_state in {"pending", "active"}
    verification = identity_ok and runtime.worker_terminal is True and runtime.task_result_published is True
    acceptance = (
        verification
        and runtime.acceptance_proven is True
        and local.checkpoint_sha is not None
    )
    integration = acceptance and remote_status == "CURRENT" and remote.checks_passed is True and remote.review_valid is True and remote.mergeable is True
    retirement = runtime.settlement_proven is True and runtime.retirement_state in {"removed", "preserved"}
    if remote_status == REMOTE_EVIDENCE_UNAVAILABLE:
        integration = False
        if "remote evidence unavailable" not in {item.reason for item in missing}:
            missing.append(MissingEvidence("remote", "remote evidence unavailable"))

    if contradictions or missing:
        next_action = REMOTE_EVIDENCE_UNAVAILABLE if remote_status == REMOTE_EVIDENCE_UNAVAILABLE else "RECONCILE"
    elif retirement and not acceptance:
        next_action = "ACCEPT"
    elif retirement:
        next_action = "NO_ACTION"
    elif integration:
        next_action = "RETIRE_RUNTIME"
    elif acceptance:
        next_action = "INTEGRATE"
    elif verification:
        next_action = "ACCEPT"
    else:
        next_action = "EXECUTE"

    return EvidenceSnapshot(
        plan_ref=local.plan_ref,
        task_id=local.task_id,
        checkpoint_sha=local.checkpoint_sha,
        lane_head_sha=local.lane_head_sha,
        attempt_id=runtime.attempt_id,
        phase=phase,
        next_action=next_action,
        eligible=Eligibility(execution, verification, acceptance, integration, retirement),
        contradictions=tuple(contradictions),
        missing_evidence=tuple(missing),
        remote_status=remote_status,
        sources=tuple(
            item
            for item in (
                ("local", local.source_ref),
                ("remote", remote.source_ref),
                ("runtime", runtime.source_ref),
            )
            if isinstance(item[1], str) and item[1]
        ),
    )


__all__ = [
    "REMOTE_EVIDENCE_UNAVAILABLE",
    "LocalEvidence",
    "RemotePrEvidence",
    "RuntimeEvidence",
    "Contradiction",
    "MissingEvidence",
    "Eligibility",
    "EvidenceSnapshot",
    "reconcile",
]
