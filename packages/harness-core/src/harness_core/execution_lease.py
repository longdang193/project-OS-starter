from __future__ import annotations

import math
import re
from typing import Any


class ExecutionLeaseError(ValueError):
    pass


_DURATION_MODEL_FIELDS = {
    "id",
    "max_turns_per_lane",
    "per_turn_overhead_seconds",
    "stop_proof_seconds",
    "check_timeout_seconds",
    "core_verification_seconds",
    "cleanup_grace_seconds",
}
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _positive(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ExecutionLeaseError(f"execution lease duration model has invalid {field}")
    return value


def normalize_duration_model(value: Any) -> dict[str, int | str]:
    if not isinstance(value, dict) or set(value) != _DURATION_MODEL_FIELDS:
        raise ExecutionLeaseError("execution lease duration model has invalid fields")
    identifier = value.get("id")
    if not isinstance(identifier, str) or not _IDENTIFIER.fullmatch(identifier):
        raise ExecutionLeaseError("execution lease duration model has invalid id")
    return {
        "id": identifier,
        "max_turns_per_lane": _positive(value.get("max_turns_per_lane"), "max_turns_per_lane"),
        "per_turn_overhead_seconds": _positive(value.get("per_turn_overhead_seconds"), "per_turn_overhead_seconds"),
        "stop_proof_seconds": _positive(value.get("stop_proof_seconds"), "stop_proof_seconds"),
        "check_timeout_seconds": _positive(value.get("check_timeout_seconds"), "check_timeout_seconds"),
        "core_verification_seconds": _positive(value.get("core_verification_seconds"), "core_verification_seconds"),
        "cleanup_grace_seconds": _positive(value.get("cleanup_grace_seconds"), "cleanup_grace_seconds"),
    }


def _execution_waves(lanes: Any) -> list[list[dict[str, Any]]]:
    if not isinstance(lanes, list) or not lanes:
        raise ExecutionLeaseError("execution lease lanes are invalid")
    by_id: dict[str, dict[str, Any]] = {}
    for lane in lanes:
        if not isinstance(lane, dict):
            raise ExecutionLeaseError("execution lease lanes are invalid")
        lane_id = lane.get("lane_id")
        dependencies = lane.get("dependencies")
        if (
            not isinstance(lane_id, str)
            or not _IDENTIFIER.fullmatch(lane_id)
            or lane_id in by_id
            or not isinstance(dependencies, list)
            or not all(isinstance(dependency, str) and _IDENTIFIER.fullmatch(dependency) for dependency in dependencies)
            or not isinstance(lane.get("write_capable"), bool)
        ):
            raise ExecutionLeaseError("execution lease lanes are invalid")
        by_id[lane_id] = lane
    if any(dependency not in by_id for lane in by_id.values() for dependency in lane["dependencies"]):
        raise ExecutionLeaseError("execution lease lane dependency is unknown")
    remaining = set(by_id)
    complete: set[str] = set()
    waves: list[list[dict[str, Any]]] = []
    while remaining:
        wave_ids = sorted(
            lane_id
            for lane_id in remaining
            if all(dependency in complete for dependency in by_id[lane_id]["dependencies"])
        )
        if not wave_ids:
            raise ExecutionLeaseError("execution lease lanes contain a dependency cycle")
        waves.append([by_id[lane_id] for lane_id in wave_ids])
        complete.update(wave_ids)
        remaining.difference_update(wave_ids)
    return waves


def resolve_execution_lease(
    duration_model: Any,
    *,
    lanes: Any,
    checks: Any,
    max_parallel_writers: Any,
    turn_timeout_seconds: Any,
) -> dict[str, Any]:
    model = normalize_duration_model(duration_model)
    if not isinstance(max_parallel_writers, int) or isinstance(max_parallel_writers, bool) or max_parallel_writers <= 0:
        raise ExecutionLeaseError("execution lease max_parallel_writers is invalid")
    turn_timeout = _positive(turn_timeout_seconds, "turn_timeout_seconds")
    if not isinstance(checks, dict) or not all(isinstance(name, str) and isinstance(command, list) for name, command in checks.items()):
        raise ExecutionLeaseError("execution lease checks are invalid")
    lane_seconds = (
        model["max_turns_per_lane"] * turn_timeout
        + (model["max_turns_per_lane"] - 1) * model["per_turn_overhead_seconds"]
        + model["stop_proof_seconds"]
    )
    host_seconds = 0
    for wave in _execution_waves(lanes):
        host_lanes = [lane for lane in wave if lane.get("kind") not in {"check", "integrate"}]
        writers = sum(lane["write_capable"] for lane in host_lanes)
        nonwriters = len(host_lanes) - writers
        host_seconds += lane_seconds * max(math.ceil(writers / max_parallel_writers), int(nonwriters > 0))
    return {
        "duration_model_id": model["id"],
        "execution_lease_seconds": host_seconds
        + len(checks) * model["check_timeout_seconds"]
        + model["core_verification_seconds"]
        + model["cleanup_grace_seconds"],
        "host_duration_limits": {
            "max_turns_per_lane": model["max_turns_per_lane"],
            "per_turn_overhead_seconds": model["per_turn_overhead_seconds"],
            "stop_proof_seconds": model["stop_proof_seconds"],
        },
        "check_timeout_seconds": model["check_timeout_seconds"],
        "core_verification_seconds": model["core_verification_seconds"],
        "cleanup_grace_seconds": model["cleanup_grace_seconds"],
    }
