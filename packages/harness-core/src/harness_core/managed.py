"""
@meta
name: harness_task
type: script
domain: harness
responsibility:
  - Resolve controller task metadata through canonical harness policy.
  - Verify task claims with fresh repository evidence.
inputs:
  - Versioned task and claimed-result JSON.
  - repo_config/harness.yaml
outputs:
  - Normalized task packet or verification evidence JSON.
tags:
  - harness
  - routing
  - verification
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
import tomllib
from typing import Any, Callable, NotRequired, TypedDict
import uuid

import yaml

from .config_validation import (
    READONLY_ARTIFACT_KINDS,
    load_yaml,
    resolve_operating_profile,
    validate as validate_harness_config,
)
from . import authority
from .compatibility import (
    APP_SERVER_MODEL_SELECTION_FIELDS,
    CURRENT_PACKET_API,
    CURRENT_RUN_API,
    admit_host_api,
    admit_packet_dispatch,
    admit_request_api,
    can_read_packet_api,
    legacy_role_capabilities,
    runtime_identity,
    static_provider_runtime_binding,
)
from .execution_lease import ExecutionLeaseError, normalize_duration_model, resolve_execution_lease, resolve_lane_timeout
from .legacy_cleanup import (
    LegacyCleanupError,
    legacy_cleanup_evidence_digest,
    normalize_legacy_cleanup_attestation,
    sign_legacy_cleanup_attestation,
)
from .terminal_observation import (
    TerminalObservationError,
    normalize_host_terminal_observation,
    normalize_terminal_observation,
)
from .timeout_observation import TimeoutObservationError, normalize_timeout_observation
from .coordination import PlanCoordination, PlanCoordinationError, PlanTask, load_plan_coordination, path_matches as _path_matches


class HarnessError(ValueError):
    pass


class ClaimError(HarnessError):
    def __init__(self, detail: str, *, subcode: str | None = None):
        super().__init__(detail)
        self.subcode = subcode


class WorkspaceBaselineError(HarnessError):
    pass


CheckRunner = Callable[[list[str]], tuple[int, str, str]]
ChangeCollector = Callable[[Path, str], list[dict[str, str]]]

MANAGED_VERSION = CURRENT_PACKET_API
LEGACY_MANAGED_VERSION = 2
CAPABILITY_LEVELS = {"enforced", "advisory", "unavailable"}
CRITERION_KINDS = {"check", "change_set", "review", "manual", "validator"}
DECISION_KINDS = {"accept", "retry", "escalate", "request_approval", "waive", "block"}
RECOVERY_EVIDENCE_FIELDS = {"version", "source", "code", "run_id", "attempt_id", "detail", "observed_at"}
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]+\Z")
FRICTION_EVENT_VERSION = 1
FRICTION_EVENT_KINDS = {"observed", "resolution"}
FRICTION_SOURCES = {"agent", "host", "validator", "check", "controller"}
FRICTION_PHASES = {"claim", "dispatch", "integration", "check", "validator", "decision"}
FRICTION_RESOLUTIONS = {"keep", "revise", "remove", "pending"}
CLAIM_OBSERVATION_VERSION = 1
CLAIM_OBSERVATION_STATES = {"missing", "non_json", "json_non_object", "object"}
CLAIM_OBSERVATION_FIELDS = {
    "version",
    "lane_id",
    "thread_id",
    "state",
    "candidate_claim",
    "content_digest",
    "content_length",
}
CLAIM_REPAIR_RESULT_FIELDS = {"claim_observation", "finalization_evidence"}
CLAIM_REPAIR_FINALIZATION_TERMINAL_STATUSES = {"completed", "timed_out"}
CLAIM_REPAIR_FINALIZATION_FIELDS = {
    "lane_id",
    "thread_id",
    "turn_id",
    "terminal_status",
    "sandbox",
    "tool_calls",
    "command_results",
    "workspace_status_before",
    "workspace_status_after",
    "agent_identity",
    "prompt_contract_version",
    "prompt_digest",
    "elapsed_seconds",
}
CLAIM_REPAIR_FINALIZATION_OPTIONAL_FIELDS = {"app_server_model_selection"}
DELEGATED_CHILD_TERMINAL_STATES = {"succeeded", "failed", "cancelled", "timed_out", "awaiting_decision"}
CORE_STATE_TRANSITIONS = {
    "classified": ["planned", "blocked"],
    "planned": ["running", "awaiting_decision", "blocked"],
    "running": ["observed", "awaiting_decision", "blocked", "orphaned"],
    "observed": ["verifying", "running", "blocked", "orphaned"],
    "verifying": ["awaiting_decision", "accepted", "blocked", "orphaned"],
    "orphaned": ["awaiting_decision", "blocked"],
    "awaiting_decision": ["awaiting_decision", "planned", "accepted", "unvalidated", "blocked"],
    "accepted": [],
    "unvalidated": [],
    "blocked": [],
}


class DelegationResult(TypedDict):
    ok: bool
    code: NotRequired[str]
    invocation_id: NotRequired[str]
    status: NotRequired[str]
    summary: NotRequired[str]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(f"invalid JSON input: {path}") from exc
    if not isinstance(payload, dict):
        raise HarnessError("JSON input must be an object")
    return payload


def _load_policy(root: Path) -> dict[str, Any]:
    path = root / "repo_config" / "harness.yaml"
    try:
        payload = load_yaml(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise HarnessError(f"invalid harness policy: {exc}") from exc
    if not isinstance(payload, dict):
        raise HarnessError("harness policy must be an object")
    payload["states"] = copy.deepcopy(CORE_STATE_TRANSITIONS)
    return payload


def _core_identity(
    policy: dict[str, Any],
    adapter: Any | None = None,
    *,
    request_api: Any | None = None,
) -> dict[str, Any]:
    core_policy = policy.get("harness_core")
    policy_request_api = core_policy.get("request_api") if isinstance(core_policy, dict) else None
    if request_api is None:
        request_api = policy_request_api
    elif request_api != policy_request_api:
        raise HarnessError("managed request API must match policy request_api")
    request_admission = admit_request_api(request_api)
    if not request_admission["ok"]:
        raise HarnessError(request_admission["code"])
    host_api = None
    if adapter is not None:
        host_admission = admit_host_api(_adapter_host_api(adapter))
        if not host_admission["ok"]:
            raise HarnessError(host_admission["code"])
        host_api = host_admission["host_api"]
        dispatch_admission = admit_packet_dispatch(host_api, request_admission["packet_api"])
        if not dispatch_admission["ok"]:
            raise HarnessError(dispatch_admission["code"])
    try:
        identity = runtime_identity()
    except RuntimeError as exc:
        raise HarnessError("harness_core_identity_unavailable") from exc
    return {
        **identity,
        "request_api": request_admission["request_api"],
        "packet_api": request_admission["packet_api"],
        "host_api": host_api,
    }


def admit_managed_operation(root: Path, adapter: Any, *, request_api: Any | None = None) -> dict[str, Any]:
    """Admit consumer and host protocol versions before provider I/O."""
    return _core_identity(_load_policy(root), adapter, request_api=request_api)


def _friction_policy(root: Path) -> dict[str, Any]:
    policy = _load_policy(root)
    friction_policy = policy.get("friction_policy")
    if not isinstance(friction_policy, dict):
        raise HarnessError("missing friction policy")
    required = {"event_version", "minimum_distinct_runs", "window_days"}
    allowed = required | {"follow_up_routes"}
    if set(friction_policy) - allowed or required - set(friction_policy):
        raise HarnessError("invalid friction policy")
    if friction_policy["event_version"] != FRICTION_EVENT_VERSION:
        raise HarnessError("unsupported friction event version")
    if any(
        not isinstance(friction_policy[name], int)
        or isinstance(friction_policy[name], bool)
        or friction_policy[name] < 1
        for name in ("minimum_distinct_runs", "window_days")
    ):
        raise HarnessError("invalid friction policy")
    follow_up_routes = friction_policy.get("follow_up_routes", {})
    if not isinstance(follow_up_routes, dict) or not all(
        isinstance(code, str) and code and isinstance(task_type, str) and task_type
        for code, task_type in follow_up_routes.items()
    ):
        raise HarnessError("invalid friction follow-up routes")
    for task_type in follow_up_routes.values():
        route = policy["routes"].get(task_type)
        if not isinstance(route, dict):
            raise HarnessError(f"friction follow-up route `{task_type}` is unknown")
        if "repo.write" in route.get("capabilities", []) or "single_work_lane" not in route.get("execution_modes", []):
            raise HarnessError(f"friction follow-up route `{task_type}` must be single-lane read-only")
    return friction_policy


def _evidence_artifact_policy(policy: dict[str, Any]) -> dict[str, Any]:
    raw = policy.get("evidence_artifacts")
    if not isinstance(raw, dict):
        raise HarnessError("invalid evidence artifact policy")
    catalog = raw.get("catalog")
    if not isinstance(catalog, dict):
        raise HarnessError("invalid evidence artifact policy")
    retained_kinds = [
        kind
        for kind, entry in catalog.items()
        if kind in READONLY_ARTIFACT_KINDS and isinstance(entry, dict) and entry.get("retention") == "writer_retained"
    ]
    return {"writer_retained_kinds": retained_kinds}


def _artifact_handoff_policy(policy: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    raw = policy.get("evidence_artifacts")
    if not isinstance(raw, dict) or not isinstance(raw.get("catalog"), dict) or not isinstance(raw.get("profiles"), dict):
        raise HarnessError("invalid artifact handoff policy")
    allowed_profiles = route.get("artifact_handoff_profiles", [])
    if not isinstance(allowed_profiles, list):
        raise HarnessError("invalid artifact handoff route")
    return {
        "catalog": copy.deepcopy(raw["catalog"]),
        "profiles": {name: copy.deepcopy(raw["profiles"][name]) for name in allowed_profiles},
        "allowed_profiles": list(allowed_profiles),
        "default_profile": route.get("default_artifact_handoff_profile"),
    }


def _artifact_content_bytes(content: Any) -> bytes:
    try:
        return json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HarnessError("evidence artifact content must be JSON") from exc


def _artifact_descriptor(kind: str, source_run_id: str, source_attempt_id: str, content: Any) -> dict[str, Any]:
    encoded = _artifact_content_bytes(content)
    return {
        "kind": kind,
        "source_run_id": source_run_id,
        "source_attempt_id": source_attempt_id,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "byte_length": len(encoded),
        "content": copy.deepcopy(content),
    }


def _validate_sanitized_command_trace(content: Any, max_bytes: int) -> None:
    if not isinstance(content, dict) or set(content) != {"version", "commands"} or content.get("version") != 1:
        raise HarnessError("sanitized command trace is invalid")
    commands = content.get("commands")
    if not isinstance(commands, list) or len(commands) > 16:
        raise HarnessError("sanitized command trace commands are invalid")
    for command in commands:
        if (
            not isinstance(command, dict)
            or set(command) != {"item_id", "command", "output", "exit_code"}
            or not isinstance(command["item_id"], str)
            or not isinstance(command["command"], str)
            or not isinstance(command["output"], str)
            or len(command["command"].encode("utf-8")) > max_bytes
            or len(command["output"].encode("utf-8")) > max_bytes
            or (command["exit_code"] is not None and (not isinstance(command["exit_code"], int) or isinstance(command["exit_code"], bool)))
        ):
            raise HarnessError("sanitized command trace command is invalid")
    if len(_artifact_content_bytes(content)) > max_bytes:
        raise HarnessError("sanitized command trace exceeds artifact_max_bytes")


def _validate_handoff_artifact_content(kind: str, content: Any, source_packet: dict[str, Any]) -> None:
    if kind == "terminal_observation":
        try:
            normalize_terminal_observation(content, source_packet)
        except TerminalObservationError as exc:
            raise HarnessError("artifact_handoff terminal_observation is invalid") from exc
        return
    if kind != "sanitized_command_trace":
        raise HarnessError(f"artifact_handoff `{kind}` is unsupported")
    retained = source_packet.get("retained_artifacts")
    if not isinstance(retained, list):
        raise HarnessError("artifact_handoff sanitized_command_trace has invalid producer")
    matches = [item for item in retained if isinstance(item, dict) and item.get("kind") == kind]
    if len(matches) != 1 or not isinstance(matches[0].get("max_bytes"), int) or isinstance(matches[0]["max_bytes"], bool) or matches[0]["max_bytes"] <= 0:
        raise HarnessError("artifact_handoff sanitized_command_trace has invalid producer")
    _validate_sanitized_command_trace(content, matches[0]["max_bytes"])


def _source_attempt(run: dict[str, Any], attempt_id: str) -> dict[str, Any]:
    if run.get("state") not in TERMINAL_RUN_STATES:
        raise HarnessError("readonly artifact source run is not terminal")
    attempts = run.get("attempts")
    if not isinstance(attempts, list):
        raise HarnessError("readonly artifact source run has invalid attempts")
    attempt = next((item for item in attempts if isinstance(item, dict) and item.get("attempt_id") == attempt_id), None)
    if not isinstance(attempt, dict):
        raise HarnessError("readonly artifact source attempt is unavailable")
    return attempt


def _stored_artifact_content(attempt: dict[str, Any], kind: str) -> Any:
    evidence = attempt.get("evidence")
    if not isinstance(evidence, dict):
        raise HarnessError("readonly artifact source attempt lacks evidence")
    if kind == "terminal_observation":
        content = evidence.get("terminal_observation")
        if isinstance(content, dict):
            return content
    artifacts = evidence.get("artifacts", [])
    if isinstance(artifacts, list):
        matches = [item for item in artifacts if isinstance(item, dict) and item.get("kind") == kind]
        if len(matches) > 1:
            raise HarnessError(f"readonly artifact `{kind}` is duplicated")
        if len(matches) == 1 and "content" in matches[0]:
            return matches[0]["content"]
    raise HarnessError(f"readonly artifact `{kind}` is unavailable")


def _handoff_source_records(
    root: Path,
    packet: dict[str, Any],
    profile: dict[str, Any],
    sources: list[dict[str, str]],
) -> list[tuple[str, str, dict[str, Any], dict[str, Any]]]:
    if not sources:
        raise HarnessError("artifact_handoff requires a source")
    records: list[tuple[str, str, dict[str, Any], dict[str, Any]]] = []
    seen: set[tuple[str, str]] = set()
    for source in sources:
        if not isinstance(source, dict) or set(source) != {"run_id", "attempt_id"}:
            raise HarnessError("artifact_handoff source has invalid fields")
        source_run_id = _safe_run_id(source["run_id"])
        source_attempt_id = _required_string(source["attempt_id"], "artifact_handoff source attempt_id")
        if (source_run_id, source_attempt_id) in seen:
            raise HarnessError("artifact_handoff contains duplicate source")
        seen.add((source_run_id, source_attempt_id))
        source_attempt = _source_attempt(_load_run(root, source_run_id), source_attempt_id)
        source_packet = source_attempt.get("packet")
        if not isinstance(source_packet, dict):
            raise HarnessError("artifact_handoff source packet is unavailable")
        base_compatibility = profile.get("base_compatibility")
        if base_compatibility == "exact_packet_base" and source_packet.get("base_commit") != packet.get("base_commit"):
            raise HarnessError("artifact_handoff source base is incompatible")
        if base_compatibility not in {"exact_packet_base", "same_repository", None}:
            raise HarnessError("artifact_handoff source base compatibility is invalid")
        records.append((source_run_id, source_attempt_id, source_attempt, source_packet))
    return records


def _select_handoff_artifacts(
    packet: dict[str, Any],
    profile: dict[str, Any],
    sources: list[tuple[str, str, dict[str, Any], dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    policy = packet["artifact_handoff_policy"]
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    selected_keys: set[tuple[str, str, str]] = set()

    def select(kind: str, source: tuple[str, str, dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        source_run_id, source_attempt_id, source_attempt, source_packet = source
        content = _stored_artifact_content(source_attempt, kind)
        _validate_handoff_artifact_content(kind, content, source_packet)
        return _artifact_descriptor(kind, source_run_id, source_attempt_id, content)

    def add(descriptor: dict[str, Any], *, required: bool) -> bool:
        key = (descriptor["kind"], descriptor["source_run_id"], descriptor["source_attempt_id"])
        if key in selected_keys:
            if required:
                raise HarnessError("artifact_handoff contains duplicate selected descriptor")
            return False
        if descriptor["byte_length"] > policy["catalog"][descriptor["kind"]]["byte_limit"]:
            if required:
                raise HarnessError("artifact_handoff required artifact exceeds byte limit")
            rejected.append({"kind": descriptor["kind"], "reason": "byte_limit"})
            return False
        if len(selected) >= profile["count_limit"] or sum(item["byte_length"] for item in selected) + descriptor["byte_length"] > profile["total_byte_limit"]:
            if required:
                raise HarnessError("artifact_handoff required artifact exceeds profile bounds")
            rejected.append({"kind": descriptor["kind"], "reason": "profile_limit"})
            return False
        selected.append(descriptor)
        selected_keys.add(key)
        return True

    for kind in profile["required_kinds"]:
        for source in sources:
            try:
                descriptor = select(kind, source)
            except HarnessError as exc:
                if "is unavailable" in str(exc):
                    continue
                raise HarnessError(f"artifact_handoff required `{kind}` is invalid") from exc
            add(descriptor, required=True)
            break
        else:
            raise HarnessError(f"artifact_handoff missing required `{kind}`")

    for kind in (kind for kind in profile["kind_priority"] if kind not in profile["required_kinds"]):
        for source in sources:
            try:
                descriptor = select(kind, source)
            except HarnessError as exc:
                rejected.append({"kind": kind, "reason": "unavailable" if "is unavailable" in str(exc) else "invalid"})
                continue
            add(descriptor, required=False)
    return selected, rejected


def _resolve_artifact_handoff_sources(
    root: Path,
    packet: dict[str, Any],
    profile_name: str,
    sources: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    policy = packet["artifact_handoff_policy"]
    if profile_name not in policy["allowed_profiles"]:
        raise HarnessError("artifact_handoff profile is not allowed by route")
    profile = policy["profiles"][profile_name]
    source_records = _handoff_source_records(root, packet, profile, sources)
    selected, rejected = _select_handoff_artifacts(packet, profile, source_records)
    digest_input = {
        "version": 1,
        "profile": profile_name,
        "lineage_mode": profile["lineage_mode"],
        "sources": [{"run_id": run_id, "attempt_id": attempt_id} for run_id, attempt_id, _attempt, _packet in source_records],
        "descriptors": [{key: item[key] for key in ("kind", "source_run_id", "source_attempt_id", "sha256", "byte_length")} for item in selected],
        "rejections": rejected,
    }
    proof = {
        "version": 1,
        "profile": profile_name,
        "lineage_mode": profile["lineage_mode"],
        "selected_count": len(selected),
        "total_bytes": sum(item["byte_length"] for item in selected),
        "selection_digest": hashlib.sha256(_artifact_content_bytes(digest_input)).hexdigest(),
    }
    audit = {**proof, "sources": digest_input["sources"], "selected": digest_input["descriptors"], "optional_rejections": rejected}
    return selected, {"proof": proof, "audit": audit}


def _resolve_artifact_handoff(root: Path, packet: dict[str, Any], value: Any) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    if value is None:
        return [], None
    if packet["workspace_write_access"] != "read_only":
        raise HarnessError("artifact_handoff requires read-only packet access")
    if not isinstance(value, dict) or set(value) - {"source_run_id", "source_attempt_id", "profile"} or {"source_run_id", "source_attempt_id"} - set(value):
        raise HarnessError("artifact_handoff has invalid fields")
    policy = packet["artifact_handoff_policy"]
    profile_name = value.get("profile", policy["default_profile"])
    if not isinstance(profile_name, str) or profile_name not in policy["allowed_profiles"]:
        raise HarnessError("artifact_handoff profile is not allowed by route")
    if policy["profiles"][profile_name]["lineage_mode"] != "direct":
        raise HarnessError("artifact_handoff requires a direct profile")
    return _resolve_artifact_handoff_sources(root, packet, profile_name, [{
        "run_id": value["source_run_id"],
        "attempt_id": value["source_attempt_id"],
    }])


def _canonical_execution_mode(
    policy: dict[str, Any], value: Any, *, allow_alias: bool, default: str
) -> str:
    execution_mode = _required_string(value if value is not None else default, "execution_mode")
    orchestration = policy["orchestration"]
    if execution_mode in orchestration:
        return execution_mode
    for name, topology in orchestration.items():
        if execution_mode in topology["aliases"]:
            if allow_alias:
                return name
            raise HarnessError(
                f"legacy execution mode `{execution_mode}`; use canonical execution mode `{name}`"
            )
    raise HarnessError(f"unknown execution mode `{execution_mode}`")


def _validate_policy(root: Path) -> None:
    errors = validate_harness_config(root)
    if errors:
        raise HarnessError("invalid harness policy: " + "; ".join(errors))


def _string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise HarnessError(f"{name} must be a non-empty list of strings")
    return value


def _safe_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or value.startswith("."):
        raise HarnessError(f"unsafe relative path `{value}`")
    return path.as_posix()


def _json_bytes(value: Any) -> int:
    return len(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _normalize_work_context(
    policy: dict[str, Any],
    *,
    user_request: str,
    role: dict[str, Any],
    base_commit: str,
    value: Any,
) -> dict[str, Any]:
    limits = policy["context_limits"]
    if len(user_request.encode("utf-8")) > limits["objective_max_bytes"]:
        raise HarnessError("user_request exceeds objective_max_bytes")
    if value is None:
        value = {
            "version": 1,
            "objective": user_request,
            "facts": [],
            "artifacts": [],
            "expected_result": {
                "kind": role["result_kind"],
                "required_fields": list(role["required_fields"]),
            },
        }
    if not isinstance(value, dict):
        raise HarnessError("work_context must be an object")
    required = {"version", "objective", "facts", "artifacts", "expected_result"}
    if required - value.keys() or set(value) - required - {"digest"}:
        raise HarnessError("work_context has invalid fields")
    if value["version"] != 1 or value["objective"] != user_request:
        raise HarnessError("work_context objective conflicts with user_request")
    facts = value["facts"]
    if not isinstance(facts, list) or len(facts) > limits["max_facts"]:
        raise HarnessError("work_context facts exceed max_facts")
    seen_fact_ids: set[str] = set()
    normalized_facts: list[dict[str, str]] = []
    for fact in facts:
        if not isinstance(fact, dict) or set(fact) != {"id", "text", "sha256"}:
            raise HarnessError("work_context fact is invalid")
        fact_id = _required_string(fact["id"], "work_context fact id")
        text = _required_string(fact["text"], "work_context fact text")
        digest = _required_string(fact["sha256"], "work_context fact sha256")
        if fact_id in seen_fact_ids or hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
            raise HarnessError("work_context fact is duplicated or has invalid sha256")
        seen_fact_ids.add(fact_id)
        normalized_facts.append({"id": fact_id, "text": text, "sha256": digest})
    if _json_bytes(normalized_facts) > limits["fact_max_bytes"]:
        raise HarnessError("work_context facts exceed fact_max_bytes")
    artifacts = value["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > limits["max_artifacts"]:
        raise HarnessError("work_context artifacts exceed max_artifacts")
    seen_artifact_paths: set[str] = set()
    normalized_artifacts: list[dict[str, str]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"path", "base_commit", "sha256"}:
            raise HarnessError("work_context artifact is invalid")
        path = _safe_path(_required_string(artifact["path"], "work_context artifact path"))
        artifact_base = _required_string(artifact["base_commit"], "work_context artifact base_commit")
        digest = _required_string(artifact["sha256"], "work_context artifact sha256")
        if path in seen_artifact_paths or artifact_base != base_commit or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise HarnessError("work_context artifact is duplicated or has invalid identity")
        seen_artifact_paths.add(path)
        normalized_artifacts.append({"path": path, "base_commit": artifact_base, "sha256": digest})
    expected_result = value["expected_result"]
    if (
        not isinstance(expected_result, dict)
        or set(expected_result) != {"kind", "required_fields"}
        or expected_result.get("kind") != role["result_kind"]
        or expected_result.get("required_fields") != role["required_fields"]
    ):
        raise HarnessError("work_context expected_result conflicts with role")
    context = {
        "version": 1,
        "objective": user_request,
        "facts": normalized_facts,
        "artifacts": normalized_artifacts,
        "expected_result": copy.deepcopy(expected_result),
    }
    digest = hashlib.sha256(json.dumps(context, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
    if value.get("digest") not in (None, digest):
        raise HarnessError("work_context digest conflicts with content")
    return {**context, "digest": digest}


def resolve_task(root: Path, task: dict[str, Any]) -> dict[str, Any]:
    _validate_policy(root)
    if task.get("version") != 1:
        raise HarnessError("task version must be 1")
    task_type = task.get("task_type")
    if not isinstance(task_type, str):
        raise HarnessError("task_type must be a string")
    criteria = _string_list(task.get("acceptance_criteria"), "acceptance_criteria")
    allowed_paths = [_safe_path(path) for path in _string_list(task.get("allowed_paths"), "allowed_paths")]
    base_ref = task.get("base_ref")
    if not isinstance(base_ref, str) or not base_ref:
        raise HarnessError("base_ref must be a non-empty string")

    policy = _load_policy(root)
    execution_mode = _canonical_execution_mode(
        policy,
        task.get("execution_mode"),
        allow_alias=True,
        default="single_agent",
    )
    route_packet = _route_packet(policy, task_type, execution_mode)
    return {
        "version": 1,
        "task_type": task_type,
        "template": route_packet["template"],
        "agent_identity": _load_agent_identity(root, route_packet["template"]),
        "role": route_packet["role"],
        "rules": route_packet["rules"],
        "skills": route_packet["skills"],
        "tools": route_packet["tools"],
        "workspace": route_packet["workspace"],
        "orchestration": route_packet["orchestration"],
        "checks": route_packet["checks"],
        "approval_gates": route_packet["approval_gates"],
        "execution_budget": route_packet["execution_budget"],
        "allowed_next_states": copy.deepcopy(CORE_STATE_TRANSITIONS),
        "acceptance_criteria": criteria,
        "allowed_paths": allowed_paths,
        "base_ref": base_ref,
    }


def _run_command(root: Path, command: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    return completed.returncode, completed.stdout, completed.stderr


def _changed_paths(root: Path, base_ref: str) -> list[str]:
    status, stdout, stderr = _run_command(root, ["git", "diff", "--name-only", base_ref, "--"])
    if status:
        raise HarnessError(f"could not read changed paths: {stderr.strip()}")
    return [line for line in stdout.splitlines() if line]


def _validate_claim(claim: dict[str, Any]) -> None:
    if claim.get("kind") != "claimed_result":
        raise HarnessError("claim kind must be `claimed_result`")
    _string_list(claim.get("changed_files"), "changed_files")
    for name in ("from_state", "next_state"):
        if not isinstance(claim.get(name), str) or not claim[name]:
            raise HarnessError(f"{name} must be a non-empty string")
    approved = claim.get("approved_gates", [])
    if not isinstance(approved, list) or not all(isinstance(item, str) for item in approved):
        raise HarnessError("approved_gates must be a list of strings")


def verify_task(
    root: Path,
    task: dict[str, Any],
    claim: dict[str, Any],
    *,
    changed_paths: list[str] | None = None,
    run_check: CheckRunner | None = None,
) -> dict[str, Any]:
    packet = resolve_task(root, task)
    _validate_claim(claim)
    changed = changed_paths if changed_paths is not None else _changed_paths(root, packet["base_ref"])
    runner = run_check or (lambda command: _run_command(root, command))
    blockers: list[dict[str, str]] = []
    for path in changed:
        safe_path = _safe_path(path)
        if not _path_matches(safe_path, packet["allowed_paths"]):
            blockers.append({"kind": "scope", "path": safe_path})
        for gate, patterns in packet["approval_gates"].items():
            if _path_matches(safe_path, patterns) and gate not in claim.get("approved_gates", []):
                blockers.append({"kind": "approval", "gate": gate, "path": safe_path})

    states = packet["allowed_next_states"]
    if claim["next_state"] not in states.get(claim["from_state"], []):
        blockers.append({"kind": "transition", "from": claim["from_state"], "to": claim["next_state"]})

    checks = []
    for name, command in packet["checks"].items():
        code, stdout, stderr = runner(command)
        checks.append({"name": name, "command": command, "exit_code": code, "stdout": stdout[:1000], "stderr": stderr[:1000]})
        if code:
            blockers.append({"kind": "check", "name": name})

    for friction in claim.get("frictions", []):
        if isinstance(friction, dict) and isinstance(friction.get("category"), str):
            blockers.append({"kind": "friction", "category": friction["category"]})

    result = {
        "version": 1,
        "status": "verified" if not blockers else "observed",
        "packet": packet,
        "changed_paths": changed,
        "checks": checks,
        "blockers": blockers,
        "acceptance": [{"criterion": criterion, "proven": not blockers} for criterion in packet["acceptance_criteria"]],
    }
    run_dir = task.get("run_dir")
    if isinstance(run_dir, str) and run_dir:
        target = Path(run_dir)
        allowed_root = (root / ".harness").resolve()
        try:
            target.resolve().relative_to(allowed_root)
        except ValueError as exc:
            raise HarnessError(f"run_dir must stay under `{allowed_root}`") from exc
        target.mkdir(parents=True, exist_ok=True)
        (target / "evidence.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _required_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise HarnessError(f"{name} must be a non-empty string")
    return value


def _safe_paths(value: Any, name: str, *, required: bool) -> list[str]:
    if value is None and not required:
        return []
    if not required:
        if not isinstance(value, list) or not all(isinstance(path, str) and path for path in value):
            raise HarnessError(f"{name} must be a list of strings")
        return [_safe_path(path) for path in value]
    return [_safe_path(path) for path in _string_list(value, name)]


def _load_role_catalog(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    with (root / "agents" / "roles.yaml").open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    roles = payload.get("roles") if isinstance(payload, dict) else None
    claim_fields = payload.get("claim_fields") if isinstance(payload, dict) else None
    if not isinstance(roles, dict) or not isinstance(claim_fields, dict):
        raise HarnessError("roles must be a mapping")
    if not all(isinstance(name, str) and name and isinstance(field_type, str) and field_type for name, field_type in claim_fields.items()):
        raise HarnessError("claim_fields must be a mapping of non-empty strings")
    return roles, claim_fields


def _load_roles(root: Path) -> dict[str, dict[str, Any]]:
    return _load_role_catalog(root)[0]


def _claim_schema(role: dict[str, Any], claim_fields: dict[str, str]) -> dict[str, Any]:
    required_fields = role.get("required_fields")
    if not isinstance(required_fields, list) or not all(isinstance(field, str) and field in claim_fields for field in required_fields):
        raise HarnessError("role claim fields conflict with claim catalog")
    field_types = {field: claim_fields[field] for field in required_fields}
    return {
        "required_fields": copy.deepcopy(required_fields),
        "field_types": field_types,
        "optional_field_types": {
            field: field_type
            for field, field_type in claim_fields.items()
            if field not in field_types
        },
        "field_constraints": copy.deepcopy(role.get("field_constraints", {})),
    }


def _load_agent_identity(root: Path, template: str) -> dict[str, str]:
    path = root / "agents" / f"{template}.toml"
    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise HarnessError(f"invalid agent template `{template}`") from exc
    if payload.get("name") != template:
        raise HarnessError(f"agent template `{template}` has mismatched name")
    fields = {
        "model_provider": payload.get("model_provider"),
        "model": payload.get("model"),
        "reasoning_effort": payload.get("model_reasoning_effort"),
    }
    if not all(isinstance(value, str) and value for value in fields.values()):
        raise HarnessError(f"agent template `{template}` has invalid model identity")
    return {"template": template, **fields}


def _resolve_execution_budget(
    policy: dict[str, Any],
    *,
    profile_name: str | None = None,
) -> dict[str, Any]:
    selected = profile_name if profile_name is not None else policy["defaults"]["execution_budget_profile"]
    budgets = policy["execution_budgets"]
    profile = budgets["profiles"].get(selected)
    if not isinstance(profile, dict):
        raise HarnessError(f"unknown execution budget profile `{selected}`")
    try:
        duration_model = normalize_duration_model(budgets.get("lease_duration_model"))
        lane_timeout_seconds = resolve_lane_timeout(
            duration_model,
            turn_timeout_seconds=profile["turn_timeout_seconds"],
        )
    except ExecutionLeaseError as exc:
        raise HarnessError(str(exc)) from exc
    budget = {
        "profile": selected,
        "turn_timeout_seconds": profile["turn_timeout_seconds"],
        "lane_timeout_seconds": lane_timeout_seconds,
        "check_timeout_seconds": duration_model["check_timeout_seconds"],
        "finalization_reserve_seconds": budgets["finalization_reserve_seconds"],
        "timeout_decisions": list(profile["timeout_decisions"]),
    }
    if "escalation_profile" in profile:
        budget["escalation_profile"] = profile["escalation_profile"]
    return budget


def _normalize_skill_set_selections(request: dict[str, Any], route: dict[str, Any]) -> list[dict[str, str]]:
    value = request.get("skill_set_selections", [])
    if not isinstance(value, list):
        raise HarnessError("skill_set_selections must be a list")
    allowed = route.get("allowed_skill_sets", [])
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {"id", "reason"}:
            raise HarnessError("skill_set_selections entries must define id and reason")
        identifier = _required_string(item.get("id"), "skill set id")
        reason = _required_string(item.get("reason"), "skill set reason")
        if identifier in seen or identifier not in allowed:
            raise HarnessError(f"skill set `{identifier}` is not allowed for task type")
        seen.add(identifier)
        selected.append({"id": identifier, "reason": reason})
    return selected


def _normalize_operating_profile_selection(request: dict[str, Any], route: dict[str, Any]) -> dict[str, str] | None:
    value = request.get("operating_profile_selection")
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"id", "reason"}:
        raise HarnessError("operating_profile_selection must define id and reason")
    identifier = _required_string(value.get("id"), "operating profile id")
    if identifier not in route.get("allowed_operating_profiles", []):
        raise HarnessError(f"operating profile `{identifier}` is not allowed for task type")
    return {"id": identifier, "reason": _required_string(value.get("reason"), "operating profile reason")}


def _resolve_skill_sets(policy: dict[str, Any], route: dict[str, Any], selected: list[dict[str, str]]) -> tuple[list[str], dict[str, Any] | None]:
    if "required_skill_sets" not in route:
        return list(route["skills"]), None
    required = list(route["required_skill_sets"])
    selected_ids = [item["id"] for item in selected]
    resolved_ids = [*required, *selected_ids]
    resolved_skills: list[str] = []
    for set_id in resolved_ids:
        for skill in policy["skill_sets"][set_id]["skills"]:
            if skill not in resolved_skills:
                resolved_skills.append(skill)
    return resolved_skills, {"required": required, "selected": selected, "resolved": resolved_ids}


def _route_packet(
    policy: dict[str, Any],
    task_type: str,
    execution_mode: str,
    *,
    execution_budget_profile: str | None = None,
    skill_set_selections: list[dict[str, str]] | None = None,
    operating_profile_selection: dict[str, str] | None = None,
) -> dict[str, Any]:
    route = policy["routes"].get(task_type)
    if not isinstance(route, dict):
        raise HarnessError(f"unknown task type `{task_type}`")
    if execution_mode not in route["execution_modes"]:
        raise HarnessError(f"unsupported execution mode `{execution_mode}` for task type `{task_type}`")
    orchestration = policy["orchestration"][execution_mode]
    profile_metadata: dict[str, Any] | None = None
    if "default_operating_profile" in route:
        selected_profile = operating_profile_selection or {"id": route["default_operating_profile"], "reason": "route_default"}
        try:
            profile = resolve_operating_profile(policy, task_type, selected_profile["id"])
        except ValueError as exc:
            raise HarnessError(str(exc)) from exc
        authority_name = profile["authority"]
        toolset_name = profile["toolset"]
        verification_profile_name = profile["verification_profile"]
        template = profile["template"]
        runtime_provider_id = profile["runtime_provider"]
        execution_budget_profile = profile["execution_budget_profile"]
        profile_metadata = {"default": route["default_operating_profile"], "selected": operating_profile_selection, "resolved": selected_profile["id"], "reason": selected_profile["reason"], "values": profile}
    else:
        authority_name = route["authority"]
        toolset_name = route["toolset"]
        verification_profile_name = route["verification_profile"]
        template = route["template"]
        runtime_provider_id = None
    authority = policy["authorities"].get(authority_name)
    tools = policy["toolsets"].get(toolset_name)
    verification_profile = policy["verification_profiles"].get(verification_profile_name)
    if not isinstance(authority, dict) or not isinstance(tools, list) or not isinstance(verification_profile, dict):
        raise HarnessError(f"task type `{task_type}` has unresolved route profiles")
    evidence_artifacts = _evidence_artifact_policy(policy)
    artifact_handoff_policy = _artifact_handoff_policy(policy, route)
    tool_bindings = [
        {
            "tool": name,
            "host_kind": policy["tools"][name]["host_kind"],
            "writer_access": policy["tools"][name]["writer_access"],
            "validator_access": policy["tools"][name]["validator_access"],
            "root_probe": policy["tools"][name]["root_probe"],
        }
        for name in tools
    ]
    skills, skill_sets = _resolve_skill_sets(policy, route, skill_set_selections or [])
    packet = {
        "task_type": task_type,
        "template": template,
        "role": route["role"],
        "rules": list(dict.fromkeys([*route["rules"], *orchestration["rules"]])),
        "skills": skills,
        "authority": authority_name,
        "toolset": toolset_name,
        "verification_profile": verification_profile_name,
        "capabilities": list(authority["capabilities"]),
        "workspace_write_access": authority["workspace_write_access"],
        "delegation_profile": route["delegation_profile"],
        "tools": list(tools),
        "tool_bindings": tool_bindings,
        "workspace": policy["defaults"]["source_workspace"],
        "context_limits": copy.deepcopy(policy["context_limits"]),
        "retained_artifacts": [
            {"kind": kind, "max_bytes": policy["context_limits"]["artifact_max_bytes"]}
            for kind in evidence_artifacts["writer_retained_kinds"]
            if authority["workspace_write_access"] == "workspace_write"
        ],
        "artifact_handoff_policy": artifact_handoff_policy,
        "orchestration": {
            "name": execution_mode,
            "work_scheduling": orchestration["work_scheduling"],
            "max_parallel_lanes": orchestration.get("max_parallel_lanes", orchestration["max_parallel_writers"]),
            "max_parallel_writers": orchestration["max_parallel_writers"],
            "workspace_mode": orchestration["workspace_mode"],
            "validator_role": orchestration["validator_role"],
        },
        "checks": {name: policy["checks"][name]["command"] for name in verification_profile["checks"]},
        "postconditions": list(verification_profile["postconditions"]),
        "approval_gates": {
            name: policy["approval_gates"][name]["paths"]
            for name in route.get("approval_gates", policy["defaults"]["approval_gates"])
        },
        "retry_policy": copy.deepcopy(policy["retry_policies"][policy["defaults"]["retry_policy"]]),
        "execution_budget": _resolve_execution_budget(
            policy,
            profile_name=execution_budget_profile,
        ),
        "allowed_next_states": copy.deepcopy(CORE_STATE_TRANSITIONS),
    }
    if skill_sets is not None:
        packet["skill_sets"] = skill_sets
    if profile_metadata is not None:
        packet["operating_profile"] = profile_metadata
        packet["runtime_provider_id"] = runtime_provider_id
    return packet


def _resolve_runtime_provider(
    policy: dict[str, Any],
    task_type: str,
    value: Any,
    *,
    packet_api: int,
) -> dict[str, Any]:
    route = policy["routes"].get(task_type)
    if not isinstance(route, dict):
        raise HarnessError(f"unknown task type `{task_type}`")
    provider_id = policy["defaults"]["runtime_provider"] if value is None else _required_string(value, "runtime_provider_id")
    if provider_id != policy["defaults"]["runtime_provider"]:
        raise HarnessError(f"runtime provider `{provider_id}` is not allowed for task type `{task_type}`")
    provider = policy["runtime_providers"].get(provider_id)
    if not isinstance(provider, dict) or not isinstance(provider.get("contract_version"), int):
        raise HarnessError(f"unknown runtime provider `{provider_id}`")
    contract_version = 2 if provider_id == "codex_app_server" and packet_api == 3 else provider["contract_version"]
    return {"provider_id": provider_id, "contract_version": contract_version}


def _resolve_commit(root: Path, base_ref: str) -> str:
    status, stdout, stderr = _run_command(root, ["git", "rev-parse", "--verify", f"{base_ref}^{{commit}}"])
    if status:
        raise HarnessError(f"could not resolve base commit `{base_ref}`: {stderr.strip()}")
    return stdout.strip()


def _safe_run_id(value: Any) -> str:
    run_id = _required_string(value, "run_id")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise HarnessError("run_id must contain only letters, digits, underscores, and hyphens")
    return run_id


def _run_path(root: Path, run_id: str) -> Path:
    return root / ".harness" / "runs" / _safe_run_id(run_id) / "run.json"


@contextmanager
def _run_lock(root: Path, run_id: str):
    target = _run_path(root, run_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    lock = target.with_name(f".{target.name}.lock")
    deadline = time.monotonic() + 10
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise HarnessError(f"run `{run_id}` is locked")
            time.sleep(0.01)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _write_run(root: Path, run: dict[str, Any]) -> None:
    target = _run_path(root, run["run_id"])
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    revision = run.get("run_revision", 0)
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise HarnessError("run_revision is invalid")
    run["run_revision"] = revision + 1
    try:
        with temporary.open("wb") as handle:
            handle.write(_canonical_json_bytes(run))
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _load_run(root: Path, run_id: str) -> dict[str, Any]:
    run = _load_json(_run_path(root, run_id))
    if run.get("version") not in {1, CURRENT_RUN_API} or run.get("run_id") != run_id or not isinstance(run.get("attempts"), list):
        raise HarnessError(f"invalid run record `{run_id}`")
    if "run_revision" not in run:
        run["run_revision"] = 0
    if run.get("state") == "planned" and run["attempts"]:
        attempt = run["attempts"][-1]
        if not isinstance(attempt, dict):
            raise HarnessError(f"invalid run record `{run_id}`")
        if "nodes" not in attempt:
            lanes = attempt.get("lanes")
            if not isinstance(lanes, list):
                return run
            nodes = copy.deepcopy(lanes)
            for node in nodes:
                if not isinstance(node, dict):
                    raise HarnessError(f"planned run `{run_id}` has invalid execution node")
                if "node_kind" not in node:
                    node["node_kind"] = "agent" if node.get("kind") in {"work", "validate"} else "integration"
            validator = next((node for node in nodes if node.get("lane_id") == "validate"), None)
            if not isinstance(validator, dict):
                raise HarnessError(f"planned run `{run_id}` has no validator node")
            if not any(node.get("lane_id") == "check" for node in nodes):
                nodes.append({
                    "lane_id": "check",
                    "node_kind": "check",
                    "kind": "check",
                    "role": None,
                    "allowed_paths": copy.deepcopy(validator["allowed_paths"]),
                    "dependencies": ["validate"],
                    "workspace_mode": validator["workspace_mode"],
                    "write_capable": False,
                })
            attempt["nodes"] = nodes
            attempt["node_observations"] = []
    return run


ACTIVE_RUN_STATES = {"planned", "running", "observed", "verifying", "orphaned", "awaiting_decision"}
TERMINAL_RUN_STATES = {"accepted", "unvalidated", "blocked"}
HANDOFF_FIELDS = {"last_verified_fact", "next_action", "blocker_or_decision"}


def _all_runs(root: Path) -> list[dict[str, Any]]:
    runs_root = root / ".harness" / "runs"
    if not runs_root.is_dir():
        return []
    runs: list[dict[str, Any]] = []
    for path in sorted(runs_root.glob("*/run.json")):
        payload = _load_json(path)
        run_id = payload.get("run_id")
        if not isinstance(run_id, str):
            raise HarnessError(f"invalid run record `{path}`")
        runs.append(_load_run(root, run_id))
    return runs


def _run_sort_key(run: dict[str, Any]) -> tuple[str, str]:
    history = run.get("state_history")
    if isinstance(history, list) and history and isinstance(history[-1], dict):
        timestamp = history[-1].get("at")
        if isinstance(timestamp, str):
            return timestamp, run["run_id"]
    return "", run["run_id"]


def _matching_plan_runs(root: Path, plan_ref: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for run in _all_runs(root):
        if not run["attempts"] or not isinstance(run["attempts"][-1], dict):
            continue
        attempt = run["attempts"][-1]
        packet = attempt.get("packet")
        if isinstance(packet, dict) and packet.get("plan_ref") == plan_ref:
            matches.append((run, attempt))
    return matches


def coordination_status(root: Path, plan_ref: str) -> dict[str, Any]:
    try:
        coordination = load_plan_coordination(root, plan_ref, require_active=True)
    except PlanCoordinationError as exc:
        raise HarnessError(str(exc)) from exc
    if coordination is None:
        raise HarnessError(f"plan `{plan_ref}` has no coordination manifest")
    runs_by_task: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {
        task.task_id: [] for task in coordination.tasks
    }
    for run, attempt in _matching_plan_runs(root, coordination.plan_ref):
        packet = attempt.get("packet", {})
        task_id = packet.get("plan_task_id") if isinstance(packet, dict) else None
        if task_id in runs_by_task:
            runs_by_task[task_id].append((run, attempt))

    statuses: dict[str, dict[str, Any]] = {}

    def derive(task: PlanTask) -> dict[str, Any]:
        if task.task_id in statuses:
            return statuses[task.task_id]
        matching = sorted(runs_by_task[task.task_id], key=lambda item: _run_sort_key(item[0]))
        if matching:
            run, attempt = matching[-1]
            state = run["state"]
            if state in ACTIVE_RUN_STATES:
                status = {"id": task.task_id, "state": "active", "run_id": run["run_id"], "reason": state}
            elif state == "accepted":
                status = {"id": task.task_id, "state": "done", "run_id": run["run_id"], "reason": state}
            elif state in TERMINAL_RUN_STATES:
                status = {"id": task.task_id, "state": "blocked", "run_id": run["run_id"], "reason": state}
            else:
                raise HarnessError(f"run `{run['run_id']}` has unsupported coordination state `{state}`")
            handoff = attempt.get("handoff")
            if isinstance(handoff, dict):
                status["handoff"] = copy.deepcopy(handoff)
            statuses[task.task_id] = status
            return status
        dependency_states = [derive(coordination.task(task_id))["state"] for task_id in task.depends_on]
        status = {
            "id": task.task_id,
            "state": "ready" if all(state == "done" for state in dependency_states) else "blocked",
            "reason": "ready" if all(state == "done" for state in dependency_states) else "waiting_dependencies",
        }
        statuses[task.task_id] = status
        return status

    return {
        "plan_ref": coordination.plan_ref,
        "target_branch": coordination.target_branch,
        "base_ref": coordination.base_ref,
        "plan_digest": coordination.digest,
        "tasks": [derive(task) for task in coordination.tasks],
    }


def record_controller_handoff(root: Path, run_id: str, handoff: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(handoff, dict) or set(handoff) != HANDOFF_FIELDS:
        raise HarnessError(f"handoff must contain only: {', '.join(sorted(HANDOFF_FIELDS))}")
    normalized = {field: _required_string(handoff.get(field), f"handoff {field}") for field in HANDOFF_FIELDS}
    run = _load_run(root, _safe_run_id(run_id))
    if run["state"] in TERMINAL_RUN_STATES:
        raise HarnessError("cannot record handoff for terminal run")
    attempt = _active_attempt(run)
    packet = attempt.get("packet")
    if not isinstance(packet, dict) or "plan_ref" not in packet or "plan_task_id" not in packet:
        raise HarnessError("controller handoff requires a coordinated run")
    attempt["handoff"] = {**normalized, "timestamp": _timestamp()}
    _write_run(root, run)
    return {"run_id": run["run_id"], "handoff": copy.deepcopy(attempt["handoff"])}


def _planned_paths_overlap(left: list[str], right: list[str]) -> bool:
    return any(_path_matches(left_path, [right_path]) or _path_matches(right_path, [left_path]) for left_path in left for right_path in right)


def _admit_coordinated_packet(root: Path, packet: dict[str, Any]) -> None:
    if "plan_ref" not in packet:
        return
    plan_ref = _required_string(packet.get("plan_ref"), "packet plan_ref")
    task_id = _required_string(packet.get("plan_task_id"), "packet plan_task_id")
    status = coordination_status(root, plan_ref)
    task_status = next((task for task in status["tasks"] if task["id"] == task_id), None)
    if not isinstance(task_status, dict) or task_status["state"] != "ready":
        reason = task_status.get("reason", "missing") if isinstance(task_status, dict) else "missing"
        raise HarnessError(f"coordinated task `{task_id}` is not ready: {reason}")
    for run in _all_runs(root):
        if run["state"] not in ACTIVE_RUN_STATES or not run["attempts"]:
            continue
        active_packet = run["attempts"][-1].get("packet")
        if not isinstance(active_packet, dict) or "plan_ref" not in active_packet:
            continue
        if active_packet["plan_ref"] == plan_ref:
            raise HarnessError(f"coordinated task activation blocked by active run `{run['run_id']}`")
        try:
            active_coordination = load_plan_coordination(root, active_packet["plan_ref"], require_active=False)
        except PlanCoordinationError as exc:
            raise HarnessError(f"cannot evaluate active coordinated run `{run['run_id']}`: {exc}") from exc
        if active_coordination is None or active_coordination.target_branch != status["target_branch"]:
            continue
        if _planned_paths_overlap(packet["planned_write_paths"], active_packet.get("planned_write_paths", [])):
            raise HarnessError(f"coordinated task paths conflict with active run `{run['run_id']}`")


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HarnessError("approval issued_at must be an ISO-8601 timestamp") from exc


def _friction_events_path(root: Path) -> Path:
    return root / ".harness" / "friction-events.jsonl"


def _friction_time(value: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HarnessError("friction event timestamp must be an ISO-8601 timestamp") from exc
    if timestamp.tzinfo is None:
        raise HarnessError("friction event timestamp must include timezone")
    return timestamp.astimezone(UTC)


def _friction_fingerprint(
    *,
    route: str,
    provider: str,
    mode: str,
    lane_kind: str,
    phase: str,
    source: str,
    code: str,
) -> str:
    payload = {
        "version": FRICTION_EVENT_VERSION,
        "route": route,
        "provider": provider,
        "mode": mode,
        "lane_kind": lane_kind,
        "phase": phase,
        "source": source,
        "code": code,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return f"v{FRICTION_EVENT_VERSION}:{digest}"


def _append_friction_event(root: Path, event: dict[str, Any]) -> dict[str, Any]:
    path = _friction_events_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def _read_friction_events(root: Path) -> list[dict[str, Any]]:
    path = _friction_events_path(root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HarnessError(f"invalid friction event at line {line_number}") from exc
        if not isinstance(event, dict) or event.get("version") != FRICTION_EVENT_VERSION:
            raise HarnessError(f"invalid friction event at line {line_number}")
        if event.get("kind") not in FRICTION_EVENT_KINDS or not isinstance(event.get("event_id"), str) or not event["event_id"]:
            raise HarnessError(f"invalid friction event at line {line_number}")
        _friction_time(_required_string(event.get("occurred_at"), "friction event occurred_at"))
        if event["kind"] == "observed":
            required = {
                "run_id", "attempt_id", "route", "provider", "mode", "lane_kind",
                "phase", "source", "code", "evidence_ref", "fingerprint",
            }
            if (
                not required.issubset(event)
                or not all(isinstance(event[name], str) and event[name] for name in required)
                or event["source"] not in FRICTION_SOURCES
                or event["phase"] not in FRICTION_PHASES
            ):
                raise HarnessError(f"invalid friction event at line {line_number}")
        else:
            required = {"run_id", "fingerprint", "decision", "observed_event_ids"}
            observed_event_ids = event.get("observed_event_ids")
            if (
                not required.issubset(event)
                or not all(isinstance(event[name], str) and event[name] for name in required - {"observed_event_ids"})
                or not isinstance(observed_event_ids, list)
                or not observed_event_ids
                or not all(isinstance(event_id, str) and event_id for event_id in observed_event_ids)
                or event["decision"] not in FRICTION_RESOLUTIONS
            ):
                raise HarnessError(f"invalid friction event at line {line_number}")
        events.append(event)
    return events


def record_friction_event(
    root: Path,
    *,
    run_id: str,
    attempt_id: str,
    packet: dict[str, Any],
    lane: dict[str, Any] | None,
    source: str,
    phase: str,
    code: str,
    evidence_ref: str,
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    _friction_policy(root)
    if source not in FRICTION_SOURCES:
        raise HarnessError("unsupported friction source")
    if phase not in FRICTION_PHASES:
        raise HarnessError("unsupported friction phase")
    route = _required_string(packet.get("task_type"), "friction route")
    provider = packet.get("runtime_provider")
    if not isinstance(provider, dict):
        raise HarnessError("friction packet lacks runtime provider")
    provider_id = _required_string(provider.get("provider_id"), "friction provider")
    contract_version = provider.get("contract_version")
    if not isinstance(contract_version, int):
        raise HarnessError("friction packet has invalid runtime provider")
    orchestration = packet.get("orchestration")
    if not isinstance(orchestration, dict):
        raise HarnessError("friction packet lacks orchestration")
    mode = _required_string(orchestration.get("name"), "friction mode")
    lane_kind = "system" if lane is None else _required_string(lane.get("kind"), "friction lane kind")
    timestamp = (occurred_at or datetime.now(UTC)).astimezone(UTC).isoformat()
    event = {
        "version": FRICTION_EVENT_VERSION,
        "kind": "observed",
        "event_id": f"friction-{uuid.uuid4().hex}",
        "run_id": _safe_run_id(run_id),
        "attempt_id": _required_string(attempt_id, "friction attempt_id"),
        "route": route,
        "provider": f"{provider_id}:{contract_version}",
        "mode": mode,
        "lane_kind": lane_kind,
        "phase": phase,
        "source": source,
        "code": _required_string(code, "friction code"),
        "evidence_ref": _required_string(evidence_ref, "friction evidence_ref"),
        "occurred_at": timestamp,
    }
    event["fingerprint"] = _friction_fingerprint(
        route=event["route"],
        provider=event["provider"],
        mode=event["mode"],
        lane_kind=event["lane_kind"],
        phase=event["phase"],
        source=event["source"],
        code=event["code"],
    )
    return _append_friction_event(root, event)


def _friction_readonly_artifact_requests(
    root: Path,
    observed: list[dict[str, Any]],
) -> list[dict[str, str]]:
    requests: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for event in sorted(observed, key=lambda item: (item["occurred_at"], item["event_id"]), reverse=True):
        try:
            source_run_id = _safe_run_id(event["run_id"])
            source_attempt_id = _required_string(event["attempt_id"], "friction source attempt_id")
            source_attempt = _source_attempt(_load_run(root, source_run_id), source_attempt_id)
            _stored_artifact_content(source_attempt, "terminal_observation")
        except HarnessError:
            continue
        key = (source_run_id, source_attempt_id)
        if key in seen:
            continue
        requests.append({"run_id": source_run_id, "attempt_id": source_attempt_id})
        seen.add(key)
    return requests


def friction_report(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    policy = _friction_policy(root)
    route_policy = _load_policy(root)
    routes = route_policy["routes"]
    current = (now or datetime.now(UTC)).astimezone(UTC)
    cutoff = current - timedelta(days=policy["window_days"])
    events = _read_friction_events(root)
    resolved_at: dict[str, datetime] = {}
    for event in events:
        if event["kind"] != "resolution":
            continue
        resolved = _friction_time(event["occurred_at"])
        if resolved <= current:
            resolved_at[event["fingerprint"]] = max(resolved_at.get(event["fingerprint"], resolved), resolved)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event["kind"] != "observed":
            continue
        occurred_at = _friction_time(event["occurred_at"])
        if not cutoff <= occurred_at <= current or occurred_at <= resolved_at.get(event["fingerprint"], datetime.min.replace(tzinfo=UTC)):
            continue
        grouped.setdefault(event["fingerprint"], []).append(event)
    candidates = []
    for fingerprint, observed in sorted(grouped.items()):
        run_ids = sorted({event["run_id"] for event in observed})
        if len(run_ids) < policy["minimum_distinct_runs"]:
            continue
        candidate = {
            "fingerprint": fingerprint,
            "event_ids": sorted(event["event_id"] for event in observed),
            "run_ids": run_ids,
            "event_count": len(observed),
            "distinct_run_count": len(run_ids),
            "first_observed_at": min(event["occurred_at"] for event in observed),
            "last_observed_at": max(event["occurred_at"] for event in observed),
        }
        task_type = policy["follow_up_routes"].get(observed[0]["code"])
        if task_type is not None:
            route = routes[task_type]
            authority = route_policy["authorities"][route["authority"]]
            sources = _friction_readonly_artifact_requests(root, observed)
            handoff_policy = _artifact_handoff_policy(route_policy, route)
            profile_name = "friction_terminal_diagnosis"
            try:
                _resolve_artifact_handoff_sources(
                    root,
                    {
                        "workspace_write_access": authority["workspace_write_access"],
                        "artifact_handoff_policy": handoff_policy,
                    },
                    profile_name,
                    sources,
                )
            except HarnessError:
                candidate["follow_up_blocked"] = "missing_required_readonly_artifacts"
            else:
                candidate["follow_up"] = {
                    "task_type": task_type,
                    "execution_mode": "single_work_lane",
                    "workspace_write_access": authority["workspace_write_access"],
                    "artifact_handoff": {"profile": profile_name},
                }
        candidates.append(candidate)
    return {
        "version": FRICTION_EVENT_VERSION,
        "minimum_distinct_runs": policy["minimum_distinct_runs"],
        "window_days": policy["window_days"],
        "candidates": candidates,
    }


def resolve_friction(
    root: Path,
    run_id: str,
    fingerprint: str,
    decision: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    if decision not in FRICTION_RESOLUTIONS:
        raise HarnessError("unsupported friction resolution")
    run = _load_run(root, _safe_run_id(run_id))
    if run.get("state") != "accepted" or run.get("request", {}).get("task_type") != "harness_improvement":
        raise HarnessError("friction resolution requires accepted harness_improvement run")
    candidate = next((item for item in friction_report(root, now=now)["candidates"] if item["fingerprint"] == fingerprint), None)
    if candidate is None:
        raise HarnessError("friction resolution requires current candidate")
    event = {
        "version": FRICTION_EVENT_VERSION,
        "kind": "resolution",
        "event_id": f"friction-resolution-{uuid.uuid4().hex}",
        "run_id": run["run_id"],
        "fingerprint": fingerprint,
        "decision": decision,
        "observed_event_ids": candidate["event_ids"],
        "occurred_at": ((now or datetime.now(UTC)).astimezone(UTC).isoformat()),
    }
    return _append_friction_event(root, event)


def _validate_criteria(value: Any, checks: dict[str, list[str]]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise HarnessError("acceptance_criteria must be a non-empty list")
    criteria: list[dict[str, Any]] = []
    seen: set[str] = set()
    validator_count = 0
    for raw in value:
        if not isinstance(raw, dict):
            raise HarnessError("managed acceptance criterion must be an object")
        criterion_id = _required_string(raw.get("id"), "criterion id")
        if criterion_id in seen:
            raise HarnessError(f"duplicate criterion id `{criterion_id}`")
        seen.add(criterion_id)
        kind = _required_string(raw.get("kind"), "criterion kind")
        if kind not in CRITERION_KINDS:
            raise HarnessError(f"unsupported criterion kind `{kind}`")
        criterion = copy.deepcopy(raw)
        if kind == "check":
            check = _required_string(raw.get("check"), "criterion check")
            if check not in checks:
                raise HarnessError(f"unknown criterion check `{check}`")
        if kind == "change_set":
            criterion["paths"] = _safe_paths(raw.get("paths"), "criterion paths", required=True)
        if kind == "validator":
            if criterion_id != "validator" or set(raw) != {"id", "kind"}:
                raise HarnessError("validator criterion must be exactly `{id: validator, kind: validator}`")
            validator_count += 1
        criteria.append(criterion)
    if validator_count > 1:
        raise HarnessError("duplicate validator criterion")
    if not validator_count:
        criteria.append({"id": "validator", "kind": "validator"})
    return criteria


def _validate_approvals(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise HarnessError("approvals must be a list")
    approvals: list[dict[str, Any]] = []
    for raw in value:
        if not isinstance(raw, dict):
            raise HarnessError("approval record must be an object")
        approval = copy.deepcopy(raw)
        approval["gate"] = _required_string(raw.get("gate"), "approval gate")
        approval["approver"] = _required_string(raw.get("approver"), "approval approver")
        approval["attempt_id"] = _required_string(raw.get("attempt_id"), "approval attempt_id")
        approval["issued_at"] = _required_string(raw.get("issued_at"), "approval issued_at")
        _parse_timestamp(approval["issued_at"])
        approval["paths"] = _safe_paths(raw.get("paths"), "approval paths", required=True)
        approvals.append(approval)
    return approvals


def _patterns_overlap(left: str, right: str) -> bool:
    if left == right:
        return True
    if left.endswith("/**"):
        return _path_matches(right, [left])
    if right.endswith("/**"):
        return _path_matches(left, [right])
    return fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left)


def _normalize_lanes(root: Path, packet: dict[str, Any], allowed_paths: list[str], value: Any) -> list[dict[str, Any]]:
    roles, claim_fields = _load_role_catalog(root)
    role_writes = lambda role: "repo.write" in (
        packet["capabilities"] if packet["version"] != 3 else legacy_role_capabilities(role)
    )

    def lane_claim_schema(role: str) -> dict[str, Any]:
        return _claim_schema(roles[role], claim_fields)

    if packet["orchestration"]["work_scheduling"] == "single":
        role = packet["role"]
        work_lanes = [{
            "lane_id": "primary",
            "node_kind": "agent",
            "kind": "work",
            "role": role,
            "allowed_paths": allowed_paths,
            "dependencies": [],
            "workspace_mode": packet["orchestration"]["workspace_mode"],
            "write_capable": role_writes(role),
            "required_claim_kind": roles[role]["result_kind"],
            "claim_schema": lane_claim_schema(role),
        }]
    else:
        if not isinstance(value, list) or not value:
            raise HarnessError("lanes must be a non-empty list for non-single topology")
        work_lanes = []
        lane_ids: set[str] = set()
        for raw in value:
            if not isinstance(raw, dict):
                raise HarnessError("lane must be an object")
            lane_id = _required_string(raw.get("lane_id"), "lane_id")
            if lane_id in {"integrate", "validate", "check"} or lane_id in lane_ids:
                raise HarnessError(f"duplicate or reserved lane_id `{lane_id}`")
            lane_ids.add(lane_id)
            role = _required_string(raw.get("role"), "lane role")
            if role not in roles:
                raise HarnessError(f"unknown lane role `{role}`")
            write_capable = raw.get("write_capable")
            if not isinstance(write_capable, bool) or write_capable != role_writes(role):
                raise HarnessError(f"lane `{lane_id}` has invalid write_capable")
            dependencies = _safe_paths(raw.get("dependencies", []), "lane dependencies", required=False)
            workspace_mode = _required_string(raw.get("workspace_mode"), "lane workspace_mode")
            if workspace_mode != packet["orchestration"]["workspace_mode"]:
                raise HarnessError(f"lane `{lane_id}` workspace_mode conflicts with execution mode")
            work_lanes.append({
                "lane_id": lane_id,
                "node_kind": "agent",
                "kind": "work",
                "role": role,
                "allowed_paths": _safe_paths(raw.get("allowed_paths"), "lane allowed_paths", required=True),
                "dependencies": dependencies,
                "workspace_mode": workspace_mode,
                "write_capable": write_capable,
                "required_claim_kind": roles[role]["result_kind"],
                "claim_schema": lane_claim_schema(role),
            })
    lane_ids = {lane["lane_id"] for lane in work_lanes}
    for lane in work_lanes:
        for dependency in lane["dependencies"]:
            if dependency == lane["lane_id"] or dependency not in lane_ids:
                raise HarnessError(f"lane `{lane['lane_id']}` has invalid dependency `{dependency}`")
    visiting: set[str] = set()
    visited: set[str] = set()
    dependencies = {lane["lane_id"]: lane["dependencies"] for lane in work_lanes}

    def visit(lane_id: str) -> None:
        if lane_id in visiting:
            raise HarnessError("lane dependencies contain a cycle")
        if lane_id in visited:
            return
        visiting.add(lane_id)
        for dependency in dependencies[lane_id]:
            visit(dependency)
        visiting.remove(lane_id)
        visited.add(lane_id)

    for lane_id in lane_ids:
        visit(lane_id)
    writable = [lane for lane in work_lanes if lane["write_capable"]]
    for index, lane in enumerate(writable):
        for other in writable[index + 1:]:
            if any(_patterns_overlap(path, other_path) for path in lane["allowed_paths"] for other_path in other["allowed_paths"]):
                raise HarnessError(f"writable lanes `{lane['lane_id']}` and `{other['lane_id']}` overlap")
    validator_role = packet["orchestration"]["validator_role"]
    validator = roles.get(validator_role)
    if not isinstance(validator, dict) or (packet["version"] == 3 and role_writes(validator_role)):
        raise HarnessError(f"invalid validator role `{validator_role}`")
    workspace_mode = packet["orchestration"]["workspace_mode"]
    return [
        *work_lanes,
        {
            "lane_id": "integrate",
            "node_kind": "integration",
            "kind": "integrate",
            "role": None,
            "allowed_paths": allowed_paths,
            "dependencies": [lane["lane_id"] for lane in work_lanes],
            "workspace_mode": workspace_mode,
            "write_capable": False,
            "required_claim_kind": "integration_result",
        },
        {
            "lane_id": "validate",
            "node_kind": "agent",
            "kind": "validate",
            "role": validator_role,
            "allowed_paths": allowed_paths,
            "dependencies": ["integrate"],
            "workspace_mode": workspace_mode,
            "write_capable": False,
            "required_claim_kind": validator["result_kind"],
            "claim_schema": lane_claim_schema(validator_role),
        },
        {
            "lane_id": "check",
            "node_kind": "check",
            "kind": "check",
            "role": None,
            "allowed_paths": allowed_paths,
            "dependencies": ["validate"],
            "workspace_mode": workspace_mode,
            "write_capable": False,
        },
    ]


def _normalize_managed_request(
    root: Path,
    policy: dict[str, Any],
    request: dict[str, Any],
) -> tuple[dict[str, Any], PlanCoordination | None, PlanTask | None]:
    version = request.get("version")
    admission = admit_request_api(version)
    if not admission["ok"]:
        raise HarnessError(admission["code"])
    core_policy = policy.get("harness_core")
    if not isinstance(core_policy, dict) or version != core_policy.get("request_api"):
        raise HarnessError("managed request API must match policy request_api")
    normalized = copy.deepcopy(request)
    normalized["execution_mode"] = _canonical_execution_mode(
        policy,
        normalized.get("execution_mode"),
        allow_alias=admission["packet_api"] == 3,
        default="single_agent" if admission["packet_api"] == 3 else "single_work_lane",
    )
    has_plan_ref = "plan_ref" in normalized
    has_plan_task_id = "plan_task_id" in normalized
    if has_plan_ref != has_plan_task_id:
        raise HarnessError("managed request requires both `plan_ref` and `plan_task_id`")
    if not has_plan_ref:
        return normalized, None, None
    plan_ref = _required_string(normalized["plan_ref"], "plan_ref")
    plan_task_id = _required_string(normalized["plan_task_id"], "plan_task_id")
    try:
        coordination = load_plan_coordination(root, plan_ref, require_active=True)
        if coordination is None:
            raise HarnessError(f"plan `{plan_ref}` has no coordination manifest")
        plan_task = coordination.task(plan_task_id)
    except PlanCoordinationError as exc:
        raise HarnessError(str(exc)) from exc
    derived = {
        "execution_mode": plan_task.execution_mode,
        "base_ref": coordination.base_ref,
        "allowed_paths": list(plan_task.allowed_paths),
        "planned_write_paths": list(plan_task.planned_write_paths),
    }
    for field, value in derived.items():
        if field in request and normalized.get(field) != value:
            raise HarnessError(f"managed request `{field}` conflicts with plan coordination")
        normalized[field] = value
    normalized["plan_ref"] = coordination.plan_ref
    normalized["plan_task_id"] = plan_task.task_id
    return normalized, coordination, plan_task


def resolve_managed_packet(
    root: Path,
    request: dict[str, Any],
    *,
    attempt_id: str,
    execution_budget_profile: str | None = None,
    core_identity: dict[str, Any] | None = None,
    provider_runtime_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = _load_policy(root)
    _validate_policy(root)
    request, coordination, plan_task = _normalize_managed_request(root, policy, request)
    request_admission = admit_request_api(request["version"])
    if not request_admission["ok"]:
        raise HarnessError(request_admission["code"])
    packet_api = request_admission["packet_api"]
    resolved_core_identity = core_identity or _core_identity(policy, request_api=request["version"])
    task_type = _required_string(request.get("task_type"), "task_type")
    execution_mode = _required_string(request.get("execution_mode"), "execution_mode")
    route = policy["routes"].get(task_type)
    if not isinstance(route, dict):
        raise HarnessError(f"unknown task type `{task_type}`")
    if "execution_budget_profile" in request:
        raise HarnessError("managed request cannot select execution budget profile")
    skill_set_selections = _normalize_skill_set_selections(request, route)
    operating_profile_selection = _normalize_operating_profile_selection(request, route)
    packet = _route_packet(
        policy,
        task_type,
        execution_mode,
        execution_budget_profile=execution_budget_profile,
        skill_set_selections=skill_set_selections,
        operating_profile_selection=operating_profile_selection,
    )
    if packet_api == 3:
        packet["capabilities"] = list(legacy_role_capabilities(packet["role"]))
    resolved_provider_id = packet.get("runtime_provider_id")
    requested_provider_id = request.get("runtime_provider_id")
    if resolved_provider_id is not None and requested_provider_id not in {None, resolved_provider_id}:
        _resolve_runtime_provider(
            policy,
            task_type,
            requested_provider_id,
            packet_api=packet_api,
        )
        raise HarnessError("runtime_provider_id conflicts with operating profile")
    runtime_provider = _resolve_runtime_provider(
        policy,
        task_type,
        resolved_provider_id if resolved_provider_id is not None else requested_provider_id,
        packet_api=packet_api,
    )
    if packet_api == CURRENT_PACKET_API:
        provider_runtime_binding = _validate_provider_runtime_binding(
            provider_runtime_binding,
            runtime_provider,
            packet_api=packet_api,
            host_api=resolved_core_identity.get("host_api"),
        )
    role = _load_roles(root).get(packet["role"])
    if not isinstance(role, dict):
        raise HarnessError(f"unknown route role `{packet['role']}`")
    allowed_paths = _safe_paths(request.get("allowed_paths"), "allowed_paths", required=True)
    planned_write_paths = _safe_paths(
        request.get("planned_write_paths"),
        "planned_write_paths",
        required="repo.write" in packet["capabilities"],
    )
    if coordination is not None and any(not _path_matches(path, allowed_paths) for path in planned_write_paths):
        raise HarnessError("plan planned_write_paths must stay within managed allowed_paths")
    base_ref = _required_string(request.get("base_ref"), "base_ref")
    base_commit = _resolve_commit(root, base_ref)
    user_request = _required_string(request.get("user_request"), "user_request")
    work_context = _normalize_work_context(
        policy,
        user_request=user_request,
        role=role,
        base_commit=base_commit,
        value=request.get("work_context"),
    )
    packet.update({
        "version": packet_api,
        "core_identity": copy.deepcopy(resolved_core_identity),
        "attempt_id": attempt_id,
        "base_ref": base_ref,
        "base_commit": base_commit,
        "user_request": user_request,
        "work_context": work_context,
        "runtime_provider": runtime_provider,
        "agent_identity": _load_agent_identity(root, packet["template"]),
        "allowed_paths": allowed_paths,
        "planned_write_paths": planned_write_paths,
        "workspace_write_access": "workspace_write" if "repo.write" in packet["capabilities"] else "read_only",
        "acceptance_criteria": _validate_criteria(request.get("acceptance_criteria"), packet["checks"]),
        "approvals": _validate_approvals(request.get("approvals")),
        "review_evidence": copy.deepcopy(request.get("review_evidence")),
        "manual_evidence": copy.deepcopy(request.get("manual_evidence")),
    })
    if packet_api == CURRENT_PACKET_API:
        packet["claim_repair"] = copy.deepcopy(policy["claim_repair"])
    if provider_runtime_binding is not None:
        packet["provider_runtime_binding"] = provider_runtime_binding
    if "readonly_artifacts" in request:
        raise HarnessError("request API 5 rejects readonly_artifacts")
    packet["readonly_artifacts"], handoff = _resolve_artifact_handoff(root, packet, request.get("artifact_handoff"))
    if handoff is not None:
        packet["artifact_handoff"] = handoff["proof"]
        packet["artifact_handoff_audit"] = handoff["audit"]
    if coordination is not None and plan_task is not None:
        packet.update({
            "plan_ref": coordination.plan_ref,
            "plan_task_id": plan_task.task_id,
            "plan_digest": coordination.digest,
        })
    packet["lanes"] = _normalize_lanes(root, packet, allowed_paths, request.get("lanes"))
    if packet_api == CURRENT_PACKET_API:
        try:
            packet["execution_lease"] = resolve_execution_lease(
                policy["execution_budgets"]["lease_duration_model"],
                lanes=packet["lanes"],
                checks=packet["checks"],
                max_parallel_lanes=packet["orchestration"]["max_parallel_lanes"],
                max_parallel_writers=packet["orchestration"]["max_parallel_writers"],
                turn_timeout_seconds=packet["execution_budget"]["turn_timeout_seconds"],
            )
        except ExecutionLeaseError as exc:
            raise HarnessError(str(exc)) from exc
        provider_contract = policy["runtime_providers"][runtime_provider["provider_id"]]
        packet["terminal_observation_contract"] = {
            "schema_id": "host_terminal_observation/v2",
            "capability": provider_contract["terminal_observation_capability"],
        }
    if packet["version"] in {4, CURRENT_PACKET_API}:
        packet["invocation_id"] = f"{attempt_id}:primary"
        packet["parent_invocation_id"] = None
    return packet


def _transition(run: dict[str, Any], states: dict[str, list[str]], next_state: str, reason: str) -> None:
    current_state = run["state"]
    if next_state not in states.get(current_state, []):
        raise HarnessError(f"invalid managed transition `{current_state}` to `{next_state}`")
    run["state"] = next_state
    run["state_history"].append({"state": next_state, "reason": reason, "at": _timestamp()})


def _new_run(request: dict[str, Any], run_id: str) -> dict[str, Any]:
    return {
        "version": CURRENT_RUN_API if admit_request_api(request.get("version")).get("packet_api") == CURRENT_PACKET_API else 1,
        "run_id": run_id,
        "request": copy.deepcopy(request),
        "state": "classified",
        "state_history": [{"state": "classified", "reason": "created", "at": _timestamp()}],
        "run_revision": 0,
        "attempts": [],
    }


def _append_attempt(run: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    attempt = {
        "attempt_id": packet["attempt_id"],
        "packet": copy.deepcopy(packet),
        "nodes": copy.deepcopy(packet["lanes"]),
        "claims": [],
        "node_observations": [],
        "evidence": {},
        "artifact_handoff_audit": copy.deepcopy(packet.get("artifact_handoff_audit")),
        "friction_event_ids": [],
        "execution_lease": None,
        "host_terminal_observations": [],
        "host_observation_digests": [],
        "terminal_record": None,
        "cancellation_request": None,
        "recovery_blocked": None,
        "outcome": None,
        "decision": None,
        "decision_history": [],
    }
    run["attempts"].append(attempt)
    return attempt


def _active_attempt(run: dict[str, Any]) -> dict[str, Any]:
    if not run["attempts"] or not isinstance(run["attempts"][-1], dict):
        raise HarnessError("run has no active attempt")
    return run["attempts"][-1]


_TERMINALIZATION_FIELDS = {"attempt_id", "host_terminal_observations"}
_TERMINALIZATION_RECOVERY_FIELDS = _TERMINALIZATION_FIELDS | {"recovery_observation"}
_TERMINALIZATION_STRANDED_RECOVERY_FIELDS = _TERMINALIZATION_FIELDS | {"stranded_recovery"}
_TERMINALIZATION_LEGACY_FIELDS = {"attempt_id", "legacy_cleanup_attestation"}
_TERMINALIZATION_OUTCOME_FIELDS = {"attempt_id", "outcome_id", "outcome_digest", "requested_decision", "controller_authorization"}
_STRANDED_RECOVERY_FIELDS = {"reason", "external_failure"}
_RECOVERY_OBSERVATION_FIELDS = {
    "lease_id",
    "lease_epoch",
    "host_instance_id",
    "observed_at",
    "host_process_absent",
    "root_processes_absent",
}
_CANCELLATION_FIELDS = {"attempt_id", "actor", "reason"}


def _attempt_lease_binding(run: dict[str, Any], attempt: dict[str, Any]) -> dict[str, Any]:
    lease = attempt.get("execution_lease")
    required = {
        "run_id",
        "attempt_id",
        "packet_sha256",
        "lease_id",
        "lease_epoch",
        "host_instance_id",
        "issued_at",
        "expires_at",
        "state",
    }
    if not isinstance(lease, dict) or required - lease.keys():
        raise HarnessError("attempt lacks execution lease")
    binding = {
        "run_id": run["run_id"],
        "attempt_id": attempt.get("attempt_id"),
        "packet_sha256": _canonical_digest(attempt.get("packet")),
        "lease_id": lease.get("lease_id"),
        "lease_epoch": lease.get("lease_epoch"),
        "host_instance_id": lease.get("host_instance_id"),
    }
    if (
        lease.get("run_id") != binding["run_id"]
        or lease.get("attempt_id") != binding["attempt_id"]
        or lease.get("packet_sha256") != binding["packet_sha256"]
        or not isinstance(binding["lease_id"], str)
        or not isinstance(binding["host_instance_id"], str)
        or not isinstance(binding["lease_epoch"], int)
        or isinstance(binding["lease_epoch"], bool)
        or binding["lease_epoch"] <= 0
        or lease.get("state") not in {"active", "recovery_blocked", "released"}
    ):
        raise HarnessError("attempt execution lease is invalid")
    _parse_timestamp(lease["issued_at"])
    _parse_timestamp(lease["expires_at"])
    return binding


def _issue_execution_lease(
    run: dict[str, Any],
    attempt: dict[str, Any],
    *,
    host_instance_id: str,
    now: datetime,
) -> dict[str, Any]:
    if attempt.get("execution_lease") is not None:
        raise HarnessError("attempt execution lease already exists")
    packet = attempt.get("packet")
    if not isinstance(packet, dict):
        raise HarnessError("attempt packet is invalid")
    duration = packet.get("execution_lease")
    seconds = duration.get("execution_lease_seconds") if isinstance(duration, dict) else None
    if not isinstance(seconds, int) or isinstance(seconds, bool) or seconds <= 0:
        raise HarnessError("packet execution lease duration is invalid")
    if not isinstance(host_instance_id, str) or not host_instance_id:
        raise HarnessError("host instance identity is invalid")
    issued_at = now.astimezone(UTC)
    lease = {
        "run_id": run["run_id"],
        "attempt_id": attempt["attempt_id"],
        "packet_sha256": _canonical_digest(packet),
        "lease_id": f"lease-{uuid.uuid4().hex}",
        "lease_epoch": len(run["attempts"]),
        "host_instance_id": host_instance_id,
        "issued_at": issued_at.isoformat(),
        "expires_at": (issued_at + timedelta(seconds=seconds)).isoformat(),
        "state": "active",
    }
    attempt["execution_lease"] = lease
    return copy.deepcopy(lease)


def _dispatch_packet(packet: dict[str, Any], execution_lease: dict[str, Any] | None) -> dict[str, Any]:
    if execution_lease is None:
        return packet
    runtime_packet = copy.deepcopy(packet)
    runtime_packet["execution_lease_binding"] = copy.deepcopy(execution_lease)
    return runtime_packet


def _record_host_terminal_observation(attempt: dict[str, Any], packet: dict[str, Any], evidence: Any) -> None:
    if packet.get("version") != CURRENT_PACKET_API:
        return
    observation = evidence.get("host_terminal_observation") if isinstance(evidence, dict) else None
    if not isinstance(observation, dict):
        raise HarnessError("host adapter lane evidence lacks terminal observation")
    observations = attempt.setdefault("host_terminal_observations", [])
    if not isinstance(observations, list):
        raise HarnessError("attempt terminal observations are invalid")
    observation_id = observation.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id:
        raise HarnessError("host terminal observation identity is invalid")
    if any(isinstance(item, dict) and item.get("observation_id") == observation_id for item in observations):
        raise HarnessError("host terminal observation is duplicated")
    observations.append(copy.deepcopy(observation))


def _terminalize_collected_attempt(root: Path, run: dict[str, Any], attempt: dict[str, Any]) -> dict[str, Any]:
    observations = attempt.get("host_terminal_observations")
    if not isinstance(observations, list) or not observations:
        raise HarnessError("attempt lacks host terminal observations")
    _write_run(root, run)
    terminalize_attempt(
        root,
        run["run_id"],
        {"attempt_id": attempt["attempt_id"], "host_terminal_observations": observations},
    )
    return _managed_result(_load_run(root, run["run_id"]))


def _has_terminal_host_failure(attempt: dict[str, Any]) -> bool:
    observations = attempt.get("host_terminal_observations")
    return isinstance(observations, list) and any(
        isinstance(observation, dict) and observation.get("source") != "completed"
        for observation in observations
    )


def _packet_check_lane_ids(packet: dict[str, Any]) -> set[str]:
    checks = packet.get("checks")
    if not isinstance(checks, dict):
        return set()
    return {f"check:{name}" for name in checks if isinstance(name, str)}


def _has_completed_host_observations(attempt: dict[str, Any]) -> bool:
    observations = attempt.get("host_terminal_observations")
    if not isinstance(observations, list) or not observations:
        return False
    if not all(isinstance(observation, dict) and observation.get("source") == "completed" for observation in observations):
        return False
    packet = attempt.get("packet")
    if not isinstance(packet, dict):
        return False
    check_lane_ids = _packet_check_lane_ids(packet)
    return {
        observation["lane_id"]
        for observation in observations
        if isinstance(observation.get("lane_id"), str) and observation["lane_id"] not in check_lane_ids
    } == _dispatched_lane_ids(attempt)


def _normalize_recovery_observation(value: Any, binding: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _RECOVERY_OBSERVATION_FIELDS:
        raise HarnessError("recovery observation is invalid")
    for field in ("lease_id", "lease_epoch", "host_instance_id"):
        if value.get(field) != binding[field]:
            raise HarnessError(f"recovery observation conflicts with {field}")
    if not isinstance(value.get("host_process_absent"), bool) or not isinstance(value.get("root_processes_absent"), bool):
        raise HarnessError("recovery observation process proof is invalid")
    observed_at = value.get("observed_at")
    if not isinstance(observed_at, str):
        raise HarnessError("recovery observation observed_at is invalid")
    _parse_timestamp(observed_at)
    return copy.deepcopy(value)


def _normalize_stranded_recovery(run: dict[str, Any], attempt: dict[str, Any], value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _STRANDED_RECOVERY_FIELDS:
        raise HarnessError("stranded recovery evidence is invalid")
    reason = value.get("reason")
    if not isinstance(reason, str) or not reason or len(reason) > 512:
        raise HarnessError("recovery reason is invalid")
    packet = attempt.get("packet")
    if not isinstance(packet, dict) or packet.get("attempt_id") != attempt.get("attempt_id"):
        raise HarnessError("recovery packet identity does not match attempt")
    if attempt.get("terminal_record") is None and (
        run["state"] != "running"
        or attempt.get("claims") != []
        or attempt.get("node_observations") != []
        or attempt.get("evidence") != {}
        or attempt.get("outcome") is not None
        or attempt.get("decision") is not None
        or attempt.get("decision_history") != []
    ):
        raise HarnessError("run is not stranded")
    evidence = _normalize_recovery_evidence(run["run_id"], attempt["attempt_id"], value["external_failure"])
    base_commit = _required_string(packet.get("base_commit"), "recovery packet base_commit")
    return {
        "reason": reason,
        "evidence": {
            "failure": {"reason": "stranded_running_recovered", "phase": "recovery", "detail": reason},
            "external_failure": evidence,
            "recovery": {
                "version": 1,
                "run_id": run["run_id"],
                "attempt_id": attempt["attempt_id"],
                "base_commit": base_commit,
                "packet_sha256": hashlib.sha256(_artifact_content_bytes(packet)).hexdigest(),
            },
        },
    }


def _terminalization_input(value: Any) -> tuple[str, list[Any], Any | None, Any | None, Any | None, dict[str, Any] | None]:
    fields = set(value) if isinstance(value, dict) else set()
    if not isinstance(value, dict) or frozenset(fields) not in {
        frozenset(_TERMINALIZATION_FIELDS),
        frozenset(_TERMINALIZATION_RECOVERY_FIELDS),
        frozenset(_TERMINALIZATION_STRANDED_RECOVERY_FIELDS),
        frozenset(_TERMINALIZATION_LEGACY_FIELDS),
        frozenset(_TERMINALIZATION_OUTCOME_FIELDS),
    }:
        raise HarnessError("terminalization evidence has invalid fields")
    attempt_id = _required_string(value.get("attempt_id"), "terminalization attempt_id")
    if frozenset(fields) == frozenset(_TERMINALIZATION_OUTCOME_FIELDS):
        return attempt_id, [], None, None, None, value
    legacy_cleanup = value.get("legacy_cleanup_attestation")
    if legacy_cleanup is not None:
        return attempt_id, [], None, None, legacy_cleanup, None
    observations = value.get("host_terminal_observations")
    if not isinstance(observations, list):
        raise HarnessError("terminalization evidence host_terminal_observations is invalid")
    recovery = value.get("recovery_observation")
    stranded_recovery = value.get("stranded_recovery")
    if recovery is None and stranded_recovery is None and not observations:
        raise HarnessError("terminalization evidence requires host observations")
    if sum(item is not None for item in (recovery, stranded_recovery)) + bool(observations) != 1:
        raise HarnessError("terminalization evidence cannot mix recovery and host observations")
    return attempt_id, observations, recovery, stranded_recovery, None, None


def _validate_legacy_cleanup_attempt(run: dict[str, Any], attempt: dict[str, Any], policy: dict[str, Any], cleanup: dict[str, Any]) -> None:
    packet = attempt.get("packet")
    cleanup_policy = policy.get("legacy_cleanup")
    if not isinstance(cleanup_policy, dict) or not isinstance(packet, dict):
        raise HarnessError("legacy cleanup is not allowed")
    packet_version = packet.get("version")
    if (
        not isinstance(packet_version, int)
        or isinstance(packet_version, bool)
        or packet_version > cleanup_policy["historical_packet_max_api"]
        or "terminal_observation_contract" in packet
        or attempt.get("execution_lease") is not None
        or attempt.get("terminal_record") is not None
        or attempt.get("claims")
        or attempt.get("node_observations")
        or attempt.get("evidence")
        or attempt.get("outcome") is not None
        or attempt.get("decision") is not None
        or attempt.get("decision_history")
        or attempt.get("host_terminal_observations")
        or attempt.get("host_observation_digests")
        or attempt.get("recovery_blocked") is not None
        or attempt.get("cancellation_request") is not None
    ):
        raise HarnessError("legacy cleanup is not allowed")
    if (
        cleanup["run_id"] != run["run_id"]
        or cleanup["attempt_id"] != attempt.get("attempt_id")
        or cleanup["packet_sha256"] != _canonical_digest(packet)
    ):
        raise HarnessError("legacy cleanup identity does not match run")


def _dispatched_lane_ids(attempt: dict[str, Any]) -> set[str]:
    recorded = attempt.get("dispatched_lane_ids")
    if isinstance(recorded, list):
        if not all(isinstance(lane_id, str) and lane_id for lane_id in recorded):
            raise HarnessError("attempt dispatched lanes are invalid")
        return set(recorded)
    nodes = attempt.get("nodes", [])
    if not isinstance(nodes, list):
        raise HarnessError("attempt nodes are invalid")
    return {
        node["lane_id"]
        for node in nodes
        if isinstance(node, dict)
        and node.get("node_kind") == "agent"
        and node.get("status") in {"running", "succeeded", "failed"}
        and isinstance(node.get("lane_id"), str)
    }


def _terminal_classification(
    attempt: dict[str, Any],
    observations: list[dict[str, Any]],
) -> tuple[str, str, list[str], list[str]]:
    packet = attempt["packet"]
    sources = {observation["source"] for observation in observations}
    if sources == {"completed"}:
        check_lane_ids = _packet_check_lane_ids(packet)
        observed_lanes = {observation["lane_id"] for observation in observations}
        observed_agent_lanes = observed_lanes - check_lane_ids
        dispatched_lanes = _dispatched_lane_ids(attempt)
        if dispatched_lanes and observed_agent_lanes != dispatched_lanes:
            raise HarnessError("terminalization lacks observations for every dispatched lane")
        failure = attempt.get("evidence", {}).get("failure")
        if isinstance(failure, dict):
            reason = failure.get("reason")
            if not isinstance(reason, str) or not reason:
                raise HarnessError("terminalization core failure is invalid")
            decisions = ["block"]
            if reason in packet["retry_policy"]["retryable_reasons"]:
                decisions = ["retry", "escalate", "block"]
            return "core_failure", reason, decisions, ["friction_event_ids", "evidence.failure"]
        verification = attempt.get("evidence")
        if not isinstance(verification, dict) or not isinstance(verification.get("criteria"), list) or not isinstance(verification.get("blockers"), list):
            raise HarnessError("terminalization lacks persisted core verification")
        reason, decisions = _outcome_for_verification(verification, packet["retry_policy"])
        return "completed", reason, decisions, ["evidence.criteria", "evidence.blockers", "evidence.checks"]
    if "cancellation" in sources:
        cancellation = attempt.get("cancellation_request")
        if not isinstance(cancellation, dict):
            raise HarnessError("cancellation observation has no persisted request")
        request_id = cancellation.get("cancellation_request_id")
        if any(observation["stop_proof"]["cancellation_request_id"] != request_id for observation in observations if observation["source"] == "cancellation"):
            raise HarnessError("cancellation observation has unknown request id")
        return "cancelled", "cancelled", ["block"], ["cancellation_request"]
    if "timeout" in sources:
        observation = next(item for item in observations if item["source"] == "timeout")
        lane = next((item for item in packet["lanes"] if item["lane_id"] == observation["lane_id"]), None)
        writer_missing = (
            observation["final_claim_state"]["state"] == "missing"
            and any(command["state"] == "completed" for command in observation["command_states"])
            and isinstance(lane, dict)
            and lane.get("kind") == "work"
            and lane.get("write_capable") is True
        )
        if writer_missing:
            return "writer_completion_missing", "writer_completion_missing", ["block"], []
        return "timeout", "dispatch_timeout", list(packet["execution_budget"]["timeout_decisions"]), []
    if "provider_failure" in sources:
        decisions = ["block"]
        if "dispatch_failed" in packet["retry_policy"]["retryable_reasons"]:
            decisions = ["retry", "escalate", "block"]
        return "provider_failure", "dispatch_failed", decisions, []
    if sources <= {"host_crash_absence", "stranded_recovery_absence"}:
        return "host_crash", "host_crash", ["block"], []
    raise HarnessError("terminalization has incompatible host observation sources")


def _terminalization_result(run: dict[str, Any], status: str, terminal_id: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "state": run["state"],
        "run_revision": run["run_revision"],
        "terminalization": {"status": status},
    }
    if terminal_id is not None:
        result["terminalization"]["terminal_id"] = terminal_id
    return result


def terminalize_attempt(root: Path, run_id: str, evidence: Any) -> dict[str, Any]:
    _validate_policy(root)
    run_id = _safe_run_id(run_id)
    with _run_lock(root, run_id):
        run = _load_run(root, run_id)
        policy = _load_policy(root)
        attempt = _active_attempt(run)
        attempt_id, raw_observations, raw_recovery, raw_stranded_recovery, raw_legacy_cleanup, raw_outcome = _terminalization_input(evidence)
        if attempt.get("attempt_id") != attempt_id:
            raise HarnessError("terminalization attempt identity does not match run")
        if raw_outcome is not None:
            outcome = _validated_outcome(attempt)
            supplied_id = _required_string(raw_outcome.get("outcome_id"), "terminalization outcome_id")
            supplied_digest = _required_string(raw_outcome.get("outcome_digest"), "terminalization outcome_digest")
            requested_decision = _required_string(raw_outcome.get("requested_decision"), "terminalization requested_decision")
            raw_authorization = raw_outcome.get("controller_authorization")
            existing_receipt = attempt.get("terminal_receipt")
            if isinstance(existing_receipt, dict):
                if (
                    existing_receipt.get("outcome_id") == supplied_id
                    and existing_receipt.get("outcome_digest") == supplied_digest
                    and existing_receipt.get("decision") == requested_decision
                    and isinstance(existing_receipt.get("authority"), dict)
                    and existing_receipt["authority"].get("authorization_digest") == authority.document_digest(raw_authorization)
                ):
                    return _terminalization_result(run, "replayed", existing_receipt.get("terminal_id"))
                raise HarnessError("attempt_already_finalized")
            if run["state"] != "awaiting_decision":
                raise HarnessError(f"run `{run_id}` is not awaiting controller decision")
            if outcome["outcome_id"] != supplied_id or outcome["outcome_digest"] != supplied_digest:
                raise HarnessError("terminalization outcome does not match run")
            try:
                normalized_authorization = authority.normalize_controller_authorization(
                    raw_authorization,
                    registry=authority.load_authorities(),
                    policy=outcome["policy_snapshot"],
                    now=datetime.now(UTC),
                )
            except authority.AuthorityError as exc:
                raise HarnessError(str(exc)) from exc
            receipt = _finalize_outcome(
                run,
                attempt,
                policy,
                decision=requested_decision,
                authorization=normalized_authorization,
                policy_auto=False,
            )
            _write_run(root, run)
            return _terminalization_result(run, "finalized", receipt["terminal_id"])
        legacy_cleanup: dict[str, Any] | None = None
        if raw_legacy_cleanup is not None:
            try:
                candidate_digest = legacy_cleanup_evidence_digest(raw_legacy_cleanup)
            except LegacyCleanupError as exc:
                raise HarnessError(str(exc)) from exc
            existing = attempt.get("terminal_record")
            if isinstance(existing, dict):
                audit = existing.get("legacy_cleanup")
                if (
                    existing.get("source_kind") == "legacy_cleanup"
                    and isinstance(audit, dict)
                    and audit.get("signed_evidence_sha256") == candidate_digest
                ):
                    return _terminalization_result(run, "replayed", existing.get("terminal_id"))
                raise HarnessError("attempt_already_terminal")
            if run["state"] not in ACTIVE_RUN_STATES:
                raise HarnessError(f"run `{run_id}` cannot terminalize from `{run['state']}")
            cleanup_policy = policy.get("legacy_cleanup")
            if not isinstance(cleanup_policy, dict):
                raise HarnessError("legacy cleanup is not configured")
            try:
                legacy_cleanup = normalize_legacy_cleanup_attestation(
                    raw_legacy_cleanup,
                    cleanup_policy,
                    now=datetime.now(UTC),
                )
            except LegacyCleanupError as exc:
                raise HarnessError(str(exc)) from exc
            if legacy_cleanup is None:
                raise HarnessError("legacy cleanup attestation is invalid")
            _validate_legacy_cleanup_attempt(run, attempt, policy, legacy_cleanup)
            binding = {"lease_id": None, "lease_epoch": None}
        else:
            if run["state"] not in {"running", "observed", "verifying", "orphaned", "awaiting_decision"}:
                raise HarnessError(f"run `{run_id}` cannot terminalize from `{run['state']}")
            binding = _attempt_lease_binding(run, attempt)
        outcome_detail: str | None = None
        stranded_recovery: dict[str, Any] | None = None
        if legacy_cleanup is not None:
            normalized_observations = []
            classification, reason, decisions, refs = "legacy_cleanup_attested", "legacy_cleanup_attested", ["block"], ["legacy_cleanup"]
            aggregate = {
                "binding": binding,
                "legacy_cleanup_signed_evidence_sha256": legacy_cleanup["signed_evidence_sha256"],
                "core_evidence_refs": refs,
            }
        elif raw_stranded_recovery is not None:
            stranded_recovery = _normalize_stranded_recovery(run, attempt, raw_stranded_recovery)
            normalized_observations = []
            classification, reason, decisions, refs = "stranded_recovery", "stranded_running_recovered", ["block"], [
                "evidence.failure",
                "evidence.external_failure",
                "evidence.recovery",
            ]
            outcome_detail = stranded_recovery["reason"]
            aggregate = {"binding": binding, "stranded_recovery": stranded_recovery["evidence"], "core_evidence_refs": refs}
        elif raw_recovery is not None:
            recovery = _normalize_recovery_observation(raw_recovery, binding)
            if _parse_timestamp(recovery["observed_at"]) < _parse_timestamp(attempt["execution_lease"]["expires_at"]):
                raise HarnessError("recovery observation precedes lease expiry")
            recovery_digest = _canonical_digest(recovery)
            if not recovery["host_process_absent"] or not recovery["root_processes_absent"]:
                existing_recovery = attempt.get("recovery_blocked")
                if isinstance(existing_recovery, dict) and existing_recovery.get("evidence_digest") == recovery_digest:
                    return _terminalization_result(run, "recovery_blocked")
                attempt["recovery_blocked"] = {"evidence_digest": recovery_digest, "observation": recovery}
                attempt["execution_lease"]["state"] = "recovery_blocked"
                if run["state"] != "orphaned":
                    _transition(run, _load_policy(root)["states"], "orphaned", "recovery_blocked")
                _write_run(root, run)
                return _terminalization_result(run, "recovery_blocked")
            normalized_observations: list[dict[str, Any]] = []
            classification, reason, decisions, refs = "host_crash", "host_crash", ["block"], ["recovery_blocked"]
            aggregate = {"recovery_observation": recovery, "binding": binding, "core_evidence_refs": refs}
        else:
            normalized_observations = [
                normalize_host_terminal_observation(raw, attempt["packet"], binding=binding)
                for raw in raw_observations
            ]
            if len({observation["observation_id"] for observation in normalized_observations}) != len(normalized_observations):
                raise HarnessError("terminalization host observations are duplicated")
            normalized_observations.sort(key=lambda item: (item["lane_id"], item["observed_at"], item["observation_id"]))
            lease_expiry = _parse_timestamp(attempt["execution_lease"]["expires_at"])
            if any(_parse_timestamp(observation["observed_at"]) > lease_expiry for observation in normalized_observations):
                raise HarnessError("terminalization observation exceeds lease expiry")
            classification, reason, decisions, refs = _terminal_classification(attempt, normalized_observations)
            aggregate = {
                "binding": binding,
                "host_observation_digests": [_canonical_digest(observation) for observation in normalized_observations],
                "core_evidence_refs": refs,
            }
        evidence_digest = _canonical_digest(aggregate)
        existing = attempt.get("terminal_record")
        if isinstance(existing, dict):
            if existing.get("evidence_digest") == evidence_digest:
                return _terminalization_result(run, "replayed", existing.get("terminal_id"))
            raise HarnessError("attempt_already_terminal")
        terminal_id = f"terminal-{_canonical_digest({'run_id': run_id, 'attempt_id': attempt_id, 'lease_id': binding['lease_id'], 'lease_epoch': binding['lease_epoch'], 'evidence_digest': evidence_digest})}"
        if stranded_recovery is not None:
            attempt["evidence"] = stranded_recovery["evidence"]
        attempt["host_terminal_observations"] = normalized_observations
        attempt["host_observation_digests"] = aggregate.get("host_observation_digests", [])
        attempt["terminal_record"] = {
            "schema_id": "attempt_terminal_evidence/v2",
            "terminal_id": terminal_id,
            "classification": classification,
            "evidence_digest": evidence_digest,
            "host_observation_digests": attempt["host_observation_digests"],
            "core_evidence_refs": refs,
            "lease_id": binding["lease_id"],
            "lease_epoch": binding["lease_epoch"],
            "recorded_at": _timestamp(),
        }
        if legacy_cleanup is not None:
            attempt["terminal_record"]["source_kind"] = "legacy_cleanup"
            attempt["terminal_record"]["legacy_cleanup"] = legacy_cleanup
        else:
            attempt["execution_lease"]["state"] = "released"
            attempt["execution_lease"]["released_at"] = _timestamp()
        _set_outcome(
            run,
            attempt,
            policy,
            reason,
            decisions,
            ["terminal_record", *refs],
            detail=outcome_detail,
            source_valid_until=legacy_cleanup["expires_at"] if legacy_cleanup is not None else None,
        )
        if _auto_finalize_outcome(run, attempt, policy) is None:
            _transition(run, policy["states"], "awaiting_decision", classification)
        _write_run(root, run)
        return _terminalization_result(run, "applied", terminal_id)


def request_attempt_cancellation(root: Path, run_id: str, request: Any) -> dict[str, Any]:
    _validate_policy(root)
    run_id = _safe_run_id(run_id)
    if not isinstance(request, dict) or set(request) != _CANCELLATION_FIELDS:
        raise HarnessError("cancellation request has invalid fields")
    attempt_id = _required_string(request.get("attempt_id"), "cancellation attempt_id")
    actor = _required_string(request.get("actor"), "cancellation actor")
    reason = _required_string(request.get("reason"), "cancellation reason")
    with _run_lock(root, run_id):
        run = _load_run(root, run_id)
        if run["state"] not in {"running", "observed", "verifying"}:
            raise HarnessError(f"run `{run_id}` cannot cancel from `{run['state']}`")
        attempt = _active_attempt(run)
        if attempt.get("attempt_id") != attempt_id:
            raise HarnessError("cancellation attempt identity does not match run")
        binding = _attempt_lease_binding(run, attempt)
        existing = attempt.get("cancellation_request")
        if isinstance(existing, dict):
            return {"cancellation_request_id": existing["cancellation_request_id"], "run_revision": run["run_revision"]}
        cancellation_request_id = f"cancel-{uuid.uuid4()}"
        attempt["cancellation_request"] = {
            "cancellation_request_id": cancellation_request_id,
            "actor": actor,
            "reason_sha256": hashlib.sha256(reason.encode("utf-8")).hexdigest(),
            "reason_length": len(reason),
            "requested_at": _timestamp(),
            "lease_id": binding["lease_id"],
            "lease_epoch": binding["lease_epoch"],
        }
        _write_run(root, run)
        return {"cancellation_request_id": cancellation_request_id, "run_revision": run["run_revision"]}


def migration_preflight(root: Path) -> dict[str, Any]:
    active: list[dict[str, str]] = []
    for run in _all_runs(root):
        if run.get("state") not in ACTIVE_RUN_STATES or not run.get("attempts"):
            continue
        attempt = _active_attempt(run)
        packet = attempt.get("packet")
        if (
            isinstance(packet, dict)
            and "terminal_observation_contract" not in packet
            and not isinstance(attempt.get("execution_lease"), dict)
            and attempt.get("terminal_record") is None
        ):
            active.append({"run_id": run["run_id"], "attempt_id": attempt.get("attempt_id", "")})
    return {"active_legacy_attempts": active, "ready": True}


def abandon_legacy_attempt(root: Path, run_id: str, request: Any) -> dict[str, Any]:
    raise HarnessError("legacy_abandonment_retired")


def _normalize_recovery_evidence(run_id: str, attempt_id: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != RECOVERY_EVIDENCE_FIELDS:
        raise HarnessError("external recovery evidence is invalid")
    if value.get("version") != 1:
        raise HarnessError("external recovery evidence version is invalid")
    if value.get("source") != "host":
        raise HarnessError("external recovery evidence source is invalid")
    if value.get("code") != "terminal_recording_failed":
        raise HarnessError("external recovery evidence code is invalid")
    if value.get("run_id") != run_id or value.get("attempt_id") != attempt_id:
        raise HarnessError("external recovery evidence identity does not match run")
    detail = value.get("detail")
    if not isinstance(detail, str) or not detail or len(detail) > 2048:
        raise HarnessError("external recovery evidence detail is invalid")
    observed_at = value.get("observed_at")
    if not isinstance(observed_at, str):
        raise HarnessError("external recovery evidence observed_at is invalid")
    _parse_timestamp(observed_at)
    return copy.deepcopy(value)


def recover_stranded_run(
    root: Path,
    run_id: str,
    attempt_id: str,
    reason: str,
    external_failure: Any,
) -> dict[str, Any]:
    run_id = _safe_run_id(run_id)
    run = _load_run(root, run_id)
    if run["state"] != "running":
        raise HarnessError(f"run `{run_id}` is not running")
    if _active_attempt(run).get("attempt_id") != attempt_id:
        raise HarnessError("recovery attempt identity does not match run")
    terminalize_attempt(
        root,
        run_id,
        {
            "attempt_id": attempt_id,
            "host_terminal_observations": [],
            "stranded_recovery": {"reason": reason, "external_failure": external_failure},
        },
    )
    return _managed_result(_load_run(root, run_id))


def delegate(root: Path, run_id: str, parent_invocation_id: str, request: dict[str, Any]) -> DelegationResult:
    run = _load_run(root, _safe_run_id(run_id))
    attempt = _active_attempt(run)
    packet = attempt.get("packet")
    if not isinstance(packet, dict) or packet.get("invocation_id") != parent_invocation_id:
        return {"ok": False, "code": "delegation_parent_not_found"}
    if "harness.delegate" not in packet.get("capabilities", []):
        return {"ok": False, "code": "delegation_not_permitted"}
    if run["state"] != "running" or not isinstance(request, dict):
        return {"ok": False, "code": "delegation_not_permitted"}

    policy = _load_policy(root)
    profiles = policy.get("delegation_profiles")
    profile_name = packet.get("delegation_profile")
    profile = profiles.get(profile_name) if isinstance(profiles, dict) and isinstance(profile_name, str) else None
    if not isinstance(profile, dict):
        return {"ok": False, "code": "delegation_not_permitted"}

    idempotency_key = request.get("idempotency_key")
    if not isinstance(idempotency_key, str) or not idempotency_key:
        return {"ok": False, "code": "delegation_not_permitted"}
    idempotency = attempt.get("delegation_idempotency", {})
    if not isinstance(idempotency, dict):
        raise HarnessError("invalid delegation idempotency state")
    if idempotency_key in idempotency:
        result = idempotency[idempotency_key]
        if not isinstance(result, dict):
            raise HarnessError("invalid delegation idempotency result")
        return copy.deepcopy(result)

    role = request.get("role")
    roles = _load_roles(root)
    if not isinstance(role, str) or role not in profile.get("allowed_roles", []) or not isinstance(roles.get(role), dict):
        return {"ok": False, "code": "delegation_not_permitted"}
    capabilities = request.get("capabilities")
    parent_capabilities = packet.get("capabilities")
    if (
        not isinstance(capabilities, list)
        or not all(isinstance(capability, str) and capability for capability in capabilities)
        or not isinstance(parent_capabilities, list)
        or not all(isinstance(capability, str) for capability in parent_capabilities)
        or not set(capabilities).issubset(parent_capabilities)
        or not set(capabilities).issubset(profile.get("capability_ceiling", []))
    ):
        return {"ok": False, "code": "delegation_capability_exceeded"}
    try:
        allowed_paths = _safe_paths(request.get("allowed_paths"), "child allowed_paths", required=True)
    except HarnessError:
        return {"ok": False, "code": "delegation_path_exceeded"}
    parent_paths = packet.get("allowed_paths")
    if not isinstance(parent_paths, list) or any(not _path_matches(path, parent_paths) for path in allowed_paths):
        return {"ok": False, "code": "delegation_path_exceeded"}
    timeout_seconds = request.get("timeout_seconds")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds < 1
        or timeout_seconds > profile.get("per_child_timeout_seconds", 0)
    ):
        return {"ok": False, "code": "delegation_budget_exceeded"}

    children = attempt.get("children", [])
    ledger = attempt.get("reservation_ledger", [])
    if not isinstance(children, list) or not isinstance(ledger, list):
        raise HarnessError("invalid delegation state")
    parent_depth = packet.get("delegation_depth", 0)
    if not isinstance(parent_depth, int) or isinstance(parent_depth, bool) or parent_depth + 1 > profile.get("max_depth", 0):
        return {"ok": False, "code": "delegation_depth_exceeded"}
    if len(children) >= profile.get("max_children", 0):
        return {"ok": False, "code": "delegation_budget_exceeded"}
    active_children = [child for child in children if isinstance(child, dict) and child.get("status") not in {"cancelled", "failed", "succeeded", "timed_out"}]
    if len(active_children) >= profile.get("max_concurrent_children", 0):
        return {"ok": False, "code": "delegation_budget_exceeded"}
    reserved_seconds = sum(entry.get("timeout_seconds", 0) for entry in ledger if isinstance(entry, dict) and not entry.get("released"))
    if reserved_seconds + timeout_seconds > profile.get("total_child_timeout_seconds", 0):
        return {"ok": False, "code": "delegation_budget_exceeded"}

    child_id = f"{parent_invocation_id}/child-{len(children) + 1}"
    child_packet = copy.deepcopy(packet)
    child_packet.update({
        "invocation_id": child_id,
        "parent_invocation_id": parent_invocation_id,
        "delegation_depth": parent_depth + 1,
        "role": role,
        "required_claim_kind": roles[role]["result_kind"],
        "claim_schema": {
            "required_fields": copy.deepcopy(roles[role]["required_fields"]),
            "field_constraints": copy.deepcopy(roles[role].get("field_constraints", {})),
        },
        "capabilities": list(capabilities),
        "allowed_paths": allowed_paths,
        "planned_write_paths": [],
        "timeout_seconds": timeout_seconds,
        "delegation_profile": profile_name,
        "workspace_write_access": profile["workspace_write_access"],
        "verification": profile["verification"],
    })
    result = {"ok": True, "invocation_id": child_id, "status": "planned"}
    children.append({"idempotency_key": idempotency_key, "status": "planned", "packet": child_packet})
    ledger.append({"idempotency_key": idempotency_key, "timeout_seconds": timeout_seconds, "released": False})
    idempotency[idempotency_key] = result
    attempt["children"] = children
    attempt["reservation_ledger"] = ledger
    attempt["delegation_idempotency"] = idempotency
    parent_node_id = parent_invocation_id.rpartition(":")[2]
    parent = next((node for node in attempt.get("nodes", []) if isinstance(node, dict) and node.get("lane_id") == parent_node_id), None)
    if not isinstance(parent, dict):
        raise HarnessError("delegation parent node is missing")
    parent["status"] = "waiting_for_child"
    _write_run(root, run)
    return copy.deepcopy(result)


def _delegated_child_packet(root: Path, run_id: str, child_invocation_id: str) -> dict[str, Any]:
    attempt = _active_attempt(_load_run(root, _safe_run_id(run_id)))
    for child in attempt.get("children", []):
        if isinstance(child, dict) and isinstance(child.get("packet"), dict) and child["packet"].get("invocation_id") == child_invocation_id:
            return copy.deepcopy(child["packet"])
    raise HarnessError("delegated child packet was not found")


def _delegation_bridge(root: Path, run: dict[str, Any], attempt: dict[str, Any], lane: dict[str, Any]) -> dict[str, Any] | None:
    packet = attempt["packet"]
    if lane.get("node_kind") != "agent" or "harness.delegate" not in packet.get("capabilities", []):
        return None
    parent_node_id = _required_string(lane.get("lane_id"), "parent node id")
    parent_invocation_id = _required_string(packet.get("invocation_id"), "parent invocation id")
    return {
        "run_id": run["run_id"],
        "attempt_id": attempt["attempt_id"],
        "parent_node_id": parent_node_id,
        "delegate": lambda request: delegate(root, run["run_id"], parent_invocation_id, request),
        "child_packet": lambda child_id: _delegated_child_packet(root, run["run_id"], child_id),
        "complete": lambda child_id, status, claim, app_server_model_selection=None: complete_delegated_child(
            root,
            run["run_id"],
            child_id,
            status,
            claim,
            app_server_model_selection,
        ),
    }


def _sync_delegation_state(root: Path, run: dict[str, Any], attempt: dict[str, Any]) -> bool:
    persisted_run = _load_run(root, run["run_id"])
    persisted_attempt = _active_attempt(persisted_run)
    for field in ("children", "reservation_ledger", "delegation_idempotency"):
        if field in persisted_attempt:
            attempt[field] = copy.deepcopy(persisted_attempt[field])
    if persisted_run["state"] == "running":
        return False
    run["state"] = persisted_run["state"]
    run["state_history"] = copy.deepcopy(persisted_run["state_history"])
    for field in ("outcome", "terminal_receipt", "decision", "decision_history"):
        if field in persisted_attempt:
            attempt[field] = copy.deepcopy(persisted_attempt[field])
    return True


def complete_delegated_child(
    root: Path,
    run_id: str,
    child_invocation_id: str,
    status: str,
    claim: dict[str, Any] | None,
    app_server_model_selection: dict[str, Any] | None = None,
) -> DelegationResult:
    run = _load_run(root, _safe_run_id(run_id))
    attempt = _active_attempt(run)
    children = attempt.get("children")
    if not isinstance(children, list):
        return {"ok": False, "code": "delegation_child_not_found"}
    child = next(
        (
            item for item in children
            if isinstance(item, dict)
            and isinstance(item.get("packet"), dict)
            and item["packet"].get("invocation_id") == child_invocation_id
        ),
        None,
    )
    if not isinstance(child, dict):
        return {"ok": False, "code": "delegation_child_not_found"}
    if child.get("status") in DELEGATED_CHILD_TERMINAL_STATES:
        result = child.get("terminal_result")
        if not isinstance(result, dict):
            raise HarnessError("terminal delegated child lacks result")
        return copy.deepcopy(result)
    if status not in DELEGATED_CHILD_TERMINAL_STATES:
        return {"ok": False, "code": "delegation_not_permitted"}

    child_packet = child["packet"]
    try:
        _validate_app_server_model_selection(child_packet, app_server_model_selection)
    except HarnessError:
        return {"ok": False, "code": "delegation_result_invalid"}
    if status == "succeeded" and child_packet.get("verification") == "schema":
        try:
            roles, claim_fields = _load_role_catalog(root)
            role = roles.get(child_packet.get("role"))
            if not isinstance(role, dict) or claim is None:
                raise HarnessError("delegated child claim is required")
            claim = _validate_managed_claim(
                claim,
                required_claim_kind=role["result_kind"],
                claim_schema=_claim_schema(role, claim_fields),
            )
        except HarnessError:
            return {"ok": False, "code": "delegation_result_invalid"}

    summary = "" if claim is None else claim.get("summary", "")
    if (
        not isinstance(summary, str)
        or len(summary.encode("utf-8")) > child_packet["context_limits"]["outcome_summary_max_bytes"]
    ):
        return {"ok": False, "code": "delegation_result_invalid"}

    child["status"] = status
    if claim is not None:
        child["claim"] = copy.deepcopy(claim)
    if app_server_model_selection is not None:
        child["app_server_model_selection"] = copy.deepcopy(app_server_model_selection)
    result: DelegationResult = {"ok": True, "invocation_id": child_invocation_id, "status": status, "summary": summary}
    child["terminal_result"] = copy.deepcopy(result)
    ledger = attempt.get("reservation_ledger")
    if not isinstance(ledger, list):
        raise HarnessError("delegated child lacks reservation ledger")
    for reservation in ledger:
        if isinstance(reservation, dict) and reservation.get("idempotency_key") == child.get("idempotency_key"):
            reservation["released"] = True
            break
    else:
        raise HarnessError("delegated child lacks reservation")

    parent_id = child_packet.get("parent_invocation_id")
    parent_node_id = parent_id.rpartition(":")[2] if isinstance(parent_id, str) else ""
    parent = next((node for node in attempt.get("nodes", []) if isinstance(node, dict) and node.get("lane_id") == parent_node_id), None)
    if isinstance(parent, dict):
        parent["status"] = "running" if status == "succeeded" else "waiting_for_child"
    if status != "succeeded" and run["state"] == "running":
        policy = _load_policy(root)
        _set_outcome(run, attempt, policy, f"child_{status}", ["block"], ["children", "reservation_ledger"])
        if _auto_finalize_outcome(run, attempt, policy) is None:
            _transition(run, policy["states"], "awaiting_decision", f"child_{status}")
    _write_run(root, run)
    return result


def _set_outcome(
    run: dict[str, Any],
    attempt: dict[str, Any],
    policy: dict[str, Any],
    reason: str,
    allowed_decisions: list[str],
    evidence_refs: list[str],
    *,
    detail: str | None = None,
    source_valid_until: str | None = None,
) -> dict[str, Any]:
    if not isinstance(reason, str) or not reason:
        raise HarnessError("outcome reason is invalid")
    if not isinstance(allowed_decisions, list) or not allowed_decisions or len(allowed_decisions) != len(set(allowed_decisions)) or any(decision not in DECISION_KINDS for decision in allowed_decisions):
        raise HarnessError("outcome allowed_decisions are invalid")
    if not isinstance(evidence_refs, list) or any(not isinstance(reference, str) or not reference for reference in evidence_refs):
        raise HarnessError("outcome evidence_refs are invalid")
    if detail is not None:
        if not isinstance(detail, str) or len(detail.encode("utf-8")) > policy["context_limits"]["outcome_summary_max_bytes"]:
            raise HarnessError("outcome detail is invalid")
    recorded_at = _timestamp()
    valid_until = _parse_timestamp(recorded_at) + timedelta(seconds=policy["terminalization"]["pending_outcome_ttl_seconds"])
    if source_valid_until is not None:
        source_deadline = _parse_timestamp(source_valid_until)
        valid_until = min(valid_until, source_deadline)
    packet = attempt.get("packet")
    if not isinstance(packet, dict):
        raise HarnessError("outcome packet is invalid")
    policy_snapshot = copy.deepcopy(policy["terminalization"])
    subject = {
        "run_id": run["run_id"],
        "attempt_id": attempt.get("attempt_id"),
        "packet_sha256": _canonical_digest(packet),
        "reason": reason,
        "allowed_decisions": allowed_decisions,
        "evidence_refs": evidence_refs,
        "detail": detail,
        "recorded_at": recorded_at,
        "valid_until": valid_until.isoformat(),
        "policy_digest": _canonical_digest(policy),
        "policy_snapshot": policy_snapshot,
    }
    outcome_id = f"outcome-{_canonical_digest(subject)}"
    outcome = {"schema_id": "attempt_outcome/v2", "outcome_id": outcome_id, **subject}
    outcome["outcome_digest"] = _canonical_digest(outcome)
    attempt["outcome"] = outcome
    return outcome


_TERMINAL_DECISIONS = {"accept", "block", "waive"}


def _validated_outcome(attempt: dict[str, Any]) -> dict[str, Any]:
    outcome = attempt.get("outcome")
    if not isinstance(outcome, dict) or outcome.get("schema_id") != "attempt_outcome/v2":
        raise HarnessError("attempt outcome is invalid")
    digest = outcome.get("outcome_digest")
    unsigned = {key: value for key, value in outcome.items() if key != "outcome_digest"}
    if not isinstance(digest, str) or digest != _canonical_digest(unsigned):
        raise HarnessError("attempt outcome digest is invalid")
    if not isinstance(outcome.get("outcome_id"), str) or not outcome["outcome_id"].startswith("outcome-"):
        raise HarnessError("attempt outcome identity is invalid")
    _parse_timestamp(outcome.get("recorded_at"))
    _parse_timestamp(outcome.get("valid_until"))
    if not isinstance(outcome.get("policy_snapshot"), dict) or not isinstance(outcome.get("policy_digest"), str):
        raise HarnessError("attempt outcome policy snapshot is invalid")
    return outcome


def _final_state_for_decision(decision: str) -> str:
    return {"accept": "accepted", "block": "blocked", "waive": "unvalidated"}[decision]


def _finalize_outcome(
    run: dict[str, Any],
    attempt: dict[str, Any],
    policy: dict[str, Any],
    *,
    decision: str,
    authorization: dict[str, Any] | None = None,
    policy_auto: bool,
) -> dict[str, Any]:
    outcome = _validated_outcome(attempt)
    if decision not in _TERMINAL_DECISIONS or decision not in outcome["allowed_decisions"]:
        raise HarnessError("terminal decision is not allowed for current outcome")
    snapshot = outcome["policy_snapshot"]
    now = datetime.now(UTC)
    expired = now > _parse_timestamp(outcome["valid_until"])
    if policy_auto:
        if snapshot.get("auto_finalize_single_terminal_outcome") is not True or outcome["allowed_decisions"] != [decision]:
            raise HarnessError("outcome is not eligible for policy auto finalization")
        authority_receipt = {"mode": "policy_auto", "principal_id": None}
    else:
        if authorization is None:
            raise HarnessError("terminal decision requires controller authorization")
        expected = {
            "run_id": run["run_id"],
            "attempt_id": attempt["attempt_id"],
            "packet_sha256": _canonical_digest(attempt["packet"]),
            "outcome_id": outcome["outcome_id"],
            "outcome_digest": outcome["outcome_digest"],
            "requested_decision": decision,
        }
        if any(authorization.get(field) != value for field, value in expected.items()):
            raise HarnessError("controller authorization does not match outcome")
        if expired and decision != "block":
            raise HarnessError("outcome is expired for acceptance or waiver")
        if expired and _parse_timestamp(authorization["issued_at"]) < _parse_timestamp(outcome["valid_until"]):
            raise HarnessError("expired outcome requires fresh controller authorization")
        legacy_cleanup = attempt.get("terminal_record", {}).get("legacy_cleanup") if isinstance(attempt.get("terminal_record"), dict) else None
        if (
            isinstance(legacy_cleanup, dict)
            and legacy_cleanup.get("issuer_key_id") == authorization.get("issuer_key_id")
            and snapshot.get("allow_same_issuer_evidence_and_authorization") is not True
        ):
            raise HarnessError("controller authorization issuer cannot pair with evidence issuer")
        authority_receipt = {
            "mode": "controller_authorization",
            "principal_id": authorization["principal_id"],
            "authorization_id": authorization["authorization_id"],
            "authorization_digest": authorization["authorization_digest"],
            "issuer_key_id": authorization["issuer_key_id"],
            "key_fingerprint": authorization["key_fingerprint"],
            "registry_digest": authorization["registry_digest"],
            "reason_sha256": authorization["reason_sha256"],
            "reason_length": authorization["reason_length"],
        }
    if policy_auto and expired:
        raise HarnessError("outcome is expired for policy auto finalization")
    if decision == "accept":
        criteria = attempt.get("evidence", {}).get("criteria", [])
        if not criteria or any(criterion.get("status") != "proven" for criterion in criteria):
            raise HarnessError("cannot accept run without proven criteria")
    receipt_subject = {
        "run_id": run["run_id"],
        "attempt_id": attempt["attempt_id"],
        "outcome_id": outcome["outcome_id"],
        "outcome_digest": outcome["outcome_digest"],
        "decision": decision,
        "authority": authority_receipt,
        "policy_digest": outcome["policy_digest"],
        "terminal_evidence_digest": attempt.get("terminal_record", {}).get("evidence_digest") if isinstance(attempt.get("terminal_record"), dict) else None,
        "finalized_at": _timestamp(),
        "outcome_expired": expired,
    }
    terminal_id = f"terminal-{_canonical_digest(receipt_subject)}"
    receipt = {"schema_id": "attempt_terminal_receipt/v3", "terminal_id": terminal_id, **receipt_subject}
    existing = attempt.get("terminal_receipt")
    if isinstance(existing, dict):
        if existing.get("terminal_id") == terminal_id:
            return existing
        raise HarnessError("attempt_already_finalized")
    attempt["terminal_receipt"] = receipt
    stored_decision = {"kind": decision, "at": receipt["finalized_at"], "authority_mode": authority_receipt["mode"]}
    attempt["decision"] = stored_decision
    attempt.setdefault("decision_history", []).append(copy.deepcopy(stored_decision))
    _transition(run, policy["states"], _final_state_for_decision(decision), f"{authority_receipt['mode']}_{decision}")
    return receipt


def _auto_finalize_outcome(run: dict[str, Any], attempt: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any] | None:
    outcome = _validated_outcome(attempt)
    decisions = outcome["allowed_decisions"]
    if len(decisions) != 1 or decisions[0] not in _TERMINAL_DECISIONS:
        return None
    return _finalize_outcome(run, attempt, policy, decision=decisions[0], policy_auto=True)


def _persist_outcome_transition(root: Path, run: dict[str, Any], attempt: dict[str, Any], policy: dict[str, Any], reason: str) -> dict[str, Any]:
    if _auto_finalize_outcome(run, attempt, policy) is None:
        _transition(run, policy["states"], "awaiting_decision", reason)
    _write_run(root, run)
    return _managed_result(run)


def _managed_result(run: dict[str, Any]) -> dict[str, Any]:
    attempt = _active_attempt(run)
    return {"run_id": run["run_id"], "state": run["state"], "attempt_id": attempt["attempt_id"], "outcome": attempt["outcome"]}


def _adapter_call(adapter: Any, name: str, *args: Any) -> Any:
    method = adapter.get(name) if isinstance(adapter, dict) else getattr(adapter, name, None)
    if not callable(method):
        raise HarnessError(f"host adapter missing `{name}`")
    return method(*args)


def _adapter_host_api(adapter: Any) -> Any:
    value = adapter.get("host_api") if isinstance(adapter, dict) else getattr(adapter, "host_api", None)
    return value() if callable(value) else value


def _adapter_capabilities(adapter: Any, canonical_modes: set[str]) -> dict[str, str]:
    capabilities = _adapter_call(adapter, "capabilities")
    if not isinstance(capabilities, dict):
        raise HarnessError("host adapter capabilities must be a mapping")
    known_capabilities = set(canonical_modes) | {
        "host_terminal_observation_v2",
        "execution_lease_duration_model",
    }
    for mode, level in capabilities.items():
        if not isinstance(mode, str) or mode not in known_capabilities or level not in CAPABILITY_LEVELS:
            raise HarnessError("host adapter capabilities contain invalid entry")
    return capabilities


def _adapter_unavailable_detail(adapter: Any) -> str | None:
    detail = adapter.get("unavailable_detail") if isinstance(adapter, dict) else getattr(adapter, "unavailable_detail", None)
    return detail if isinstance(detail, str) and detail else None


def _adapter_identity(adapter: Any, runtime_provider: dict[str, Any]) -> dict[str, Any]:
    identity = _adapter_call(adapter, "identity")
    if (
        not isinstance(identity, dict)
        or set(identity) != {"provider_id", "contract_version"}
        or not isinstance(identity.get("provider_id"), str)
        or not identity["provider_id"]
        or not isinstance(identity.get("contract_version"), int)
        or isinstance(identity["contract_version"], bool)
        or identity["contract_version"] < 1
    ):
        raise HarnessError("host adapter identity must contain provider_id and contract_version")
    if identity != runtime_provider:
        raise HarnessError("host adapter identity conflicts with packet runtime provider")
    return copy.deepcopy(identity)


def _record_host_preflight(attempt: dict[str, Any], adapter: Any) -> None:
    method = adapter.get("preflight_evidence") if isinstance(adapter, dict) else getattr(adapter, "preflight_evidence", None)
    if method is None:
        return
    if not callable(method):
        raise HarnessError("host adapter preflight evidence must be callable")
    evidence = method()
    if not isinstance(evidence, dict):
        raise HarnessError("host adapter preflight evidence must be an object")
    protocol = _required_string(evidence.get("protocol"), "host adapter preflight protocol")
    server_uri = _required_string(evidence.get("server_uri"), "host adapter preflight server_uri")
    attempt["host_preflight"] = {"protocol": protocol, "server_uri": server_uri}


def _provider_runtime_binding(adapter: Any, *, required: bool) -> dict[str, Any] | None:
    method = adapter.get("preflight_evidence") if isinstance(adapter, dict) else getattr(adapter, "preflight_evidence", None)
    if method is None:
        if required:
            raise HarnessError("provider preflight evidence is required")
        return None
    if not callable(method):
        raise HarnessError("host adapter preflight evidence must be callable")
    evidence = method()
    required_fields = {
        "provider_id",
        "host_api",
        "contract_version",
        "transport",
        "lifecycle",
        "protocol",
        "configuration_digest",
        "readiness",
    }
    accepted_fields = {frozenset(required_fields), frozenset({*required_fields, "host_instance_id"})}
    if not isinstance(evidence, dict) or frozenset(evidence) not in accepted_fields:
        raise HarnessError("host adapter preflight evidence has invalid shape")
    if (
        not isinstance(evidence["provider_id"], str)
        or not evidence["provider_id"]
        or not isinstance(evidence["host_api"], int)
        or isinstance(evidence["host_api"], bool)
        or evidence["host_api"] < 1
        or not isinstance(evidence["contract_version"], int)
        or isinstance(evidence["contract_version"], bool)
        or evidence["contract_version"] < 1
        or evidence["transport"] not in {"stdio", "websocket"}
        or evidence["lifecycle"] not in {"host_spawn", "external"}
        or not isinstance(evidence["protocol"], str)
        or not evidence["protocol"]
        or not isinstance(evidence["configuration_digest"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", evidence["configuration_digest"])
        or evidence["readiness"] != "ready"
    ):
        raise HarnessError("host adapter preflight evidence has invalid values")
    host_instance_id = evidence.get("host_instance_id")
    if host_instance_id is not None and (not isinstance(host_instance_id, str) or not host_instance_id or len(host_instance_id) > 256):
        raise HarnessError("host adapter preflight evidence has invalid host instance identity")
    if any(re.search(r"(?i)(api[_-]?key|token|password|secret|authorization|cookie)", value) for value in evidence.values() if isinstance(value, str)):
        raise HarnessError("host adapter preflight evidence contains secret-bearing value")
    return copy.deepcopy(evidence)


def _validate_provider_runtime_binding(
    binding: Any,
    runtime_provider: dict[str, Any],
    *,
    packet_api: int,
    host_api: Any,
) -> dict[str, Any]:
    if not isinstance(binding, dict):
        raise HarnessError("provider runtime binding is required")
    static_binding = static_provider_runtime_binding(binding)
    if static_binding.get("provider_id") != runtime_provider["provider_id"] or static_binding.get("contract_version") != runtime_provider["contract_version"]:
        raise HarnessError("provider runtime binding conflicts with packet runtime provider")
    if host_api is not None and static_binding.get("host_api") != host_api:
        raise HarnessError("provider runtime binding conflicts with host API")
    dispatch = admit_packet_dispatch(static_binding.get("host_api"), packet_api, static_binding.get("contract_version"))
    if not dispatch["ok"]:
        raise HarnessError(dispatch["code"])
    return static_binding


def _host_instance_id(binding: dict[str, Any]) -> str:
    host_instance_id = binding.get("host_instance_id")
    if not isinstance(host_instance_id, str) or not host_instance_id or len(host_instance_id) > 256:
        raise HarnessError("provider preflight evidence lacks host instance identity")
    return host_instance_id


def _record_tool_binding_evidence(
    attempt: dict[str, Any],
    lane: dict[str, Any],
    packet: dict[str, Any],
    workspace: dict[str, Any],
    evidence: Any,
) -> None:
    if not isinstance(workspace.get("path"), str) or not workspace["path"]:
        raise HarnessError("host adapter workspace must include path")
    if not isinstance(evidence, list):
        raise HarnessError("host adapter tool binding evidence must be a list")
    expected_access_key = "validator_access" if lane["kind"] == "validate" or packet.get("workspace_write_access") == "read_only" else "writer_access"
    expected = {binding["tool"]: binding for binding in packet["tool_bindings"]}
    observed: dict[str, dict[str, Any]] = {}
    for binding in evidence:
        if not isinstance(binding, dict) or not isinstance(binding.get("tool"), str):
            raise HarnessError("host adapter tool binding evidence contains invalid entry")
        tool = binding["tool"]
        if tool in observed or tool not in expected:
            raise HarnessError("host adapter tool binding evidence conflicts with packet")
        required = expected[tool]
        if (
            binding.get("host_kind") != required["host_kind"]
            or binding.get("access") != required[expected_access_key]
            or binding.get("root_probe") != required["root_probe"]
            or binding.get("workspace_root") != workspace["path"]
            or binding.get("verified") is not True
            or binding.get("runtime_provider") != packet["runtime_provider"]
        ):
            raise HarnessError(f"host adapter tool binding `{tool}` is not verified for packet workspace")
        observed[tool] = binding
    if set(observed) != set(expected):
        raise HarnessError("host adapter did not verify every packet-selected tool")
    attempt.setdefault("tool_binding_evidence", []).append({
        "lane_id": lane["lane_id"],
        "workspace": copy.deepcopy(workspace),
        "bindings": copy.deepcopy(evidence),
    })


def _validate_app_server_model_selection(packet: dict[str, Any], value: Any) -> None:
    if value is None:
        return
    identity = packet.get("agent_identity")
    if not isinstance(identity, dict):
        raise HarnessError("packet agent identity is invalid")
    expected = {field: identity.get(field) for field in APP_SERVER_MODEL_SELECTION_FIELDS}
    if (
        not isinstance(value, dict)
        or set(value) != set(APP_SERVER_MODEL_SELECTION_FIELDS)
        or not all(isinstance(item, str) and item for item in expected.values())
        or value != expected
    ):
        raise HarnessError("host adapter app server model selection conflicts with packet")


def _record_lane_execution_evidence(
    attempt: dict[str, Any],
    lane: dict[str, Any],
    packet: dict[str, Any],
    workspace: dict[str, Any],
    evidence: Any,
) -> None:
    workspace_root = workspace.get("path")
    if not isinstance(workspace_root, str) or not workspace_root:
        raise HarnessError("host adapter workspace must include path")
    if not isinstance(evidence, dict):
        raise HarnessError("host adapter lane execution evidence must be an object")
    read_only = lane["kind"] == "validate" or packet.get("workspace_write_access") == "read_only"
    expected_sandbox = "read-only" if read_only else "workspace-write"
    if (
        evidence.get("lane_id") != lane["lane_id"]
        or evidence.get("workspace_root") != workspace_root
        or evidence.get("sandbox") != expected_sandbox
        or evidence.get("ambient_mcp") is not False
        or evidence.get("runtime_provider") != packet["runtime_provider"]
        or evidence.get("agent_identity") != packet["agent_identity"]
        or not isinstance(evidence.get("thread_id"), str)
        or not evidence["thread_id"]
        or not isinstance(evidence.get("turn_id"), str)
        or not evidence["turn_id"]
        or not isinstance(evidence.get("workspace_status_before"), str)
        or not isinstance(evidence.get("workspace_status_after"), str)
    ):
        raise HarnessError("host adapter lane execution evidence conflicts with packet")
    _validate_app_server_model_selection(packet, evidence.get("app_server_model_selection"))
    is_current_packet = packet.get("version") == CURRENT_PACKET_API
    if is_current_packet and evidence.get("terminal_status") != "completed":
        _record_host_terminal_observation(attempt, packet, evidence)
        records = attempt.setdefault("execution_evidence", [])
        if any(record.get("lane_id") == lane["lane_id"] for record in records):
            raise HarnessError("host adapter produced duplicate lane execution evidence")
        records.append(copy.deepcopy(evidence))
        return
    selected_tools = evidence.get("selected_tools_used")
    tool_calls = evidence.get("tool_calls")
    command_results = evidence.get("command_results")
    if (
        not isinstance(selected_tools, list)
        or not selected_tools
        or not all(isinstance(tool, str) and tool for tool in selected_tools)
        or len(set(selected_tools)) != len(selected_tools)
        or not isinstance(tool_calls, list)
        or not all(isinstance(call, str) and call for call in tool_calls)
        or not isinstance(command_results, list)
        or not all(
            isinstance(result, dict)
            and result.get("cwd") == workspace_root
            and result.get("runtime_provider") == packet["runtime_provider"]
            for result in command_results
        )
    ):
        raise HarnessError("host adapter lane execution evidence lacks packet tool proof")
    access_key = "validator_access" if read_only else "writer_access"
    required_access = "read_only" if read_only else "workspace_write"
    bindings = {binding["tool"]: binding for binding in packet["tool_bindings"]}
    if any(tool not in bindings for tool in selected_tools) or not any(
        bindings[tool][access_key] == required_access for tool in selected_tools
    ):
        raise HarnessError("host adapter lane did not use a packet-selected tool with required access")
    if read_only and evidence["workspace_status_before"] != evidence["workspace_status_after"]:
        raise HarnessError("read-only packet lane changed workspace")
    records = attempt.setdefault("execution_evidence", [])
    if any(record.get("lane_id") == lane["lane_id"] for record in records):
        raise HarnessError("host adapter produced duplicate lane execution evidence")
    records.append(copy.deepcopy(evidence))
    _record_host_terminal_observation(attempt, packet, evidence)


def _record_node_observation(attempt: dict[str, Any], node: dict[str, Any], observation: dict[str, Any]) -> None:
    record = {"node_id": node["lane_id"], "node_kind": node["node_kind"], **copy.deepcopy(observation)}
    observations = attempt["node_observations"]
    if any(item.get("node_id") == node["lane_id"] for item in observations):
        raise HarnessError("execution node produced duplicate observation")
    node["observation"] = copy.deepcopy(record)
    observations.append(record)


def _approval_matches(approval: dict[str, Any], gate: str, path: str, attempt_id: str, ttl_seconds: int, now: datetime) -> bool:
    if approval["gate"] != gate or approval["attempt_id"] != attempt_id:
        return False
    issued_at = _parse_timestamp(approval["issued_at"])
    if issued_at > now or now - issued_at > timedelta(seconds=ttl_seconds):
        return False
    return _path_matches(path, approval["paths"])


def _gate_blockers(packet: dict[str, Any], paths: list[str], now: datetime) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for path in paths:
        for gate, patterns in packet["approval_gates"].items():
            if not _path_matches(path, patterns):
                continue
            approved = any(
                _approval_matches(
                    approval,
                    gate,
                    path,
                    packet["attempt_id"],
                    packet["retry_policy"]["approval_ttl_seconds"],
                    now,
                )
                for approval in packet["approvals"]
            )
            if not approved:
                blockers.append({"kind": "approval", "gate": gate, "path": path})
    return blockers


def _collect_changes(root: Path, base_commit: str) -> list[dict[str, str]]:
    status, stdout, stderr = _run_command(root, ["git", "diff", "--name-status", "-z", base_commit, "--"])
    if status:
        raise HarnessError(f"could not read changed paths: {stderr.strip()}")
    tokens = stdout.split("\0")
    changes: list[dict[str, str]] = []
    index = 0
    while index < len(tokens) and tokens[index]:
        status_code = tokens[index]
        index += 1
        if status_code[:1] in {"R", "C"}:
            if index + 1 >= len(tokens):
                raise HarnessError("malformed renamed change-set entry")
            changes.append({"path": _safe_path(tokens[index]), "kind": "renamed_from"})
            changes.append({"path": _safe_path(tokens[index + 1]), "kind": "renamed_to"})
            index += 2
            continue
        if index >= len(tokens):
            raise HarnessError("malformed change-set entry")
        kind = {"A": "added", "M": "modified", "D": "deleted", "T": "type_changed", "U": "unmerged"}.get(status_code[:1], status_code[:1].lower())
        changes.append({"path": _safe_path(tokens[index]), "kind": kind})
        index += 1
    status, stdout, stderr = _run_command(root, ["git", "ls-files", "--others", "--exclude-standard", "-z"])
    if status:
        raise HarnessError(f"could not read untracked paths: {stderr.strip()}")
    seen = {(change["path"], change["kind"]) for change in changes}
    for path in stdout.split("\0"):
        if path and (_safe_path(path), "untracked") not in seen:
            changes.append({"path": _safe_path(path), "kind": "untracked"})
    return changes


def _assert_workspace_baseline(
    lane: dict[str, Any],
    workspace: dict[str, Any],
    base_commit: str,
) -> None:
    path = workspace.get("path")
    if not isinstance(path, str) or not Path(path).is_dir():
        raise WorkspaceBaselineError("host adapter workspace path is unavailable")
    baseline = workspace.get("baseline")
    if not isinstance(baseline, dict):
        raise WorkspaceBaselineError("host adapter workspace lacks baseline evidence")
    dependencies = lane.get("dependencies")
    if not isinstance(dependencies, list) or not all(isinstance(item, str) and item for item in dependencies):
        raise WorkspaceBaselineError("packet lane has invalid dependencies")
    if not dependencies:
        if baseline.get("kind") == "packet_base" and baseline.get("base_commit") == base_commit and baseline.get("clean") is True:
            return
        raise WorkspaceBaselineError("workspace baseline does not match clean packet base")
    if baseline.get("kind") == "predecessor" and baseline.get("lane_id") in dependencies:
        return
    raise WorkspaceBaselineError("workspace baseline does not match packet predecessor")


def _assert_workspace_readonly_artifacts(packet: dict[str, Any], workspace: dict[str, Any]) -> None:
    expected = packet.get("readonly_artifacts", [])
    if not isinstance(expected, list):
        raise WorkspaceBaselineError("packet readonly_artifacts is invalid")
    observed = workspace.get("readonly_artifacts", [])
    artifact_root = workspace.get("readonly_artifact_root")
    if not expected:
        if observed not in (None, []) or artifact_root is not None:
            raise WorkspaceBaselineError("host adapter materialized unexpected readonly artifacts")
        return
    policy = packet.get("readonly_artifact_policy")
    if not isinstance(policy, dict) or not isinstance(policy.get("artifact_max_bytes"), int):
        raise WorkspaceBaselineError("packet readonly artifact policy is invalid")
    artifact_max_bytes = policy["artifact_max_bytes"]
    if not isinstance(observed, list) or not isinstance(artifact_root, str) or not Path(artifact_root).is_dir():
        raise WorkspaceBaselineError("host adapter readonly artifacts are unavailable")
    if len(observed) != len(expected):
        raise WorkspaceBaselineError("host adapter readonly artifact count conflicts with packet")
    expected_by_key = {
        (item["kind"], item["source_run_id"], item["source_attempt_id"]): item
        for item in expected
    }
    observed_keys: set[tuple[str, str, str]] = set()
    for artifact in observed:
        if not isinstance(artifact, dict):
            raise WorkspaceBaselineError("host adapter readonly artifact is invalid")
        key = (artifact.get("kind"), artifact.get("source_run_id"), artifact.get("source_attempt_id"))
        expected_artifact = expected_by_key.get(key)
        path = artifact.get("path")
        if (
            expected_artifact is None
            or key in observed_keys
            or artifact.get("sha256") != expected_artifact["sha256"]
            or artifact.get("byte_length") != expected_artifact["byte_length"]
            or expected_artifact["byte_length"] > artifact_max_bytes
            or not isinstance(path, str)
            or not Path(path).is_file()
            or Path(path).parent != Path(artifact_root)
        ):
            raise WorkspaceBaselineError("host adapter readonly artifact conflicts with packet")
        payload = Path(path).read_bytes()
        if len(payload) != expected_artifact["byte_length"] or hashlib.sha256(payload).hexdigest() != expected_artifact["sha256"]:
            raise WorkspaceBaselineError("host adapter readonly artifact content conflicts with packet")
        observed_keys.add(key)


def _claim_field_matches_type(value: Any, field_type: str) -> bool:
    if field_type == "nonempty_string":
        return isinstance(value, str) and bool(value)
    if field_type == "string_list":
        return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)
    if field_type == "friction_list":
        return isinstance(value, list) and all(
            isinstance(item, dict) and isinstance(item.get("category"), str) and bool(item["category"])
            for item in value
        )
    raise HarnessError("claim schema has unsupported field type")


def _validate_managed_claim(
    claim: Any,
    *,
    required_claim_kind: str,
    claim_schema: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(claim, dict):
        raise ClaimError("managed claim must be an object", subcode="claim_not_object")
    if claim.get("kind") != required_claim_kind:
        raise ClaimError("managed claim has invalid result kind", subcode="claim_kind_mismatch")
    required_fields = claim_schema.get("required_fields")
    field_types = claim_schema.get("field_types")
    optional_field_types = claim_schema.get("optional_field_types")
    constraints = claim_schema.get("field_constraints")
    if (
        not isinstance(required_fields, list)
        or not all(isinstance(field, str) and field for field in required_fields)
        or not isinstance(field_types, dict)
        or set(field_types) != set(required_fields)
        or not isinstance(optional_field_types, dict)
        or not isinstance(constraints, dict)
    ):
        raise HarnessError("lane claim schema is invalid")
    for field in required_fields:
        if field not in claim:
            raise ClaimError(f"managed claim missing required field `{field}`", subcode="claim_field_missing")
        if not _claim_field_matches_type(claim[field], field_types[field]):
            raise ClaimError(f"managed claim field `{field}` has invalid type", subcode="claim_field_type_invalid")
    for field, field_type in optional_field_types.items():
        if not isinstance(field, str) or not isinstance(field_type, str):
            raise HarnessError("lane claim schema optional fields are invalid")
        if field in claim and not _claim_field_matches_type(claim[field], field_type):
            raise ClaimError(f"managed claim field `{field}` has invalid type", subcode="claim_field_type_invalid")
    for field, allowed_values in constraints.items():
        if claim.get(field) not in allowed_values:
            raise ClaimError(
                f"managed claim field `{field}` has unsupported value",
                subcode="claim_field_constraint_invalid",
            )
    return copy.deepcopy(claim)


def _claim_schema_for_lane(root: Path, lane: dict[str, Any], packet_version: int) -> dict[str, Any]:
    schema = lane.get("claim_schema")
    if isinstance(schema, dict) and "field_types" in schema and "optional_field_types" in schema:
        return schema
    if packet_version == CURRENT_PACKET_API:
        raise HarnessError("packet V7 lane lacks typed claim schema")
    role_name = lane.get("role")
    roles, claim_fields = _load_role_catalog(root)
    role = roles.get(role_name)
    if not isinstance(role, dict):
        raise HarnessError(f"lane `{lane['lane_id']}` has unknown role `{role_name}`")
    return _claim_schema(role, claim_fields)


def _normalize_claim_observation(value: Any, lane: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) - CLAIM_OBSERVATION_FIELDS:
        raise HarnessError("host adapter claim observation is invalid")
    state = value.get("state")
    if (
        value.get("version") != CLAIM_OBSERVATION_VERSION
        or value.get("lane_id") != lane["lane_id"]
        or value.get("thread_id") != evidence.get("thread_id")
        or state not in CLAIM_OBSERVATION_STATES
    ):
        raise HarnessError("host adapter claim observation conflicts with lane evidence")
    if state == "object":
        if "candidate_claim" not in value:
            raise HarnessError("host adapter object claim observation lacks candidate")
    elif "candidate_claim" in value:
        raise HarnessError("host adapter non-object claim observation includes candidate")
    if "content_digest" in value and (
        not isinstance(value["content_digest"], str)
        or re.fullmatch(r"[0-9a-f]{64}", value["content_digest"]) is None
    ):
        raise HarnessError("host adapter claim observation digest is invalid")
    if "content_length" in value and (not isinstance(value["content_length"], int) or value["content_length"] < 0):
        raise HarnessError("host adapter claim observation length is invalid")
    normalized = {
        "version": CLAIM_OBSERVATION_VERSION,
        "lane_id": lane["lane_id"],
        "thread_id": evidence["thread_id"],
        "state": state,
    }
    for field in ("content_digest", "content_length", "candidate_claim"):
        if field in value:
            normalized[field] = copy.deepcopy(value[field])
    return normalized


def _record_claim_observation(attempt: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    record = {
        "lane_id": observation["lane_id"],
        "thread_id": observation["thread_id"],
        "state": observation["state"],
    }
    for field in ("content_digest", "content_length"):
        if field in observation:
            record[field] = observation[field]
    records = attempt.setdefault("evidence", {}).setdefault("claim_observations", [])
    if any(item.get("lane_id") == record["lane_id"] for item in records):
        raise HarnessError("lane produced duplicate claim observation")
    records.append(record)
    return record


def _validator_criterion(root: Path, attempt: dict[str, Any]) -> dict[str, str]:
    nodes = {node.get("lane_id"): node for node in attempt["nodes"] if isinstance(node, dict)}
    validator_lane = nodes.get("validate")
    integration_node = nodes.get("integrate")
    claims = {
        record.get("lane_id"): record.get("claim")
        for record in attempt["claims"]
        if isinstance(record, dict)
    }
    validator_claim = claims.get("validate")
    if (
        not isinstance(validator_lane, dict)
        or not isinstance(integration_node, dict)
        or not isinstance(integration_node.get("workspace"), dict)
        or not isinstance(validator_claim, dict)
    ):
        return {"status": "failed", "evidence_ref": "validator_claim"}
    try:
        claim = _validate_managed_claim(
            validator_claim,
            required_claim_kind=validator_lane["required_claim_kind"],
            claim_schema=_claim_schema_for_lane(root, validator_lane, attempt["packet"]["version"]),
        )
    except (HarnessError, KeyError, TypeError):
        return {"status": "failed", "evidence_ref": "validator_claim"}
    if (
        claim.get("kind") != validator_lane.get("required_claim_kind")
        or claim.get("verdict") != "pass"
        or validator_lane.get("workspace") != integration_node["workspace"]
    ):
        return {"status": "failed", "evidence_ref": "validator_claim"}
    return {"status": "proven", "evidence_ref": "validator_claim"}


def _verification_workspace(attempt: dict[str, Any]) -> Path:
    integration_node = next(
        (node for node in attempt["nodes"] if isinstance(node, dict) and node.get("lane_id") == "integrate"),
        None,
    )
    if not isinstance(integration_node, dict) or not isinstance(integration_node.get("workspace"), dict):
        raise HarnessError("verification requires integrated workspace")
    path = integration_node["workspace"].get("path")
    if not isinstance(path, str) or not Path(path).is_dir():
        raise HarnessError("verification workspace is unavailable")
    return Path(path).resolve()


def _require_lane_execution_evidence(attempt: dict[str, Any]) -> None:
    nodes = {
        node["lane_id"]: node
        for node in attempt["nodes"]
        if isinstance(node, dict) and node.get("node_kind") == "agent"
    }
    records = attempt.get("execution_evidence")
    if not isinstance(records, list) or {record.get("lane_id") for record in records if isinstance(record, dict)} != set(nodes):
        raise HarnessError("verification requires host execution evidence for every dispatched lane")
    for record in records:
        node = nodes[record["lane_id"]]
        workspace = node.get("workspace")
        if not isinstance(workspace, dict) or record.get("workspace_root") != workspace.get("path"):
            raise HarnessError("host execution evidence workspace conflicts with lane")


def _verify_managed(
    root: Path,
    packet: dict[str, Any],
    attempt: dict[str, Any],
    *,
    collect_changes: ChangeCollector,
    now: datetime,
) -> dict[str, Any]:
    _require_lane_execution_evidence(attempt)
    verification_root = _verification_workspace(attempt)
    changes = collect_changes(verification_root, packet["base_commit"])
    normalized_changes: list[dict[str, str]] = []
    blockers: list[dict[str, str]] = []
    for change in changes:
        if not isinstance(change, dict) or not isinstance(change.get("path"), str) or not isinstance(change.get("kind"), str):
            raise HarnessError("change-set entry must contain path and kind")
        path = _safe_path(change["path"])
        normalized_changes.append({"path": path, "kind": change["kind"]})
        if not _path_matches(path, packet["allowed_paths"]):
            blockers.append({"kind": "scope", "path": path})
    blockers.extend(_gate_blockers(packet, [change["path"] for change in normalized_changes], now))

    check_node = next(
        (node for node in attempt["nodes"] if isinstance(node, dict) and node.get("node_kind") == "check"),
        None,
    )
    if not isinstance(check_node, dict) or not isinstance(check_node.get("observation"), dict):
        raise HarnessError("verification requires check-node observation")
    checks = check_node["observation"].get("checks")
    if not isinstance(checks, list) or any(not isinstance(check, dict) for check in checks):
        raise HarnessError("check-node observation lacks checks")
    checks_by_name = {check.get("name"): check for check in checks}
    if set(checks_by_name) != set(packet["checks"]):
        raise HarnessError("check-node observation conflicts with packet checks")
    for name, command in packet["checks"].items():
        check = checks_by_name[name]
        if check.get("command") != command or not isinstance(check.get("exit_code"), int):
            raise HarnessError(f"check-node observation for `{name}` conflicts with packet")
        code = check["exit_code"]
        if code:
            blockers.append({"kind": "check", "name": name})

    postconditions: list[dict[str, str]] = []
    for name in packet.get("postconditions", []):
        if name != "workspace_unchanged":
            raise HarnessError(f"unsupported packet postcondition `{name}`")
        status = "proven" if not normalized_changes else "failed"
        postconditions.append({"name": name, "status": status})
        if status == "failed":
            blockers.append({"kind": "postcondition", "name": name})

    criteria: list[dict[str, Any]] = []
    for criterion in packet["acceptance_criteria"]:
        kind = criterion["kind"]
        result: dict[str, Any] = {"id": criterion["id"], "kind": kind}
        if kind == "check":
            check = checks_by_name[criterion["check"]]
            result.update({"status": "proven" if check["exit_code"] == 0 else "failed", "evidence_ref": f"checks.{criterion['check']}"})
        elif kind == "change_set":
            proven = all(any(_path_matches(change["path"], [pattern]) for change in normalized_changes) for pattern in criterion["paths"])
            result.update({"status": "proven" if proven else "failed", "evidence_ref": "change_set"})
        elif kind == "validator":
            result.update(_validator_criterion(root, attempt))
        else:
            evidence = packet["review_evidence"] if kind == "review" else packet["manual_evidence"]
            result.update({"status": "proven" if isinstance(evidence, dict) else "review_required", "evidence_ref": kind})
        if result["status"] == "failed":
            blockers.append({"kind": "criterion", "id": criterion["id"]})
        criteria.append(result)
    return {
        "change_set": normalized_changes,
        "checks": checks,
        "postconditions": postconditions,
        "criteria": criteria,
        "blockers": blockers,
    }


def _outcome_for_verification(verification: dict[str, Any], retry_policy: dict[str, Any]) -> tuple[str, list[str]]:
    kinds = {blocker["kind"] for blocker in verification["blockers"]}
    if "scope" in kinds:
        return "scope_escape", ["block"]
    if "approval" in kinds:
        return "approval_required", ["request_approval", "retry", "block"]
    if kinds:
        decisions = ["block"]
        if "verification_failed" in retry_policy["retryable_reasons"]:
            decisions = ["retry", "escalate", "block"]
        return "verification_failed", decisions
    if any(criterion["status"] == "review_required" for criterion in verification["criteria"]):
        decisions = ["block"]
        if "review_required" in retry_policy["retryable_reasons"]:
            decisions = ["retry", "block"]
        return "review_required", decisions
    return "verification_passed", ["accept", "block"]


def _record_attempt_friction(
    root: Path,
    run: dict[str, Any],
    attempt: dict[str, Any],
    *,
    lane: dict[str, Any] | None,
    source: str,
    phase: str,
    code: str,
    evidence_ref: str,
) -> dict[str, Any]:
    event = record_friction_event(
        root,
        run_id=run["run_id"],
        attempt_id=attempt["attempt_id"],
        packet=attempt["packet"],
        lane=lane,
        source=source,
        phase=phase,
        code=code,
        evidence_ref=evidence_ref,
    )
    attempt["friction_event_ids"].append(event["event_id"])
    return event


def _record_failure(
    root: Path,
    run: dict[str, Any],
    policy: dict[str, Any],
    attempt: dict[str, Any],
    reason: str,
    detail: str,
    *,
    phase: str,
) -> dict[str, Any]:
    _record_attempt_friction(
        root,
        run,
        attempt,
        lane=None,
        source="host",
        phase=phase,
        code=reason,
        evidence_ref=f"outcome.{reason}",
    )
    failure = {"reason": reason, "phase": phase, "detail": detail}
    attempt.setdefault("evidence", {})["failure"] = failure
    decisions = ["block"]
    if reason in attempt["packet"]["retry_policy"]["retryable_reasons"]:
        decisions = ["retry", "escalate", "block"]
    _set_outcome(run, attempt, policy, reason, decisions, ["friction_event_ids", "evidence.failure"], detail=detail)
    return _persist_outcome_transition(root, run, attempt, policy, reason)


def _record_core_failure_and_terminalize(
    root: Path,
    run: dict[str, Any],
    policy: dict[str, Any],
    attempt: dict[str, Any],
    reason: str,
    detail: str,
    *,
    phase: str,
) -> dict[str, Any]:
    _record_attempt_friction(
        root,
        run,
        attempt,
        lane=None,
        source="controller",
        phase=phase,
        code=reason,
        evidence_ref="evidence.failure",
    )
    attempt.setdefault("evidence", {})["failure"] = {
        "reason": reason,
        "phase": phase,
        "detail": detail,
    }
    _write_run(root, run)
    return _terminalize_collected_attempt(root, run, attempt)


def _normalize_terminal_evidence(exc: Exception, packet: dict[str, Any]) -> dict[str, Any] | None:
    raw = getattr(exc, "terminal_observation", None)
    if raw is None:
        legacy = getattr(exc, "timeout_observation", None)
        if legacy is None:
            return None
        try:
            normalized_legacy = normalize_timeout_observation(legacy, packet)
        except TimeoutObservationError as error:
            return {"version": 1, "invalid": True, "error": str(error)}
        raw = {
            **normalized_legacy,
            "kind": "timeout",
            "source": "host_timeout_interrupt",
            "error": None,
        }
    try:
        return normalize_terminal_observation(raw, packet)
    except TerminalObservationError as error:
        return {"version": 1, "invalid": True, "error": str(error)}


def _terminal_failure_reason(packet: dict[str, Any], terminal_evidence: dict[str, Any]) -> str:
    if terminal_evidence.get("invalid") or terminal_evidence.get("kind") != "timeout":
        return "dispatch_failed"
    if terminal_evidence["final_claim_state"]["state"] != "missing":
        return "dispatch_timeout"
    if not any(command["state"] == "completed" for command in terminal_evidence["command_states"]):
        return "dispatch_timeout"
    lane_id = terminal_evidence["lane_id"]
    lane = next((item for item in packet["lanes"] if item["lane_id"] == lane_id), None)
    if isinstance(lane, dict) and lane["kind"] == "work" and lane["write_capable"] is True:
        return "writer_completion_missing"
    return "dispatch_timeout"


def _normalize_retained_artifacts(exc: Exception, packet: dict[str, Any]) -> list[dict[str, Any]]:
    retained = packet.get("retained_artifacts", [])
    if not isinstance(retained, list):
        raise HarnessError("packet retained_artifacts is invalid")
    limits = {
        item["kind"]: item["max_bytes"]
        for item in retained
        if isinstance(item, dict)
        and item.get("kind") in READONLY_ARTIFACT_KINDS
        and isinstance(item.get("max_bytes"), int)
        and item["max_bytes"] > 0
    }
    raw = getattr(exc, "evidence_artifacts", [])
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise HarnessError("host retained artifacts are invalid")
    normalized: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"kind", "content"}:
            raise HarnessError("host retained artifact has invalid fields")
        kind = item["kind"]
        if kind not in limits:
            raise HarnessError(f"host retained artifact `{kind}` was not packet-approved")
        content = item["content"]
        if kind == "sanitized_command_trace":
            _validate_sanitized_command_trace(content, limits[kind])
        elif len(_artifact_content_bytes(content)) > limits[kind]:
            raise HarnessError("retained artifact exceeds artifact_max_bytes")
        normalized.append({"kind": kind, "content": copy.deepcopy(content)})
    if len({item["kind"] for item in normalized}) != len(normalized):
        raise HarnessError("host retained artifacts must not contain duplicate kinds")
    return normalized


def _record_terminal_failure(
    root: Path,
    run: dict[str, Any],
    policy: dict[str, Any],
    attempt: dict[str, Any],
    detail: str,
    *,
    phase: str,
    terminal_evidence: dict[str, Any],
    artifacts: list[dict[str, Any]] | None = None,
    artifact_rejections: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    reason = _terminal_failure_reason(attempt["packet"], terminal_evidence)
    is_timeout = reason == "dispatch_timeout"
    _record_attempt_friction(
        root,
        run,
        attempt,
        lane=None,
        source="host",
        phase=phase,
        code=reason,
        evidence_ref=f"outcome.{reason}",
    )
    attempt.setdefault("evidence", {})["failure"] = {
        "reason": reason,
        "phase": phase,
        "detail": detail,
    }
    attempt["evidence"]["terminal_observation"] = terminal_evidence
    if artifacts:
        attempt["evidence"]["artifacts"] = artifacts
    if artifact_rejections:
        attempt["evidence"]["artifact_rejections"] = artifact_rejections
    decisions = ["block"]
    if is_timeout:
        decisions = list(attempt["packet"]["execution_budget"]["timeout_decisions"])
    elif not terminal_evidence.get("invalid") and reason in attempt["packet"]["retry_policy"]["retryable_reasons"]:
        decisions = ["retry", "escalate", "block"]
    evidence_refs = ["friction_event_ids", "evidence.failure", "evidence.terminal_observation"]
    if artifacts:
        evidence_refs.append("evidence.artifacts")
    if artifact_rejections:
        evidence_refs.append("evidence.artifact_rejections")
    _set_outcome(
        run,
        attempt,
        policy,
        reason,
        decisions,
        evidence_refs,
        detail=detail,
    )
    return _persist_outcome_transition(root, run, attempt, policy, reason)


def _record_dispatch_exception(
    root: Path,
    run: dict[str, Any],
    policy: dict[str, Any],
    attempt: dict[str, Any],
    exc: Exception,
    *,
    phase: str,
) -> dict[str, Any]:
    if isinstance(exc, WorkspaceBaselineError):
        return _record_failure(root, run, policy, attempt, "workspace_baseline_invalid", str(exc), phase=phase)
    if attempt["packet"].get("version") == CURRENT_PACKET_API:
        host_observation = getattr(exc, "host_terminal_observation", None)
        if isinstance(host_observation, dict):
            try:
                normalize_host_terminal_observation(
                    host_observation,
                    attempt["packet"],
                    binding=_attempt_lease_binding(run, attempt),
                )
            except TerminalObservationError as error:
                raise HarnessError(f"host terminal observation is invalid: {error}") from error
            _record_host_terminal_observation(
                attempt,
                attempt["packet"],
                {"host_terminal_observation": host_observation},
            )
            if _has_terminal_host_failure(attempt):
                _write_run(root, run)
                return _terminalize_collected_attempt(root, run, attempt)
            if _has_completed_host_observations(attempt):
                return _record_core_failure_and_terminalize(
                    root,
                    run,
                    policy,
                    attempt,
                    "dispatch_failed",
                    str(exc),
                    phase=phase,
                )
    terminal_evidence = _normalize_terminal_evidence(exc, attempt["packet"])
    if terminal_evidence is not None:
        try:
            artifacts = _normalize_retained_artifacts(exc, attempt["packet"])
            artifact_rejections: list[dict[str, str]] = []
        except HarnessError as error:
            artifacts = []
            artifact_rejections = [{"reason": str(error)[:256]}]
        return _record_terminal_failure(
            root,
            run,
            policy,
            attempt,
            str(exc),
            phase=phase,
            terminal_evidence=terminal_evidence,
            artifacts=artifacts,
            artifact_rejections=artifact_rejections,
        )
    return _record_failure(root, run, policy, attempt, "dispatch_failed", str(exc), phase=phase)


def _cancel_active_lanes(
    root: Path,
    run: dict[str, Any],
    attempt: dict[str, Any],
    adapter: Any,
    active_handles: list[tuple[dict[str, Any], Any]],
    *,
    phase: str,
) -> None:
    cancellation = attempt.get("cancellation_request")
    cancellation_request_id = cancellation.get("cancellation_request_id") if isinstance(cancellation, dict) else None
    for lane, handle in active_handles:
        try:
            if isinstance(cancellation_request_id, str) and cancellation_request_id:
                _adapter_call(adapter, "cancel_lane", handle, cancellation_request_id)
            else:
                _adapter_call(adapter, "cancel_lane", handle)
        except Exception:
            _record_attempt_friction(
                root,
                run,
                attempt,
                lane=lane,
                source="host",
                phase=phase,
                code="cancellation_failed",
                evidence_ref=f"lanes.{lane['lane_id']}.cancellation",
            )


def _record_lane_claim(
    root: Path,
    run: dict[str, Any],
    attempt: dict[str, Any],
    lane: dict[str, Any],
    claim: Any,
    *,
    packet_version: int,
) -> None:
    try:
        if lane.get("node_kind") != "agent":
            raise HarnessError(f"lane `{lane['lane_id']}` cannot collect an agent claim")
        required_claim_kind = lane.get("required_claim_kind")
        if not isinstance(required_claim_kind, str) or not required_claim_kind:
            raise HarnessError(f"lane `{lane['lane_id']}` lacks required claim kind")
        normalized_claim = _validate_managed_claim(
            claim,
            required_claim_kind=required_claim_kind,
            claim_schema=_claim_schema_for_lane(root, lane, packet_version),
        )
    except ClaimError:
        raise
    except HarnessError as exc:
        raise ClaimError(str(exc)) from exc
    attempt["claims"].append({"lane_id": lane["lane_id"], "claim": normalized_claim})
    for friction in normalized_claim.get("frictions", []):
        _record_attempt_friction(
            root,
            run,
            attempt,
            lane=lane,
            source="validator" if lane["kind"] == "validate" else "agent",
            phase="validator" if lane["kind"] == "validate" else "claim",
            code=friction["category"],
            evidence_ref=f"claims.{lane['lane_id']}",
        )


def _claim_observation_failure(observation: dict[str, Any]) -> ClaimError | None:
    state = observation["state"]
    if state == "missing":
        return ClaimError("managed final claim is missing", subcode="missing_final_claim")
    if state == "non_json":
        return ClaimError("managed final claim is not JSON", subcode="claim_not_json")
    if state == "json_non_object":
        return ClaimError("managed final claim is not a JSON object", subcode="claim_not_object")
    return None


def _claim_repair_admission(
    attempt: dict[str, Any],
    lane: dict[str, Any],
    packet: dict[str, Any],
    evidence: dict[str, Any],
    capabilities: dict[str, str],
) -> tuple[bool, str, int]:
    repair = packet.get("claim_repair")
    if not isinstance(repair, dict):
        raise HarnessError("packet V7 lacks claim repair contract")
    max_repairs = repair.get("max_repairs_per_lane")
    if not isinstance(max_repairs, int) or max_repairs < 1:
        raise HarnessError("packet claim repair budget is invalid")
    records = attempt.setdefault("evidence", {}).setdefault("claim_repair", [])
    repair_count = sum(
        1
        for record in records
        if isinstance(record, dict)
        and record.get("lane_id") == lane["lane_id"]
        and record.get("admission", {}).get("admitted") is True
    )
    if lane.get("node_kind") != "agent":
        return False, "lane_not_agent", repair_count
    if evidence.get("terminal_status") != "completed":
        return False, "terminal_completion_not_confirmed", repair_count
    if not isinstance(evidence.get("thread_id"), str) or not evidence["thread_id"]:
        return False, "original_thread_missing", repair_count
    if repair_count >= max_repairs:
        return False, "repair_budget_exhausted", repair_count
    reserve = packet.get("execution_budget", {}).get("finalization_reserve_seconds")
    if not isinstance(reserve, int) or reserve <= 0:
        return False, "finalization_reserve_unavailable", repair_count
    capability = repair.get("required_host_capability")
    if not isinstance(capability, str) or capabilities.get(capability) != "enforced":
        return False, "required_host_capability_unavailable", repair_count
    return True, "eligible", repair_count


def _normalize_claim_repair_result(
    value: Any,
    lane: dict[str, Any],
    packet: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != CLAIM_REPAIR_RESULT_FIELDS:
        raise HarnessError("host adapter claim repair result is invalid")
    finalization = value["finalization_evidence"]
    if (
        not isinstance(finalization, dict)
        or not CLAIM_REPAIR_FINALIZATION_FIELDS <= set(finalization)
        or set(finalization) - CLAIM_REPAIR_FINALIZATION_FIELDS - CLAIM_REPAIR_FINALIZATION_OPTIONAL_FIELDS
    ):
        raise HarnessError("host adapter claim repair evidence is invalid")
    elapsed = finalization["elapsed_seconds"]
    reserve = packet["execution_budget"]["finalization_reserve_seconds"]
    if (
        finalization["lane_id"] != lane["lane_id"]
        or finalization["thread_id"] != evidence["thread_id"]
        or not isinstance(finalization["turn_id"], str)
        or not finalization["turn_id"]
        or finalization["terminal_status"] not in CLAIM_REPAIR_FINALIZATION_TERMINAL_STATUSES
        or finalization["sandbox"] != "read-only"
        or finalization["tool_calls"] != []
        or finalization["command_results"] != []
        or finalization["workspace_status_before"] != finalization["workspace_status_after"]
        or finalization["agent_identity"] != packet["agent_identity"]
        or finalization["prompt_contract_version"] != 1
        or not isinstance(finalization["prompt_digest"], str)
        or re.fullmatch(r"[0-9a-f]{64}", finalization["prompt_digest"]) is None
        or isinstance(elapsed, bool)
        or not isinstance(elapsed, (int, float))
        or elapsed < 0
        or elapsed > reserve
    ):
        raise HarnessError("host adapter claim repair evidence conflicts with packet")
    _validate_app_server_model_selection(packet, finalization.get("app_server_model_selection"))
    observation = _normalize_claim_observation(value["claim_observation"], lane, evidence)
    if finalization["terminal_status"] == "timed_out" and observation["state"] != "missing":
        raise HarnessError("timed-out claim repair returned a candidate")
    return observation, copy.deepcopy(finalization)


def _record_v7_lane_claim(
    root: Path,
    run: dict[str, Any],
    attempt: dict[str, Any],
    adapter: Any,
    capabilities: dict[str, str],
    lane: dict[str, Any],
    packet: dict[str, Any],
    workspace: dict[str, Any],
    handle: Any,
    evidence: dict[str, Any],
    value: Any,
) -> None:
    observation = _normalize_claim_observation(value, lane, evidence)
    observation_record = _record_claim_observation(attempt, observation)
    unusable = _claim_observation_failure(observation)
    if unusable is None:
        try:
            _record_lane_claim(
                root,
                run,
                attempt,
                lane,
                observation["candidate_claim"],
                packet_version=packet["version"],
            )
            return
        except ClaimError as exc:
            unusable = exc
    if unusable.subcode not in packet["claim_repair"]["admissible_subcodes"]:
        raise HarnessError("claim validation produced unsupported repair subcode")
    observation_record["subcode"] = unusable.subcode
    admitted, reason, repair_count = _claim_repair_admission(attempt, lane, packet, evidence, capabilities)
    repair_record = {
        "lane_id": lane["lane_id"],
        "observation": copy.deepcopy(observation_record),
        "subcode": unusable.subcode,
        "admission": {"admitted": admitted, "reason": reason},
        "repair_count": repair_count + (1 if admitted else 0),
    }
    attempt["evidence"]["claim_repair"].append(repair_record)
    if not admitted:
        raise unusable
    _write_run(root, run)
    try:
        result = _adapter_call(
            adapter,
            "repair_claim",
            handle,
            lane,
            packet,
            workspace,
            {"version": 1, "subcode": unusable.subcode, "detail": str(unusable)},
        )
        repaired_observation, finalization = _normalize_claim_repair_result(result, lane, packet, evidence)
        repair_record["finalization_identity"] = {
            "thread_id": finalization["thread_id"],
            "turn_id": finalization["turn_id"],
        }
        repair_record["safe_prompt_digest"] = finalization["prompt_digest"]
        if "app_server_model_selection" in finalization:
            repair_record["app_server_model_selection"] = copy.deepcopy(finalization["app_server_model_selection"])
        repaired_failure = _claim_observation_failure(repaired_observation)
        if repaired_failure is not None:
            raise repaired_failure
        _record_lane_claim(
            root,
            run,
            attempt,
            lane,
            repaired_observation["candidate_claim"],
            packet_version=packet["version"],
        )
    except ClaimError as exc:
        repair_record["repeated_validation"] = {"status": "invalid", "subcode": exc.subcode}
        _record_attempt_friction(
            root,
            run,
            attempt,
            lane=lane,
            source="host",
            phase="validator" if lane["kind"] == "validate" else "claim",
            code="claim_repair_failed",
            evidence_ref=f"evidence.claim_repair.{lane['lane_id']}",
        )
        raise
    except Exception:
        repair_record["repeated_validation"] = {"status": "finalization_failed"}
        _record_attempt_friction(
            root,
            run,
            attempt,
            lane=lane,
            source="host",
            phase="validator" if lane["kind"] == "validate" else "claim",
            code="claim_repair_failed",
            evidence_ref=f"evidence.claim_repair.{lane['lane_id']}",
        )
        raise
    repair_record["repeated_validation"] = {"status": "valid"}


def _record_verification_frictions(root: Path, run: dict[str, Any], attempt: dict[str, Any], verification: dict[str, Any]) -> None:
    for blocker in verification["blockers"]:
        kind = blocker["kind"]
        if kind == "check":
            source, phase, code = "check", "check", "check_failed"
        elif kind == "criterion" and blocker.get("id") == "validator":
            source, phase, code = "validator", "validator", "validator_failed"
        elif kind in {"scope", "approval"}:
            source, phase, code = "controller", "decision", f"{kind}_blocked"
        else:
            source, phase, code = "host", "integration", "verification_failed"
        _record_attempt_friction(
            root,
            run,
            attempt,
            lane=None,
            source=source,
            phase=phase,
            code=code,
            evidence_ref="evidence.blockers",
        )


def _execute_attempt(
    root: Path,
    run: dict[str, Any],
    policy: dict[str, Any],
    adapter: Any,
    *,
    run_check: CheckRunner | None,
    collect_changes: ChangeCollector,
    host_instance_id: str | None,
    now: datetime,
) -> dict[str, Any]:
    attempt = _active_attempt(run)
    packet = attempt["packet"]
    planned_blockers = _gate_blockers(packet, packet["planned_write_paths"], now)
    attempt["authorization"] = {"planned_write_paths": packet["planned_write_paths"], "blockers": planned_blockers}
    if planned_blockers:
        _record_attempt_friction(
            root,
            run,
            attempt,
            lane=None,
            source="controller",
            phase="decision",
            code="approval_required",
            evidence_ref="authorization.blockers",
        )
        _set_outcome(run, attempt, policy, "approval_required", ["request_approval", "retry", "block"], ["authorization"])
        return _persist_outcome_transition(root, run, attempt, policy, "approval_required")
    try:
        required_capabilities = set(policy["orchestration"]) | {policy["claim_repair"]["required_host_capability"]}
        if packet.get("version") == CURRENT_PACKET_API:
            terminal_contract = packet.get("terminal_observation_contract")
            if not isinstance(terminal_contract, dict) or not isinstance(terminal_contract.get("capability"), str):
                raise HarnessError("packet terminal observation contract is invalid")
            required_capabilities.update({terminal_contract["capability"], "execution_lease_duration_model"})
        capabilities = _adapter_capabilities(
            adapter,
            required_capabilities,
        )
    except Exception as exc:
        return _record_failure(root, run, policy, attempt, "dispatch_failed", str(exc), phase="dispatch")
    mode = packet["orchestration"]["name"]
    if capabilities.get(mode) != "enforced":
        detail = _adapter_unavailable_detail(adapter)
        _record_attempt_friction(
            root,
            run,
            attempt,
            lane=None,
            source="host",
            phase="dispatch",
            code="execution_mode_unavailable",
            evidence_ref="capabilities",
        )
        _set_outcome(
            run,
            attempt,
            policy,
            "execution_mode_unavailable",
            ["waive", "block"],
            ["capabilities"],
            detail=detail,
        )
        _transition(run, policy["states"], "awaiting_decision", "execution_mode_unavailable")
        _write_run(root, run)
        return _managed_result(run)
    terminalization_capabilities = {"host_terminal_observation_v2", "execution_lease_duration_model"}
    if packet.get("version") == CURRENT_PACKET_API and any(
        capabilities.get(capability) != "enforced"
        for capability in terminalization_capabilities
    ):
        return _record_failure(root, run, policy, attempt, "execution_mode_unavailable", "host lacks required terminalization capability", phase="dispatch")
    try:
        attempt["adapter_identity"] = _adapter_identity(adapter, packet["runtime_provider"])
    except Exception as exc:
        return _record_failure(root, run, policy, attempt, "dispatch_failed", str(exc), phase="dispatch")

    if packet.get("version") == CURRENT_PACKET_API:
        if host_instance_id is None:
            raise HarnessError("host instance identity is invalid")
        _issue_execution_lease(run, attempt, host_instance_id=host_instance_id, now=now)
        packet = _dispatch_packet(packet, attempt["execution_lease"])
    _transition(run, policy["states"], "running", "dispatch")
    _write_run(root, run)
    pending = {node["lane_id"]: node for node in attempt["nodes"]}
    workspaces: dict[str, dict[str, Any]] = {}
    active_handles: list[tuple[dict[str, Any], Any]] = []
    failure_phase = "dispatch"
    try:
        while pending:
            completed = {
                lane["lane_id"]
                for lane in attempt["nodes"]
                if lane.get("status") == "succeeded"
            }
            ready = [
                lane for lane in pending.values()
                if all(dependency in completed for dependency in lane["dependencies"])
            ]
            if not ready:
                raise HarnessError("lane scheduler found unresolved dependencies")

            work_lanes = [lane for lane in ready if lane["kind"] == "work"]
            if work_lanes:
                lane_slots = packet["orchestration"].get(
                    "max_parallel_lanes",
                    packet["orchestration"]["max_parallel_writers"],
                )
                writer_slots = packet["orchestration"]["max_parallel_writers"]
                scheduled: list[dict[str, Any]] = []
                for lane in work_lanes:
                    if not lane_slots:
                        break
                    if lane["write_capable"]:
                        if not writer_slots:
                            continue
                        writer_slots -= 1
                    scheduled.append(lane)
                    lane_slots -= 1
                for lane in scheduled:
                    workspace = _adapter_call(adapter, "prepare_workspace", lane, packet)
                    if not isinstance(workspace, dict):
                        raise HarnessError("host adapter workspace must be an object")
                    _assert_workspace_baseline(lane, workspace, packet["base_commit"])
                    _assert_workspace_readonly_artifacts(packet, workspace)
                    lane["workspace"] = copy.deepcopy(workspace)
                    bindings = _adapter_call(adapter, "verify_tool_bindings", lane, packet, workspace)
                    _record_tool_binding_evidence(attempt, lane, packet, workspace, bindings)
                    handle = _adapter_call(adapter, "dispatch_lane", lane, packet, workspace, _delegation_bridge(root, run, attempt, lane))
                    lane["status"] = "running"
                    active_handles.append((lane, handle))
                for lane, handle in active_handles[:]:
                    evidence = _adapter_call(adapter, "collect_lane_evidence", handle, lane, packet, lane["workspace"])
                    _record_lane_execution_evidence(attempt, lane, packet, lane["workspace"], evidence)
                    claim = _adapter_call(adapter, "collect_claim", handle)
                    if _sync_delegation_state(root, run, attempt):
                        _cancel_active_lanes(root, run, attempt, adapter, active_handles, phase="delegation")
                        _write_run(root, run)
                        return _managed_result(run)
                    if packet["version"] == CURRENT_PACKET_API:
                        _record_v7_lane_claim(
                            root,
                            run,
                            attempt,
                            adapter,
                            capabilities,
                            lane,
                            packet,
                            lane["workspace"],
                            handle,
                            evidence,
                            claim,
                        )
                    else:
                        _record_lane_claim(root, run, attempt, lane, claim, packet_version=packet["version"])
                    lane["status"] = "succeeded"
                    workspaces[lane["lane_id"]] = copy.deepcopy(lane["workspace"])
                    pending.pop(lane["lane_id"])
                    active_handles.remove((lane, handle))
                continue

            integration = next((lane for lane in ready if lane["kind"] == "integrate"), None)
            if integration is not None:
                failure_phase = "integration"
                workspace = _adapter_call(adapter, "materialize_final_state", integration, packet, workspaces)
                if not isinstance(workspace, dict):
                    raise HarnessError("host adapter final workspace must be an object")
                integration["workspace"] = copy.deepcopy(workspace)
                integration["status"] = "succeeded"
                _record_node_observation(attempt, integration, {"workspace": workspace})
                pending.pop(integration["lane_id"])
                continue

            validator = next((lane for lane in ready if lane["kind"] == "validate"), None)
            if validator is not None:
                failure_phase = "validator"
                integration = next(lane for lane in attempt["nodes"] if lane["lane_id"] == "integrate")
                workspace = integration.get("workspace")
                if not isinstance(workspace, dict):
                    raise HarnessError("validator requires final workspace")
                validator["workspace"] = copy.deepcopy(workspace)
                bindings = _adapter_call(adapter, "verify_tool_bindings", validator, packet, workspace)
                _record_tool_binding_evidence(attempt, validator, packet, workspace, bindings)
                handle = _adapter_call(adapter, "dispatch_lane", validator, packet, workspace, _delegation_bridge(root, run, attempt, validator))
                validator["status"] = "running"
                active_handles.append((validator, handle))
                evidence = _adapter_call(adapter, "collect_lane_evidence", handle, validator, packet, workspace)
                _record_lane_execution_evidence(attempt, validator, packet, workspace, evidence)
                claim = _adapter_call(adapter, "collect_claim", handle)
                if packet["version"] == CURRENT_PACKET_API:
                    _record_v7_lane_claim(
                        root,
                        run,
                        attempt,
                        adapter,
                        capabilities,
                        validator,
                        packet,
                        workspace,
                        handle,
                        evidence,
                        claim,
                    )
                else:
                    _record_lane_claim(root, run, attempt, validator, claim, packet_version=packet["version"])
                validator["status"] = "succeeded"
                pending.pop(validator["lane_id"])
                active_handles.remove((validator, handle))
                continue

            check_node = next((lane for lane in ready if lane["kind"] == "check"), None)
            if check_node is None:
                raise HarnessError("lane scheduler found unsupported lane kind")
            failure_phase = "check"
            integration = next(lane for lane in attempt["nodes"] if lane["lane_id"] == "integrate")
            workspace = integration.get("workspace")
            if not isinstance(workspace, dict):
                raise HarnessError("check requires final workspace")
            host_checks: dict[str, Any] = {}
            if not run_check and packet["checks"]:
                host_checks = _adapter_call(adapter, "run_checks", packet, workspace)
                if not isinstance(host_checks, dict):
                    raise HarnessError("host adapter checks must be a mapping")
            checks: list[dict[str, Any]] = []
            for name, command in packet["checks"].items():
                if run_check:
                    code, stdout, stderr = run_check(command)
                    checks.append({"name": name, "command": command, "exit_code": code, "stdout": stdout[:1000], "stderr": stderr[:1000]})
                    continue
                check = host_checks.get(name)
                if (
                    not isinstance(check, dict)
                    or check.get("command") != command
                    or check.get("workspace_root") != workspace.get("path")
                    or check.get("tool") != "shell"
                    or check.get("binding_verified") is not True
                    or check.get("runtime_provider") != packet["runtime_provider"]
                    or not isinstance(check.get("exit_code"), int)
                    or not isinstance(check.get("stdout"), str)
                    or not isinstance(check.get("stderr"), str)
                ):
                    raise HarnessError(f"host adapter check `{name}` lacks packet workspace evidence")
                _validate_app_server_model_selection(packet, check.get("app_server_model_selection"))
                if packet.get("version") == CURRENT_PACKET_API:
                    _record_host_terminal_observation(attempt, packet, check)
                checks.append({"name": name, **check})
            check_node["workspace"] = copy.deepcopy(workspace)
            check_node["status"] = "succeeded"
            _record_node_observation(attempt, check_node, {"workspace": workspace, "checks": checks})
            pending.pop(check_node["lane_id"])
    except ClaimError as exc:
        _cancel_active_lanes(root, run, attempt, adapter, active_handles, phase="claim")
        if packet.get("version") == CURRENT_PACKET_API and _has_terminal_host_failure(attempt):
            return _terminalize_collected_attempt(root, run, attempt)
        if packet.get("version") == CURRENT_PACKET_API and _has_completed_host_observations(attempt):
            return _record_core_failure_and_terminalize(
                root,
                run,
                policy,
                attempt,
                "claim_invalid",
                str(exc),
                phase="claim",
            )
        return _record_failure(root, run, policy, attempt, "claim_invalid", str(exc), phase="claim")
    except Exception as exc:
        recovery_evidence = getattr(exc, "recovery_evidence", None)
        if isinstance(recovery_evidence, dict):
            _normalize_recovery_evidence(run["run_id"], attempt["attempt_id"], recovery_evidence)
            raise
        _cancel_active_lanes(root, run, attempt, adapter, active_handles, phase=failure_phase)
        if packet.get("version") == CURRENT_PACKET_API and _has_terminal_host_failure(attempt):
            return _terminalize_collected_attempt(root, run, attempt)
        if packet.get("version") == CURRENT_PACKET_API and _has_completed_host_observations(attempt):
            return _record_core_failure_and_terminalize(
                root,
                run,
                policy,
                attempt,
                "dispatch_failed",
                str(exc),
                phase=failure_phase,
            )
        return _record_dispatch_exception(root, run, policy, attempt, exc, phase=failure_phase)
    _transition(run, policy["states"], "observed", "claim_collected")
    _transition(run, policy["states"], "verifying", "verify")
    try:
        verification = _verify_managed(
            root,
            packet,
            attempt,
            collect_changes=collect_changes,
            now=now,
        )
    except Exception as exc:
        terminal_evidence = _normalize_terminal_evidence(exc, packet)
        if terminal_evidence is not None:
            return _record_terminal_failure(
                root,
                run,
                policy,
                attempt,
                str(exc),
                phase="check",
                terminal_evidence=terminal_evidence,
            )
        if packet.get("version") == CURRENT_PACKET_API and _has_completed_host_observations(attempt):
            return _record_core_failure_and_terminalize(
                root,
                run,
                policy,
                attempt,
                "verification_failed",
                str(exc),
                phase="check",
            )
        return _record_failure(root, run, policy, attempt, "verification_failed", str(exc), phase="check")
    attempt.setdefault("evidence", {}).update(verification)
    _record_verification_frictions(root, run, attempt, verification)
    if packet.get("version") == CURRENT_PACKET_API:
        return _terminalize_collected_attempt(root, run, attempt)
    reason, decisions = _outcome_for_verification(verification, packet["retry_policy"])
    _set_outcome(run, attempt, policy, reason, decisions, ["evidence"])
    return _persist_outcome_transition(root, run, attempt, policy, reason)


def run_managed(
    root: Path,
    request: dict[str, Any] | None,
    adapter: Any,
    *,
    run_id: str | None = None,
    run_check: CheckRunner | None = None,
    collect_changes: ChangeCollector | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    policy = _load_policy(root)
    _validate_policy(root)
    preflight_binding: dict[str, Any] | None = None
    host_instance_id: str | None = None
    if run_id is None:
        if request is None:
            raise HarnessError("managed run request is required")
        run_id = _safe_run_id(request.get("run_id") or uuid.uuid4().hex)
        if _run_path(root, run_id).exists():
            raise HarnessError(f"run `{run_id}` already exists")
        core_identity = admit_managed_operation(root, adapter, request_api=request.get("version"))
        preflight_binding = _provider_runtime_binding(adapter, required=core_identity["packet_api"] == CURRENT_PACKET_API)
        if core_identity["packet_api"] == CURRENT_PACKET_API:
            if preflight_binding is None:
                raise HarnessError("provider preflight evidence is required")
            host_instance_id = _host_instance_id(preflight_binding)
        packet = resolve_managed_packet(
            root,
            request,
            attempt_id="attempt-1",
            core_identity=core_identity,
            provider_runtime_binding=preflight_binding,
        )
        _admit_coordinated_packet(root, packet)
        run = _new_run(request, run_id)
        _transition(run, policy["states"], "planned", "preflight")
        _append_attempt(run, packet)
        _write_run(root, run)
    else:
        run_id = _safe_run_id(run_id)
        run = _load_run(root, run_id)
        if request is not None and request != run["request"]:
            raise HarnessError("managed continuation request does not match run record")
        if run["state"] != "planned":
            raise HarnessError(f"run `{run_id}` is not ready to execute")
        attempt = _active_attempt(run)
        packet = attempt["packet"]
        packet_identity = packet.get("core_identity")
        if not isinstance(packet_identity, dict) or not can_read_packet_api(packet_identity.get("packet_api")):
            raise HarnessError("harness_core_packet_api_unreadable")
        packet_api = packet_identity.get("packet_api")
        runtime_provider = packet.get("runtime_provider")
        if packet.get("version") != packet_api or not isinstance(runtime_provider, dict):
            raise HarnessError("harness_core_packet_api_unreadable")
        host_admission = admit_host_api(_adapter_host_api(adapter))
        if not host_admission["ok"]:
            raise HarnessError(host_admission["code"])
        dispatch_admission = admit_packet_dispatch(
            host_admission["host_api"],
            packet_api,
            runtime_provider.get("contract_version"),
        )
        if not dispatch_admission["ok"]:
            raise HarnessError(dispatch_admission["code"])
        if packet_api == CURRENT_PACKET_API:
            preflight_binding = _provider_runtime_binding(adapter, required=True)
            if preflight_binding is None:
                raise HarnessError("provider preflight evidence is required")
            host_instance_id = _host_instance_id(preflight_binding)
            if _validate_provider_runtime_binding(
                preflight_binding,
                runtime_provider,
                packet_api=packet_api,
                host_api=host_admission["host_api"],
            ) != _validate_provider_runtime_binding(
                packet.get("provider_runtime_binding"),
                runtime_provider,
                packet_api=packet_api,
                host_api=host_admission["host_api"],
            ):
                raise HarnessError("provider runtime binding changed")
        if "plan_ref" in packet:
            try:
                plan_ref = _required_string(packet.get("plan_ref"), "packet plan_ref")
                plan_task_id = _required_string(packet.get("plan_task_id"), "packet plan_task_id")
                plan_digest = _required_string(packet.get("plan_digest"), "packet plan_digest")
                coordination = load_plan_coordination(root, plan_ref, require_active=True)
                if coordination is None or coordination.task(plan_task_id).task_id != plan_task_id:
                    raise HarnessError("coordinated packet no longer resolves to its plan task")
                if plan_digest != coordination.digest:
                    raise HarnessError("coordinated packet plan digest changed")
                if packet["base_commit"] != _resolve_commit(root, coordination.base_ref):
                    raise HarnessError("coordinated packet base commit changed")
            except (PlanCoordinationError, HarnessError):
                _set_outcome(run, attempt, policy, "plan_binding_changed", ["retry", "block"], ["packet"])
                return _persist_outcome_transition(root, run, attempt, policy, "plan_binding_changed")
    if packet.get("provider_runtime_binding") is not None:
        _active_attempt(run)["host_preflight"] = copy.deepcopy(preflight_binding or packet["provider_runtime_binding"])
    _write_run(root, run)
    collector = collect_changes or _collect_changes
    return _execute_attempt(
        root,
        run,
        policy,
        adapter,
        run_check=run_check,
        collect_changes=collector,
        host_instance_id=host_instance_id,
        now=now or datetime.now(UTC),
    )


def _successor_request(run: dict[str, Any], successor: Any) -> dict[str, Any]:
    request = copy.deepcopy(run["request"])
    if "plan_ref" in _active_attempt(run)["packet"]:
        for field in ("execution_mode", "base_ref", "allowed_paths", "planned_write_paths"):
            request.pop(field, None)
    if successor is None:
        return request
    if not isinstance(successor, dict):
        raise HarnessError("decision successor must be an object")
    allowed = {"execution_mode", "runtime_provider_id", "user_request", "allowed_paths", "planned_write_paths", "acceptance_criteria", "base_ref", "approvals", "review_evidence", "manual_evidence", "lanes", "plan_ref", "plan_task_id"}
    unknown = set(successor) - allowed
    if unknown:
        raise HarnessError(f"decision successor has unsupported fields: {', '.join(sorted(unknown))}")
    request.update(copy.deepcopy(successor))
    request["run_id"] = run["run_id"]
    return request


def apply_controller_decision(root: Path, run_id: str, decision: dict[str, Any]) -> dict[str, Any]:
    _validate_policy(root)
    if not isinstance(decision, dict):
        raise HarnessError("decision must be an object")
    kind = _required_string(decision.get("kind"), "decision kind")
    if kind not in DECISION_KINDS:
        raise HarnessError(f"unsupported decision kind `{kind}`")
    if kind in _TERMINAL_DECISIONS:
        if set(decision) != {"kind", "controller_authorization"}:
            raise HarnessError("terminal decision requires only controller_authorization")
        run = _load_run(root, _safe_run_id(run_id))
        attempt = _active_attempt(run)
        outcome = _validated_outcome(attempt)
        terminalize_attempt(
            root,
            run_id,
            {
                "attempt_id": attempt["attempt_id"],
                "outcome_id": outcome["outcome_id"],
                "outcome_digest": outcome["outcome_digest"],
                "requested_decision": kind,
                "controller_authorization": decision["controller_authorization"],
            },
        )
        return _managed_result(_load_run(root, _safe_run_id(run_id)))
    policy = _load_policy(root)
    run = _load_run(root, _safe_run_id(run_id))
    if run["state"] != "awaiting_decision":
        raise HarnessError(f"run `{run_id}` is not awaiting controller decision")
    attempt = _active_attempt(run)
    outcome = attempt.get("outcome")
    if not isinstance(outcome, dict) or kind not in outcome.get("allowed_decisions", []):
        raise HarnessError(f"decision `{kind}` is not allowed for current outcome")
    terminal_record = attempt.get("terminal_record")
    if isinstance(terminal_record, dict) and terminal_record.get("classification") == "legacy_cleanup_attested" and kind != "block":
        raise HarnessError("legacy cleanup outcome requires block")
    stored = copy.deepcopy(decision)
    stored["at"] = _timestamp()
    attempt["decision"] = stored
    attempt.setdefault("decision_history", []).append(stored)
    if kind == "request_approval":
        _transition(run, policy["states"], "awaiting_decision", "controller_request_approval")
    else:
        retry_policy = attempt["packet"]["retry_policy"]
        execution_budget_profile = None
        provider_runtime_binding = None
        if attempt["packet"].get("version") == CURRENT_PACKET_API:
            provider_runtime_binding = attempt["packet"].get("provider_runtime_binding")
            if not isinstance(provider_runtime_binding, dict):
                raise HarnessError("successor attempt lacks provider runtime binding")
        if outcome["reason"] == "dispatch_timeout":
            if kind != "escalate":
                raise HarnessError("timeout outcome requires escalation or block")
            profile_metadata = attempt["packet"].get("operating_profile")
            if isinstance(profile_metadata, dict):
                route = policy["routes"][attempt["packet"]["task_type"]]
                transition = next((item for item in route.get("escalation_transitions", []) if item["from"] == profile_metadata["resolved"] and item["on"] == "dispatch_timeout"), None)
                if not isinstance(transition, dict):
                    raise HarnessError("timeout outcome lacks operating profile transition")
                successor_request = _successor_request(run, decision.get("successor"))
                successor_request["operating_profile_selection"] = {"id": transition["to"], "reason": "dispatch_timeout"}
            else:
                execution_budget_profile = attempt["packet"]["execution_budget"].get("escalation_profile")
                if not isinstance(execution_budget_profile, str) or not execution_budget_profile:
                    raise HarnessError("timeout outcome lacks escalation budget profile")
                successor_request = _successor_request(run, decision.get("successor"))
        elif outcome["reason"] not in retry_policy["retryable_reasons"] and outcome["reason"] not in {"approval_required", "plan_binding_changed"}:
            raise HarnessError(f"outcome `{outcome['reason']}` is not retryable")
        else:
            successor_request = _successor_request(run, decision.get("successor"))
        if len(run["attempts"]) >= retry_policy["max_attempts"]:
            _set_outcome(run, attempt, policy, "retry_exhausted", ["block"], ["decision"])
            _auto_finalize_outcome(run, attempt, policy)
        else:
            packet = resolve_managed_packet(
                root,
                successor_request,
                attempt_id=f"attempt-{len(run['attempts']) + 1}",
                execution_budget_profile=execution_budget_profile,
                provider_runtime_binding=provider_runtime_binding,
            )
            _append_attempt(run, packet)
            _transition(run, policy["states"], "planned", f"controller_{kind}")
    _write_run(root, run)
    return _managed_result(run)


def sign_controller_authorization(
    root: Path,
    run_id: str,
    issuer_key_id: str,
    requested_decision: str,
    rationale_path: Path,
    private_key_path: Path,
    output_path: Path,
    *,
    expires_in_seconds: int | None = None,
) -> dict[str, str]:
    _validate_policy(root)
    root = root.resolve()
    private_key_path = private_key_path.resolve()
    output_path = output_path.resolve()
    if private_key_path.is_relative_to(root):
        raise HarnessError("controller authorization private key must be outside repository")
    if output_path.is_relative_to(root):
        raise HarnessError("controller authorization output must be outside repository")
    try:
        rationale = rationale_path.read_bytes()
    except OSError as exc:
        raise HarnessError("controller authorization rationale is unavailable") from exc
    with _run_lock(root, _safe_run_id(run_id)):
        policy = _load_policy(root)
        terminalization = policy["terminalization"]
        if not rationale or len(rationale) > terminalization["max_authorization_bytes"]:
            raise HarnessError("controller authorization rationale is invalid")
        if requested_decision not in _TERMINAL_DECISIONS:
            raise HarnessError("controller authorization decision is invalid")
        lifetime = terminalization["max_authorization_lifetime_seconds"] if expires_in_seconds is None else expires_in_seconds
        if not isinstance(lifetime, int) or isinstance(lifetime, bool) or lifetime <= 0 or lifetime > terminalization["max_authorization_lifetime_seconds"]:
            raise HarnessError("controller authorization expiry is invalid")
        run = _load_run(root, run_id)
        if run["state"] != "awaiting_decision":
            raise HarnessError(f"run `{run_id}` is not awaiting controller decision")
        attempt = _active_attempt(run)
        outcome = _validated_outcome(attempt)
        if requested_decision not in outcome["allowed_decisions"]:
            raise HarnessError("controller authorization decision is not allowed")
        now = datetime.now(UTC)
        if requested_decision in {"accept", "waive"} and now > _parse_timestamp(outcome["valid_until"]):
            raise HarnessError("outcome is expired for controller authorization")
        try:
            registry = authority.load_authorities()
            entry = registry["entries"].get(issuer_key_id)
            if not isinstance(entry, dict):
                raise authority.AuthorityError("controller authorization issuer is unknown")
            if entry.get("status") != "active":
                raise authority.AuthorityError("controller authorization issuer is revoked")
            if not set(entry.get("roles", [])) & set(terminalization["allowed_controller_roles"]):
                raise authority.AuthorityError("controller authorization issuer role is not allowed")
            private_key = authority.load_private_ed25519_key(private_key_path)
            key_proof = {"issuer_key_id": issuer_key_id}
            authority.verify_document(
                key_proof,
                authority.base64url_encode(private_key.sign(authority.canonical_json_bytes(key_proof))),
                entry["public_key"],
            )
        except authority.AuthorityError as exc:
            raise HarnessError(str(exc)) from exc
        expires_at = now + timedelta(seconds=lifetime)
        authorization = authority.sign_document(
            {
                "schema_id": "controller_authorization/v1",
                "authorization_id": f"authorization-{uuid.uuid4().hex}",
                "run_id": run_id,
                "attempt_id": attempt["attempt_id"],
                "packet_sha256": outcome["packet_sha256"],
                "outcome_id": outcome["outcome_id"],
                "outcome_digest": outcome["outcome_digest"],
                "requested_decision": requested_decision,
                "issuer_key_id": issuer_key_id,
                "issued_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "reason_sha256": hashlib.sha256(rationale).hexdigest(),
                "reason_length": len(rationale),
            },
            private_key,
        )
        try:
            normalized = authority.normalize_controller_authorization(
                authorization,
                registry=registry,
                policy=terminalization,
                now=now,
            )
        except authority.AuthorityError as exc:
            raise HarnessError(str(exc)) from exc
    if output_path.exists():
        raise HarnessError("controller authorization output already exists")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(authorization, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    except OSError as exc:
        raise HarnessError("controller authorization output is unavailable") from exc
    return {
        "authorization_id": normalized["authorization_id"],
        "authorization_digest": normalized["authorization_digest"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve, run, and verify harness tasks.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1])
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "verify"):
        command = subparsers.add_parser(name)
        command.add_argument("--task", required=True)
        if name == "verify":
            command.add_argument("--claim", required=True)
    run_command = subparsers.add_parser("run-unavailable")
    run_command.add_argument("--task")
    run_command.add_argument("--run-id")
    decision_command = subparsers.add_parser("decision")
    decision_command.add_argument("--run-id", required=True)
    decision_command.add_argument("--decision", required=True)
    coordination_status_command = subparsers.add_parser("coordination-status")
    coordination_status_command.add_argument("--plan", required=True)
    handoff_command = subparsers.add_parser("handoff")
    handoff_command.add_argument("--run-id", required=True)
    handoff_command.add_argument("--handoff", required=True)
    subparsers.add_parser("friction-report")
    friction_resolve_command = subparsers.add_parser("friction-resolve")
    friction_resolve_command.add_argument("--run-id", required=True)
    friction_resolve_command.add_argument("--fingerprint", required=True)
    friction_resolve_command.add_argument("--decision", required=True, choices=sorted(FRICTION_RESOLUTIONS))
    recover_command = subparsers.add_parser("recover-stranded")
    recover_command.add_argument("--run-id", required=True)
    recover_command.add_argument("--attempt-id", required=True)
    recover_command.add_argument("--reason", required=True)
    recover_command.add_argument("--evidence", required=True)
    terminalize_command = subparsers.add_parser("terminalize-attempt")
    terminalize_command.add_argument("--run-id", required=True)
    terminalize_input = terminalize_command.add_mutually_exclusive_group(required=True)
    terminalize_input.add_argument("--input")
    terminalize_input.add_argument("--evidence")
    terminalize_command.add_argument("--auto-block", action="store_true")
    sign_cleanup_command = subparsers.add_parser("sign-legacy-cleanup")
    sign_cleanup_command.add_argument("--attestation", required=True)
    sign_cleanup_command.add_argument("--private-key-file", required=True)
    sign_cleanup_command.add_argument("--output", required=True)
    sign_authorization_command = subparsers.add_parser("sign-controller-authorization")
    sign_authorization_command.add_argument("--run-id", required=True)
    sign_authorization_command.add_argument("--issuer-key-id", required=True)
    sign_authorization_command.add_argument("--decision", required=True, choices=sorted(_TERMINAL_DECISIONS))
    sign_authorization_command.add_argument("--rationale-file", required=True)
    sign_authorization_command.add_argument("--private-key-file", required=True)
    sign_authorization_command.add_argument("--output", required=True)
    sign_authorization_command.add_argument("--expires-in-seconds", type=int)
    migrate_authorities_command = subparsers.add_parser("migrate-harness-authorities")
    migrate_authorities_command.add_argument("--source")
    migrate_authorities_command.add_argument("--target")
    migrate_authorities_command.add_argument("--dry-run", action="store_true")
    migrate_authorities_command.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = Path(args.repo_root).resolve()
        if args.command == "preflight":
            result = resolve_task(root, _load_json(Path(args.task)))
        elif args.command == "verify":
            result = verify_task(root, _load_json(Path(args.task)), _load_json(Path(args.claim)))
        elif args.command == "run-unavailable":
            if not args.task and not args.run_id:
                raise HarnessError("run-unavailable requires --task or --run-id")
            task = _load_json(Path(args.task)) if args.task else None
            result = run_managed(
                root,
                task,
                {
                    "host_api": 7,
                    "identity": lambda: {"provider_id": "codex_app_server", "contract_version": 7},
                    "preflight_evidence": lambda: {
                        "provider_id": "codex_app_server",
                        "host_api": 7,
                        "contract_version": 7,
                        "transport": "stdio",
                        "lifecycle": "host_spawn",
                        "protocol": "app-server-v1",
                        "configuration_digest": "0" * 64,
                        "readiness": "ready",
                        "host_instance_id": "generic-cli",
                    },
                    "capabilities": lambda: {},
                    "unavailable_detail": "Generic harness CLI has no injected host adapter; use a provider host entrypoint.",
                },
                run_id=args.run_id,
            )
        elif args.command == "friction-report":
            result = friction_report(root)
        elif args.command == "friction-resolve":
            result = resolve_friction(root, args.run_id, args.fingerprint, args.decision)
        elif args.command == "recover-stranded":
            result = recover_stranded_run(root, args.run_id, args.attempt_id, args.reason, _load_json(Path(args.evidence)))
        elif args.command == "terminalize-attempt":
            if args.auto_block:
                raise HarnessError("terminalize-attempt --auto-block is retired")
            if args.input:
                terminal_evidence = _load_json(Path(args.input))
            else:
                legacy_evidence = _load_json(Path(args.evidence))
                if not isinstance(legacy_evidence, dict) or legacy_evidence.get("schema_id") != "legacy_cleanup_attestation/v1":
                    raise HarnessError("terminalize-attempt --evidence accepts only legacy cleanup evidence")
                legacy_run = _load_run(root, _safe_run_id(args.run_id))
                legacy_attempt = _active_attempt(legacy_run)
                if legacy_attempt.get("packet", {}).get("version") != CURRENT_PACKET_API:
                    raise HarnessError("terminalize-attempt --evidence requires packet API 8")
                terminal_evidence = {
                    "attempt_id": legacy_evidence.get("attempt_id"),
                    "legacy_cleanup_attestation": legacy_evidence,
                }
            result = terminalize_attempt(root, args.run_id, terminal_evidence)
        elif args.command == "sign-legacy-cleanup":
            private_key_path = Path(args.private_key_file).resolve()
            if private_key_path.is_relative_to(root):
                raise HarnessError("legacy cleanup private key must be outside repository")
            output_path = Path(args.output).resolve()
            if output_path.name == "run.json" or output_path.is_relative_to(root / ".harness" / "runs"):
                raise HarnessError("legacy cleanup signer cannot write run.json")
            signed = sign_legacy_cleanup_attestation(_load_json(Path(args.attestation)), private_key_path)
            cleanup_policy = _load_policy(root).get("legacy_cleanup")
            if not isinstance(cleanup_policy, dict):
                raise HarnessError("legacy cleanup is not configured")
            try:
                normalize_legacy_cleanup_attestation(signed, cleanup_policy, now=datetime.now(UTC))
            except LegacyCleanupError as exc:
                raise HarnessError(str(exc)) from exc
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(signed, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            result = {"signed_evidence_sha256": legacy_cleanup_evidence_digest(signed)}
        elif args.command == "sign-controller-authorization":
            result = sign_controller_authorization(
                root,
                args.run_id,
                args.issuer_key_id,
                args.decision,
                Path(args.rationale_file),
                Path(args.private_key_file),
                Path(args.output),
                expires_in_seconds=args.expires_in_seconds,
            )
        elif args.command == "migrate-harness-authorities":
            try:
                result = authority.migrate_legacy_attesters(
                    Path(args.source) if args.source else None,
                    Path(args.target) if args.target else None,
                    dry_run=args.dry_run,
                    overwrite=args.overwrite,
                )
            except authority.AuthorityError as exc:
                raise HarnessError(str(exc)) from exc
        elif args.command == "coordination-status":
            result = coordination_status(root, args.plan)
        elif args.command == "handoff":
            try:
                handoff = json.loads(args.handoff)
            except json.JSONDecodeError as exc:
                raise HarnessError("handoff must be JSON") from exc
            result = record_controller_handoff(root, args.run_id, handoff)
        else:
            result = apply_controller_decision(root, args.run_id, _load_json(Path(args.decision)))
    except HarnessError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if args.command in {"preflight", "friction-report", "friction-resolve", "coordination-status", "handoff", "recover-stranded", "terminalize-attempt", "sign-legacy-cleanup", "sign-controller-authorization", "migrate-harness-authorities"} or result.get("status") == "verified" or result.get("state") == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
