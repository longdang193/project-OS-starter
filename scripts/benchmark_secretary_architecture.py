from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Callable, Mapping


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
    evidence_kind: str
    live: bool
    correct: bool | None
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
    subprocess_count: int | None = None
    allocation_reuse: str = "unavailable"
    reconciliation_count: int | None = None


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
    correct: bool | None,
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
    evidence_kind: str = "deterministic_contract",
    live: bool = False,
    latency_ms: float | None = None,
    time_to_first_result_ms: float | None = None,
    measurement_status: str = "not_attempted",
    measurement_source: str | None = None,
    sample_count: int = 0,
    subprocess_count: int | None = None,
    allocation_reuse: str = "unavailable",
    reconciliation_count: int | None = None,
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
        evidence_kind=evidence_kind,
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
        time_to_first_result_ms=time_to_first_result_ms,
        latency_ms=latency_ms,
        **measurement,
        subprocess_count=subprocess_count,
        allocation_reuse=allocation_reuse,
        reconciliation_count=reconciliation_count,
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


def _default_live_runner(scenario_id: str, architecture: str) -> dict[str, object]:
    del scenario_id, architecture
    return {
        "correct": None,
        "latency_ms": None,
        "time_to_first_result_ms": None,
        "subprocess_count": None,
        "allocation_reuse": "unavailable",
        "reconciliation_count": None,
    }


def run_live_benchmark(
    iterations: int = 1,
    *,
    runner: Callable[[str, str], Mapping[str, object]] | None = None,
) -> list[ContractMetric]:
    if iterations < 1:
        raise ValueError("iterations must be positive")
    sample_runner = runner or _default_live_runner
    injected_runner = runner is not None
    results: list[ContractMetric] = []
    for run_id in range(1, iterations + 1):
        for scenario_id in SCENARIOS:
            for architecture in ("baseline", "target"):
                observed = sample_runner(scenario_id, architecture)
                latency = observed.get("latency_ms")
                first_result = observed.get("time_to_first_result_ms")
                measured = (
                    isinstance(latency, (int, float))
                    and not isinstance(latency, bool)
                    and math.isfinite(float(latency))
                    and float(latency) >= 0
                )
                subprocess_count = observed.get("subprocess_count")
                if subprocess_count is not None and (
                    not isinstance(subprocess_count, int)
                    or isinstance(subprocess_count, bool)
                    or subprocess_count < 0
                ):
                    raise ValueError("live subprocess_count must be a non-negative integer")
                reconciliation_count = observed.get("reconciliation_count")
                if reconciliation_count is not None and (
                    not isinstance(reconciliation_count, int)
                    or isinstance(reconciliation_count, bool)
                    or reconciliation_count < 0
                ):
                    raise ValueError("live reconciliation_count must be a non-negative integer")
                allocation_reuse = observed.get("allocation_reuse", "unavailable")
                if allocation_reuse not in {"reused", "recreated", "unavailable"}:
                    raise ValueError("live allocation_reuse must be reused, recreated, or unavailable")
                results.append(
                    _metric(
                        scenario_id,
                        run_id,
                        architecture,
                        correct=observed.get("correct"),
                        outcome="observed_live_sample" if measured else "measurement_unavailable",
                        semantic_result="not_captured",
                        failure_classification="not_classified",
                        blocker="measurement_only",
                        evidence_provenance=(
                            "injected-runner" if injected_runner and measured else "unavailable"
                        ),
                        evidence_kind=(
                            "injected_measurement" if injected_runner and measured else "unavailable"
                        ),
                        live=True,
                        latency_ms=float(latency) if measured else None,
                        time_to_first_result_ms=(
                            float(first_result)
                            if isinstance(first_result, (int, float))
                            and not isinstance(first_result, bool)
                            and math.isfinite(float(first_result))
                            and float(first_result) >= 0
                            else None
                        ),
                        measurement_status="measured" if measured else "unavailable",
                        measurement_source=(
                            str(observed["measurement_source"])
                            if measured and observed.get("measurement_source")
                            else None
                        ),
                        sample_count=1 if measured else 0,
                        subprocess_count=subprocess_count,
                        allocation_reuse=str(allocation_reuse),
                        reconciliation_count=reconciliation_count,
                    )
                )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode")
    contract = subparsers.add_parser("contract")
    contract.add_argument("iterations", nargs="?", type=int, default=1)
    for name in ("live", "trace"):
        live = subparsers.add_parser(name)
        live.add_argument("iterations", nargs="?", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0].isdigit():
        raw_argv.insert(0, "contract")
    args = build_parser().parse_args(raw_argv)
    mode = args.mode or "contract"
    iterations = getattr(args, "iterations", 1)
    if mode in {"live", "trace"}:
        results = run_live_benchmark(iterations)
    else:
        results = run_contract_benchmark(iterations)
    print(json.dumps([asdict(item) for item in results], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
