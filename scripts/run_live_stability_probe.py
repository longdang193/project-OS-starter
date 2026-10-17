"""Record attributable live-stability evidence without executing work."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

try:
    from scripts.benchmark_operational_comparison import load_json, sha256_json, validate_protocol, validate_row
except ModuleNotFoundError:
    from benchmark_operational_comparison import load_json, sha256_json, validate_protocol, validate_row
try:
    from scripts.project_os_runtime.acceptance import validate_acceptance_decision
except ModuleNotFoundError:
    from project_os_runtime.acceptance import validate_acceptance_decision


SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "environment",
    "password",
    "prompt",
    "raw_output",
    "secret",
    "stderr",
    "stdout",
    "token",
}
OWNER_FIELDS = {
    "attempted",
    "base_identity",
    "capability_state",
    "lifecycle",
    "metrics",
    "run_identity",
    "source_producer",
    "stage_timestamps",
    "useful_intervals_ms",
}
OWNER_BOUND_FIELDS = {
    "protocol_id",
    "protocol_digest",
    "trial_id",
    "arm",
    "condition",
    "repetition",
}


def sanitize_record(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: sanitize_record(item)
            for key, item in value.items()
            if str(key).lower() not in SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [sanitize_record(item) for item in value]
    return value


def _validate_protocol_or_raise(protocol: dict[str, Any]) -> None:
    errors = validate_protocol(protocol)
    if errors:
        raise ValueError(f"protocol is invalid: {'; '.join(errors)}")


def _expected_trial(protocol: dict[str, Any], trial_id: str) -> dict[str, Any]:
    try:
        order_index = protocol["trial_design"]["order"].index(trial_id)
    except ValueError as exc:
        raise ValueError(f"trial_id is not in the protocol order: {trial_id}") from exc
    arm, condition, repetition_text = trial_id.split(":")
    return {
        "order_index": order_index,
        "arm": arm,
        "condition": condition,
        "repetition": int(repetition_text),
    }


def _blocked_metrics(protocol: dict[str, Any], reason: str) -> dict[str, dict[str, Any]]:
    return {
        name: {"status": "blocked", "value": None, "reason": reason}
        for name in protocol["metric_names"]
    }


def _blocked_lifecycle() -> dict[str, str]:
    return {
        "accepted_outcome": "not_observed",
        "review": "not_started",
        "integration": "not_started",
        "retirement": "not_started",
        "cleanup": "not_applicable",
        "reconciliation": "not_required",
    }


def _base_row(protocol: dict[str, Any], trial_id: str, *, status: str, arm: str, condition: str, repetition: int, owner_result: dict[str, Any]) -> dict[str, Any]:
    workload = protocol["workload"]
    return {
        "schema": "topology-economics-row/v1",
        "protocol_id": protocol["protocol_id"],
        "protocol_digest": protocol["protocol_digest"],
        "trial_id": trial_id,
        "order_index": _expected_trial(protocol, trial_id)["order_index"],
        "arm": arm,
        "condition": condition,
        "repetition": repetition,
        "status": status,
        "source_producer": owner_result["source_producer"],
        "source_digest": owner_result.get("source_digest") or sha256_json(owner_result),
        "run_identity": owner_result["run_identity"],
        "base_identity": owner_result["base_identity"],
        "workload_digest": workload["workload_digest"],
        "final_artifact_digest": workload["final_artifact_digest"],
        "acceptance_criteria_digest": workload["acceptance_criteria_digest"],
        "verification_commands_digest": workload["verification_commands_digest"],
        "configuration_digest": workload["configuration_digest"],
        "attempted": owner_result["attempted"],
        "stage_timestamps": owner_result["stage_timestamps"],
        "useful_intervals_ms": owner_result.get("useful_intervals_ms", []),
        "metrics": owner_result["metrics"],
        "lifecycle": owner_result["lifecycle"],
        "capability_state": owner_result["capability_state"],
    }


def _validate_row_or_raise(protocol: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    trial_id = row["trial_id"]
    errors = validate_row(row, protocol, {trial_id: _expected_trial(protocol, trial_id)})
    if errors:
        raise ValueError(f"owner result evidence is invalid: {'; '.join(errors)}")
    return row


def validate_owner_result(protocol: dict[str, Any], owner_result: dict[str, Any], *, trial_id: str, expected_arm: str) -> dict[str, Any]:
    if not isinstance(owner_result, dict):
        raise ValueError("owner result must be an object")
    expected = _expected_trial(protocol, trial_id)
    if expected["arm"] != expected_arm:
        raise ValueError(f"record mode arm mismatch: expected {expected_arm}, protocol has {expected['arm']}")
    sanitized = sanitize_record(owner_result)
    matching_fields = set(protocol["workload"]["matching_fields"])
    required_fields = OWNER_FIELDS | OWNER_BOUND_FIELDS | matching_fields
    missing = sorted(required_fields - sanitized.keys())
    if missing:
        raise ValueError(f"owner result missing fields: {', '.join(missing)}")
    expected_fields = {
        "protocol_id": protocol["protocol_id"],
        "protocol_digest": protocol["protocol_digest"],
        "trial_id": trial_id,
        "arm": expected["arm"],
        "condition": expected["condition"],
        "repetition": expected["repetition"],
        **{field: protocol["workload"][field] for field in matching_fields},
    }
    for field, expected_value in expected_fields.items():
        if sanitized[field] != expected_value:
            raise ValueError(f"owner result {field} does not match protocol")
    if sanitized["base_identity"] != protocol["base_revision"]:
        raise ValueError("owner result base_identity does not match protocol base_revision")
    if sanitized["attempted"] is not True:
        raise ValueError("observed owner result must have attempted=true")
    if sanitized["capability_state"] != "confirmed":
        raise ValueError("observed owner result requires capability_state=confirmed")
    if sanitized.get("status", "observed") != "observed":
        raise ValueError("owner result status must be observed")
    lifecycle = sanitized["lifecycle"]
    if lifecycle.get("accepted_outcome") != "accepted":
        raise ValueError("runtime completion is not semantic acceptance")
    for field, allowed in protocol["evidence_rules"]["accepted_lifecycle"].items():
        if lifecycle.get(field) not in allowed:
            raise ValueError(f"owner result lifecycle field is not accepted: {field}")
    if sanitized.get("runtime_status") in {"completed", "succeeded"} and lifecycle.get("accepted_outcome") != "accepted":
        raise ValueError("runtime completion is not semantic acceptance")
    return _validate_row_or_raise(protocol, _base_row(
        protocol,
        trial_id,
        status="observed",
        arm=expected_arm,
        condition=expected["condition"],
        repetition=expected["repetition"],
        owner_result=sanitized,
    ))


def _record_owner_result(protocol: dict[str, Any], owner_result: dict[str, Any], *, trial_id: str, expected_arm: str) -> dict[str, Any]:
    _validate_protocol_or_raise(protocol)
    return validate_owner_result(protocol, owner_result, trial_id=trial_id, expected_arm=expected_arm)


def record_direct(protocol: dict[str, Any], owner_result: dict[str, Any], *, trial_id: str) -> dict[str, Any]:
    return _record_owner_result(protocol, owner_result, trial_id=trial_id, expected_arm="direct_controller")


def record_worker_result(protocol: dict[str, Any], owner_result: dict[str, Any], *, trial_id: str) -> dict[str, Any]:
    return _record_owner_result(protocol, owner_result, trial_id=trial_id, expected_arm="single_worker")


_ACCEPTANCE_BINDING_FIELDS = (
    "task_id",
    "plan_identity",
    "candidate_sha",
    "acceptance_checkpoint_sha",
    "assignment_id",
    "attempt_id",
)


def _require_acceptance_binding(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("expected acceptance binding must be an object")
    missing = [
        field
        for field in _ACCEPTANCE_BINDING_FIELDS
        if not isinstance(value.get(field), str) or not value.get(field, "").strip()
    ]
    if missing:
        raise ValueError(
            "expected acceptance binding is incomplete: " + ", ".join(missing)
        )
    return value


def record_cos_result(
    protocol: dict[str, Any],
    owner_result: dict[str, Any],
    *,
    trial_id: str,
    expected_acceptance_binding: Mapping[str, Any],
) -> dict[str, Any]:
    acceptance_decision = owner_result.get("acceptance_decision")
    if not isinstance(acceptance_decision, dict) or acceptance_decision.get("decision") != "PASS":
        raise ValueError("CoS owner result requires a real AcceptanceDecision(PASS)")
    expected_binding = _require_acceptance_binding(expected_acceptance_binding)
    validation_reasons = validate_acceptance_decision(
        acceptance_decision,
        expected_task_id=expected_binding["task_id"],
        expected_plan_identity=expected_binding["plan_identity"],
        expected_candidate_sha=expected_binding["candidate_sha"],
        expected_acceptance_checkpoint_sha=expected_binding["acceptance_checkpoint_sha"],
        expected_assignment_id=expected_binding["assignment_id"],
        expected_attempt_id=expected_binding["attempt_id"],
    )
    if validation_reasons:
        raise ValueError(
            "CoS owner result acceptance decision is invalid: "
            + "; ".join(validation_reasons)
        )
    row = _record_owner_result(protocol, owner_result, trial_id=trial_id, expected_arm="cos_two_lane")
    row["acceptance_decision"] = sanitize_record(acceptance_decision)
    return row


def record_blocked(protocol: dict[str, Any], *, trial_id: str, reason: str, source_producer: str = "capability-preflight") -> dict[str, Any]:
    _validate_protocol_or_raise(protocol)
    expected = _expected_trial(protocol, trial_id)
    owner_result = {
        "attempted": False,
        "base_identity": protocol["base_revision"],
        "capability_state": "blocked",
        "lifecycle": _blocked_lifecycle(),
        "metrics": _blocked_metrics(protocol, reason),
        "run_identity": f"blocked:{trial_id}",
        "source_producer": source_producer,
        "stage_timestamps": [{"stage": "admission", "started_at_ms": None, "ended_at_ms": None}],
    }
    row = _base_row(
        protocol,
        trial_id,
        status="BLOCKED_CAPABILITY",
        arm=expected["arm"],
        condition=expected["condition"],
        repetition=expected["repetition"],
        owner_result=owner_result,
    )
    row["blocked_reason"] = reason
    return _validate_row_or_raise(protocol, row)


def write_row(path: str | Path, row: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(sanitize_record(row), sort_keys=True) + "\n")


def _load_result(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("owner result JSON must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["record-direct", "record-worker-result", "record-cos-result", "record-blocked"])
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--acceptance-binding", type=Path)
    parser.add_argument("--reason")
    parser.add_argument("--source-producer", default="capability-preflight")
    args = parser.parse_args(argv)
    protocol = load_json(args.protocol)
    _validate_protocol_or_raise(protocol)
    if args.mode == "record-blocked":
        if not args.reason:
            parser.error("--reason is required for record-blocked")
        row = record_blocked(protocol, trial_id=args.trial_id, reason=args.reason, source_producer=args.source_producer)
    else:
        if not args.result:
            parser.error("--result is required for owner-result modes")
        owner_result = _load_result(args.result)
        if args.mode == "record-cos-result":
            if not args.acceptance_binding:
                parser.error("--acceptance-binding is required for record-cos-result")
            row = record_cos_result(
                protocol,
                owner_result,
                trial_id=args.trial_id,
                expected_acceptance_binding=_load_result(args.acceptance_binding),
            )
        else:
            recorders = {
                "record-direct": record_direct,
                "record-worker-result": record_worker_result,
            }
            row = recorders[args.mode](protocol, owner_result, trial_id=args.trial_id)
    write_row(args.output, row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
