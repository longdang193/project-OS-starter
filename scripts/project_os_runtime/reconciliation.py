"""Pure phase-specific reconciliation over owner-supplied facts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from typing import Any


PHASES = frozenset({"dispatch", "verify", "accept", "integrate", "retire", "prune"})


@dataclass(frozen=True, slots=True)
class RemotePrEvidence:
    repository_identity: str | None = None
    pr_ref: str | None = None
    pr_number: int | None = None
    base_ref: str | None = None
    base_sha: str | None = None
    head_sha: str | None = None
    checks: tuple[Mapping[str, Any], ...] = ()
    review_identity: str | None = None
    review_pr_number: int | None = None
    reviewed_head_sha: str | None = None
    mergeability: str | None = None
    merged: bool = False
    source_ref: str | None = None
    available: bool = False
    checks_passed: bool | None = None
    review_valid: bool | None = None
    mergeable: bool | None = None

    @property
    def checks_current(self) -> bool:
        if self.checks:
            return bool(self.checks) and all(
                check.get("head_sha") == self.head_sha
                and check.get("conclusion") in {"success", "neutral", "skipped"}
                for check in self.checks
            )
        return self.checks_passed is True

    def review_is_valid(self) -> bool:
        if self.review_valid is not None:
            return self.review_valid
        return bool(
            self.review_identity
            and self.review_pr_number == self.pr_number
            and self.reviewed_head_sha
            and self.reviewed_head_sha == self.head_sha
        )


@dataclass(frozen=True, slots=True)
class ReconciliationInput:
    phase: str
    facts: Mapping[str, Any] = field(default_factory=dict)
    remote: RemotePrEvidence | None = None


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    phase: str
    eligible: bool
    complete: bool
    missing: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    next_action: str = "reconcile"

    @property
    def integration_eligible(self) -> bool:
        return self.phase == "integrate" and self.eligible

    @property
    def integration_complete(self) -> bool:
        return self.phase == "integrate" and self.complete

    @property
    def retirement_eligible(self) -> bool:
        return self.phase == "retire" and self.eligible

    @property
    def retirement_complete(self) -> bool:
        return self.phase == "retire" and self.complete

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "eligible": self.eligible,
            "complete": self.complete,
            "integration_eligible": self.integration_eligible,
            "integration_complete": self.integration_complete,
            "retirement_eligible": self.retirement_eligible,
            "retirement_complete": self.retirement_complete,
            "missing": list(self.missing),
            "contradictions": list(self.contradictions),
            "next_action": self.next_action,
        }


def _required_true(facts: Mapping[str, Any], name: str, missing: list[str], failures: list[str]) -> None:
    value = facts.get(name)
    if value is None:
        missing.append(name)
    elif value is not True:
        failures.append(name)


def _dispatch(facts: Mapping[str, Any]) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    for name in ("plan_valid", "dependencies_ready", "workspace_valid"):
        _required_true(facts, name, missing, failures)
    if facts.get("active_attempt_conflict") is True:
        failures.append("active_attempt_conflict")
    eligible = not missing and not failures
    return ReconciliationResult(
        "dispatch",
        eligible,
        False,
        tuple(missing),
        tuple(failures),
        "dispatch" if eligible else "reconcile dispatch prerequisites",
    )


def _verify(facts: Mapping[str, Any]) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    for name in ("attempt_exists", "candidate_attributable", "worker_terminal", "task_result_published"):
        _required_true(facts, name, missing, failures)
    eligible = not missing and not failures
    return ReconciliationResult(
        "verify",
        eligible,
        eligible and facts.get("verification_complete") is True,
        tuple(missing),
        tuple(failures),
        "accept" if eligible and facts.get("verification_complete") is True else "verify" if eligible else "reconcile verification",
    )


def _accept(facts: Mapping[str, Any]) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    for name in ("verification_current", "candidate_unchanged", "acceptance_criteria_evaluable"):
        _required_true(facts, name, missing, failures)
    eligible = not missing and not failures
    return ReconciliationResult(
        "accept",
        eligible,
        eligible and facts.get("cos_pass") is True,
        tuple(missing),
        tuple(failures),
        "integrate" if eligible and facts.get("cos_pass") is True else "accept" if eligible else "reconcile acceptance",
    )


def _integrate(facts: Mapping[str, Any], remote: RemotePrEvidence | None) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    _required_true(facts, "cos_pass", missing, failures)
    if remote is None:
        missing.append("remote_pr_evidence")
    else:
        expected_fields = {
            "repository_identity": facts.get("repository_identity"),
            "pr_number": facts.get("pr_number"),
            "base_ref": facts.get("base_ref"),
            "base_sha": facts.get("base_sha"),
            "candidate_sha": facts.get("candidate_sha"),
        }
        for name, value in expected_fields.items():
            if value is None:
                missing.append(name)
        expected_repository = expected_fields["repository_identity"]
        expected_pr = expected_fields["pr_number"]
        expected_base_ref = expected_fields["base_ref"]
        expected_base_sha = expected_fields["base_sha"]
        expected_head = expected_fields["candidate_sha"]
        if expected_repository is not None and remote.repository_identity != expected_repository:
            failures.append("repository_identity")
        if expected_pr is not None and remote.pr_number != expected_pr:
            failures.append("pr_number")
        if expected_base_ref is not None and remote.base_ref != expected_base_ref:
            failures.append("base_ref")
        if expected_base_sha is not None and remote.base_sha != expected_base_sha:
            failures.append("base_sha")
        if expected_head is not None and remote.head_sha != expected_head:
            failures.append("head_sha")
        if not remote.checks_current:
            failures.append("checks_bound_to_head")
        if not remote.review_is_valid():
            failures.append("review_bound_to_head")
        if not isinstance(remote.source_ref, str) or not remote.source_ref.strip():
            failures.append("remote_source_ref")
        if remote.mergeability not in {"mergeable", "clean"}:
            failures.append("mergeability")
    eligible = not missing and not failures
    complete = eligible and remote is not None and remote.merged is True
    return ReconciliationResult(
        "integrate",
        eligible,
        complete,
        tuple(missing),
        tuple(failures),
        "retire" if complete else "integrate" if eligible else "reconcile integration",
    )


def _retire(facts: Mapping[str, Any]) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    for name in ("runtime_owned", "no_continuation", "settled"):
        _required_true(facts, name, missing, failures)
    if facts.get("recovery_required") is True:
        failures.append("recovery_required")
    eligible = not missing and not failures
    return ReconciliationResult(
        "retire",
        eligible,
        eligible and facts.get("retirement_complete") is True,
        tuple(missing),
        tuple(failures),
        "prune" if eligible and facts.get("retirement_complete") is True else "retire" if eligible else "reconcile retirement",
    )


def _prune(facts: Mapping[str, Any]) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    for name in ("canonical_consequence", "consumer_release", "retention_expired"):
        _required_true(facts, name, missing, failures)
    if facts.get("recovery_required") is True:
        failures.append("recovery_required")
    eligible = not missing and not failures
    return ReconciliationResult(
        "prune",
        eligible,
        eligible and facts.get("evidence_released") is True,
        tuple(missing),
        tuple(failures),
        "prune" if eligible else "retain evidence",
    )


def _reconcile_legacy(*args: Any, input: ReconciliationInput | None = None, phase: str | None = None, facts: Mapping[str, Any] | None = None, remote: RemotePrEvidence | None = None) -> Any:
    """Recompute one lifecycle phase from owner facts without side effects."""
    if len(args) == 3 and input is None and phase is None and facts is None and remote is None:
        return _reconcile_snapshot(args[0], args[1], args[2])
    if args:
        raise TypeError("legacy reconciliation accepts either one input or three evidence inputs")
    if input is not None:
        if phase is not None or facts is not None or remote is not None:
            raise TypeError("reconcile accepts either input or keyword facts")
        phase = input.phase
        facts = input.facts
        remote = input.remote
    if phase not in PHASES:
        raise ValueError(f"unsupported reconciliation phase: {phase}")
    current_facts = facts if isinstance(facts, Mapping) else {}
    return {
        "dispatch": _dispatch,
        "verify": _verify,
        "accept": _accept,
        "integrate": lambda values: _integrate(values, remote),
        "retire": _retire,
        "prune": _prune,
    }[phase](current_facts)


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
        value = {
            "plan_ref": self.plan_ref,
            "task_id": self.task_id,
            "checkpoint_sha": self.checkpoint_sha,
            "lane_head_sha": self.lane_head_sha,
            "attempt_id": self.attempt_id,
            "phase": self.phase,
            "next_action": self.next_action,
            "eligible": {
                "execution": self.eligible.execution,
                "verification": self.eligible.verification,
                "acceptance": self.eligible.acceptance,
                "integration": self.eligible.integration,
                "retirement": self.eligible.retirement,
            },
            "contradictions": [{"code": item.code, "detail": item.detail} for item in self.contradictions],
            "missing_evidence": [{"field": item.field, "reason": item.reason} for item in self.missing_evidence],
            "remote_status": self.remote_status,
            "sources": dict(self.sources),
        }
        return value


def _coerce(value: object, cls: type[Any]) -> Any:
    if isinstance(value, cls):
        return value
    if not isinstance(value, Mapping):
        raise TypeError(f"expected {cls.__name__} or mapping")
    allowed = {item.name for item in fields(cls)}
    return cls(**{key: item for key, item in value.items() if key in allowed})


def _reconcile_snapshot(
    local: LocalEvidence | Mapping[str, Any],
    remote: RemotePrEvidence | Mapping[str, Any],
    runtime: RuntimeEvidence | Mapping[str, Any],
) -> EvidenceSnapshot:
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
    if local.task_state in {"completed", "accepted"} and runtime.task_result_published is not True:
        missing.append(MissingEvidence("task_result", "terminal worker has no published TaskResult"))
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
    acceptance = verification and runtime.acceptance_proven is True and runtime.settlement_proven is True and local.checkpoint_sha is not None
    integration = acceptance and remote_status == "CURRENT" and remote.checks_passed is True and remote.review_valid is True and remote.mergeable is True
    retirement = runtime.settlement_proven is True and runtime.retirement_state in {"removed", "preserved"}
    if remote_status == REMOTE_EVIDENCE_UNAVAILABLE:
        integration = False
        if "remote evidence unavailable" not in {item.reason for item in missing}:
            missing.append(MissingEvidence("remote", "remote evidence unavailable"))
    if contradictions or missing:
        next_action = REMOTE_EVIDENCE_UNAVAILABLE if remote_status == REMOTE_EVIDENCE_UNAVAILABLE else "RECONCILE"
    elif integration and retirement:
        next_action = "NO_ACTION"
    elif integration:
        next_action = "RETIRE_RUNTIME"
    elif acceptance:
        next_action = "INTEGRATE"
    elif verification:
        next_action = "ACCEPT"
    elif retirement:
        next_action = "NO_ACTION"
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
            item for item in (("local", local.source_ref), ("remote", remote.source_ref), ("runtime", runtime.source_ref))
            if isinstance(item[1], str) and item[1]
        ),
    )


def reconcile(*args: Any, input: ReconciliationInput | None = None, phase: str | None = None, facts: Mapping[str, Any] | None = None, remote: RemotePrEvidence | None = None, runtime: RuntimeEvidence | Mapping[str, Any] | None = None) -> Any:
    if len(args) == 3 and input is None and phase is None and facts is None:
        return _reconcile_snapshot(args[0], args[1], args[2])
    if input is not None:
        if phase is not None or facts is not None or remote is not None or runtime is not None:
            raise TypeError("reconcile accepts either input or keyword facts")
        return _reconcile_legacy(input)
    if phase is not None:
        return _reconcile_legacy(ReconciliationInput(phase=phase, facts=facts or {}, remote=remote))
    raise TypeError("reconcile requires either three evidence inputs or a lifecycle phase")


__all__ = [
    "REMOTE_EVIDENCE_UNAVAILABLE",
    "PHASES",
    "LocalEvidence",
    "RemotePrEvidence",
    "RuntimeEvidence",
    "ReconciliationInput",
    "ReconciliationResult",
    "Contradiction",
    "MissingEvidence",
    "Eligibility",
    "EvidenceSnapshot",
    "reconcile",
    "_reconcile_legacy",
]
