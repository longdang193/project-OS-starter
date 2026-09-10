"""Launch one registry-bound top-level lane through Herdr."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from contextvars import ContextVar
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import uuid
from typing import Any

try:
    from agent_profile_registry import AgentProfile, load_agent_profiles
except ModuleNotFoundError:
    from scripts.agent_profile_registry import AgentProfile, load_agent_profiles
try:
    from mcp_selection import McpSelectionError, load_mcp_capabilities, normalize_mcp_selection
except ModuleNotFoundError:
    from scripts.mcp_selection import (
        McpSelectionError,
        load_mcp_capabilities,
        normalize_mcp_selection,
    )


class LaunchBlocked(RuntimeError):
    """Raised when a required runtime binding is unavailable or mismatched."""


class CommandTransportTimeout(LaunchBlocked):
    """Raised when a launcher subprocess times out before returning a result."""


class TargetCandidateRejected(LaunchBlocked):
    """Raised when one auto-discovery candidate fails eligibility checks."""


class TargetResolutionBlocked(LaunchBlocked):
    def __init__(self, message: str, resolution: dict[str, Any]) -> None:
        super().__init__(message)
        self.resolution = resolution


_EXECUTORS = {"codex", "deepagents"}
_MAX_TASK_LENGTH = 4096
_CODEX_TASK_PROGRESS_TIMEOUT_SECONDS = 30.0
_CODEX_START_TIMEOUT_MS = "120000"
_HERDR_COMMAND_TIMEOUT = 30.0
_DEEPAGENTS_RUN_TIMEOUT = 1800.0
_DEEPAGENTS_COMPLETION_WAIT_SECONDS = 60.0
_DEEPAGENTS_COMPLETION_POLL_SECONDS = 1.0
_CODEX_ASSIGNMENT_TIMEOUT = _CODEX_TASK_PROGRESS_TIMEOUT_SECONDS + 5.0
_CODEX_START_TIMEOUT = (float(_CODEX_START_TIMEOUT_MS) / 1000) + 5.0
_TARGET_DISCOVERY_TIMEOUT = 5.0
_HERDR_DEFAULT_SESSION = "default"
_NATIVE_GRANT_VALUE = "native"
_CHILD_AGENT_GRANT_VALUES = {"allow", "deny"}
_SHELL_PROCESS_NAMES = {"powershell.exe", "pwsh.exe", "cmd.exe", "bash", "sh", "zsh", "fish"}
_DEEPAGENTS_SHELL_PROCESS_NAMES = {"powershell.exe", "pwsh.exe"}
_DEEPAGENTS_RESULT_SCHEMA = "dcode-project.result.v1"
_DEEPAGENTS_RESULT_MAX_BYTES = 16 * 1024
_DEEPAGENTS_RESULT_MAX_AGE_SECONDS = 3600
_DEEPAGENTS_RESULT_WAIT_SECONDS = 5.0
_DEEPAGENTS_FAILURE_PATTERN = re.compile(
    r"(?im)^\s*(?:\[FAIL\]\s*)?Task failed\b|^\s*Traceback \(most recent call last\):|^\s*ERROR:\s*"
)
_CODEX_PROMPT_REJECTION_CODES = {
    "agent_blocked",
    "agent_not_found",
    "agent_prompt_rejected",
    "empty_agent_prompt",
    "invalid_agent",
    "invalid_prompt",
}
_ACTIVE_METRICS: ContextVar[dict[str, Any] | None] = ContextVar(
    "herdr_launcher_metrics",
    default=None,
)
_PERFORMANCE_PHASES = (
    "preflight",
    "target_discovery",
    "worker_initialization",
    "delivery",
    "observation",
    "retirement",
)


def _herdr_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("HERDR_ENV", None)
    return environment


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: float = _HERDR_COMMAND_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    metrics = _ACTIVE_METRICS.get()
    if metrics is not None:
        metrics["total"] = int(metrics.get("total", 0)) + 1
        executable = Path(command[0]).name.lower()
        by_executable = metrics.setdefault("by_executable", {})
        by_executable[executable] = int(by_executable.get(executable, 0)) + 1
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTransportTimeout(
            f"Command timed out after {timeout:g}s: {' '.join(command)}"
        ) from exc


def _run_checked(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: float = _HERDR_COMMAND_TIMEOUT,
) -> str:
    result = _run(command, cwd=cwd, env=env, timeout=timeout)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise LaunchBlocked(f"Command failed ({result.returncode}): {' '.join(command)}: {detail}")
    return result.stdout.strip()


def _write_runtime_output(stream: Any, value: str) -> None:
    try:
        stream.write(value)
    except UnicodeEncodeError:
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            raise
        reconfigure(encoding="utf-8", errors="replace")
        stream.write(value)


def _json_command(
    command: list[str], *, env: dict[str, str] | None = None,
    timeout: float = _HERDR_COMMAND_TIMEOUT,
) -> dict[str, Any]:
    output = _run_checked(command, env=env, timeout=timeout)
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise LaunchBlocked(f"Herdr returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise LaunchBlocked("Herdr returned a non-object JSON response.")
    return payload


def _result(payload: dict[str, Any], key: str) -> Any:
    result = payload.get("result")
    if not isinstance(result, dict) or key not in result:
        raise LaunchBlocked(f"Herdr response missing result.{key}.")
    return result[key]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_deepagents_receipt(path: Path | None, attempt_id: str) -> dict[str, Any]:
    unknown = {"state": "unknown", "detail": "receipt unavailable"}
    if path is None:
        return unknown
    deadline = time.monotonic() + _DEEPAGENTS_RESULT_WAIT_SECONDS
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    try:
        stat = path.stat()
        if (
            not path.is_file()
            or stat.st_size > _DEEPAGENTS_RESULT_MAX_BYTES
            or time.time() - stat.st_mtime > _DEEPAGENTS_RESULT_MAX_AGE_SECONDS
        ):
            return unknown
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"state": "unknown", "detail": "receipt malformed"}
    if not isinstance(payload, dict) or payload.get("schema") != _DEEPAGENTS_RESULT_SCHEMA:
        return {"state": "unknown", "detail": "receipt schema mismatch"}
    if payload.get("attempt_id") != attempt_id:
        return {"state": "unknown", "detail": "receipt correlation mismatch"}
    worker = payload.get("worker")
    cleanup = payload.get("cleanup")
    if not isinstance(worker, dict) or not isinstance(cleanup, dict):
        return {"state": "unknown", "detail": "receipt lifecycle fields missing"}
    if worker.get("state") not in {"exited", "failed", "start_failed", "recovery_blocked"}:
        return {"state": "unknown", "detail": "receipt worker state invalid"}
    if cleanup.get("state") not in {"removed", "preserved", "unverified"}:
        return {"state": "unknown", "detail": "receipt cleanup state invalid"}
    exit_code = worker.get("exit_code")
    if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
        return {"state": "unknown", "detail": "receipt exit code invalid"}
    return {
        "state": "confirmed",
        "worker_state": worker["state"],
        "worker_exit_code": exit_code,
        "descendant_state": worker.get("descendant_state"),
        "cleanup_state": cleanup["state"],
        "role_views_state": cleanup.get("role_views_state", cleanup["state"]),
        "recovery_required": payload.get("recovery_required") is True,
    }


def _discard_deepagents_receipt(path: Path | None) -> None:
    if path is None:
        return
    removed = False
    try:
        path.unlink()
        removed = True
    except FileNotFoundError:
        pass
    if removed:
        try:
            path.parent.rmdir()
        except OSError:
            pass


def _codex_runtime(cwd: Path, configured_home: Path | None = None) -> dict[str, Any]:
    raw_home = configured_home or Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    codex_home = raw_home.expanduser().resolve()
    if not codex_home.is_dir():
        raise LaunchBlocked(f"CODEX_HOME must be an existing directory: {codex_home}")

    stop_hook_scopes: list[str] = []
    for hooks_path in (codex_home / "hooks.json", cwd.resolve() / ".codex" / "hooks.json"):
        if not hooks_path.is_file():
            continue
        try:
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LaunchBlocked(f"Cannot read Codex hooks file {hooks_path}: {exc}") from exc
        hooks = payload.get("hooks") if isinstance(payload, dict) else None
        if isinstance(hooks, dict) and hooks.get("Stop"):
            stop_hook_scopes.append(str(hooks_path.resolve()))

    if len(stop_hook_scopes) > 1:
        joined = ", ".join(stop_hook_scopes)
        raise LaunchBlocked(f"duplicate Stop-hook scopes: {joined}")
    return {
        "codex_home": str(codex_home),
        "stop_hook_scopes": stop_hook_scopes,
    }


def _codex_environment(codex_home: Path) -> dict[str, str]:
    environment = _herdr_environment()
    environment["CODEX_HOME"] = str(codex_home.resolve())
    return environment


def _codex_runtime_mcp_servers(
    codex: str,
    cwd: Path,
    *,
    env: dict[str, str],
) -> dict[str, bool]:
    result = _run(
        [codex, "mcp", "list", "--json"],
        cwd=cwd,
        env=env,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise LaunchBlocked(
            f"Cannot inspect Codex MCP servers ({result.returncode}): {detail}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise LaunchBlocked(f"Codex MCP listing returned invalid JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise LaunchBlocked("Codex MCP listing returned a non-list JSON response.")
    servers: dict[str, bool] = {}
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise LaunchBlocked("Codex MCP listing returned an invalid server entry.")
        name = item["name"].strip()
        if not name:
            raise LaunchBlocked("Codex MCP listing returned an empty server name.")
        servers[name] = item.get("enabled", True) is not False
    return servers


def _codex_mcp_selection(
    cwd: Path,
    codex_home: Path,
    values: list[str],
    *,
    runtime_servers: Mapping[str, bool] | None = None,
) -> dict[str, tuple[str, ...]]:
    configs: list[dict[str, Any]] = []
    for config_path in (codex_home / "config.toml", cwd.resolve() / ".codex" / "config.toml"):
        if not config_path.is_file():
            continue
        try:
            config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise LaunchBlocked(f"Cannot read Codex MCP config {config_path}: {exc}") from exc
        configs.append(config)
    try:
        capabilities = load_mcp_capabilities(*configs)
        runtime_only_servers: set[str] = set()
        for name, enabled in (runtime_servers or {}).items():
            if enabled:
                if name not in capabilities:
                    runtime_only_servers.add(name)
                capabilities.setdefault(name, ())
            else:
                capabilities.pop(name, None)
        selection = normalize_mcp_selection(values, capabilities, allow_tools=False)
    except McpSelectionError as exc:
        raise LaunchBlocked(str(exc)) from exc
    return {
        **selection,
        "server_names": tuple(capabilities),
        "runtime_only_servers": tuple(sorted(runtime_only_servers)),
    }


def _git_value(cwd: Path, *arguments: str) -> str:
    return _run_checked(["git", "-C", str(cwd), *arguments])


def _git_identity(cwd: Path, expected_base: str) -> dict[str, str]:
    worktree = cwd.resolve()
    repo_root = Path(_git_value(worktree, "rev-parse", "--show-toplevel")).resolve()
    if worktree != repo_root:
        raise LaunchBlocked(f"--cwd must equal exact Git worktree root: {worktree}")
    common_dir = Path(_git_value(worktree, "rev-parse", "--git-common-dir"))
    if not common_dir.is_absolute():
        common_dir = (worktree / common_dir).resolve()
    else:
        common_dir = common_dir.resolve()
    branch = _git_value(worktree, "branch", "--show-current")
    head = _git_value(worktree, "rev-parse", "HEAD")
    expected = _git_value(worktree, "rev-parse", "--verify", f"{expected_base}^{{commit}}")
    return {
        "worktree": str(worktree),
        "repo_root": str(repo_root),
        "git_common_dir": str(common_dir),
        "branch": branch,
        "head": head,
        "expected_base": expected,
    }


def _executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise LaunchBlocked(f"Required executable unavailable on PATH: {name}")
    return str(Path(path).resolve())


def _version(path: str, *, env: dict[str, str] | None = None) -> str:
    output = _run_checked([path, "--version"], env=env)
    return output.splitlines()[0] if output else ""


def _profile(agents_root: Path, name: str) -> AgentProfile:
    try:
        profiles = load_agent_profiles(agents_root)
    except (OSError, ValueError) as exc:
        raise LaunchBlocked(str(exc)) from exc
    selected = profiles.get(name)
    if selected is None:
        raise LaunchBlocked(f"Unknown agent profile: {name}")
    return selected


def _herdr_pane(
    cwd: Path,
    session: str,
    pane: str,
    herdr: str,
    *,
    executor: str = "codex",
    env: dict[str, str] | None = None,
    panes: list[Any] | None = None,
    timeout: float = _HERDR_COMMAND_TIMEOUT,
) -> dict[str, Any]:
    if panes is None:
        panes = _result(
            _json_command(
                [herdr, "--session", session, "pane", "list"],
                env=env,
                timeout=timeout,
            ),
            "panes",
        )
    if not isinstance(panes, list):
        raise LaunchBlocked("Herdr pane list is not an array.")
    if any(not isinstance(item, dict) for item in panes):
        raise LaunchBlocked("Herdr pane list contains invalid entries.")
    selected = next((item for item in panes if item.get("pane_id") == pane), None)
    if not isinstance(selected, dict):
        raise TargetCandidateRejected(f"Pane is unavailable in session `{session}`: {pane}")
    pane_cwd = Path(str(selected.get("cwd", ""))).resolve()
    if pane_cwd != cwd.resolve():
        raise TargetCandidateRejected(f"Pane cwd mismatch: expected {cwd}, got {pane_cwd}")
    if selected.get("agent") or selected.get("agent_status") not in (None, "unknown"):
        raise TargetCandidateRejected(f"Pane already has agent state: {pane}")

    process_payload = _json_command(
        [herdr, "--session", session, "pane", "process-info", "--pane", pane],
        env=env,
        timeout=timeout,
    )
    process_info = _result(process_payload, "process_info")
    if not isinstance(process_info, dict):
        raise TargetCandidateRejected("Herdr pane process information is invalid.")
    if "foreground_processes" not in process_info:
        raise TargetCandidateRejected("Herdr pane process information is incomplete.")
    foreground = process_info["foreground_processes"]
    if not isinstance(foreground, list):
        raise TargetCandidateRejected("Herdr pane process information is invalid.")
    shell_names = (
        _DEEPAGENTS_SHELL_PROCESS_NAMES
        if executor == "deepagents"
        else _SHELL_PROCESS_NAMES
    )
    conflicting: list[str] = []
    for process in foreground:
        if not isinstance(process, dict):
            raise TargetCandidateRejected("Herdr pane process information is invalid.")
        process_name = str(process.get("name", "unknown"))
        if process_name.lower() not in shell_names:
            conflicting.append(process_name)
    if conflicting:
        raise TargetCandidateRejected(f"Pane has conflicting foreground process: {', '.join(conflicting)}")
    return {"pane": selected, "process_info": process_info}


def _resolve_target_selector(
    cwd: Path,
    session: str,
    pane: str,
    herdr: str,
    *,
    executor: str = "codex",
    env: dict[str, str] | None = None,
) -> tuple[str, str, dict[str, Any]]:
    if (session == "auto") != (pane == "auto"):
        raise LaunchBlocked("`--session auto` and `--pane auto` must be used together.")
    if session != "auto":
        return session, pane, {
            "status": "selected",
            "mode": "exact",
            "candidate_count": 1,
            "session": session,
            "pane": pane,
        }

    deadline = time.monotonic() + _TARGET_DISCOVERY_TIMEOUT

    def remaining_timeout() -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TargetResolutionBlocked(
                "target discovery deadline expired",
                {"status": "incomplete", "mode": "auto", "failure_kind": "deadline"},
            )
        return remaining

    try:
        snapshot = _result(
            _json_command(
                [herdr, "api", "snapshot"],
                env=env,
                timeout=remaining_timeout(),
            ),
            "snapshot",
        )
    except CommandTransportTimeout as exc:
        raise TargetResolutionBlocked(
            "target discovery transport timed out",
            {"status": "incomplete", "mode": "auto", "failure_kind": "transport_timeout"},
        ) from exc
    panes = snapshot.get("panes") if isinstance(snapshot, dict) else None
    if not isinstance(panes, list):
        raise LaunchBlocked("Herdr snapshot is missing panes.")
    if any(not isinstance(item, dict) for item in panes):
        raise LaunchBlocked("Herdr snapshot contains malformed pane entries.")
    if any(not isinstance(item.get("cwd"), str) or not item["cwd"] for item in panes):
        raise LaunchBlocked("Herdr snapshot contains pane entry without cwd.")

    candidates: list[tuple[str, str]] = []
    rejections: list[dict[str, str]] = []
    control_session = _HERDR_DEFAULT_SESSION
    for item in panes:
        workspace_id = item.get("workspace_id")
        pane_id = item.get("pane_id")
        if not isinstance(workspace_id, str) or not isinstance(pane_id, str):
            raise LaunchBlocked("Herdr snapshot contains pane entry without workspace_id/pane_id.")
        if Path(str(item.get("cwd", ""))).resolve() != cwd.resolve():
            continue
        session_panes = [
            candidate for candidate in panes
            if candidate.get("workspace_id") == workspace_id
        ]
        try:
            _herdr_pane(
                cwd,
                control_session,
                pane_id,
                herdr,
                executor=executor,
                env=env,
                panes=session_panes,
                timeout=remaining_timeout(),
            )
        except TargetCandidateRejected as exc:
            rejections.append({"session": control_session, "pane": pane_id, "reason": str(exc)})
        else:
            candidates.append((control_session, pane_id))

    candidates.sort()
    if not candidates:
        status = "blocked" if rejections else "not_found"
        raise TargetResolutionBlocked(
            f"target_resolution={status}; eligible candidates=0",
            {
                "status": status,
                "mode": "auto",
                "candidate_count": 0,
                "candidates": [],
                "rejections": rejections,
            },
        )
    selected_session, selected_pane = candidates[0]
    return selected_session, selected_pane, {
        "status": "selected",
        "mode": "auto",
        "candidate_count": len(candidates),
        "rejections": rejections,
        "candidates": [
            {"session": candidate_session, "pane": candidate_pane}
            for candidate_session, candidate_pane in candidates
        ],
        "session": selected_session,
        "pane": selected_pane,
    }


def _codex_arguments(
    profile: AgentProfile,
    cwd: Path,
    *,
    mcp_server_names: tuple[str, ...] = (),
    selected_mcp_servers: tuple[str, ...] = (),
    runtime_only_mcp_servers: tuple[str, ...] = (),
) -> list[str]:
    arguments = [
        "-C",
        str(cwd),
        "-c",
        f"model_provider={json.dumps(profile.model_provider)}",
        "-c",
        f"model={json.dumps(profile.model)}",
        "-c",
        f"developer_instructions={json.dumps(profile.developer_instructions)}",
    ]
    runtime_only = set(runtime_only_mcp_servers)
    for server in mcp_server_names:
        if server in runtime_only and server not in selected_mcp_servers:
            arguments.extend(
                (
                    "-c",
                    f'mcp_servers.{server}.command="cmd"',
                    "-c",
                    f"mcp_servers.{server}.args=[]",
                )
            )
        arguments.extend(("-c", f"mcp_servers.{server}.enabled=false"))
    arguments.extend(
        value
        for server in selected_mcp_servers
        for value in ("-c", f"mcp_servers.{server}.enabled=true")
    )
    return arguments


def _redacted_arguments(arguments: list[str]) -> list[str]:
    redacted: list[str] = []
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value == "-c" and index + 1 < len(arguments):
            setting = arguments[index + 1]
            if setting.startswith("developer_instructions="):
                setting = "developer_instructions=<sha256>"
            redacted.extend([value, setting])
            index += 2
            continue
        if value == "prompt" and index + 2 < len(arguments):
            redacted.extend([
                value,
                arguments[index + 1],
                f"task=<sha256:{_sha256_text(arguments[index + 2])}>",
            ])
            index += 3
            continue
        if value in {"-n", "--task"} and index + 1 < len(arguments):
            redacted.extend([value, f"task=<sha256:{_sha256_text(arguments[index + 1])}>"])
            index += 2
            continue
        redacted.append(value)
        index += 1
    return redacted


def _powershell_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _validate_task(task: str | None) -> str:
    if task is None or not task.strip():
        raise LaunchBlocked("Launch requires non-empty bounded task text.")
    if len(task) > _MAX_TASK_LENGTH:
        raise LaunchBlocked(f"Task text exceeds {_MAX_TASK_LENGTH} characters.")
    if "\r" in task or "\n" in task:
        raise LaunchBlocked("Task text cannot contain newlines.")
    return task.strip()


def _project_runtime_grant(task: str, runtime_grant: dict[str, Any]) -> str:
    delegation = runtime_grant.get("delegation")
    child_agents = delegation.get("child_agents") if isinstance(delegation, dict) else None
    if child_agents not in _CHILD_AGENT_GRANT_VALUES:
        raise LaunchBlocked("Runtime Grant is missing valid delegation.child_agents.")
    return f"{task} [Runtime Grant: delegation.child_agents = {child_agents}]"


def _elapsed_ms(started: float) -> float:
    return round(max(0.0, time.monotonic() - started) * 1000, 3)


def _metrics_snapshot() -> dict[str, Any]:
    metrics = _ACTIVE_METRICS.get()
    if metrics is None:
        return {"total": 0, "by_executable": {}}
    return {
        "total": int(metrics.get("total", 0)),
        "by_executable": dict(metrics.get("by_executable", {})),
    }


def _new_performance_evidence() -> dict[str, Any]:
    return {
        "status": "preparation",
        "phase_durations_ms": {
            phase: {"status": "not_attempted", "duration_ms": None}
            for phase in _PERFORMANCE_PHASES
        },
        "subprocess_counts": _metrics_snapshot(),
        "attempts": [],
        "phase_occurrences": {phase: [] for phase in _PERFORMANCE_PHASES},
        "phase_aggregates": {
            phase: {"status": "not_attempted", "duration_ms": None, "occurrence_count": 0}
            for phase in _PERFORMANCE_PHASES
        },
        "unattributed_duration_ms": None,
        "total_duration_ms": None,
    }


def _record_performance_phase(
    performance: dict[str, Any],
    name: str,
    started: float,
    *,
    now: float | None = None,
) -> None:
    if name not in _PERFORMANCE_PHASES:
        raise LaunchBlocked(f"Unknown performance phase: {name}")
    durations = performance.setdefault("phase_durations_ms", {})
    if not isinstance(durations, dict):
        raise LaunchBlocked("Performance phase durations must be an object.")
    current = time.monotonic() if now is None else now
    durations[name] = {
        "status": "measured",
        "duration_ms": round(max(0.0, current - started) * 1000, 3),
    }
    occurrences = performance.setdefault("phase_occurrences", {}).setdefault(name, [])
    occurrences.append(durations[name].copy())
    aggregate = performance.setdefault("phase_aggregates", {}).setdefault(name, {})
    aggregate.update({
        "status": "measured",
        "duration_ms": round(
            sum(float(item["duration_ms"]) for item in occurrences),
            3,
        ),
        "occurrence_count": len(occurrences),
    })
    performance["_last_monotonic"] = current
    performance["subprocess_counts"] = _metrics_snapshot()


def _record_performance_attempt(
    performance: dict[str, Any],
    attempt_id: str,
    started: float,
    *,
    now: float | None = None,
    pane_run_duration_ms: float | None = None,
) -> None:
    current = performance.get("_last_monotonic") if now is None else now
    if current is None:
        current = time.monotonic()
    attempts = performance.setdefault("attempts", [])
    if not isinstance(attempts, list):
        raise LaunchBlocked("Performance attempts must be an array.")
    attempt = {
        "attempt_id": attempt_id,
        "duration_ms": round(max(0.0, current - started) * 1000, 3),
    }
    if pane_run_duration_ms is not None:
        attempt["pane_run_duration_ms"] = round(max(0.0, pane_run_duration_ms), 3)
    attempts.append(attempt)


def _finalize_performance(
    performance: dict[str, Any],
    started: float,
    *,
    now: float | None = None,
) -> dict[str, Any]:
    current = performance.pop("_last_monotonic", None) if now is None else now
    if current is None:
        current = time.monotonic()
    performance["status"] = "measured"
    performance["total_duration_ms"] = round(max(0.0, current - started) * 1000, 3)
    measured = sum(
        float(item.get("duration_ms", 0.0))
        for occurrences in performance.get("phase_occurrences", {}).values()
        if isinstance(occurrences, list)
        for item in occurrences
        if isinstance(item, dict)
    )
    performance["unattributed_duration_ms"] = round(
        max(0.0, performance["total_duration_ms"] - measured),
        3,
    )
    performance["subprocess_counts"] = _metrics_snapshot()
    return performance


def _build_assignment_result(
    *,
    dispatch_id: str | None,
    attempt_id: str,
    agent_name: str,
    delivery: dict[str, Any],
    execution: dict[str, Any],
    observation: dict[str, Any],
    task_result: dict[str, Any],
    cleanup: dict[str, Any],
    performance: dict[str, Any],
    launcher_exit_code: int,
    legacy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    legacy_values = legacy or {}
    delivery_state = delivery.get("state", "unknown")
    delivery_certainty = delivery.get("certainty", "unknown")
    task_accepted = task_result.get("accepted")
    assignment = {
        "agent_name": agent_name,
        "attempt_id": attempt_id,
        "dispatch_id": dispatch_id,
        "delivery": delivery,
        "execution": execution,
        "observation": observation,
        "task_result": task_result,
        "cleanup": cleanup,
        "performance": performance,
        "launcher_exit_code": launcher_exit_code,
        "worker_exit_code": execution.get("worker_exit_code"),
        "delivery_state": delivery_state,
        "delivery_certainty": delivery_certainty,
        "delivery_task_sha256": legacy_values.get("delivery_task_sha256"),
        "exit_code": launcher_exit_code,
        "failure_kind": legacy_values.get("failure_kind"),
        "grant_digest": legacy_values.get("grant_digest"),
        "phase": legacy_values.get("phase"),
        "prompt_accepted": delivery.get("prompt_accepted"),
        "reconciliation_required": legacy_values.get(
            "reconciliation_required",
            delivery.get("reconciliation_required", False),
        ),
        "session": legacy_values.get("session"),
        "status": legacy_values.get("status", execution.get("state", "unknown")),
        "submission": delivery.get("submission"),
        "task_accepted": task_accepted,
        "task_sha256": legacy_values.get("task_sha256"),
    }
    for key, value in legacy_values.items():
        if key not in assignment:
            assignment[key] = value
    return {"assignment": assignment}


def _codex_assignment_command(
    herdr: str,
    session: str,
    agent_name: str,
    task: str,
) -> list[str]:
    return [
        herdr,
        "--session",
        session,
        "agent",
        "prompt",
        agent_name,
        task,
    ]


def _agent_name_taken(result: subprocess.CompletedProcess[str]) -> bool:
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    error = payload.get("error")
    return isinstance(error, dict) and error.get("code") == "agent_name_taken"


def _classify_codex_prompt_result(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    if result.returncode == 0:
        return {
            "submission": "acknowledged",
            "prompt_accepted": True,
            "failure_kind": None,
            "reconciliation_required": False,
        }
    error_code: str | None = None
    for output in (result.stdout, result.stderr):
        if not output:
            continue
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            continue
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            error_code = error["code"]
            break
    if error_code in _CODEX_PROMPT_REJECTION_CODES:
        return {
            "submission": "rejected",
            "prompt_accepted": False,
            "failure_kind": error_code,
            "reconciliation_required": False,
        }
    return {
        "submission": "unknown",
        "prompt_accepted": None,
        "failure_kind": error_code or "command_exit",
        "reconciliation_required": True,
    }


def _codex_completion_snapshot(
    herdr: str,
    session: str,
    agent_name: str,
    *,
    env: dict[str, str],
    timeout_seconds: float = _CODEX_TASK_PROGRESS_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    started = time.monotonic()

    def remaining_timeout() -> float:
        return max(0.01, timeout_seconds - (time.monotonic() - started))

    get_result: subprocess.CompletedProcess[str] | None = None
    read_result: subprocess.CompletedProcess[str] | None = None
    state = "unknown"
    state_change_seq: int | None = None
    observation_error: str | None = None
    try:
        get_result = _run(
            [herdr, "--session", session, "agent", "get", agent_name],
            env=env,
            timeout=remaining_timeout(),
        )
    except CommandTransportTimeout:
        observation_error = "agent get transport timeout"
    if get_result is not None and get_result.returncode:
        observation_error = "agent get failed"
    elif get_result is not None:
        try:
            payload = json.loads(get_result.stdout)
            agent = _result(payload, "agent")
            if not isinstance(agent, dict):
                raise LaunchBlocked("agent get returned invalid agent information")
            state = str(agent.get("agent_status") or "unknown")
            raw_seq = agent.get("state_change_seq")
            if isinstance(raw_seq, int):
                state_change_seq = raw_seq
        except (LaunchBlocked, json.JSONDecodeError) as exc:
            observation_error = str(exc)
    try:
        read_result = _run(
            [
                herdr,
                "--session",
                session,
                "agent",
                "read",
                agent_name,
                "--source",
                "recent-unwrapped",
                "--lines",
                "200",
                "--format",
                "text",
            ],
            env=env,
            timeout=remaining_timeout(),
        )
    except CommandTransportTimeout:
        observation_error = observation_error or "agent read transport timeout"
    if read_result is not None and read_result.returncode:
        observation_error = observation_error or "agent read failed"
    output = _pane_output(read_result) if read_result is not None else ""
    return {
        "state": state,
        "state_change_seq": state_change_seq,
        "output_sha256": _sha256_text(output),
        "output_chars": len(output),
        "observation_error": observation_error,
    }


def _reconcile_failed_codex_start(
    herdr: str,
    session: str,
    pane: str,
    agent_name: str,
    *,
    env: dict[str, str],
    before_process_ids: set[int] | None = None,
) -> dict[str, Any]:
    try:
        panes = _result(
            _json_command(
                [herdr, "--session", session, "pane", "list"],
                env=env,
            ),
            "panes",
        )
        selected = next(
            (item for item in panes if isinstance(item, dict) and item.get("pane_id") == pane),
            None,
        )
        if not isinstance(selected, dict):
            return {"state": "uncertain", "cleanup": None, "detail": "target pane disappeared"}
        process_info = _result(
            _json_command(
                [herdr, "--session", session, "pane", "process-info", "--pane", pane],
                env=env,
            ),
            "process_info",
        )
        foreground = process_info.get("foreground_processes") if isinstance(process_info, dict) else None
        if not isinstance(foreground, list):
            return {"state": "uncertain", "cleanup": None, "detail": "invalid process evidence"}
        process_ids = _process_ids(foreground, require_non_shell=False)
        if not process_ids:
            return {"state": "absent", "cleanup": None, "process_ids": []}
        if before_process_ids is None or not (process_ids - before_process_ids):
            return {
                "state": "uncertain",
                "cleanup": None,
                "process_ids": sorted(process_ids),
                "detail": "no new process proves failed-attempt ownership",
            }
        if selected.get("agent") != agent_name:
            return {
                "state": "uncertain",
                "cleanup": None,
                "process_ids": sorted(process_ids),
                "detail": "process owner does not match failed attempt",
            }
        cleanup = _terminate_codex_lane(herdr, session, pane, env=env)
        if cleanup.get("verified") is True:
            return {
                "state": "retired",
                "cleanup": cleanup,
                "process_ids": sorted(process_ids),
            }
        return {
            "state": "uncertain",
            "cleanup": cleanup,
            "process_ids": sorted(process_ids),
            "detail": "owned process cleanup was not verified",
        }
    except (LaunchBlocked, json.JSONDecodeError) as exc:
        return {"state": "uncertain", "cleanup": None, "detail": str(exc)}


def _unique_agent_name(agent_name: str) -> str:
    return f"{agent_name}-{uuid.uuid4().hex[:8]}"


def _parse_grant_value(value: str | int | None, label: str) -> int | str:
    if value is None or (isinstance(value, str) and value.strip().lower() == _NATIVE_GRANT_VALUE):
        return _NATIVE_GRANT_VALUE
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise LaunchBlocked(f"{label} must be `native` or a positive integer.") from exc
    if parsed <= 0:
        raise LaunchBlocked(f"{label} must be `native` or a positive integer.")
    return parsed


def _parse_child_agent_grant(value: str | None) -> str:
    grant = "deny" if value is None else value.strip().lower()
    if grant not in _CHILD_AGENT_GRANT_VALUES:
        raise LaunchBlocked("Grant child_agents must be `deny` or `allow`.")
    return grant


def _normalize_runtime_grant(
    *,
    executor: str,
    grant_turns: str | int | None,
    grant_wall_clock_seconds: str | int | None,
    mcp_select: list[str] | None,
    grant_child_agents: str | None = None,
) -> dict[str, Any]:
    turns = _parse_grant_value(grant_turns, "Grant turns")
    wall_clock_seconds = _parse_grant_value(
        grant_wall_clock_seconds,
        "Grant wall-clock seconds",
    )
    if executor == "codex" and turns != _NATIVE_GRANT_VALUE:
        raise LaunchBlocked("Codex strict turn budget is unsupported; use `native`.")
    if executor == "codex" and wall_clock_seconds != _NATIVE_GRANT_VALUE:
        raise LaunchBlocked(
            "Codex strict wall-clock enforcement is unavailable; use `native`."
        )
    if (
        executor == "deepagents"
        and wall_clock_seconds != _NATIVE_GRANT_VALUE
        and wall_clock_seconds > int(_DEEPAGENTS_RUN_TIMEOUT)
    ):
        raise LaunchBlocked(
            "DeepAgents wall-clock budget cannot exceed the 1800-second Herdr watchdog."
        )
    child_agents = _parse_child_agent_grant(grant_child_agents)
    return {
        "turns": {
            "requested": turns,
            "effective": turns,
            "enforcement": "runtime" if turns != _NATIVE_GRANT_VALUE else "native",
        },
        "wall_clock_seconds": {
            "requested": wall_clock_seconds,
            "effective": wall_clock_seconds,
            "enforcement": (
                "runtime" if wall_clock_seconds != _NATIVE_GRANT_VALUE else "native"
            ),
        },
        "outer_watchdog_seconds": (
            int(_DEEPAGENTS_RUN_TIMEOUT)
            if executor == "deepagents"
            else None
        ),
        "mcp_select": list(mcp_select or []),
        "delegation": {"child_agents": child_agents},
    }


def _codex_watchdog_seconds(evidence: dict[str, Any]) -> int | None:
    registry = evidence.get("registry_launcher")
    grant = registry.get("runtime_grant") if isinstance(registry, dict) else None
    wall_clock = grant.get("wall_clock_seconds") if isinstance(grant, dict) else None
    requested = wall_clock.get("requested") if isinstance(wall_clock, dict) else None
    return requested if isinstance(requested, int) else None


def _process_ids(processes: Any, *, require_non_shell: bool) -> set[int]:
    if not isinstance(processes, list) or not processes:
        raise LaunchBlocked("termination verification returned empty process information")
    process_ids: set[int] = set()

    def collect(process: Any) -> None:
        if not isinstance(process, dict):
            raise LaunchBlocked("termination verification returned invalid process information")
        pid = process.get("pid")
        if not isinstance(pid, int) or pid <= 0:
            raise LaunchBlocked("termination verification returned process without pid")
        if str(process.get("name", "")).lower() not in _SHELL_PROCESS_NAMES:
            process_ids.add(pid)
        children = process.get("children", [])
        if not isinstance(children, list):
            raise LaunchBlocked("termination verification returned invalid child processes")
        for child in children:
            collect(child)

    for process in processes:
        collect(process)
    if require_non_shell and not process_ids:
        raise LaunchBlocked("termination verification found no launch-owned process")
    return process_ids


def _process_ids_alive(process_ids: set[int]) -> set[int]:
    alive: set[int] = set()
    for pid in process_ids:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        except PermissionError:
            alive.add(pid)
        except OSError:
            alive.add(pid)
        else:
            alive.add(pid)
    return alive


def _deepagents_task_state(
    foreground_processes: list[Any],
    pane_output: str,
    expected_marker: str,
) -> str:
    live_process = any(
        str(process.get("name", "")).lower() not in _DEEPAGENTS_SHELL_PROCESS_NAMES
        for process in foreground_processes
        if isinstance(process, dict)
    )
    lines = [line.strip() for line in pane_output.splitlines() if line.strip()]
    start_index = max(
        (index for index, line in enumerate(lines) if line == "Running task non-interactively..."),
        default=0,
    )
    current_lines = lines[start_index:]
    if _DEEPAGENTS_FAILURE_PATTERN.search("\n".join(current_lines)):
        return "failed"
    if any(
        current_lines[index:index + 2] == ["COMPLETED", expected_marker]
        for index in range(len(current_lines) - 1)
    ):
        return "running" if live_process else "completed"
    if "COMPLETED" in current_lines:
        return "running" if live_process else "no-report"
    if live_process:
        return "running"
    return "no-report"


def _pane_output(result: subprocess.CompletedProcess[str]) -> str:
    output = result.stdout.strip()
    if not output:
        return ""
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return output
    result_payload = payload.get("result") if isinstance(payload, dict) else None
    if isinstance(result_payload, str):
        return result_payload.strip()
    if isinstance(result_payload, dict):
        for key in ("text", "output", "content"):
            value = result_payload.get(key)
            if isinstance(value, str):
                return value.strip()
    return output


def _deepagents_completion_snapshot(
    herdr: str,
    session: str,
    pane: str,
    *,
    env: dict[str, str],
    expected_marker: str,
    deadline: float | None = None,
) -> dict[str, Any]:
    def observation_timeout() -> float:
        if deadline is None:
            return _HERDR_COMMAND_TIMEOUT
        return min(_HERDR_COMMAND_TIMEOUT, deadline - time.monotonic())

    process_result: subprocess.CompletedProcess[str] | None = None
    read_result: subprocess.CompletedProcess[str] | None = None
    process_error: str | None = None
    read_error: str | None = None
    try:
        timeout = observation_timeout()
        if timeout <= 0:
            raise CommandTransportTimeout("observation deadline exceeded before process-info")
        process_result = _run(
            [herdr, "--session", session, "pane", "process-info", "--pane", pane],
            env=env,
            timeout=timeout,
        )
    except CommandTransportTimeout:
        process_error = "pane process-info transport timeout"
    try:
        timeout = observation_timeout()
        if timeout <= 0:
            raise CommandTransportTimeout("observation deadline exceeded before pane read")
        read_result = _run(
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
            timeout=timeout,
        )
    except CommandTransportTimeout:
        read_error = "pane read transport timeout"
    pane_output = _pane_output(read_result) if read_result is not None else ""
    foreground: list[Any] = []
    observation_error: str | None = process_error or read_error
    if process_result is not None and process_result.returncode:
        observation_error = observation_error or "pane process-info failed"
    elif process_result is not None:
        try:
            process_payload = json.loads(process_result.stdout)
            process_info = _result(process_payload, "process_info")
            foreground_value = process_info.get("foreground_processes") if isinstance(process_info, dict) else None
            if not isinstance(foreground_value, list):
                observation_error = "pane process-info returned invalid foreground_processes"
            else:
                foreground = foreground_value
        except (LaunchBlocked, json.JSONDecodeError) as exc:
            observation_error = str(exc)
    if read_result is not None and read_result.returncode:
        observation_error = observation_error or "pane read failed"
    state = _deepagents_task_state(foreground, pane_output, expected_marker)
    if observation_error and state == "completed":
        state = "no-report"
    return {
        "state": state,
        "marker_present": expected_marker in pane_output,
        "report_present": state in {"completed", "failed"},
        "report_sha256": _sha256_text(pane_output),
        "report_chars": len(pane_output),
        "observed_at": time.time(),
        "foreground_processes": [
            str(process.get("name", "unknown"))
            for process in foreground
            if isinstance(process, dict)
        ],
        "observation_error": observation_error,
    }


def _deepagents_completion_evidence(
    herdr: str,
    session: str,
    pane: str,
    *,
    env: dict[str, str],
    expected_marker: str,
) -> dict[str, Any]:
    started = time.monotonic()
    deadline = started + _DEEPAGENTS_COMPLETION_WAIT_SECONDS
    evidence: dict[str, Any] | None = None
    while True:
        evidence = _deepagents_completion_snapshot(
            herdr,
            session,
            pane,
            env=env,
            expected_marker=expected_marker,
            deadline=deadline,
        )
        if evidence["state"] in {"completed", "failed"}:
            return evidence
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            evidence["last_observed_state"] = evidence["state"]
            evidence["state"] = "timed_out"
            evidence["observation_deadline_exceeded"] = True
            return evidence
        time.sleep(min(_DEEPAGENTS_COMPLETION_POLL_SECONDS, remaining))


def _terminate_codex_lane(
    herdr: str,
    session: str,
    pane: str,
    *,
    env: dict[str, str],
) -> dict[str, Any]:
    before_result = _run(
        [herdr, "--session", session, "pane", "process-info", "--pane", pane],
        env=env,
    )
    if before_result.returncode:
        detail = before_result.stderr.strip() or before_result.stdout.strip()
        return {
            "requested": False,
            "action": "pane-close",
            "verified": False,
            "detail": detail or f"pre-close process verification failed ({before_result.returncode})",
        }
    try:
        before_payload = json.loads(before_result.stdout)
        before_info = _result(before_payload, "process_info")
        if not isinstance(before_info, dict):
            raise LaunchBlocked("termination verification returned invalid process information")
        before_processes = before_info.get("foreground_processes")
        before_ids = _process_ids(before_processes, require_non_shell=True)
    except (LaunchBlocked, json.JSONDecodeError) as exc:
        return {
            "requested": False,
            "action": "pane-close",
            "verified": False,
            "detail": f"pre-close process verification failed: {exc}",
        }

    close_result = _run(
        [herdr, "--session", session, "pane", "close", pane],
        env=env,
    )
    if close_result.returncode:
        detail = close_result.stderr.strip() or close_result.stdout.strip()
        return {
            "requested": True,
            "action": "pane-close",
            "verified": False,
            "detail": detail or f"pane close failed ({close_result.returncode})",
        }

    list_result = _run(
        [herdr, "--session", session, "pane", "list"],
        env=env,
    )
    if list_result.returncode:
        detail = list_result.stderr.strip() or list_result.stdout.strip()
        return {
            "requested": True,
            "action": "pane-close",
            "verified": False,
            "detail": detail or f"pane list failed ({list_result.returncode})",
        }
    try:
        payload = json.loads(list_result.stdout)
        panes = _result(payload, "panes")
    except (LaunchBlocked, json.JSONDecodeError) as exc:
        return {
            "requested": True,
            "action": "pane-close",
            "verified": False,
            "detail": f"termination verification failed: {exc}",
        }
    if not isinstance(panes, list):
        return {
            "requested": True,
            "action": "pane-close",
            "verified": False,
            "detail": "termination verification returned invalid panes",
        }
    selected = next((item for item in panes if item.get("pane_id") == pane), None)
    if not isinstance(selected, dict):
        remaining_ids = sorted(_process_ids_alive(before_ids))
        if remaining_ids:
            return {
                "requested": True,
                "action": "pane-close",
                "verified": False,
                "state": "processes-remain",
                "remaining_process_ids": remaining_ids,
            }
        return {
            "requested": True,
            "action": "pane-close",
            "verified": True,
            "state": "pane-closed",
            "verified_process_ids": sorted(before_ids),
        }

    process_result = _run(
        [herdr, "--session", session, "pane", "process-info", "--pane", pane],
        env=env,
    )
    if process_result.returncode:
        detail = process_result.stderr.strip() or process_result.stdout.strip()
        return {
            "requested": True,
            "action": "pane-close",
            "verified": False,
            "detail": detail or f"process verification failed ({process_result.returncode})",
        }
    try:
        process_payload = json.loads(process_result.stdout)
        process_info = _result(process_payload, "process_info")
        if not isinstance(process_info, dict):
            raise LaunchBlocked("termination verification returned invalid process information")
    except (LaunchBlocked, json.JSONDecodeError) as exc:
        return {
            "requested": True,
            "action": "pane-close",
            "verified": False,
            "detail": f"process verification failed: {exc}",
        }
    foreground = process_info.get("foreground_processes")
    try:
        after_ids = _process_ids(foreground, require_non_shell=False)
    except LaunchBlocked as exc:
        return {
            "requested": True,
            "action": "pane-close",
            "verified": False,
            "detail": str(exc),
        }
    shell_names = _SHELL_PROCESS_NAMES
    remaining = [
        str(process.get("name", "unknown"))
        for process in foreground
        if str(process.get("name", "")).lower() not in shell_names
    ]
    return {
        "requested": True,
        "action": "pane-close",
        "verified": not remaining and not (before_ids & after_ids),
        "state": "shell-only" if not remaining else "processes-remain",
        "remaining_foreground_processes": remaining,
        "remaining_process_ids": sorted(before_ids & after_ids),
    }


def resolve_launch(
    *,
    profile_name: str,
    session: str,
    pane: str,
    cwd: Path,
    expected_base: str,
    executor: str = "codex",
    mcp_select: list[str] | None = None,
    grant_turns: str | int | None = None,
    grant_wall_clock_seconds: str | int | None = None,
    grant_child_agents: str | None = None,
    task: str | None = None,
    name: str | None = None,
    codex_home: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    launch_started = time.monotonic()
    if executor not in _EXECUTORS:
        raise LaunchBlocked(f"Unsupported executor: {executor}")
    task_text = _validate_task(task)
    runtime_grant = _normalize_runtime_grant(
        executor=executor,
        grant_turns=grant_turns,
        grant_wall_clock_seconds=grant_wall_clock_seconds,
        mcp_select=mcp_select,
        grant_child_agents=grant_child_agents,
    )
    delivery_task = _project_runtime_grant(task_text, runtime_grant)
    completion_marker = None
    if executor == "deepagents":
        completion_marker = f"DEEPAGENTS_COMPLETED_{uuid.uuid4().hex[:16]}"
        delivery_task += (
            " Output these two final lines exactly when task is complete: "
            f"COMPLETED, then {completion_marker}."
        )
    grant_digest = _sha256_text(
        json.dumps(
            {
                "executor": executor,
                "turns": runtime_grant["turns"]["requested"],
                "wall_clock_seconds": runtime_grant["wall_clock_seconds"]["requested"],
                "mcp_select": runtime_grant["mcp_select"],
                "delegation": runtime_grant["delegation"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    lane_root = cwd.resolve()
    selected = _profile(lane_root / "agents", profile_name)
    runtime = _codex_runtime(cwd, codex_home) if executor == "codex" else None
    environment = (
        _codex_environment(Path(runtime["codex_home"]))
        if runtime is not None
        else _herdr_environment()
    )
    herdr = _executable("herdr")
    codex = _executable("codex") if executor == "codex" else None
    dcode = _executable("dcode-project") if executor == "deepagents" else None
    git = _git_identity(cwd, expected_base)
    performance = _new_performance_evidence()
    _record_performance_phase(performance, "preflight", launch_started)
    target_started = time.monotonic()
    session, pane, target_resolution = _resolve_target_selector(
        cwd,
        session,
        pane,
        herdr,
        executor=executor,
        env=environment,
    )
    _record_performance_phase(performance, "target_discovery", target_started)
    worker_started = time.monotonic()
    pane_state = _herdr_pane(cwd, session, pane, herdr, executor=executor, env=environment)
    agent_name = name or (
        _unique_agent_name(f"{selected.name}-main")
        if executor == "codex"
        else f"{selected.name}-main"
    )
    if executor == "codex":
        runtime_mcp_servers = _codex_runtime_mcp_servers(
            str(codex),
            cwd,
            env=environment,
        )
        codex_mcp_selection = _codex_mcp_selection(
            cwd,
            Path(str(runtime["codex_home"])),
            list(mcp_select or []),
            runtime_servers=runtime_mcp_servers,
        )
        runtime_arguments = _codex_arguments(
            selected,
            cwd,
            mcp_server_names=codex_mcp_selection["server_names"],
            selected_mcp_servers=codex_mcp_selection["effective_servers"],
            runtime_only_mcp_servers=codex_mcp_selection["runtime_only_servers"],
        )
        command = [
            herdr,
            "--session",
            session,
            "agent",
            "start",
            agent_name,
            "--kind",
            "codex",
            "--pane",
            pane,
            "--timeout",
            _CODEX_START_TIMEOUT_MS,
            "--",
            *runtime_arguments,
        ]
    else:
        direct_mcp = bool(mcp_select and any(value.strip() for value in mcp_select))
        runtime_arguments = [
            "&",
            _powershell_literal(str(dcode)),
            "--role",
            selected.name,
            "--json",
            *(["--max-turns", str(runtime_grant["turns"]["requested"])]
              if runtime_grant["turns"]["requested"] != _NATIVE_GRANT_VALUE
              else []),
            *(["--timeout", str(runtime_grant["wall_clock_seconds"]["requested"])]
              if runtime_grant["wall_clock_seconds"]["requested"] != _NATIVE_GRANT_VALUE
              else []),
            *sum(
                (["--mcp-select", _powershell_literal(value)] for value in (mcp_select or [])),
                [],
            ),
            *([] if direct_mcp else ["--no-mcp"]),
            "-n",
            _powershell_literal(delivery_task),
        ]
        command = [herdr, "--session", session, "pane", "run", pane, *runtime_arguments]
    evidence = {
        "registry_launcher": {
            "dispatch_id": uuid.uuid4().hex,
            "profile": selected.name,
            "profile_source": str(selected.source),
            "executor": executor,
            "model_provider": selected.model_provider,
            "model": selected.model,
            "developer_instructions_sha256": _sha256_text(selected.developer_instructions),
            "projected_config_keys": [
                "model_provider",
                "model",
                "developer_instructions",
            ],
            "redacted_runtime_argv": _redacted_arguments(runtime_arguments),
            "assignment_task_sha256": _sha256_text(task_text),
            "grant_digest": grant_digest,
            "runtime_grant": runtime_grant,
            "delivery_task_sha256": _sha256_text(delivery_task),
            "completion_marker": completion_marker,
            "mcp_selection_requested": list(mcp_select or []),
        },
        "git": git,
            "herdr": {
            "executable": herdr,
            "version": _version(herdr, env=environment),
            "session": session,
            "pane": pane,
            "agent_name": agent_name,
            "agent_kind": "codex" if executor == "codex" else "pane-process",
                "pane_cwd": str(Path(str(pane_state["pane"].get("cwd"))).resolve()),
                "start_process_ids": sorted(
                    _process_ids(
                        pane_state.get("process_info", {}).get("foreground_processes", []),
                        require_non_shell=False,
                    )
                    if pane_state.get("process_info", {}).get("foreground_processes")
                    else set()
                ),
            },
        "target_resolution": target_resolution,
        "observation": {
            "executor": executor,
            "session": session,
            "pane": pane,
            "agent_name": agent_name,
            "task_sha256": _sha256_text(task_text),
            "delivery_task_sha256": _sha256_text(delivery_task),
            "grant_digest": grant_digest,
            "state": "unknown",
            "source": "herdr.agent" if executor == "codex" else "herdr.pane_process",
            "read_commands": (
                ["agent get", "agent read"]
                if executor == "codex"
                else ["pane process-info", "pane read"]
            ),
        },
        "runtime": {
            "executable": codex or dcode,
            "argv_shape": _redacted_arguments(runtime_arguments),
        },
        "assignment_request": {
            "status": "pending",
            "required": True,
            "delivery": "herdr_agent_prompt" if executor == "codex" else "inline_pane_run",
            "redacted_prompt_argv": _redacted_arguments(
                _codex_assignment_command(
                    herdr,
                    session,
                    agent_name,
                    delivery_task,
                )
            ) if executor == "codex" else None,
        },
        "performance": performance,
    }
    if runtime is not None:
        evidence["codex"] = {
            "executable": codex,
            "version": _version(str(codex), env=environment),
            **runtime,
        }
        evidence["codex"]["mcp_selection"] = codex_mcp_selection
    else:
        evidence["deepagents"] = {
            "executable": dcode,
            "mcp_mode": "direct" if direct_mcp else "disabled",
            "mcp_selection": list(mcp_select or []),
        }
    _record_performance_phase(performance, "worker_initialization", worker_started)
    return command, evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--session", required=True, help="Herdr session ID or auto")
    parser.add_argument("--pane", required=True, help="Herdr pane ID or auto")
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--expected-base", required=True)
    parser.add_argument("--executor", choices=sorted(_EXECUTORS), default="codex")
    parser.add_argument("--mcp-select", action="append", default=[])
    parser.add_argument("--grant-turns", default=_NATIVE_GRANT_VALUE)
    parser.add_argument("--grant-wall-clock-seconds", default=_NATIVE_GRANT_VALUE)
    parser.add_argument("--grant-child-agents", choices=["allow", "deny"], default="deny")
    parser.add_argument("--task", required=True)
    parser.add_argument("--name")
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _main_body(args: argparse.Namespace) -> int:
    invocation_started = time.monotonic()
    dispatch_id = uuid.uuid4().hex
    preparation_performance = _new_performance_evidence()

    def emit_failure(message: str, resolution: dict[str, Any] | None = None) -> int:
        phases = preparation_performance.get("phase_durations_ms", {})
        if isinstance(phases, dict):
            for phase in phases.values():
                if isinstance(phase, dict) and phase.get("status") == "not_attempted":
                    phase["status"] = "unavailable"
        performance = _finalize_performance(preparation_performance, invocation_started)
        result = _build_assignment_result(
            dispatch_id=dispatch_id,
            attempt_id=uuid.uuid4().hex,
            agent_name=args.name or f"{args.profile}-main",
            delivery={"state": "not_attempted", "certainty": "unknown"},
            execution={"state": "not_started", "worker_exit_code": None},
            observation={"state": "not_attempted"},
            task_result={"state": "not_attempted", "accepted": False},
            cleanup={"state": "not_attempted"},
            performance=performance,
            launcher_exit_code=2,
            legacy={"failure_kind": message, "status": "blocked"},
        )
        if resolution is not None:
            result["target_resolution"] = resolution
        print(json.dumps(result, sort_keys=True))
        return 2

    try:
        command, evidence = resolve_launch(
            profile_name=args.profile,
            session=args.session,
            pane=args.pane,
            cwd=args.cwd,
            expected_base=args.expected_base,
            executor=args.executor,
            mcp_select=args.mcp_select,
            grant_turns=args.grant_turns,
            grant_wall_clock_seconds=args.grant_wall_clock_seconds,
            grant_child_agents=args.grant_child_agents,
            task=args.task,
            name=args.name,
            codex_home=args.codex_home,
        )
        attempt_id = uuid.uuid4().hex
        registry_evidence = evidence.setdefault("registry_launcher", {})
        observation_evidence = evidence.setdefault("observation", {})
        if not isinstance(registry_evidence, dict) or not isinstance(observation_evidence, dict):
            raise LaunchBlocked("Launcher evidence has invalid lifecycle sections.")
        performance_evidence = evidence.setdefault("performance", preparation_performance)
        if not isinstance(performance_evidence, dict):
            raise LaunchBlocked("Launcher evidence has invalid performance section.")
        dispatch_id = str(registry_evidence.setdefault("dispatch_id", dispatch_id))
        receipt_file: Path | None = None
        if args.executor == "deepagents" and not args.dry_run and "-n" in command:
            receipt_dir = Path(tempfile.mkdtemp(prefix=f"herdr-result-{attempt_id}-"))
            receipt_file = receipt_dir / "result.json"
            command = command.copy()
            command[command.index("-n"):command.index("-n")] = [
                "--result-file",
                _powershell_literal(str(receipt_file)),
                "--attempt-id",
                _powershell_literal(attempt_id),
            ]
            registry_evidence["result_file"] = str(receipt_file)

        def record_phase(name: str, started: float) -> None:
            if args.executor == "deepagents" and name == "delivery":
                return
            _record_performance_phase(performance_evidence, name, started)

        def emit_assignment(payload: dict[str, Any]) -> dict[str, Any]:
            assignment = payload.get("assignment", payload)
            if not isinstance(assignment, dict):
                raise LaunchBlocked("Assignment evidence must be an object.")
            execution = assignment.setdefault("execution", {"state": "unknown", "worker_exit_code": None})
            if not isinstance(execution, dict):
                execution = {"state": "unknown", "worker_exit_code": None}
                assignment["execution"] = execution
            delivery = assignment.get("delivery")
            if not isinstance(delivery, dict):
                delivery = {
                    "state": assignment.get("delivery_state", "unknown"),
                    "certainty": assignment.get("delivery_certainty", "unknown"),
                }
            if "prompt_accepted" in assignment:
                delivery.setdefault("prompt_accepted", assignment["prompt_accepted"])
            if "submission" in assignment:
                delivery.setdefault("submission", assignment["submission"])
            if "reconciliation_required" in assignment:
                delivery.setdefault(
                    "reconciliation_required",
                    assignment["reconciliation_required"],
                )
            observation = assignment.get("observation")
            if not isinstance(observation, dict):
                observation = {"state": "unknown"}
            task_result = assignment.get("task_result")
            if not isinstance(task_result, dict):
                task_result = {"state": "unknown", "accepted": assignment.get("task_accepted")}
            cleanup = assignment.get("cleanup")
            if not isinstance(cleanup, dict):
                cleanup = {"state": "unknown"}
            receipt = _read_deepagents_receipt(receipt_file, str(assignment.get("attempt_id", attempt_id)))
            if args.executor == "deepagents":
                assignment["lifecycle_receipt"] = receipt
                if receipt.get("state") == "confirmed":
                    execution = {
                        **execution,
                        "state": "exited" if receipt["worker_state"] != "recovery_blocked" else "unknown",
                        "worker_exit_code": receipt.get("worker_exit_code"),
                        "descendant_state": receipt.get("descendant_state"),
                        "recovery_required": receipt.get("recovery_required", False),
                    }
                    cleanup = {
                        "state": receipt["cleanup_state"],
                        "role_views_state": receipt.get("role_views_state"),
                        "recovery_required": receipt.get("recovery_required", False),
                    }
                    observed = assignment.get("observation")
                    task_verified = (
                        receipt["worker_state"] == "exited"
                        and receipt.get("worker_exit_code") == 0
                        and receipt["cleanup_state"] == "removed"
                        and isinstance(observed, dict)
                        and observed.get("marker_present") is True
                        and observed.get("report_present") is True
                        and observed.get("observation_error") is None
                    )
                    task_result = {
                        "state": "verified" if task_verified else "unknown",
                        "accepted": task_verified,
                    }
                else:
                    execution = {"state": "unknown", "worker_exit_code": None}
                    cleanup = {"state": "unknown"}
                    task_result = {"state": "unknown", "accepted": False}
                if assignment.get("delivery_state") == "delivered":
                    delivery = {
                        "state": "unknown",
                        "certainty": "unknown",
                        "submission": "unavailable",
                    }
                _discard_deepagents_receipt(receipt_file)
            legacy = {
                key: value
                for key, value in assignment.items()
                if key not in {
                    "agent_name",
                    "attempt_id",
                    "dispatch_id",
                    "delivery",
                    "execution",
                    "observation",
                    "task_result",
                    "cleanup",
                    "performance",
                    "launcher_exit_code",
                    "worker_exit_code",
                }
            }
            result = _build_assignment_result(
                dispatch_id=str(assignment.get("dispatch_id", dispatch_id)),
                attempt_id=str(assignment.get("attempt_id", attempt_id)),
                agent_name=str(assignment.get("agent_name", evidence["herdr"]["agent_name"])),
                delivery=delivery,
                execution=execution,
                observation=observation,
                task_result=task_result,
                cleanup=cleanup,
                performance=performance_evidence,
                launcher_exit_code=int(assignment.get("exit_code", 2)),
                legacy=legacy,
            )
            result["assignment"]["performance"] = performance_evidence
            _record_performance_attempt(
                performance_evidence,
                attempt_id,
                attempt_started,
                pane_run_duration_ms=pane_run_duration_ms,
            )
            _finalize_performance(performance_evidence, invocation_started)
            return result

        registry_evidence["attempt_id"] = attempt_id
        observation_evidence["attempt_id"] = attempt_id
        if isinstance(performance_evidence, dict):
            performance_evidence.pop("_last_monotonic", None)
        print(json.dumps(evidence, sort_keys=True))
        if args.dry_run:
            return 0
        try:
            resolved_session = str(evidence["herdr"]["session"])
            resolved_pane = str(evidence["herdr"]["pane"])
        except (KeyError, TypeError) as exc:
            raise LaunchBlocked("Launcher evidence missing resolved Herdr target.") from exc
        registry_launcher = evidence.get("registry_launcher")
        if not isinstance(registry_launcher, dict):
            raise LaunchBlocked("Launcher evidence missing registry binding.")
        assignment_task_sha256 = registry_launcher.get("assignment_task_sha256")
        if not isinstance(assignment_task_sha256, str):
            raise LaunchBlocked("Launcher evidence missing assignment task identity.")
        completion_marker = registry_launcher.get("completion_marker")
        delivery_task_sha256 = registry_launcher.get(
            "delivery_task_sha256",
            assignment_task_sha256,
        )
        grant_digest = registry_launcher.get("grant_digest")
        if args.executor == "codex":
            codex_evidence = evidence.get("codex")
            if not isinstance(codex_evidence, dict) or not codex_evidence.get("codex_home"):
                raise LaunchBlocked("Launcher evidence missing codex_home.")
            environment = _codex_environment(Path(str(codex_evidence["codex_home"])))
        else:
            if not isinstance(completion_marker, str) or not completion_marker:
                raise LaunchBlocked("Launcher evidence missing completion marker.")
            environment = _herdr_environment()
        for attempt in range(2):
            attempt_started = time.monotonic()
            pane_run_duration_ms: float | None = None
            pane_run_started = time.monotonic()
            try:
                try:
                    result = _run(
                        command,
                        env=environment,
                        timeout=(
                            _DEEPAGENTS_RUN_TIMEOUT
                            if args.executor == "deepagents"
                            else _CODEX_START_TIMEOUT
                        ),
                    )
                finally:
                    if args.executor == "deepagents":
                        pane_run_duration_ms = max(0.0, time.monotonic() - pane_run_started) * 1000
            except CommandTransportTimeout:
                record_phase("delivery", attempt_started)
                print(json.dumps(emit_assignment({
                    "assignment": {
                        "agent_name": evidence["herdr"]["agent_name"],
                        "attempt_id": attempt_id,
                        "delivery_state": "delivery_uncertain",
                        "delivery_certainty": "unknown",
                        "delivery_task_sha256": delivery_task_sha256,
                        "exit_code": 2,
                        "failure_kind": "transport_timeout",
                        "grant_digest": grant_digest,
                        "phase": "pane_run" if args.executor == "deepagents" else "start",
                        "prompt_accepted": None,
                        "reconciliation_required": True,
                        "session": resolved_session,
                        "status": "uncertain",
                        "task_sha256": assignment_task_sha256,
                    }
                }), sort_keys=True))
                return 2
            if not (
                args.executor == "codex"
                and args.name is None
                and attempt == 0
                and result.returncode
                and _agent_name_taken(result)
            ):
                break
            retirement_started = time.monotonic()
            reconciliation = _reconcile_failed_codex_start(
                str(evidence["herdr"]["executable"]),
                resolved_session,
                resolved_pane,
                str(evidence["herdr"]["agent_name"]),
                env=environment,
                before_process_ids=set(evidence["herdr"].get("start_process_ids", [])),
            )
            record_phase("retirement", retirement_started)
            registry_launcher["failed_start_reconciliation"] = reconciliation
            if reconciliation["state"] == "uncertain":
                print(json.dumps(emit_assignment({
                    "assignment": {
                        "agent_name": evidence["herdr"]["agent_name"],
                        "attempt_id": attempt_id,
                        "delivery_state": "delivery_uncertain",
                        "delivery_certainty": "unknown",
                        "delivery_task_sha256": delivery_task_sha256,
                        "exit_code": 2,
                        "failure_kind": "reconciliation_required",
                        "grant_digest": grant_digest,
                        "phase": "start",
                        "prompt_accepted": None,
                        "reconciliation_required": True,
                        "reconciliation": reconciliation,
                        "session": resolved_session,
                        "status": "uncertain",
                        "task_sha256": assignment_task_sha256,
                    }
                }), sort_keys=True))
                return 2
            if reconciliation["state"] == "retired":
                resolved_session, resolved_pane, target_resolution = _resolve_target_selector(
                    args.cwd,
                    args.session,
                    args.pane,
                    str(evidence["herdr"]["executable"]),
                    executor="codex",
                    env=environment,
                )
                pane_state = _herdr_pane(
                    args.cwd,
                    resolved_session,
                    resolved_pane,
                    str(evidence["herdr"]["executable"]),
                    executor="codex",
                    env=environment,
                )
                evidence["herdr"].update(
                    {
                        "session": resolved_session,
                        "pane": resolved_pane,
                        "pane_cwd": str(Path(str(pane_state["pane"]["cwd"])).resolve()),
                        "start_process_ids": sorted(
                            _process_ids(
                                pane_state["process_info"].get("foreground_processes", []),
                                require_non_shell=False,
                            )
                        ),
                    }
                )
                evidence["target_resolution"] = target_resolution
                evidence["observation"].update(
                    {"session": resolved_session, "pane": resolved_pane}
                )
                command = command.copy()
                command[command.index("--session") + 1] = resolved_session
                command[command.index("--pane") + 1] = resolved_pane
            _record_performance_attempt(
                performance_evidence,
                attempt_id,
                attempt_started,
                pane_run_duration_ms=pane_run_duration_ms,
            )
            agent_name = _unique_agent_name(str(evidence["herdr"]["agent_name"]))
            attempt_id = uuid.uuid4().hex
            evidence["registry_launcher"]["attempt_id"] = attempt_id
            evidence["observation"]["attempt_id"] = attempt_id
            command = command.copy()
            command[command.index("start") + 1] = agent_name
            evidence["herdr"]["agent_name"] = agent_name
            evidence["observation"]["agent_name"] = agent_name
            prompt_argv = evidence["assignment_request"].get("redacted_prompt_argv")
            if isinstance(prompt_argv, list) and "prompt" in prompt_argv:
                prompt_argv[prompt_argv.index("prompt") + 1] = agent_name
        if result.stdout:
            _write_runtime_output(sys.stdout, result.stdout)
        if result.stderr:
            _write_runtime_output(sys.stderr, result.stderr)
        if result.returncode:
            record_phase("delivery", attempt_started)
            print(json.dumps(emit_assignment({
                "assignment": {
                    "agent_name": evidence["herdr"]["agent_name"],
                    "attempt_id": attempt_id,
                    "delivery_state": "delivery_failed",
                    "delivery_certainty": "not_delivered",
                    "delivery_task_sha256": delivery_task_sha256,
                    "exit_code": result.returncode,
                    "failure_kind": "command_exit",
                    "phase": "pane_run" if args.executor == "deepagents" else "start",
                    "reconciliation_required": True,
                    "session": resolved_session,
                    "status": "failed",
                    "grant_digest": grant_digest,
                    "task_sha256": assignment_task_sha256,
                }
            }), sort_keys=True))
            return result.returncode
        if args.executor == "codex":
            herdr = str(evidence["herdr"]["executable"])
            agent_name = str(evidence["herdr"]["agent_name"])
            runtime_grant = (
                registry_launcher.get("runtime_grant")
                if isinstance(registry_launcher, dict)
                else None
            )
            delivery_task = _validate_task(args.task)
            if (
                isinstance(runtime_grant, dict)
                and isinstance(runtime_grant.get("delegation"), dict)
                and "child_agents" in runtime_grant["delegation"]
            ):
                delivery_task = _project_runtime_grant(delivery_task, runtime_grant)
            delivery_task_sha256 = registry_launcher.get(
                "delivery_task_sha256",
                _sha256_text(delivery_task),
            )
            grant_digest = registry_launcher.get("grant_digest")
            assignment = _codex_assignment_command(
                herdr,
                resolved_session,
                agent_name,
                delivery_task,
            )
            transport_timeout: CommandTransportTimeout | None = None
            assignment_result: subprocess.CompletedProcess[str] | None = None
            try:
                assignment_result = _run(
                    assignment,
                    env=environment,
                    timeout=_CODEX_ASSIGNMENT_TIMEOUT,
                )
            except CommandTransportTimeout as exc:
                transport_timeout = exc
            if transport_timeout is not None:
                record_phase("delivery", attempt_started)
                print(json.dumps(emit_assignment({
                    "assignment": {
                        "agent_name": agent_name,
                        "attempt_id": attempt_id,
                        "delivery_state": "delivery_uncertain",
                        "delivery_certainty": "unknown",
                        "delivery_task_sha256": delivery_task_sha256,
                        "exit_code": 2,
                        "failure_kind": "transport_timeout",
                        "grant_digest": grant_digest,
                        "phase": "prompt",
                        "prompt_accepted": None,
                        "reconciliation_required": True,
                        "session": resolved_session,
                        "status": "uncertain",
                        "task_sha256": assignment_task_sha256,
                    }
                }), sort_keys=True))
                return 2
            if assignment_result is None:
                raise LaunchBlocked("Codex assignment produced no result.")
            if assignment_result.stdout:
                print(assignment_result.stdout, end="")
            if assignment_result.stderr:
                print(assignment_result.stderr, file=sys.stderr, end="")
            prompt_result = _classify_codex_prompt_result(assignment_result)
            if prompt_result["submission"] == "unknown":
                record_phase("delivery", attempt_started)
                print(json.dumps(emit_assignment({
                    "assignment": {
                        "agent_name": agent_name,
                        "attempt_id": attempt_id,
                        "delivery_state": "delivery_uncertain",
                        "delivery_certainty": "unknown",
                        "delivery_task_sha256": delivery_task_sha256,
                        "exit_code": assignment_result.returncode,
                        "failure_kind": prompt_result["failure_kind"],
                        "grant_digest": grant_digest,
                        "phase": "prompt",
                        "prompt_accepted": None,
                        "reconciliation_required": True,
                        "session": resolved_session,
                        "status": "uncertain",
                        "submission": "unknown",
                        "task_sha256": assignment_task_sha256,
                    }
                }), sort_keys=True))
                return assignment_result.returncode
            if prompt_result["submission"] == "rejected":
                record_phase("delivery", attempt_started)
                print(json.dumps(emit_assignment({
                    "assignment": {
                        "agent_name": agent_name,
                        "attempt_id": attempt_id,
                        "delivery_state": "delivery_failed",
                        "delivery_certainty": "not_delivered",
                        "delivery_task_sha256": delivery_task_sha256,
                        "exit_code": assignment_result.returncode,
                        "failure_kind": prompt_result["failure_kind"],
                        "grant_digest": grant_digest,
                        "phase": "prompt",
                        "prompt_accepted": False,
                        "reconciliation_required": False,
                        "session": resolved_session,
                        "status": "failed",
                        "submission": "rejected",
                        "task_sha256": assignment_task_sha256,
                    }
                }), sort_keys=True))
                return assignment_result.returncode
            execution = {
                "state": "unknown",
                "observation_error": "not_observed",
                "observed_at": None,
            }
            observation = dict(evidence.get("observation", {}))
            observation.update(execution)
            observation["session"] = resolved_session
            observation["pane"] = resolved_pane
            observation["agent_name"] = agent_name
            record_phase("delivery", attempt_started)
            print(json.dumps(emit_assignment({
                "assignment": {
                    "agent_name": agent_name,
                    "attempt_id": attempt_id,
                    "completion_observed": False,
                    "delivery_state": "delivered",
                    "delivery_certainty": "confirmed",
                    "delivery_task_sha256": delivery_task_sha256,
                    "execution": execution,
                    "observation": observation,
                    "task_result": {"state": "unknown", "accepted": False},
                    "cleanup": {"state": "unknown"},
                    "exit_code": 0,
                    "failure_kind": None,
                    "grant_digest": grant_digest,
                    "phase": "prompt",
                    "prompt_accepted": True,
                    "reconciliation_required": False,
                    "session": resolved_session,
                    "status": "submitted",
                    "submission": "acknowledged",
                    "task_sha256": assignment_task_sha256,
                }
            }), sort_keys=True))
            return 0
        if result.returncode:
            record_phase("delivery", attempt_started)
            print(json.dumps(emit_assignment({
                "assignment": {
                    "agent_name": evidence["herdr"]["agent_name"],
                    "attempt_id": attempt_id,
                    "delivery_state": "delivery_failed",
                    "delivery_certainty": "not_delivered",
                    "delivery_task_sha256": delivery_task_sha256,
                    "exit_code": result.returncode,
                    "failure_kind": "command_exit",
                    "grant_digest": grant_digest,
                    "phase": "pane_run",
                    "reconciliation_required": True,
                    "session": resolved_session,
                    "status": "failed",
                    "task_sha256": assignment_task_sha256,
                }
            }), sort_keys=True))
            return result.returncode
        observation_started = time.monotonic()
        completion = _deepagents_completion_evidence(
            str(evidence["herdr"]["executable"]),
            resolved_session,
            resolved_pane,
            env=environment,
            expected_marker=completion_marker,
        )
        record_phase("observation", observation_started)
        task_state = str(completion["state"])
        if completion.get("observation_error") is not None and task_state == "completed":
            task_state = "no-report"
        foreground_processes = completion.get("foreground_processes", [])
        worker_live = any(
            str(name).lower() not in _DEEPAGENTS_SHELL_PROCESS_NAMES
            for name in foreground_processes
        )
        execution_state = "running" if worker_live else (
            "exited" if task_state in {"completed", "failed", "no-report"} else "unknown"
        )
        task_verified = (
            not worker_live
            and completion.get("marker_present") is True
            and completion.get("report_present") is True
            and completion.get("observation_error") is None
        )
        completed = task_state == "completed" and task_verified
        record_phase("delivery", attempt_started)
        print(json.dumps(emit_assignment({
            "assignment": {
                "agent_name": evidence["herdr"]["agent_name"],
                "attempt_id": attempt_id,
                "completion": completion,
                "execution": {
                    "state": execution_state,
                    "worker_exit_code": None,
                    "marker_reported": completion.get("marker_present") is True,
                    "last_observed_state": completion.get("last_observed_state"),
                },
                "observation": completion,
                "task_result": {
                    "state": "verified" if task_verified else "unknown",
                    "accepted": completed,
                },
                "cleanup": {
                    "state": "unknown" if worker_live else ("unverified" if completed else "unknown"),
                },
                "delivery_state": "delivered",
                "delivery_certainty": "confirmed",
                "delivery_task_sha256": delivery_task_sha256,
                "exit_code": 0 if completed else 2,
                "failure_kind": None if completed else task_state,
                "grant_digest": grant_digest,
                "phase": "pane_run",
                "reconciliation_required": not completed,
                "session": resolved_session,
                "status": task_state,
                "task_accepted": completed,
                "task_sha256": assignment_task_sha256,
            }
        }), sort_keys=True))
        return 0 if completed else 2
    except TargetResolutionBlocked as exc:
        print(f"TARGET_RESOLUTION: {exc}", file=sys.stderr)
        return emit_failure(str(exc), exc.resolution)
    except LaunchBlocked as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return emit_failure(str(exc))



def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    metrics = {"total": 0, "by_executable": {}}
    token = _ACTIVE_METRICS.set(metrics)
    try:
        return _main_body(args)
    finally:
        _ACTIVE_METRICS.reset(token)


if __name__ == "__main__":
    raise SystemExit(main())
