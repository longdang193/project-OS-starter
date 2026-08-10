from __future__ import annotations

import hashlib

import pytest

from harness_core.terminal_observation import (
    TerminalObservationError,
    normalize_host_terminal_observation,
    normalize_terminal_observation,
)


PACKET = {
    "execution_budget": {"turn_timeout_seconds": 300},
    "lanes": [{"lane_id": "work"}, {"lane_id": "validate"}],
    "checks": {"diff": ["git", "diff", "--check"]},
}

V2_PACKET = {
    **PACKET,
    "execution_lease": {
        "duration_model_id": "codex_app_server.v1",
        "execution_lease_seconds": 1_500,
    },
}
V2_BINDING = {
    "run_id": "run-1",
    "attempt_id": "attempt-1",
    "packet_sha256": "a" * 64,
    "lease_id": "lease-1",
    "lease_epoch": 1,
    "host_instance_id": "host-1",
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


def host_observation(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_id": "host_terminal_observation/v2",
        "observation_id": "observation-1",
        **V2_BINDING,
        "lane_id": "work",
        "source": "completed",
        "observed_at": "2026-08-09T12:00:00+00:00",
        "elapsed_seconds": 3.5,
        "provider_session_id": "thread-1",
        "provider_turn_id": "turn-1",
        "terminal_status": "completed",
        "item_states": [],
        "command_states": [],
        "final_claim_state": {
            "state": "valid",
            "response_hash": _digest('{"kind":"claimed_result"}'),
            "response_length": 25,
        },
        "error": None,
        "containment": {
            "state": "stopped",
            "job_id": "job-1",
            "root_processes": [{"pid": 123, "creation_id": "process-1"}],
            "active_process_count": 0,
            "termination_action": "none",
        },
        "stop_proof": {
            "state": "confirmed",
            "observed_at": "2026-08-09T12:00:01+00:00",
            "host_process": {"pid": 456, "creation_id": "host-process-1"},
            "cancellation_request_id": None,
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


def test_normalize_terminal_observation_preserves_bounded_command_timing() -> None:
    raw = observation(
        command_states=[{
            "item_id": "command-1",
            "state": "completed",
            "command_hash": _digest("pytest"),
            "command_length": 6,
            "response_hash": _digest("ok"),
            "response_length": 2,
            "exit_code": 0,
            "observed_elapsed_seconds": 12.5,
        }],
        final_claim_state={
            "state": "unverified",
            "response_hash": _digest('{"kind":"claimed_result"}'),
            "response_length": 25,
            "observed_elapsed_seconds": 13.0,
        },
    )

    assert normalize_terminal_observation(raw, PACKET) == raw


def test_normalize_host_terminal_observation_v2_binds_packet_lease_and_containment() -> None:
    raw = host_observation()

    assert normalize_host_terminal_observation(raw, V2_PACKET, binding=V2_BINDING) == raw


def test_normalize_host_terminal_observation_v2_allows_no_start_provider_failure() -> None:
    raw = host_observation(
        source="provider_failure",
        provider_session_id=None,
        provider_turn_id=None,
        terminal_status="failed",
        final_claim_state={"state": "missing"},
        error={
            "field_names": ["message"],
            "code_hash": None,
            "code_length": None,
            "message_hash": _digest("provider admission failed"),
            "message_length": 25,
        },
        containment={
            "state": "not_started",
            "job_id": "job-1",
            "root_processes": [],
            "active_process_count": 0,
            "termination_action": "none",
        },
    )

    assert normalize_host_terminal_observation(raw, V2_PACKET, binding=V2_BINDING) == raw


@pytest.mark.parametrize(
    "raw",
    [
        host_observation(lease_id="lease-2"),
        host_observation(containment={
            "state": "stopped",
            "job_id": "job-1",
            "root_processes": [{"pid": 123, "creation_id": "process-1"}],
            "active_process_count": 1,
            "termination_action": "none",
        }),
        host_observation(error={
            "field_names": ["message"],
            "code_hash": None,
            "code_length": None,
            "message_hash": _digest("secret"),
            "message_length": 6,
            "raw_message": "secret",
        }),
        host_observation(stop_proof={
            "state": "confirmed",
            "observed_at": "2026-08-09T12:00:01+00:00",
            "host_process": {"pid": 456, "creation_id": "host-process-1"},
            "cancellation_request_id": "cancel-1",
        }),
    ],
)
def test_normalize_host_terminal_observation_v2_rejects_unbound_or_sensitive_data(raw: dict[str, object]) -> None:
    with pytest.raises(TerminalObservationError):
        normalize_host_terminal_observation(raw, V2_PACKET, binding=V2_BINDING)


@pytest.mark.parametrize("raw", [
    observation(kind="timeout"),
    observation(error={"field_names": ["message", "code"], "code_hash": None, "code_length": None, "message_hash": _digest("x"), "message_length": 1}),
    observation(error={"field_names": ["message"], "code_hash": None, "code_length": None, "message_hash": _digest("secret"), "message_length": 6, "raw_message": "secret"}),
    observation(session_id=None),
])
def test_normalize_terminal_observation_rejects_invalid_or_sensitive_evidence(raw: dict[str, object]) -> None:
    with pytest.raises(TerminalObservationError):
        normalize_terminal_observation(raw, PACKET)
