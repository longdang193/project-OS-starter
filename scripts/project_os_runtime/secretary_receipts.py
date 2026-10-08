from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any, Mapping


SECRETARY_PROVIDER = "9router"
REQUIRED_BINDINGS = (
    "pair_id",
    "arm",
    "run_id",
    "attempt_id",
    "task_id",
    "plan_revision",
    "repository_identity",
    "plan_identity",
    "git_revision",
    "worktree",
    "workstream",
    "checkpoint",
)
REQUIRED_TIMESTAMP_KEYS = (
    "run_started",
    "cos_entry",
    "secretary_entry",
    "worker_entry",
    "publication",
    "settlement",
    "acceptance",
    "secretary_exit",
    "cos_exit",
    "run_finished",
)
REQUIRED_METRIC_KEYS = (
    "cos_turns",
    "secretary_turns",
    "human_interventions",
    "publication_success",
    "settlement_proven",
    "acceptance_decision",
    "token_usage",
    "cost",
)
_SENSITIVE_KEY = re.compile(
    r"(?:^|[_-])(?:authorization|api[_-]?key|password|secret|cookie|credential|raw[_-]?(?:body|header|response))$",
    re.IGNORECASE,
)


class ReceiptValidationError(ValueError):
    pass


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReceiptValidationError(f"{label} must be non-empty text")
    return value.strip()


def _timestamp(value: object, label: str) -> datetime | None:
    if value is None:
        return None
    text = _text(value, label).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ReceiptValidationError(f"{label} must be ISO-8601") from exc


def _reject_sensitive(value: object, path: str = "receipt") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if _SENSITIVE_KEY.search(key_text):
                raise ReceiptValidationError(f"sensitive field present: {path}.{key_text}")
            _reject_sensitive(child, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_sensitive(child, f"{path}[{index}]")


def build_live_receipt(
    *,
    binding: Mapping[str, Any],
    runtime: Mapping[str, Any],
    timestamps: Mapping[str, Any],
    metrics: Mapping[str, Any],
    sources: Mapping[str, Any],
) -> dict[str, Any]:
    receipt = {
        "schema_version": "secretary-live-runtime-receipt-v1",
        **dict(binding),
        "provider": runtime.get("provider"),
        "model": runtime.get("model"),
        "controller_id": runtime.get("controller_id"),
        "session_id": runtime.get("session_id"),
        "timestamps": dict(timestamps),
        "metrics": dict(metrics),
        "sources": dict(sources),
    }
    return receipt


def validate_live_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise ReceiptValidationError("receipt must be an object")
    _reject_sensitive(receipt)
    for field in REQUIRED_BINDINGS:
        _text(receipt.get(field), field)
    if receipt.get("provider") != SECRETARY_PROVIDER:
        raise ReceiptValidationError(f"provider must be {SECRETARY_PROVIDER}")
    _text(receipt.get("model"), "model")
    _text(receipt.get("controller_id"), "controller_id")
    _text(receipt.get("session_id"), "session_id")

    timestamps = receipt.get("timestamps")
    if not isinstance(timestamps, Mapping):
        raise ReceiptValidationError("timestamps must be an object")
    parsed = []
    for field in REQUIRED_TIMESTAMP_KEYS:
        parsed_value = _timestamp(timestamps.get(field), f"timestamps.{field}")
        if parsed_value is not None:
            parsed.append((field, parsed_value))
    for (left_name, left), (right_name, right) in zip(parsed, parsed[1:]):
        if right < left:
            raise ReceiptValidationError(f"timestamps are not monotonic: {left_name}, {right_name}")

    metrics = receipt.get("metrics")
    if not isinstance(metrics, Mapping):
        raise ReceiptValidationError("metrics must be an object")
    for field in REQUIRED_METRIC_KEYS:
        if field not in metrics:
            raise ReceiptValidationError(f"missing metrics.{field}")
    for field in ("cos_turns", "secretary_turns", "human_interventions"):
        value = metrics[field]
        if value != "unknown" and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            raise ReceiptValidationError(f"metrics.{field} must be non-negative integer or unknown")
    for field in ("token_usage", "cost"):
        value = metrics[field]
        if value != "unknown" and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
            raise ReceiptValidationError(f"metrics.{field} must be non-negative number or unknown")
    if metrics["publication_success"] not in (True, False, "unknown"):
        raise ReceiptValidationError("metrics.publication_success must be boolean or unknown")
    if metrics["settlement_proven"] not in (True, False, "unknown"):
        raise ReceiptValidationError("metrics.settlement_proven must be boolean or unknown")
    _text(metrics["acceptance_decision"], "metrics.acceptance_decision")

    sources = receipt.get("sources")
    if not isinstance(sources, Mapping) or not sources:
        raise ReceiptValidationError("sources must be a non-empty object")
    for name, source in sources.items():
        if not isinstance(source, Mapping):
            raise ReceiptValidationError(f"sources.{name} must be an object")
        _text(source.get("producer"), f"sources.{name}.producer")
        for field in REQUIRED_BINDINGS + ("provider", "model"):
            if field in source and source[field] != receipt.get(field):
                raise ReceiptValidationError(f"sources.{name}.{field} mismatch")

    normalized = json.loads(json.dumps(receipt))
    normalized["valid"] = True
    normalized["evidence_provenance"] = "live-attributed"
    return normalized


__all__ = [
    "REQUIRED_BINDINGS",
    "REQUIRED_METRIC_KEYS",
    "REQUIRED_TIMESTAMP_KEYS",
    "ReceiptValidationError",
    "build_live_receipt",
    "validate_live_receipt",
]
