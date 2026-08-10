from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from .compatibility import TERMINAL_OBSERVATION_VERSION


class TerminalObservationError(ValueError):
    pass


_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = {
    "version",
    "kind",
    "source",
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
    "error",
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
_COMMAND_OPTIONAL_FIELDS = {"observed_elapsed_seconds"}
_ERROR_FIELDS = {"field_names", "code_hash", "code_length", "message_hash", "message_length"}
_FINAL_STATES = {"missing", "unverified", "valid"}
_SOURCE_BY_KIND = {
    "timeout": "host_timeout_interrupt",
    "provider_failure": "provider_terminal",
    "approval_required": "approval_request",
    "protocol_failure": "transport_exception",
}
MAX_TERMINAL_OBSERVATION_ITEMS = 16
_MAX_ERROR_FIELDS = 8
_MAX_LENGTH = 1_000_000
_HOST_V2_FIELDS = {
    "schema_id",
    "observation_id",
    "run_id",
    "attempt_id",
    "packet_sha256",
    "lease_id",
    "lease_epoch",
    "host_instance_id",
    "lane_id",
    "source",
    "observed_at",
    "elapsed_seconds",
    "provider_session_id",
    "provider_turn_id",
    "terminal_status",
    "item_states",
    "command_states",
    "final_claim_state",
    "error",
    "containment",
    "stop_proof",
}
_HOST_V2_SOURCES = {
    "completed": "completed",
    "provider_failure": "failed",
    "timeout": "timed_out",
    "cancellation": "cancelled",
    "host_crash_absence": "absent",
    "stranded_recovery_absence": "absent",
}
_PROCESS_FIELDS = {"pid", "creation_id"}
_CONTAINMENT_FIELDS = {"state", "job_id", "root_processes", "active_process_count", "termination_action"}
_STOP_PROOF_FIELDS = {"state", "observed_at", "host_process", "cancellation_request_id"}


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise TerminalObservationError(f"terminal observation has invalid {field}")
    return value


def _status(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise TerminalObservationError(f"terminal observation has invalid {field}")
    return value


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise TerminalObservationError(f"terminal observation has invalid {field}")
    return value


def _length(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= _MAX_LENGTH:
        raise TerminalObservationError(f"terminal observation has invalid {field}")
    return value


def _elapsed(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= _MAX_LENGTH:
        raise TerminalObservationError(f"terminal observation has invalid {field}")
    return float(value)


def _optional_identifier(value: Any, field: str) -> str | None:
    return None if value is None else _identifier(value, field)


def _optional_status(value: Any, field: str) -> str | None:
    return None if value is None else _status(value, field)


def _item_states(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > MAX_TERMINAL_OBSERVATION_ITEMS:
        raise TerminalObservationError("terminal observation has invalid item_states")
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != _ITEM_FIELDS:
            raise TerminalObservationError("terminal observation has invalid item_states")
        normalized.append({
            "item_id": _identifier(item.get("item_id"), "item_states.item_id"),
            "type": _status(item.get("type"), "item_states.type"),
            "state": _status(item.get("state"), "item_states.state"),
        })
    return normalized


def _command_states(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > MAX_TERMINAL_OBSERVATION_ITEMS:
        raise TerminalObservationError("terminal observation has invalid command_states")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or not (_COMMAND_FIELDS <= set(item) <= _COMMAND_FIELDS | _COMMAND_OPTIONAL_FIELDS):
            raise TerminalObservationError("terminal observation has invalid command_states")
        exit_code = item.get("exit_code")
        if exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
            raise TerminalObservationError("terminal observation has invalid command_states.exit_code")
        record = {
            "item_id": _identifier(item.get("item_id"), "command_states.item_id"),
            "state": _status(item.get("state"), "command_states.state"),
            "command_hash": _hash(item.get("command_hash"), "command_states.command_hash"),
            "command_length": _length(item.get("command_length"), "command_states.command_length"),
            "response_hash": _hash(item.get("response_hash"), "command_states.response_hash"),
            "response_length": _length(item.get("response_length"), "command_states.response_length"),
            "exit_code": exit_code,
        }
        if "observed_elapsed_seconds" in item:
            record["observed_elapsed_seconds"] = _elapsed(
                item.get("observed_elapsed_seconds"), "command_states.observed_elapsed_seconds"
            )
        normalized.append(record)
    return normalized


def _final_claim_state(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("state"), str):
        raise TerminalObservationError("terminal observation has invalid final_claim_state")
    state = value["state"]
    if state not in _FINAL_STATES:
        raise TerminalObservationError("terminal observation has invalid final_claim_state")
    if state == "missing":
        if set(value) != {"state"}:
            raise TerminalObservationError("terminal observation has invalid final_claim_state")
        return {"state": state}
    allowed = {"state", "response_hash", "response_length", "observed_elapsed_seconds"}
    if not {"state", "response_hash", "response_length"} <= set(value) <= allowed:
        raise TerminalObservationError("terminal observation has invalid final_claim_state")
    normalized = {
        "state": state,
        "response_hash": _hash(value.get("response_hash"), "final_claim_state.response_hash"),
        "response_length": _length(value.get("response_length"), "final_claim_state.response_length"),
    }
    if "observed_elapsed_seconds" in value:
        normalized["observed_elapsed_seconds"] = _elapsed(
            value.get("observed_elapsed_seconds"), "final_claim_state.observed_elapsed_seconds"
        )
    return normalized


def _error(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _ERROR_FIELDS:
        raise TerminalObservationError("terminal observation has invalid error")
    field_names = value.get("field_names")
    if (
        not isinstance(field_names, list)
        or len(field_names) > _MAX_ERROR_FIELDS
        or any(not isinstance(name, str) or not _IDENTIFIER.fullmatch(name) for name in field_names)
        or field_names != sorted(set(field_names))
    ):
        raise TerminalObservationError("terminal observation has invalid error.field_names")
    normalized: dict[str, Any] = {"field_names": field_names}
    for prefix in ("code", "message"):
        digest = value.get(f"{prefix}_hash")
        length = value.get(f"{prefix}_length")
        if digest is None and length is None:
            normalized[f"{prefix}_hash"] = None
            normalized[f"{prefix}_length"] = None
            continue
        normalized[f"{prefix}_hash"] = _hash(digest, f"error.{prefix}_hash")
        normalized[f"{prefix}_length"] = _length(length, f"error.{prefix}_length")
    return normalized


def _packet_lane(packet: dict[str, Any], lane_id: str) -> None:
    lanes = packet.get("lanes")
    lane_ids = {lane.get("lane_id") for lane in lanes if isinstance(lane, dict)} if isinstance(lanes, list) else set()
    checks = packet.get("checks")
    check_lane = lane_id.startswith("check:") and isinstance(checks, dict) and lane_id[6:] in checks
    if lane_id not in lane_ids and not check_lane:
        raise TerminalObservationError("terminal observation lane_id conflicts with packet")


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise TerminalObservationError(f"terminal observation has invalid {field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TerminalObservationError(f"terminal observation has invalid {field}") from exc
    if parsed.tzinfo is None:
        raise TerminalObservationError(f"terminal observation has invalid {field}")
    return value


def _process(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _PROCESS_FIELDS:
        raise TerminalObservationError(f"terminal observation has invalid {field}")
    pid = value.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise TerminalObservationError(f"terminal observation has invalid {field}.pid")
    return {"pid": pid, "creation_id": _identifier(value.get("creation_id"), f"{field}.creation_id")}


def _containment(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _CONTAINMENT_FIELDS:
        raise TerminalObservationError("terminal observation has invalid containment")
    roots = value.get("root_processes")
    count = value.get("active_process_count")
    state = value.get("state")
    action = value.get("termination_action")
    if not isinstance(roots, list) or not isinstance(count, int) or isinstance(count, bool) or count != 0:
        raise TerminalObservationError("terminal observation has incomplete containment proof")
    if state == "not_started":
        if roots or action != "none":
            raise TerminalObservationError("terminal observation has incomplete containment proof")
    elif state == "stopped":
        if not 1 <= len(roots) <= MAX_TERMINAL_OBSERVATION_ITEMS or action not in {"none", "job_terminated", "host_handle_closed", "external_cleanup"}:
            raise TerminalObservationError("terminal observation has incomplete containment proof")
    else:
        raise TerminalObservationError("terminal observation has incomplete containment proof")
    if action not in {"none", "job_terminated", "host_handle_closed", "external_cleanup"}:
        raise TerminalObservationError("terminal observation has invalid containment termination_action")
    return {
        "state": state,
        "job_id": _identifier(value.get("job_id"), "containment.job_id"),
        "root_processes": [_process(item, "containment.root_processes") for item in roots],
        "active_process_count": 0,
        "termination_action": action,
    }


def _stop_proof(value: Any, source: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _STOP_PROOF_FIELDS or value.get("state") != "confirmed":
        raise TerminalObservationError("terminal observation has invalid stop_proof")
    cancellation_request_id = value.get("cancellation_request_id")
    if source == "cancellation":
        cancellation_request_id = _identifier(cancellation_request_id, "stop_proof.cancellation_request_id")
    elif cancellation_request_id is not None:
        raise TerminalObservationError("terminal observation has invalid stop_proof.cancellation_request_id")
    return {
        "state": "confirmed",
        "observed_at": _timestamp(value.get("observed_at"), "stop_proof.observed_at"),
        "host_process": _process(value.get("host_process"), "stop_proof.host_process"),
        "cancellation_request_id": cancellation_request_id,
    }


def normalize_host_terminal_observation(
    raw: Any,
    packet: dict[str, Any],
    *,
    binding: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != _HOST_V2_FIELDS:
        raise TerminalObservationError("terminal observation has unsupported fields")
    required_binding = {"run_id", "attempt_id", "packet_sha256", "lease_id", "lease_epoch", "host_instance_id"}
    if not isinstance(binding, dict) or set(binding) != required_binding:
        raise TerminalObservationError("terminal observation has invalid binding")
    normalized_binding = {
        "run_id": _identifier(binding.get("run_id"), "binding.run_id"),
        "attempt_id": _identifier(binding.get("attempt_id"), "binding.attempt_id"),
        "packet_sha256": _hash(binding.get("packet_sha256"), "binding.packet_sha256"),
        "lease_id": _identifier(binding.get("lease_id"), "binding.lease_id"),
        "lease_epoch": _length(binding.get("lease_epoch"), "binding.lease_epoch"),
        "host_instance_id": _identifier(binding.get("host_instance_id"), "binding.host_instance_id"),
    }
    if normalized_binding["lease_epoch"] == 0:
        raise TerminalObservationError("terminal observation has invalid binding.lease_epoch")
    lease = packet.get("execution_lease")
    if (
        not isinstance(lease, dict)
        or not isinstance(lease.get("execution_lease_seconds"), int)
        or isinstance(lease["execution_lease_seconds"], bool)
        or lease["execution_lease_seconds"] <= 0
    ):
        raise TerminalObservationError("packet execution lease is invalid")
    if raw.get("schema_id") != "host_terminal_observation/v2":
        raise TerminalObservationError("terminal observation has unsupported schema_id")
    for field, expected in normalized_binding.items():
        if raw.get(field) != expected:
            raise TerminalObservationError(f"terminal observation conflicts with {field}")
    source = raw.get("source")
    if source not in _HOST_V2_SOURCES or raw.get("terminal_status") != _HOST_V2_SOURCES[source]:
        raise TerminalObservationError("terminal observation has invalid source or terminal_status")
    lane_id = _identifier(raw.get("lane_id"), "lane_id")
    _packet_lane(packet, lane_id)
    elapsed = raw.get("elapsed_seconds")
    if (
        not isinstance(elapsed, (int, float))
        or isinstance(elapsed, bool)
        or not 0 <= elapsed <= lease["execution_lease_seconds"]
    ):
        raise TerminalObservationError("terminal observation has invalid elapsed_seconds")
    session_id = _optional_identifier(raw.get("provider_session_id"), "provider_session_id")
    turn_id = _optional_identifier(raw.get("provider_turn_id"), "provider_turn_id")
    if (session_id is None) != (turn_id is None):
        raise TerminalObservationError("terminal observation has incomplete provider identity")
    containment = _containment(raw.get("containment"))
    if source in {"completed", "timeout", "cancellation"} and (session_id is None or turn_id is None):
        raise TerminalObservationError("terminal observation lacks provider identity")
    if source == "completed" and containment["state"] != "stopped":
        raise TerminalObservationError("terminal observation has incomplete containment proof")
    if source != "provider_failure" and containment["state"] == "not_started":
        raise TerminalObservationError("terminal observation has incomplete containment proof")
    return {
        "schema_id": "host_terminal_observation/v2",
        "observation_id": _identifier(raw.get("observation_id"), "observation_id"),
        **normalized_binding,
        "lane_id": lane_id,
        "source": source,
        "observed_at": _timestamp(raw.get("observed_at"), "observed_at"),
        "elapsed_seconds": float(elapsed),
        "provider_session_id": session_id,
        "provider_turn_id": turn_id,
        "terminal_status": raw["terminal_status"],
        "item_states": _item_states(raw.get("item_states")),
        "command_states": _command_states(raw.get("command_states")),
        "final_claim_state": _final_claim_state(raw.get("final_claim_state")),
        "error": _error(raw.get("error")),
        "containment": containment,
        "stop_proof": _stop_proof(raw.get("stop_proof"), source),
    }


def normalize_terminal_observation(raw: Any, packet: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != _FIELDS:
        raise TerminalObservationError("terminal observation has unsupported fields")
    if raw.get("version") != TERMINAL_OBSERVATION_VERSION:
        raise TerminalObservationError("terminal observation has unsupported version")
    kind = raw.get("kind")
    source = raw.get("source")
    if kind not in _SOURCE_BY_KIND or source != _SOURCE_BY_KIND[kind]:
        raise TerminalObservationError("terminal observation has invalid kind or source")
    lane_id = _identifier(raw.get("lane_id"), "lane_id")
    _packet_lane(packet, lane_id)
    budget = packet.get("execution_budget")
    timeout = budget.get("turn_timeout_seconds") if isinstance(budget, dict) else None
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise TerminalObservationError("packet execution budget is invalid")
    elapsed = raw.get("elapsed_seconds")
    if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or not 0 <= elapsed <= timeout + 30:
        raise TerminalObservationError("terminal observation has invalid elapsed_seconds")
    session_id = _optional_identifier(raw.get("session_id"), "session_id")
    turn_id = _optional_identifier(raw.get("turn_id"), "turn_id")
    terminal_status = _optional_status(raw.get("terminal_status"), "terminal_status")
    observation_timeout = raw.get("turn_timeout_seconds")
    interrupt_status = raw.get("interrupt_status")
    if kind == "timeout":
        if session_id is None or turn_id is None or terminal_status is None:
            raise TerminalObservationError("timeout observation lacks terminal interruption proof")
        if observation_timeout != timeout:
            raise TerminalObservationError("timeout observation conflicts with packet execution budget")
        if interrupt_status != "terminal_confirmed":
            raise TerminalObservationError("timeout observation lacks terminal interruption proof")
    else:
        if observation_timeout is not None or interrupt_status is not None:
            raise TerminalObservationError("terminal observation has invalid timeout fields")
        if kind == "provider_failure" and (session_id is None or turn_id is None or terminal_status is None):
            raise TerminalObservationError("provider failure lacks terminal identity")
        if kind == "approval_required" and (session_id is None or turn_id is None or terminal_status is not None):
            raise TerminalObservationError("approval observation has invalid terminal identity")
        if kind == "protocol_failure" and ((session_id is None) != (turn_id is None) or terminal_status is not None):
            raise TerminalObservationError("protocol observation has invalid terminal identity")
    return {
        "version": TERMINAL_OBSERVATION_VERSION,
        "kind": kind,
        "source": source,
        "lane_id": lane_id,
        "session_id": session_id,
        "turn_id": turn_id,
        "turn_timeout_seconds": observation_timeout,
        "elapsed_seconds": elapsed,
        "terminal_status": terminal_status,
        "interrupt_status": interrupt_status,
        "item_states": _item_states(raw.get("item_states")),
        "command_states": _command_states(raw.get("command_states")),
        "final_claim_state": _final_claim_state(raw.get("final_claim_state")),
        "error": _error(raw.get("error")),
    }
