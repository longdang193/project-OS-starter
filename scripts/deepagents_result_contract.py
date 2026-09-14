"""Shared contract for dcode-project lifecycle receipts."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any


RESULT_SCHEMA = "dcode-project.result.v1"
RESULT_MAX_BYTES = 16 * 1024
RESULT_MAX_AGE_SECONDS = 3600
WORKER_STATES = frozenset({"exited", "failed", "start_failed", "recovery_blocked"})
CLEANUP_STATES = frozenset({"removed", "preserved", "unverified"})
DESCENDANT_STATES = frozenset({"terminated", "not_started", "unknown"})


def _validate_payload(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("receipt payload invalid")
    if payload.get("schema") != RESULT_SCHEMA:
        raise ValueError("receipt schema mismatch")
    if not isinstance(payload.get("attempt_id"), str) or not payload["attempt_id"]:
        raise ValueError("receipt attempt id invalid")
    worker = payload.get("worker")
    cleanup = payload.get("cleanup")
    if not isinstance(worker, dict) or not isinstance(cleanup, dict):
        raise ValueError("receipt lifecycle fields missing")
    worker_state = worker.get("state")
    if not isinstance(worker_state, str) or worker_state not in WORKER_STATES:
        raise ValueError("receipt worker state invalid")
    cleanup_state = cleanup.get("state")
    if not isinstance(cleanup_state, str) or cleanup_state not in CLEANUP_STATES:
        raise ValueError("receipt cleanup state invalid")
    exit_code = worker.get("exit_code")
    if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
        raise ValueError("receipt exit code invalid")
    if worker_state == "exited" and not isinstance(exit_code, int):
        raise ValueError("receipt exited worker exit code missing")
    descendant_state = worker.get("descendant_state", "unknown")
    if not isinstance(descendant_state, str) or descendant_state not in DESCENDANT_STATES:
        raise ValueError("receipt descendant state invalid")
    recovery_required = payload.get("recovery_required", False)
    if not isinstance(recovery_required, bool):
        raise ValueError("receipt recovery flag invalid")
    remaining_paths = cleanup.get("remaining_paths", [])
    if not isinstance(remaining_paths, list) or not all(
        isinstance(path, str) and path for path in remaining_paths
    ):
        raise ValueError("receipt cleanup paths invalid")
    if cleanup_state == "removed" and remaining_paths:
        raise ValueError("receipt removed cleanup has remaining paths")
    marker_state = cleanup.get("marker_state", "unknown")
    if not isinstance(marker_state, str) or not marker_state:
        raise ValueError("receipt marker state invalid")
    return {
        "worker": worker,
        "cleanup": cleanup,
        "worker_state": worker_state,
        "worker_exit_code": exit_code,
        "descendant_state": descendant_state,
        "cleanup_state": cleanup_state,
        "recovery_required": recovery_required,
        "remaining_paths": remaining_paths,
        "marker_state": marker_state,
    }


def encode_result_receipt(payload: dict[str, Any]) -> bytes:
    _validate_payload(payload)
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    if len(encoded) > RESULT_MAX_BYTES:
        raise RuntimeError(f"dcode-project result receipt exceeds {RESULT_MAX_BYTES} bytes.")
    return encoded


def parse_result_receipt(path: Path, attempt_id: str) -> dict[str, Any]:
    unknown = {"state": "unknown", "detail": "receipt unavailable"}
    try:
        stat = path.stat()
        if (
            not path.is_file()
            or stat.st_size > RESULT_MAX_BYTES
            or time.time() - stat.st_mtime > RESULT_MAX_AGE_SECONDS
        ):
            return unknown
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return unknown
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"state": "unknown", "detail": "receipt malformed"}
    try:
        fields = _validate_payload(payload)
    except ValueError as exc:
        return {"state": "unknown", "detail": str(exc)}
    if payload.get("attempt_id") != attempt_id:
        return {"state": "unknown", "detail": "receipt correlation mismatch"}
    return {
        "state": "confirmed",
        "worker_state": fields["worker_state"],
        "worker_exit_code": fields["worker_exit_code"],
        "descendant_state": fields["descendant_state"],
        "cleanup_state": fields["cleanup_state"],
        "role_views_state": fields["cleanup"].get("role_views_state", fields["cleanup_state"]),
        "remaining_paths": fields["remaining_paths"],
        "marker_state": fields["marker_state"],
        "recovery_required": fields["recovery_required"],
    }
