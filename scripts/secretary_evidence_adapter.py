"""Assemble sanitized local Secretary evidence without changing upstream runtimes."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

try:
    from scripts.observe_9router_usage import observe_run_usage, observe_window_usage
    from scripts.project_os_runtime.secretary_receipts import validate_live_receipt
except ModuleNotFoundError:
    from observe_9router_usage import observe_run_usage, observe_window_usage
    from project_os_runtime.secretary_receipts import validate_live_receipt


SCHEMA_VERSION = "secretary-local-evidence-v1"
_IDENTITY_KEYS = ("task_id", "plan_revision", "attempt_id", "run_id", "provider")
_PROVIDER_FIELDS = (
    "schema_version", "source", "disposition", "reason", "attribution", "confidence",
    "session_id", "provider", "model", "models", "input_tokens", "output_tokens",
    "total_tokens", "cache_read_input_tokens", "cache_write_input_tokens", "cost",
    "currency", "cost_provenance", "usage_count", "matched_count", "first_timestamp",
    "last_timestamp", "observation_window", "availability", "coverage", "selected_count",
    "measured_count", "excluded_count", "excluded_row_reasons", "metrics",
)
_TARGET_FIELDS = ("session", "pane", "pane_id", "workspace_id", "cwd")
_LAUNCH_FIELDS = (
    "schema_version", "disposition", "evidence_provenance", "failure_kind", "returncode",
    "assignment", "preflight", "post_submit_observation", "runtime_identity", "timestamps",
)


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _mapping(value: object) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _copy_fields(value: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {key: value[key] for key in fields if key in value}


def _identity(value: Mapping[str, Any]) -> dict[str, str]:
    return {key: text for key in _IDENTITY_KEYS if (text := _text(value.get(key))) is not None}


def _join_provider_usage(launcher: Mapping[str, Any], usage: Mapping[str, Any]) -> dict[str, Any]:
    launch_identity = _identity(launcher)
    usage_identity = _identity(usage)
    conflicts = {
        key: {"launcher": launch_identity[key], "provider": usage_identity[key]}
        for key in launch_identity.keys() & usage_identity.keys()
        if launch_identity[key] != usage_identity[key]
    }
    matching_run_key = next(
        (key for key in ("run_id", "attempt_id") if launch_identity.get(key) and launch_identity.get(key) == usage_identity.get(key)),
        None,
    )
    provider_matches = not usage_identity.get("provider") or usage_identity.get("provider") == launch_identity.get("provider")
    if conflicts or not provider_matches:
        state = "mismatch"
    elif matching_run_key:
        state = "matched"
    else:
        state = "unjoined"
    return {
        "state": state,
        "identifier_matched": state == "matched",
        "matching_key": matching_run_key,
        "conflicts": conflicts,
    }


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def load_reusable_target(path: Path) -> dict[str, str]:
    target = load_json(path)
    values = {key: _text(target.get(key)) for key in _TARGET_FIELDS}
    if not values["session"] or values["session"] == "auto" or values["pane"] != "auto":
        raise ValueError("reusable target requires a named session and pane=auto")
    if not values["pane_id"] or not values["workspace_id"] or not values["cwd"]:
        raise ValueError("reusable target requires pane_id, workspace_id, and cwd")
    if not values["pane_id"].startswith(f"{values['workspace_id']}:"):
        raise ValueError("reusable target pane_id must belong to workspace_id")
    return {key: value for key, value in values.items() if value is not None}


def _provider_usage(launcher: Mapping[str, Any], provider: Mapping[str, Any] | None) -> dict[str, Any]:
    if provider is None:
        return {
            "state": "missing",
            "secretary_attributed": False,
            "data": {"disposition": "inconclusive", "reason": "provider_usage_missing"},
        }
    join = _join_provider_usage(launcher, provider)
    receipt = _secretary_receipt(launcher)
    receipt_data = _mapping(receipt.get("data")) if receipt["state"] == "present" else None
    provider_session = _text(provider.get("session_id"))
    receipt_session = _text(receipt_data.get("session_id")) if receipt_data else None
    coverage = provider.get("coverage") if provider.get("coverage") in {"complete", "partial", "unknown"} else "unknown"
    provider_attribution = provider.get("attribution")
    if provider_attribution == "time-window":
        provider_attribution = "window"
    if provider_attribution not in {"request", "session", "attempt", "run", "window", "none"}:
        provider_attribution = "session" if provider_session else "none"
    session_bridge = bool(provider_session and receipt_session and provider_session == receipt_session)
    secretary_attributed = receipt["state"] == "present" and session_bridge and coverage == "complete"
    attribution = provider_attribution
    if secretary_attributed:
        attribution = "run" if _text(receipt_data.get("run_id")) else "attempt"
    return {
        "state": "observed",
        "secretary_attributed": secretary_attributed,
        "availability": provider.get("availability", "inconclusive"),
        "attribution": attribution,
        "coverage": coverage,
        "session_bridge": session_bridge,
        "join": join,
        "data": _copy_fields(provider, _PROVIDER_FIELDS),
        "economics": "run-bound" if secretary_attributed else "partial-unattributed",
    }


def _secretary_receipt(launcher: Mapping[str, Any]) -> dict[str, Any]:
    receipt = _mapping(launcher.get("receipt"))
    if receipt and receipt.get("valid") is True and receipt.get("evidence_provenance") == "live-attributed":
        try:
            return {"state": "present", "data": validate_live_receipt(receipt)}
        except ValueError:
            pass
    return {"state": "missing", "reason": "runtime_structured_receipt_missing"}


def build_evidence_bundle(
    launcher: Mapping[str, Any],
    *,
    target: Mapping[str, Any] | None = None,
    provider: Mapping[str, Any] | None = None,
    herdr: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    receipt = _secretary_receipt(launcher)
    launch = _copy_fields(launcher, _LAUNCH_FIELDS)
    provider_usage = _provider_usage(launcher, provider)
    if provider is None:
        embedded_provider = _mapping(launcher.get("provider_telemetry"))
        if embedded_provider:
            provider_usage = _provider_usage(launcher, embedded_provider)
    return {
        "schema_version": SCHEMA_VERSION,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "identity": _identity(launcher),
        "launcher_evidence": launch,
        "provider_usage": provider_usage,
        "herdr_evidence": dict(herdr) if herdr else {},
        "probe_target": {
            "reuse": True,
            "selector": _copy_fields(target, ("session", "pane")) if target else {},
            "recorded_target": _copy_fields(target, ("pane_id", "workspace_id", "cwd")) if target else {},
        },
        "secretary_receipt": receipt,
        "readiness": "READY" if launch.get("disposition") == "READY" and receipt["state"] == "present" else "BLOCKED_CAPABILITY",
    }


def collect_provider_usage(
    database: Path,
    *,
    start: str,
    end: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    if session_id:
        return observe_run_usage(database, start=start, end=end, expected_session_id=session_id)
    return observe_window_usage(database, start=start, end=end)


def check_herdr(herdr: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [herdr, "status", "server"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"state": "inconclusive", "reason": type(exc).__name__}
    output = f"{completed.stdout}\n{completed.stderr}".casefold()
    return {"state": "ready" if completed.returncode == 0 and "status: running" in output else "unavailable"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launcher-json", type=Path, required=True)
    parser.add_argument("--target-json", type=Path)
    parser.add_argument("--provider-json", type=Path)
    parser.add_argument("--provider-db", type=Path)
    parser.add_argument("--provider-start")
    parser.add_argument("--provider-end")
    parser.add_argument("--provider-session-id")
    parser.add_argument("--herdr", default="herdr")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    launcher = load_json(args.launcher_json)
    target = load_reusable_target(args.target_json) if args.target_json else None
    provider = load_json(args.provider_json) if args.provider_json else None
    if args.provider_db:
        if not args.provider_start or not args.provider_end:
            parser.error("--provider-db requires --provider-start and --provider-end")
        provider = collect_provider_usage(
            args.provider_db,
            start=args.provider_start,
            end=args.provider_end,
            session_id=args.provider_session_id,
        )
    bundle = build_evidence_bundle(
        launcher,
        target=target,
        provider=provider,
        herdr=check_herdr(args.herdr),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(bundle, sort_keys=True))
    return 0 if bundle["readiness"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
