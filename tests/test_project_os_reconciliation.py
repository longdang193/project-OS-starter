from scripts.project_os_runtime.reconciliation import ReconciliationInput, reconcile


def test_accept_does_not_compare_checkpoint_to_candidate() -> None:
    result = reconcile(ReconciliationInput("accept", {
        "verification_current": True,
        "candidate_unchanged": True,
        "acceptance_criteria_evaluable": True,
        "checkpoint_sha": "C",
        "lane_head_sha": "H",
    }))
    assert result.eligible is True


def test_failed_terminal_runtime_can_be_retired() -> None:
    result = reconcile(ReconciliationInput("retire", {
        "runtime_owned": True,
        "no_continuation": True,
        "settled": True,
        "retirement_complete": True,
    }))
    assert result.retirement_eligible is True
    assert result.retirement_complete is True


def test_recovery_blocks_retirement_and_prune() -> None:
    retire = reconcile(ReconciliationInput("retire", {
        "runtime_owned": True,
        "no_continuation": True,
        "settled": True,
        "retirement_complete": True,
        "recovery_required": True,
    }))
    prune = reconcile(ReconciliationInput("prune", {
        "canonical_consequence": True,
        "consumer_release": True,
        "retention_expired": True,
        "retirement_complete": True,
        "evidence_released": True,
        "recovery_required": True,
    }))
    assert retire.eligible is False
    assert prune.eligible is False
