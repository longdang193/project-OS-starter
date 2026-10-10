"""Run one bounded, supervised Secretary attempt through Herdr and Codex."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import sqlite3
import tomllib
from typing import Any, Mapping

try:
    from scripts.herdr_main_launcher import (
        CommandTransportTimeout,
        _codex_completion_snapshot,
        _run as _herdr_run,
    )
except ModuleNotFoundError:
    from herdr_main_launcher import (
        CommandTransportTimeout,
        _codex_completion_snapshot,
        _run as _herdr_run,
    )

try:
    from project_os_runtime.secretary_economics import normalize_response_usage
    from project_os_runtime.secretary_receipts import (
        SOURCE_PRODUCERS,
        build_live_receipt,
        validate_live_receipt,
    )
except ModuleNotFoundError:
    from scripts.project_os_runtime.secretary_economics import normalize_response_usage
    from scripts.project_os_runtime.secretary_receipts import (
        SOURCE_PRODUCERS,
        build_live_receipt,
        validate_live_receipt,
    )

try:
    from scripts.observe_9router_usage import observe_window_usage
except ModuleNotFoundError:
    from observe_9router_usage import observe_window_usage


SECRETARY_PROVIDER = "9router"
SECRETARY_CONTROLLER = "cos-supervised"
_SAFE_ASSIGNMENT_KEYS = {
    "status",
    "launcher_exit_code",
    "attempt_id",
    "agent_name",
    "failure_kind",
    "reconciliation_required",
}
_RUNTIME_BINDING_KEYS = ("task_id", "plan_revision", "attempt_id", "run_id")
_OBSERVED_TIMESTAMP_KEYS = (
    "run_started", "cos_entry", "secretary_entry", "worker_entry", "publication",
    "settlement", "acceptance", "secretary_exit", "cos_exit", "run_finished",
)
_OBSERVED_METRIC_KEYS = (
    "cos_turns", "secretary_turns", "human_interventions", "publication_success",
    "settlement_proven", "acceptance_decision", "token_usage", "cost",
)
_SOURCE_KEYS = ("launch", "secretary", "task_result", "settlement", "acceptance")
_SOURCE_SAFE_FIELDS = {
    "producer",
    "source_ref", "source_digest",
    "pair_id", "arm", "run_id", "attempt_id", "task_id", "plan_revision",
    "repository_identity", "plan_identity", "git_revision", "worktree",
    "workstream", "checkpoint", "provider", "model", "controller_id", "session_id",
}
_CODEX_OBSERVATION_TIMEOUT_SECONDS = 120.0
_CODEX_OBSERVATION_POLL_SECONDS = 0.5
_PROVIDER_TELEMETRY_LOOKBACK_SECONDS = 0.0
_SAFE_SOURCE_DIGEST = re.compile(r"[0-9a-f]{64}")
_SAFE_SOURCE_VALUE = re.compile(
    r"(?:bearer\s|api[_-]?key|authorization|password|credentials?|cookies?|\bsecret\b|raw(?:[_-]?)(?:body|bodies|header|headers|prompt|prompts|response|responses|transport(?:[_-]?)(?:body|bodies)))",
    re.IGNORECASE,
)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _safe_text(value: object) -> str | None:
    if isinstance(value, str) and not _SAFE_SOURCE_VALUE.search(value):
        return value
    return None


def _safe_assignment(assignment: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(assignment, Mapping):
        return {}
    safe: dict[str, Any] = {}
    for key in _SAFE_ASSIGNMENT_KEYS:
        value = assignment.get(key)
        if key == "launcher_exit_code":
            if isinstance(value, int) and not isinstance(value, bool):
                safe[key] = value
        elif key == "reconciliation_required":
            if isinstance(value, bool):
                safe[key] = value
        else:
            safe_value = _safe_text(value)
            if safe_value is not None:
                safe[key] = safe_value
    return safe


def _launcher_failure_kind(assignment: Mapping[str, Any]) -> str | None:
    failure = assignment.get("failure_kind")
    if not isinstance(failure, str):
        return None
    normalized = failure.casefold()
    if "server_not_running" in normalized:
        return "herdr_server_unavailable"
    if "target_resolution=not_found" in normalized:
        return "target_not_found"
    if "target_resolution=blocked" in normalized:
        return "target_resolution_blocked"
    if "target_resolution=incomplete" in normalized or "transport_timeout" in normalized:
        return "herdr_transport_incomplete"
    return None


@dataclass(frozen=True)
class SecretaryLaunchRequest:
    task_id: str
    plan_revision: str
    attempt_id: str
    run_id: str
    repository_identity: str
    plan_identity: str
    git_revision: str
    worktree: Path
    expected_base: str
    task: str
    codex_home: Path
    provider: str = SECRETARY_PROVIDER
    profile: str = "normal"
    session: str = "auto"
    pane: str = "auto"

    def __post_init__(self) -> None:
        for field in (
            "task_id",
            "plan_revision",
            "attempt_id",
            "run_id",
            "repository_identity",
            "plan_identity",
            "git_revision",
            "expected_base",
            "task",
            "provider",
            "profile",
            "session",
            "pane",
        ):
            _required_text(getattr(self, field), field)
        if self.provider != SECRETARY_PROVIDER:
            raise ValueError(f"Secretary provider must be {SECRETARY_PROVIDER}")


def _bound_task(request: SecretaryLaunchRequest) -> str:
    return (
        f"{request.task}\n\n"
        "Secretary runtime binding (do not modify):\n"
        f"task_id={request.task_id}\n"
        f"plan_revision={request.plan_revision}\n"
        f"attempt_id={request.attempt_id}\n"
        f"run_id={request.run_id}\n"
        f"provider={request.provider}"
    )


def build_launcher_command(request: SecretaryLaunchRequest, *, dry_run: bool = False) -> list[str]:
    launcher = Path(__file__).with_name("herdr_main_launcher.py")
    command = [
        sys.executable,
        str(launcher),
        "--profile",
        request.profile,
        "--session",
        request.session,
        "--pane",
        request.pane,
        "--cwd",
        str(request.worktree),
        "--expected-base",
        request.expected_base,
        "--executor",
        "codex",
        "--task",
        _bound_task(request),
        "--codex-home",
        str(request.codex_home),
        "--repository-identity",
        request.repository_identity,
        "--plan-identity",
        request.plan_identity,
        "--secretary-task-id",
        request.task_id,
        "--secretary-plan-revision",
        request.plan_revision,
        "--secretary-attempt-id",
        request.attempt_id,
        "--secretary-run-id",
        request.run_id,
    ]
    if dry_run:
        command.append("--dry-run")
    return command


def _release_codex_agent(
    herdr: str,
    session: str,
    agent_name: str,
    pane: str,
    *,
    env: dict[str, str],
) -> dict[str, Any]:
    try:
        result = _herdr_run(
            [
                herdr,
                "--session",
                session,
                "agent",
                "send-keys",
                agent_name,
                "ctrl+c",
            ],
            env=env,
            timeout=5.0,
        )
    except CommandTransportTimeout:
        return {"state": "unknown", "error": "release-agent transport timeout"}
    if result.returncode:
        return {"state": "unknown", "error": "agent interruption failed"}
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            get_result = _herdr_run(
                [herdr, "--session", session, "agent", "get", agent_name],
                env=env,
                timeout=1.0,
            )
        except CommandTransportTimeout:
            return {"state": "unknown", "error": "agent retirement observation timed out"}
        if get_result.returncode:
            error_code = None
            for output in (get_result.stdout, get_result.stderr):
                try:
                    payload = json.loads(output)
                except (TypeError, json.JSONDecodeError):
                    continue
                error = payload.get("error") if isinstance(payload, Mapping) else None
                if isinstance(error, Mapping) and isinstance(error.get("code"), str):
                    error_code = error["code"]
                    break
            if error_code == "agent_not_found":
                return {"state": "removed"}
            return {"state": "unknown", "error": "agent retirement observation failed"}
        time.sleep(0.1)
    return {"state": "unknown", "error": "agent retirement not observed"}


def _observe_submitted_codex(
    request: SecretaryLaunchRequest,
    payload: Mapping[str, Any],
    *,
    env: dict[str, str],
) -> dict[str, Any]:
    herdr = payload.get("herdr")
    if not isinstance(herdr, Mapping):
        return {"state": "unknown", "error": "launcher Herdr evidence missing"}
    executable = herdr.get("executable")
    session = herdr.get("session")
    pane = herdr.get("pane")
    agent_name = herdr.get("agent_name")
    if not all(isinstance(value, str) and value.strip() for value in (executable, session, pane, agent_name)):
        return {"state": "unknown", "error": "launcher Codex identity incomplete"}

    deadline = time.monotonic() + _CODEX_OBSERVATION_TIMEOUT_SECONDS
    snapshot: dict[str, Any] = {
        "state": "unknown",
        "observation_error": "completion observation deadline expired",
    }
    while time.monotonic() < deadline:
        remaining = max(0.01, deadline - time.monotonic())
        snapshot = _codex_completion_snapshot(
            executable,
            session,
            agent_name,
            env=env,
            timeout_seconds=min(5.0, remaining),
        )
        if snapshot.get("state") in {"idle", "failed", "stopped"}:
            break
        time.sleep(min(_CODEX_OBSERVATION_POLL_SECONDS, remaining))

    observation = {
        key: snapshot.get(key)
        for key in ("state", "state_change_seq", "output_sha256", "output_chars", "observation_error")
        if key in snapshot
    }
    cleanup: dict[str, Any] = {"state": "not_attempted"}
    if snapshot.get("state") == "idle" and not snapshot.get("observation_error"):
        cleanup = _release_codex_agent(
            executable,
            session,
            agent_name,
            pane,
            env=env,
        )
    observation["cleanup"] = cleanup
    observation["observed_at"] = datetime.now(timezone.utc).isoformat()
    return observation


def _observe_provider_telemetry(start: str, end: str) -> dict[str, Any]:
    candidates: list[Path] = []
    configured = os.environ.get("NINEROUTER_DATABASE")
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.append(Path.home() / "AppData" / "Roaming" / "9router" / "db" / "data.sqlite")
    database = next((path for path in candidates if path.is_file()), None)
    if database is None:
        return {
            "schema_version": "9router-usage-observation-v1",
            "disposition": "inconclusive",
            "source": "9router-local-read-only",
            "attribution": "time-window",
            "reason": "database_unavailable",
        }
    start_at = datetime.fromisoformat(start.replace("Z", "+00:00"))
    padded_start = start_at.isoformat()
    try:
        result = observe_window_usage(database, start=padded_start, end=end)
        result["observation_window"] = {
            "start": padded_start,
            "end": end,
            "lookback_seconds": _PROVIDER_TELEMETRY_LOOKBACK_SECONDS,
        }
        return result
    except (OSError, ValueError, sqlite3.Error) as exc:
        return {
            "schema_version": "9router-usage-observation-v1",
            "disposition": "inconclusive",
            "source": "9router-local-read-only",
            "attribution": "time-window",
            "reason": type(exc).__name__,
        }


def _classify_capabilities(
    disposition: str,
    observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    transport_proven = (
        isinstance(observation, Mapping)
        and observation.get("state") == "idle"
        and isinstance(observation.get("cleanup"), Mapping)
        and observation["cleanup"].get("state") == "removed"
    )
    missing: list[str] = []
    if not transport_proven:
        missing.append("transport_completion_or_cleanup")
    if disposition != "READY":
        missing.append("secretary_runtime_receipt")
    return {
        "transport_evidence": "proven" if transport_proven else "unproven",
        "missing_capabilities": missing,
    }
def _json_payloads(output: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for line in output.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            payloads.append(value)
    return payloads


def select_launcher_payload(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for payload in payloads:
        if any(key in payload for key in ("herdr", "codex", "runtime", "git", "registry_launcher", "assignment", "secretary_runtime")):
            for key in ("herdr", "codex", "runtime", "git", "registry_launcher", "assignment", "secretary_runtime"):
                value = payload.get(key)
                if isinstance(value, Mapping):
                    value = dict(value)
                    if key in selected and selected[key] != value:
                        raise ValueError(f"conflicting launcher evidence for {key}")
                    selected[key] = value
    return selected


def _observed_runtime(payload: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    runtime = payload.get("secretary_runtime") if isinstance(payload, Mapping) else None
    if not isinstance(runtime, Mapping) or runtime.get("observed") is not True:
        return None
    return runtime


def _binding_matches(request: SecretaryLaunchRequest, runtime: Mapping[str, Any], assignment: Mapping[str, Any] | None) -> bool:
    expected = {key: getattr(request, key) for key in _RUNTIME_BINDING_KEYS}
    if any(runtime.get(key) != value for key, value in expected.items()):
        return False
    for field, value in {
        "repository_identity": request.repository_identity,
        "plan_identity": request.plan_identity,
        "git_revision": request.git_revision,
        "worktree": str(request.worktree.resolve()),
        "provider": request.provider,
    }.items():
        if runtime.get(field) != value:
            return False
    if runtime.get("controller_id") != SECRETARY_CONTROLLER:
        return False
    for field in ("model", "session_id"):
        if not isinstance(runtime.get(field), str) or not runtime[field].strip():
            return False
    return not isinstance(assignment, Mapping) or assignment.get("attempt_id") in (None, request.attempt_id)


def _completion_observed(payload: Mapping[str, Any] | None, runtime: Mapping[str, Any] | None) -> bool:
    if runtime is None or not isinstance(payload, Mapping):
        return False
    assignment = payload.get("assignment")
    execution = assignment.get("execution") if isinstance(assignment, Mapping) else None
    task_result = assignment.get("task_result") if isinstance(assignment, Mapping) else None
    return (
        isinstance(assignment, Mapping)
        and assignment.get("status") == "completed"
        and isinstance(execution, Mapping)
        and execution.get("state") == "completed"
        and isinstance(task_result, Mapping)
        and task_result.get("state") == "reported_completed"
        and isinstance(runtime.get("timestamps"), Mapping)
        and isinstance(runtime.get("metrics"), Mapping)
        and isinstance(runtime.get("sources"), Mapping)
        and set(runtime["sources"]) == set(_SOURCE_KEYS)
    )


def _launcher_identity_matches(runtime: Mapping[str, Any], herdr: Mapping[str, Any] | None) -> bool:
    if not isinstance(herdr, Mapping):
        return False
    session = herdr.get("session")
    if isinstance(session, str) and session.strip():
        safe_session = _safe_text(session)
        return safe_session is not None and runtime.get("session_id") == safe_session
    return True


def _launcher_facts_match(
    request: SecretaryLaunchRequest,
    payload: Mapping[str, Any] | None,
    runtime: Mapping[str, Any],
    configured_model: str | None,
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    git = payload.get("git")
    registry = payload.get("registry_launcher")
    if not isinstance(git, Mapping) or not isinstance(registry, Mapping):
        return False
    if git.get("worktree") != str(request.worktree.resolve()) or git.get("repo_root") != str(request.worktree.resolve()):
        return False
    if git.get("expected_base") != request.expected_base:
        return False
    if runtime.get("git_revision") != git.get("head"):
        return False
    if registry.get("repository_identity") != request.repository_identity:
        return False
    if registry.get("plan_identity") != request.plan_identity:
        return False
    if registry.get("attempt_id") != request.attempt_id:
        return False
    if registry.get("model_provider") != request.provider:
        return False
    return configured_model is None or registry.get("model") == configured_model


def _safe_metrics(metrics: Mapping[str, Any] | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    integer_fields = {"cos_turns", "secretary_turns", "human_interventions"}
    boolean_fields = {"publication_success", "settlement_proven"}
    number_fields = {"token_usage", "cost"}
    for field in _OBSERVED_METRIC_KEYS:
        value = metrics.get(field) if isinstance(metrics, Mapping) else None
        if field in integer_fields and isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            result[field] = value
        elif field in boolean_fields and isinstance(value, bool):
            result[field] = value
        elif field == "token_usage":
            result[field] = _safe_token_usage(value)
        elif field == "cost":
            result[field] = _safe_cost(value)
        elif field == "acceptance_decision" and value in {"PASS", "FAIL", "unknown"}:
            result[field] = value
        else:
            result[field] = "unknown"
    return result


def _safe_timestamps(timestamps: Mapping[str, Any] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in _OBSERVED_TIMESTAMP_KEYS:
        value = timestamps.get(field) if isinstance(timestamps, Mapping) else None
        if not isinstance(value, str):
            continue
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        result[field] = value
    return result


def _safe_token_usage(value: object) -> object:
    if value == "unknown":
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return value
    try:
        normalized = normalize_response_usage(value)
    except ValueError:
        return "unknown"
    if not isinstance(normalized, Mapping):
        return "unknown"
    if normalized.get("source") != "response.usage" or normalized.get("confidence") != "observed":
        return "unknown"
    input_tokens = normalized.get("input_tokens")
    output_tokens = normalized.get("output_tokens")
    total_tokens = normalized.get("total_tokens")
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in (input_tokens, output_tokens, total_tokens)):
        return "unknown"
    if input_tokens + output_tokens != total_tokens:
        return "unknown"
    cache_fields = ("cache_read_input_tokens", "cache_write_input_tokens")
    cache_values = {field: normalized.get(field, 0) for field in cache_fields}
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in cache_values.values()):
        return "unknown"
    if sum(cache_values.values()) > input_tokens:
        return "unknown"
    result = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "source": "response.usage",
        "confidence": "observed",
    }
    result.update({field: normalized.get(field) for field in cache_fields if field in normalized})
    return result


def _safe_cost(value: object) -> object:
    if value == "unknown":
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return value
    if not isinstance(value, Mapping):
        return "unknown"
    numeric_value = value.get("value")
    if numeric_value == "unknown":
        reason = _safe_text(value.get("reason"))
        return {"value": "unknown", "reason": reason} if reason is not None else "unknown"
    if value.get("kind") != "estimated":
        return "unknown"
    if isinstance(numeric_value, bool) or not isinstance(numeric_value, (int, float)) or numeric_value < 0:
        return "unknown"
    fields = ("currency", "pricing_source", "pricing_effective_date", "model")
    text_values = {field: _safe_text(value.get(field)) for field in fields}
    if any(text_values[field] is None for field in fields) or value.get("model_resolution") not in {"exact", "requested", "scenario"}:
        return "unknown"
    return {
        "value": numeric_value,
        "kind": "estimated",
        **text_values,
        "model_resolution": value["model_resolution"],
    }


def _safe_runtime_snapshot(
    runtime: Mapping[str, Any],
    expected_values: Mapping[str, str],
) -> dict[str, Any]:
    identity_fields = _RUNTIME_BINDING_KEYS + (
        "repository_identity", "plan_identity", "git_revision", "worktree",
        "provider", "model", "controller_id", "session_id",
    )
    snapshot = {
        key: runtime[key]
        for key in identity_fields
        if key in runtime and runtime.get(key) == expected_values.get(key)
    }
    snapshot["observed"] = runtime.get("observed") is True
    timestamps = runtime.get("timestamps")
    snapshot["timestamps"] = _safe_timestamps(timestamps if isinstance(timestamps, Mapping) else None)
    metrics = runtime.get("metrics")
    snapshot["metrics"] = _safe_metrics(metrics if isinstance(metrics, Mapping) else None)
    sources = runtime.get("sources")
    if isinstance(sources, Mapping):
        def safe_source(name: str, source: Mapping[str, Any]) -> dict[str, Any]:
            safe: dict[str, Any] = {}
            for key in _SOURCE_SAFE_FIELDS:
                value = source.get(key)
                if key == "source_digest":
                    if isinstance(value, str) and _SAFE_SOURCE_DIGEST.fullmatch(value) and set(value) != {"0"}:
                        safe[key] = value
                elif key == "source_ref":
                    if isinstance(value, str) and not _SAFE_SOURCE_VALUE.search(value):
                        safe[key] = value
                elif key == "producer":
                    if isinstance(value, str) and value == SOURCE_PRODUCERS.get(name):
                        safe[key] = value
                elif key in expected_values and value == expected_values[key]:
                    if key != "session_id" or _safe_text(value) is not None:
                        safe[key] = value
            return safe
        snapshot["sources"] = {
            name: safe_source(name, source)
            for name, source in sources.items()
            if name in _SOURCE_KEYS and isinstance(source, Mapping)
        }
    return snapshot


def _sha256_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_codex_runtime_snapshot(
    request: SecretaryLaunchRequest,
    payload: Mapping[str, Any] | None,
    observation: Mapping[str, Any],
    *,
    configured_model: str | None,
    started_at: str,
    finished_at: str,
    provider_telemetry: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    if observation.get("state") != "idle":
        return None
    cleanup = observation.get("cleanup")
    if not isinstance(cleanup, Mapping) or cleanup.get("state") != "removed":
        return None
    if not isinstance(payload, Mapping):
        return None

    herdr = payload.get("herdr")
    git = payload.get("git")
    registry = payload.get("registry_launcher")
    if not all(isinstance(value, Mapping) for value in (herdr, git, registry)):
        return None
    session_id = _safe_text(herdr.get("session"))
    model = _safe_text(registry.get("model")) or configured_model
    if session_id is None or model is None:
        return None
    if git.get("worktree") != str(request.worktree.resolve()) or git.get("repo_root") != str(request.worktree.resolve()):
        return None
    if git.get("expected_base") != request.expected_base or git.get("head") != request.git_revision:
        return None
    if registry.get("repository_identity") != request.repository_identity:
        return None
    if registry.get("plan_identity") != request.plan_identity:
        return None
    if registry.get("model_provider") != request.provider:
        return None
    if configured_model is not None and registry.get("model") != configured_model:
        return None

    observed_at = _safe_text(observation.get("observed_at")) or finished_at
    raw_runtime = payload.get("secretary_runtime")
    expected_values = {
        **{key: getattr(request, key) for key in _RUNTIME_BINDING_KEYS},
        "repository_identity": request.repository_identity,
        "plan_identity": request.plan_identity,
        "git_revision": request.git_revision,
        "worktree": str(request.worktree.resolve()),
        "provider": request.provider,
        "model": model,
        "controller_id": SECRETARY_CONTROLLER,
        "session_id": session_id,
        "pair_id": request.run_id,
        "arm": "candidate",
        "workstream": "secretary-live-runtime",
        "checkpoint": f"{request.plan_revision}:{request.task_id}",
    }
    existing = (
        _safe_runtime_snapshot(raw_runtime, expected_values)
        if isinstance(raw_runtime, Mapping)
        else {}
    )
    fallback_timestamps = {
        "run_started": started_at,
        "cos_entry": started_at,
        "secretary_entry": started_at,
        "worker_entry": started_at,
        "publication": observed_at,
        "settlement": observed_at,
        "acceptance": observed_at,
        "secretary_exit": finished_at,
        "cos_exit": finished_at,
        "run_finished": finished_at,
    }
    timestamps = {
        key: existing.get("timestamps", {}).get(key, fallback)
        for key, fallback in fallback_timestamps.items()
    }
    try:
        parsed_timestamps = [
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            for value in timestamps.values()
        ]
    except (AttributeError, TypeError, ValueError):
        return None
    if any(right < left for left, right in zip(parsed_timestamps, parsed_timestamps[1:])):
        return None

    metrics = _safe_metrics(existing.get("metrics"))
    if (
        metrics["token_usage"] == "unknown"
        and isinstance(provider_telemetry, Mapping)
        and provider_telemetry.get("disposition") == "matched"
    ):
        metrics["token_usage"] = _safe_token_usage(
            {
                "input_tokens": provider_telemetry.get("input_tokens"),
                "output_tokens": provider_telemetry.get("output_tokens"),
                "total_tokens": provider_telemetry.get("total_tokens"),
                "cache_read_input_tokens": provider_telemetry.get("cache_read_input_tokens", 0),
                "cache_write_input_tokens": provider_telemetry.get("cache_write_input_tokens", 0),
                "source": "response.usage",
                "confidence": "observed",
            }
        )
        request_count = provider_telemetry.get("request_count")
        if (
            metrics["token_usage"] != "unknown"
            and metrics["secretary_turns"] == "unknown"
            and isinstance(request_count, int)
            and not isinstance(request_count, bool)
            and request_count >= 0
        ):
            metrics["secretary_turns"] = request_count

    binding = {
        "pair_id": request.run_id,
        "arm": "candidate",
        "run_id": request.run_id,
        "attempt_id": request.attempt_id,
        "task_id": request.task_id,
        "plan_revision": request.plan_revision,
        "repository_identity": request.repository_identity,
        "plan_identity": request.plan_identity,
        "git_revision": request.git_revision,
        "worktree": str(request.worktree.resolve()),
        "workstream": "secretary-live-runtime",
        "checkpoint": f"{request.plan_revision}:{request.task_id}",
    }
    runtime_identity = {
        **binding,
        "provider": request.provider,
        "model": model,
        "controller_id": SECRETARY_CONTROLLER,
        "session_id": session_id,
    }
    source_evidence = {
        "launch": {key: payload.get(key) for key in ("herdr", "codex", "git", "registry_launcher")},
        "secretary": {"timestamps": timestamps, "metrics": metrics},
        "task_result": {"observation": dict(observation)},
        "settlement": {"state": "unobserved"},
        "acceptance": {"decision": "unknown"},
    }
    sources = {
        name: {
            "producer": producer,
            "source_ref": f"runtime://{name}/{request.run_id}",
            "source_digest": _sha256_json(source_evidence[name]),
            **runtime_identity,
        }
        for name, producer in SOURCE_PRODUCERS.items()
    }
    return {
        **runtime_identity,
        "observed": True,
        "timestamps": timestamps,
        "metrics": metrics,
        "sources": sources,
    }


def sanitize_launcher_result(
    request: SecretaryLaunchRequest,
    *,
    returncode: int,
    payload: Mapping[str, Any] | None,
    configured_model: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> dict[str, Any]:
    assignment = payload.get("assignment") if isinstance(payload, Mapping) else None
    safe_assignment = _safe_assignment(assignment if isinstance(assignment, Mapping) else None)
    codex = payload.get("codex") if isinstance(payload, Mapping) else None
    herdr = payload.get("herdr") if isinstance(payload, Mapping) else None
    raw_runtime = payload.get("secretary_runtime") if isinstance(payload, Mapping) else None
    observed_runtime = _observed_runtime(payload)
    expected_values = {
        **{key: getattr(request, key) for key in _RUNTIME_BINDING_KEYS},
        "repository_identity": request.repository_identity,
        "plan_identity": request.plan_identity,
        "git_revision": request.git_revision,
        "worktree": str(request.worktree.resolve()),
        "provider": request.provider,
        "controller_id": SECRETARY_CONTROLLER,
        "pair_id": request.run_id,
        "arm": "candidate",
        "workstream": "secretary-live-runtime",
        "checkpoint": f"{request.plan_revision}:{request.task_id}",
    }
    if configured_model is not None:
        expected_values["model"] = configured_model
    if isinstance(herdr, Mapping):
        session_id = _safe_text(herdr.get("session"))
        if session_id is not None and session_id.strip():
            expected_values["session_id"] = session_id
    structured_binding = (
        _safe_runtime_snapshot(raw_runtime, expected_values)
        if isinstance(raw_runtime, Mapping)
        else None
    )
    live_attributed = (
        returncode == 0
        and observed_runtime is not None
        and (configured_model is None or observed_runtime.get("model") == configured_model)
        and _binding_matches(request, observed_runtime, assignment if isinstance(assignment, Mapping) else None)
        and _launcher_identity_matches(observed_runtime, herdr if isinstance(herdr, Mapping) else None)
        and _launcher_facts_match(request, payload, observed_runtime, configured_model)
        and _completion_observed(payload, observed_runtime)
    )
    observed_metrics = structured_binding.get("metrics") if isinstance(structured_binding, Mapping) else None
    failure_kind = _launcher_failure_kind(safe_assignment)
    return {
        "schema_version": "secretary-live-runtime-v1",
        "evidence_provenance": "live-attributed" if live_attributed else "capability-probe",
        "provider": request.provider,
        "task_id": request.task_id,
        "plan_revision": request.plan_revision,
        "attempt_id": request.attempt_id,
        "run_id": request.run_id,
        "repository_identity": request.repository_identity,
        "plan_identity": request.plan_identity,
        "git_revision": request.git_revision,
        "worktree": str(request.worktree.resolve()),
        "returncode": returncode,
        "assignment": safe_assignment,
        "runtime_identity": {
            "agent_name": _safe_text(herdr.get("agent_name")) if isinstance(herdr, Mapping) else None,
            "session": _safe_text(herdr.get("session")) if isinstance(herdr, Mapping) else None,
            "pane": _safe_text(herdr.get("pane")) if isinstance(herdr, Mapping) else None,
            "codex_version": _safe_text(codex.get("version")) if isinstance(codex, Mapping) else None,
            "provider": structured_binding.get("provider") if isinstance(structured_binding, Mapping) else None,
            "model": structured_binding.get("model") if isinstance(structured_binding, Mapping) else None,
            "controller_id": structured_binding.get("controller_id") if isinstance(structured_binding, Mapping) else None,
            "session_id": structured_binding.get("session_id") if isinstance(structured_binding, Mapping) else None,
            "secretary_runtime": structured_binding,
        },
        "timestamps": {
            "run_started": started_at,
            "run_finished": finished_at,
        },
        "metrics": {
            **_safe_metrics(observed_metrics if isinstance(observed_metrics, Mapping) else None)
        },
        "disposition": "READY" if live_attributed else "BLOCKED_CAPABILITY",
        "failure_kind": None if live_attributed else failure_kind or "runtime_completion_evidence_missing",
        **_classify_capabilities("READY" if live_attributed else "BLOCKED_CAPABILITY", None),
    }


def _configured_provider(codex_home: Path) -> str:
    config_path = codex_home / "config.toml"
    auth_path = codex_home / "auth.json"
    if not config_path.is_file() or not auth_path.is_file():
        raise RuntimeError("configured Codex config.toml/auth.json unavailable")
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    providers = config.get("model_providers")
    if not isinstance(providers, Mapping) or SECRETARY_PROVIDER not in providers:
        raise RuntimeError(f"configured Codex provider {SECRETARY_PROVIDER} unavailable")
    return SECRETARY_PROVIDER


def _configured_model(request: SecretaryLaunchRequest) -> str:
    profile_path = request.worktree / "agents" / f"{request.profile}.toml"
    if not profile_path.is_file():
        return "unknown"
    profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    if profile.get("model_provider") != SECRETARY_PROVIDER:
        raise RuntimeError(f"Secretary profile must use {SECRETARY_PROVIDER}")
    model = profile.get("model")
    return model.strip() if isinstance(model, str) and model.strip() else "unknown"


def _smoke_receipt(
    request: SecretaryLaunchRequest,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    if result.get("evidence_provenance") != "live-attributed":
        return {
            "schema_version": "secretary-live-runtime-receipt-v1",
            "disposition": "BLOCKED_CAPABILITY",
            "evidence_provenance": "capability-probe",
            "reason": result.get("failure_kind", "runtime_completion_evidence_missing"),
        }
    runtime_identity = result.get("runtime_identity")
    if not isinstance(runtime_identity, Mapping):
        runtime_identity = {}
    binding = {
        "pair_id": request.run_id,
        "arm": "candidate",
        "run_id": request.run_id,
        "attempt_id": request.attempt_id,
        "task_id": request.task_id,
        "plan_revision": request.plan_revision,
        "repository_identity": request.repository_identity,
        "plan_identity": request.plan_identity,
        "git_revision": request.git_revision,
        "worktree": str(request.worktree.resolve()),
        "workstream": "secretary-live-runtime",
        "checkpoint": f"{request.plan_revision}:{request.task_id}",
    }
    runtime = {
        "provider": runtime_identity.get("provider"),
        "model": runtime_identity.get("model"),
        "controller_id": runtime_identity.get("controller_id"),
        "session_id": runtime_identity.get("session_id"),
    }
    structured_runtime = runtime_identity.get("secretary_runtime") if isinstance(runtime_identity, Mapping) else None
    timestamps = structured_runtime.get("timestamps") if isinstance(structured_runtime, Mapping) else None
    if not isinstance(timestamps, Mapping):
        raise RuntimeError("live Secretary receipt missing observed timestamps")
    observed_metrics = structured_runtime.get("metrics") if isinstance(structured_runtime, Mapping) else None
    if not isinstance(observed_metrics, Mapping):
        raise RuntimeError("live Secretary receipt missing observed metrics")
    return validate_live_receipt(
        build_live_receipt(
            binding=binding,
            runtime=runtime,
            timestamps={
                "run_started": timestamps.get("run_started"),
                **timestamps,
            },
            metrics=observed_metrics,
            sources=structured_runtime.get("sources", {}),
        )
    )


def run_smoke(request: SecretaryLaunchRequest, *, output: Path) -> dict[str, Any]:
    _configured_provider(request.codex_home)
    configured_model = _configured_model(request)
    started = datetime.now(timezone.utc).isoformat()
    environment = dict(os.environ)
    environment["CODEX_HOME"] = str(request.codex_home.resolve())
    completed = subprocess.run(
        build_launcher_command(request),
        cwd=request.worktree,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    payloads = _json_payloads(completed.stdout) + _json_payloads(completed.stderr)
    payload = select_launcher_payload(payloads) if payloads else None
    result = sanitize_launcher_result(
        request,
        returncode=completed.returncode,
        payload=payload,
        configured_model=configured_model,
        started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )
    if result.get("disposition") != "READY" and completed.returncode == 0 and isinstance(payload, Mapping):
        post_submit = _observe_submitted_codex(request, payload, env=environment)
        result["post_submit_observation"] = post_submit
        if post_submit.get("state") != "idle":
            result["failure_kind"] = "runtime_completion_observation_missing"
        elif post_submit.get("cleanup", {}).get("state") != "removed":
            result["failure_kind"] = "runtime_cleanup_evidence_missing"
        else:
            result["failure_kind"] = "runtime_structured_receipt_missing"
        result.update(_classify_capabilities(result["disposition"], post_submit))
    else:
        result.update(_classify_capabilities(result["disposition"], None))
    result["provider_telemetry"] = _observe_provider_telemetry(
        started,
        datetime.now(timezone.utc).isoformat(),
    )
    runtime_snapshot = _build_codex_runtime_snapshot(
        request,
        payload,
        result.get("post_submit_observation", {}),
        configured_model=configured_model,
        started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(),
        provider_telemetry=result.get("provider_telemetry"),
    )
    if runtime_snapshot is not None:
        previous_identity = result.get("runtime_identity")
        previous_identity = previous_identity if isinstance(previous_identity, Mapping) else {}
        result["evidence_provenance"] = "live-attributed"
        result["runtime_identity"] = {
            "agent_name": previous_identity.get("agent_name"),
            "session": runtime_snapshot["session_id"],
            "pane": previous_identity.get("pane"),
            "codex_version": previous_identity.get("codex_version"),
            **{key: runtime_snapshot[key] for key in ("provider", "model", "controller_id", "session_id")},
            "secretary_runtime": runtime_snapshot,
        }
        result["timestamps"] = runtime_snapshot["timestamps"]
        result["metrics"] = runtime_snapshot["metrics"]
        result["disposition"] = "READY"
        result["failure_kind"] = None
        result.update(_classify_capabilities("READY", result.get("post_submit_observation")))
    result["receipt"] = _smoke_receipt(request, result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    smoke = subparsers.add_parser("smoke")
    smoke.add_argument("--output", type=Path, required=True)
    smoke.add_argument("--task-id", required=True)
    smoke.add_argument("--plan-revision", required=True)
    smoke.add_argument("--attempt-id", required=True)
    smoke.add_argument("--run-id", required=True)
    smoke.add_argument("--repository-identity", required=True)
    smoke.add_argument("--plan-identity", required=True)
    smoke.add_argument("--git-revision", required=True)
    smoke.add_argument("--cwd", type=Path, default=Path.cwd())
    smoke.add_argument("--expected-base", required=True)
    smoke.add_argument("--task", required=True)
    smoke.add_argument("--codex-home", type=Path)
    smoke.add_argument("--profile", default="normal")
    smoke.add_argument("--session", default="auto")
    smoke.add_argument("--pane", default="auto")
    args = parser.parse_args(argv)
    if args.command == "smoke":
        codex_home = (args.codex_home or Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")).expanduser()
        request = SecretaryLaunchRequest(
            task_id=args.task_id,
            plan_revision=args.plan_revision,
            attempt_id=args.attempt_id,
            run_id=args.run_id,
            repository_identity=args.repository_identity,
            plan_identity=args.plan_identity,
            git_revision=args.git_revision,
            worktree=args.cwd,
            expected_base=args.expected_base,
            task=args.task,
            codex_home=codex_home,
            profile=args.profile,
            session=args.session,
            pane=args.pane,
        )
        try:
            result = run_smoke(request, output=args.output)
        except (OSError, RuntimeError, ValueError) as exc:
            result = sanitize_launcher_result(request, returncode=2, payload=None)
            result["error"] = type(exc).__name__
            result["error_detail"] = str(exc)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 0 if result["disposition"] == "READY" else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
