from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

ADMISSION_STATES = frozenset({"ADMITTED", "DEFERRED", "BLOCKED", "REJECTED"})


@dataclass(frozen=True)
class AdmissionResult:
    lane_id: str
    state: str
    reason: str


@dataclass(frozen=True, slots=True)
class AdmissionBatch:
    prepared: tuple[Mapping[str, Any], ...]
    results: tuple[AdmissionResult, ...]


def canonical_token(value: object) -> str:
    return str(value).replace("\\", "/").strip("/").casefold()


def path_conflicts(left: object, right: object) -> bool:
    left_value = canonical_token(left)
    right_value = canonical_token(right)
    return (
        left_value == right_value
        or left_value.startswith(f"{right_value}/")
        or right_value.startswith(f"{left_value}/")
    )


def resource_sets_conflict(left: Any, right: Any) -> bool:
    return any(
        path_conflicts(left_item, right_item)
        for left_item in left
        for right_item in right
    )


def classify_admission(
    lane_id: str,
    *,
    duplicate_id: bool = False,
    executor: str | None = "deepagents",
    dependency_ready: bool = True,
    preparation_error: str | None = None,
    conflict_reason: str | None = None,
    fixed_contracts_match: bool = True,
    capacity_available: bool = True,
    capacity_reason: str = "capacity unavailable",
) -> AdmissionResult:
    if duplicate_id:
        return AdmissionResult(lane_id, "REJECTED", "duplicate lane ID")
    if executor != "deepagents":
        return AdmissionResult(lane_id, "REJECTED", f"unsupported executor: {executor}")
    if not dependency_ready:
        return AdmissionResult(lane_id, "BLOCKED", "dependency not ready")
    if preparation_error is not None:
        return AdmissionResult(lane_id, "REJECTED", preparation_error)
    if not fixed_contracts_match:
        return AdmissionResult(lane_id, "REJECTED", "fixed contracts differ")
    if conflict_reason is not None:
        return AdmissionResult(lane_id, "BLOCKED", conflict_reason)
    if not capacity_available:
        return AdmissionResult(lane_id, "DEFERRED", capacity_reason)
    return AdmissionResult(lane_id, "ADMITTED", "ready")


def validate_admission_results(results: list[AdmissionResult] | tuple[AdmissionResult, ...]) -> tuple[AdmissionResult, ...]:
    seen: set[str] = set()
    for result in results:
        if result.state not in ADMISSION_STATES:
            raise ValueError(f"unknown admission state: {result.state}")
        if result.lane_id in seen:
            raise ValueError("each lane must have one state")
        seen.add(result.lane_id)
    return tuple(results)


def legacy_admission_lists(
    results: list[AdmissionResult] | tuple[AdmissionResult, ...],
    lanes_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    validate_admission_results(results)
    output = {"admitted": [], "deferred": [], "blocked": [], "rejected": []}
    for result in results:
        lane = lanes_by_id.get(result.lane_id, {"lane_id": result.lane_id})
        if result.state == "REJECTED":
            output["rejected"].append({"lane_id": result.lane_id, "reason": result.reason})
        else:
            output[result.state.casefold()].append(lane)
    return output
