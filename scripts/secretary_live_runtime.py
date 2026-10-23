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
import stat
import subprocess
import sys
import threading
import time
import sqlite3
import tempfile
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
    from agent_profile_registry import load_agent_profiles
    from project_os_runtime.attempt import grant_digest, normalize_runtime_grant
    from project_os_runtime.submission_gate import (
        claim_submission,
        derive_logical_operation_id,
        gate_path,
        settle_submission,
    )
    from project_os_runtime.secretary_economics import normalize_response_usage
    from project_os_runtime.secretary_receipts import (
        SOURCE_PRODUCERS,
        build_live_receipt,
        validate_live_receipt,
    )
    from project_os_runtime.secretary_results import (
        NATIVE_APP_SERVER_AUTHORITY,
        NATIVE_BINDING_SCHEMA,
        NATIVE_SUBMISSION_SCHEMA,
        NATIVE_RESULT_SCHEMA,
        NATIVE_RESULT_MAX_BYTES,
        NATIVE_RESULT_PRODUCER,
        NATIVE_RESULT_AUTHORITY,
        NativeResultConflictError,
        native_binding_path,
        native_submission_path,
        parse_native_binding,
        parse_native_submission,
        native_result_path,
        parse_native_result,
        validate_native_binding_payload,
        validate_native_submission_payload,
        validate_native_result_payload,
        publish_native_binding,
        publish_native_submission,
        publish_native_result,
        request_fingerprint,
    )
    from project_os_runtime.codex_app_server import CodexAppServerClient, NativeAppServerError
except ModuleNotFoundError:
    from scripts.agent_profile_registry import load_agent_profiles
    from scripts.project_os_runtime.attempt import grant_digest, normalize_runtime_grant
    from scripts.project_os_runtime.submission_gate import (
        claim_submission,
        derive_logical_operation_id,
        gate_path,
        settle_submission,
    )
    from scripts.project_os_runtime.secretary_economics import normalize_response_usage
    from scripts.project_os_runtime.secretary_receipts import (
        SOURCE_PRODUCERS,
        build_live_receipt,
        validate_live_receipt,
    )
    from scripts.project_os_runtime.secretary_results import (
        NATIVE_APP_SERVER_AUTHORITY,
        NATIVE_BINDING_SCHEMA,
        NATIVE_SUBMISSION_SCHEMA,
        NATIVE_RESULT_SCHEMA,
        NATIVE_RESULT_MAX_BYTES,
        NATIVE_RESULT_PRODUCER,
        NATIVE_RESULT_AUTHORITY,
        NativeResultConflictError,
        native_binding_path,
        native_submission_path,
        parse_native_binding,
        parse_native_submission,
        native_result_path,
        parse_native_result,
        validate_native_binding_payload,
        validate_native_submission_payload,
        validate_native_result_payload,
        publish_native_binding,
        publish_native_submission,
        publish_native_result,
        request_fingerprint,
    )
    from scripts.project_os_runtime.codex_app_server import CodexAppServerClient, NativeAppServerError

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
    "pre_submit_completion_seq",
    "pre_submit_state_change_seq",
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
_WORKSPACE_STATUS_MAX_BYTES = 4 * 1024 * 1024
_WORKSPACE_TRACKED_DIFF_MAX_BYTES = 16 * 1024 * 1024
_WORKSPACE_UNTRACKED_ENTRY_MAX = 4096
_WORKSPACE_UNTRACKED_FILE_MAX_BYTES = 8 * 1024 * 1024
_WORKSPACE_UNTRACKED_TOTAL_MAX_BYTES = 64 * 1024 * 1024
_WORKSPACE_GIT_COMMAND_TIMEOUT_SECONDS = 5.0
_WORKSPACE_GIT_READ_CHUNK_BYTES = 64 * 1024
_CODEX_OBSERVATION_POLL_SECONDS = 0.5
_PROVIDER_TELEMETRY_LOOKBACK_SECONDS = 0.0
_HERDR_SERVER_START_TIMEOUT_SECONDS = 10.0
_HERDR_PREFLIGHT_RECHECK_SECONDS = 0.25
_SAFE_SOURCE_DIGEST = re.compile(r"[0-9a-f]{64}")
_NOT_APPLICABLE_RUNTIME_GRANT = "not_applicable"
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
        elif key in {"pre_submit_completion_seq", "pre_submit_state_change_seq"}:
            if type(value) is int and value >= 0:
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
    logical_operation_id: str | None = None

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
        if self.logical_operation_id is not None:
            _required_text(self.logical_operation_id, "logical_operation_id")


@dataclass(frozen=True)
class SecretaryNormalRequest:
    worktree: Path
    task: str
    codex_home: Path
    profile: str = "normal"
    repository_identity: str = ""
    git_revision: str = ""
    model_identity: str = ""
    runtime_grant_digest: str = ""
    logical_operation_id: str | None = None
    resume: bool = False

    def __post_init__(self) -> None:
        for field in ("task", "profile"):
            _required_text(getattr(self, field), field)
        for field in ("repository_identity", "git_revision", "model_identity", "runtime_grant_digest"):
            if not isinstance(getattr(self, field), str):
                raise ValueError(f"{field} must be text")
        if self.logical_operation_id is not None:
            _required_text(self.logical_operation_id, "logical_operation_id")


@dataclass(frozen=True)
class ResolvedSecretaryRequest:
    request: SecretaryNormalRequest
    task_sha256: str
    repository_identity: str
    git_revision: str
    execution_role: str
    provider_identity: str
    model_identity: str
    runtime_grant_digest: str
    logical_operation_id: str
    request_fingerprint: str
    workspace_dirty: bool = False
    workspace_change_digest: str | None = None
    unknown_fields: tuple[str, ...] = ()

    @property
    def reuse_allowed(self) -> bool:
        return not self.unknown_fields


def _canonical_repository_identity(repository_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository_root), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, TypeError, ValueError, AttributeError):
        return None
    remote = completed.stdout.strip() if completed.returncode == 0 else ""
    if remote:
        return remote.replace("\\", "/").rstrip("/")
    try:
        common_dir = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, TypeError, ValueError, AttributeError):
        return None
    if common_dir.returncode == 0 and common_dir.stdout.strip():
        return str((repository_root / common_dir.stdout.strip()).resolve())
    return None


def _resolve_normal_request(
    request: SecretaryNormalRequest,
    environment: Mapping[str, str] | None = None,
    *,
    output: Path | None = None,
    git_anchor: tuple[Path, str] | None = None,
) -> ResolvedSecretaryRequest:
    repository_root, git_revision = git_anchor or _read_only_git_anchor(request.worktree)
    if output is not None:
        _reject_tracked_runtime_paths(repository_root, output)
        workspace_dirty, workspace_change_digest, workspace_unknown_fields = _read_only_workspace_identity(
            repository_root,
            output,
        )
    else:
        workspace_dirty, workspace_change_digest, workspace_unknown_fields = _read_only_workspace_identity(repository_root)
    canonical_repository_identity = _canonical_repository_identity(repository_root)
    repository_identity = canonical_repository_identity or request.repository_identity.strip()
    resolved_git_revision = git_revision or request.git_revision.strip()
    provider_identity = SECRETARY_PROVIDER
    model_identity = request.model_identity.strip()
    if not model_identity:
        profile_path = repository_root / "agents" / f"{request.profile}.toml"
        try:
            profile = tomllib.loads(profile_path.read_text(encoding="utf-8")) if profile_path.is_file() else {}
        except (OSError, tomllib.TOMLDecodeError):
            profile = {}
        if isinstance(profile, Mapping) and profile.get("herdr_only") is True:
            profiles = load_agent_profiles(
                repository_root / "agents",
                runtime_provider=provider_identity,
            )
            selected_profile = profiles.get(request.profile)
            if selected_profile is None or selected_profile.herdr_only:
                raise LaunchBlocked(
                    f"Native Secretary cannot launch herdr_only profile: {request.profile}"
                )
        profile_provider = profile.get("model_provider") if isinstance(profile, Mapping) else None
        if profile_provider is not None and profile_provider != provider_identity:
            raise ValueError(f"Secretary profile must use {provider_identity}")
        profile_model = profile.get("model") if isinstance(profile, Mapping) else None
        if isinstance(profile_model, str) and profile_model.strip():
            model_identity = profile_model.strip()
    runtime_grant_digest = request.runtime_grant_digest.strip() or _NOT_APPLICABLE_RUNTIME_GRANT
    unknown_fields = tuple(
        field
        for field, value in (
            ("repository_identity", repository_identity),
            ("git_revision", resolved_git_revision),
            ("model_identity", model_identity),
        )
        if not value
    ) + workspace_unknown_fields
    repository_identity_value = repository_identity or "<unknown:repository_identity>"
    git_revision_value = resolved_git_revision or "<unknown:git_revision>"
    model_identity_value = model_identity or "<unknown:model_identity>"
    runtime_grant_value = runtime_grant_digest
    task_sha256 = hashlib.sha256(request.task.encode("utf-8")).hexdigest()
    operation_id = request.logical_operation_id or uuid.uuid4().hex
    resolved_request = replace(
        request,
        worktree=repository_root,
        repository_identity=repository_identity_value,
        git_revision=git_revision_value,
        model_identity=model_identity_value,
        runtime_grant_digest=runtime_grant_value,
        logical_operation_id=operation_id,
    )
    fingerprint_fields: dict[str, object] = {
            "task_sha256": task_sha256,
            "repository_identity": repository_identity_value,
            "git_revision": git_revision_value,
            "execution_role": "secretary",
            "provider_identity": provider_identity,
            "model_identity": model_identity_value,
            "runtime_grant_digest": runtime_grant_value,
        }
    if workspace_change_digest is not None:
        fingerprint_fields["workspace_change_digest"] = workspace_change_digest
    fingerprint = request_fingerprint(fingerprint_fields)
    return ResolvedSecretaryRequest(
        request=resolved_request,
        task_sha256=task_sha256,
        repository_identity=repository_identity_value,
        git_revision=git_revision_value,
        execution_role="secretary",
        provider_identity=provider_identity,
        model_identity=model_identity_value,
        runtime_grant_digest=runtime_grant_value,
        logical_operation_id=operation_id,
        request_fingerprint=fingerprint,
        workspace_dirty=workspace_dirty,
        workspace_change_digest=workspace_change_digest,
        unknown_fields=unknown_fields,
    )


def _require_attempt_budget(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise NativeAppServerError(
            "Secretary native attempt deadline exhausted.", failure_kind="NATIVE_RESULT_TIMEOUT"
        )


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
    if request.logical_operation_id is not None:
        command.extend(["--logical-operation-id", request.logical_operation_id])
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
    initial_snapshot: Mapping[str, Any] | None = None,
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
    herdr_pre_submit_completion_seq = herdr.get("pre_submit_completion_seq")
    native_boundary_captured = (
        type(herdr_pre_submit_completion_seq) is int
        and herdr_pre_submit_completion_seq >= 0
    )
    if not native_boundary_captured and isinstance(assignment, Mapping):
        assignment_completion_seq = assignment.get("pre_submit_completion_seq")
        if type(assignment_completion_seq) is int and assignment_completion_seq >= 0:
            native_boundary_captured = True
            herdr_pre_submit_completion_seq = assignment_completion_seq
        else:
            herdr_pre_submit_completion_seq = None
    herdr_pre_submit_state_change_seq = herdr.get("pre_submit_state_change_seq")
    state_boundary_captured = (
        type(herdr_pre_submit_state_change_seq) is int
        and herdr_pre_submit_state_change_seq >= 0
    )
    if not state_boundary_captured and isinstance(assignment, Mapping):
        assignment_state_change_seq = assignment.get("pre_submit_state_change_seq")
        if type(assignment_state_change_seq) is int and assignment_state_change_seq >= 0:
            state_boundary_captured = True
            herdr_pre_submit_state_change_seq = assignment_state_change_seq
        else:
            herdr_pre_submit_state_change_seq = None
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

    initial_elapsed_ms = initial_snapshot.get("observation_elapsed_ms", 0) if isinstance(initial_snapshot, Mapping) else 0
    if not isinstance(initial_elapsed_ms, (int, float)) or isinstance(initial_elapsed_ms, bool) or initial_elapsed_ms < 0:
        initial_elapsed_ms = 0
    observation_budget = max(
        0.01,
        _CODEX_OBSERVATION_TIMEOUT_SECONDS - (float(initial_elapsed_ms) / 1000),
    )
    deadline = time.monotonic() + observation_budget
    snapshot: dict[str, Any] = {
        "state": "unknown",
        "observation_error": "completion observation deadline expired",
    }
    completed = False
    freshness_proven = False
    initial_snapshot_consumed = False
    if native_boundary_captured:
        if not isinstance(anchor, Mapping):
            anchor = {}
        anchor = {**anchor, "completion_seq": herdr_pre_submit_completion_seq}
    if state_boundary_captured:
        if not isinstance(anchor, Mapping):
            anchor = {}
        anchor = {**anchor, "state_change_seq": herdr_pre_submit_state_change_seq}
    while time.monotonic() < deadline:
        remaining = max(0.01, deadline - time.monotonic())
        if not initial_snapshot_consumed and isinstance(initial_snapshot, Mapping):
            snapshot = dict(initial_snapshot)
            initial_snapshot_consumed = True
        else:
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
        if freshness_proven and isinstance(attempt_id, str):
            snapshot.update({
                "attempt_id": attempt_id,
                "freshness_proven": True,
            })
            snapshot.setdefault("producer", NATIVE_RESULT_PRODUCER)
            snapshot.setdefault("assistant_owned", True)
        semantic_content = native_turn["assistantText"] if native_turn else None
        if snapshot.get("state") in {"failed", "stopped"}:
            break
        if not (native_boundary_captured or state_boundary_captured) and snapshot.get("state") in {"idle", "done"}:
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
            "observation_elapsed_ms",
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
    observation["pre_submit_state_change_seq"] = herdr_pre_submit_state_change_seq
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
    anchor_completion_seq = anchor.get("completion_seq")
    snapshot_completion_seq = snapshot.get("completion_seq")
    if (
        type(anchor_completion_seq) is int
        and anchor_completion_seq >= 0
        and type(snapshot_completion_seq) is int
        and snapshot_completion_seq >= 0
    ):
        return snapshot_completion_seq > anchor_completion_seq
    anchor_state_change_seq = anchor.get("state_change_seq")
    snapshot_state_change_seq = snapshot.get("state_change_seq")
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
    if (
        type(anchor_state_change_seq) is int
        and anchor_state_change_seq >= 0
        and type(snapshot_state_change_seq) is int
        and snapshot_state_change_seq >= 0
    ):
        return snapshot_state_change_seq > anchor_state_change_seq
    if "completion_seq" in anchor or "completion_seq" in snapshot:
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
    active_provider = config.get("model_provider")
    if active_provider != SECRETARY_PROVIDER:
        raise RuntimeError(f"configured Codex active provider must be {SECRETARY_PROVIDER}")
    providers = config.get("model_providers")
    if (
        not isinstance(providers, Mapping)
        or not isinstance(providers.get(SECRETARY_PROVIDER), Mapping)
    ):
        raise RuntimeError(f"configured Codex provider {SECRETARY_PROVIDER} unavailable")
    return active_provider


def _configured_model(request: SecretaryLaunchRequest) -> str:
    profile_path = request.worktree / "agents" / f"{request.profile}.toml"
    if not profile_path.is_file():
        return "unknown"
    profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    if profile.get("model_provider") != SECRETARY_PROVIDER:
        raise RuntimeError(f"Secretary profile must use {SECRETARY_PROVIDER}")
    model = profile.get("model")
    return model.strip() if isinstance(model, str) and model.strip() else "unknown"


def _probe_operation_id(request: SecretaryLaunchRequest) -> str:
    return request.logical_operation_id or derive_logical_operation_id(
        task_id=request.task_id,
        plan_revision=request.plan_revision,
        run_id=request.run_id,
    )


def _probe_submission_binding(
    request: SecretaryLaunchRequest,
    *,
    configured_model: str,
) -> dict[str, str]:
    runtime_grant = normalize_runtime_grant(executor="codex")
    return {
        "task_sha256": hashlib.sha256(request.task.encode("utf-8")).hexdigest(),
        "repository_identity": request.repository_identity,
        "plan_identity": request.plan_identity,
        "profile": request.profile,
        "model_identity": f"{request.provider}/{configured_model}",
        "grant_digest": grant_digest("codex", runtime_grant),
    }


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


def _bounded_git_output(
    command: Sequence[str],
    *,
    max_bytes: int,
    timeout_seconds: float,
) -> tuple[bytes | None, str | None]:
    try:
        process = subprocess.Popen(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, TypeError, ValueError, AttributeError) as exc:
        return None, type(exc).__name__

    chunks: list[bytes] = []
    total = 0
    overflow = False
    read_error: str | None = None

    def read_output() -> None:
        nonlocal total, overflow, read_error
        stream = process.stdout
        if stream is None:
            read_error = "missing_stdout"
            return
        try:
            while True:
                chunk = stream.read(_WORKSPACE_GIT_READ_CHUNK_BYTES)
                if not chunk:
                    return
                total += len(chunk)
                if total > max_bytes:
                    overflow = True
                    return
                chunks.append(chunk)
        except (OSError, ValueError) as exc:
            read_error = type(exc).__name__

    reader = threading.Thread(target=read_output, name="workspace-identity-reader", daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    while reader.is_alive():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            break
        reader.join(min(remaining, 0.05))

    if timed_out or overflow or reader.is_alive():
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=1)
    except (OSError, subprocess.TimeoutExpired):
        try:
            process.kill()
        except OSError:
            pass
        try:
            process.wait(timeout=1)
        except (OSError, subprocess.TimeoutExpired):
            pass
    reader.join(timeout=1)

    if timed_out:
        return None, "timeout"
    if overflow:
        return None, "output_limit"
    if reader.is_alive() or read_error is not None:
        return None, read_error or "reader_failure"
    if process.returncode != 0:
        return None, "command_failed"
    return b"".join(chunks), None


def _runtime_artifact_paths(output: Path) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    stable_paths = (
        output.resolve(),
        native_binding_path(output).resolve(),
        native_submission_path(output).resolve(),
        native_result_path(output).resolve(),
    )
    lock_paths = tuple(f".{path.name}.release.lock" for path in stable_paths)
    temporary_prefixes = tuple(f".{path.name}." for path in stable_paths)
    return stable_paths, lock_paths + temporary_prefixes


def _path_is_runtime_artifact(path: Path, output: Path) -> bool:
    output_path = Path(os.path.abspath(output))
    stable_paths = {
        output_path,
        Path(os.path.abspath(native_binding_path(output))),
        Path(os.path.abspath(native_submission_path(output))),
        Path(os.path.abspath(native_result_path(output))),
    }
    candidate = Path(os.path.abspath(path))
    if candidate in stable_paths:
        return True
    if candidate.parent != output_path.parent:
        return False
    generated_names = tuple(f".{path.name}." for path in stable_paths)
    return any(candidate.name.startswith(prefix) for prefix in generated_names)


def _relative_runtime_paths(repository_root: Path, output: Path) -> list[str]:
    stable_paths, _ = _runtime_artifact_paths(output)
    root = repository_root.resolve()
    relative_paths: list[str] = []
    for path in stable_paths:
        try:
            relative_paths.append(path.relative_to(root).as_posix())
        except ValueError:
            continue
        lock_path = path.with_name(f".{path.name}.release.lock")
        try:
            relative_paths.append(lock_path.relative_to(root).as_posix())
        except ValueError:
            continue
    return relative_paths


def _reject_tracked_runtime_paths(repository_root: Path, output: Path) -> None:
    relative_paths = _relative_runtime_paths(repository_root, output)
    if not relative_paths or not (repository_root / ".git").exists():
        return
    tracked, error = _bounded_git_output(
        ["git", "-C", str(repository_root), "ls-files", "--cached", "-z", "--", *relative_paths],
        max_bytes=64 * 1024,
        timeout_seconds=_WORKSPACE_GIT_COMMAND_TIMEOUT_SECONDS,
    )
    if error is not None:
        raise LaunchBlocked(f"runtime output path tracking check unavailable: {error}")
    if tracked:
        raise LaunchBlocked("Project OS runtime output or sidecar path is tracked by Git")


def _read_bounded_regular_file(path: Path, limit: int) -> bytes | None:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    if no_follow:
        flags |= no_follow
    descriptor: int | None = None
    try:
        initial = path.lstat()
        if not stat.S_ISREG(initial.st_mode):
            return None
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        current = path.lstat()
        if not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(current.st_mode):
            return None
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            return None
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(_WORKSPACE_GIT_READ_CHUNK_BYTES, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        if sum(len(chunk) for chunk in chunks) > limit:
            return None
        finished = os.fstat(descriptor)
        opened_identity = (
            opened.st_dev,
            opened.st_ino,
            stat.S_IFMT(opened.st_mode),
            opened.st_size,
        )
        finished_identity = (
            finished.st_dev,
            finished.st_ino,
            stat.S_IFMT(finished.st_mode),
            finished.st_size,
        )
        if opened_identity != finished_identity:
            return None
        final = path.lstat()
        if not stat.S_ISREG(final.st_mode):
            return None
        if (opened.st_dev, opened.st_ino) != (final.st_dev, final.st_ino):
            return None
        if final.st_size != finished.st_size:
            return None
        return b"".join(chunks)
    except (OSError, ValueError):
        return None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_bounded_json_payload(path: Path) -> dict[str, Any] | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise NativeAppServerError(
            "Existing native evidence is uncertain.", failure_kind="NATIVE_RESULT_CONFLICT"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise NativeAppServerError(
            "Existing native evidence is not a regular file.", failure_kind="NATIVE_RESULT_CONFLICT"
        )
    content = _read_bounded_regular_file(path, NATIVE_RESULT_MAX_BYTES)
    if content is None:
        raise NativeAppServerError(
            "Existing native evidence is unreadable or changed during read.",
            failure_kind="NATIVE_RESULT_CONFLICT",
        )
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativeAppServerError(
            "Existing native evidence is unreadable.", failure_kind="NATIVE_RESULT_CONFLICT"
        ) from exc
    if not isinstance(payload, Mapping):
        raise NativeAppServerError(
            "Existing native evidence is not a mapping.", failure_kind="NATIVE_RESULT_CONFLICT"
        )
    return dict(payload)


def _read_only_workspace_identity(
    repository_root: Path,
    output: Path | None = None,
) -> tuple[bool, str | None, tuple[str, ...]]:
    status_output, status_error = _bounded_git_output(
        [
            "git",
            "-C",
            str(repository_root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "-z",
        ],
        max_bytes=_WORKSPACE_STATUS_MAX_BYTES,
        timeout_seconds=_WORKSPACE_GIT_COMMAND_TIMEOUT_SECONDS,
    )
    if status_error is not None or status_output is None:
        return False, None, ("workspace_identity",)
    if not status_output:
        return False, None, ()

    diff_output, diff_error = _bounded_git_output(
        ["git", "-C", str(repository_root), "diff", "--binary", "HEAD", "--"],
        max_bytes=_WORKSPACE_TRACKED_DIFF_MAX_BYTES,
        timeout_seconds=_WORKSPACE_GIT_COMMAND_TIMEOUT_SECONDS,
    )
    if diff_error is not None or diff_output is None:
        return True, None, ("workspace_identity",)

    identity_status_entries: list[bytes] = []
    untracked_contents: list[tuple[str, bytes]] = []
    untracked_entries = 0
    untracked_bytes = 0
    for entry in status_output.split(b"\0"):
        if not entry:
            continue
        if not entry.startswith(b"?? "):
            identity_status_entries.append(entry)
            continue
        relative = entry[3:].decode("utf-8", errors="surrogateescape")
        path = repository_root / relative
        if output is not None:
            try:
                if _path_is_runtime_artifact(path, output):
                    continue
            except (OSError, ValueError):
                return True, None, ("workspace_identity",)
        untracked_entries += 1
        if untracked_entries > _WORKSPACE_UNTRACKED_ENTRY_MAX:
            return True, None, ("workspace_identity",)
        content = _read_bounded_regular_file(path, _WORKSPACE_UNTRACKED_FILE_MAX_BYTES)
        if content is None:
            return True, None, ("workspace_identity",)
        untracked_bytes += len(content)
        if untracked_bytes > _WORKSPACE_UNTRACKED_TOTAL_MAX_BYTES:
            return True, None, ("workspace_identity",)
        identity_status_entries.append(entry)
        untracked_contents.append((relative, content))
    if not identity_status_entries and not diff_output:
        return False, None, ()
    digest = hashlib.sha256()
    digest.update(b"\0".join(identity_status_entries) + b"\0")
    digest.update(b"\0")
    digest.update(diff_output)
    for relative, content in untracked_contents:
        digest.update(relative.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return True, digest.hexdigest(), ()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


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
        elif candidate in {"not_required", "not_attempted", "already_absent"}:
            if state == "unknown":
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
    empty_state: str = "unknown",
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
        state = empty_state if empty_state in {"settled", "quarantined", "unknown"} else "unknown"
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


def recover_quarantined_receipt(receipt: Path, *, herdr: str = "herdr") -> dict[str, Any]:
    """Close exactly the resources owned by one quarantined attempt.

    Recovery is deliberately separate from probing: it never submits a task,
    retries a task, or selects another profile. Uncertain cleanup keeps the
    receipt quarantined so a later invocation can retry the same cleanup.
    """

    receipt_path = Path(receipt).expanduser().resolve()
    if receipt_path.stat().st_size > _WORKSPACE_STATUS_MAX_BYTES:
        raise ValueError("receipt exceeds the bounded recovery read size")
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("receipt is not valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("receipt must be a JSON object")

    attempt_id = _safe_text(payload.get("attempt_id"))
    inventory = payload.get("resource_inventory")
    if attempt_id is None or not isinstance(inventory, Mapping):
        raise ValueError("receipt is missing attempt identity or resource inventory")
    if inventory.get("attempt_id") != attempt_id:
        raise ValueError("resource inventory attempt identity does not match receipt attempt identity")
    resources = inventory.get("resources")
    if not isinstance(resources, list) or not resources:
        raise ValueError("receipt has no exact resource identities")

    validated: list[dict[str, Any]] = []
    for resource in resources:
        if not isinstance(resource, Mapping):
            raise ValueError("resource inventory contains a non-object entry")
        kind = _safe_text(resource.get("kind"))
        identity = resource.get("identity")
        resource_attempt = resource.get("attempt_id")
        state = _safe_text(resource.get("state"))
        if kind is None or not isinstance(identity, str) or not identity.strip() or state is None:
            raise ValueError("resource inventory contains an incomplete identity")
        if resource_attempt != attempt_id:
            raise ValueError("resource attempt identity does not match receipt attempt identity")
        validated.append(dict(resource))

    if payload.get("recovery_required") is not True and inventory.get("state") == "settled":
        return {
            "state": "settled",
            "recovery_required": False,
            "attempt_id": attempt_id,
            "receipt": str(receipt_path),
            "idempotent": True,
        }
    if inventory.get("state") != "quarantined" and payload.get("recovery_required") is not True:
        raise ValueError("receipt is not quarantined or marked for recovery")

    environment = dict(os.environ)
    server = _ensure_herdr_server(herdr, env=environment)
    cleanup: list[dict[str, Any]] = []
    all_verified = True
    for resource in validated:
        if resource.get("state") in {"removed", "already_absent", "settled"}:
            cleanup.append({"kind": resource["kind"], "identity": resource["identity"], "verified": True, "state": "already_absent"})
            continue
        if resource["kind"] not in {"workspace", "herdr.workspace"}:
            result = {"kind": resource["kind"], "identity": resource["identity"], "verified": False, "state": "quarantined", "reason": "no canonical cleanup owner"}
        else:
            result = _close_herdr_workspace(herdr, resource["identity"], env=environment)
            result = {"kind": resource["kind"], "identity": resource["identity"], **result}
        cleanup.append(result)
        all_verified = all_verified and result.get("verified") is True

    if not all_verified:
        return {
            "state": "quarantined",
            "recovery_required": True,
            "attempt_id": attempt_id,
            "receipt": str(receipt_path),
            "server": server,
            "cleanup": cleanup,
        }

    for resource in validated:
        resource["state"] = "removed"
    inventory_update = dict(inventory)
    inventory_update.update({
        "resources": validated,
        "state": "settled",
        "reuse_blocked": False,
        "recovery_required": False,
    })
    updated = dict(payload)
    updated.update({"resource_inventory": inventory_update, "recovery_required": False})
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=receipt_path.parent, delete=False) as temp:
        temp.write(json.dumps(updated, indent=2, sort_keys=True) + "\n")
        temp_path = Path(temp.name)
    os.replace(temp_path, receipt_path)
    return {
        "state": "settled",
        "recovery_required": False,
        "attempt_id": attempt_id,
        "receipt": str(receipt_path),
        "server": server,
        "cleanup": cleanup,
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
        if source.get("native_authority") not in {NATIVE_RESULT_AUTHORITY, NATIVE_APP_SERVER_AUTHORITY}:
            return False
        if source.get("attempt_id") != expected_attempt_id or not isinstance(source.get("attempt_id"), str):
            return False
        if source.get("freshness_proven") is not True or source.get("assistant_owned") is not True:
            return False
        if source.get("content_source") == "native_app_server_completed_turn":
            return (
                source.get("terminal_status") == "completed"
                and isinstance(source.get("native_turn_id"), str)
                and bool(source.get("native_turn_id", "").strip())
                and bool(_result_evidence(source)[0] or _result_evidence(source)[1])
            )
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
        empty_state=resource["state"],
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


def _apply_native_retirement_evidence(
    result: dict[str, Any], retirement: Mapping[str, Any] | None,
) -> dict[str, Any]:
    evidence = dict(retirement) if isinstance(retirement, Mapping) else {"state": "unknown"}
    result.setdefault("preflight", {})["retirement"] = evidence
    if evidence.get("state") == "retired":
        result["resource"] = {"state": "settled", "reuse_blocked": False}
        inventory = result.get("resource_inventory")
        if isinstance(inventory, Mapping) and not inventory.get("resources"):
            result["resource_inventory"] = {
                **inventory,
                "state": "settled",
                "reuse_blocked": False,
                "recovery_required": False,
            }
        result["finalization_outcome"] = {"state": "settled", "recovery_required": False}
        result["recovery_required"] = False
        result.setdefault("observability", {})["cleanup_state"] = "retired"
        return result
    result["failure_kind"] = "NATIVE_RETIREMENT_UNVERIFIED"
    result["recovery_required"] = True
    result["resource"] = {"state": "quarantined", "reuse_blocked": True}
    inventory = result.get("resource_inventory")
    if isinstance(inventory, Mapping):
        result["resource_inventory"] = {
            **inventory,
            "state": "quarantined",
            "reuse_blocked": True,
            "recovery_required": True,
        }
    result["finalization_outcome"] = {"state": "recovery_required", "recovery_required": True}
    result["settlement"] = {"state": "retirement_unverified", "recovery_required": True}
    return result


def _discover_native_logical_operation(output: Path) -> str | None:
    discovered: set[str] = set()
    for path in (
        native_result_path(output),
        native_binding_path(output),
        native_submission_path(output),
    ):
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise NativeAppServerError(
                "Existing native evidence is uncertain.", failure_kind="NATIVE_RESULT_CONFLICT"
            ) from exc
        content = _read_bounded_regular_file(path, NATIVE_RESULT_MAX_BYTES)
        if content is None:
            raise NativeAppServerError(
                "Existing native evidence is uncertain.", failure_kind="NATIVE_RESULT_CONFLICT"
            )
        try:
            raw = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NativeAppServerError(
                "Existing native evidence is unreadable.", failure_kind="NATIVE_RESULT_CONFLICT"
            ) from exc
        if not isinstance(raw, Mapping) or raw.get("schema") not in {
            NATIVE_RESULT_SCHEMA,
            NATIVE_BINDING_SCHEMA,
            NATIVE_SUBMISSION_SCHEMA,
        }:
            continue
        value = raw.get("logical_operation_id")
        if not isinstance(value, str) or not value.strip():
            raise NativeAppServerError(
                "Existing native evidence has no logical operation identity.",
                failure_kind="NATIVE_RESULT_CONFLICT",
            )
        discovered.add(value.strip())
    if len(discovered) > 1:
        raise NativeAppServerError(
            "Existing native evidence has conflicting logical operation identities.",
            failure_kind="NATIVE_RESULT_CONFLICT",
        )
    return next(iter(discovered), None)


def _bind_native_resume_request(request: SecretaryNormalRequest, output: Path) -> SecretaryNormalRequest:
    discovered = _discover_native_logical_operation(output)
    supplied = request.logical_operation_id
    if discovered is not None and supplied is not None and supplied != discovered:
        raise NativeAppServerError(
            "Supplied logical operation identity conflicts with existing native evidence.",
            failure_kind="NATIVE_RESULT_CONFLICT",
        )
    if discovered is not None and supplied is None:
        return replace(request, logical_operation_id=discovered)
    return request


def _bind_native_retirement_identity(
    retirement: Mapping[str, Any] | None,
    *,
    logical_operation_id: str | None,
    request_fingerprint_value: str | None,
    attempt_id: str | None,
    native_session_id: str | None,
    native_thread_id: str | None,
    native_turn_id: str | None,
) -> dict[str, Any]:
    bound = dict(retirement) if isinstance(retirement, Mapping) else {"state": "unknown"}
    for key, value in {
        "logical_operation_id": logical_operation_id,
        "request_fingerprint": request_fingerprint_value,
        "attempt_id": attempt_id,
        "native_session_id": native_session_id,
        "native_thread_id": native_thread_id,
        "native_turn_id": native_turn_id,
    }.items():
        if value is not None:
            bound[key] = value
    return bound


def _retirement_identity_matches(
    retirement: Mapping[str, Any] | None,
    *,
    logical_operation_id: str,
    request_fingerprint_value: str,
    attempt_id: str,
    native_session_id: str | None,
    native_thread_id: str | None,
    native_turn_id: str | None,
) -> bool:
    if not isinstance(retirement, Mapping):
        return False
    expected = {
        "logical_operation_id": logical_operation_id,
        "request_fingerprint": request_fingerprint_value,
        "attempt_id": attempt_id,
        "native_session_id": native_session_id,
        "native_thread_id": native_thread_id,
        "native_turn_id": native_turn_id,
    }
    return all(retirement.get(key) == value and value is not None for key, value in expected.items())


def _native_namespace_state(output: Path) -> str:
    stable_paths = (
        output,
        native_result_path(output),
        native_binding_path(output),
        native_submission_path(output),
    )
    candidate_paths = list(stable_paths)
    lock_names = {f".{path.name}.release.lock" for path in stable_paths}
    temporary_prefixes = tuple(f".{path.name}." for path in stable_paths)
    try:
        for child in output.parent.iterdir():
            if child.name in lock_names or any(child.name.startswith(prefix) for prefix in temporary_prefixes):
                candidate_paths.append(child)
    except FileNotFoundError:
        pass
    except OSError:
        return "foreign_or_uncertain"
    states: list[str] = []
    for path in candidate_paths:
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            states.append("absent")
            continue
        except OSError:
            states.append("uncertain")
            continue
        states.append("regular" if stat.S_ISREG(mode) else "occupied")
    if all(state == "absent" for state in states):
        return "empty"
    if any(state in {"occupied", "uncertain"} for state in states):
        return "foreign_or_uncertain"
    return "occupied"


def _existing_output_matches_current_identity(
    output: Path,
    *,
    logical_operation_id: str,
    request_fingerprint_value: str,
    attempt_id: str,
    output_payload: Mapping[str, Any] | None = None,
) -> bool:
    if output_payload is None:
        try:
            raw = _read_bounded_json_payload(output)
        except NativeAppServerError:
            return False
    else:
        raw = output_payload
    if not isinstance(raw, Mapping):
        return False
    if raw.get("logical_operation_id") != logical_operation_id:
        return False
    if raw.get("request_fingerprint") != request_fingerprint_value:
        return False
    if "attempt_id" in raw and raw.get("attempt_id") != attempt_id:
        return False
    preflight = raw.get("preflight")
    if not isinstance(preflight, Mapping):
        return False
    if preflight.get("logical_operation_id") not in {None, logical_operation_id}:
        return False
    if preflight.get("request_fingerprint") not in {None, request_fingerprint_value}:
        return False
    authoritative_attempts: list[object] = []
    if "attempt_id" in preflight:
        authoritative_attempts.append(preflight.get("attempt_id"))
    retirement = preflight.get("retirement")
    if retirement is not None:
        if not isinstance(retirement, Mapping):
            return False
        if any(
            retirement.get(key) != expected
            for key, expected in {
                "logical_operation_id": logical_operation_id,
                "request_fingerprint": request_fingerprint_value,
            }.items()
        ):
            return False
        if "attempt_id" in retirement:
            authoritative_attempts.append(retirement.get("attempt_id"))
    if not authoritative_attempts or any(value != attempt_id for value in authoritative_attempts):
        return False
    return True


def _reconcile_native_artifacts(
    *,
    output: Path,
    invocation_id: str,
    started_at: str,
    request_fingerprint_value: str,
    logical_operation_id: str | None = None,
    reuse_allowed: bool = True,
    resume: bool = False,
) -> dict[str, Any] | None:
    namespace_state = _native_namespace_state(output)
    if namespace_state == "empty":
        return None
    if namespace_state != "occupied":
        raise NativeAppServerError(
            "Existing output namespace is foreign or uncertain and cannot be overwritten.",
            failure_kind="NATIVE_RESULT_CONFLICT",
        )
    if not reuse_allowed:
        if native_binding_path(output).is_file() or native_submission_path(output).is_file():
            if not native_result_path(output).is_file() and not output.is_file():
                raise NativeAppServerError(
                    "Native binding or submission evidence exists but request identity is unknown; delivery is uncertain and will not be retried automatically.",
                    failure_kind="NATIVE_SUBMISSION_FAILED",
                )
        raise NativeAppServerError(
            "Request identity is unknown; existing native evidence cannot be reused.",
            failure_kind="NATIVE_RESULT_CONFLICT",
        )
    if not logical_operation_id:
        logical_operation_id = _discover_native_logical_operation(output)
    if not logical_operation_id:
        raise NativeAppServerError(
            "Existing native evidence has no trustworthy logical operation identity.",
            failure_kind="NATIVE_RESULT_CONFLICT",
        )
    result_path = native_result_path(output)
    result_payload = _read_bounded_json_payload(result_path)
    if result_payload is not None:
        namespace_state = "owned_existing_operation"
        try:
            persisted_payload = validate_native_result_payload(result_payload)
        except ValueError as exc:
            raise NativeAppServerError(
                "Existing native result is unreadable.", failure_kind="NATIVE_RESULT_CONFLICT"
            ) from exc
        attempt_id = persisted_payload.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id.strip():
            raise NativeAppServerError("Existing native result has no attempt identity.", failure_kind="NATIVE_RESULT_CONFLICT")
        for field, expected in {
            "request_fingerprint": request_fingerprint_value,
            "logical_operation_id": logical_operation_id,
        }.items():
            if persisted_payload.get(field) != expected:
                raise NativeAppServerError(
                    f"Existing native result {field.replace('request_fingerprint', 'request fingerprint')} mismatch.",
                    failure_kind="NATIVE_RESULT_CONFLICT",
                )
        output_payload = _read_bounded_json_payload(output)
        if output_payload is not None:
            if not _existing_output_matches_current_identity(
                output,
                logical_operation_id=logical_operation_id,
                request_fingerprint_value=request_fingerprint_value,
                attempt_id=attempt_id,
                output_payload=output_payload,
            ):
                raise NativeAppServerError(
                    "Existing invocation output is not attributable to the current request.",
                    failure_kind="NATIVE_RESULT_CONFLICT",
                )
        persisted = {"state": "confirmed", **persisted_payload, "result_reference": str(result_path)}
        binding_payload = _read_bounded_json_payload(native_binding_path(output))
        submission_payload = _read_bounded_json_payload(native_submission_path(output))
        if binding_payload is None or submission_payload is None:
            raise NativeAppServerError(
                "Existing native result lacks matching binding or submission evidence.",
                failure_kind="NATIVE_RESULT_CONFLICT",
            )
        try:
            binding = validate_native_binding_payload(binding_payload)
            submission = validate_native_submission_payload(submission_payload)
        except ValueError as exc:
            raise NativeAppServerError(
                "Existing native result lacks matching binding or submission evidence.",
                failure_kind="NATIVE_RESULT_CONFLICT",
            ) from exc
        if (
            any(
                binding.get(key) != persisted.get(key)
                for key in ("request_fingerprint", "attempt_id", "native_session_id")
            )
            or any(
                submission.get(key) != persisted.get(key)
                for key in ("request_fingerprint", "attempt_id", "native_session_id", "native_thread_id", "native_turn_id")
            )
        ):
            raise NativeAppServerError(
                "Existing native artifacts disagree on request or turn identity.",
                failure_kind="NATIVE_RESULT_CONFLICT",
            )
        assignment = {
            "attempt_id": attempt_id,
            "session": persisted.get("session", "codex-app-server"),
            "pane": persisted.get("pane", "native"),
            "agent_name": persisted.get("agent_name", "normal-secretary"),
            "execution": {"state": "completed", "worker_exit_code": 0},
            "task_result": {"state": "unknown"},
        }
        prior_retirement: Mapping[str, Any] | None = None
        if output_payload is not None and _existing_output_matches_current_identity(
            output,
            logical_operation_id=logical_operation_id,
            request_fingerprint_value=request_fingerprint_value,
            attempt_id=attempt_id,
            output_payload=output_payload,
        ):
            preflight = output_payload.get("preflight")
            candidate = preflight.get("retirement") if isinstance(preflight, Mapping) else None
            if _retirement_identity_matches(
                candidate,
                logical_operation_id=logical_operation_id,
                request_fingerprint_value=request_fingerprint_value,
                attempt_id=attempt_id,
                native_session_id=persisted.get("native_session_id"),
                native_thread_id=persisted.get("native_thread_id"),
                native_turn_id=persisted.get("native_turn_id"),
            ):
                prior_retirement = candidate
        retirement = dict(prior_retirement or {"state": "unknown", "reason": "retirement evidence unavailable"})
        cleanup = {
            "state": "removed" if retirement.get("state") == "retired" else "unknown",
            "verified": retirement.get("state") == "retired",
            "retirement": retirement,
        }
        result = _normalize_native_v3_outcome(
            invocation_id=invocation_id,
            persisted=persisted,
            payload={"assignment": assignment},
            cleanup=cleanup,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        result["logical_operation_id"] = logical_operation_id
        result["request_fingerprint"] = request_fingerprint_value
        result["preflight"] = {
            "transport": "codex-app-server",
            "reconciled": True,
            "logical_operation_id": logical_operation_id,
            "request_fingerprint": request_fingerprint_value,
            "attempt_id": attempt_id,
            "retirement": retirement,
        }
        if retirement.get("state") != "retired":
            result = _apply_native_retirement_evidence(result, retirement)
        return result
    binding_path = native_binding_path(output)
    submission_path = native_submission_path(output)
    if binding_path.is_file() or submission_path.is_file():
        raise NativeAppServerError(
            "Native binding or submission evidence exists without a published result; delivery is uncertain and will not be retried automatically.",
            failure_kind="NATIVE_SUBMISSION_FAILED",
        )
    return None


def _normalize_native_v3_outcome(
    *,
    invocation_id: str,
    persisted: Mapping[str, Any],
    payload: Mapping[str, Any],
    cleanup: Mapping[str, Any] | None = None,
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    """Project a validated v3 result without legacy source arbitration."""
    observation = {
        "state": "done",
        "cleanup": dict(cleanup or {"state": "pending_retirement", "verified": False}),
    }
    result = _normalize_invocation_outcome(
        invocation_id=invocation_id,
        returncode=0,
        payload=payload,
        observation=observation,
        started_at=started_at,
        finished_at=finished_at,
    )
    semantic_outcome = {
        "state": "reported",
        "status": "completed",
        "reference": persisted.get("result_reference"),
        "content": persisted.get("semantic_content"),
    }
    result["result"] = _project_semantic_result(semantic_outcome)
    result["semantic_outcome"] = semantic_outcome
    result["observability"] = {
        **result.get("observability", {}),
        "state": "available",
        "reference": persisted.get("result_reference"),
        "completion_state": "done",
    }
    return result


def _run_normal_via_native_app_server(
    request: SecretaryNormalRequest,
    *,
    output: Path,
    environment: Mapping[str, str],
    invocation_id: str,
    git_anchor: tuple[Path, str] | None = None,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    payload: Mapping[str, Any] | None = None
    observation: Mapping[str, Any] = {}
    preflight: dict[str, Any] = {"transport": "codex-app-server"}
    client: CodexAppServerClient | None = None
    owns_output = False
    resolved: ResolvedSecretaryRequest | None = None
    attempt_id: str | None = None
    thread: Any | None = None
    turn: Any | None = None
    result: dict[str, Any] = {}
    try:
        attempt_deadline = time.monotonic() + _CODEX_OBSERVATION_TIMEOUT_SECONDS
        request = _bind_native_resume_request(request, output)
        resolve_kwargs: dict[str, Any] = {"output": output}
        if git_anchor is not None:
            resolve_kwargs["git_anchor"] = git_anchor
        resolved = _resolve_normal_request(request, environment, **resolve_kwargs)
        request = resolved.request
        worktree = resolved.request.worktree
        request_fingerprint_value = resolved.request_fingerprint
        preflight.update(
            {
                "task_sha256": resolved.task_sha256,
                "repository_identity": resolved.repository_identity,
                "git_revision": resolved.git_revision,
                "execution_role": resolved.execution_role,
                "provider_identity": resolved.provider_identity,
                "model_identity": resolved.model_identity,
                "runtime_grant_digest": resolved.runtime_grant_digest,
                "workspace_dirty": resolved.workspace_dirty,
                "workspace_change_digest": resolved.workspace_change_digest,
                "request_fingerprint": request_fingerprint_value,
                "resume": resolved.request.resume,
                "identity_reuse_allowed": resolved.reuse_allowed,
            }
        )
        reconciled = _reconcile_native_artifacts(
            output=output,
            invocation_id=invocation_id,
            started_at=started,
            request_fingerprint_value=request_fingerprint_value,
            logical_operation_id=resolved.logical_operation_id,
            reuse_allowed=resolved.reuse_allowed,
            resume=resolved.request.resume,
        )
        if reconciled is not None:
            _atomic_write_json(output, reconciled)
            return reconciled
        codex_executable = environment.get("CODEX_EXECUTABLE") or shutil.which("codex")
        if not isinstance(codex_executable, str) or not codex_executable.strip():
            raise LaunchBlocked("Required executable unavailable on PATH: codex")
        configured_provider = _configured_provider(request.codex_home)
        if configured_provider != resolved.provider_identity:
            raise NativeAppServerError(
                "Configured Codex provider does not match Secretary provider.",
                failure_kind="NATIVE_BINDING_FAILED",
            )
        attempt_id = uuid.uuid4().hex
        binding_path = native_binding_path(output)
        submission_path = native_submission_path(output)
        if binding_path.exists() or submission_path.exists() or native_result_path(output).exists():
            raise NativeAppServerError("Codex app-server native evidence already exists", failure_kind="NATIVE_RESULT_CONFLICT")
        client = CodexAppServerClient(
            codex_executable,
            cwd=worktree,
            codex_home=request.codex_home,
            environment=environment,
            timeout_seconds=_CODEX_OBSERVATION_TIMEOUT_SECONDS,
            attempt_deadline=attempt_deadline,
        )
        with client:
            thread = client.start_thread(model=resolved.model_identity)
            binding = {
                "schema": NATIVE_BINDING_SCHEMA,
                "attempt_id": attempt_id,
                "logical_operation_id": resolved.logical_operation_id,
                "request_fingerprint": request_fingerprint_value,
                "provider": resolved.provider_identity,
                "model": resolved.model_identity,
                "native_session_id": thread.session_id,
                "native_thread_id": thread.thread_id,
                "pre_submit_boundary": thread.pre_submit_boundary,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "fresh_session": thread.ephemeral,
            }
            _require_attempt_budget(attempt_deadline)
            publish_native_binding(binding_path, binding)
            owns_output = True
            _require_attempt_budget(attempt_deadline)
            turn = client.start_turn(thread, request.task)
            submission = {
                "schema": NATIVE_SUBMISSION_SCHEMA,
                "attempt_id": attempt_id,
                "logical_operation_id": resolved.logical_operation_id,
                "request_fingerprint": request_fingerprint_value,
                "native_session_id": thread.session_id,
                "native_thread_id": thread.thread_id,
                "native_turn_id": turn.turn_id,
                "accepted_at": datetime.now(timezone.utc).isoformat(),
                "status": "accepted",
            }
            _require_attempt_budget(attempt_deadline)
            publish_native_submission(submission_path, submission)
            _require_attempt_budget(attempt_deadline)
            evidence = client.wait_for_turn(turn)
            native_payload = {
                "schema": NATIVE_RESULT_SCHEMA,
                "producer": NATIVE_RESULT_PRODUCER,
                "attempt_id": attempt_id,
                "logical_operation_id": resolved.logical_operation_id,
                "request_fingerprint": request_fingerprint_value,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "native_authority": NATIVE_APP_SERVER_AUTHORITY,
                "native_session_id": thread.session_id,
                "native_thread_id": thread.thread_id,
                "native_turn_id": evidence.turn_id,
                "terminal_status": evidence.status,
                "content_source": "native_app_server_completed_turn",
                "answer_provenance": "native_final_answer",
                "semantic_complete": True,
                "freshness_proven": True,
                "assistant_owned": True,
                "semantic_content": evidence.semantic_content,
            }
            _require_attempt_budget(attempt_deadline)
            publish_native_result(native_result_path(output), native_payload)
            _require_attempt_budget(attempt_deadline)
            persisted = parse_native_result(
                native_result_path(output),
                attempt_id=attempt_id,
                request_fingerprint=request_fingerprint_value,
                logical_operation_id=resolved.logical_operation_id,
                native_session_id=thread.session_id,
                native_thread_id=thread.thread_id,
                native_turn_id=turn.turn_id,
            )
            if persisted.get("state") != "confirmed":
                raise LaunchBlocked("Codex app-server native result read-back failed")
            payload = {
                "assignment": {
                    "attempt_id": attempt_id,
                    "assignment_id": None,
                    "agent_name": "normal-secretary",
                    "session": "codex-app-server",
                    "pane": "native",
                    "execution": {"state": "completed", "worker_exit_code": 0},
                    "task_result": {"state": "unknown"},
                    "status": "completed",
                    "transport": "codex-app-server",
                }
            }
            result = _normalize_native_v3_outcome(
                invocation_id=invocation_id,
                persisted=persisted,
                payload=payload,
                started_at=started,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            result["logical_operation_id"] = resolved.logical_operation_id
            result["request_fingerprint"] = request_fingerprint_value
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
        if isinstance(exc, NativeAppServerError):
            result["failure_kind"] = exc.failure_kind
        elif isinstance(exc, NativeResultConflictError):
            result["failure_kind"] = "NATIVE_RESULT_CONFLICT"
        elif isinstance(exc, (OSError, ValueError)):
            result["failure_kind"] = "NATIVE_RESULT_PUBLICATION_FAILED"
        preflight["error"] = str(exc)
    finally:
        if client is not None:
            retirement = _bind_native_retirement_identity(
                getattr(client, "retirement_evidence", {"state": "unknown"}),
                logical_operation_id=resolved.logical_operation_id if resolved is not None else None,
                request_fingerprint_value=request_fingerprint_value if "request_fingerprint_value" in locals() else None,
                attempt_id=attempt_id,
                native_session_id=getattr(thread, "session_id", None),
                native_thread_id=getattr(thread, "thread_id", None),
                native_turn_id=getattr(turn, "turn_id", None),
            )
            preflight["retirement"] = retirement
            if result:
                result = _apply_native_retirement_evidence(result, retirement)
    result["logical_operation_id"] = resolved.logical_operation_id if resolved is not None else request.logical_operation_id
    result["request_fingerprint"] = request_fingerprint_value if "request_fingerprint_value" in locals() else None
    preflight["logical_operation_id"] = result["logical_operation_id"]
    result["preflight"] = preflight
    if owns_output:
        _atomic_write_json(output, result)
    return result


def run_normal(request: SecretaryNormalRequest, *, output: Path) -> dict[str, Any]:
    environment = dict(os.environ)
    invocation_id = uuid.uuid4().hex
    git_anchor = _read_only_git_anchor(request.worktree)
    worktree, _ = git_anchor
    return _run_normal_via_native_app_server(
        replace(request, worktree=worktree),
        output=output,
        environment=environment,
        invocation_id=invocation_id,
        git_anchor=git_anchor,
    )


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
    operation_id = _probe_operation_id(request)
    submission_binding = _probe_submission_binding(request, configured_model="unknown")
    submission_path: Path | None = None
    submission_attempt_id = uuid.uuid4().hex
    submission_claimed = False
    try:
        _configured_provider(request.codex_home)
        configured_model = _configured_model(request)
        submission_binding = _probe_submission_binding(
            request,
            configured_model=configured_model,
        )
        submission_path = gate_path(operation_id)
        admission = claim_submission(
            submission_path,
            operation_id=operation_id,
            attempt_id=submission_attempt_id,
            binding=submission_binding,
        )
        if admission.get("state") == "blocked":
            raise LaunchBlocked(
                "logical operation admission blocked; prior attempt already owns delivery"
            )
        submission_claimed = True
        if not herdr:
            raise LaunchBlocked("Required executable unavailable on PATH: herdr")
        launch_request = replace(request, logical_operation_id=operation_id)
        launch_request, preflight, workspace_id = _prepare_herdr_target(
            launch_request,
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
            assignment = payload.get("assignment")
            launcher_observation = (
                assignment.get("observation")
                if isinstance(assignment, Mapping)
                else None
            )
            post_submit = _observe_submitted_codex(
                request,
                payload,
                pre_submit=submission_anchor,
                initial_snapshot=(
                    launcher_observation
                    if isinstance(launcher_observation, Mapping)
                    else None
                ),
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
                    empty_state=resource["state"],
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
        if submission_claimed and submission_path is not None:
            if result is not None and result.get("disposition") == "READY":
                settlement = "settled"
            elif workspace_id is None:
                settlement = "not_delivered"
            else:
                settlement = "delivery_uncertain"
            settle_submission(
                submission_path,
                attempt_id=submission_attempt_id,
                state=settlement,
            )
            if result is not None:
                result["submission_gate"] = {
                    "logical_operation_id": operation_id,
                    "state": settlement,
                    "path": str(submission_path),
                }
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
    run.add_argument("--logical-operation-id")
    run.add_argument("--resume", action="store_true")
    recover = subparsers.add_parser("recover")
    recover.add_argument("--receipt", type=Path, required=True)
    recover.add_argument("--herdr", default="herdr")
    args = parser.parse_args(argv)
    if args.command == "recover":
        try:
            result = recover_quarantined_receipt(args.receipt, herdr=args.herdr)
        except (OSError, RuntimeError, ValueError, LaunchBlocked) as exc:
            result = {
                "state": "quarantined",
                "recovery_required": True,
                "error": type(exc).__name__,
                "error_detail": str(exc),
            }
        print(json.dumps(result, sort_keys=True))
        return 0 if result["state"] == "settled" else 2
    if args.command == "run":
        codex_home = (args.codex_home or Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")).expanduser()
        request = SecretaryNormalRequest(
            worktree=args.cwd,
            task=args.task,
            codex_home=codex_home,
            profile=args.profile,
            logical_operation_id=args.logical_operation_id,
            resume=args.resume,
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
