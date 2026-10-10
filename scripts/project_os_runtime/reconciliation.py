"""Pure phase reconciliation over owner-supplied facts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


PHASES = frozenset({"dispatch", "verify", "accept", "integrate", "retire", "prune"})
_SUCCESSFUL_CHECKS = frozenset({"success", "neutral", "skipped"})


@dataclass(frozen=True, slots=True)
class RemotePrEvidence:
    repository_identity: str | None = None
    pr_ref: str | None = None
    pr_number: int | None = None
    base_ref: str | None = None
    base_sha: str | None = None
    head_sha: str | None = None
    required_checks: tuple[str, ...] = ()
    checks: tuple[Mapping[str, Any], ...] = ()
    policy_source: str | None = None
    review_policy_source: str | None = None
    review_policy_satisfied: bool | None = None
    effective_review_state: str | None = None
    review_required: bool | None = None
    review_identity: str | None = None
    review_pr_number: int | None = None
    reviewed_head_sha: str | None = None
    mergeability: str | None = None
    merged: bool = False
    source_ref: str | None = None
    available: bool = False

    @property
    def checks_current(self) -> bool:
        return bool(self.checks) and all(
            check.get("head_sha") == self.head_sha
            and check.get("conclusion") in _SUCCESSFUL_CHECKS
            for check in self.checks
        )

    @property
    def successful_check_names(self) -> frozenset[str]:
        return frozenset(
            str(check.get("name") or check.get("context"))
            for check in self.checks
            if (
                check.get("head_sha") == self.head_sha
                and check.get("conclusion") in _SUCCESSFUL_CHECKS
                and (check.get("name") is not None or check.get("context") is not None)
            )
        )

    @property
    def checks_satisfy_policy(self) -> bool:
        policy_source = self.policy_source or self.review_policy_source
        policy_bound = isinstance(policy_source, str) and policy_source.startswith(("github://", "repo-contract://"))
        return policy_bound and self.checks_current and set(self.required_checks) <= set(self.successful_check_names)

    @property
    def review_policy_is_satisfied(self) -> bool:
        policy_source = self.review_policy_source or self.policy_source
        if not isinstance(policy_source, str) or not policy_source.strip():
            return False
        if self.review_policy_satisfied is not True:
            return False
        if self.review_required is False:
            return self.effective_review_state == "NONE"
        return self.review_required is True and self.effective_review_state == "APPROVED"

    @property
    def review_is_valid(self) -> bool:
        if self.review_required is False:
            return self.review_policy_is_satisfied
        return bool(
            self.review_identity
            and self.review_pr_number == self.pr_number
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
        }


def _required_true(facts: Mapping[str, Any], name: str, missing: list[str], failures: list[str]) -> None:
    value = facts.get(name)
    if value is None:
        missing.append(name)
    elif value is not True:
        failures.append(name)


def _result(phase: str, facts: Mapping[str, Any], required: Sequence[str], *, complete: bool = False) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    for name in required:
        _required_true(facts, name, missing, failures)
    eligible = not missing and not failures
    return ReconciliationResult(
        phase,
        eligible,
        eligible and complete,
        tuple(missing),
        tuple(failures),
    )


def _dispatch(facts: Mapping[str, Any]) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    for name in ("plan_valid", "dependencies_ready", "workspace_valid"):
        _required_true(facts, name, missing, failures)
    if facts.get("active_attempt_conflict") is True:
        failures.append("active_attempt_conflict")
    eligible = not missing and not failures
    return ReconciliationResult("dispatch", eligible, False, tuple(missing), tuple(failures))


def _verify(facts: Mapping[str, Any]) -> ReconciliationResult:
    result = _result("verify", facts, ("attempt_exists", "candidate_attributable", "worker_terminal", "task_result_published"), complete=facts.get("verification_complete") is True)
    return result


def _accept(facts: Mapping[str, Any]) -> ReconciliationResult:
    result = _result("accept", facts, ("verification_current", "candidate_unchanged", "acceptance_criteria_evaluable"), complete=facts.get("cos_pass") is True)
    return result


def _integrate(facts: Mapping[str, Any], remote: RemotePrEvidence | None) -> ReconciliationResult:
    missing: list[str] = []
    failures: list[str] = []
    _required_true(facts, "cos_pass", missing, failures)
    if remote is None:
        missing.append("remote_pr_evidence")
    elif not remote.available:
        failures.append("remote_unavailable")
    else:
        expected = {
            "repository_identity": facts.get("repository_identity"),
            "pr_number": facts.get("pr_number"),
            "base_ref": facts.get("base_ref"),
            "base_sha": facts.get("base_sha"),
            "candidate_sha": facts.get("candidate_sha"),
        }
        for name, value in expected.items():
            if value is None:
                missing.append(name)
        for name, value in expected.items():
            remote_name = "head_sha" if name == "candidate_sha" else name
            if value is not None and getattr(remote, remote_name) != value:
                failures.append(remote_name)
        if not remote.checks_satisfy_policy:
            failures.append("required_checks")
        if not remote.review_policy_is_satisfied:
            failures.append("review_policy")
        if not remote.review_is_valid:
            failures.append("review_bound_to_head")
        if remote.mergeability not in {"mergeable", "clean"}:
            failures.append("mergeability")
        if not isinstance(remote.source_ref, str) or not remote.source_ref.strip():
            failures.append("remote_source_ref")
    eligible = not missing and not failures
    return ReconciliationResult("integrate", eligible, eligible and remote is not None and remote.merged, tuple(missing), tuple(failures))


def _retire(facts: Mapping[str, Any]) -> ReconciliationResult:
    result = _result("retire", facts, ("runtime_owned", "no_continuation", "settled"), complete=facts.get("retirement_complete") is True)
    if facts.get("recovery_required") is True:
        return ReconciliationResult(result.phase, False, False, result.missing, (*result.contradictions, "recovery_required"))
    return result


def _prune(facts: Mapping[str, Any]) -> ReconciliationResult:
    result = _result("prune", facts, ("canonical_consequence", "consumer_release", "retention_expired", "retirement_complete"), complete=facts.get("evidence_released") is True)
    if facts.get("recovery_required") is True:
        return ReconciliationResult(result.phase, False, False, result.missing, (*result.contradictions, "recovery_required"))
    return result


def reconcile(reconciliation_input: ReconciliationInput) -> ReconciliationResult:
    """Evaluate one lifecycle phase from immutable owner-supplied facts."""
    if not isinstance(reconciliation_input, ReconciliationInput):
        raise TypeError("reconcile requires ReconciliationInput")
    if reconciliation_input.phase not in PHASES:
        raise ValueError(f"unsupported reconciliation phase: {reconciliation_input.phase}")
    facts = reconciliation_input.facts if isinstance(reconciliation_input.facts, Mapping) else {}
    handlers = {
        "dispatch": lambda: _dispatch(facts),
        "verify": lambda: _verify(facts),
        "accept": lambda: _accept(facts),
        "integrate": lambda: _integrate(facts, reconciliation_input.remote),
        "retire": lambda: _retire(facts),
        "prune": lambda: _prune(facts),
    }
    return handlers[reconciliation_input.phase]()


__all__ = ["PHASES", "RemotePrEvidence", "ReconciliationInput", "ReconciliationResult", "reconcile"]
