from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


SCENARIOS = (
    "direct_secretary",
    "advisory_cos_without_plan",
    "managed_secretary_without_receipt",
    "ambiguous_result",
    "cleanup_quarantine",
    "multi_workstream_escalation",
)


@dataclass(frozen=True)
class ContractMetric:
    scenario_id: str
    run_id: int
    architecture: str
    evidence_provenance: str
    live: bool
    correct: bool
    outcome: str
    semantic_result: str
    failure_classification: str
    blocker: str
    mandatory_inputs: int
    preflight_count: int
    provider_queries: int
    messages: int
    duplicate_effects: int
    time_to_first_result_ms: None = None
    latency_ms: None = None
    token_usage: None = None


def _metric(
    scenario_id: str,
    run_id: int,
    architecture: str,
    *,
    correct: bool,
    outcome: str,
    semantic_result: str,
    failure_classification: str = "none",
    blocker: str = "none",
    mandatory_inputs: int = 1,
    preflight_count: int = 0,
    provider_queries: int = 0,
    messages: int = 0,
    duplicate_effects: int = 0,
) -> ContractMetric:
    return ContractMetric(
        scenario_id=scenario_id,
        run_id=run_id,
        architecture=architecture,
        evidence_provenance="deterministic-fake",
        live=False,
        correct=correct,
        outcome=outcome,
        semantic_result=semantic_result,
        failure_classification=failure_classification,
        blocker=blocker,
        mandatory_inputs=mandatory_inputs,
        preflight_count=preflight_count,
        provider_queries=provider_queries,
        messages=messages,
        duplicate_effects=duplicate_effects,
    )


def _target_metric(scenario_id: str, run_id: int) -> ContractMetric:
    values = {
        "direct_secretary": dict(
            outcome="attention_routed",
            semantic_result="reported",
        ),
        "advisory_cos_without_plan": dict(
            outcome="recommendation_returned",
            semantic_result="reported",
        ),
        "managed_secretary_without_receipt": dict(
            outcome="result_preserved",
            semantic_result="reported",
            blocker="optional_observability",
        ),
        "ambiguous_result": dict(
            outcome="reconcile_without_retry",
            semantic_result="ambiguous",
            failure_classification="ambiguous_result",
            blocker="retry_blocked",
        ),
        "cleanup_quarantine": dict(
            outcome="result_preserved_resource_quarantined",
            semantic_result="reported",
            failure_classification="cleanup_recovery_required",
            blocker="reuse_blocked",
        ),
        "multi_workstream_escalation": dict(
            outcome="secretary_routes_to_governed_plan",
            semantic_result="reported",
            blocker="plan_bound_mutation",
            messages=2,
        ),
    }
    return _metric(scenario_id, run_id, "target", correct=True, **values[scenario_id])


def _baseline_metric(scenario_id: str, run_id: int) -> ContractMetric:
    values = {
        "direct_secretary": dict(
            correct=False,
            outcome="blocked_by_universal_preflight",
            semantic_result="unavailable",
            failure_classification="false_blocker",
            blocker="plan_or_provider_required",
            preflight_count=3,
            provider_queries=1,
        ),
        "advisory_cos_without_plan": dict(
            correct=False,
            outcome="blocked_without_plan",
            semantic_result="unavailable",
            failure_classification="false_blocker",
            blocker="plan_required",
            preflight_count=2,
        ),
        "managed_secretary_without_receipt": dict(
            correct=False,
            outcome="discarded_without_receipt",
            semantic_result="unavailable",
            failure_classification="false_blocker",
            blocker="receipt_required",
            preflight_count=3,
            provider_queries=1,
        ),
        "ambiguous_result": dict(
            correct=False,
            outcome="duplicate_retry",
            semantic_result="ambiguous",
            failure_classification="duplicate_effect",
            blocker="retry_not_correlated",
            preflight_count=1,
            duplicate_effects=1,
        ),
        "cleanup_quarantine": dict(
            correct=False,
            outcome="discarded_on_cleanup_uncertainty",
            semantic_result="unavailable",
            failure_classification="false_blocker",
            blocker="cleanup_required_for_result",
            preflight_count=2,
        ),
        "multi_workstream_escalation": dict(
            correct=False,
            outcome="duplicate_coordination_mesh",
            semantic_result="ambiguous",
            failure_classification="duplicate_effect",
            blocker="unowned_cross_workstream_handoff",
            preflight_count=2,
            messages=4,
            duplicate_effects=1,
        ),
    }
    return _metric(scenario_id, run_id, "baseline", **values[scenario_id])


def run_contract_benchmark(iterations: int = 1) -> list[ContractMetric]:
    if iterations < 1:
        raise ValueError("iterations must be positive")
    results: list[ContractMetric] = []
    for run_id in range(1, iterations + 1):
        for scenario_id in SCENARIOS:
            results.append(_baseline_metric(scenario_id, run_id))
            results.append(_target_metric(scenario_id, run_id))
    return results


def main() -> int:
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(json.dumps([asdict(item) for item in run_contract_benchmark(iterations)], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
