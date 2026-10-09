from scripts.project_os_runtime.reconciliation import (
    REMOTE_EVIDENCE_UNAVAILABLE,
    LocalEvidence,
    RemotePrEvidence,
    RuntimeEvidence,
    reconcile,
)


def _local(**overrides):
    values = dict(
        repository_identity="repo",
        plan_ref="plan.md",
        plan_revision="plan-v1",
        task_id="Task 1",
        task_state="active",
        checkpoint_sha="abc",
        lane_head_sha="abc",
        source_ref="git",
    )
    values.update(overrides)
    return LocalEvidence(**values)


def _runtime(**overrides):
    values = dict(
        attempt_id="attempt-1",
        worker_terminal=True,
        task_result_published=True,
        settlement_proven=True,
        retirement_state="preserved",
        source_ref="receipt",
    )
    values.update(overrides)
    return RuntimeEvidence(**values)


def test_reconcile_rejects_changed_pr_head():
    snapshot = reconcile(
        _local(),
        RemotePrEvidence(available=True, head_sha="def", checks_passed=True, review_valid=True, mergeable=True, source_ref="github"),
        _runtime(),
    )

    assert snapshot.next_action == "RECONCILE"
    assert snapshot.contradictions[0].code == "PR_HEAD_MISMATCH"
    assert snapshot.eligible.integration is False


def test_reconcile_fails_closed_when_github_is_unavailable():
    snapshot = reconcile(_local(), RemotePrEvidence(), _runtime())

    assert snapshot.remote_status == REMOTE_EVIDENCE_UNAVAILABLE
    assert snapshot.next_action == REMOTE_EVIDENCE_UNAVAILABLE
    assert snapshot.eligible.integration is False


def test_reconcile_accepts_bound_current_evidence():
    snapshot = reconcile(
        _local(task_state="completed"),
        RemotePrEvidence(available=True, head_sha="abc", checks_passed=True, review_valid=True, mergeable=True, source_ref="github"),
        _runtime(),
    )

    assert snapshot.eligible.verification is True
    assert snapshot.eligible.acceptance is True
    assert snapshot.eligible.integration is True
    assert snapshot.next_action == "NO_ACTION"
