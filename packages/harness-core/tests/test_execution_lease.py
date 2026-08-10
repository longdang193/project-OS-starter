from __future__ import annotations

import pytest

from harness_core.execution_lease import ExecutionLeaseError, resolve_execution_lease


DURATION_MODEL = {
    "id": "codex_app_server.v1",
    "max_turns_per_lane": 2,
    "per_turn_overhead_seconds": 15,
    "stop_proof_seconds": 30,
    "check_timeout_seconds": 60,
    "core_verification_seconds": 45,
    "cleanup_grace_seconds": 30,
}


def test_resolve_execution_lease_uses_dependency_waves_and_writer_limit() -> None:
    result = resolve_execution_lease(
        DURATION_MODEL,
        lanes=[
            {"lane_id": "work-a", "dependencies": [], "write_capable": True},
            {"lane_id": "work-b", "dependencies": [], "write_capable": True},
            {"lane_id": "validate", "dependencies": ["work-a", "work-b"], "write_capable": False},
            {"lane_id": "check", "dependencies": ["validate"], "write_capable": False, "kind": "check"},
        ],
        checks={"diff": ["git", "diff", "--check"]},
        max_parallel_lanes=1,
        max_parallel_writers=1,
        turn_timeout_seconds=300,
    )

    assert result == {
        "duration_model_id": "codex_app_server.v1",
        "execution_lease_seconds": 2_070,
        "host_duration_limits": {
            "max_turns_per_lane": 2,
            "per_turn_overhead_seconds": 15,
            "stop_proof_seconds": 30,
        },
        "check_timeout_seconds": 60,
        "core_verification_seconds": 45,
        "cleanup_grace_seconds": 30,
    }


@pytest.mark.parametrize(
    ("model", "message"),
    [
        ({**DURATION_MODEL, "max_turns_per_lane": 0}, "max_turns_per_lane"),
        ({**DURATION_MODEL, "check_timeout_seconds": -1}, "check_timeout_seconds"),
        ({key: value for key, value in DURATION_MODEL.items() if key != "cleanup_grace_seconds"}, "fields"),
    ],
)
def test_resolve_execution_lease_rejects_unbounded_or_invalid_duration_model(model, message: str) -> None:
    with pytest.raises(ExecutionLeaseError, match=message):
        resolve_execution_lease(
            model,
            lanes=[{"lane_id": "work", "dependencies": [], "write_capable": True}],
            checks={},
            max_parallel_lanes=1,
            max_parallel_writers=1,
            turn_timeout_seconds=300,
        )


def test_resolve_execution_lease_caps_parallel_nonwriters_to_lane_limit() -> None:
    result = resolve_execution_lease(
        DURATION_MODEL,
        lanes=[
            {"lane_id": f"research-{index}", "dependencies": [], "write_capable": False}
            for index in range(5)
        ],
        checks={},
        max_parallel_lanes=2,
        max_parallel_writers=1,
        turn_timeout_seconds=300,
    )

    assert result["execution_lease_seconds"] == 2_010


@pytest.mark.parametrize(
    ("max_parallel_lanes", "max_parallel_writers", "message"),
    [
        (0, 1, "max_parallel_lanes"),
        (1, 2, "must cover max_parallel_writers"),
    ],
)
def test_resolve_execution_lease_rejects_invalid_lane_limit(
    max_parallel_lanes: int,
    max_parallel_writers: int,
    message: str,
) -> None:
    with pytest.raises(ExecutionLeaseError, match=message):
        resolve_execution_lease(
            DURATION_MODEL,
            lanes=[{"lane_id": "work", "dependencies": [], "write_capable": True}],
            checks={},
            max_parallel_lanes=max_parallel_lanes,
            max_parallel_writers=max_parallel_writers,
            turn_timeout_seconds=300,
        )
