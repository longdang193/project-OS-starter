"""Durable attempt-bound result contract for native Secretary Codex runs."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from .results import evidence_path_lock

NATIVE_RESULT_SCHEMA = "secretary-native-result.v1"
NATIVE_BINDING_SCHEMA = "secretary-native-binding.v1"
NATIVE_SUBMISSION_SCHEMA = "secretary-native-submission.v1"
NATIVE_RESULT_PRODUCER = "codex-native"
NATIVE_RESULT_AUTHORITY = "lightrsi-codex-context-history"
NATIVE_APP_SERVER_AUTHORITY = "codex-app-server"
NATIVE_RESULT_MAX_BYTES = 64 * 1024
NATIVE_RESULT_CONTENT_SOURCES = frozenset({"lightrsi_completed_turn", "native_app_server_completed_turn"})
NATIVE_RESULT_LEGACY_CONTENT_SOURCES = frozenset({"native_completed_turn"})


class NativeResultConflictError(ValueError):
    """Raised when one attempt is published with conflicting native results."""


def native_result_path(output: Path) -> Path:
    return output.with_name(f"{output.name}.native-result.json")


def native_binding_path(output: Path) -> Path:
    return output.with_name(f"{output.name}.native-binding.json")


def native_submission_path(output: Path) -> Path:
    return output.with_name(f"{output.name}.native-submission.json")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"native result {field} invalid")
    return value.strip()


def _digest(value: object, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"native result {field} invalid")
    return value


def redact_semantic_content(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("native result semantic_content invalid")
    redacted = value
    for secret in tuple(item for item in os.environ.get("SECRETARY_SEMANTIC_SECRETS", "").split(",") if item):
        redacted = redacted.replace(secret, "[REDACTED]")
    redacted = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", redacted)
    redacted = re.sub(
        r"(?i)([\"']?(?:password|authorization|api[_-]?key|apikey|secret|token|access_token)[\"']?\s*[:=]\s*)\"(?:\\.|[^\"\\])*\"",
        r'\1"[REDACTED]"',
        redacted,
    )
    redacted = re.sub(
        r"(?i)([\"']?(?:password|authorization|api[_-]?key|apikey|secret|token|access_token)[\"']?\s*[:=]\s*)'(?:\\.|[^'\\])*'",
        r"\1'[REDACTED]'",
        redacted,
    )
    redacted = re.sub(
        r"(?i)([?&](?:token|access_token|api[_-]?key|apikey|authorization|key|secret)=)[^&#\s]+",
        r"\1[REDACTED]",
        redacted,
    )
    return re.sub(
        r"(?i)([\"']?(?:password|authorization|api[_-]?key|apikey|secret|token|access_token)[\"']?\s*[:=]\s*)([^\"'\s,;}]+)",
        r"\1[REDACTED]",
        redacted,
    )


def _publication_identity(payload: Mapping[str, Any]) -> tuple[object, ...]:
    return (
        payload["attempt_id"],
        payload["native_session_id"],
        payload["native_turn_id"],
        payload.get("turn_seq", payload.get("completion_seq")),
        payload["content_sha256"],
    )


def _validate_binding(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("native binding payload invalid")
    if payload.get("schema") != NATIVE_BINDING_SCHEMA:
        raise ValueError("native binding schema mismatch")
    for field in ("attempt_id", "native_session_id", "created_at"):
        _text(payload.get(field), field)
    if payload.get("pre_submit_boundary") is not None:
        _text(payload.get("pre_submit_boundary"), "pre_submit_boundary")
    elif payload.get("pre_submit_cursor") is not None:
        _text(payload.get("pre_submit_cursor"), "pre_submit_cursor")
    else:
        raise ValueError("native binding pre-submit boundary invalid")
    if payload.get("lightrsi_cli_path") is not None:
        _text(payload.get("lightrsi_cli_path"), "lightrsi_cli_path")
    if payload.get("assignment_id") is not None:
        _text(payload.get("assignment_id"), "assignment_id")
    transport = payload.get("transport")
    if not isinstance(transport, dict):
        raise ValueError("native binding transport invalid")
    for field in ("session", "pane", "agent_name"):
        _text(transport.get(field), f"transport.{field}")
    return dict(payload)


def publish_native_binding(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _validate_binding(dict(payload))
    encoded = (json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > NATIVE_RESULT_MAX_BYTES:
        raise ValueError(f"native binding exceeds {NATIVE_RESULT_MAX_BYTES} bytes")
    digest = hashlib.sha256(encoded).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path_lock(path):
        if path.exists():
            existing = path.read_bytes()
            if existing == encoded:
                return {"state": "idempotent", "path": str(path), "digest": digest}
            raise NativeResultConflictError("native binding conflicts with existing evidence")
        temporary = path.with_name(f".{path.name}.{digest}.tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return {"state": "published", "path": str(path), "digest": digest}


def parse_native_binding(path: Path, *, attempt_id: str) -> dict[str, Any]:
    try:
        if not path.is_file() or path.stat().st_size > NATIVE_RESULT_MAX_BYTES:
            return {"state": "unknown", "detail": "native binding unavailable"}
        payload = _validate_binding(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError:
        return {"state": "unknown", "detail": "native binding unavailable"}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {"state": "unknown", "detail": "native binding malformed"}
    if payload["attempt_id"] != attempt_id:
        return {"state": "unknown", "detail": "native binding attempt mismatch"}
    return {"state": "confirmed", **payload, "binding_reference": str(path)}


def _validate_submission(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != NATIVE_SUBMISSION_SCHEMA:
        raise ValueError("native submission payload invalid")
    for field in ("attempt_id", "native_session_id", "native_thread_id", "native_turn_id", "accepted_at"):
        _text(payload.get(field), field)
    if payload.get("status") != "accepted":
        raise ValueError("native submission status invalid")
    return dict(payload)


def publish_native_submission(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _validate_submission(dict(payload))
    encoded = (json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > NATIVE_RESULT_MAX_BYTES:
        raise ValueError(f"native submission exceeds {NATIVE_RESULT_MAX_BYTES} bytes")
    digest = hashlib.sha256(encoded).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path_lock(path):
        if path.exists():
            existing = path.read_bytes()
            if existing == encoded:
                return {"state": "idempotent", "path": str(path), "digest": digest}
            raise NativeResultConflictError("native submission conflicts with existing evidence")
        temporary = path.with_name(f".{path.name}.{digest}.tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return {"state": "published", "path": str(path), "digest": digest}


def parse_native_submission(path: Path, *, attempt_id: str) -> dict[str, Any]:
    try:
        if not path.is_file() or path.stat().st_size > NATIVE_RESULT_MAX_BYTES:
            return {"state": "unknown", "detail": "native submission unavailable"}
        payload = _validate_submission(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError:
        return {"state": "unknown", "detail": "native submission unavailable"}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {"state": "unknown", "detail": "native submission malformed"}
    if payload["attempt_id"] != attempt_id:
        return {"state": "unknown", "detail": "native submission attempt mismatch"}
    return {"state": "confirmed", **payload, "submission_reference": str(path)}


def _validate_contract(
    payload: object,
    *,
    allow_legacy_content_source: bool,
    require_content_digest: bool,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("native result payload invalid")
    if payload.get("schema") != NATIVE_RESULT_SCHEMA:
        raise ValueError("native result schema mismatch")
    if payload.get("producer") != NATIVE_RESULT_PRODUCER:
        raise ValueError("native result producer invalid")
    for field in (
        "attempt_id",
        "observed_at",
        "native_authority",
        "native_session_id",
        "native_turn_id",
        "content_source",
    ):
        _text(payload.get(field), field)
    for field in ("session", "pane", "agent_name"):
        if payload.get(field) is not None:
            _text(payload.get(field), field)
    _text(payload.get("semantic_content"), "semantic_content")
    if payload.get("native_authority") not in {NATIVE_RESULT_AUTHORITY, NATIVE_APP_SERVER_AUTHORITY}:
        raise ValueError("native result authority invalid")
    content_source = payload.get("content_source")
    allowed_sources = set(NATIVE_RESULT_CONTENT_SOURCES)
    if allow_legacy_content_source:
        allowed_sources.update(NATIVE_RESULT_LEGACY_CONTENT_SOURCES)
    if content_source not in allowed_sources:
        raise ValueError("native result content source invalid")
    if content_source == "lightrsi_completed_turn":
        turn_seq = payload.get("turn_seq")
        if isinstance(turn_seq, bool) or not isinstance(turn_seq, int) or turn_seq < 1:
            raise ValueError("native result turn_seq invalid")
        if payload.get("semantic_complete") is not True:
            raise ValueError("native result semantic completeness missing")
        if payload["native_turn_id"] != f"{payload['native_session_id']}:t{turn_seq}":
            raise ValueError("native result canonical turn id mismatch")
    else:
        completion_seq = payload.get("completion_seq")
        if isinstance(completion_seq, bool) or not isinstance(completion_seq, int) or completion_seq < 1:
            raise ValueError("native result completion_seq invalid")
    for field in ("native_request_id", "native_response_id"):
        if payload.get(field) is not None:
            _text(payload.get(field), field)
    if payload.get("assignment_id") is not None:
        _text(payload.get("assignment_id"), "assignment_id")
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
    if content_sha256 is None and require_content_digest:
        if content_source not in NATIVE_RESULT_LEGACY_CONTENT_SOURCES:
            raise ValueError("native result content digest missing")
    elif content_sha256 is not None and content_sha256 != expected_content_sha256:
        raise ValueError("native result content digest mismatch")
    if content_sha256 is None:
        normalized["content_sha256"] = expected_content_sha256
    return normalized


def normalize_for_publication(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _validate_contract(
        dict(payload),
        allow_legacy_content_source=False,
        require_content_digest=False,
    )
    semantic_content = redact_semantic_content(normalized["semantic_content"])
    normalized["semantic_content"] = semantic_content
    normalized["content_sha256"] = hashlib.sha256(semantic_content.encode("utf-8")).hexdigest()
    return normalized


def validate_persisted_result(payload: object) -> dict[str, Any]:
    return _validate_contract(
        payload,
        allow_legacy_content_source=True,
        require_content_digest=True,
    )


def _encode(payload: Mapping[str, Any]) -> bytes:
    normalized = validate_persisted_result(dict(payload))
    encoded = (json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > NATIVE_RESULT_MAX_BYTES:
        raise ValueError(f"native result exceeds {NATIVE_RESULT_MAX_BYTES} bytes")
    return encoded


def publish_native_result(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_for_publication(payload)
    encoded = _encode(normalized)
    digest = hashlib.sha256(encoded).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path_lock(path):
        if path.exists():
            existing = path.read_bytes()
            if existing == encoded:
                return {"state": "idempotent", "path": str(path), "digest": digest}
            try:
                existing_payload = validate_persisted_result(json.loads(existing.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                raise NativeResultConflictError(
                    "native result publication conflicts with malformed existing evidence"
                ) from exc
            if _publication_identity(existing_payload) == _publication_identity(normalized):
                return {
                    "state": "idempotent",
                    "path": str(path),
                    "digest": hashlib.sha256(existing).hexdigest(),
                }
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
        normalized = validate_persisted_result(payload)
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
    "NATIVE_APP_SERVER_AUTHORITY",
    "NATIVE_RESULT_CONTENT_SOURCES",
    "NATIVE_RESULT_LEGACY_CONTENT_SOURCES",
    "NATIVE_RESULT_SCHEMA",
    "NATIVE_BINDING_SCHEMA",
    "NATIVE_SUBMISSION_SCHEMA",
    "NativeResultConflictError",
    "native_result_path",
    "native_binding_path",
    "native_submission_path",
    "parse_native_binding",
    "parse_native_submission",
    "parse_native_result",
    "publish_native_result",
    "publish_native_binding",
    "publish_native_submission",
    "redact_semantic_content",
    "normalize_for_publication",
    "validate_persisted_result",
]
