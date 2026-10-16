"""Validate and summarize matched operational topology evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


STATUS_VALUES = {
    "observed",
    "unavailable",
    "BLOCKED_CAPABILITY",
    "INCONCLUSIVE",
    "invalid",
}
REQUIRED_ROW_FIELDS = (
    "protocol_id",
    "protocol_digest",
    "trial_id",
    "order_index",
    "arm",
    "condition",
    "repetition",
    "status",
    "source_producer",
    "source_digest",
    "run_identity",
    "base_identity",
    "workload_digest",
    "final_artifact_digest",
    "acceptance_criteria_digest",
    "verification_commands_digest",
    "configuration_digest",
    "attempted",
    "stage_timestamps",
    "metrics",
    "lifecycle",
    "capability_state",
)


class EvidenceError(ValueError):
    """Raised when a protocol or evidence record is structurally invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def protocol_digest(protocol: dict[str, Any]) -> str:
    payload = dict(protocol)
    payload.pop("protocol_digest", None)
    return sha256_json(payload)


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidenceError(f"expected JSON object: {path}")
    return value


def load_rows(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise EvidenceError(f"row {line_number} is not a JSON object")
        value["_line"] = line_number
        rows.append(value)
    return rows


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if protocol.get("schema") != "topology-economics-protocol/v1":
        errors.append("unsupported protocol schema")
    if protocol.get("protocol_digest") != protocol_digest(protocol):
        errors.append("protocol_digest does not match canonical protocol content")
    arms = protocol.get("arms")
    if not isinstance(arms, list) or {item.get("id") for item in arms if isinstance(item, dict)} != {
        "direct_controller",
        "single_worker",
        "cos_two_lane",
    }:
        errors.append("protocol must declare exactly the three supported arms")
    trial_design = protocol.get("trial_design", {})
    if trial_design.get("attempted_trials") != 18:
        errors.append("protocol must declare 18 attempted trials")
    if trial_design.get("repetitions_per_arm_per_condition") != 3:
        errors.append("protocol must declare three repetitions per arm and condition")
    order = trial_design.get("order")
    if not isinstance(order, list) or len(order) != 18 or len(set(order)) != 18:
        errors.append("protocol trial order must contain 18 unique trial identifiers")
    if protocol.get("evidence_rules", {}).get("no_synthetic_fallback") is not True:
        errors.append("protocol must forbid synthetic fallback")
    return errors


def _expected_trials(protocol: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for order_index, trial_id in enumerate(protocol["trial_design"]["order"]):
        arm, condition, repetition_text = trial_id.split(":")
        result[trial_id] = {
            "order_index": order_index,
            "arm": arm,
            "condition": condition,
            "repetition": int(repetition_text),
        }
    return result


def _metric_status(metric: Any) -> str:
    if not isinstance(metric, dict):
        return "invalid"
    return str(metric.get("status", "invalid"))


def _validate_stage_timestamps(row: dict[str, Any], protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    stages = protocol.get("stages", [])
    allowed = {item.get("name") for item in stages if isinstance(item, dict)}
    previous_end: float | None = None
    for item in row.get("stage_timestamps", []):
        if not isinstance(item, dict) or item.get("stage") not in allowed:
            errors.append("stage_timestamps contains an unknown stage")
            continue
        started = item.get("started_at_ms")
        ended = item.get("ended_at_ms")
        if started is None or ended is None:
            continue
        if not isinstance(started, (int, float)) or not isinstance(ended, (int, float)):
            errors.append(f"stage {item['stage']} timestamps must be numeric or null")
            continue
        if ended < started:
            errors.append(f"stage {item['stage']} ends before it starts")
        if previous_end is not None and started < previous_end:
            errors.append("stage timestamps are not monotonic")
        previous_end = ended
    return errors


def _validate_intervals(row: dict[str, Any]) -> list[str]:
    if "useful_intervals_ms" not in row:
        return []
    intervals = row["useful_intervals_ms"]
    if not isinstance(intervals, list):
        return ["useful_intervals_ms must be a list"]
    errors: list[str] = []
    for index, interval in enumerate(intervals):
        if not isinstance(interval, list) or len(interval) != 2:
            errors.append(f"useful interval {index} must contain exactly two endpoints")
            continue
        start, end = interval
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in interval):
            errors.append(f"useful interval {index} endpoints must be numeric")
            continue
        if not math.isfinite(float(start)) or not math.isfinite(float(end)):
            errors.append(f"useful interval {index} endpoints must be finite")
            continue
        if end < start:
            errors.append(f"useful interval {index} ends before it starts")
    return errors


def validate_row(row: dict[str, Any], protocol: dict[str, Any], expected: dict[str, dict[str, Any]]) -> list[str]:
    status = row.get("status")
    if status not in STATUS_VALUES:
        return [f"unsupported status: {status!r}"]
    if status == "invalid":
        return [] if row.get("invalid_reason") else ["invalid rows require invalid_reason"]
    errors = [f"missing field: {field}" for field in REQUIRED_ROW_FIELDS if field not in row]
    if errors:
        return errors
    trial_id = row["trial_id"]
    expected_trial = expected.get(trial_id)
    if expected_trial is None:
        errors.append("trial_id is not in the protocol order")
    else:
        for field in ("order_index", "arm", "condition", "repetition"):
            if row.get(field) != expected_trial[field]:
                errors.append(f"{field} does not match protocol trial order")
    if row.get("protocol_id") != protocol.get("protocol_id"):
        errors.append("protocol_id does not match")
    if row.get("protocol_digest") != protocol.get("protocol_digest"):
        errors.append("protocol_digest does not match")
    matching_fields = protocol["workload"]["matching_fields"]
    for field in matching_fields:
        if row.get(field) != protocol["workload"].get(field):
            errors.append(f"{field} does not match protocol")
    if row.get("base_identity") != protocol.get("base_revision"):
        errors.append("base_identity does not match protocol base_revision")
    for field in ("source_digest", "run_identity", "base_identity", "source_producer"):
        if not row.get(field):
            errors.append(f"{field} is required for non-invalid rows")
    if not isinstance(row.get("attempted"), bool):
        errors.append("attempted must be boolean")
    if status == "observed" and row.get("attempted") is not True:
        errors.append("observed rows must have attempted=true")
    if status == "BLOCKED_CAPABILITY" and row.get("capability_state") != "blocked":
        errors.append("BLOCKED_CAPABILITY rows require capability_state=blocked")
    if row.get("capability_state") not in {"confirmed", "unavailable", "blocked"}:
        errors.append("unsupported capability_state")
    errors.extend(_validate_stage_timestamps(row, protocol))
    errors.extend(_validate_intervals(row))
    metrics = row.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("metrics must be an object")
    else:
        for metric_name in protocol.get("metric_names", []):
            if metric_name not in metrics:
                errors.append(f"missing metric: {metric_name}")
                continue
            metric = metrics[metric_name]
            metric_status = _metric_status(metric)
            if metric_status not in {"observed", "unavailable", "blocked"}:
                errors.append(f"unsupported metric status: {metric_name}")
            if metric_status == "observed" and not isinstance(metric.get("value"), (int, float)):
                errors.append(f"observed metric has no numeric value: {metric_name}")
            if metric_status != "observed" and metric.get("value") is not None:
                errors.append(f"unavailable metric has a value: {metric_name}")
    lifecycle = row.get("lifecycle")
    if not isinstance(lifecycle, dict):
        errors.append("lifecycle must be an object")
    else:
        for field in ("accepted_outcome", "review", "integration", "retirement", "cleanup", "reconciliation"):
            if field not in lifecycle:
                errors.append(f"missing lifecycle field: {field}")
        if status == "observed":
            requirements = protocol["evidence_rules"]["accepted_lifecycle"]
            for field, allowed in requirements.items():
                if lifecycle.get(field) not in allowed:
                    errors.append(f"observed rows require accepted lifecycle field: {field}")
            if row.get("capability_state") != "confirmed":
                errors.append("observed rows require capability_state=confirmed")
            metrics = row.get("metrics")
            accepted_metric = metrics.get("accepted_outcome_wall_time_ms") if isinstance(metrics, dict) else None
            if not isinstance(accepted_metric, dict) or accepted_metric.get("status") != "observed":
                errors.append("observed rows require accepted outcome wall time")
    return errors


def validate_rows(protocol: dict[str, Any], rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    protocol_errors = validate_protocol(protocol)
    expected = _expected_trials(protocol) if not protocol_errors else {}
    seen: set[str] = set()
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for row in rows:
        errors = validate_row(row, protocol, expected) if not protocol_errors else ["protocol is invalid"]
        trial_id = row.get("trial_id")
        if trial_id in seen and row.get("status") != "invalid":
            errors.append("duplicate trial_id")
        if trial_id and row.get("status") != "invalid":
            seen.add(trial_id)
        if errors:
            invalid.append({"line": row.get("_line"), "trial_id": trial_id, "errors": errors})
        else:
            valid.append(row)
    missing_trials = sorted(set(expected) - seen)
    return {
        "protocol_errors": protocol_errors,
        "valid_rows": valid,
        "invalid_rows": invalid,
        "missing_trials": missing_trials,
        "valid": not protocol_errors and not invalid and not missing_trials,
    }


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def _union_duration(intervals: list[list[float]]) -> float | None:
    if not intervals:
        return None
    ordered = sorted((start, end) for start, end in intervals if end >= start)
    if not ordered:
        return None
    total = 0.0
    start, end = ordered[0]
    for next_start, next_end in ordered[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return total + end - start


def _metric_aggregate(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    values = [row["metrics"][name]["value"] for row in rows if row["metrics"][name]["status"] == "observed"]
    if not values:
        return {"status": "unavailable", "value": None, "observed_count": 0}
    numeric = [float(value) for value in values]
    return {
        "status": "observed",
        "value": {
            "count": len(numeric),
            "mean": sum(numeric) / len(numeric),
            "p50": _percentile(numeric, 0.50),
            "p95": _percentile(numeric, 0.95),
        },
        "observed_count": len(numeric),
    }


def summarize(protocol: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    validation = validate_rows(protocol, rows)
    valid_rows = validation["valid_rows"]
    observed_rows = [row for row in valid_rows if row.get("status") == "observed"]
    arms = {arm["id"]: {} for arm in protocol.get("arms", [])}
    for arm in arms:
        for condition in protocol["trial_design"]["conditions"]:
            subset = [row for row in valid_rows if row.get("arm") == arm and row.get("condition") == condition]
            observed = [row for row in subset if row.get("status") == "observed"]
            interval_values = [row.get("useful_intervals_ms") for row in observed]
            per_trial_union = [_union_duration(intervals) for intervals in interval_values]
            interval_union = None
            if observed and all(isinstance(intervals, list) for intervals in interval_values):
                interval_union = sum(value or 0.0 for value in per_trial_union)
            arms[arm][condition] = {
                "row_count": len(subset),
                "observed_count": len(observed),
                "blocked_count": sum(row.get("status") == "BLOCKED_CAPABILITY" for row in subset),
                "unavailable_count": sum(row.get("status") == "unavailable" for row in subset),
                "inconclusive_count": sum(row.get("status") == "INCONCLUSIVE" for row in subset),
                "wall_time_ms": _metric_aggregate(observed, "accepted_outcome_wall_time_ms"),
                "useful_interval_sum_ms": sum(
                    end - start for row in observed for start, end in row.get("useful_intervals_ms", [])
                ) if observed else None,
                "useful_interval_union_ms": interval_union,
                "trace_trial_ids": [row["trial_id"] for row in subset],
            }
    return {
        "schema": "topology-economics-summary/v1",
        "protocol_id": protocol.get("protocol_id"),
        "protocol_digest": protocol.get("protocol_digest"),
        "validation": {
            "protocol_errors": validation["protocol_errors"],
            "valid": validation["valid"],
            "valid_row_count": len(valid_rows),
            "invalid_row_count": len(validation["invalid_rows"]),
            "invalid_rows": validation["invalid_rows"],
            "missing_trials": validation["missing_trials"],
        },
        "status_counts": {
            status: sum(row.get("status") == status for row in rows) for status in sorted(STATUS_VALUES)
        },
        "observed_row_count": len(observed_rows),
        "arms": arms,
        "decision": {
            "disposition": "inconclusive",
            "reason": "No production optimization decision is made by the passive aggregator; the report must apply the evidence gate.",
        },
    }


def _public_validation(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "valid": result["valid"],
        "protocol_errors": result["protocol_errors"],
        "invalid_rows": result["invalid_rows"],
        "missing_trials": result["missing_trials"],
        "valid_row_count": len(result["valid_rows"]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--protocol", type=Path, required=True)
    validate.add_argument("--input", type=Path, required=True)
    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("--protocol", type=Path, required=True)
    summarize_parser.add_argument("--input", type=Path, required=True)
    summarize_parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    protocol = load_json(args.protocol)
    rows = load_rows(args.input)
    if args.command == "validate":
        result = validate_rows(protocol, rows)
        print(json.dumps(_public_validation(result), indent=2, sort_keys=True))
        return 0 if not result["protocol_errors"] and not result["missing_trials"] and not result["invalid_rows"] else 1
    result = summarize(protocol, rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "observed_row_count": result["observed_row_count"]}, sort_keys=True))
    return 0 if result["validation"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
