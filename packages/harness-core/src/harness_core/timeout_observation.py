from __future__ import annotations

import copy
import re
from typing import Any

from .compatibility import TIMEOUT_OBSERVATION_VERSION


class TimeoutObservationError(ValueError):
    pass


_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
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
_ITEM_FIELDS = {"item_id", "type", "state"}
_COMMAND_FIELDS = {
    "item_id",
    "state",
    "command_hash",
    "command_length",
    "response_hash",
    "response_length",
    "exit_code",
}
_FINAL_STATES = {"missing", "unverified", "valid"}
_MAX_ITEMS = 16
_MAX_LENGTH = 1_000_000


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise TimeoutObservationError(f"timeout observation has invalid {field}")
    return value


def _status(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise TimeoutObservationError(f"timeout observation has invalid {field}")
    return value


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise TimeoutObservationError(f"timeout observation has invalid {field}")
    return value


def _length(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= _MAX_LENGTH:
        raise TimeoutObservationError(f"timeout observation has invalid {field}")
    return value


def _item_states(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > _MAX_ITEMS:
        raise TimeoutObservationError("timeout observation has invalid item_states")
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != _ITEM_FIELDS:
            raise TimeoutObservationError("timeout observation has invalid item_states")
        normalized.append({
            "item_id": _identifier(item.get("item_id"), "item_states.item_id"),
            "type": _status(item.get("type"), "item_states.type"),
            "state": _status(item.get("state"), "item_states.state"),
        })
    return normalized


def _command_states(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > _MAX_ITEMS:
        raise TimeoutObservationError("timeout observation has invalid command_states")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != _COMMAND_FIELDS:
            raise TimeoutObservationError("timeout observation has invalid command_states")
        exit_code = item.get("exit_code")
        if exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
            raise TimeoutObservationError("timeout observation has invalid command_states.exit_code")
        normalized.append({
            "item_id": _identifier(item.get("item_id"), "command_states.item_id"),
            "state": _status(item.get("state"), "command_states.state"),
            "command_hash": _hash(item.get("command_hash"), "command_states.command_hash"),
            "command_length": _length(item.get("command_length"), "command_states.command_length"),
            "response_hash": _hash(item.get("response_hash"), "command_states.response_hash"),
            "response_length": _length(item.get("response_length"), "command_states.response_length"),
            "exit_code": exit_code,
        })
    return normalized


def _final_claim_state(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("state"), str):
        raise TimeoutObservationError("timeout observation has invalid final_claim_state")
    state = value["state"]
    if state not in _FINAL_STATES:
        raise TimeoutObservationError("timeout observation has invalid final_claim_state")
    if state == "missing":
        if set(value) != {"state"}:
            raise TimeoutObservationError("timeout observation has invalid final_claim_state")
        return {"state": state}
    if set(value) != {"state", "response_hash", "response_length"}:
        raise TimeoutObservationError("timeout observation has invalid final_claim_state")
    return {
        "state": state,
        "response_hash": _hash(value.get("response_hash"), "final_claim_state.response_hash"),
        "response_length": _length(value.get("response_length"), "final_claim_state.response_length"),
    }


def normalize_timeout_observation(raw: Any, packet: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != _FIELDS:
        raise TimeoutObservationError("timeout observation has unsupported fields")
    if raw.get("version") != TIMEOUT_OBSERVATION_VERSION:
        raise TimeoutObservationError("timeout observation has unsupported version")
    lane_id = _identifier(raw.get("lane_id"), "lane_id")
    lanes = packet.get("lanes")
    lane_ids = {lane.get("lane_id") for lane in lanes if isinstance(lane, dict)} if isinstance(lanes, list) else set()
    checks = packet.get("checks")
    check_lane = lane_id.startswith("check:") and isinstance(checks, dict) and lane_id[6:] in checks
    if lane_id not in lane_ids and not check_lane:
        raise TimeoutObservationError("timeout observation lane_id conflicts with packet")
    budget = packet.get("execution_budget")
    if not isinstance(budget, dict) or not isinstance(budget.get("turn_timeout_seconds"), int):
        raise TimeoutObservationError("packet execution budget is invalid")
    timeout = raw.get("turn_timeout_seconds")
    if timeout != budget["turn_timeout_seconds"]:
        raise TimeoutObservationError("timeout observation conflicts with packet execution budget")
    elapsed = raw.get("elapsed_seconds")
    if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0 or elapsed > timeout + 30:
        raise TimeoutObservationError("timeout observation has invalid elapsed_seconds")
    if raw.get("interrupt_status") != "terminal_confirmed":
        raise TimeoutObservationError("timeout observation lacks terminal interruption proof")
    return {
        "version": TIMEOUT_OBSERVATION_VERSION,
        "lane_id": lane_id,
        "session_id": _identifier(raw.get("session_id"), "session_id"),
        "turn_id": _identifier(raw.get("turn_id"), "turn_id"),
        "turn_timeout_seconds": timeout,
        "elapsed_seconds": elapsed,
        "terminal_status": _status(raw.get("terminal_status"), "terminal_status"),
        "interrupt_status": "terminal_confirmed",
        "item_states": _item_states(raw.get("item_states")),
        "command_states": _command_states(raw.get("command_states")),
        "final_claim_state": _final_claim_state(raw.get("final_claim_state")),
    }
