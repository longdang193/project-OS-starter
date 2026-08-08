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
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
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
from .compatibility import (
    CURRENT_PACKET_API,
    CURRENT_RUN_API,
    admit_host_api,
    admit_packet_dispatch,
    admit_request_api,
    can_read_packet_api,
    legacy_role_capabilities,
    runtime_identity,
)
from .terminal_observation import TerminalObservationError, normalize_terminal_observation
from .timeout_observation import TimeoutObservationError, normalize_timeout_observation
from .coordination import PlanCoordination, PlanCoordinationError, PlanTask, load_plan_coordination, path_matches as _path_matches


class HarnessError(ValueError):
    pass


class ClaimError(HarnessError):
    pass


class WorkspaceBaselineError(HarnessError):
    pass


CheckRunner = Callable[[list[str]], tuple[int, str, str]]
ChangeCollector = Callable[[Path, str], list[dict[str, str]]]

MANAGED_VERSION = CURRENT_PACKET_API
LEGACY_MANAGED_VERSION = 2
CAPABILITY_LEVELS = {"enforced", "advisory", "unavailable"}
CRITERION_KINDS = {"check", "change_set", "review", "manual", "validator"}
DECISION_KINDS = {"accept", "retry", "escalate", "request_approval", "waive", "block"}
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]+\Z")
FRICTION_EVENT_VERSION = 1
FRICTION_EVENT_KINDS = {"observed", "resolution"}
FRICTION_SOURCES = {"agent", "host", "validator", "check", "controller"}
FRICTION_PHASES = {"claim", "dispatch", "integration", "check", "validator", "decision"}
FRICTION_RESOLUTIONS = {"keep", "revise", "remove", "pending"}
DELEGATED_CHILD_TERMINAL_STATES = {"succeeded", "failed", "cancelled", "timed_out", "awaiting_decision"}
CORE_STATE_TRANSITIONS = {
    "classified": ["planned", "blocked"],
    "planned": ["running", "awaiting_decision", "blocked"],
    "running": ["observed", "awaiting_decision", "blocked"],
    "observed": ["verifying", "running", "blocked"],
    "verifying": ["awaiting_decision", "accepted", "blocked"],
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
    if request_api is None:
        request_api = core_policy.get("request_api") if isinstance(core_policy, dict) else None
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
    raw = policy.get("evidence_artifacts", {})
    if raw == {}:
        return {"writer_retained_kinds": []}
    if not isinstance(raw, dict):
        raise HarnessError("invalid evidence artifact policy")
    retained_kinds = raw.get("writer_retained_kinds")
    if (
        not isinstance(retained_kinds, list)
        or len(set(retained_kinds)) != len(retained_kinds)
        or not set(retained_kinds) <= READONLY_ARTIFACT_KINDS
    ):
        raise HarnessError("invalid evidence artifact policy")
    return {"writer_retained_kinds": list(retained_kinds)}


def _readonly_artifact_policy(route: dict[str, Any], artifact_max_bytes: int) -> dict[str, Any]:
    raw = route.get("readonly_artifacts", {})
    if not isinstance(raw, dict):
        raise HarnessError("invalid readonly artifact policy")
    allowed_kinds = raw.get("allowed_kinds", [])
    required_kinds = raw.get("required_kinds", [])
    if (
        not isinstance(allowed_kinds, list)
        or len(set(allowed_kinds)) != len(allowed_kinds)
        or not set(allowed_kinds) <= READONLY_ARTIFACT_KINDS
        or not isinstance(required_kinds, list)
        or len(set(required_kinds)) != len(required_kinds)
        or not set(required_kinds) <= set(allowed_kinds)
    ):
        raise HarnessError("invalid readonly artifact policy")
    return {
        "allowed_kinds": list(allowed_kinds),
        "required_kinds": list(required_kinds),
        "artifact_max_bytes": artifact_max_bytes,
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
        artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("kind") == kind), None)
        if isinstance(artifact, dict) and "content" in artifact:
            return artifact["content"]
    raise HarnessError(f"readonly artifact `{kind}` is unavailable")


def _resolve_readonly_artifacts(root: Path, packet: dict[str, Any], value: Any) -> list[dict[str, Any]]:
    policy = packet["readonly_artifact_policy"]
    if value is None:
        value = []
    if not isinstance(value, list):
        raise HarnessError("readonly_artifacts must be a list")
    if packet["workspace_write_access"] != "read_only" and value:
        raise HarnessError("readonly_artifacts require read-only packet access")
    resolved: list[dict[str, Any]] = []
    for raw in value:
        if not isinstance(raw, dict) or set(raw) != {"kind", "source_run_id", "source_attempt_id"}:
            raise HarnessError("readonly_artifact has invalid fields")
        kind = _required_string(raw.get("kind"), "readonly artifact kind")
        if kind not in policy["allowed_kinds"]:
            raise HarnessError(f"readonly artifact `{kind}` is not allowed by route")
        source_run_id = _safe_run_id(raw.get("source_run_id"))
        source_attempt_id = _required_string(raw.get("source_attempt_id"), "readonly artifact source_attempt_id")
        source_attempt = _source_attempt(_load_run(root, source_run_id), source_attempt_id)
        descriptor = _artifact_descriptor(
            kind,
            source_run_id,
            source_attempt_id,
            _stored_artifact_content(source_attempt, kind),
        )
        if descriptor["byte_length"] > policy["artifact_max_bytes"]:
            raise HarnessError("readonly artifact exceeds artifact_max_bytes")
        resolved.append(descriptor)
    if len({(item["kind"], item["source_run_id"], item["source_attempt_id"]) for item in resolved}) != len(resolved):
        raise HarnessError("readonly_artifacts must not contain duplicates")
    if not set(policy["required_kinds"]) <= {item["kind"] for item in resolved}:
        raise HarnessError("readonly_artifacts missing route-required kinds")
    return resolved


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


def _load_roles(root: Path) -> dict[str, dict[str, Any]]:
    with (root / "agents" / "roles.yaml").open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    roles = payload.get("roles") if isinstance(payload, dict) else None
    if not isinstance(roles, dict):
        raise HarnessError("roles must be a mapping")
    return roles


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
    budget = {
        "profile": selected,
        "turn_timeout_seconds": profile["turn_timeout_seconds"],
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
    readonly_artifact_policy = _readonly_artifact_policy(route, policy["context_limits"]["artifact_max_bytes"])
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
        "readonly_artifact_policy": readonly_artifact_policy,
        "orchestration": {
            "name": execution_mode,
            "work_scheduling": orchestration["work_scheduling"],
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


def _write_run(root: Path, run: dict[str, Any]) -> None:
    target = _run_path(root, run["run_id"])
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def _load_run(root: Path, run_id: str) -> dict[str, Any]:
    run = _load_json(_run_path(root, run_id))
    if run.get("version") not in {1, CURRENT_RUN_API} or run.get("run_id") != run_id or not isinstance(run.get("attempts"), list):
        raise HarnessError(f"invalid run record `{run_id}`")
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


ACTIVE_RUN_STATES = {"planned", "running", "observed", "verifying", "awaiting_decision"}
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
    route: dict[str, Any],
) -> list[dict[str, str]]:
    policy = _readonly_artifact_policy(route, _load_policy(root)["context_limits"]["artifact_max_bytes"])
    if not policy["allowed_kinds"]:
        return []
    requests: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for event in sorted(observed, key=lambda item: (item["occurred_at"], item["event_id"]), reverse=True):
        try:
            source_run_id = _safe_run_id(event["run_id"])
            source_attempt_id = _required_string(event["attempt_id"], "friction source attempt_id")
            source_attempt = _source_attempt(_load_run(root, source_run_id), source_attempt_id)
        except HarnessError:
            continue
        for kind in policy["allowed_kinds"]:
            key = (kind, source_run_id, source_attempt_id)
            if key in seen:
                continue
            try:
                _stored_artifact_content(source_attempt, kind)
            except HarnessError:
                continue
            requests.append({"kind": kind, "source_run_id": source_run_id, "source_attempt_id": source_attempt_id})
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
            readonly_artifacts = _friction_readonly_artifact_requests(root, observed, route)
            readonly_policy = _readonly_artifact_policy(route, route_policy["context_limits"]["artifact_max_bytes"])
            if set(readonly_policy["required_kinds"]) <= {item["kind"] for item in readonly_artifacts}:
                candidate["follow_up"] = {
                    "task_type": task_type,
                    "execution_mode": "single_work_lane",
                    "workspace_write_access": authority["workspace_write_access"],
                    "readonly_artifacts": readonly_artifacts,
                }
            else:
                candidate["follow_up_blocked"] = "missing_required_readonly_artifacts"
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
    roles = _load_roles(root)
    role_writes = lambda role: "repo.write" in (
        packet["capabilities"] if packet["version"] != 3 else legacy_role_capabilities(role)
    )
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
            "claim_schema": {
                "required_fields": copy.deepcopy(roles[role]["required_fields"]),
                "field_constraints": copy.deepcopy(roles[role].get("field_constraints", {})),
            },
            "claim_schema": {
                "required_fields": copy.deepcopy(roles[role]["required_fields"]),
                "field_constraints": copy.deepcopy(roles[role].get("field_constraints", {})),
            },
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
                "claim_schema": {
                    "required_fields": copy.deepcopy(roles[role]["required_fields"]),
                    "field_constraints": copy.deepcopy(roles[role].get("field_constraints", {})),
                },
                "claim_schema": {
                    "required_fields": copy.deepcopy(roles[role]["required_fields"]),
                    "field_constraints": copy.deepcopy(roles[role].get("field_constraints", {})),
                },
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
            "claim_schema": {
                "required_fields": copy.deepcopy(validator["required_fields"]),
                "field_constraints": copy.deepcopy(validator.get("field_constraints", {})),
            },
            "claim_schema": {
                "required_fields": copy.deepcopy(validator["required_fields"]),
                "field_constraints": copy.deepcopy(validator.get("field_constraints", {})),
            },
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
    if provider_runtime_binding is not None:
        packet["provider_runtime_binding"] = provider_runtime_binding
    packet["readonly_artifacts"] = _resolve_readonly_artifacts(root, packet, request.get("readonly_artifacts"))
    if coordination is not None and plan_task is not None:
        packet.update({
            "plan_ref": coordination.plan_ref,
            "plan_task_id": plan_task.task_id,
            "plan_digest": coordination.digest,
        })
    packet["lanes"] = _normalize_lanes(root, packet, allowed_paths, request.get("lanes"))
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
        "friction_event_ids": [],
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
        "complete": lambda child_id, status, claim: complete_delegated_child(root, run["run_id"], child_id, status, claim),
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
    attempt["outcome"] = copy.deepcopy(persisted_attempt["outcome"])
    return True


def complete_delegated_child(
    root: Path,
    run_id: str,
    child_invocation_id: str,
    status: str,
    claim: dict[str, Any] | None,
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
    if status == "succeeded" and child_packet.get("verification") == "schema":
        try:
            role = _load_roles(root).get(child_packet.get("role"))
            if not isinstance(role, dict) or claim is None:
                raise HarnessError("delegated child claim is required")
            claim = _validate_managed_claim(claim, role)
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
        _set_outcome(attempt, f"child_{status}", ["block"], ["children", "reservation_ledger"])
        _transition(run, _load_policy(root)["states"], "awaiting_decision", f"child_{status}")
    _write_run(root, run)
    return result


def _set_outcome(
    attempt: dict[str, Any],
    reason: str,
    allowed_decisions: list[str],
    evidence_refs: list[str],
    *,
    detail: str | None = None,
) -> dict[str, Any]:
    outcome = {"reason": reason, "allowed_decisions": allowed_decisions, "evidence_refs": evidence_refs}
    if detail:
        outcome["detail"] = detail
    attempt["outcome"] = outcome
    return outcome


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
    for mode, level in capabilities.items():
        if not isinstance(mode, str) or mode not in canonical_modes or level not in CAPABILITY_LEVELS:
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
    if not isinstance(evidence, dict) or set(evidence) != required_fields:
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
    if binding.get("provider_id") != runtime_provider["provider_id"] or binding.get("contract_version") != runtime_provider["contract_version"]:
        raise HarnessError("provider runtime binding conflicts with packet runtime provider")
    if host_api is not None and binding.get("host_api") != host_api:
        raise HarnessError("provider runtime binding conflicts with host API")
    dispatch = admit_packet_dispatch(binding.get("host_api"), packet_api, binding.get("contract_version"))
    if not dispatch["ok"]:
        raise HarnessError(dispatch["code"])
    return copy.deepcopy(binding)


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


def _validate_managed_claim(claim: Any, role: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(claim, dict) or claim.get("kind") != role["result_kind"]:
        raise HarnessError("managed claim has invalid result kind")
    for field in role["required_fields"]:
        value = claim.get(field)
        if field in {"changed_files", "findings"}:
            _string_list(value, f"managed claim {field}")
        elif not isinstance(value, str) or not value:
            raise HarnessError(f"managed claim missing required field `{field}`")
    for field, allowed_values in role.get("field_constraints", {}).items():
        if claim.get(field) not in allowed_values:
            raise HarnessError(f"managed claim field `{field}` has unsupported value")
    frictions = claim.get("frictions", [])
    if not isinstance(frictions, list):
        raise HarnessError("managed claim frictions must be a list")
    for friction in frictions:
        if not isinstance(friction, dict) or not isinstance(friction.get("category"), str) or not friction["category"]:
            raise HarnessError("managed claim friction must have category")
    return copy.deepcopy(claim)


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
        role = _load_roles(root)[validator_lane["role"]]
        claim = _validate_managed_claim(validator_claim, role)
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
    _set_outcome(attempt, reason, decisions, ["friction_event_ids", "evidence.failure"], detail=detail)
    _transition(run, policy["states"], "awaiting_decision", reason)
    _write_run(root, run)
    return _managed_result(run)


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
                    or len(command["command"].encode("utf-8")) > limits[kind]
                    or len(command["output"].encode("utf-8")) > limits[kind]
                    or (command["exit_code"] is not None and (not isinstance(command["exit_code"], int) or isinstance(command["exit_code"], bool)))
                ):
                    raise HarnessError("sanitized command trace command is invalid")
        if len(_artifact_content_bytes(content)) > limits[kind]:
            raise HarnessError("sanitized command trace exceeds artifact_max_bytes")
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
        attempt,
        reason,
        decisions,
        evidence_refs,
        detail=detail,
    )
    _transition(run, policy["states"], "awaiting_decision", reason)
    _write_run(root, run)
    return _managed_result(run)


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
    for lane, handle in active_handles:
        try:
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


def _record_lane_claim(root: Path, run: dict[str, Any], attempt: dict[str, Any], lane: dict[str, Any], claim: Any) -> None:
    try:
        role_name = lane.get("role")
        if not isinstance(role_name, str):
            raise HarnessError(f"lane `{lane['lane_id']}` cannot collect an agent claim")
        role = _load_roles(root).get(role_name)
        if not isinstance(role, dict):
            raise HarnessError(f"lane `{lane['lane_id']}` has unknown role `{role_name}`")
        normalized_claim = _validate_managed_claim(claim, role)
        if normalized_claim["kind"] != lane["required_claim_kind"]:
            raise HarnessError(f"lane `{lane['lane_id']}` claim kind conflicts with packet")
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
        _set_outcome(attempt, "approval_required", ["request_approval", "retry", "block"], ["authorization"])
        _transition(run, policy["states"], "awaiting_decision", "approval_required")
        _write_run(root, run)
        return _managed_result(run)
    try:
        capabilities = _adapter_capabilities(adapter, set(policy["orchestration"]))
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
            attempt,
            "execution_mode_unavailable",
            ["waive", "block"],
            ["capabilities"],
            detail=detail,
        )
        _transition(run, policy["states"], "awaiting_decision", "execution_mode_unavailable")
        _write_run(root, run)
        return _managed_result(run)
    try:
        attempt["adapter_identity"] = _adapter_identity(adapter, packet["runtime_provider"])
    except Exception as exc:
        return _record_failure(root, run, policy, attempt, "dispatch_failed", str(exc), phase="dispatch")

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
                writer_slots = packet["orchestration"]["max_parallel_writers"]
                scheduled: list[dict[str, Any]] = []
                for lane in work_lanes:
                    if lane["write_capable"]:
                        if not writer_slots:
                            continue
                        writer_slots -= 1
                    scheduled.append(lane)
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
                    active_handles.append((lane, handle))
                for lane, handle in active_handles[:]:
                    claim = _adapter_call(adapter, "collect_claim", handle)
                    if _sync_delegation_state(root, run, attempt):
                        _cancel_active_lanes(root, run, attempt, adapter, active_handles, phase="delegation")
                        _write_run(root, run)
                        return _managed_result(run)
                    _record_lane_claim(root, run, attempt, lane, claim)
                    evidence = _adapter_call(adapter, "collect_lane_evidence", handle, lane, packet, lane["workspace"])
                    _record_lane_execution_evidence(attempt, lane, packet, lane["workspace"], evidence)
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
                active_handles.append((validator, handle))
                claim = _adapter_call(adapter, "collect_claim", handle)
                _record_lane_claim(root, run, attempt, validator, claim)
                evidence = _adapter_call(adapter, "collect_lane_evidence", handle, validator, packet, workspace)
                _record_lane_execution_evidence(attempt, validator, packet, workspace, evidence)
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
            if not run_check:
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
                checks.append({"name": name, **check})
            check_node["workspace"] = copy.deepcopy(workspace)
            check_node["status"] = "succeeded"
            _record_node_observation(attempt, check_node, {"workspace": workspace, "checks": checks})
            pending.pop(check_node["lane_id"])
    except ClaimError as exc:
        _cancel_active_lanes(root, run, attempt, adapter, active_handles, phase="claim")
        return _record_failure(root, run, policy, attempt, "claim_invalid", str(exc), phase="claim")
    except Exception as exc:
        _cancel_active_lanes(root, run, attempt, adapter, active_handles, phase=failure_phase)
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
        return _record_failure(root, run, policy, attempt, "verification_failed", str(exc), phase="check")
    attempt["evidence"] = verification
    _record_verification_frictions(root, run, attempt, verification)
    reason, decisions = _outcome_for_verification(verification, packet["retry_policy"])
    _set_outcome(attempt, reason, decisions, ["evidence"])
    _transition(run, policy["states"], "awaiting_decision", reason)
    _write_run(root, run)
    return _managed_result(run)


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
    if run_id is None:
        if request is None:
            raise HarnessError("managed run request is required")
        run_id = _safe_run_id(request.get("run_id") or uuid.uuid4().hex)
        if _run_path(root, run_id).exists():
            raise HarnessError(f"run `{run_id}` already exists")
        core_identity = admit_managed_operation(root, adapter, request_api=request.get("version"))
        binding = _provider_runtime_binding(adapter, required=core_identity["packet_api"] == CURRENT_PACKET_API)
        packet = resolve_managed_packet(
            root,
            request,
            attempt_id="attempt-1",
            core_identity=core_identity,
            provider_runtime_binding=binding,
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
            binding = _provider_runtime_binding(adapter, required=True)
            if _validate_provider_runtime_binding(
                binding,
                runtime_provider,
                packet_api=packet_api,
                host_api=host_admission["host_api"],
            ) != packet.get("provider_runtime_binding"):
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
                _set_outcome(attempt, "plan_binding_changed", ["retry", "block"], ["packet"])
                _transition(run, policy["states"], "awaiting_decision", "plan_binding_changed")
                _write_run(root, run)
                return _managed_result(run)
    if packet.get("provider_runtime_binding") is not None:
        _active_attempt(run)["host_preflight"] = copy.deepcopy(packet["provider_runtime_binding"])
    _write_run(root, run)
    collector = collect_changes or _collect_changes
    return _execute_attempt(root, run, policy, adapter, run_check=run_check, collect_changes=collector, now=now or datetime.now(UTC))


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
    policy = _load_policy(root)
    run = _load_run(root, _safe_run_id(run_id))
    if run["state"] != "awaiting_decision":
        raise HarnessError(f"run `{run_id}` is not awaiting controller decision")
    kind = _required_string(decision.get("kind"), "decision kind")
    if kind not in DECISION_KINDS:
        raise HarnessError(f"unsupported decision kind `{kind}`")
    attempt = _active_attempt(run)
    outcome = attempt.get("outcome")
    if not isinstance(outcome, dict) or kind not in outcome.get("allowed_decisions", []):
        raise HarnessError(f"decision `{kind}` is not allowed for current outcome")
    stored = copy.deepcopy(decision)
    stored["at"] = _timestamp()
    attempt["decision"] = stored
    attempt.setdefault("decision_history", []).append(stored)
    if kind == "accept":
        criteria = attempt.get("evidence", {}).get("criteria", [])
        if not criteria or any(criterion.get("status") != "proven" for criterion in criteria):
            raise HarnessError("cannot accept run without proven criteria")
        _transition(run, policy["states"], "accepted", "controller_accept")
    elif kind == "waive":
        _required_string(decision.get("reason"), "waiver reason")
        _transition(run, policy["states"], "unvalidated", "controller_waive")
    elif kind == "block":
        _transition(run, policy["states"], "blocked", "controller_block")
    elif kind == "request_approval":
        _transition(run, policy["states"], "awaiting_decision", "controller_request_approval")
    else:
        retry_policy = attempt["packet"]["retry_policy"]
        execution_budget_profile = None
        provider_runtime_binding = None
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
                if attempt["packet"].get("version") == CURRENT_PACKET_API:
                    provider_runtime_binding = attempt["packet"].get("provider_runtime_binding")
                    if not isinstance(provider_runtime_binding, dict):
                        raise HarnessError("timeout outcome lacks provider runtime binding")
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
            _set_outcome(attempt, "retry_exhausted", ["block"], ["decision"])
            _transition(run, policy["states"], "blocked", "retry_exhausted")
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
                    "host_api": 2,
                    "capabilities": lambda: {},
                    "unavailable_detail": "Generic harness CLI has no injected host adapter; use a provider host entrypoint.",
                },
                run_id=args.run_id,
            )
        elif args.command == "friction-report":
            result = friction_report(root)
        elif args.command == "friction-resolve":
            result = resolve_friction(root, args.run_id, args.fingerprint, args.decision)
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
    return 0 if args.command in {"preflight", "friction-report", "friction-resolve", "coordination-status", "handoff"} or result.get("status") == "verified" or result.get("state") == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
