import pytest
from dataclasses import replace

from scripts.project_os_runtime.reconciliation import (
    ReconciliationInput,
    RemotePrEvidence,
    reconcile,
)


def _remote(*, head_sha="H", merged=False, reviewed_head_sha="H", checks=None):
    return RemotePrEvidence(
        available=True,
        repository_identity="org/repo",
        pr_number=7,
        base_ref="main",
        base_sha="B",
        head_sha=head_sha,
        required_checks=("Repository contracts", "Runtime contracts (ubuntu-latest)"),
        checks=checks or (
            {"name": "Repository contracts", "head_sha": head_sha, "conclusion": "success"},
            {"name": "Runtime contracts (ubuntu-latest)", "head_sha": head_sha, "conclusion": "success"},
        ),
        policy_source="github://ruleset/main",
        review_policy_source="github://ruleset/main",
        review_policy_satisfied=True,
        effective_review_state="APPROVED",
        review_required=True,
        review_identity="review-1",
        review_pr_number=7,
        reviewed_head_sha=reviewed_head_sha,
        mergeability="mergeable",
        merged=merged,
        source_ref="github://org/repo/pulls/7",
    )


def test_reconcile_requires_canonical_input() -> None:
    with pytest.raises(TypeError, match="ReconciliationInput"):
        reconcile({"phase": "dispatch"})  # type: ignore[arg-type]


def test_dispatch_does_not_require_github_or_attempt_id() -> None:
    result = reconcile(ReconciliationInput("dispatch", {
        "plan_valid": True,
        "dependencies_ready": True,
        "workspace_valid": True,
    }))
    assert result.eligible is True


def test_dispatch_blocks_unready_dependencies() -> None:
    result = reconcile(ReconciliationInput("dispatch", {
        "plan_valid": True,
        "dependencies_ready": False,
        "workspace_valid": True,
    }))
    assert result.eligible is False
    assert result.contradictions == ("dependencies_ready",)


def test_verify_requires_published_terminal_result() -> None:
    result = reconcile(ReconciliationInput("verify", {
        "attempt_exists": True,
        "candidate_attributable": True,
        "worker_terminal": True,
        "task_result_published": False,
    }))
    assert result.eligible is False


def test_accept_requires_current_candidate_and_cos_pass() -> None:
    result = reconcile(ReconciliationInput("accept", {
        "verification_current": True,
        "candidate_unchanged": True,
        "acceptance_criteria_evaluable": True,
        "cos_pass": True,
    }))
    assert result.complete is True


def test_integrate_rejects_missing_required_check() -> None:
    remote = _remote(checks=({"name": "Repository contracts", "head_sha": "H", "conclusion": "success"},))
    result = reconcile(ReconciliationInput("integrate", {
        "cos_pass": True,
        "repository_identity": "org/repo",
        "pr_number": 7,
        "base_ref": "main",
        "base_sha": "B",
        "candidate_sha": "H",
    }, remote))
    assert result.eligible is False
    assert "required_checks" in result.contradictions


def test_accept_does_not_advance_until_cos_pass() -> None:
    result = reconcile(ReconciliationInput("accept", {
        "verification_current": True,
        "candidate_unchanged": True,
        "acceptance_criteria_evaluable": True,
        "cos_pass": False,
    }))
    assert result.complete is False


def test_integrate_rejects_review_for_old_head() -> None:
    result = reconcile(ReconciliationInput("integrate", {
        "cos_pass": True,
        "repository_identity": "org/repo",
        "pr_number": 7,
        "base_ref": "main",
        "base_sha": "B",
        "candidate_sha": "H",
    }, _remote(reviewed_head_sha="OLD")))
    assert result.eligible is False
    assert "review_bound_to_head" in result.contradictions


@pytest.mark.parametrize("state", ["COMMENTED", "CHANGES_REQUESTED", "DISMISSED"])
def test_integrate_rejects_non_approving_effective_review_state(state: str) -> None:
    remote = _remote()
    remote = replace(remote, effective_review_state=state, review_policy_satisfied=False)
    result = reconcile(ReconciliationInput("integrate", {
        "cos_pass": True,
        "repository_identity": "org/repo",
        "pr_number": 7,
        "base_ref": "main",
        "base_sha": "B",
        "candidate_sha": "H",
    }, remote))
    assert result.eligible is False
    assert "review_policy" in result.contradictions


def test_integrate_allows_review_not_required_policy() -> None:
    remote = _remote()
    remote = replace(
        remote,
        review_policy_source="repo-contract://review-not-required",
        review_policy_satisfied=True,
        effective_review_state="NONE",
        review_required=False,
        review_identity=None,
        review_pr_number=None,
        reviewed_head_sha=None,
    )
    result = reconcile(ReconciliationInput("integrate", {
        "cos_pass": True,
        "repository_identity": "org/repo",
        "pr_number": 7,
        "base_ref": "main",
        "base_sha": "B",
        "candidate_sha": "H",
    }, remote))
    assert result.eligible is True


def test_integrate_eligibility_does_not_claim_merge_completion() -> None:
    facts = {
        "cos_pass": True,
        "repository_identity": "org/repo",
        "pr_number": 7,
        "base_ref": "main",
        "base_sha": "B",
        "candidate_sha": "H",
    }
    result = reconcile(ReconciliationInput("integrate", facts, _remote()))
    assert result.integration_eligible is True
    assert result.integration_complete is False


def test_integrate_requires_remote_availability() -> None:
    result = reconcile(ReconciliationInput("integrate", {"cos_pass": True}, RemotePrEvidence()))
    assert result.eligible is False
    assert "remote_unavailable" in result.contradictions


def test_retire_requires_settlement_and_no_continuation() -> None:
    result = reconcile(ReconciliationInput("retire", {
        "runtime_owned": True,
        "no_continuation": False,
        "settled": True,
    }))
    assert result.eligible is False


def test_prune_requires_retirement_complete() -> None:
    result = reconcile(ReconciliationInput("prune", {
        "canonical_consequence": True,
        "consumer_release": True,
        "retention_expired": True,
        "retirement_complete": False,
        "evidence_released": True,
    }))
    assert result.eligible is False


def test_prune_does_not_advance_until_retirement_complete() -> None:
    result = reconcile(ReconciliationInput("prune", {
        "canonical_consequence": True,
        "consumer_release": True,
        "retention_expired": True,
        "retirement_complete": False,
    }))
    assert result.complete is False
