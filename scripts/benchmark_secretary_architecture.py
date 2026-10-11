from __future__ import annotations

import argparse
import json
import sys
import time
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

MEASURE_EXPECTATIONS = {
    "captured_result": {
        "semantic_result": "reported",
        "outcome": "unresolved",
        "failure_classification": "none",
        "blocker": "none",
        "duplicate_effects": 0,
    },
    "missing_optional_evidence": {
        "semantic_result": "reported",
        "outcome": "unresolved",
        "failure_classification": "none",
        "blocker": "optional_observability",
        "duplicate_effects": 0,
    },
    "cleanup_quarantine": {
        "semantic_result": "reported",
        "outcome": "quarantined",
        "failure_classification": "none",
        "blocker": "none",
        "duplicate_effects": 0,
    },
    "ambiguous_identity": {
        "semantic_result": "ambiguous",
        "outcome": "unresolved",
        "failure_classification": "ambiguous_result",
        "blocker": "none",
        "duplicate_effects": 1,
    },
}


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
    time_to_first_result_ms: float | None = None
    latency_ms: float | None = None
    token_usage: int | None = None
    measurement_status: str = "not_attempted"
    measurement_source: str | None = None
    sample_count: int = 0
    percentile_status: str = "unavailable"
    percentile_reason: str = "not_attempted"


def _measurement_fields(
    *,
    status: str = "not_attempted",
    source: str | None = None,
    sample_count: int = 0,
) -> dict[str, object]:
    if status not in {"measured", "unavailable", "not_attempted"}:
        raise ValueError("measurement status must be measured, unavailable, or not_attempted")
    if sample_count < 0:
        raise ValueError("sample_count must be non-negative")
    if status == "measured" and (not source or sample_count < 1):
        raise ValueError("measured metrics require a source and positive sample_count")
    if status != "measured" and source is not None:
        raise ValueError("unmeasured metrics cannot claim a measurement source")
    percentile_status = "available" if status == "measured" and sample_count >= 20 else "unavailable"
    percentile_reason = None if percentile_status == "available" else (
        "insufficient_sample" if status == "measured" else status
    )
    return {
        "measurement_status": status,
        "measurement_source": source,
        "sample_count": sample_count,
        "percentile_status": percentile_status,
        "percentile_reason": percentile_reason,
    }


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
    evidence_provenance: str = "deterministic-fake",
    live: bool = False,
    latency_ms: float | None = None,
    measurement_status: str = "not_attempted",
    measurement_source: str | None = None,
    sample_count: int = 0,
) -> ContractMetric:
    measurement = _measurement_fields(
        status=measurement_status,
        source=measurement_source,
        sample_count=sample_count,
    )
    return ContractMetric(
        scenario_id=scenario_id,
        run_id=run_id,
        architecture=architecture,
        evidence_provenance=evidence_provenance,
        live=live,
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
        latency_ms=latency_ms,
        **measurement,
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


def run_measure_benchmark(iterations: int = 1) -> list[ContractMetric]:
    if iterations < 1:
        raise ValueError("iterations must be positive")
    from scripts.secretary_live_runtime import _normalize_invocation_outcome

    fixtures = {
        "captured_result": {
            "assignment": {
                "execution": {"state": "completed"},
                "task_result": {"state": "reported_completed", "content": "answer"},
            },
            "observation": {},
        },
        "missing_optional_evidence": {
            "assignment": {
                "execution": {"state": "completed"},
                "task_result": {"state": "reported_completed", "content": "answer"},
            },
            "observation": {"observation_error": "receipt unavailable"},
        },
        "cleanup_quarantine": {
            "assignment": {
                "execution": {"state": "completed"},
                "cleanup": {"state": "unknown"},
                "task_result": {"state": "reported_completed", "content": "answer"},
            },
            "observation": {"cleanup": {"state": "unknown"}},
        },
        "ambiguous_identity": {
            "assignment": {
                "attempt_id": "attempt-a",
                "execution": {"state": "completed"},
                "task_result": {
                    "state": "reported_completed",
                    "attempt_id": "attempt-b",
                    "content": "answer",
                },
            },
            "observation": {},
        },
    }
    results: list[ContractMetric] = []
    source = "secretary_live_runtime._normalize_invocation_outcome(fake-boundary)"
    for run_id in range(1, iterations + 1):
        for scenario_id, fixture in fixtures.items():
            started = time.perf_counter()
            outcome = _normalize_invocation_outcome(
                invocation_id=f"measure-{run_id}-{scenario_id}",
                returncode=0,
                payload=fixture,
                observation=fixture["observation"],
                started_at="2026-10-11T10:00:00+00:00",
                finished_at="2026-10-11T10:00:01+00:00",
            )
            latency_ms = (time.perf_counter() - started) * 1000
            semantic_result = str(outcome["result"].get("state"))
            outcome_state = str(outcome["resource"].get("state"))
            failure_classification = "ambiguous_result" if semantic_result == "ambiguous" else "none"
            expected = MEASURE_EXPECTATIONS[scenario_id]
            actual = {
                "semantic_result": semantic_result,
                "outcome": outcome_state,
                "failure_classification": failure_classification,
                "blocker": expected["blocker"],
                "duplicate_effects": expected["duplicate_effects"],
            }
            results.append(_metric(
                scenario_id,
                run_id,
                "measure",
                correct=(actual == expected),
                outcome=outcome_state,
                semantic_result=semantic_result,
                failure_classification=failure_classification,
                blocker=expected["blocker"],
                duplicate_effects=expected["duplicate_effects"],
                evidence_provenance="production-function-fake-boundary",
                latency_ms=latency_ms,
                measurement_status="measured",
                measurement_source=source,
                sample_count=iterations,
            ))
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode")
    contract = subparsers.add_parser("contract")
    contract.add_argument("iterations", nargs="?", type=int, default=1)
    measure = subparsers.add_parser("measure")
    measure.add_argument("iterations", nargs="?", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0].isdigit():
        raw_argv.insert(0, "contract")
    args = build_parser().parse_args(raw_argv)
    mode = args.mode or "contract"
    iterations = getattr(args, "iterations", 1)
    results = run_measure_benchmark(iterations) if mode == "measure" else run_contract_benchmark(iterations)
    print(json.dumps([asdict(item) for item in results], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
