from __future__ import annotations

from typing import Any

from .terminal_observation import TerminalObservationError, normalize_terminal_observation


class TimeoutObservationError(TerminalObservationError):
    pass


_FIELDS = {
    "version",
    "lane_id",
    "session_id",
    "turn_id",
    "turn_timeout_seconds",
    "elapsed_seconds",
    "terminal_status",
    "interrupt_status",
    "item_states",
    "command_states",
    "final_claim_state",
}


def normalize_timeout_observation(raw: Any, packet: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != _FIELDS:
        raise TimeoutObservationError("timeout observation has unsupported fields")
    terminal_raw = {
        **raw,
        "kind": "timeout",
        "source": "host_timeout_interrupt",
        "error": None,
    }
    try:
        normalized = normalize_terminal_observation(terminal_raw, packet)
    except TerminalObservationError as error:
        raise TimeoutObservationError(str(error).replace("terminal observation", "timeout observation")) from error
    return {field: normalized[field] for field in _FIELDS}
