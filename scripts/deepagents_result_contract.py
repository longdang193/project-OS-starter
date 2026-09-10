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


def encode_result_receipt(payload: dict[str, Any]) -> bytes:
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
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"state": "unknown", "detail": "receipt malformed"}
    if not isinstance(payload, dict) or payload.get("schema") != RESULT_SCHEMA:
        return {"state": "unknown", "detail": "receipt schema mismatch"}
    if payload.get("attempt_id") != attempt_id:
        return {"state": "unknown", "detail": "receipt correlation mismatch"}
    worker = payload.get("worker")
    cleanup = payload.get("cleanup")
    if not isinstance(worker, dict) or not isinstance(cleanup, dict):
        return {"state": "unknown", "detail": "receipt lifecycle fields missing"}
    if worker.get("state") not in WORKER_STATES:
        return {"state": "unknown", "detail": "receipt worker state invalid"}
    if cleanup.get("state") not in CLEANUP_STATES:
        return {"state": "unknown", "detail": "receipt cleanup state invalid"}
    exit_code = worker.get("exit_code")
    if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
        return {"state": "unknown", "detail": "receipt exit code invalid"}
    recovery_required = payload.get("recovery_required", False)
    if not isinstance(recovery_required, bool):
        return {"state": "unknown", "detail": "receipt recovery flag invalid"}
    remaining_paths = cleanup.get("remaining_paths", [])
    if not isinstance(remaining_paths, list) or not all(
        isinstance(path, str) and path for path in remaining_paths
    ):
        return {"state": "unknown", "detail": "receipt cleanup paths invalid"}
    marker_state = cleanup.get("marker_state", "unknown")
    if not isinstance(marker_state, str) or not marker_state:
        return {"state": "unknown", "detail": "receipt marker state invalid"}
    return {
        "state": "confirmed",
        "worker_state": worker["state"],
        "worker_exit_code": exit_code,
        "descendant_state": worker.get("descendant_state"),
        "cleanup_state": cleanup["state"],
        "role_views_state": cleanup.get("role_views_state", cleanup["state"]),
        "remaining_paths": remaining_paths,
        "marker_state": marker_state,
        "recovery_required": recovery_required,
    }
