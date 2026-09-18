from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ADMISSION_STATES = frozenset({"ADMITTED", "DEFERRED", "BLOCKED", "REJECTED"})


@dataclass(frozen=True)
class AdmissionResult:
    lane_id: str
    state: str
    reason: str


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
    lanes_by_id: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    validate_admission_results(results)
    output = {"admitted": [], "deferred": [], "blocked": [], "rejected": []}
    for result in results:
        lane = lanes_by_id.get(result.lane_id, {"lane_id": result.lane_id})
        if result.state == "REJECTED":
            output["rejected"].append({"lane_id": result.lane_id, "reason": result.reason})
        else:
            output[result.state.casefold()].append(lane)
    return output
