from __future__ import annotations

from scripts.project_os_runtime.reconciliation import RemotePrEvidence, reconcile


def _remote(*, pr_number: int = 7, head_sha: str = "H", reviewed_head_sha: str = "H") -> RemotePrEvidence:
    return RemotePrEvidence(
        repository_identity="org/repo",
        pr_number=pr_number,
        base_ref="main",
        base_sha="B",
        head_sha=head_sha,
        checks=({"head_sha": head_sha, "conclusion": "success"},),
        review_identity="review-1",
        review_pr_number=pr_number,
        reviewed_head_sha=reviewed_head_sha,
        mergeability="mergeable",
        source_ref="github://org/repo/pulls/7",
    )


def test_dispatch_does_not_require_github_or_attempt_id() -> None:
    result = reconcile(
        phase="dispatch",
        facts={
            "plan_valid": True,
            "dependencies_ready": True,
            "workspace_valid": True,
            "attempt_id": None,
        },
    )

    assert result.eligible is True
    assert result.next_action == "dispatch"


def test_dispatch_blocks_unready_dependencies() -> None:
    result = reconcile(
        phase="dispatch",
        facts={
            "plan_valid": True,
            "dependencies_ready": False,
            "workspace_valid": True,
        },
    )

    assert result.eligible is False
    assert result.contradictions == ("dependencies_ready",)


def test_accept_does_not_compare_plan_checkpoint_to_candidate_sha() -> None:
    result = reconcile(
        phase="accept",
        facts={
            "verification_current": True,
            "candidate_unchanged": True,
            "acceptance_criteria_evaluable": True,
            "checkpoint_sha": "C",
            "lane_head_sha": "H",
        },
    )

    assert result.eligible is True
    assert result.contradictions == ()


def test_integration_rejects_wrong_pr_even_when_head_matches() -> None:
    result = reconcile(
        phase="integrate",
        facts={
            "cos_pass": True,
            "repository_identity": "org/repo",
            "pr_number": 8,
            "base_ref": "main",
            "base_sha": "B",
            "candidate_sha": "H",
        },
        remote=_remote(pr_number=7),
    )

    assert result.eligible is False
    assert "pr_number" in result.contradictions


def test_integration_requires_expected_bindings() -> None:
    result = reconcile(phase="integrate", facts={"cos_pass": True}, remote=_remote())

    assert result.eligible is False
    assert set(result.missing) == {
        "repository_identity",
        "pr_number",
        "base_ref",
        "base_sha",
        "candidate_sha",
    }


def test_integration_rejects_review_bound_to_old_head() -> None:
    result = reconcile(
        phase="integrate",
        facts={
            "cos_pass": True,
            "repository_identity": "org/repo",
            "pr_number": 7,
            "base_ref": "main",
            "base_sha": "B",
            "candidate_sha": "H",
        },
        remote=_remote(reviewed_head_sha="OLD"),
    )

    assert result.eligible is False
    assert "review_bound_to_head" in result.contradictions


def test_green_remote_facts_without_cos_pass_cannot_integrate() -> None:
    result = reconcile(
        phase="integrate",
        facts={
            "cos_pass": False,
            "repository_identity": "org/repo",
            "pr_number": 7,
            "base_ref": "main",
            "base_sha": "B",
            "candidate_sha": "H",
        },
        remote=_remote(),
    )

    assert result.eligible is False
    assert "cos_pass" in result.contradictions


def test_merge_eligibility_does_not_claim_merge_completion() -> None:
    result = reconcile(
        phase="integrate",
        facts={
            "cos_pass": True,
            "repository_identity": "org/repo",
            "pr_number": 7,
            "base_ref": "main",
            "base_sha": "B",
            "candidate_sha": "H",
        },
        remote=_remote(),
    )

    assert result.integration_eligible is True
    assert result.integration_complete is False
    assert result.next_action == "integrate"


def test_incomplete_phases_do_not_advance() -> None:
    verify = reconcile(
        phase="verify",
        facts={
            "attempt_exists": True,
            "candidate_attributable": True,
            "worker_terminal": True,
            "task_result_published": True,
            "verification_complete": False,
        },
    )
    retire = reconcile(
        phase="retire",
        facts={
            "runtime_owned": True,
            "no_continuation": True,
            "settled": True,
            "retirement_complete": "false",
        },
    )

    assert verify.next_action == "verify"
    assert retire.next_action == "retire"


def test_prune_requires_positive_release_facts() -> None:
    result = reconcile(
        phase="prune",
        facts={
            "canonical_consequence": True,
            "consumer_release": True,
            "retention_expired": True,
            "evidence_released": True,
        },
    )

    assert result.complete is True
