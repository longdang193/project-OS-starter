"""Run one bounded, supervised Secretary attempt through Herdr and Codex."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import sqlite3
import tomllib
import uuid
from typing import Any, Mapping

try:
    from scripts.herdr_main_launcher import (
        _HERDR_DEFAULT_SESSION,
        _herdr_pane,
        CommandTransportTimeout,
        LaunchBlocked,
        TargetCandidateRejected,
        _codex_completion_snapshot,
        _run as _herdr_run,
    )
except ModuleNotFoundError:
    from herdr_main_launcher import (
        _HERDR_DEFAULT_SESSION,
        _herdr_pane,
        CommandTransportTimeout,
        LaunchBlocked,
        TargetCandidateRejected,
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
    from scripts.observe_9router_usage import observe_run_usage, observe_window_usage
except ModuleNotFoundError:
    from observe_9router_usage import observe_run_usage, observe_window_usage


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
_HERDR_SERVER_START_TIMEOUT_SECONDS = 10.0
_HERDR_PREFLIGHT_RECHECK_SECONDS = 0.25
_SAFE_SOURCE_DIGEST = re.compile(r"[0-9a-f]{64}")
_ACCEPTED_RESULT_PRODUCERS = frozenset({"dcode-project", "deepagents-worker"})
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


def _redact_semantic_content(value: object, configured_secrets: tuple[str, ...] = ()) -> str | None:
    if not isinstance(value, str):
        return None
    redacted = value
    for secret in configured_secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    redacted = re.sub(
        r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+",
        "Bearer [REDACTED]",
        redacted,
    )
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
    redacted = re.sub(
        r"(?i)([\"']?(?:password|authorization|api[_-]?key|apikey|secret|token|access_token)[\"']?\s*[:=]\s*)([^\"'\s,;}]+)",
        r"\1[REDACTED]",
        redacted,
    )
    return redacted


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


@dataclass(frozen=True)
class SecretaryNormalRequest:
    worktree: Path
    task: str
    codex_home: Path
    profile: str = "normal"
    session: str = "auto"
    pane: str = "auto"

    def __post_init__(self) -> None:
        for field in ("task", "profile", "session", "pane"):
            _required_text(getattr(self, field), field)


def build_normal_launcher_command(
    request: SecretaryNormalRequest,
    *,
    expected_base: str,
    dry_run: bool = False,
) -> list[str]:
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
        expected_base,
        "--executor",
        "codex",
        "--task",
        (
            f"{request.task}\n\n"
            "Secretary normal-mode boundary: inspect, reason, prioritize, route, or summarize only. "
            "Do not modify repository files. For implementation requests, recommend routing to CoS "
            "and an authorized Worker or governed execution path."
        ),
        "--codex-home",
        str(request.codex_home),
    ]
    if dry_run:
        command.append("--dry-run")
    return command


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


def _herdr_server_running(herdr: str, *, env: dict[str, str]) -> bool:
    try:
        result = _herdr_run([herdr, "status", "server"], env=env, timeout=5.0)
    except CommandTransportTimeout:
        return False
    output = f"{result.stdout}\n{result.stderr}".casefold()
    return result.returncode == 0 and "status: running" in output


def _start_herdr_server(herdr: str, *, env: dict[str, str]) -> None:
    kwargs: dict[str, Any] = {
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs["startupinfo"] = startup_info
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    subprocess.Popen([herdr, "server"], **kwargs)


def _ensure_herdr_server(herdr: str, *, env: dict[str, str]) -> dict[str, Any]:
    if _herdr_server_running(herdr, env=env):
        return {"state": "ready", "started": False}
    _start_herdr_server(herdr, env=env)
    deadline = time.monotonic() + _HERDR_SERVER_START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if _herdr_server_running(herdr, env=env):
            return {"state": "ready", "started": True}
        time.sleep(_HERDR_PREFLIGHT_RECHECK_SECONDS)
    raise LaunchBlocked("herdr_server_unavailable: server did not become ready")


def _create_herdr_workspace(
    request: SecretaryLaunchRequest | SecretaryNormalRequest,
    herdr: str,
    *,
    env: dict[str, str],
    invocation_id: str | None = None,
) -> tuple[str, str]:
    label_source = invocation_id or getattr(request, "attempt_id", "secretary")
    label = f"secretary-{label_source[:12]}"
    result = _herdr_run(
        [
            herdr,
            "workspace",
            "create",
            "--cwd",
            str(request.worktree),
            "--label",
            label,
            "--no-focus",
        ],
        env=env,
        timeout=30.0,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise LaunchBlocked(f"Herdr workspace bootstrap failed: {detail}")
    workspace_id: str | None = None
    try:
        payload = json.loads(result.stdout)
        result_payload = payload.get("result") if isinstance(payload, Mapping) else None
        if isinstance(result_payload, Mapping):
            workspace_id = _safe_text(result_payload.get("workspace_id"))
        if not isinstance(result_payload, Mapping):
            raise TypeError("workspace creation result is not an object")
        root_pane = result_payload.get("root_pane")
        if not isinstance(root_pane, Mapping):
            raise TypeError("workspace root pane is not an object")
        root_workspace_id = _safe_text(root_pane.get("workspace_id"))
        if root_workspace_id is None:
            raise ValueError("root pane workspace identity missing")
        if workspace_id is not None and workspace_id != root_workspace_id:
            raise ValueError("root pane workspace identity mismatch")
        workspace_id = root_workspace_id
        pane_id = root_pane["pane_id"]
        pane_cwd = Path(root_pane["cwd"]).resolve()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        workspace_close = (
            _close_herdr_workspace(herdr, workspace_id, env=env)
            if workspace_id
            else None
        )
        error = LaunchBlocked("Herdr workspace bootstrap returned invalid root pane data")
        error.workspace_id = workspace_id
        error.workspace_close = workspace_close
        raise error from exc
    if not all(isinstance(value, str) and value.strip() for value in (workspace_id, pane_id)):
        if isinstance(workspace_id, str) and workspace_id.strip():
            workspace_close = _close_herdr_workspace(herdr, workspace_id, env=env)
        else:
            workspace_close = None
        error = LaunchBlocked("Herdr workspace bootstrap returned incomplete root pane data")
        error.workspace_id = workspace_id
        error.workspace_close = workspace_close
        raise error
    if pane_cwd != request.worktree.resolve():
        workspace_close = _close_herdr_workspace(herdr, workspace_id, env=env)
        error = LaunchBlocked(f"Herdr workspace cwd mismatch: expected {request.worktree}, got {pane_cwd}")
        error.workspace_id = workspace_id
        error.workspace_close = workspace_close
        raise error
    return workspace_id, pane_id


def _verify_herdr_pane(
    request: SecretaryLaunchRequest,
    herdr: str,
    pane: str,
    *,
    env: dict[str, str],
) -> None:
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            _herdr_pane(
                request.worktree,
                _HERDR_DEFAULT_SESSION,
                pane,
                herdr,
                env=env,
            )
            return
        except (CommandTransportTimeout, TargetCandidateRejected) as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(_HERDR_PREFLIGHT_RECHECK_SECONDS)
    raise LaunchBlocked(f"Herdr pane preflight failed: {last_error}")


def _prepare_herdr_target(
    request: SecretaryLaunchRequest | SecretaryNormalRequest,
    *,
    herdr: str,
    env: dict[str, str],
    invocation_id: str | None = None,
) -> tuple[SecretaryLaunchRequest | SecretaryNormalRequest, dict[str, Any], str | None]:
    if request.session == "auto" and request.pane != "auto":
        raise LaunchBlocked("`--session auto` and `--pane auto` must be used together.")
    server = _ensure_herdr_server(herdr, env=env)
    if request.session != "auto":
        return request, {
            "server": server["state"],
            "server_started": server["started"],
            "selector_mode": "named-session-auto-pane" if request.pane == "auto" else "exact",
            "session": request.session,
            "pane": request.pane,
            "pane_cwd_verified": False,
            "workspace_created": False,
        }, None
    workspace_id, pane = _create_herdr_workspace(
        request,
        herdr,
        env=env,
        invocation_id=invocation_id,
    )
    try:
        _verify_herdr_pane(request, herdr, pane, env=env)
    except Exception as exc:
        exc.workspace_id = workspace_id
        exc.workspace_close = _close_herdr_workspace(herdr, workspace_id, env=env)
        raise
    return replace(request, session=_HERDR_DEFAULT_SESSION, pane=pane), {
        "server": server["state"],
        "server_started": server["started"],
        "selector_mode": "bootstrapped",
        "session": _HERDR_DEFAULT_SESSION,
        "pane": pane,
        "pane_cwd_verified": True,
        "workspace_created": True,
        "workspace_id": workspace_id,
    }, workspace_id


def _close_herdr_workspace(herdr: str, workspace_id: str, *, env: dict[str, str]) -> dict[str, Any]:
    try:
        result = _herdr_run(
            [herdr, "workspace", "close", workspace_id],
            env=env,
            timeout=30.0,
        )
    except (CommandTransportTimeout, OSError):
        return {"state": "unknown", "verified": False, "reason": "transport_timeout"}
    if result is None or not isinstance(getattr(result, "returncode", None), int):
        return {"state": "unknown", "verified": False, "reason": "malformed_close_response"}
    if result.returncode:
        return {"state": "unknown", "verified": False, "reason": "close_failed"}
    for output in (getattr(result, "stdout", ""), getattr(result, "stderr", "")):
        try:
            payload = json.loads(output)
        except (TypeError, json.JSONDecodeError):
            continue
        evidence = payload.get("result") if isinstance(payload, Mapping) else None
        evidence = evidence if isinstance(evidence, Mapping) else payload
        if isinstance(evidence, Mapping) and evidence.get("workspace_id") == workspace_id and evidence.get("state") in {"closed", "removed", "absent"}:
            return {"state": "closed", "verified": True, "authority": "herdr.workspace.close"}
    try:
        check = _herdr_run(
            [herdr, "workspace", "get", workspace_id],
            env=env,
            timeout=5.0,
        )
    except (CommandTransportTimeout, OSError):
        return {"state": "closed", "verified": False, "reason": "workspace_retirement_not_proven"}
    if check is None or not isinstance(getattr(check, "returncode", None), int):
        return {"state": "closed", "verified": False, "reason": "workspace_retirement_not_proven"}
    if check.returncode:
        for output in (getattr(check, "stdout", ""), getattr(check, "stderr", "")):
            try:
                payload = json.loads(output)
            except (TypeError, json.JSONDecodeError):
                continue
            error = payload.get("error") if isinstance(payload, Mapping) else None
            code = error.get("code") if isinstance(error, Mapping) else None
            if code in {"workspace_not_found", "workspace_missing", "not_found"}:
                return {"state": "closed", "verified": True, "authority": "herdr.workspace.get"}
        return {"state": "closed", "verified": False, "reason": "workspace_retirement_not_proven"}
    return {"state": "closed", "verified": False, "reason": "workspace_still_present"}


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
    except (CommandTransportTimeout, OSError):
        return {"state": "unknown", "error": "release-agent transport timeout"}
    if result is None or not isinstance(getattr(result, "returncode", None), int):
        return {"state": "unknown", "error": "malformed agent interruption response"}
    if result.returncode:
        try:
            get_result = _herdr_run(
                [herdr, "--session", session, "agent", "get", agent_name],
                env=env,
                timeout=1.0,
            )
        except (CommandTransportTimeout, OSError):
            return {"state": "unknown", "error": "agent interruption failed"}
        if get_result is None or not isinstance(getattr(get_result, "returncode", None), int):
            return {"state": "unknown", "error": "malformed agent observation response"}
        if get_result.returncode:
            for output in (getattr(get_result, "stdout", ""), getattr(get_result, "stderr", "")):
                try:
                    payload = json.loads(output)
                except (TypeError, json.JSONDecodeError):
                    continue
                error = payload.get("error") if isinstance(payload, Mapping) else None
                if isinstance(error, Mapping) and error.get("code") == "agent_not_found":
                    return {"state": "removed"}
        return {"state": "unknown", "error": "agent interruption failed"}
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            get_result = _herdr_run(
                [herdr, "--session", session, "agent", "get", agent_name],
                env=env,
                timeout=1.0,
            )
        except (CommandTransportTimeout, OSError):
            return {"state": "unknown", "error": "agent retirement observation timed out"}
        if get_result is None or not isinstance(getattr(get_result, "returncode", None), int):
            return {"state": "unknown", "error": "malformed agent observation response"}
        if get_result.returncode:
            error_code = None
            for output in (getattr(get_result, "stdout", ""), getattr(get_result, "stderr", "")):
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
    grace_deadline = deadline + 5.0
    while time.monotonic() < grace_deadline:
        try:
            get_result = _herdr_run(
                [herdr, "--session", session, "agent", "get", agent_name],
                env=env,
                timeout=1.0,
            )
        except (CommandTransportTimeout, OSError):
            return {"state": "unknown", "error": "agent retirement observation timed out"}
        if get_result is None or not isinstance(getattr(get_result, "returncode", None), int):
            return {"state": "unknown", "error": "malformed agent observation response"}
        for output in (getattr(get_result, "stdout", ""), getattr(get_result, "stderr", "")):
            try:
                payload = json.loads(output)
            except (TypeError, json.JSONDecodeError):
                continue
            error = payload.get("error") if isinstance(payload, Mapping) else None
            if isinstance(error, Mapping) and error.get("code") == "agent_not_found":
                return {"state": "removed"}
        time.sleep(0.1)
    return {"state": "unknown", "error": "agent retirement not observed"}


def _observe_submitted_codex(
    request: SecretaryLaunchRequest | SecretaryNormalRequest,
    payload: Mapping[str, Any],
    *,
    pre_submit: Mapping[str, Any] | None = None,
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

    assignment = payload.get("assignment")
    assignment = assignment if isinstance(assignment, Mapping) else None
    ownership = herdr.get("ownership")
    ownership = ownership if isinstance(ownership, Mapping) else None
    assignment_id = assignment.get("assignment_id") if assignment else None
    attempt_id = assignment.get("attempt_id") if assignment else None
    if assignment is not None and not isinstance(attempt_id, str):
        return {"state": "unknown", "error": "launcher assignment identity incomplete"}
    if ownership is not None:
        for key in ("assignment_id", "attempt_id"):
            owned_value = ownership.get(key)
            assignment_value = assignment.get(key) if assignment else None
            if (
                owned_value is not None
                and assignment_value is not None
                and owned_value != assignment_value
            ):
                return {"state": "unknown", "error": "completion identity mismatch"}

    anchor = pre_submit
    if not isinstance(anchor, Mapping):
        anchor = payload.get("pre_submit")
    if not isinstance(anchor, Mapping):
        anchor = None

    deadline = time.monotonic() + _CODEX_OBSERVATION_TIMEOUT_SECONDS
    snapshot: dict[str, Any] = {
        "state": "unknown",
        "observation_error": "completion observation deadline expired",
    }
    completed = False
    task_result = assignment.get("task_result") if assignment else None
    structured_result_owned = _result_source_authoritative(task_result, assignment)
    freshness_proven = False
    legacy_first_snapshot: dict[str, Any] | None = None
    legacy_output_changed = False
    legacy_state_changed = False
    legacy_state_seq_changed = False
    legacy_activity = False
    while time.monotonic() < deadline:
        remaining = max(0.01, deadline - time.monotonic())
        snapshot = _codex_completion_snapshot(
            executable,
            session,
            agent_name,
            env=env,
            timeout_seconds=min(5.0, remaining),
        )
        if any(key in snapshot for key in ("assignment_id", "attempt_id")):
            if (
                (assignment_id is not None and snapshot.get("assignment_id") not in (None, assignment_id))
                or (attempt_id is not None and snapshot.get("attempt_id") not in (None, attempt_id))
            ):
                snapshot["observation_error"] = "completion identity mismatch"
                snapshot["state"] = "unknown"
                break
        if anchor is None and legacy_first_snapshot is None:
            legacy_first_snapshot = dict(snapshot)
            legacy_activity = snapshot.get("state") == "working" or (
                snapshot.get("state") == "idle" and bool(snapshot.get("observation_error"))
            )
        elif anchor is None and legacy_first_snapshot is not None:
            legacy_output_changed = any(
                snapshot.get(key) != legacy_first_snapshot.get(key)
                for key in ("content", "output_sha256", "output_chars")
            )
            legacy_state_changed = snapshot.get("state") != legacy_first_snapshot.get("state")
            legacy_state_seq_changed = (
                snapshot.get("state_change_seq") is not None
                and snapshot.get("state_change_seq") != legacy_first_snapshot.get("state_change_seq")
            )
        freshness_anchor = anchor or legacy_first_snapshot
        freshness_proven = _submission_freshness_proven(freshness_anchor, snapshot)
        semantic_content = _extract_codex_semantic_content(snapshot.get("content"))
        initial_prompt_content = _codex_initial_prompt_bullet(snapshot.get("content"))
        if semantic_content and initial_prompt_content == semantic_content:
            completion_identity = any(
                snapshot.get(key) not in (None, "")
                for key in ("result_id", "result_reference", "completion_id")
            )
            anchor_semantic = (
                _extract_codex_semantic_content(anchor.get("content"))
                if isinstance(anchor, Mapping)
                else None
            )
            if not completion_identity and anchor_semantic != semantic_content:
                semantic_content = None
        snapshot_result_owned = _result_source_authoritative(snapshot, assignment)
        terminal_result_owned = _terminal_result_proven(snapshot, freshness_proven)
        if semantic_content and not (
            structured_result_owned or snapshot_result_owned or terminal_result_owned
        ):
            semantic_content = None
        if snapshot.get("state") in {"failed", "stopped"}:
            break
        if (
            (
                snapshot.get("state") in {"idle", "done"}
                and freshness_proven
                and semantic_content
            )
            or (
                anchor is None
                and legacy_activity
                and snapshot.get("state") in {"idle", "done", "failed", "stopped"}
                and legacy_output_changed
                and (legacy_state_changed or legacy_state_seq_changed)
            )
            and not snapshot.get("observation_error")
        ):
            completed = True
            break
        time.sleep(min(_CODEX_OBSERVATION_POLL_SECONDS, remaining))

    if not completed and snapshot.get("state") in {"idle", "done"}:
        snapshot["observation_error"] = snapshot.get("observation_error") or (
            "submission freshness not proven" if not freshness_proven else "completion output not observed"
        )

    observation = {
        key: snapshot.get(key)
        for key in (
            "state",
            "state_change_seq",
            "content",
            "output_sha256",
            "output_chars",
            "observation_error",
        )
        if key in snapshot
    }
    semantic_content = None
    if completed and snapshot.get("state") in {"idle", "done"} and not snapshot.get("observation_error"):
        semantic_content = _extract_codex_semantic_content(snapshot.get("content"))
        if semantic_content and not (
            structured_result_owned
            or _result_source_authoritative(snapshot, assignment)
            or _terminal_result_proven(snapshot, freshness_proven)
        ):
            semantic_content = None
    if semantic_content:
        observation["semantic_content"] = semantic_content
        observation["assistant_owned"] = True
        for key in ("result_id", "result_reference", "completion_id"):
            if snapshot.get(key) not in (None, ""):
                observation[key] = snapshot[key]
    observation.update({"session": session, "pane": pane, "agent_name": agent_name})
    if assignment_id is not None:
        observation["assignment_id"] = assignment_id
    if attempt_id is not None:
        observation["attempt_id"] = attempt_id
    observation["freshness_proven"] = freshness_proven
    cleanup: dict[str, Any] = {"state": "not_attempted"}
    if snapshot.get("state") in {"idle", "done"}:
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


def _submission_freshness_proven(
    anchor: Mapping[str, Any] | None,
    snapshot: Mapping[str, Any],
) -> bool:
    if not isinstance(anchor, Mapping):
        return False
    identity_changed = False
    for key in ("result_id", "result_reference", "completion_id"):
        if snapshot.get(key) not in (None, "") and snapshot.get(key) != anchor.get(key):
            identity_changed = True
            break
    anchor_semantic = _extract_codex_semantic_content(anchor.get("content"))
    snapshot_semantic = _extract_codex_semantic_content(snapshot.get("content"))
    if anchor_semantic and snapshot_semantic and anchor_semantic == snapshot_semantic and not identity_changed:
        anchor_completion = _extract_codex_completion_marker(anchor.get("content"))
        snapshot_completion = _extract_codex_completion_marker(snapshot.get("content"))
        if snapshot_completion is None:
            return False
        if snapshot.get("content") != anchor.get("content") and (
            snapshot_completion == anchor_completion
            or _codex_has_post_completion_bullet(snapshot.get("content"))
            or _codex_completion_prefix(snapshot.get("content"))
            != _codex_completion_prefix(anchor.get("content"))
        ):
            return False
    anchor_seq = anchor.get("state_change_seq")
    snapshot_seq = snapshot.get("state_change_seq")
    if anchor_seq is not None and snapshot_seq is not None and anchor_seq != snapshot_seq:
        return True
    anchor_digest = anchor.get("output_sha256")
    snapshot_digest = snapshot.get("output_sha256")
    if isinstance(anchor_digest, str) and isinstance(snapshot_digest, str) and anchor_digest != snapshot_digest:
        return True
    anchor_chars = anchor.get("output_chars")
    snapshot_chars = snapshot.get("output_chars")
    if isinstance(anchor_chars, int) and isinstance(snapshot_chars, int) and anchor_chars != snapshot_chars:
        return True
    for key in ("result_id", "result_reference", "completion_id"):
        if snapshot.get(key) not in (None, "") and snapshot.get(key) != anchor.get(key):
            return True
    return False


def _capture_submission_anchor(
    herdr: str,
    session: str,
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
                "pane",
                "read",
                pane,
                "--source",
                "recent-unwrapped",
                "--lines",
                "200",
                "--format",
                "text",
            ],
            env=env,
            timeout=5.0,
        )
    except (CommandTransportTimeout, OSError):
        return {"state": "unknown", "observation_error": "submission anchor read timed out"}
    if result.returncode:
        return {"state": "unknown", "observation_error": "submission anchor read failed"}
    content = result.stdout.strip()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, Mapping):
        result_value = parsed.get("result")
        if isinstance(result_value, str):
            content = result_value.strip()
        elif isinstance(result_value, Mapping):
            for key in ("text", "output", "content"):
                if isinstance(result_value.get(key), str):
                    content = result_value[key].strip()
                    break
    return {
        "state": "idle",
        "content": content,
        "output_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "output_chars": len(content),
    }


def _observe_provider_telemetry(start: str, end: str, *, expected_session_id: str | None = None) -> dict[str, Any]:
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
        if isinstance(expected_session_id, str) and expected_session_id.strip():
            result = observe_run_usage(
                database,
                start=padded_start,
                end=end,
                expected_session_id=expected_session_id,
            )
        else:
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
        and observation.get("state") in {"idle", "done"}
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
    if _identity_conflict(runtime, assignment):
        return False
    if isinstance(assignment, Mapping) and assignment.get("attempt_id") not in (None, request.attempt_id):
        return False
    return runtime.get("attempt_id") == request.attempt_id


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
    return _safe_text(runtime.get("session_id")) is not None


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


def _validated_runtime_receipt(
    request: SecretaryLaunchRequest,
    runtime: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(runtime, Mapping):
        return None
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
    try:
        return validate_live_receipt(
            build_live_receipt(
                binding=binding,
                runtime={
                    "provider": runtime.get("provider"),
                    "model": runtime.get("model"),
                    "controller_id": runtime.get("controller_id"),
                    "session_id": runtime.get("session_id"),
                },
                timestamps=runtime.get("timestamps", {}),
                metrics=runtime.get("metrics", {}),
                sources=runtime.get("sources", {}),
            )
        )
    except (TypeError, ValueError):
        return None


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
    if observation.get("state") not in {"idle", "done"}:
        return None
    cleanup = observation.get("cleanup")
    if not isinstance(cleanup, Mapping) or cleanup.get("state") != "removed":
        return None
    if not isinstance(payload, Mapping):
        return None

    raw_runtime = payload.get("secretary_runtime")
    if not isinstance(raw_runtime, Mapping) or raw_runtime.get("observed") is not True:
        return None
    raw_timestamps = raw_runtime.get("timestamps")
    raw_metrics = raw_runtime.get("metrics")
    raw_sources = raw_runtime.get("sources")
    if (
        not isinstance(raw_timestamps, Mapping)
        or set(raw_timestamps) != set(_OBSERVED_TIMESTAMP_KEYS)
        or not isinstance(raw_metrics, Mapping)
        or set(raw_metrics) != set(_OBSERVED_METRIC_KEYS)
        or not isinstance(raw_sources, Mapping)
        or set(raw_sources) != set(_SOURCE_KEYS)
    ):
        return None

    herdr = payload.get("herdr")
    git = payload.get("git")
    registry = payload.get("registry_launcher")
    if not all(isinstance(value, Mapping) for value in (herdr, git, registry)):
        return None
    session_id = _safe_text(raw_runtime.get("session_id"))
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
    identity_fields = _RUNTIME_BINDING_KEYS + (
        "repository_identity", "plan_identity", "git_revision", "worktree",
        "provider", "model", "controller_id", "session_id",
    )
    if any(raw_runtime.get(key) != expected_values.get(key) for key in identity_fields):
        return None
    existing = (
        _safe_runtime_snapshot(raw_runtime, expected_values)
        if isinstance(raw_runtime, Mapping)
        else {}
    )
    timestamps = existing.get("timestamps")
    if not isinstance(timestamps, Mapping) or set(timestamps) != set(_OBSERVED_TIMESTAMP_KEYS):
        return None
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
    existing["metrics"] = metrics
    existing["session_id"] = session_id
    validated = _validated_runtime_receipt(request, existing)
    if validated is None:
        return None
    runtime_identity = {
        **{key: validated[key] for key in (
            "pair_id", "arm", "run_id", "attempt_id", "task_id", "plan_revision",
            "repository_identity", "plan_identity", "git_revision", "worktree",
            "workstream", "checkpoint",
        )},
        "provider": validated["provider"],
        "model": validated["model"],
        "controller_id": validated["controller_id"],
        "session_id": validated["session_id"],
    }
    return {
        **runtime_identity,
        "observed": True,
        "timestamps": validated["timestamps"],
        "metrics": validated["metrics"],
        "sources": validated["sources"],
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
    if isinstance(raw_runtime, Mapping):
        session_id = _safe_text(raw_runtime.get("session_id"))
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
        and _validated_runtime_receipt(request, structured_binding) is not None
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
    if result.get("disposition") not in (None, "READY") or result.get("evidence_provenance") != "live-attributed":
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


def _read_only_git_anchor(worktree: Path) -> tuple[Path, str]:
    completed = subprocess.run(
        ["git", "-C", str(worktree), "rev-parse", "--show-toplevel", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "git worktree anchor unavailable"
        raise LaunchBlocked(detail)
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 2:
        raise LaunchBlocked("git worktree anchor returned incomplete identity")
    return Path(lines[0]).resolve(), _required_text(lines[1], "git_revision")


def _identity_conflict(*sources: Mapping[str, Any] | None) -> bool:
    for field in ("assignment_id", "attempt_id"):
        values = {
            value.strip()
            for source in sources
            if isinstance(source, Mapping)
            for value in (source.get(field),)
            if isinstance(value, str) and value.strip()
        }
        if len(values) > 1:
            return True
    return False


def _reduce_resource_evidence(*evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    state = "unknown"
    for item in evidence:
        if not isinstance(item, Mapping):
            continue
        candidate = item.get("state")
        verified = item.get("verified") is True
        if candidate in {"removed", "closed", "settled"} and verified:
            if state in {"unknown", "present"}:
                state = "removed"
        elif candidate in {"present", "preserved"}:
            if state == "removed":
                return {
                    "state": "quarantined",
                    "evidence_state": "conflict",
                    "reuse_blocked": True,
                    "recovery_required": True,
                }
            state = "present"
    if state == "present":
        return {
            "state": "quarantined",
            "evidence_state": "present",
            "reuse_blocked": True,
            "recovery_required": True,
        }
    if state == "removed":
        return {
            "state": "settled",
            "evidence_state": "removed",
            "reuse_blocked": False,
            "recovery_required": False,
        }
    return {
        "state": "quarantined",
        "evidence_state": "unknown",
        "reuse_blocked": True,
        "recovery_required": True,
    }


def _owned_resources(
    payload: Mapping[str, Any] | None,
    observation: Mapping[str, Any] | None,
    *,
    cleanup_state: str | None = None,
    workspace_id: str | None = None,
    workspace_close: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    herdr = payload.get("herdr") if isinstance(payload, Mapping) else None
    herdr = herdr if isinstance(herdr, Mapping) else {}
    observed = observation if isinstance(observation, Mapping) else {}
    cleanup = observed.get("cleanup") if isinstance(observed.get("cleanup"), Mapping) else {}
    effective_cleanup_state = cleanup_state or cleanup.get("state")
    ownership = herdr.get("ownership")
    ownership = ownership if isinstance(ownership, Mapping) else {}
    resources: list[dict[str, Any]] = []
    if workspace_id:
        resources.append({
            "kind": "workspace",
            "identity": workspace_id,
            "state": "settled" if workspace_close and workspace_close.get("verified") is True else "quarantined",
            "authority": "herdr.workspace.close",
        })
    pane_identity = _safe_text(herdr.get("pane"))
    if workspace_id and pane_identity:
        resources.append({
            "kind": "pane",
            "identity": pane_identity,
            "state": "settled" if effective_cleanup_state == "removed" else "quarantined",
            "authority": "herdr.workspace.close",
        })
    agent_identity = _safe_text(herdr.get("agent_name"))
    agent_owned = (
        agent_identity
        and (
            ownership.get("agent") == agent_identity
            or effective_cleanup_state == "removed"
        )
    )
    if agent_owned:
        resources.append({
            "kind": "agent",
            "identity": agent_identity,
            "state": "settled" if effective_cleanup_state == "removed" else "quarantined",
            "authority": "secretary_live_runtime._release_codex_agent",
        })
    process_identity = herdr.get("process_identity") or observed.get("process_identity")
    if isinstance(process_identity, Mapping):
        safe_identity = {
            key: process_identity[key]
            for key in ("pid", "name", "cwd")
            if key in process_identity and _safe_text(str(process_identity[key])) is not None
        }
        if safe_identity and agent_owned:
            resources.append({
                "kind": "process",
                "identity": safe_identity,
                "state": "settled" if effective_cleanup_state == "removed" else "quarantined",
                "authority": "herdr.process-retirement",
            })
    return resources


def _safe_result_value(value: object, *, allow_long: bool = False) -> str | None:
    text = _safe_text(value)
    if text is None or (not allow_long and len(text) > 4096):
        return None
    return text


def _safe_semantic_result_value(value: object, *, allow_long: bool = False) -> str | None:
    text = _redact_semantic_content(value, _configured_semantic_secrets())
    if text is None or (not allow_long and len(text) > 4096):
        return None
    return text


def _extract_codex_semantic_content(value: object) -> str | None:
    text = _redact_semantic_content(value, _configured_semantic_secrets())
    if text is None or "› Ask Codex" not in text:
        return None
    segments = re.split(r"(?m)^\s*Worked for\b.*$", text)
    has_completion_marker = bool(re.search(r"(?m)^\s*Worked for\b.*$", text))
    candidates: list[str] = []
    prompt_boundary = False
    for segment_index, segment in enumerate(segments):
        lines = segment.splitlines()
        saw_prompt = False
        prompt_echo = False
        found_candidate = False
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("› "):
                saw_prompt = True
                prompt_echo = prompt_echo or stripped.casefold().startswith(
                    "› please echo this input:"
                )
                continue
            if (
                prompt_boundary
                or prompt_echo
                or (saw_prompt and not has_completion_marker)
            ):
                continue
            if not stripped.startswith("• "):
                continue
            content_lines = [stripped[2:].strip()]
            for continuation in lines[index + 1:]:
                continuation = continuation.strip()
                if not continuation:
                    continue
                if continuation.startswith(("• ", "› ", "Ask Codex", "combo-")):
                    break
                content_lines.append(continuation)
            content = "\n".join(line for line in content_lines if line)
            if content:
                candidates.append(content)
                found_candidate = True
        if prompt_echo and not found_candidate:
            prompt_boundary = True
        elif found_candidate:
            prompt_boundary = False
    return candidates[-1] if candidates else None


def _codex_initial_prompt_bullet(value: object) -> str | None:
    text = _redact_semantic_content(value, _configured_semantic_secrets())
    if text is None or "› Ask Codex" not in text:
        return None
    first_segment = re.split(r"(?m)^\s*Worked for\b.*$", text, maxsplit=1)[0]
    prompt_echo = False
    lines = first_segment.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("› "):
            prompt_echo = stripped.casefold().startswith("› please echo this input:")
            continue
        if prompt_echo and stripped.startswith("• "):
            content_lines = [stripped[2:].strip()]
            for continuation in lines[index + 1:]:
                continuation = continuation.strip()
                if not continuation:
                    continue
                if continuation.startswith(("› ", "Ask Codex", "combo-")):
                    break
                content_lines.append(continuation)
            content = "\n".join(line for line in content_lines if line)
            return content or None
    return None


def _extract_codex_completion_marker(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    matches = re.findall(r"(?m)^\s*Worked for\b.*$", value)
    return matches[-1].strip() if matches else None


def _terminal_result_proven(
    snapshot: Mapping[str, Any],
    freshness_proven: bool,
) -> bool:
    return bool(
        freshness_proven
        and snapshot.get("state") in {"idle", "done"}
        and not snapshot.get("observation_error")
        and _extract_codex_completion_marker(snapshot.get("content"))
    )


def _codex_completion_prefix(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    matches = list(re.finditer(r"(?m)^\s*Worked for\b.*$", value))
    if not matches:
        return value.strip()
    return value[: matches[-1].start()].strip()


def _codex_has_post_completion_bullet(value: object) -> bool:
    if not isinstance(value, str):
        return False
    matches = list(re.finditer(r"(?m)^\s*Worked for\b.*$", value))
    if not matches:
        return False
    return re.search(r"(?m)^\s*• ", value[matches[-1].end() :]) is not None


def _configured_semantic_secrets() -> tuple[str, ...]:
    configured = os.environ.get("SECRETARY_SEMANTIC_SECRETS", "")
    return tuple(value for value in configured.split(",") if value)


def _result_evidence(source: Mapping[str, Any]) -> tuple[str | None, str | None]:
    reference = None
    for key in ("result_reference", "reference", "source_ref", "result_ref"):
        reference = _safe_result_value(source.get(key))
        if reference:
            break
    content = None
    for key in ("semantic_content", "content", "response", "message", "result_content", "resolved_content"):
        content = _safe_semantic_result_value(source.get(key), allow_long=True)
        if content:
            break
    if content:
        return reference, content
    resolver = _safe_text(source.get("result_resolver") or source.get("resolver"))
    retrieved = source.get("result_retrieved") is True or source.get("retrieved") is True
    if reference and resolver and retrieved:
        return reference, None
    return None, None


def _result_source_authoritative(
    source: object,
    assignment: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(source, Mapping):
        return False
    source_identity = {
        key: source.get(key)
        for key in ("assignment_id", "attempt_id")
        if isinstance(source.get(key), str) and source.get(key).strip()
    }
    assignment_identity = {
        key: assignment.get(key)
        for key in ("assignment_id", "attempt_id")
        if isinstance(assignment, Mapping)
        and isinstance(assignment.get(key), str)
        and assignment.get(key).strip()
    }
    if not source_identity or not assignment_identity:
        producer = source.get("producer")
        if source.get("assistant_owned") is not True:
            return False
        if producer is not None and producer not in _ACCEPTED_RESULT_PRODUCERS:
            return False
        reference, content = _result_evidence(source)
        reference = reference or next(
            (
                _safe_result_value(source.get(key))
                for key in ("result_reference", "reference", "source_ref", "result_ref")
                if _safe_result_value(source.get(key))
            ),
            None,
        )
        return bool(reference or content)
    if any(assignment_identity.get(key) != value for key, value in source_identity.items()):
        return False
    producer = source.get("producer")
    if producer is not None and producer not in _ACCEPTED_RESULT_PRODUCERS:
        return False
    reference, content = _result_evidence(source)
    reference = reference or next(
        (
            _safe_result_value(source.get(key))
            for key in ("result_reference", "reference", "source_ref", "result_ref")
            if _safe_result_value(source.get(key))
        ),
        None,
    )
    return bool(reference or content)


def _project_semantic_result(outcome: Mapping[str, Any]) -> dict[str, Any]:
    result = {
        "state": outcome.get("state"),
        "status": outcome.get("status"),
    }
    for key in ("reference", "content"):
        value = outcome.get(key)
        if value:
            result[key] = value
    return result
    resolver = _safe_text(source.get("result_resolver") or source.get("resolver"))
    retrieved = source.get("result_retrieved") is True or source.get("retrieved") is True
    if reference and resolver and retrieved:
        return reference, None
    return None, None


def _normalize_invocation_outcome(
    *,
    invocation_id: str,
    returncode: int,
    payload: Mapping[str, Any] | None,
    observation: Mapping[str, Any] | None,
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    assignment = payload.get("assignment") if isinstance(payload, Mapping) else None
    assignment = assignment if isinstance(assignment, Mapping) else {}
    execution = assignment.get("execution")
    execution = dict(execution) if isinstance(execution, Mapping) else {}
    launcher_observation_error = _safe_text(execution.get("observation_error"))
    if launcher_observation_error:
        execution["observation_error_scope"] = "launcher"
        execution["launcher_observation_error"] = launcher_observation_error
    if not isinstance(execution.get("state"), str):
        execution["state"] = "failed" if returncode else "unknown"
    cleanup = assignment.get("cleanup")
    cleanup = cleanup if isinstance(cleanup, Mapping) else {}
    observed = observation if isinstance(observation, Mapping) else {}
    task_result = assignment.get("task_result")
    task_result = task_result if isinstance(task_result, Mapping) else {}
    task_state = task_result.get("state")
    result_status = {
        "reported_completed": "completed",
        "reported_failed": "failed",
    }.get(task_state)

    references: list[str] = []
    content: str | None = None
    observation_reportable = (
        observed.get("state") in {"idle", "done"}
        and not observed.get("observation_error")
    )
    observed_evidence: Mapping[str, Any] = (
        {key: value for key, value in observed.items() if key != "content"}
        if observation_reportable
        else {}
    )
    for source in (task_result, observed_evidence):
        if not _result_source_authoritative(source, assignment):
            continue
        reference, source_content = _result_evidence(source)
        if reference and reference not in references:
            references.append(reference)
        if content is None and source_content:
            content = source_content

    ambiguous = bool(task_result.get("ambiguous")) or _identity_conflict(task_result, assignment)
    if len(references) > 1:
        ambiguous = True
    if result_status is None and (references or content) and not ambiguous:
        result_status = "failed" if observed.get("state") == "failed" else "completed"
    if ambiguous:
        semantic_outcome = {
            "state": "ambiguous",
            "status": None,
            "reference": None,
            "content": None,
        }
    elif result_status is not None and (references or content):
        semantic_outcome = {
            "state": "reported",
            "status": result_status,
            "reference": references[0] if references else None,
            "content": content,
        }
    else:
        semantic_outcome = {
            "state": "unavailable",
            "status": None,
            "reference": None,
            "content": None,
        }
    result = _project_semantic_result(semantic_outcome)

    observed_cleanup = observed.get("cleanup")
    cleanup_state = cleanup.get("state")
    if isinstance(observed_cleanup, Mapping):
        observed_cleanup_state = observed_cleanup.get("state")
        if observed_cleanup_state and cleanup_state in {None, "unknown", "not_attempted", "preserved"}:
            cleanup_state = observed_cleanup_state
    resource = _reduce_resource_evidence(
        {"state": cleanup_state, "verified": cleanup_state == "removed"},
    )
    owned_resources = _owned_resources(payload, observed, cleanup_state=cleanup_state)

    observability_state = (
        "available" if observed and not observed.get("observation_error") else "unavailable"
    )
    observed_cleanup_state = (
        observed_cleanup.get("state") if isinstance(observed_cleanup, Mapping) else None
    )
    observability = {
        "state": observability_state,
        "reference": references[0] if references else None,
        "completion_state": observed.get("state"),
        "cleanup_state": cleanup_state or observed_cleanup_state,
        "state_change_seq": observed.get("state_change_seq"),
        "output_chars": observed.get("output_chars"),
        "observation_error": observed.get("observation_error"),
        "launcher_observation_error": launcher_observation_error,
    }
    return {
        "schema_version": "secretary-invocation-v1",
        "invocation_id": invocation_id,
        "execution": execution,
        "result": result,
        "semantic_outcome": dict(semantic_outcome),
        "finalization_outcome": {
            "state": "settled" if resource["state"] == "settled" else "recovery_required",
            "recovery_required": resource["recovery_required"],
        },
        "resource": {key: resource[key] for key in ("state", "reuse_blocked")},
        "owned_resources": owned_resources,
        "recovery_required": resource["recovery_required"],
        "observability": observability,
        "timestamps": {"started": started_at, "finished": finished_at},
    }


def run_normal(request: SecretaryNormalRequest, *, output: Path) -> dict[str, Any]:
    invocation_id = uuid.uuid4().hex
    worktree, expected_base = _read_only_git_anchor(request.worktree)
    request = replace(request, worktree=worktree)
    started = datetime.now(timezone.utc).isoformat()
    environment = dict(os.environ)
    environment["CODEX_HOME"] = str(request.codex_home.resolve())
    herdr = shutil.which("herdr")
    if not herdr:
        raise LaunchBlocked("Required executable unavailable on PATH: herdr")
    launch_request = request
    preflight: dict[str, Any] = {}
    workspace_id: str | None = None
    workspace_close: Mapping[str, Any] | None = None
    payload: Mapping[str, Any] | None = None
    observation: Mapping[str, Any] = {}
    submission_anchor: Mapping[str, Any] | None = None
    result: dict[str, Any] | None = None
    try:
        launch_request, preflight, workspace_id = _prepare_herdr_target(
            request,
            herdr=herdr,
            env=environment,
            invocation_id=invocation_id,
        )
        submission_anchor = _capture_submission_anchor(
            herdr,
            launch_request.session,
            launch_request.pane,
            env=environment,
        )
        completed = subprocess.run(
            build_normal_launcher_command(launch_request, expected_base=expected_base),
            cwd=launch_request.worktree,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        payloads = _json_payloads(completed.stdout) + _json_payloads(completed.stderr)
        payload = select_launcher_payload(payloads) if payloads else None
        if completed.returncode == 0 and isinstance(payload, Mapping):
            observation = _observe_submitted_codex(
                launch_request,
                payload,
                pre_submit=submission_anchor,
                env=environment,
            )
        result = _normalize_invocation_outcome(
            invocation_id=invocation_id,
            returncode=completed.returncode,
            payload=payload,
            observation=observation,
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        workspace_id = getattr(exc, "workspace_id", workspace_id)
        workspace_close = getattr(exc, "workspace_close", None)
        if isinstance(workspace_close, Mapping):
            preflight["workspace_close"] = dict(workspace_close)
        result = _normalize_invocation_outcome(
            invocation_id=invocation_id,
            returncode=1,
            payload=payload,
            observation=observation,
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        result["execution"]["state"] = "failed"
        result["execution"]["error"] = type(exc).__name__
    finally:
        if workspace_id is not None:
            if not isinstance(workspace_close, Mapping) or workspace_close.get("verified") is not True:
                workspace_close = _close_herdr_workspace(herdr, workspace_id, env=environment)
                preflight["workspace_close"] = dict(workspace_close)
            if result is None:
                result = _normalize_invocation_outcome(
                    invocation_id=invocation_id,
                    returncode=1,
                    payload=payload,
                    observation=observation,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
                result["execution"]["state"] = "failed"
            cleanup_state = result.get("observability", {}).get("cleanup_state")
            herdr_identity = payload.get("herdr") if isinstance(payload, Mapping) else None
            cleanup_verified = cleanup_state == "removed" or not isinstance(herdr_identity, Mapping)
            close_verified = preflight.get("workspace_close", {}).get("verified") is True
            resource = (
                {"state": "settled", "reuse_blocked": False, "recovery_required": False}
                if cleanup_verified and close_verified
                else _reduce_resource_evidence({"state": "unknown", "verified": False})
            )
            result["resource"] = {key: resource[key] for key in ("state", "reuse_blocked")}
            result["owned_resources"] = _owned_resources(
                payload,
                observation,
                cleanup_state=cleanup_state,
                workspace_id=workspace_id,
                workspace_close=preflight["workspace_close"],
            )
            result["recovery_required"] = resource["recovery_required"]
            result["finalization_outcome"] = {
                "state": "settled" if resource["state"] == "settled" else "recovery_required",
                "recovery_required": resource["recovery_required"],
            }
    if result is None:
        raise RuntimeError("Secretary normal run did not produce a result")
    result["preflight"] = preflight
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_probe(request: SecretaryLaunchRequest, *, output: Path) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    environment = dict(os.environ)
    environment["CODEX_HOME"] = str(request.codex_home.resolve())
    herdr = shutil.which("herdr")
    launch_request = request
    preflight: dict[str, Any] = {}
    workspace_id: str | None = None
    workspace_close: Mapping[str, Any] | None = None
    configured_model = "unknown"
    result: dict[str, Any] | None = None
    payload: Mapping[str, Any] | None = None
    submission_anchor: Mapping[str, Any] | None = None
    provider_session_id: str | None = None
    try:
        _configured_provider(request.codex_home)
        configured_model = _configured_model(request)
        if not herdr:
            raise LaunchBlocked("Required executable unavailable on PATH: herdr")
        launch_request, preflight, workspace_id = _prepare_herdr_target(
            request,
            herdr=herdr,
            env=environment,
        )
        submission_anchor = _capture_submission_anchor(
            herdr,
            launch_request.session,
            launch_request.pane,
            env=environment,
        )
        completed = subprocess.run(
            build_launcher_command(launch_request),
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
            post_submit = _observe_submitted_codex(
                request,
                payload,
                pre_submit=submission_anchor,
                env=environment,
            )
            result["post_submit_observation"] = post_submit
            if post_submit.get("state") not in {"idle", "done"}:
                result["failure_kind"] = "runtime_completion_observation_missing"
            elif post_submit.get("cleanup", {}).get("state") != "removed":
                result["failure_kind"] = "runtime_cleanup_evidence_missing"
            else:
                result["failure_kind"] = "runtime_structured_receipt_missing"
            result.update(_classify_capabilities(result["disposition"], post_submit))
        else:
            result.update(_classify_capabilities(result["disposition"], None))
        runtime_identity = result.get("runtime_identity")
        expected_session_id = (
            _safe_text(runtime_identity.get("session_id"))
            if isinstance(runtime_identity, Mapping)
            else None
        )
        provider_session_id = expected_session_id
        runtime_snapshot = _build_codex_runtime_snapshot(
            request,
            payload,
            result.get("post_submit_observation", {}),
            configured_model=configured_model,
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
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
    except Exception as exc:
        workspace_id = getattr(exc, "workspace_id", workspace_id)
        workspace_close = getattr(exc, "workspace_close", None)
        if isinstance(workspace_close, Mapping):
            preflight["workspace_close"] = dict(workspace_close)
        result = {
            "disposition": "BLOCKED_CAPABILITY",
            "evidence_provenance": "capability-probe",
            "failure_kind": type(exc).__name__,
            "missing_capabilities": ["secretary_runtime_receipt"],
        }
    finally:
        if workspace_id is not None and herdr:
            if not isinstance(workspace_close, Mapping) or workspace_close.get("verified") is not True:
                workspace_close = _close_herdr_workspace(herdr, workspace_id, env=environment)
                preflight["workspace_close"] = dict(workspace_close)
            if result is not None:
                result["preflight"] = preflight
                post_submit = result.get("post_submit_observation")
                cleanup = post_submit.get("cleanup") if isinstance(post_submit, Mapping) else None
                cleanup_state = cleanup.get("state") if isinstance(cleanup, Mapping) else None
                herdr_identity = payload.get("herdr") if isinstance(payload, Mapping) else None
                cleanup_verified = cleanup_state == "removed" or not isinstance(herdr_identity, Mapping)
                close_verified = preflight["workspace_close"].get("verified") is True
                resource = (
                    {"state": "settled", "reuse_blocked": False, "recovery_required": False}
                    if cleanup_verified and close_verified
                    else _reduce_resource_evidence({"state": "unknown", "verified": False})
                )
                result["resource"] = {key: resource[key] for key in ("state", "reuse_blocked")}
                result["owned_resources"] = _owned_resources(
                    payload,
                    post_submit if isinstance(post_submit, Mapping) else {},
                    cleanup_state=cleanup_state,
                    workspace_id=workspace_id,
                    workspace_close=preflight["workspace_close"],
                )
                result["recovery_required"] = resource["recovery_required"]
                if (
                    result.get("disposition") == "READY"
                    and preflight["workspace_close"].get("verified") is not True
                ):
                    result["disposition"] = "BLOCKED_CAPABILITY"
                    result["evidence_provenance"] = "capability-probe"
                    result["failure_kind"] = "runtime_workspace_cleanup_evidence_missing"
                    result.update(_classify_capabilities("BLOCKED_CAPABILITY", result.get("post_submit_observation")))
    if result is None:
        raise RuntimeError("Secretary smoke did not produce a launcher result")
    result.setdefault("preflight", preflight)
    result["provider_telemetry"] = _observe_provider_telemetry(
        started,
        datetime.now(timezone.utc).isoformat(),
        expected_session_id=provider_session_id,
    )
    result["receipt"] = _smoke_receipt(request, result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


run_smoke = run_probe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command_name in ("probe", "smoke"):
        probe = subparsers.add_parser(command_name)
        probe.add_argument("--output", type=Path, required=True)
        probe.add_argument("--task-id", required=True)
        probe.add_argument("--plan-revision", required=True)
        probe.add_argument("--attempt-id", required=True)
        probe.add_argument("--run-id", required=True)
        probe.add_argument("--repository-identity", required=True)
        probe.add_argument("--plan-identity", required=True)
        probe.add_argument("--git-revision", required=True)
        probe.add_argument("--cwd", type=Path, default=Path.cwd())
        probe.add_argument("--expected-base", required=True)
        probe.add_argument("--task", required=True)
        probe.add_argument("--codex-home", type=Path)
        probe.add_argument("--profile", default="normal")
        probe.add_argument("--session", default="auto")
        probe.add_argument("--pane", default="auto")
    run = subparsers.add_parser("run")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--cwd", type=Path, default=Path.cwd())
    run.add_argument("--task", required=True)
    run.add_argument("--codex-home", type=Path)
    run.add_argument("--profile", default="normal")
    run.add_argument("--session", default="auto")
    run.add_argument("--pane", default="auto")
    args = parser.parse_args(argv)
    if args.command == "run":
        codex_home = (args.codex_home or Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")).expanduser()
        request = SecretaryNormalRequest(
            worktree=args.cwd,
            task=args.task,
            codex_home=codex_home,
            profile=args.profile,
            session=args.session,
            pane=args.pane,
        )
        try:
            result = run_normal(request, output=args.output)
        except (OSError, RuntimeError, ValueError, LaunchBlocked) as exc:
            result = _normalize_invocation_outcome(
                invocation_id=uuid.uuid4().hex,
                returncode=1,
                payload=None,
                observation=None,
                started_at=datetime.now(timezone.utc).isoformat(),
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            result["execution"]["error"] = type(exc).__name__
            result["error"] = type(exc).__name__
            result["error_detail"] = str(exc)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 0 if result["result"]["state"] == "reported" else 2
    if args.command in {"probe", "smoke"}:
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
            result = run_probe(request, output=args.output)
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
