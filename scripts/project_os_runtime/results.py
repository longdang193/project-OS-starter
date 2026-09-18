"""Shared contract for dcode-project lifecycle receipts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any


RESULT_SCHEMA = "dcode-project.result.v1"
RESULT_MAX_BYTES = 16 * 1024
RESULT_MAX_AGE_SECONDS = 3600
WORKER_STATES = frozenset({"exited", "failed", "start_failed", "recovery_blocked"})
CLEANUP_STATES = frozenset({"removed", "preserved", "unverified"})
DESCENDANT_STATES = frozenset({"terminated", "not_started", "unknown"})
TASK_RESULT_SCHEMA = "dcode-project.task-result.v1"
TASK_RESULT_MAX_BYTES = 16 * 1024
TASK_RESULT_STATUSES = frozenset({"in_progress", "completed", "failed", "blocked", "unknown"})
_CAPABILITY_DIGEST_FIELDS = ("requested", "passed_to_worker", "validated_available")


def _capability_digest(values: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(values, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _capability_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"receipt capability {name} invalid")
    return list(value)


def _capability_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    canonical = payload.get("capabilities")
    compatibility = payload.get("shell_capabilities")
    unavailable = {
        "capability_state": "unavailable",
        "capabilities": None,
        "shell_capabilities": compatibility if isinstance(compatibility, dict) else None,
    }
    if canonical is None and compatibility is None:
        return unavailable
    if not isinstance(canonical, dict):
        return {**unavailable, "capability_detail": "canonical capability evidence missing"}
    try:
        normalized = {
            name: _capability_list(canonical.get(name), name)
            for name in _CAPABILITY_DIGEST_FIELDS
        }
        digest = canonical.get("digest")
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError("receipt capability digest invalid")
        validation_error = canonical.get("validation_error")
        if validation_error is not None and not isinstance(validation_error, str):
            raise ValueError("receipt capability validation error invalid")
        if validation_error is not None:
            raise ValueError(validation_error or "worker capability validation failed")
        if digest != _capability_digest(normalized["validated_available"]):
            raise ValueError("receipt capability digest mismatch")
        if isinstance(compatibility, dict):
            shell_requested = _capability_list(compatibility.get("requested"), "requested")
            shell_available = _capability_list(compatibility.get("available"), "available")
            shell_effective = _capability_list(compatibility.get("effective"), "effective")
            if (
                shell_requested != normalized["requested"]
                or shell_effective != normalized["passed_to_worker"]
                or shell_available != normalized["validated_available"]
            ):
                raise ValueError("receipt capability evidence disagreement")
        elif compatibility is not None:
            raise ValueError("receipt shell capability evidence invalid")
    except ValueError as exc:
        return {**unavailable, "capability_detail": str(exc)}
    return {
        "capability_state": "confirmed",
        "capabilities": {
            **normalized,
            "digest": digest,
            "validation_error": None,
        },
        "shell_capabilities": compatibility if isinstance(compatibility, dict) else None,
    }


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
    if "recovery_required" not in payload:
        raise ValueError("receipt recovery flag missing")
    recovery_required = payload["recovery_required"]
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
        "capability_evidence": _capability_evidence(payload),
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
    capability_evidence = fields["capability_evidence"]
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
        **capability_evidence,
    }


def _task_identity(payload: dict[str, Any]) -> None:
    for name in ("assignment_id", "attempt_id", "producer"):
        if not isinstance(payload.get(name), str) or not payload[name].strip():
            raise ValueError(f"task result {name} invalid")
    for name in ("task_sha256", "grant_digest"):
        value = payload.get(name)
        if not isinstance(value, str) or len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError(f"task result {name} invalid")


def validate_task_result(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("task result payload invalid")
    if payload.get("schema") != TASK_RESULT_SCHEMA:
        raise ValueError("task result schema mismatch")
    _task_identity(payload)
    status = payload.get("status")
    if status not in TASK_RESULT_STATUSES:
        raise ValueError("task result status invalid")
    for name, expected in (
        ("progress", dict),
        ("checkpoint", (dict, type(None))),
        ("remaining_work", list),
        ("verification", (dict, list)),
        ("continuation", dict),
    ):
        if not isinstance(payload.get(name), expected):
            raise ValueError(f"task result {name} invalid")
    if not all(isinstance(item, str) and item for item in payload["remaining_work"]):
        raise ValueError("task result remaining_work invalid")
    accepted = payload.get("accepted")
    if accepted is not None and not isinstance(accepted, bool):
        raise ValueError("task result accepted invalid")
    return dict(payload)


def encode_task_result(payload: dict[str, Any]) -> bytes:
    normalized = validate_task_result(payload)
    normalized.setdefault("accepted", None)
    encoded = (json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    if len(encoded) > TASK_RESULT_MAX_BYTES:
        raise RuntimeError(f"dcode-project task result exceeds {TASK_RESULT_MAX_BYTES} bytes.")
    return encoded


def publish_task_result(path: Path, payload: dict[str, Any]) -> None:
    encoded = encode_task_result(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def parse_task_result(
    path: Path,
    *,
    assignment_id: str,
    attempt_id: str,
    task_sha256: str,
    grant_digest: str,
) -> dict[str, Any]:
    unknown = {
        "state": "unknown",
        "continuation_eligible": False,
        "detail": "task result unavailable",
    }
    try:
        stat = path.stat()
        if not path.is_file() or stat.st_size > TASK_RESULT_MAX_BYTES:
            return unknown
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload = validate_task_result(payload)
    except FileNotFoundError:
        return unknown
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {**unknown, "detail": "task result malformed"}
    expected = {
        "assignment_id": assignment_id,
        "attempt_id": attempt_id,
        "task_sha256": task_sha256,
        "grant_digest": grant_digest,
    }
    if any(payload.get(name) != value for name, value in expected.items()):
        return {**unknown, "detail": "task result identity mismatch"}
    return {
        "state": "confirmed",
        "assignment_id": payload["assignment_id"],
        "attempt_id": payload["attempt_id"],
        "task_sha256": payload["task_sha256"],
        "grant_digest": payload["grant_digest"],
        "producer": payload["producer"],
        "status": payload["status"],
        "progress": payload["progress"],
        "checkpoint": payload["checkpoint"],
        "remaining_work": payload["remaining_work"],
        "verification": payload["verification"],
        "continuation": payload["continuation"],
        "continuation_eligible": False,
        "accepted": payload.get("accepted"),
    }
