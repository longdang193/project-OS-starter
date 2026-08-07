from __future__ import annotations

import hashlib

import pytest

from harness_core.terminal_observation import TerminalObservationError, normalize_terminal_observation


PACKET = {
    "execution_budget": {"turn_timeout_seconds": 300},
    "lanes": [{"lane_id": "work"}, {"lane_id": "validate"}],
    "checks": {"diff": ["git", "diff", "--check"]},
}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def observation(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "version": 1,
        "kind": "provider_failure",
        "source": "provider_terminal",
        "lane_id": "work",
        "session_id": "thread-1",
        "turn_id": "turn-1",
        "turn_timeout_seconds": None,
        "elapsed_seconds": 3.5,
        "terminal_status": "failed",
        "interrupt_status": None,
        "item_states": [],
        "command_states": [],
        "final_claim_state": {"state": "missing"},
        "error": {
            "field_names": ["code", "message"],
            "code_hash": _digest("E_FAIL"),
            "code_length": 6,
            "message_hash": _digest("provider failed"),
            "message_length": 15,
        },
    }
    value.update(overrides)
    return value


def test_normalize_terminal_observation_persists_bounded_provider_failure() -> None:
    assert normalize_terminal_observation(observation(), PACKET) == observation()


def test_normalize_terminal_observation_accepts_preallocation_protocol_failure() -> None:
    result = normalize_terminal_observation(observation(
        kind="protocol_failure",
        source="transport_exception",
        session_id=None,
        turn_id=None,
        terminal_status=None,
        error={
            "field_names": ["message"],
            "code_hash": None,
            "code_length": None,
            "message_hash": _digest("invalid payload"),
            "message_length": 15,
        },
    ), PACKET)

    assert result["kind"] == "protocol_failure"
    assert result["session_id"] is None


def test_normalize_terminal_observation_accepts_approval_request() -> None:
    result = normalize_terminal_observation(observation(
        kind="approval_required",
        source="approval_request",
        terminal_status=None,
        error=None,
    ), PACKET)

    assert result["kind"] == "approval_required"
    assert result["terminal_status"] is None


def test_normalize_terminal_observation_accepts_packet_check_lane() -> None:
    assert normalize_terminal_observation(observation(lane_id="check:diff"), PACKET)["lane_id"] == "check:diff"


@pytest.mark.parametrize("raw", [
    observation(kind="timeout"),
    observation(error={"field_names": ["message", "code"], "code_hash": None, "code_length": None, "message_hash": _digest("x"), "message_length": 1}),
    observation(error={"field_names": ["message"], "code_hash": None, "code_length": None, "message_hash": _digest("secret"), "message_length": 6, "raw_message": "secret"}),
    observation(session_id=None),
])
def test_normalize_terminal_observation_rejects_invalid_or_sensitive_evidence(raw: dict[str, object]) -> None:
    with pytest.raises(TerminalObservationError):
        normalize_terminal_observation(raw, PACKET)
