from collections import defaultdict

import pytest

from scripts.benchmark_secretary_architecture import (
    SCENARIOS,
    run_contract_benchmark,
    run_live_benchmark,
)


def test_contract_benchmark_runs_six_paired_deterministic_scenarios() -> None:
    results = run_contract_benchmark()

    assert len(SCENARIOS) == 6
    assert len(results) == len(SCENARIOS) * 2
    assert {item.evidence_provenance for item in results} == {"deterministic-fake"}
    assert all(item.live is False for item in results)
    assert all(item.latency_ms is None for item in results)
    assert all(item.time_to_first_result_ms is None for item in results)

    paired = defaultdict(dict)
    for item in results:
        paired[(item.scenario_id, item.run_id)][item.architecture] = item

    assert set(paired) == {(scenario, 1) for scenario in SCENARIOS}
    assert all(set(pair) == {"baseline", "target"} for pair in paired.values())


def test_target_has_no_provider_query_and_uses_minimal_preflight() -> None:
    target = [item for item in run_contract_benchmark() if item.architecture == "target"]

    assert all(item.provider_queries == 0 for item in target)
    assert all(item.preflight_count == 0 for item in target)


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_target_preserves_strongest_proven_fact(scenario_id: str) -> None:
    target = next(
        item
        for item in run_contract_benchmark()
        if item.scenario_id == scenario_id and item.architecture == "target"
    )

    assert target.correct is True
    assert target.duplicate_effects == 0


def test_degraded_cases_do_not_turn_optional_evidence_into_result_loss() -> None:
    managed = next(
        item
        for item in run_contract_benchmark()
        if item.scenario_id == "managed_secretary_without_receipt" and item.architecture == "target"
    )
    cleanup = next(
        item
        for item in run_contract_benchmark()
        if item.scenario_id == "cleanup_quarantine" and item.architecture == "target"
    )

    assert managed.semantic_result == "reported"
    assert managed.blocker == "optional_observability"
    assert cleanup.semantic_result == "reported"
    assert cleanup.blocker == "reuse_blocked"


def test_benchmark_does_not_claim_latency_or_token_improvement() -> None:
    for item in run_contract_benchmark(2):
        assert item.latency_ms is None
        assert item.time_to_first_result_ms is None
        assert item.token_usage is None


def test_contract_cli_mode_is_explicit_and_preserves_fixture_provenance() -> None:
    from pathlib import Path
    import subprocess
    import sys

    script = Path(__file__).parents[1] / "scripts" / "benchmark_secretary_architecture.py"
    result = subprocess.run(
        [sys.executable, str(script), "contract", "2"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert '"measurement_status": "not_attempted"' in result.stdout


def test_live_benchmark_reports_runner_measurements_without_inventing_unobserved_state() -> None:
    calls: list[tuple[str, str]] = []

    def runner(scenario_id: str, architecture: str) -> dict[str, object]:
        calls.append((scenario_id, architecture))
        return {
            "correct": None,
            "latency_ms": 12.5,
            "time_to_first_result_ms": 8.0,
            "subprocess_count": 2,
            "allocation_reuse": "reused" if architecture == "target" else "recreated",
            "reconciliation_count": 1 if architecture == "target" else 2,
            "measurement_source": "test-runner",
        }

    results = run_live_benchmark(runner=runner)

    assert len(results) == len(SCENARIOS) * 2
    assert len(calls) == len(results)
    assert all(item.live is True for item in results)
    assert all(item.measurement_status == "measured" for item in results)
    assert all(item.measurement_source == "test-runner" for item in results)
    assert all(item.latency_ms == 12.5 for item in results)
    assert all(item.subprocess_count == 2 for item in results)
    assert {item.allocation_reuse for item in results} == {"reused", "recreated"}
    assert {item.reconciliation_count for item in results} == {1, 2}
    assert all(item.correct is None for item in results)


def test_live_cli_mode_does_not_claim_contract_probe_as_architecture_measurement() -> None:
    from pathlib import Path
    import subprocess
    import sys

    script = Path(__file__).parents[1] / "scripts" / "benchmark_secretary_architecture.py"
    result = subprocess.run(
        [sys.executable, str(script), "live", "1"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    rows = __import__("json").loads(result.stdout)
    assert len(rows) == len(SCENARIOS) * 2
    assert all(row["live"] is True for row in rows)
    assert all(row["measurement_status"] == "unavailable" for row in rows)
    assert all(row["subprocess_count"] is None for row in rows)
    assert all(row["allocation_reuse"] == "unavailable" for row in rows)
    assert all(row["reconciliation_count"] is None for row in rows)
