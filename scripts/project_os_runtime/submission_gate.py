"""Durable single-owner admission for model-producing submissions."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any

from .results import evidence_path_lock

_GATE_SCHEMA = "project-os.submission-gate.v1"
_GATE_MAX_BYTES = 16 * 1024
_BINDING_FIELDS = (
    "task_sha256",
    "repository_identity",
    "plan_identity",
    "profile",
    "model_identity",
    "grant_digest",
)
_BLOCKING_STATES = {
    "prepared": "submission intent already recorded",
    "submitted": "submission already recorded",
    "delivery_uncertain": "delivery is uncertain",
    "settled": "submission already settled",
}
_ALLOWED_SETTLEMENTS = {"not_delivered", "submitted", "delivery_uncertain", "settled"}
_lock_registry_guard = threading.Lock()
_lock_registry: dict[str, threading.Lock] = {}


class SubmissionGateConflict(RuntimeError):
    """Raised when durable submission evidence cannot be trusted or reused."""


def _text(value: object, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise SubmissionGateConflict(f"submission gate {field} is invalid")
    return value.strip()


def _binding(binding: Mapping[str, object]) -> dict[str, str]:
    if not isinstance(binding, Mapping):
        raise SubmissionGateConflict("submission gate binding is invalid")
    return {
        field: _text(binding.get(field, ""), field, allow_empty=True)
        for field in _BINDING_FIELDS
    }


def derive_logical_operation_id(
    *,
    task_id: str,
    plan_revision: str,
    run_id: str,
) -> str:
    values = {
        "task_id": _text(task_id, "task_id"),
        "plan_revision": _text(plan_revision, "plan_revision"),
        "run_id": _text(run_id, "run_id"),
    }
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"operation-{hashlib.sha256(encoded).hexdigest()}"


def _default_root() -> Path:
    configured = os.environ.get("PROJECT_OS_SUBMISSION_GATE_ROOT")
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "project-os" / "submissions"
    return Path.home() / ".local" / "share" / "project-os" / "submissions"


def gate_path(operation_id: str, *, root: Path | None = None) -> Path:
    operation_id = _text(operation_id, "logical_operation_id")
    digest = hashlib.sha256(operation_id.encode("utf-8")).hexdigest()
    return (root or _default_root()) / f"{digest}.json"


@contextmanager
def _gate_lock(path: Path):
    key = str(path.resolve())
    with _lock_registry_guard:
        lock = _lock_registry.setdefault(key, threading.Lock())
    with lock:
        with evidence_path_lock(path):
            yield


def _read(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        if not path.is_file() or path.stat().st_size > _GATE_MAX_BYTES:
            raise SubmissionGateConflict("submission gate is malformed or oversized")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SubmissionGateConflict("submission gate is unreadable") from exc
    if not isinstance(payload, dict) or payload.get("schema") != _GATE_SCHEMA:
        raise SubmissionGateConflict("submission gate schema mismatch")
    if payload.get("state") not in _BLOCKING_STATES and payload.get("state") != "not_delivered":
        raise SubmissionGateConflict("submission gate state is invalid")
    return payload


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (json.dumps(dict(payload), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > _GATE_MAX_BYTES:
        raise SubmissionGateConflict("submission gate exceeds size limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{hashlib.sha256(encoded).hexdigest()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def claim_submission(
    path: Path,
    *,
    operation_id: str,
    attempt_id: str,
    binding: Mapping[str, object],
) -> dict[str, Any]:
    operation_id = _text(operation_id, "logical_operation_id")
    attempt_id = _text(attempt_id, "attempt_id")
    normalized_binding = _binding(binding)
    with _gate_lock(path):
        existing = _read(path)
        if existing is not None:
            if existing.get("logical_operation_id") != operation_id:
                raise SubmissionGateConflict("submission gate logical operation mismatch")
            if existing.get("binding") != normalized_binding:
                raise SubmissionGateConflict("submission gate binding mismatch")
            state = existing["state"]
            if state in _BLOCKING_STATES:
                return {"state": "blocked", "reason": _BLOCKING_STATES[state], "record": existing}
            generation = int(existing.get("generation", 1)) + 1
        else:
            generation = 1
        record = {
            "schema": _GATE_SCHEMA,
            "logical_operation_id": operation_id,
            "attempt_id": attempt_id,
            "binding": normalized_binding,
            "state": "prepared",
            "generation": generation,
            "created_at": existing.get("created_at", _now()) if existing else _now(),
            "updated_at": _now(),
        }
        _write(path, record)
        return {"state": "claimed", "record": record}


def settle_submission(path: Path, *, attempt_id: str, state: str) -> dict[str, Any]:
    attempt_id = _text(attempt_id, "attempt_id")
    if state not in _ALLOWED_SETTLEMENTS:
        raise SubmissionGateConflict(f"submission gate settlement state is invalid: {state}")
    with _gate_lock(path):
        record = _read(path)
        if record is None:
            raise SubmissionGateConflict("submission gate intent is missing")
        if record.get("attempt_id") != attempt_id:
            raise SubmissionGateConflict("submission gate attempt mismatch")
        updated = {**record, "state": state, "updated_at": _now()}
        _write(path, updated)
        return updated


__all__ = [
    "SubmissionGateConflict",
    "claim_submission",
    "derive_logical_operation_id",
    "gate_path",
    "settle_submission",
]
