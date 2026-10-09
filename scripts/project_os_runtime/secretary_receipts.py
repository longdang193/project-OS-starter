"""Validation and sanitization for live Secretary receipts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


LIVE_RECEIPT_SCHEMA = "project-os.secretary-live-receipt.v1"
READY = "READY"
BLOCKED_CAPABILITY = "BLOCKED_CAPABILITY"
_STATUSES = {READY, BLOCKED_CAPABILITY}
_SENSITIVE_KEYS = {
    "api_key",
    "auth",
    "authorization",
    "credential",
    "error",
    "password",
    "prompt",
    "raw_transport_body",
    "secret",
    "token",
}
_REQUIRED_FIELDS = (
    "schema",
    "status",
    "task_id",
    "plan_revision",
    "attempt_id",
    "run_id",
    "provider",
    "model",
    "timestamps",
    "completion",
    "provenance",
    "metrics",
    "outcomes",
)


class ReceiptValidationError(ValueError):
    """Raised when a receipt cannot prove live, bound runtime evidence."""


def _required_string(payload: Mapping[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ReceiptValidationError(f"receipt {name} invalid")
    return value.strip()


def _is_sensitive(key: str) -> bool:
    lowered = key.casefold()
    return lowered in _SENSITIVE_KEYS or lowered.endswith(("_secret", "_credential", "_password"))


def sanitize_receipt(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): sanitize_receipt(item)
            for key, item in value.items()
            if not _is_sensitive(str(key))
        }
    if isinstance(value, list):
        return [sanitize_receipt(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_receipt(item) for item in value]
    return value


def validate_live_receipt(
    payload: Mapping[str, Any],
    *,
    expected: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ReceiptValidationError("receipt must be an object")
    if any(field not in payload for field in _REQUIRED_FIELDS):
        raise ReceiptValidationError("receipt required fields missing")
    if payload.get("schema") != LIVE_RECEIPT_SCHEMA:
        raise ReceiptValidationError("receipt schema unsupported")
    status = payload.get("status")
    if status not in _STATUSES:
        raise ReceiptValidationError("receipt status invalid")
    for field in ("task_id", "plan_revision", "attempt_id", "run_id", "provider", "model"):
        _required_string(payload, field)
    if expected:
        for field, value in expected.items():
            if payload.get(field) != value:
                raise ReceiptValidationError(f"receipt {field} mismatch")
    timestamps = payload["timestamps"]
    if not isinstance(timestamps, Mapping) or not _required_string(timestamps, "entry_at"):
        raise ReceiptValidationError("receipt timestamps invalid")
    exit_at = timestamps.get("exit_at")
    if exit_at is not None and (not isinstance(exit_at, str) or not exit_at.strip()):
        raise ReceiptValidationError("receipt exit timestamp invalid")
    completion = payload["completion"]
    if not isinstance(completion, Mapping) or not isinstance(completion.get("observed"), bool):
        raise ReceiptValidationError("receipt completion evidence invalid")
    if status == READY and completion["observed"] is not True:
        raise ReceiptValidationError("ready receipt lacks observed completion")
    provenance = payload["provenance"]
    if not isinstance(provenance, Mapping):
        raise ReceiptValidationError("receipt provenance invalid")
    if provenance.get("source_type") != "runtime" or provenance.get("observed") is not True:
        raise ReceiptValidationError("receipt provenance is not independently observed")
    _required_string(provenance, "producer")
    _required_string(provenance, "source_ref")
    metrics = payload["metrics"]
    if not isinstance(metrics, Mapping):
        raise ReceiptValidationError("receipt metrics invalid")
    for name in ("cos_turns", "secretary_turns", "human_interventions"):
        value = metrics.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ReceiptValidationError(f"receipt metric {name} invalid")
    for name in ("token_usage", "cost"):
        value = metrics.get(name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
            raise ReceiptValidationError(f"receipt metric {name} invalid")
    if not isinstance(payload["outcomes"], Mapping):
        raise ReceiptValidationError("receipt outcomes invalid")
    return sanitize_receipt(dict(payload))


def receipt_digest(payload: Mapping[str, Any]) -> str:
    sanitized = validate_live_receipt(payload)
    encoded = json.dumps(sanitized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "BLOCKED_CAPABILITY",
    "LIVE_RECEIPT_SCHEMA",
    "READY",
    "ReceiptValidationError",
    "receipt_digest",
    "sanitize_receipt",
    "validate_live_receipt",
]
