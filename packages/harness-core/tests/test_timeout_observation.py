from __future__ import annotations

import pytest

from harness_core.timeout_observation import TimeoutObservationError, normalize_timeout_observation


PACKET = {
    "execution_budget": {"turn_timeout_seconds": 300},
    "lanes": [{"lane_id": "work"}, {"lane_id": "validate"}],
}


def observation(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "version": 1,
        "lane_id": "work",
        "session_id": "thread-1",
        "turn_id": "turn-1",
        "turn_timeout_seconds": 300,
        "elapsed_seconds": 300.5,
        "terminal_status": "interrupted",
        "interrupt_status": "terminal_confirmed",
        "item_states": [{"item_id": "cmd-1", "type": "commandExecution", "state": "completed"}],
        "command_states": [{
            "item_id": "cmd-1",
            "state": "completed",
            "command_hash": "a" * 64,
            "command_length": 12,
            "response_hash": "b" * 64,
            "response_length": 3,
            "exit_code": 0,
        }],
        "final_claim_state": {"state": "unverified", "response_hash": "c" * 64, "response_length": 18},
    }
    value.update(overrides)
    return value


def test_normalize_timeout_observation_persists_bounded_safe_fields() -> None:
    assert normalize_timeout_observation(observation(), PACKET) == observation()


@pytest.mark.parametrize(("field", "value", "message"), [
    ("lane_id", "missing", "lane_id"),
    ("turn_timeout_seconds", 301, "execution budget"),
    ("elapsed_seconds", 331, "elapsed_seconds"),
    ("session_id", "bad secret value", "session_id"),
])
def test_normalize_timeout_observation_rejects_packet_conflicts_and_malformed_ids(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(TimeoutObservationError, match=message):
        normalize_timeout_observation(observation(**{field: value}), PACKET)


@pytest.mark.parametrize("raw", [
    observation(stdout="secret"),
    observation(command_states=[{"item_id": "cmd-1", "state": "completed", "stdout": "secret"}]),
    observation(item_states=[{"item_id": f"item-{index}", "type": "commandExecution", "state": "completed"} for index in range(17)]),
])
def test_normalize_timeout_observation_rejects_sensitive_or_over_bound_evidence(raw: dict[str, object]) -> None:
    with pytest.raises(TimeoutObservationError):
        normalize_timeout_observation(raw, PACKET)
