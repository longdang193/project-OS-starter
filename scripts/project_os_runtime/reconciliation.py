"""Pure phase-specific reconciliation over owner-supplied facts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


PHASES = frozenset({"dispatch", "verify", "accept", "integrate", "retire", "prune"})


@dataclass(frozen=True, slots=True)
class RemotePrEvidence:
    repository_identity: str
    pr_number: int
    base_ref: str
    base_sha: str
    head_sha: str
    checks: tuple[Mapping[str, Any], ...] = ()
    review_identity: str | None = None
    reviewed_head_sha: str | None = None
    mergeability: str | None = None
    merged: bool = False
    source_ref: str | None = None

    @property
    def checks_current(self) -> bool:
        return bool(self.checks) and all(
            check.get("head_sha") == self.head_sha
            and check.get("conclusion") in {"success", "neutral", "skipped"}
            for check in self.checks
        )

    @property
    def review_valid(self) -> bool:
        return bool(
            self.review_identity
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
        if not remote.review_valid:
            failures.append("review_bound_to_head")
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


def reconcile(input: ReconciliationInput | None = None, *, phase: str | None = None, facts: Mapping[str, Any] | None = None, remote: RemotePrEvidence | None = None) -> ReconciliationResult:
    """Recompute one lifecycle phase from owner facts without side effects."""
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


__all__ = [
    "PHASES",
    "RemotePrEvidence",
    "ReconciliationInput",
    "ReconciliationResult",
    "reconcile",
]
