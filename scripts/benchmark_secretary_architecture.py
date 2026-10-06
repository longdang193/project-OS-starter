from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.project_os_runtime.secretary_adapter import (
    AttentionBrief,
    InMemoryActivationReceiptJournal,
    InMemoryControllerSessionAdapter,
)
from scripts.project_os_runtime.secretary_events import (
    DEPENDENCY_CHANGED,
    EventHint,
    ReconciliationEvidence,
    coalesce_event_hints,
    reconcile_event_hint,
)


SCENARIOS = (
    "simple_direct_work",
    "bounded_executor_work",
    "sustained_cos_workstream",
    "restart_recovery",
    "duplicate_activation",
    "lost_activation_response",
    "activation_binding_conflict",
    "release_replay",
    "delivery_payload_conflict",
    "missed_event",
    "unresolved_old_event",
    "stale_session",
    "dependency_change_cached_session",
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
    failure_classification: str
    activation_calls: int
    reconciliation_calls: int
    duplicate_effects: int
    model_wakes: int
    messages: int
    payload_bytes: int
    context_items: int
    latency_ms: None = None
    token_usage: None = None


def _metric(
    scenario_id: str,
    run_id: int,
    architecture: str,
    *,
    correct: bool = True,
    outcome: str = "completed",
    failure_classification: str = "none",
    activation_calls: int = 0,
    reconciliation_calls: int = 0,
    duplicate_effects: int = 0,
    model_wakes: int = 0,
    messages: int = 0,
    payload_bytes: int = 128,
    context_items: int = 1,
) -> ContractMetric:
    return ContractMetric(
        scenario_id=scenario_id,
        run_id=run_id,
        architecture=architecture,
        evidence_provenance="deterministic-fake",
        live=False,
        correct=correct,
        outcome=outcome,
        failure_classification=failure_classification,
        activation_calls=activation_calls,
        reconciliation_calls=reconciliation_calls,
        duplicate_effects=duplicate_effects,
        model_wakes=model_wakes,
        messages=messages,
        payload_bytes=payload_bytes,
        context_items=context_items,
    )


def _adapter_metrics(scenario_id: str, run_id: int) -> ContractMetric:
    if scenario_id in {"simple_direct_work", "bounded_executor_work"}:
        return _metric(
            scenario_id,
            run_id,
            "target",
            activation_calls=int(scenario_id == "bounded_executor_work"),
            model_wakes=int(scenario_id == "bounded_executor_work"),
            messages=int(scenario_id == "bounded_executor_work"),
        )
    if scenario_id == "sustained_cos_workstream":
        return _metric(
            scenario_id,
            run_id,
            "target",
            activation_calls=1,
            model_wakes=1,
            messages=1,
            context_items=2,
        )
    if scenario_id in {
        "restart_recovery",
        "duplicate_activation",
        "lost_activation_response",
    }:
        journal = InMemoryActivationReceiptJournal()
        adapter = InMemoryControllerSessionAdapter(journal)
        first = adapter.activate(
            "runtime", "activation-1", AttentionBrief("runtime", "reconcile")
        )
        restarted = InMemoryControllerSessionAdapter(journal)
        second = restarted.activate(
            "runtime", "activation-1", AttentionBrief("runtime", "reconcile")
        )
        return _metric(
            scenario_id,
            run_id,
            "target",
            correct=first.created and second.reused,
            outcome="reused_after_reconciliation",
            failure_classification="none" if first.created and second.reused else "recovery_required",
            activation_calls=2,
            reconciliation_calls=1,
            duplicate_effects=max(0, restarted.activation_side_effects),
            model_wakes=1,
            messages=1,
        )
    if scenario_id == "activation_binding_conflict":
        adapter = InMemoryControllerSessionAdapter()
        first = adapter.activate(
            "runtime",
            "activation-1",
            AttentionBrief("runtime", "reconcile", repository_identity="repo-a", canonical_work="plan-a"),
        )
        conflict = adapter.activate(
            "runtime",
            "activation-2",
            AttentionBrief("runtime", "reconcile", repository_identity="repo-a", canonical_work="plan-b"),
        )
        return _metric(
            scenario_id,
            run_id,
            "target",
            correct=first.created and conflict.recovery_required,
            outcome="recovery_required",
            failure_classification="binding_conflict",
            activation_calls=2,
            reconciliation_calls=1,
            duplicate_effects=0,
        )
    if scenario_id == "release_replay":
        adapter = InMemoryControllerSessionAdapter()
        brief = AttentionBrief("runtime", "reconcile")
        first = adapter.activate("runtime", "activation-1", brief)
        released = adapter.release_session(first.controller) if first.controller else None
        replay = adapter.activate("runtime", "activation-1", brief)
        return _metric(
            scenario_id,
            run_id,
            "target",
            correct=first.created and released is not None and released.released and replay.recovery_required,
            outcome="recovery_required",
            failure_classification="released_replay",
            activation_calls=2,
            reconciliation_calls=1,
            duplicate_effects=0,
        )
    if scenario_id == "delivery_payload_conflict":
        adapter = InMemoryControllerSessionAdapter()
        brief = AttentionBrief("runtime", "reconcile")
        first = adapter.activate("runtime", "activation-1", brief)
        if first.controller is None:
            return _metric(scenario_id, run_id, "target", correct=False, outcome="recovery_required")
        delivered = adapter.deliver(first.controller, brief, delivery_identity="delivery-1")
        conflict = adapter.deliver(
            first.controller,
            AttentionBrief("runtime", "changed"),
            delivery_identity="delivery-1",
        )
        return _metric(
            scenario_id,
            run_id,
            "target",
            correct=delivered.delivered and conflict.recovery_required,
            outcome="recovery_required",
            failure_classification="delivery_payload_conflict",
            activation_calls=1,
            reconciliation_calls=1,
            duplicate_effects=0,
        )
    if scenario_id == "stale_session":
        return _metric(
            scenario_id,
            run_id,
            "target",
            outcome="reconcile_required",
            reconciliation_calls=1,
            model_wakes=0,
        )

    if scenario_id == "unresolved_old_event":
        old = EventHint("fake", DEPENDENCY_CHANGED, "runtime", "event-1", "anchor-3", 3)
        action = reconcile_event_hint(
            old,
            ReconciliationEvidence("runtime", current_anchor="anchor-4"),
        )
        return _metric(
            scenario_id,
            run_id,
            "target",
            correct=action == "RECONCILE",
            outcome=action,
            reconciliation_calls=1,
            model_wakes=1,
            messages=1,
        )

    hints = [
        EventHint("fake", DEPENDENCY_CHANGED, "runtime", "event-1", "anchor-4", 4),
        EventHint("fake", DEPENDENCY_CHANGED, "runtime", "event-1", "anchor-4", 4),
    ]
    coalesced = coalesce_event_hints(hints)
    action = reconcile_event_hint(
        coalesced[0], ReconciliationEvidence("runtime", current_anchor="anchor-4")
    )
    return _metric(
        scenario_id,
        run_id,
        "target",
        correct=len(coalesced) == 1 and action == "SECRETARY_ATTENTION",
        outcome=action,
        reconciliation_calls=1,
        model_wakes=1,
        messages=1,
    )


def _baseline_metrics(scenario_id: str, run_id: int) -> ContractMetric:
    if scenario_id in {"simple_direct_work", "bounded_executor_work"}:
        return _metric(
            scenario_id,
            run_id,
            "baseline",
            activation_calls=int(scenario_id == "bounded_executor_work"),
            model_wakes=int(scenario_id == "bounded_executor_work"),
            messages=int(scenario_id == "bounded_executor_work"),
        )
    if scenario_id == "sustained_cos_workstream":
        return _metric(
            scenario_id,
            run_id,
            "baseline",
            activation_calls=1,
            model_wakes=1,
            messages=1,
            context_items=2,
        )
    if scenario_id in {
        "restart_recovery",
        "duplicate_activation",
        "lost_activation_response",
    }:
        return _metric(
            scenario_id,
            run_id,
            "baseline",
            correct=False,
            outcome="duplicate_activation",
            failure_classification="duplicate_effect",
            activation_calls=2,
            duplicate_effects=1,
            model_wakes=2,
            messages=2,
        )
    if scenario_id in {"activation_binding_conflict", "release_replay", "delivery_payload_conflict"}:
        return _metric(
            scenario_id,
            run_id,
            "baseline",
            correct=False,
            outcome="duplicate_effect",
            failure_classification="duplicate_effect",
            activation_calls=2,
            duplicate_effects=1,
            model_wakes=2,
            messages=2,
        )
    if scenario_id == "stale_session":
        return _metric(
            scenario_id,
            run_id,
            "baseline",
            correct=True,
            outcome="reconcile_required",
            model_wakes=0,
        )
    if scenario_id == "unresolved_old_event":
        return _metric(
            scenario_id,
            run_id,
            "baseline",
            correct=False,
            outcome="NO_ACTION",
            failure_classification="dropped_obligation",
            model_wakes=0,
        )
    return _metric(
        scenario_id,
        run_id,
        "baseline",
        correct=False,
        outcome="duplicate_event_activation",
        failure_classification="duplicate_effect",
        model_wakes=2,
        messages=2,
    )


def run_contract_benchmark(iterations: int = 1) -> list[ContractMetric]:
    if iterations < 1:
        raise ValueError("iterations must be positive")
    results: list[ContractMetric] = []
    for run_id in range(1, iterations + 1):
        for scenario_id in SCENARIOS:
            results.append(_baseline_metrics(scenario_id, run_id))
            results.append(_adapter_metrics(scenario_id, run_id))
    return results


def main() -> int:
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(json.dumps([asdict(item) for item in run_contract_benchmark(iterations)], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
