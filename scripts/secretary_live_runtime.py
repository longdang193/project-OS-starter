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
from collections.abc import Sequence
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
    from project_os_runtime.secretary_results import (
        NATIVE_RESULT_PRODUCER,
        NATIVE_RESULT_AUTHORITY,
        NativeResultConflictError,
        native_binding_path,
        parse_native_binding,
        native_result_path,
        parse_native_result,
        publish_native_binding,
        publish_native_result,
    )
    from project_os_runtime.lightrsi_reader import LightRSIResultReader
except ModuleNotFoundError:
    from scripts.project_os_runtime.secretary_economics import normalize_response_usage
    from scripts.project_os_runtime.secretary_receipts import (
        SOURCE_PRODUCERS,
        build_live_receipt,
        validate_live_receipt,
    )
    from scripts.project_os_runtime.secretary_results import (
        NATIVE_RESULT_PRODUCER,
        NATIVE_RESULT_AUTHORITY,
        NativeResultConflictError,
        native_binding_path,
        parse_native_binding,
        native_result_path,
        parse_native_result,
        publish_native_binding,
        publish_native_result,
    )
    from scripts.project_os_runtime.lightrsi_reader import LightRSIResultReader

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
_RUNTIME_BINDING_KEYS = ("task_id", "plan_revision", "run_id")
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
_LIGHTRSI_CLI_PATH_ENV = "LIGHTRSI_CLI_PATH"
_LIGHTRSI_NODE_ENV = "LIGHTRSI_NODE"
_LIGHTRSI_NATIVE_SESSION_ENV = "LIGHTRSI_NATIVE_SESSION_ID"
_LIGHTRSI_PRE_SUBMIT_CURSOR_ENV = "LIGHTRSI_PRE_SUBMIT_CURSOR"
_LIGHTRSI_SOURCE_FINGERPRINT_ENV = "LIGHTRSI_SOURCE_FINGERPRINT"
_LIGHTRSI_ARTIFACT_SHA256_ENV = "LIGHTRSI_ARTIFACT_SHA256"
_CODEX_NATIVE_APP_SERVER_ENV = "PROJECT_OS_CODEX_NATIVE_APP_SERVER"
_LIGHTRSI_RESULT_TIMEOUT_SECONDS = 120.0
_LIGHTRSI_RESULT_POLL_SECONDS = 0.5
_CODEX_NATIVE_HANDOFF_TIMEOUT_SECONDS = 30.0
_CODEX_NATIVE_HANDOFF_SCHEMA = "codex-native-session-handoff.v1"
_CODEX_NATIVE_HANDOFF_ACK_SCHEMA = "codex-native-session-handoff-ack.v1"
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
    native_app_server: bool = False,
    native_binding_path: Path | None = None,
    lightrsi_cli_path: Path | None = None,
    native_handoff_path: Path | None = None,
    native_handoff_ack_path: Path | None = None,
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
    if native_app_server:
        if native_binding_path is None or lightrsi_cli_path is None:
            raise ValueError("native app-server requires binding and LightRSI paths")
        command.extend([
            "--native-app-server",
            "--native-binding-path",
            str(native_binding_path),
            "--lightrsi-cli-path",
            str(lightrsi_cli_path),
        ])
    if native_handoff_path is not None or native_handoff_ack_path is not None:
        if native_handoff_path is None or native_handoff_ack_path is None:
            raise ValueError("native handoff requires both artifact paths")
        command.extend([
            "--native-handoff-path",
            str(native_handoff_path),
            "--native-handoff-ack-path",
            str(native_handoff_ack_path),
        ])
    return command


def _bound_task(request: SecretaryLaunchRequest) -> str:
    return request.task


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
    native_binding: Mapping[str, Any] | None = None,
    native_reader: LightRSIResultReader | None = None,
    native_result_output: Path | None = None,
    env: dict[str, str],
) -> dict[str, Any]:
    if isinstance(native_binding, Mapping) and native_reader is not None:
        return _observe_bound_lightrsi_result(
            request,
            payload,
            native_binding=native_binding,
            native_reader=native_reader,
            native_result_output=native_result_output,
            env=env,
        )
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
    if assignment is not None:
        assignment = dict(assignment)
        assignment.setdefault("session", session)
        assignment.setdefault("pane", pane)
        assignment.setdefault("agent_name", agent_name)
    ownership = herdr.get("ownership")
    ownership = ownership if isinstance(ownership, Mapping) else None
    assignment_id = assignment.get("assignment_id") if assignment else None
    attempt_id = assignment.get("attempt_id") if assignment else None
    if assignment is not None and not isinstance(attempt_id, str):
        return {"state": "unknown", "error": "launcher assignment identity incomplete"}
    native_boundary_captured = "pre_submit_completion_seq" in herdr
    herdr_pre_submit_completion_seq = herdr.get("pre_submit_completion_seq")
    if not native_boundary_captured and isinstance(assignment, Mapping):
        native_boundary_captured = "pre_submit_completion_seq" in assignment
        herdr_pre_submit_completion_seq = assignment.get("pre_submit_completion_seq")
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
    freshness_proven = False
    if native_boundary_captured:
        if not isinstance(anchor, Mapping):
            anchor = {}
        anchor = {**anchor, "completion_seq": herdr_pre_submit_completion_seq}
    while time.monotonic() < deadline:
        remaining = max(0.01, deadline - time.monotonic())
        snapshot = _codex_completion_snapshot(
            executable,
            session,
            agent_name,
            env=env,
            pane=pane,
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
        native_turn = _native_completed_turn(
            snapshot.get("native_completed_turn"),
            session=session,
        )
        if snapshot.get("native_completed_turn_error"):
            snapshot["observation_error"] = snapshot["native_completed_turn_error"]
            break
        if snapshot.get("native_completed_turn") is not None and native_turn is None:
            snapshot["observation_error"] = "native completed turn invalid"
            break
        freshness_anchor = anchor
        freshness_proven = _submission_freshness_proven(freshness_anchor, snapshot)
        snapshot.update({"session": session, "pane": pane, "agent_name": agent_name})
        if assignment_id is not None:
            snapshot["assignment_id"] = assignment_id
        if (
            freshness_proven
            and native_boundary_captured
            and isinstance(attempt_id, str)
            and isinstance(snapshot.get("completion_seq"), int)
        ):
            snapshot.update({
                "producer": NATIVE_RESULT_PRODUCER,
                "attempt_id": attempt_id,
                "assistant_owned": True,
                "freshness_proven": True,
            })
        semantic_content = native_turn["assistantText"] if native_turn else None
        if snapshot.get("state") in {"failed", "stopped"}:
            break
        if not native_boundary_captured and snapshot.get("state") in {"idle", "done"}:
            break
        if (
            snapshot.get("state") in {"idle", "done"}
            and freshness_proven
            and native_turn is not None
            and semantic_content
        ):
            completed = True
            break
        time.sleep(min(_CODEX_OBSERVATION_POLL_SECONDS, remaining))

    if not completed and snapshot.get("state") in {"idle", "done"}:
        snapshot["observation_error"] = snapshot.get("observation_error") or (
            "submission freshness not proven"
            if not freshness_proven
            else (
                "completion provenance not established"
                if snapshot.get("state") == "done"
                else "completion output not observed"
            )
        )

    native_turn = _native_completed_turn(snapshot.get("native_completed_turn"), session=session)
    native_content = native_turn["assistantText"] if native_turn else None
    if completed and native_turn is not None and native_content:
        snapshot["diagnostic_content_source"] = "native_completed_turn"

    observation = {
        key: snapshot.get(key)
        for key in (
            "state",
            "state_change_seq",
            "completion_seq",
            "content",
            "output_sha256",
            "output_chars",
            "observation_error",
            "producer",
            "content_source",
            "diagnostic_content_source",
        )
        if key in snapshot
    }
    observation.update({"session": session, "pane": pane, "agent_name": agent_name})
    if assignment_id is not None:
        observation["assignment_id"] = assignment_id
    if attempt_id is not None:
        observation["attempt_id"] = attempt_id
    observation["pre_submit_completion_seq"] = herdr_pre_submit_completion_seq
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


def _observe_bound_lightrsi_result(
    request: SecretaryLaunchRequest | SecretaryNormalRequest,
    payload: Mapping[str, Any],
    *,
    native_binding: Mapping[str, Any],
    native_reader: LightRSIResultReader,
    native_result_output: Path | None,
    env: dict[str, str],
) -> dict[str, Any]:
    herdr = payload.get("herdr")
    assignment = payload.get("assignment")
    if not isinstance(herdr, Mapping) or not isinstance(assignment, Mapping):
        return {"state": "unknown", "observation_error": "native binding context missing"}
    executable = herdr.get("executable")
    transport_session = herdr.get("session")
    pane = herdr.get("pane")
    agent_name = herdr.get("agent_name")
    native_session_id = native_binding.get("native_session_id")
    after_cursor = native_binding.get("pre_submit_cursor")
    attempt_id = native_binding.get("attempt_id")
    request_id = native_binding.get("native_request_id") or assignment.get("native_request_id")
    turn_id = native_binding.get("native_turn_id") or assignment.get("native_turn_id")
    if not all(isinstance(value, str) and value.strip() for value in (
        executable, transport_session, pane, agent_name, native_session_id, after_cursor, attempt_id,
    )):
        return {"state": "unknown", "observation_error": "native binding identity incomplete"}

    deadline = time.monotonic() + _LIGHTRSI_RESULT_TIMEOUT_SECONDS
    native_result: Mapping[str, Any] | None = None
    terminal_error: str | None = None
    while time.monotonic() < deadline:
        try:
            candidate = native_reader.read(
                session_id=native_session_id,
                after_cursor=after_cursor,
                request_id=request_id if isinstance(request_id, str) else None,
                turn_id=turn_id if isinstance(turn_id, str) else None,
            )
        except Exception as exc:
            terminal_error = f"LightRSI reader failed: {type(exc).__name__}"
            break
        state = candidate.get("state") if isinstance(candidate, Mapping) else None
        if state == "completed":
            native_result = candidate
            break
        if state in {"unavailable", "conflict"}:
            reason = candidate.get("reason") if isinstance(candidate, Mapping) else None
            terminal_error = f"LightRSI result {state}: {reason or 'unknown'}"
            break
        if state != "pending":
            terminal_error = "LightRSI reader returned an invalid state"
            break
        time.sleep(min(_LIGHTRSI_RESULT_POLL_SECONDS, max(0.01, deadline - time.monotonic())))
    if native_result is None and terminal_error is None:
        terminal_error = "LightRSI result wait timed out"

    observation: dict[str, Any] = {
        "state": "done" if native_result is not None else "unknown",
        "session": transport_session,
        "pane": pane,
        "agent_name": agent_name,
        "attempt_id": attempt_id,
        "native_session_id": native_session_id,
        "pre_submit_cursor": after_cursor,
        "freshness_proven": native_result is not None,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }
    if terminal_error:
        observation["observation_error"] = terminal_error

    publication: Mapping[str, Any] | None = None
    if native_result is not None and native_result_output is not None:
        native_source: dict[str, Any] = {
            "schema": "secretary-native-result.v1",
            "producer": NATIVE_RESULT_PRODUCER,
            "attempt_id": attempt_id,
            "session": transport_session,
            "pane": pane,
            "agent_name": agent_name,
            "native_authority": NATIVE_RESULT_AUTHORITY,
            "native_session_id": native_result["sessionId"],
            "native_turn_id": native_result["turnId"],
            "turn_seq": native_result["turnSeq"],
            "semantic_complete": native_result["semanticComplete"],
            "semantic_content": native_result["content"],
            "freshness_proven": True,
            "assistant_owned": True,
            "content_source": "lightrsi_completed_turn",
            "observed_at": observation["observed_at"],
        }
        for source_key, result_key in (("requestId", "native_request_id"), ("responseId", "native_response_id")):
            if native_result.get(source_key):
                native_source[result_key] = native_result[source_key]
        assignment_id = assignment.get("assignment_id")
        if isinstance(assignment_id, str) and assignment_id.strip():
            native_source["assignment_id"] = assignment_id
        try:
            publication = publish_native_result(native_result_output, native_source)
            persisted = parse_native_result(native_result_output, attempt_id=attempt_id)
            if persisted.get("state") != "confirmed":
                raise ValueError("native result read-back unavailable")
            if persisted.get("native_session_id") != native_source["native_session_id"]:
                raise ValueError("native result native session mismatch")
            if persisted.get("native_turn_id") != native_source["native_turn_id"]:
                raise ValueError("native result native turn mismatch")
            observation.update({
                "semantic_content": persisted["semantic_content"],
                "assistant_owned": True,
                "producer": persisted["producer"],
                "content_source": persisted["content_source"],
                "native_authority": persisted["native_authority"],
                "native_turn_id": persisted["native_turn_id"],
                "native_request_id": persisted.get("native_request_id"),
                "native_response_id": persisted.get("native_response_id"),
                "turn_seq": persisted["turn_seq"],
                "semantic_complete": persisted["semantic_complete"],
                "result_reference": persisted["result_reference"],
                "source_digest": publication["digest"],
                "publication": publication,
            })
        except (OSError, ValueError, KeyError, NativeResultConflictError) as exc:
            observation.pop("semantic_content", None)
            observation["state"] = "unknown"
            observation["observation_error"] = f"native result publication failed: {type(exc).__name__}"

    if payload.get("transport") == "codex-app-server" or herdr.get("transport") == "codex-app-server":
        observation["cleanup"] = {"state": "not_required", "reason": "codex-app-server owns the native process"}
    elif observation["state"] in {"done", "unknown"}:
        observation["cleanup"] = _release_codex_agent(
            executable,
            transport_session,
            agent_name,
            pane,
            env=env,
        )
    else:
        observation["cleanup"] = {"state": "not_attempted"}
    return observation


def _submission_freshness_proven(
    anchor: Mapping[str, Any] | None,
    snapshot: Mapping[str, Any],
) -> bool:
    if not isinstance(anchor, Mapping):
        return False
    anchor_completion_seq = anchor.get("completion_seq")
    snapshot_completion_seq = snapshot.get("completion_seq")
    if "completion_seq" in anchor or "completion_seq" in snapshot:
        if anchor_completion_seq is None:
            return isinstance(snapshot_completion_seq, int) and snapshot_completion_seq >= 0
        return (
            isinstance(anchor_completion_seq, int)
            and isinstance(snapshot_completion_seq, int)
            and snapshot_completion_seq > anchor_completion_seq
        )
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
        and not observation.get("observation_error")
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


def _launcher_attempt_id(payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    values = {
        str(value).strip()
        for source in (
            payload.get("assignment"),
            payload.get("registry_launcher"),
            payload.get("secretary_runtime"),
        )
        if isinstance(source, Mapping)
        for value in (source.get("attempt_id"),)
        if isinstance(value, str) and value.strip()
    }
    return next(iter(values)) if len(values) == 1 else None


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
    attempt_id = _launcher_attempt_id({"assignment": assignment, "secretary_runtime": runtime})
    if attempt_id is None or runtime.get("attempt_id") != attempt_id:
        return False
    return True


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
    attempt_id = _launcher_attempt_id({"registry_launcher": registry, "secretary_runtime": runtime})
    if attempt_id is None or registry.get("attempt_id") != attempt_id or runtime.get("attempt_id") != attempt_id:
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
        "attempt_id",
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
    attempt_id: str | None,
) -> dict[str, Any] | None:
    if not isinstance(runtime, Mapping) or not isinstance(attempt_id, str) or not attempt_id.strip():
        return None
    binding = {
        "pair_id": request.run_id,
        "arm": "candidate",
        "run_id": request.run_id,
        "attempt_id": attempt_id,
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
    attempt_id = _launcher_attempt_id(payload)
    if attempt_id is None:
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
        "attempt_id": attempt_id,
    }
    identity_fields = _RUNTIME_BINDING_KEYS + (
        "attempt_id", "repository_identity", "plan_identity", "git_revision", "worktree",
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
    validated = _validated_runtime_receipt(request, existing, attempt_id)
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
    observed_attempt_id = _launcher_attempt_id(payload)
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
    if observed_attempt_id is not None:
        expected_values["attempt_id"] = observed_attempt_id
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
        and _validated_runtime_receipt(request, structured_binding, observed_attempt_id) is not None
    )
    observed_metrics = structured_binding.get("metrics") if isinstance(structured_binding, Mapping) else None
    failure_kind = _launcher_failure_kind(safe_assignment)
    return {
        "schema_version": "secretary-live-runtime-v1",
        "evidence_provenance": "live-attributed" if live_attributed else "capability-probe",
        "provider": request.provider,
        "task_id": request.task_id,
        "plan_revision": request.plan_revision,
        "attempt_id": observed_attempt_id,
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
    attempt_id = _safe_text(result.get("attempt_id"))
    structured_runtime = runtime_identity.get("secretary_runtime")
    if attempt_id is None and isinstance(structured_runtime, Mapping):
        attempt_id = _safe_text(structured_runtime.get("attempt_id"))
    if attempt_id is None:
        raise RuntimeError("live Secretary receipt missing launcher attempt identity")
    binding = {
        "pair_id": request.run_id,
        "arm": "candidate",
        "run_id": request.run_id,
        "attempt_id": attempt_id,
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


def canonical_resource_inventory(
    resources: Sequence[Mapping[str, Any]],
    *,
    attempt_id: str | None = None,
) -> dict[str, Any]:
    """Deduplicate attempt-bound resource observations and fail closed on conflict."""

    entries: dict[str, dict[str, Any]] = {}
    invalid = False
    for resource in resources:
        if not isinstance(resource, Mapping):
            invalid = True
            continue
        kind = _safe_text(resource.get("kind"))
        identity = resource.get("identity")
        state = _safe_text(resource.get("state"))
        if kind is None or identity is None or state is None:
            invalid = True
            continue
        observed_attempt = resource.get("attempt_id")
        if attempt_id is not None and observed_attempt not in (None, attempt_id):
            invalid = True
        normalized = dict(resource)
        if attempt_id is not None:
            normalized["attempt_id"] = attempt_id
        identity_key = json.dumps(identity, sort_keys=True, separators=(",", ":"), default=str)
        key = f"{kind}:{identity_key}"
        previous = entries.get(key)
        if previous is None:
            entries[key] = normalized
            continue
        comparable = {name: value for name, value in previous.items() if name not in {"state", "authority"}}
        current_comparable = {name: value for name, value in normalized.items() if name not in {"state", "authority"}}
        if comparable != current_comparable or previous.get("state") != normalized.get("state"):
            invalid = True
            previous["state"] = "quarantined"
            normalized["state"] = "quarantined"
        entries[key] = normalized
    ordered = [entries[key] for key in sorted(entries)]
    if invalid:
        for item in ordered:
            item["state"] = "quarantined"
    unresolved = invalid or any(
        item.get("state") not in {"removed", "already_absent", "settled"}
        for item in ordered
    )
    if not ordered:
        state = "unknown"
    elif unresolved:
        state = "quarantined"
    else:
        state = "settled"
    return {
        "schema": "secretary-resource-inventory/v1",
        "attempt_id": attempt_id,
        "resources": ordered,
        "state": state,
        "reuse_blocked": state != "settled",
        "recovery_required": state != "settled",
    }


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


def _native_completed_turn(
    value: object,
    *,
    session: str,
) -> dict[str, str] | None:
    if not isinstance(value, Mapping) or value.get("kind") != "completed":
        return None
    if value.get("authority") != NATIVE_RESULT_AUTHORITY:
        return None
    if value.get("toolCallContinuation") is True:
        return None
    session_id = value.get("sessionId")
    turn_id = value.get("turnId")
    assistant_text = _safe_semantic_result_value(value.get("assistantText"), allow_long=True)
    if (
        not isinstance(session_id, str)
        or not session_id.strip()
        or session_id != session
        or not isinstance(turn_id, str)
        or not turn_id.strip()
        or not assistant_text
    ):
        return None
    normalized = {
        "kind": "completed",
        "authority": NATIVE_RESULT_AUTHORITY,
        "sessionId": session_id.strip(),
        "turnId": turn_id.strip(),
        "assistantText": assistant_text,
    }
    for key in ("requestId", "responseId"):
        optional = value.get(key)
        if optional is not None:
            if not isinstance(optional, str) or not optional.strip():
                return None
            normalized[key] = optional.strip()
    return normalized


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


def _result_source_content(source: Mapping[str, Any]) -> str | None:
    _, content = _result_evidence(source)
    return content


def _snapshot_result_content(source: Mapping[str, Any]) -> str | None:
    return _safe_semantic_result_value(source.get("semantic_content"), allow_long=True)


def _select_authoritative_result_source(
    task_result: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    assignment: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, str | None]:
    task_result_owned = _result_source_authoritative(task_result, assignment)
    snapshot_owned = _result_source_authoritative(
        snapshot,
        assignment,
        require_assistant_provenance=True,
    )
    task_result_content = _result_source_content(task_result) if task_result_owned else None
    snapshot_content = _snapshot_result_content(snapshot) if snapshot_owned else None
    if snapshot_owned and snapshot_content:
        return snapshot, snapshot_content
    if task_result_owned and task_result_content:
        return task_result, task_result_content
    if task_result_owned:
        return task_result, task_result_content
    if snapshot_owned:
        return snapshot, snapshot_content
    return None, None


def _result_source_authoritative(
    source: object,
    assignment: Mapping[str, Any] | None,
    *,
    require_assistant_provenance: bool = False,
) -> bool:
    if not isinstance(source, Mapping):
        return False
    if not isinstance(assignment, Mapping):
        return False
    producer = source.get("producer")
    if producer == NATIVE_RESULT_PRODUCER:
        expected_context = {
            key: assignment.get(key)
            for key in ("session", "pane", "agent_name")
        }
        if any(
            not isinstance(value, str) or not value.strip()
            for value in expected_context.values()
        ):
            return False
        if any(source.get(key) != value for key, value in expected_context.items()):
            return False
        expected_assignment_id = assignment.get("assignment_id")
        if expected_assignment_id is not None and source.get("assignment_id") != expected_assignment_id:
            return False
        expected_attempt_id = assignment.get("attempt_id")
        if source.get("native_authority") != NATIVE_RESULT_AUTHORITY:
            return False
        if source.get("attempt_id") != expected_attempt_id or not isinstance(source.get("attempt_id"), str):
            return False
        if source.get("freshness_proven") is not True or source.get("assistant_owned") is not True:
            return False
        if source.get("content_source") == "lightrsi_completed_turn":
            turn_seq = source.get("turn_seq")
            native_session = source.get("native_session_id")
            return (
                isinstance(native_session, str)
                and bool(native_session.strip())
                and isinstance(turn_seq, int)
                and not isinstance(turn_seq, bool)
                and turn_seq > 0
                and source.get("native_turn_id") == f"{native_session}:t{turn_seq}"
                and source.get("semantic_complete") is True
                and bool(_result_evidence(source)[0] or _result_evidence(source)[1])
            )
        return False
    assignment_identity = {
        key: assignment.get(key)
        for key in ("assignment_id", "attempt_id")
    }
    source_identity = {
        key: source.get(key)
        for key in ("assignment_id", "attempt_id")
    }
    if any(
        not isinstance(value, str) or not value.strip()
        for value in (*assignment_identity.values(), *source_identity.values())
    ):
        return False
    if source_identity != assignment_identity:
        return False
    producer = source.get("producer")
    if not isinstance(producer, str) or producer not in _ACCEPTED_RESULT_PRODUCERS:
        return False
    if "assistant_owned" in source and source.get("assistant_owned") is not True:
        return False
    if require_assistant_provenance and source.get("assistant_owned") is not True and not any(
        source.get(key) not in (None, "")
        for key in ("result_id", "result_reference", "completion_id")
    ):
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
    result_status: str | None = None

    reference: str | None = None
    content: str | None = None
    observation_reportable = observed.get("state") in {"idle", "done"}
    observed_evidence: Mapping[str, Any] = (
        {key: value for key, value in observed.items() if key != "content"}
        if observation_reportable
        else {}
    )
    authoritative_task_result = (
        task_result if _result_source_authoritative(task_result, assignment) else {}
    )
    authoritative_sources: list[tuple[Mapping[str, Any], str | None, str | None]] = []
    for source in (task_result, observed_evidence):
        if not _result_source_authoritative(
            source,
            assignment,
            require_assistant_provenance=source is observed_evidence,
        ):
            continue
        reference, source_content = _result_evidence(source)
        authoritative_sources.append((source, reference, source_content))

    evidence_conflict = False
    selected_source: Mapping[str, Any] | None = None
    if authoritative_sources:
        for index, (_, left_reference, left_content) in enumerate(authoritative_sources):
            for _, right_reference, right_content in authoritative_sources[index + 1:]:
                shared_evidence = False
                if left_reference and right_reference:
                    shared_evidence = True
                    if left_reference != right_reference:
                        evidence_conflict = True
                if left_content and right_content:
                    shared_evidence = True
                    if left_content != right_content:
                        evidence_conflict = True
                if not shared_evidence:
                    evidence_conflict = True
        if not evidence_conflict:
            selected_source, reference, content = max(
                authoritative_sources,
                key=lambda item: int(item[1] is not None) + int(item[2] is not None),
            )

    if selected_source is not None:
        result_status = {
            "reported_completed": "completed",
            "reported_failed": "failed",
        }.get(selected_source.get("state"))

    if authoritative_task_result.get("state") == "reported_failed":
        result_status = "failed"
    ambiguous = bool(authoritative_task_result.get("ambiguous")) or _identity_conflict(
        authoritative_task_result,
        assignment,
    )
    if evidence_conflict:
        ambiguous = True
    if result_status is None and (reference or content) and not ambiguous:
        result_status = "failed" if observed.get("state") == "failed" else "completed"
    if ambiguous:
        semantic_outcome = {
            "state": "ambiguous",
            "status": None,
            "reference": None,
            "content": None,
        }
    elif result_status is not None and (reference or content):
        semantic_outcome = {
            "state": "reported",
            "status": result_status,
            "reference": reference,
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
    attempt_id = assignment.get("attempt_id")
    resource_inventory = canonical_resource_inventory(
        owned_resources,
        attempt_id=attempt_id if isinstance(attempt_id, str) else None,
    )
    if resource_inventory["resources"]:
        resource = {
            "state": resource_inventory["state"],
            "reuse_blocked": resource_inventory["reuse_blocked"],
            "recovery_required": resource_inventory["recovery_required"],
        }
        owned_resources = resource_inventory["resources"]

    observability_state = (
        "available" if observed and not observed.get("observation_error") else "unavailable"
    )
    observed_cleanup_state = (
        observed_cleanup.get("state") if isinstance(observed_cleanup, Mapping) else None
    )
    observability = {
        "state": observability_state,
        "reference": reference,
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
        "resource_inventory": resource_inventory,
        "recovery_required": resource["recovery_required"],
        "observability": observability,
        "timestamps": {"started": started_at, "finished": finished_at},
    }


def _normal_managed_result_capability_available() -> bool:
    return all(callable(value) for value in (native_result_path, publish_native_result, LightRSIResultReader))


def _configured_lightrsi_reader(environment: Mapping[str, str] | None = None) -> LightRSIResultReader | None:
    values = dict(os.environ) if environment is None else dict(environment)
    configured_path = values.get(_LIGHTRSI_CLI_PATH_ENV)
    if not isinstance(configured_path, str) or not configured_path.strip():
        return None
    try:
        cli_path = Path(configured_path).expanduser()
        if not cli_path.is_absolute():
            return None
        return LightRSIResultReader(
            cli_path,
            timeout_seconds=5.0,
            node_executable=values.get(_LIGHTRSI_NODE_ENV, "node"),
            environment=values,
        )
    except (OSError, ValueError):
        return None


def _run_normal_via_native_app_server(
    request: SecretaryNormalRequest,
    *,
    output: Path,
    environment: Mapping[str, str],
    native_reader: LightRSIResultReader,
    invocation_id: str,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    process: subprocess.Popen[str] | None = None
    payload: Mapping[str, Any] | None = None
    observation: Mapping[str, Any] = {}
    preflight: dict[str, Any] = {"transport": "codex-app-server"}
    try:
        worktree, expected_base = _read_only_git_anchor(request.worktree)
        codex_executable = environment.get("CODEX_EXECUTABLE") or shutil.which("codex")
        if not isinstance(codex_executable, str) or not codex_executable.strip():
            raise LaunchBlocked("Required executable unavailable on PATH: codex")
        binding_path = native_binding_path(output)
        if binding_path.exists():
            raise LaunchBlocked("Codex app-server native binding already exists")
        command = build_normal_launcher_command(
            replace(request, worktree=worktree),
            expected_base=expected_base,
            native_app_server=True,
            native_binding_path=binding_path,
            lightrsi_cli_path=native_reader.cli_path,
        )
        process = subprocess.Popen(
            command,
            cwd=worktree,
            env=dict(environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        native_binding = _wait_for_native_binding(binding_path, process)
        stdout, stderr = process.communicate()
        completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        payloads = _json_payloads(completed.stdout) + _json_payloads(completed.stderr)
        payload = select_launcher_payload(payloads) if payloads else None
        if completed.returncode != 0 or not isinstance(payload, Mapping):
            raise LaunchBlocked("Codex app-server did not return a successful assignment")
        assignment = payload.get("assignment")
        if not isinstance(assignment, Mapping):
            raise LaunchBlocked("Codex app-server assignment evidence is missing")
        if assignment.get("attempt_id") != native_binding.get("attempt_id"):
            raise LaunchBlocked("Codex app-server binding and assignment attempts do not match")
        bound = dict(native_binding)
        for key in ("native_request_id", "native_turn_id"):
            value = assignment.get(key)
            if isinstance(value, str) and value.strip():
                bound[key] = value
        observation = _observe_submitted_codex(
            replace(request, worktree=worktree),
            payload,
            native_binding=bound,
            native_reader=native_reader,
            native_result_output=native_result_path(output),
            env=dict(environment),
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
        preflight["error"] = str(exc)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
    result["preflight"] = preflight
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _native_binding_for_submission(
    *,
    attempt_id: str,
    launch_request: SecretaryNormalRequest,
    output: Path,
    environment: Mapping[str, str],
    reader: LightRSIResultReader,
    handoff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if handoff is not None:
        if handoff.get("schema") != _CODEX_NATIVE_HANDOFF_SCHEMA:
            raise LaunchBlocked("Codex native session handoff schema mismatch")
        cursor = handoff.get("pre_submit_cursor")
        native_session_id = handoff.get("native_session_id")
        if not isinstance(cursor, str) or not cursor.strip():
            raise LaunchBlocked("Codex native session handoff cursor unavailable")
        if not isinstance(native_session_id, str) or not native_session_id.strip():
            raise LaunchBlocked("Codex native session handoff session unavailable")
    else:
        cursor = environment.get(_LIGHTRSI_PRE_SUBMIT_CURSOR_ENV)
        if not isinstance(cursor, str) or not cursor.strip():
            raise LaunchBlocked("LightRSI pre-submit cursor unavailable")
        native_session_id = environment.get(_LIGHTRSI_NATIVE_SESSION_ENV)
        if not isinstance(native_session_id, str) or not native_session_id.strip():
            raise LaunchBlocked("LightRSI native session unavailable")
    binding: dict[str, Any] = {
        "schema": "secretary-native-binding.v1",
        "attempt_id": attempt_id,
        "native_session_id": native_session_id,
        "pre_submit_cursor": cursor,
        "lightrsi_cli_path": str(reader.cli_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "transport": {
            "session": launch_request.session,
            "pane": launch_request.pane,
            "agent_name": "normal-secretary",
        },
    }
    source_fingerprint = environment.get(_LIGHTRSI_SOURCE_FINGERPRINT_ENV)
    if isinstance(source_fingerprint, str) and source_fingerprint.strip():
        binding["lightrsi_source_fingerprint"] = source_fingerprint
    artifact_sha256 = environment.get(_LIGHTRSI_ARTIFACT_SHA256_ENV)
    if isinstance(artifact_sha256, str) and artifact_sha256.strip():
        binding["lightrsi_artifact_sha256"] = artifact_sha256
    publish_native_binding(native_binding_path(output), binding)
    persisted = parse_native_binding(native_binding_path(output), attempt_id=attempt_id)
    if persisted.get("state") != "confirmed":
        raise LaunchBlocked("LightRSI native binding read-back unavailable")
    return persisted


def _read_native_handoff(path: Path, *, attempt_id: str | None = None) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LaunchBlocked("Codex native session handoff is invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema") != _CODEX_NATIVE_HANDOFF_SCHEMA:
        raise LaunchBlocked("Codex native session handoff schema mismatch")
    handoff_attempt_id = payload.get("attempt_id")
    if not isinstance(handoff_attempt_id, str) or not handoff_attempt_id.strip():
        raise LaunchBlocked("Codex native session handoff attempt unavailable")
    if attempt_id is not None and handoff_attempt_id != attempt_id:
        raise LaunchBlocked("Codex native session handoff attempt mismatch")
    if not isinstance(payload.get("native_session_id"), str) or not payload["native_session_id"].strip():
        raise LaunchBlocked("Codex native session handoff session unavailable")
    if not isinstance(payload.get("pre_submit_cursor"), str) or not payload["pre_submit_cursor"].strip():
        raise LaunchBlocked("Codex native session handoff cursor unavailable")
    return payload


def _wait_for_native_handoff(
    path: Path,
    process: subprocess.Popen[str],
    *,
    attempt_id: str | None = None,
) -> dict[str, Any]:
    deadline = time.monotonic() + _CODEX_NATIVE_HANDOFF_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if path.is_file():
            return _read_native_handoff(path, attempt_id=attempt_id)
        if process.poll() is not None:
            process.communicate()
            raise LaunchBlocked("Codex native session handoff was not captured before launcher exit")
        time.sleep(0.05)
    raise LaunchBlocked("Timed out waiting for Codex native session handoff")


def _wait_for_native_binding(path: Path, process: subprocess.Popen[str]) -> dict[str, Any]:
    deadline = time.monotonic() + _CODEX_NATIVE_HANDOFF_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise LaunchBlocked("Codex app-server native binding is invalid") from exc
            if not isinstance(payload, dict) or payload.get("schema") != "secretary-native-binding.v1":
                raise LaunchBlocked("Codex app-server native binding schema mismatch")
            required = ("attempt_id", "native_session_id", "pre_submit_cursor", "lightrsi_cli_path")
            if not all(isinstance(payload.get(key), str) and payload[key].strip() for key in required):
                raise LaunchBlocked("Codex app-server native binding identity incomplete")
            return payload
        if process.poll() is not None:
            raise LaunchBlocked("Codex app-server exited before native binding")
        time.sleep(0.05)
    raise LaunchBlocked("Timed out waiting for Codex app-server native binding")


def _write_native_handoff_ack(path: Path, handoff: Mapping[str, Any]) -> None:
    payload = {
        "schema": _CODEX_NATIVE_HANDOFF_ACK_SCHEMA,
        "attempt_id": handoff["attempt_id"],
        "native_session_id": handoff["native_session_id"],
        "pre_submit_cursor": handoff["pre_submit_cursor"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def run_normal(request: SecretaryNormalRequest, *, output: Path) -> dict[str, Any]:
    invocation_id = uuid.uuid4().hex
    started = datetime.now(timezone.utc).isoformat()
    if not _normal_managed_result_capability_available():
        result = _normalize_invocation_outcome(
            invocation_id=invocation_id,
            returncode=1,
            payload=None,
            observation=None,
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        result["execution"].update({"state": "blocked", "error": "BLOCKED_CAPABILITY"})
        result["failure_kind"] = "BLOCKED_CAPABILITY"
        result["capability_state"] = "BLOCKED_CAPABILITY"
        result["preflight"] = {
            "disposition": "BLOCKED_CAPABILITY",
            "reason": "native result publication interface unavailable",
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result

    worktree, expected_base = _read_only_git_anchor(request.worktree)
    request = replace(request, worktree=worktree)
    environment = dict(os.environ)
    environment["CODEX_HOME"] = str(request.codex_home.resolve())
    native_reader = _configured_lightrsi_reader(environment)
    if native_reader is None:
        raise LaunchBlocked("LightRSI reader capability unavailable")
    capability = native_reader.capability_check(
        expected_artifact_sha256=environment.get(_LIGHTRSI_ARTIFACT_SHA256_ENV)
    )
    if capability.get("state") != "ready":
        raise LaunchBlocked(f"LightRSI capability unavailable: {capability.get('reason', 'unknown')}")
    if environment.get(_CODEX_NATIVE_APP_SERVER_ENV, "").strip().lower() in {"1", "true", "yes"}:
        return _run_normal_via_native_app_server(
            request,
            output=output,
            environment=environment,
            native_reader=native_reader,
            invocation_id=invocation_id,
        )
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
    native_binding: Mapping[str, Any] | None = None
    native_handoff_path = output.with_name(f".{output.name}.{invocation_id}.native-handoff.json")
    native_handoff_ack_path = output.with_name(f".{output.name}.{invocation_id}.native-handoff-ack.json")
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
        completed_process = subprocess.Popen(
            build_normal_launcher_command(
                launch_request,
                expected_base=expected_base,
                native_handoff_path=native_handoff_path,
                native_handoff_ack_path=native_handoff_ack_path,
            ),
            cwd=launch_request.worktree,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            native_handoff = _wait_for_native_handoff(
                native_handoff_path,
                completed_process,
            )
            if native_reader is not None:
                native_attempt_id = native_handoff.get("attempt_id")
                if not isinstance(native_attempt_id, str) or not native_attempt_id.strip():
                    raise LaunchBlocked("Codex native session handoff attempt unavailable")
                native_binding = _native_binding_for_submission(
                    attempt_id=native_attempt_id,
                    launch_request=launch_request,
                    output=output,
                    environment=environment,
                    reader=native_reader,
                    handoff=native_handoff,
                )
            _write_native_handoff_ack(native_handoff_ack_path, native_handoff)
            stdout, stderr = completed_process.communicate()
        except Exception:
            if completed_process.poll() is None:
                completed_process.terminate()
            stdout, stderr = completed_process.communicate(timeout=5)
            raise
        completed = subprocess.CompletedProcess(
            completed_process.args,
            completed_process.returncode,
            stdout,
            stderr,
        )
        payloads = _json_payloads(completed.stdout) + _json_payloads(completed.stderr)
        payload = select_launcher_payload(payloads) if payloads else None
        if isinstance(payload, dict):
            assignment_payload = payload.get("assignment")
            if isinstance(assignment_payload, dict):
                assignment_payload.setdefault("session", launch_request.session)
                assignment_payload.setdefault("pane", launch_request.pane)
                assignment_payload.setdefault(
                    "agent_name",
                    payload.get("herdr", {}).get("agent_name")
                    if isinstance(payload.get("herdr"), Mapping)
                    else None,
                )
        if completed.returncode == 0 and isinstance(payload, Mapping):
            observation = _observe_submitted_codex(
                launch_request,
                payload,
                pre_submit=submission_anchor,
                native_binding=native_binding,
                native_reader=native_reader,
                native_result_output=native_result_path(output),
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
        native_handoff_path.unlink(missing_ok=True)
        native_handoff_ack_path.unlink(missing_ok=True)
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
            result["owned_resources"] = _owned_resources(
                payload,
                observation,
                cleanup_state=cleanup_state,
                workspace_id=workspace_id,
                workspace_close=preflight["workspace_close"],
            )
            assignment_payload = payload.get("assignment") if isinstance(payload, Mapping) else None
            attempt_id = assignment_payload.get("attempt_id") if isinstance(assignment_payload, Mapping) else None
            resource_inventory = canonical_resource_inventory(
                result["owned_resources"],
                attempt_id=attempt_id if isinstance(attempt_id, str) else None,
            )
            if resource_inventory["resources"]:
                resource = {
                    "state": resource_inventory["state"],
                    "reuse_blocked": resource_inventory["reuse_blocked"],
                    "recovery_required": resource_inventory["recovery_required"],
                }
                result["owned_resources"] = resource_inventory["resources"]
            result["resource"] = {key: resource[key] for key in ("state", "reuse_blocked")}
            result["resource_inventory"] = resource_inventory
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
                native_result_output=native_result_path(output),
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
                result["owned_resources"] = _owned_resources(
                    payload,
                    post_submit if isinstance(post_submit, Mapping) else {},
                    cleanup_state=cleanup_state,
                    workspace_id=workspace_id,
                    workspace_close=preflight["workspace_close"],
                )
                assignment_payload = payload.get("assignment") if isinstance(payload, Mapping) else None
                attempt_id = assignment_payload.get("attempt_id") if isinstance(assignment_payload, Mapping) else None
                resource_inventory = canonical_resource_inventory(
                    result["owned_resources"],
                    attempt_id=attempt_id if isinstance(attempt_id, str) else None,
                )
                if resource_inventory["resources"]:
                    resource = {
                        "state": resource_inventory["state"],
                        "reuse_blocked": resource_inventory["reuse_blocked"],
                        "recovery_required": resource_inventory["recovery_required"],
                    }
                    result["owned_resources"] = resource_inventory["resources"]
                result["resource"] = {key: resource[key] for key in ("state", "reuse_blocked")}
                result["resource_inventory"] = resource_inventory
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
