"""Durable attempt-bound result contract for native Secretary Codex runs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from .results import evidence_path_lock

NATIVE_RESULT_SCHEMA = "secretary-native-result.v1"
NATIVE_RESULT_PRODUCER = "codex-native"
NATIVE_RESULT_AUTHORITY = "lightrsi-codex-context-history"
NATIVE_RESULT_MAX_BYTES = 64 * 1024


class NativeResultConflictError(ValueError):
    """Raised when one attempt is published with conflicting native results."""


def native_result_path(output: Path) -> Path:
    return output.with_name(f"{output.name}.native-result.json")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"native result {field} invalid")
    return value.strip()


def _digest(value: object, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"native result {field} invalid")
    return value


def _validate(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("native result payload invalid")
    if payload.get("schema") != NATIVE_RESULT_SCHEMA:
        raise ValueError("native result schema mismatch")
    if payload.get("producer") != NATIVE_RESULT_PRODUCER:
        raise ValueError("native result producer invalid")
    for field in (
        "attempt_id",
        "session",
        "pane",
        "agent_name",
        "semantic_content",
        "observed_at",
        "native_authority",
        "native_session_id",
        "native_turn_id",
        "content_source",
    ):
        _text(payload.get(field), field)
    if payload.get("native_authority") != NATIVE_RESULT_AUTHORITY:
        raise ValueError("native result authority invalid")
    if payload.get("content_source") != "native_completed_turn":
        raise ValueError("native result content source invalid")
    if payload["native_session_id"] != payload["session"]:
        raise ValueError("native result session mismatch")
    for field in ("native_request_id", "native_response_id"):
        if payload.get(field) is not None:
            _text(payload.get(field), field)
    if payload.get("assignment_id") is not None:
        _text(payload.get("assignment_id"), "assignment_id")
    completion_seq = payload.get("completion_seq")
    if isinstance(completion_seq, bool) or not isinstance(completion_seq, int) or completion_seq < 0:
        raise ValueError("native result completion_seq invalid")
    if payload.get("freshness_proven") is not True:
        raise ValueError("native result freshness proof missing")
    if payload.get("assistant_owned") is not True:
        raise ValueError("native result assistant ownership missing")
    observed_at = payload["observed_at"]
    try:
        datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("native result observed_at invalid") from exc
    normalized = dict(payload)
    semantic_content = normalized["semantic_content"]
    expected_content_sha256 = hashlib.sha256(semantic_content.encode("utf-8")).hexdigest()
    content_sha256 = normalized.get("content_sha256")
    if content_sha256 is not None and content_sha256 != expected_content_sha256:
        raise ValueError("native result content digest mismatch")
    normalized["content_sha256"] = expected_content_sha256
    return normalized


def _encode(payload: Mapping[str, Any]) -> bytes:
    normalized = _validate(dict(payload))
    encoded = (json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > NATIVE_RESULT_MAX_BYTES:
        raise ValueError(f"native result exceeds {NATIVE_RESULT_MAX_BYTES} bytes")
    return encoded


def publish_native_result(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    encoded = _encode(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path_lock(path):
        if path.exists():
            existing = path.read_bytes()
            if existing == encoded:
                return {"state": "idempotent", "path": str(path), "digest": digest}
            raise NativeResultConflictError("native result publication conflicts with existing evidence")
        temporary = path.with_name(f".{path.name}.{digest}.tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(encoded)
                handle.flush()
                import os

                os.fsync(handle.fileno())
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return {"state": "published", "path": str(path), "digest": digest}


def parse_native_result(path: Path, *, attempt_id: str) -> dict[str, Any]:
    try:
        if not path.is_file() or path.stat().st_size > NATIVE_RESULT_MAX_BYTES:
            return {"state": "unknown", "detail": "native result unavailable"}
        payload = json.loads(path.read_text(encoding="utf-8"))
        normalized = _validate(payload)
    except FileNotFoundError:
        return {"state": "unknown", "detail": "native result unavailable"}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {"state": "unknown", "detail": "native result malformed"}
    if normalized["attempt_id"] != attempt_id:
        return {"state": "unknown", "detail": "native result attempt mismatch"}
    return {
        "state": "confirmed",
        **normalized,
        "result_reference": str(path),
    }


__all__ = [
    "NATIVE_RESULT_PRODUCER",
    "NATIVE_RESULT_AUTHORITY",
    "NATIVE_RESULT_SCHEMA",
    "NativeResultConflictError",
    "native_result_path",
    "parse_native_result",
    "publish_native_result",
]
