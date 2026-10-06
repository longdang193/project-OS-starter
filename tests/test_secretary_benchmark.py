from collections import defaultdict

import pytest

from scripts.benchmark_secretary_architecture import (
    SCENARIOS,
    run_contract_benchmark,
)


def test_contract_benchmark_runs_paired_deterministic_scenarios() -> None:
    results = run_contract_benchmark()

    assert len(results) == len(SCENARIOS) * 2
    assert {item.run_id for item in results} == {1}
    assert {item.evidence_provenance for item in results} == {"deterministic-fake"}
    assert all(item.live is False for item in results)
    assert all(item.latency_ms is None for item in results)
    assert all(item.token_usage is None for item in results)

    paired = defaultdict(dict)
    for item in results:
        paired[(item.scenario_id, item.run_id)][item.architecture] = item

    for pair in paired.values():
        assert set(pair) == {"baseline", "target"}
        assert pair["target"].payload_bytes == pair["baseline"].payload_bytes
        assert pair["target"].context_items == pair["baseline"].context_items


@pytest.mark.parametrize(
    "scenario_id",
    ["restart_recovery", "duplicate_activation", "lost_activation_response"],
)
def test_target_reconciles_activation_without_duplicate_effects(scenario_id: str) -> None:
    results = [item for item in run_contract_benchmark() if item.scenario_id == scenario_id]
    target = [item for item in results if item.architecture == "target"]
    baseline = [item for item in results if item.architecture == "baseline"]

    assert all(item.correct and item.duplicate_effects == 0 for item in target)
    assert all(item.duplicate_effects == 1 for item in baseline)


def test_target_coalesces_missed_event_without_live_claims() -> None:
    results = [item for item in run_contract_benchmark() if item.scenario_id == "missed_event"]
    target = [item for item in results if item.architecture == "target"]
    baseline = [item for item in results if item.architecture == "baseline"]

    assert all(item.correct and item.model_wakes == 1 for item in target)
    assert all(item.model_wakes == 2 for item in baseline)


@pytest.mark.parametrize(
    "scenario_id",
    ["activation_binding_conflict", "release_replay", "delivery_payload_conflict"],
)
def test_target_blocks_changed_activation_or_delivery_inputs(scenario_id: str) -> None:
    target = [
        item
        for item in run_contract_benchmark()
        if item.scenario_id == scenario_id and item.architecture == "target"
    ]

    assert len(target) == 1
    assert target[0].correct is True
    assert target[0].duplicate_effects == 0


def test_target_keeps_unresolved_old_event_actionable() -> None:
    results = [item for item in run_contract_benchmark() if item.scenario_id == "unresolved_old_event"]
    target = next(item for item in results if item.architecture == "target")
    baseline = next(item for item in results if item.architecture == "baseline")

    assert target.correct is True
    assert target.outcome == "RECONCILE"
    assert baseline.correct is False
