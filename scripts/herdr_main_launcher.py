"""Launch one registry-bound top-level lane through Herdr."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from contextlib import contextmanager
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
try:
    from project_os_runtime.results import (
        RESULT_MAX_AGE_SECONDS,
        RESULT_MAX_BYTES,
        RESULT_SCHEMA,
        parse_task_result,
        parse_result_receipt,
    )
except ModuleNotFoundError:
    from scripts.project_os_runtime.results import (
        RESULT_MAX_AGE_SECONDS,
        RESULT_MAX_BYTES,
        RESULT_SCHEMA,
        parse_task_result,
        parse_result_receipt,
    )
try:
    from project_os_runtime.attempt import (
        AttemptContractError,
        WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
        capability_digest,
        grant_digest,
        normalize_local_capabilities,
        normalize_runtime_grant,
        remaining_attempt_seconds,
        resolve_attempt_budget,
        terminal_settlement_proven,
    )
except ModuleNotFoundError:
    from scripts.project_os_runtime.attempt import (
        AttemptContractError,
        WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
        capability_digest,
        grant_digest,
        normalize_local_capabilities,
        normalize_runtime_grant,
        remaining_attempt_seconds,
        resolve_attempt_budget,
        terminal_settlement_proven,
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
_DEEPAGENTS_COMPLETION_WAIT_SECONDS = 120.0
# ponytail: fixed 30s receipt grace; increase only with measured receipt latency.
_DEEPAGENTS_RECEIPT_GRACE_SECONDS = 30.0
_DEEPAGENTS_COMPLETION_POLL_SECONDS = 1.0
_DEEPAGENTS_RECEIPT_POLL_SECONDS = 0.1
_DEEPAGENTS_OBSERVATION_RESERVE_SECONDS = 0.1
_CODEX_ASSIGNMENT_TIMEOUT = _CODEX_TASK_PROGRESS_TIMEOUT_SECONDS + 5.0
_CODEX_START_TIMEOUT = (float(_CODEX_START_TIMEOUT_MS) / 1000) + 5.0
_TARGET_DISCOVERY_TIMEOUT = 5.0
_HERDR_DEFAULT_SESSION = "default"
_PANE_LOCK_PARENT = "herdr-pane-ownership"
_NATIVE_GRANT_VALUE = "native"
_CHILD_AGENT_GRANT_VALUES = {"allow", "deny"}
_SHELL_PROCESS_NAMES = {"powershell.exe", "pwsh.exe", "cmd.exe", "bash", "sh", "zsh", "fish"}
_DEEPAGENTS_SHELL_PROCESS_NAMES = {"powershell.exe", "pwsh.exe"}
_HERDR_AGENT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
_HERDR_AGENT_NAME_MAX_LENGTH = 32
_DEEPAGENTS_RESULT_SCHEMA = RESULT_SCHEMA
_DEEPAGENTS_RESULT_MAX_BYTES = RESULT_MAX_BYTES
_DEEPAGENTS_RESULT_MAX_AGE_SECONDS = RESULT_MAX_AGE_SECONDS
_DEEPAGENTS_FAILURE_PATTERN = re.compile(
    r"(?im)^(?:FAIL|BLOCKED)(?::(?:\s.*)?)?$|^\s*(?:\[FAIL\]\s*)?Task failed\b|^\s*Traceback \(most recent call last\):|^\s*ERROR:\s*"
)
_CODEX_PROMPT_REJECTION_CODES = {
    "agent_blocked",
    "agent_not_found",
    "agent_prompt_rejected",
    "agent_not_running",
    "empty_agent_prompt",
    "invalid_agent",
    "invalid_prompt",
}
_CODEX_ACTIVE_AGENT_STATES = {"idle", "working"}
_ACTIVE_METRICS: ContextVar[dict[str, Any] | None] = ContextVar(
    "herdr_launcher_metrics",
    default=None,
)
_PERFORMANCE_PHASES = (
    "preflight",
    "target_discovery",
    "launch_preparation",
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


def _normalize_local_capabilities(values: object) -> list[str]:
    try:
        return normalize_local_capabilities(values)
    except AttemptContractError as exc:
        raise LaunchBlocked(str(exc)) from exc


def _read_deepagents_receipt(path: Path | None, attempt_id: str) -> dict[str, Any]:
    if path is None:
        return {"state": "unknown", "detail": "receipt unavailable"}
    return parse_result_receipt(path, attempt_id)


def _read_deepagents_task_result(
    path: Path | None,
    *,
    assignment_id: str | None,
    attempt_id: str,
    task_sha256: str | None,
    grant_digest_value: str | None,
) -> dict[str, Any]:
    if path is None or not all(
        isinstance(value, str) and value for value in (
            assignment_id, task_sha256, grant_digest_value
        )
    ):
        return {"state": "unknown", "continuation_eligible": False, "detail": "task result binding unavailable"}
    return parse_task_result(
        path,
        assignment_id=assignment_id,
        attempt_id=attempt_id,
        task_sha256=task_sha256,
        grant_digest=grant_digest_value,
    )


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
    shell_names = _shell_process_names(executor)
    conflicting: list[str] = []
    try:
        processes = _process_records(foreground, require_pid=False)
    except LaunchBlocked as exc:
        raise TargetCandidateRejected(str(exc)) from exc
    for process in processes:
        process_name = str(process.get("name", "unknown"))
        if process_name.lower() not in shell_names:
            conflicting.append(process_name)
    if conflicting:
        raise TargetCandidateRejected(f"Pane has conflicting foreground process: {', '.join(conflicting)}")
    return {"pane": selected, "process_info": process_info}


def _pane_ownership_lock_path(cwd: Path, session: str, pane: str) -> Path:
    identity = f"{session}\0{pane}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / _PANE_LOCK_PARENT / f"{digest}.lock"


@contextmanager
def _pane_ownership_lock(cwd: Path, session: str, pane: str):
    path = _pane_ownership_lock_path(cwd, session, pane)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    if os.name == "nt" and os.fstat(fd).st_size == 0:
        os.write(fd, b"\0")
    os.set_inheritable(fd, False)
    acquired = False
    try:
        try:
            if os.name == "nt":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LaunchBlocked(
                f"Another launch owns pane `{session}:{pane}`."
            ) from exc
        acquired = True
        yield
    finally:
        try:
            if acquired:
                if os.name == "nt":
                    import msvcrt

                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _run_with_pane_ownership(
    cwd: Path,
    session: str,
    pane: str,
    herdr: str,
    executor: str,
    command: list[str],
    env: dict[str, str],
    timeout: float,
    verify: bool = True,
) -> subprocess.CompletedProcess[str]:
    with _pane_ownership_lock(cwd, session, pane):
        if verify:
            _herdr_pane(cwd, session, pane, herdr, executor=executor, env=env)
        return _run(command, env=env, timeout=timeout)


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
        "--dangerously-bypass-hook-trust",
        "-c",
        "check_for_update_on_startup=false",
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
    evidence = {
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
    evidence["phase_durations_ms"]["worker_initialization"]["status"] = "unavailable"
    evidence["phase_aggregates"]["worker_initialization"]["status"] = "unavailable"
    evidence["_phase_intervals"] = []
    return evidence


def _record_performance_phase(
    performance: dict[str, Any],
    name: str,
    started: float,
    *,
    now: float | None = None,
    attempt_id: str | None = None,
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
    occurrence = {**durations[name], "attempt_id": attempt_id}
    occurrences.append(occurrence)
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
    intervals = performance.setdefault("_phase_intervals", [])
    if not isinstance(intervals, list):
        raise LaunchBlocked("Performance phase intervals must be an array.")
    intervals.append({"start": started, "end": current, "name": name})
    performance["subprocess_counts"] = _metrics_snapshot()


def _record_performance_attempt(
    performance: dict[str, Any],
    attempt_id: str,
    started: float,
    *,
    now: float | None = None,
    pane_run_duration_ms: float | None = None,
) -> None:
    current = time.monotonic() if now is None else now
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
    current = time.monotonic() if now is None else now
    performance["status"] = "measured"
    performance["total_duration_ms"] = round(max(0.0, current - started) * 1000, 3)
    intervals = [
        (max(started, float(interval["start"])), min(current, float(interval["end"])))
        for interval in performance.pop("_phase_intervals", [])
        if isinstance(interval, dict)
        and isinstance(interval.get("start"), (int, float))
        and isinstance(interval.get("end"), (int, float))
        and float(interval["end"]) > started
    ]
    intervals.sort()
    covered = 0.0
    covered_start: float | None = None
    covered_end: float | None = None
    for interval_start, interval_end in intervals:
        if interval_end <= interval_start:
            continue
        if covered_start is None:
            covered_start, covered_end = interval_start, interval_end
        elif interval_start <= covered_end:
            covered_end = max(covered_end, interval_end)
        else:
            covered += covered_end - covered_start
            covered_start, covered_end = interval_start, interval_end
    if covered_start is not None and covered_end is not None:
        covered += covered_end - covered_start
    performance["unattributed_duration_ms"] = round(
        max(0.0, performance["total_duration_ms"] - covered * 1000),
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
    task_state = task_result.get("state", "unknown")
    execution_state = execution.get("state", "unknown")
    observation_state = observation.get("state", "unknown")
    cleanup_state = cleanup.get("state", "unknown")
    status = legacy_values.get("status")
    if status is None:
        if task_state == "reported_failed":
            status = "failed"
        elif execution_state in {
            "failed",
            "start_failed",
            "recovery_blocked",
            "completed",
            "running",
        }:
            status = execution_state
        elif delivery_state in {"delivery_failed", "delivery_uncertain"}:
            status = "failed" if delivery_state == "delivery_failed" else "uncertain"
        else:
            status = "unknown"
    failure_kind = legacy_values.get("failure_kind")
    if failure_kind is None:
        if task_state == "reported_failed":
            failure_kind = "task_report_failed"
        elif execution_state == "start_failed":
            failure_kind = "worker_start_failed"
        elif execution_state == "failed":
            failure_kind = "worker_exit"
        elif delivery_state == "delivery_failed":
            failure_kind = "delivery_failed"
        elif delivery_state == "delivery_uncertain":
            failure_kind = "delivery_uncertain"
    if "reconciliation_required" in legacy_values:
        reconciliation_required = bool(legacy_values["reconciliation_required"])
    else:
        reconciliation_required = bool(delivery.get("reconciliation_required")) or (
            execution_state in {"unknown", "running"}
            or observation_state in {"unknown", "timed_out"}
            or task_state in {"unknown", "unverified"}
            or cleanup_state in {"unknown", "preserved", "unverified"}
        )
    assignment = {
        "agent_name": agent_name,
        "attempt_id": attempt_id,
        "assignment_id": legacy_values.get("assignment_id"),
        "repository_identity": legacy_values.get("repository_identity"),
        "plan_identity": legacy_values.get("plan_identity"),
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
        "failure_kind": failure_kind,
        "grant_digest": legacy_values.get("grant_digest"),
        "phase": legacy_values.get("phase"),
        "prompt_accepted": delivery.get("prompt_accepted"),
        "reconciliation_required": reconciliation_required,
        "session": legacy_values.get("session"),
        "status": status,
        "submission": delivery.get("submission"),
        "task_accepted": task_accepted,
        "task_sha256": legacy_values.get("task_sha256"),
    }
    for key, value in legacy_values.items():
        if key not in assignment:
            assignment[key] = value
    return {"assignment": assignment}


def _classify_deepagents_outcome(
    *,
    delivery: dict[str, Any],
    observation: dict[str, Any],
    receipt: dict[str, Any],
    fallback_failure_kind: str | None,
    task_result_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    execution = {"state": "unknown", "worker_exit_code": None}
    cleanup = {"state": "unknown"}
    task_result = {"state": "unverified", "accepted": None}
    if isinstance(task_result_evidence, dict) and task_result_evidence.get("state") == "confirmed":
        task_result = dict(task_result_evidence)
        task_result["state"] = {
            "completed": "reported_completed",
            "failed": "reported_failed",
        }.get(str(task_result.get("status")), "unverified")
        task_result["accepted"] = None
    status = "unknown"
    failure_kind = fallback_failure_kind
    reconciliation_required = True
    launcher_exit_code = 2

    if receipt.get("state") == "confirmed":
        worker_state = receipt["worker_state"]
        worker_exit_code = receipt.get("worker_exit_code")
        descendant_state = receipt.get("descendant_state")
        cleanup_state = receipt["cleanup_state"]
        recovery_required = receipt.get("recovery_required", False)
        cleanup = {
            "state": cleanup_state,
            "role_views_state": receipt.get("role_views_state"),
            "remaining_paths": receipt.get("remaining_paths", []),
            "marker_state": receipt.get("marker_state"),
            "recovery_required": recovery_required,
        }
        execution = {
            "state": "unknown",
            "worker_exit_code": worker_exit_code,
            "descendant_state": descendant_state,
            "recovery_required": recovery_required,
        }
        if worker_state == "start_failed":
            execution["state"] = "start_failed"
            status = "start_failed"
            failure_kind = "worker_start_failed"
        elif worker_state == "recovery_blocked":
            status = "recovery_blocked"
            failure_kind = "worker_recovery_blocked"
        elif worker_state == "exited" and isinstance(worker_exit_code, int):
            if worker_exit_code == 0:
                execution["state"] = "completed"
                status = "completed"
                report_observed = (
                    observation.get("report_present") is True
                    and observation.get("observation_error") is None
                )
                if task_result["state"] == "reported_failed":
                    status = "failed"
                    failure_kind = "task_report_failed"
                elif task_result["state"] == "reported_completed":
                    failure_kind = None
                elif observation.get("receipt_authoritative"):
                    failure_kind = "task_result_unverified"
                elif observation.get("state") == "failed" and report_observed:
                    task_result = {
                        "state": "reported_failed",
                        "accepted": False,
                        "source": "herdr_pane",
                        "authoritative": False,
                    }
                    status = "failed"
                    failure_kind = "task_report_failed"
                else:
                    if task_result["state"] not in {"reported_completed", "reported_failed"}:
                        task_result = {
                            "state": "reported_completed" if report_observed else "unverified",
                            "accepted": None,
                        }
                    if report_observed and task_result.get("source") is None:
                        task_result.update({"source": "herdr_pane", "authoritative": False})
                if not report_observed and not observation.get("receipt_authoritative"):
                    failure_kind = "completion_evidence_missing"
            else:
                execution["state"] = "failed"
                status = "failed"
                failure_kind = "worker_exit"
        elif worker_state == "failed":
            execution["state"] = "failed"
            status = "failed"
            failure_kind = "worker_failed"
        else:
            failure_kind = "worker_exit_unknown"

        cleanup_settled = terminal_settlement_proven(
            receipt,
            cleanup_confirmed=cleanup_state == "removed",
            descendants_retired=descendant_state in {"terminated", "not_started"},
        )
        completed_evidence = (
            worker_state == "exited"
            and worker_exit_code == 0
            and cleanup_settled
            and task_result["state"] == "reported_completed"
        )
        if worker_state == "exited" and worker_exit_code == 0:
            launcher_exit_code = 0 if completed_evidence else 2
        elif isinstance(worker_exit_code, int) and worker_exit_code != 0:
            launcher_exit_code = worker_exit_code
        if not cleanup_settled:
            failure_kind = "cleanup_recovery_required"
        reconciliation_required = launcher_exit_code != 0
    else:
        failure_kind = fallback_failure_kind or receipt.get("detail") or "receipt_unavailable"

    return {
        "delivery": delivery,
        "execution": execution,
        "observation": observation,
        "task_result": task_result,
        "cleanup": cleanup,
        "status": status,
        "failure_kind": failure_kind,
        "reconciliation_required": reconciliation_required,
        "launcher_exit_code": launcher_exit_code,
    }


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


def _confirm_codex_start(
    herdr: str,
    session: str,
    pane: str,
    agent_name: str,
    *,
    env: dict[str, str],
    before_process_ids: set[int],
    expected_codex_executable: str,
    expected_cwd: Path,
) -> dict[str, Any]:
    try:
        agent_payload = _json_command(
            [herdr, "--session", session, "agent", "get", agent_name],
            env=env,
        )
        agent = _result(agent_payload, "agent")
        if not isinstance(agent, dict):
            raise LaunchBlocked("Codex agent information is invalid.")
        agent_status = str(agent.get("agent_status") or "unknown")
        if agent_status not in _CODEX_ACTIVE_AGENT_STATES:
            raise LaunchBlocked(
                f"Codex agent is not active before prompt delivery: {agent_status}."
            )
        process_payload = _json_command(
            [herdr, "--session", session, "pane", "process-info", "--pane", pane],
            env=env,
        )
        process_info = _result(process_payload, "process_info")
        if not isinstance(process_info, dict):
            raise LaunchBlocked("Codex process information is invalid.")
        processes = _process_records(process_info.get("foreground_processes"))
        process_ids = _process_ids(processes, require_non_shell=True)
    except (CommandTransportTimeout, LaunchBlocked, json.JSONDecodeError) as exc:
        if isinstance(exc, LaunchBlocked) and str(exc).startswith("Codex "):
            raise
        raise LaunchBlocked("Codex process is not running before prompt delivery.") from exc
    owned_process_ids = {
        int(process["pid"])
        for process in processes
        if int(process["pid"]) not in before_process_ids
        and str(process.get("name", "")).lower() not in _SHELL_PROCESS_NAMES
        and _matches_codex_process(process, expected_codex_executable, expected_cwd)
    }
    if not owned_process_ids:
        raise LaunchBlocked("Codex process ownership is unconfirmed before prompt delivery.")
    return {"agent_status": agent_status, "process_ids": sorted(owned_process_ids)}


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
    expected_codex_executable: str | None = None,
    expected_cwd: Path | None = None,
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
        processes = _process_records(foreground)
        process_ids = _process_ids(processes, require_non_shell=False)
        if not process_ids:
            return {"state": "absent", "cleanup": None, "process_ids": []}
        if before_process_ids is None or not (process_ids - before_process_ids):
            return {
                "state": "uncertain",
                "cleanup": None,
                "process_ids": sorted(process_ids),
                "detail": "no new process proves failed-attempt ownership",
            }
        if expected_codex_executable is None or expected_cwd is None:
            return {
                "state": "uncertain",
                "cleanup": None,
                "process_ids": sorted(process_ids),
                "detail": "Codex identity evidence is unavailable",
            }
        owned_processes = [
            process
            for process in processes
            if int(process["pid"]) not in before_process_ids
            and str(process.get("name", "")).lower() not in _SHELL_PROCESS_NAMES
            and _matches_codex_process(process, expected_codex_executable, expected_cwd)
        ]
        if not owned_processes:
            return {
                "state": "uncertain",
                "cleanup": None,
                "process_ids": sorted(process_ids),
                "detail": "no new process proves failed-attempt Codex ownership",
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


def _validate_agent_name(agent_name: str) -> None:
    if (
        len(agent_name) > _HERDR_AGENT_NAME_MAX_LENGTH
        or not _HERDR_AGENT_NAME_PATTERN.fullmatch(agent_name)
    ):
        raise LaunchBlocked(
            "Invalid Herdr agent name: expected lowercase letters, digits, '-' or '_' "
            f"and at most {_HERDR_AGENT_NAME_MAX_LENGTH} characters."
        )


def _unique_agent_name(agent_name: str) -> str:
    suffix = uuid.uuid4().hex[:8]
    return f"{agent_name[:_HERDR_AGENT_NAME_MAX_LENGTH - len(suffix) - 1]}-{suffix}"


def _codex_watchdog_seconds(evidence: dict[str, Any]) -> int | None:
    registry = evidence.get("registry_launcher")
    grant = registry.get("runtime_grant") if isinstance(registry, dict) else None
    wall_clock = grant.get("wall_clock_seconds") if isinstance(grant, dict) else None
    requested = wall_clock.get("requested") if isinstance(wall_clock, dict) else None
    return requested if isinstance(requested, int) else None


def _shell_process_names(executor: str) -> set[str]:
    return _DEEPAGENTS_SHELL_PROCESS_NAMES if executor == "deepagents" else _SHELL_PROCESS_NAMES


def _process_records(processes: Any, *, require_pid: bool = True) -> list[dict[str, Any]]:
    if not isinstance(processes, list):
        raise LaunchBlocked("process information is not an array")
    records: list[dict[str, Any]] = []

    def collect(process: Any) -> None:
        if not isinstance(process, dict):
            raise LaunchBlocked("process information contains invalid process data")
        pid = process.get("pid")
        if require_pid and (not isinstance(pid, int) or pid <= 0):
            raise LaunchBlocked("process information contains process without pid")
        children = process.get("children", [])
        if not isinstance(children, list):
            raise LaunchBlocked("process information contains invalid child processes")
        records.append(process)
        for child in children:
            collect(child)

    for process in processes:
        collect(process)
    return records


def _process_ids(
    processes: Any,
    *,
    require_non_shell: bool,
    shell_names: set[str] | None = None,
) -> set[int]:
    records = _process_records(processes)
    if not records:
        raise LaunchBlocked("termination verification returned empty process information")
    shell_names = shell_names or _SHELL_PROCESS_NAMES
    process_ids: set[int] = set()
    process_ids.update(
        int(process["pid"])
        for process in records
        if str(process.get("name", "")).lower() not in shell_names
    )
    if require_non_shell and not process_ids:
        raise LaunchBlocked("termination verification found no launch-owned process")
    return process_ids


def _matches_codex_process(
    process: dict[str, Any],
    expected_executable: str,
    expected_cwd: Path,
) -> bool:
    expected_name = Path(expected_executable).name.lower()
    executable_match = any(
        value and Path(str(value)).name.lower() == expected_name
        for value in (process.get("argv0"), process.get("name"))
    )
    process_cwd = process.get("cwd")
    return bool(
        executable_match
        and isinstance(process_cwd, str)
        and Path(process_cwd).resolve() == expected_cwd.resolve()
    )


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
    expected_marker: str | None,
) -> str:
    live_process = any(
        str(process.get("name", "")).lower() not in _DEEPAGENTS_SHELL_PROCESS_NAMES
        for process in foreground_processes
        if isinstance(process, dict)
    )
    raw_lines = [line.rstrip() for line in pane_output.splitlines() if line.strip()]
    lines = [line.strip() for line in raw_lines]
    start_index = max(
        (index for index, line in enumerate(lines) if line == "Running task non-interactively..."),
        default=0,
    )
    current_lines = lines[start_index:]
    current_raw_lines = raw_lines[start_index:]
    if _DEEPAGENTS_FAILURE_PATTERN.search("\n".join(current_raw_lines)):
        return "failed"
    if expected_marker and any(
        current_lines[index:index + 2] == ["COMPLETED", expected_marker]
        for index in range(len(current_lines) - 1)
    ):
        return "running" if live_process else "completed"
    if "COMPLETED" in current_lines:
        return "running" if live_process else "no-report"
    if live_process:
        return "running"
    return "no-report"


def _deepagents_marker_present(pane_output: str, expected_marker: str) -> bool:
    if not expected_marker:
        return False
    lines = [line.strip() for line in pane_output.splitlines() if line.strip()]
    start_index = max(
        (index for index, line in enumerate(lines) if line == "Running task non-interactively..."),
        default=0,
    )
    current_lines = lines[start_index:]
    return any(
        current_lines[index:index + 2] == ["COMPLETED", expected_marker]
        for index in range(len(current_lines) - 1)
    )


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
    expected_marker: str | None,
    deadline: float | None = None,
    wait_for_marker: bool = True,
    marker_observed: bool = False,
) -> dict[str, Any]:
    def observation_timeout() -> float:
        if deadline is None:
            return _HERDR_COMMAND_TIMEOUT
        return min(_HERDR_COMMAND_TIMEOUT, deadline - time.monotonic())

    def observation_deadline_expired() -> bool:
        return deadline is not None and deadline - time.monotonic() <= 0

    process_result: subprocess.CompletedProcess[str] | None = None
    read_result: subprocess.CompletedProcess[str] | None = None
    process_error: str | None = None
    read_error: str | None = None
    observation_deadline_exceeded = False
    marker_wait_state = (
        "skipped"
        if marker_observed or not wait_for_marker or not expected_marker
        else "not_attempted"
    )
    wait_timeout = observation_timeout()
    if expected_marker and wait_for_marker and not marker_observed and wait_timeout > 0:
        reserved = min(_DEEPAGENTS_OBSERVATION_RESERVE_SECONDS, wait_timeout / 2)
        wait_timeout = max(0.0, wait_timeout - reserved)
    if expected_marker and wait_for_marker and not marker_observed and wait_timeout > 0:
        try:
            wait_result = _run(
                [
                    herdr,
                    "--session",
                    session,
                    "pane",
                    "wait-output",
                    "--regex",
                    rf"(?m)^{re.escape(expected_marker)}$",
                    "--source",
                    "recent-unwrapped",
                    "--lines",
                    "200",
                    "--timeout",
                    str(max(1, int(wait_timeout * 1000))),
                    pane,
                ],
                env=env,
                timeout=min(_HERDR_COMMAND_TIMEOUT, wait_timeout),
            )
            marker_wait_state = "observed" if wait_result.returncode == 0 else "expired"
        except CommandTransportTimeout:
            marker_wait_state = "transport_failed"
            observation_deadline_exceeded = observation_deadline_expired()
    try:
        timeout = observation_timeout()
        if deadline is not None:
            timeout = max(0.0, timeout - (2 * _DEEPAGENTS_OBSERVATION_RESERVE_SECONDS))
        if timeout <= 0:
            observation_deadline_exceeded = True
            raise CommandTransportTimeout("observation deadline exceeded before process-info")
        process_result = _run(
            [herdr, "--session", session, "pane", "process-info", "--pane", pane],
            env=env,
            timeout=timeout,
        )
    except CommandTransportTimeout:
        observation_deadline_exceeded = observation_deadline_expired()
        process_error = (
            "observation deadline exceeded"
            if observation_deadline_exceeded
            else "pane process-info transport timeout"
        )
    if observation_deadline_expired():
        observation_deadline_exceeded = True
        process_error = "observation deadline exceeded"
    try:
        timeout = observation_timeout()
        if timeout <= 0:
            observation_deadline_exceeded = True
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
        observation_deadline_exceeded = observation_deadline_expired()
        read_error = (
            "observation deadline exceeded"
            if observation_deadline_exceeded
            else "pane read transport timeout"
        )
    pane_output = _pane_output(read_result) if read_result is not None else ""
    foreground: list[Any] = []
    observation_error: str | None = process_error or read_error
    if marker_wait_state == "transport_failed":
        observation_error = observation_error or "pane wait-output transport timeout"
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
        "marker_present": marker_observed or _deepagents_marker_present(pane_output, expected_marker),
        "report_present": state in {"completed", "failed"},
        "report_sha256": _sha256_text(pane_output),
        "report_chars": len(pane_output),
        "observed_at": time.time(),
        "observation_deadline_exceeded": observation_deadline_exceeded,
        "foreground_processes": [
            str(process.get("name", "unknown"))
            for process in foreground
            if isinstance(process, dict)
        ],
        "observation_error": observation_error,
        "marker_wait_state": marker_wait_state,
    }


def _deepagents_completion_evidence(
    herdr: str,
    session: str,
    pane: str,
    *,
    env: dict[str, str],
    expected_marker: str | None,
    receipt_file: Path | None = None,
    attempt_id: str | None = None,
    completion_wait_seconds: float | None = None,
    attempt_deadline: float | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    observation_wait_seconds = (
        _DEEPAGENTS_COMPLETION_WAIT_SECONDS
        if completion_wait_seconds is None
        else completion_wait_seconds
    )
    if observation_wait_seconds < 0:
        raise LaunchBlocked("DeepAgents completion observation budget cannot be negative.")
    observation_deadline = started + observation_wait_seconds
    if attempt_deadline is not None:
        observation_deadline = min(
            observation_deadline,
            attempt_deadline - _DEEPAGENTS_RECEIPT_GRACE_SECONDS,
        )
    settlement_deadline = observation_deadline + _DEEPAGENTS_RECEIPT_GRACE_SECONDS
    if attempt_deadline is not None:
        settlement_deadline = min(settlement_deadline, attempt_deadline)
    evidence: dict[str, Any] | None = None
    receipt = _read_deepagents_receipt(receipt_file, attempt_id or "")
    terminal_observed_at: float | None = None

    def wait_for_receipt() -> dict[str, Any]:
        nonlocal receipt
        while receipt.get("state") != "confirmed":
            terminal_deadline = (
                min(terminal_observed_at + _DEEPAGENTS_RECEIPT_GRACE_SECONDS, settlement_deadline)
                if terminal_observed_at is not None
                else settlement_deadline
            )
            remaining = terminal_deadline - time.monotonic()
            if remaining <= 0:
                return receipt
            time.sleep(min(_DEEPAGENTS_RECEIPT_POLL_SECONDS, remaining))
            if time.monotonic() >= terminal_deadline:
                return receipt
            receipt = _read_deepagents_receipt(receipt_file, attempt_id or "")
        return receipt

    marker_observed = False
    while True:
        if receipt.get("state") == "confirmed":
            worker_state = receipt.get("worker_state")
            worker_exit_code = receipt.get("worker_exit_code")
            if worker_state == "exited" and worker_exit_code == 0:
                state = "completed"
            elif worker_state in {"exited", "failed", "start_failed", "recovery_blocked"}:
                state = "failed"
            else:
                state = "unknown"
            return {
                "state": state,
                "marker_present": False,
                "report_present": False,
                "foreground_processes": [],
                "observation_error": None,
                "receipt_authoritative": True,
                "lifecycle_receipt": receipt,
            }
        evidence = _deepagents_completion_snapshot(
            herdr,
            session,
            pane,
            env=env,
            expected_marker=expected_marker,
            deadline=observation_deadline,
            marker_observed=marker_observed,
        )
        marker_observed = marker_observed or evidence.get("marker_present") is True
        if receipt_file is not None and evidence.get("marker_wait_state") in {
            "observed",
            "expired",
            "transport_failed",
        }:
            receipt = _read_deepagents_receipt(receipt_file, attempt_id or "")
            if receipt.get("state") == "confirmed":
                evidence["lifecycle_receipt"] = receipt
                return evidence
        if evidence["state"] in {"completed", "failed"}:
            terminal_observed_at = time.monotonic()
            if receipt_file is None:
                return evidence
            receipt = wait_for_receipt()
            evidence["lifecycle_receipt"] = receipt
            return evidence
        remaining = observation_deadline - time.monotonic()
        if remaining <= 0:
            if receipt_file is not None:
                receipt = wait_for_receipt()
                if receipt.get("state") == "confirmed" and time.monotonic() < settlement_deadline:
                    evidence = _deepagents_completion_snapshot(
                        herdr,
                        session,
                        pane,
                        env=env,
                        expected_marker=expected_marker,
                        deadline=settlement_deadline,
                        wait_for_marker=False,
                        marker_observed=marker_observed,
                    )
                evidence["lifecycle_receipt"] = receipt
                return evidence
            evidence["last_observed_state"] = evidence["state"]
            evidence["state"] = "timed_out"
            evidence["observation_deadline_exceeded"] = True
            if receipt_file is not None:
                evidence["lifecycle_receipt"] = receipt
            return evidence
        time.sleep(min(_DEEPAGENTS_COMPLETION_POLL_SECONDS, remaining))
        receipt = _read_deepagents_receipt(receipt_file, attempt_id or "")


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
        after_processes = _process_records(foreground)
        after_ids = _process_ids(after_processes, require_non_shell=False)
    except LaunchBlocked as exc:
        return {
            "requested": True,
            "action": "pane-close",
            "verified": False,
            "detail": str(exc),
        }
    remaining = [
        str(process.get("name", "unknown"))
        for process in after_processes
        if str(process.get("name", "")).lower() not in _SHELL_PROCESS_NAMES
    ]
    return {
        "requested": True,
        "action": "pane-close",
        "verified": not remaining and not (before_ids & after_ids),
        "state": "shell-only" if not remaining else "processes-remain",
        "remaining_foreground_processes": remaining,
        "remaining_processes": remaining,
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
    local_capabilities: list[str] | None = None,
    grant_turns: str | int | None = None,
    grant_wall_clock_seconds: str | int | None = None,
    grant_child_agents: str | None = None,
    task: str | None = None,
    name: str | None = None,
    codex_home: Path | None = None,
    assignment_id: str | None = None,
    repository_identity: str | None = None,
    plan_identity: str | None = None,
    task_sha256: str | None = None,
    grant_digest_value: str | None = None,
    remaining_authorized_task_allowance: int | float | None = None,
    attempt_deadline: float | None = None,
) -> tuple[list[str], dict[str, Any]]:
    launch_started = time.monotonic()
    attempt_deadline = attempt_deadline or launch_started + _DEEPAGENTS_RUN_TIMEOUT
    if executor not in _EXECUTORS:
        raise LaunchBlocked(f"Unsupported executor: {executor}")
    task_text = _validate_task(task)
    if executor == "deepagents" and assignment_id is not None and remaining_authorized_task_allowance is None:
        raise LaunchBlocked("Coordinated launch requires remaining authorized task allowance.")
    try:
        runtime_grant = normalize_runtime_grant(
            executor=executor,
            grant_turns=grant_turns,
            grant_wall_clock_seconds=grant_wall_clock_seconds,
            mcp_select=mcp_select,
            grant_child_agents=grant_child_agents,
        )
    except AttemptContractError as exc:
        message = str(exc)
        if executor == "codex" and "numeric wall-clock budget" in message:
            message = "Codex strict wall-clock enforcement is unavailable; use `native`."
        raise LaunchBlocked(message) from exc
    runtime_grant["outer_watchdog_seconds"] = int(_DEEPAGENTS_RUN_TIMEOUT) if executor == "deepagents" else None
    if executor == "deepagents":
        allowance = (
            WHOLE_ATTEMPT_WALL_CLOCK_SECONDS
            if remaining_authorized_task_allowance is None
            else remaining_authorized_task_allowance
        )
        try:
            resolve_attempt_budget(
                runtime_grant["wall_clock_seconds"]["requested"],
                allowance,
                remaining_attempt_seconds(time.monotonic() - launch_started),
            )
        except AttemptContractError as exc:
            raise LaunchBlocked(str(exc)) from exc
    requested_local_capabilities = list(local_capabilities or [])
    effective_local_capabilities = _normalize_local_capabilities(requested_local_capabilities)
    computed_grant_digest = grant_digest(executor, runtime_grant)
    if assignment_id is not None:
        if not isinstance(repository_identity, str) or not repository_identity.strip():
            raise LaunchBlocked("Coordinated launch requires repository identity.")
        if not isinstance(plan_identity, str) or not plan_identity.strip():
            raise LaunchBlocked("Coordinated launch requires plan identity.")
        if not isinstance(task_sha256, str) or not task_sha256:
            raise LaunchBlocked("Coordinated launch requires task identity.")
        if not isinstance(grant_digest_value, str) or not grant_digest_value:
            raise LaunchBlocked("Coordinated launch requires grant identity.")
        if task_sha256 != _sha256_text(task_text):
            raise LaunchBlocked("Launcher task identity does not match task text.")
        if grant_digest_value != computed_grant_digest:
            raise LaunchBlocked("Launcher grant identity does not match runtime grant.")
        expected_grant_digest = computed_grant_digest
    else:
        expected_grant_digest = computed_grant_digest
    lane_root = cwd.resolve()
    selected = _profile(lane_root / "agents", profile_name)
    if name is not None:
        _validate_agent_name(name)
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
    if executor == "deepagents":
        allowance = (
            WHOLE_ATTEMPT_WALL_CLOCK_SECONDS
            if remaining_authorized_task_allowance is None
            else remaining_authorized_task_allowance
        )
        try:
            effective_budget = resolve_attempt_budget(
                runtime_grant["wall_clock_seconds"]["requested"],
                allowance,
                max(0.0, attempt_deadline - time.monotonic()),
            )
        except AttemptContractError as exc:
            raise LaunchBlocked(str(exc)) from exc
        runtime_grant["wall_clock_seconds"]["effective"] = effective_budget
        runtime_grant["wall_clock_seconds"]["enforcement"] = "runtime"
    delivery_task = _project_runtime_grant(task_text, runtime_grant)
    completion_marker = None
    agent_name = name or (
        _unique_agent_name(f"{selected.name}-main")
        if executor == "codex"
        else f"{selected.name}-main"[:_HERDR_AGENT_NAME_MAX_LENGTH]
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
            *(["--timeout", str(runtime_grant["wall_clock_seconds"]["effective"])]
              if runtime_grant["wall_clock_seconds"]["effective"] != _NATIVE_GRANT_VALUE
              else []),
            *sum(
                (["--mcp-select", _powershell_literal(value)] for value in (mcp_select or [])),
                [],
            ),
            *sum(
                (["--local-capability", _powershell_literal(value)] for value in effective_local_capabilities),
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
            "assignment_id": assignment_id,
            "repository_identity": repository_identity,
            "plan_identity": plan_identity,
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
                "check_for_update_on_startup",
            ],
            "redacted_runtime_argv": _redacted_arguments(runtime_arguments),
            "assignment_task_sha256": _sha256_text(task_text),
            "grant_digest": expected_grant_digest,
            "runtime_grant": runtime_grant,
            "delivery_task_sha256": _sha256_text(delivery_task),
            "completion_marker": completion_marker,
            "mcp_selection_requested": list(mcp_select or []),
            "local_capabilities": {
                "requested": requested_local_capabilities,
                "effective": effective_local_capabilities,
                "verification_commands": list(effective_local_capabilities),
                "source_task_sha256": _sha256_text(task_text),
                "digest": capability_digest(effective_local_capabilities),
            },
        },
        "git": git,
            "herdr": {
            "executable": herdr,
            "codex_executable": codex,
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
            "grant_digest": expected_grant_digest,
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
    _record_performance_phase(performance, "launch_preparation", worker_started)
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
    parser.add_argument("--local-capability", action="append", default=[])
    parser.add_argument("--grant-turns", default=_NATIVE_GRANT_VALUE)
    parser.add_argument("--grant-wall-clock-seconds", default=_NATIVE_GRANT_VALUE)
    parser.add_argument("--grant-child-agents", choices=["allow", "deny"], default="deny")
    parser.add_argument("--task", required=True)
    parser.add_argument("--name")
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--assignment-id")
    parser.add_argument("--repository-identity")
    parser.add_argument("--plan-identity")
    parser.add_argument("--task-sha256")
    parser.add_argument("--grant-digest")
    parser.add_argument("--prior-attempt-known", choices=["true", "false"], default="false")
    parser.add_argument("--remaining-authorized-task-allowance", type=float)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _main_body(args: argparse.Namespace) -> int:
    invocation_started = time.monotonic()
    attempt_deadline = invocation_started + _DEEPAGENTS_RUN_TIMEOUT
    dispatch_id = uuid.uuid4().hex
    preparation_performance = _new_performance_evidence()
    attempt_context: dict[str, Any] = {
        "attempt_id": None,
        "agent_name": args.name or f"{args.profile}-main",
        "session": None,
        "pane": None,
        "started": False,
        "delivery": None,
        "execution": None,
        "observation": None,
        "task_result": None,
        "cleanup": None,
        "reconciliation_required": False,
        "task_sha256": None,
        "delivery_task_sha256": None,
        "grant_digest": None,
        "assignment_id": args.assignment_id,
        "repository_identity": args.repository_identity,
        "plan_identity": args.plan_identity,
        "prior_attempt_known": args.prior_attempt_known == "true",
    }

    def emit_failure(message: str, resolution: dict[str, Any] | None = None) -> int:
        started = attempt_context["started"] is True
        current_attempt_id = attempt_context.get("attempt_id")
        current_agent_name = attempt_context.get("agent_name")
        has_attempt = isinstance(current_attempt_id, str) and bool(current_attempt_id)
        delivery = attempt_context.get("delivery")
        execution = attempt_context.get("execution")
        observation = attempt_context.get("observation")
        task_result = attempt_context.get("task_result")
        cleanup = attempt_context.get("cleanup")
        if not isinstance(delivery, dict):
            delivery = {"state": "not_attempted", "certainty": "unknown"}
        if not isinstance(execution, dict):
            execution = (
                {"state": "unknown", "worker_exit_code": None}
                if started
                else {"state": "not_started", "worker_exit_code": None}
            )
        if not isinstance(observation, dict):
            observation = {"state": "unknown" if started else "not_attempted"}
        if not isinstance(task_result, dict):
            task_result = (
                {"state": "unverified", "accepted": None}
                if started
                else {"state": "not_attempted", "accepted": False}
            )
        if not isinstance(cleanup, dict):
            cleanup = {"state": "unknown" if started else "not_attempted"}
        phases = preparation_performance.get("phase_durations_ms", {})
        if isinstance(phases, dict):
            for phase in phases.values():
                if isinstance(phase, dict) and phase.get("status") == "not_attempted":
                    phase["status"] = "unavailable"
        performance = _finalize_performance(preparation_performance, invocation_started)
        legacy = {
            "failure_kind": message,
            "status": "blocked",
            "reconciliation_required": (
                bool(attempt_context.get("reconciliation_required"))
                if started
                else False
            ),
        }
        for key in ("assignment_id", "repository_identity", "plan_identity"):
            value = attempt_context.get(key)
            if isinstance(value, str):
                legacy[key] = value
        if isinstance(attempt_context.get("session"), str):
            legacy["session"] = attempt_context["session"]
        if isinstance(attempt_context.get("task_sha256"), str):
            legacy["task_sha256"] = attempt_context["task_sha256"]
        if isinstance(attempt_context.get("delivery_task_sha256"), str):
            legacy["delivery_task_sha256"] = attempt_context["delivery_task_sha256"]
        if isinstance(attempt_context.get("grant_digest"), str):
            legacy["grant_digest"] = attempt_context["grant_digest"]
        result = _build_assignment_result(
            dispatch_id=dispatch_id,
            attempt_id=(current_attempt_id if has_attempt else uuid.uuid4().hex),
            agent_name=(current_agent_name if isinstance(current_agent_name, str) else args.profile + "-main"),
            delivery=delivery,
            execution=execution,
            observation=observation,
            task_result=task_result,
            cleanup=cleanup,
            performance=performance,
            launcher_exit_code=2,
            legacy=legacy,
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
            local_capabilities=args.local_capability,
            grant_turns=args.grant_turns,
            grant_wall_clock_seconds=args.grant_wall_clock_seconds,
            grant_child_agents=args.grant_child_agents,
            task=args.task,
            name=args.name,
            codex_home=args.codex_home,
            assignment_id=args.assignment_id,
            repository_identity=args.repository_identity,
            plan_identity=args.plan_identity,
            task_sha256=args.task_sha256,
            grant_digest_value=args.grant_digest,
            remaining_authorized_task_allowance=args.remaining_authorized_task_allowance,
            attempt_deadline=attempt_deadline,
        )
        if args.executor == "deepagents" and time.monotonic() >= attempt_deadline:
            raise LaunchBlocked("DeepAgents whole-attempt deadline expired during setup.")
        attempt_id = uuid.uuid4().hex
        attempt_context.update(
            {
                "attempt_id": attempt_id,
                "agent_name": evidence.get("herdr", {}).get("agent_name", args.profile + "-main"),
            }
        )
        registry_evidence = evidence.setdefault("registry_launcher", {})
        observation_evidence = evidence.setdefault("observation", {})
        if not isinstance(registry_evidence, dict) or not isinstance(observation_evidence, dict):
            raise LaunchBlocked("Launcher evidence has invalid lifecycle sections.")
        performance_evidence = evidence.setdefault("performance", preparation_performance)
        if not isinstance(performance_evidence, dict):
            raise LaunchBlocked("Launcher evidence has invalid performance section.")
        dispatch_id = str(registry_evidence.setdefault("dispatch_id", dispatch_id))
        for key in ("assignment_id", "repository_identity", "plan_identity"):
            if registry_evidence.get(key) is not None:
                attempt_context[key] = registry_evidence[key]
        receipt_file: Path | None = None
        task_result_file: Path | None = None
        if args.executor == "deepagents" and not args.dry_run and "-n" in command:
            receipt_dir = Path(tempfile.mkdtemp(prefix=f"herdr-result-{attempt_id}-"))
            receipt_file = receipt_dir / "result.json"
            task_result_file = receipt_dir / "task-result.json"
            command = command.copy()
            command[command.index("-n"):command.index("-n")] = [
                "--result-file",
                _powershell_literal(str(receipt_file)),
                "--attempt-id",
                _powershell_literal(attempt_id),
            ]
            if args.assignment_id is not None:
                command[command.index("-n"):command.index("-n")] = [
                    "--assignment-id",
                    _powershell_literal(args.assignment_id),
                    "--repository-identity",
                    _powershell_literal(str(args.repository_identity)),
                    "--task-sha256",
                    _powershell_literal(str(args.task_sha256)),
                    "--grant-digest",
                    _powershell_literal(str(args.grant_digest)),
                    "--prior-attempt-known",
                    _powershell_literal(args.prior_attempt_known),
                ]
            registry_evidence["result_file"] = str(receipt_file)
            registry_evidence["task_result_file"] = str(task_result_file)

        def record_phase(name: str, started: float, *, attempt_id: str | None = None) -> None:
            if args.executor == "deepagents" and name == "delivery":
                return
            _record_performance_phase(
                performance_evidence,
                name,
                started,
                attempt_id=attempt_id,
            )

        def emit_assignment(payload: dict[str, Any]) -> dict[str, Any]:
            assignment = payload.get("assignment", payload)
            if not isinstance(assignment, dict):
                raise LaunchBlocked("Assignment evidence must be an object.")
            local_capabilities = registry_evidence.get("local_capabilities")
            if isinstance(local_capabilities, dict):
                assignment["local_capabilities"] = dict(local_capabilities)
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
            completion = assignment.get("completion")
            receipt = assignment.get("lifecycle_receipt")
            if not isinstance(receipt, dict) and isinstance(completion, dict):
                receipt = completion.get("lifecycle_receipt")
            if not isinstance(receipt, dict):
                receipt = _read_deepagents_receipt(
                    receipt_file,
                    str(assignment.get("attempt_id", attempt_id)),
                )
            task_result_evidence = _read_deepagents_task_result(
                task_result_file,
                assignment_id=str(assignment.get("assignment_id", args.assignment_id))
                if assignment.get("assignment_id", args.assignment_id) is not None
                else None,
                attempt_id=str(assignment.get("attempt_id", attempt_id)),
                task_sha256=str(assignment.get("task_sha256", args.task_sha256))
                if assignment.get("task_sha256", args.task_sha256) is not None
                else None,
                grant_digest_value=str(assignment.get("grant_digest", args.grant_digest))
                if assignment.get("grant_digest", args.grant_digest) is not None
                else None,
            )
            receipt_capabilities = receipt.get("capabilities")
            capability_state = receipt.get("capability_state", "unavailable")
            assignment["capability_state"] = capability_state
            if capability_state == "confirmed" and isinstance(receipt_capabilities, dict) and all(
                name in receipt_capabilities
                for name in ("requested", "passed_to_worker", "validated_available", "digest")
            ):
                projected_capabilities = dict(local_capabilities or {})
                projected_capabilities.update(
                    {
                        "requested": receipt_capabilities["requested"],
                        "effective": receipt_capabilities["passed_to_worker"],
                        "verification_commands": receipt_capabilities["passed_to_worker"],
                        "digest": receipt_capabilities["digest"],
                    }
                )
                assignment["local_capabilities"] = projected_capabilities
                assignment["capabilities"] = dict(receipt_capabilities)
            else:
                assignment["capability_detail"] = receipt.get(
                    "capability_detail", "worker capability evidence unavailable"
                )
            if args.executor == "deepagents":
                assignment["lifecycle_receipt"] = receipt
                classified = _classify_deepagents_outcome(
                    delivery=delivery,
                    observation=observation,
                    receipt=receipt,
                    fallback_failure_kind=assignment.get("failure_kind"),
                    task_result_evidence=task_result_evidence,
                )
                delivery = classified["delivery"]
                execution = classified["execution"]
                observation = classified["observation"]
                task_result = classified["task_result"]
                cleanup = classified["cleanup"]
                assignment.update(
                    {
                        "status": classified["status"],
                        "failure_kind": classified["failure_kind"],
                        "reconciliation_required": classified["reconciliation_required"],
                        "exit_code": classified["launcher_exit_code"],
                        "prompt_accepted": delivery.get("prompt_accepted"),
                        "task_accepted": task_result.get("accepted"),
                    }
                )
                if receipt.get("state") == "confirmed" and not receipt.get("recovery_required"):
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
            attempt_context.update(
                {
                    "attempt_id": result["assignment"]["attempt_id"],
                    "agent_name": result["assignment"]["agent_name"],
                    "delivery": delivery,
                    "execution": execution,
                    "observation": observation,
                    "task_result": task_result,
                    "cleanup": cleanup,
                    "reconciliation_required": result["assignment"].get(
                        "reconciliation_required", False
                    ),
                }
            )
            return result

        registry_evidence["attempt_id"] = attempt_id
        observation_evidence["attempt_id"] = attempt_id
        if isinstance(performance_evidence, dict):
            performance_evidence.pop("_last_monotonic", None)
            performance_evidence.pop("_phase_intervals", None)
        print(json.dumps(evidence, sort_keys=True), flush=True)
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
        attempt_context.update(
            {
                "session": resolved_session,
                "pane": resolved_pane,
                "task_sha256": assignment_task_sha256,
                "delivery_task_sha256": delivery_task_sha256,
                "grant_digest": grant_digest,
            }
        )
        if args.executor == "codex":
            codex_evidence = evidence.get("codex")
            if not isinstance(codex_evidence, dict) or not codex_evidence.get("codex_home"):
                raise LaunchBlocked("Launcher evidence missing codex_home.")
            environment = _codex_environment(Path(str(codex_evidence["codex_home"])))
        else:
            environment = _herdr_environment()
        for attempt in range(2):
            attempt_started = time.monotonic()
            pane_run_duration_ms: float | None = None
            pane_run_started = time.monotonic()
            try:
                try:
                        result = _run_with_pane_ownership(
                            args.cwd,
                            resolved_session,
                            resolved_pane,
                            str(evidence["herdr"].get("executable", "")),
                            args.executor,
                            command,
                            environment,
                        (
                            max(0.01, attempt_deadline - time.monotonic())
                            if args.executor == "deepagents"
                            else _CODEX_START_TIMEOUT
                        ),
                        verify=bool(evidence["herdr"].get("pane_cwd")),
                    )
                finally:
                    if args.executor == "deepagents":
                        pane_run_duration_ms = max(0.0, time.monotonic() - pane_run_started) * 1000
            except CommandTransportTimeout:
                record_phase("delivery", attempt_started, attempt_id=attempt_id)
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
            attempt_context.update(
                {
                    "started": result.returncode == 0,
                    "attempt_id": attempt_id,
                    "agent_name": evidence["herdr"]["agent_name"],
                    "session": resolved_session,
                    "pane": resolved_pane,
                    "reconciliation_required": result.returncode == 0,
                }
            )
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
                expected_codex_executable=str(evidence["herdr"].get("codex_executable") or "codex"),
                expected_cwd=Path(str(evidence["herdr"].get("pane_cwd", args.cwd))),
            )
            record_phase("retirement", retirement_started, attempt_id=attempt_id)
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
            attempt_context.update(
                {
                    "attempt_id": attempt_id,
                    "agent_name": agent_name,
                    "started": False,
                    "delivery": None,
                    "execution": None,
                    "observation": None,
                    "task_result": None,
                    "cleanup": None,
                    "reconciliation_required": False,
                }
            )
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
            record_phase("delivery", attempt_started, attempt_id=attempt_id)
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
            if command[3:5] == ["agent", "start"]:
                _confirm_codex_start(
                    herdr,
                    resolved_session,
                    resolved_pane,
                    agent_name,
                    env=environment,
                    before_process_ids=set(evidence["herdr"].get("start_process_ids", [])),
                    expected_codex_executable=str(evidence["herdr"].get("codex_executable") or "codex"),
                    expected_cwd=Path(str(evidence["herdr"].get("pane_cwd", args.cwd))),
                )
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
                record_phase("delivery", attempt_started, attempt_id=attempt_id)
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
                record_phase("delivery", attempt_started, attempt_id=attempt_id)
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
                record_phase("delivery", attempt_started, attempt_id=attempt_id)
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
            record_phase("delivery", attempt_started, attempt_id=attempt_id)
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
        runtime_grant = registry_launcher.get("runtime_grant")
        wall_clock_grant = (
            runtime_grant.get("wall_clock_seconds")
            if isinstance(runtime_grant, dict)
            else None
        )
        requested_wait = (
            wall_clock_grant.get("requested")
            if isinstance(wall_clock_grant, dict)
            else None
        )
        completion = _deepagents_completion_evidence(
            str(evidence["herdr"]["executable"]),
            resolved_session,
            resolved_pane,
            env=environment,
            expected_marker=completion_marker,
            receipt_file=receipt_file,
            attempt_id=attempt_id,
            completion_wait_seconds=(
                float(requested_wait)
                if isinstance(requested_wait, int)
                else max(
                    0.0,
                    attempt_deadline - time.monotonic() - _DEEPAGENTS_RECEIPT_GRACE_SECONDS,
                )
            ),
            attempt_deadline=attempt_deadline,
        )
        record_phase("observation", observation_started, attempt_id=attempt_id)
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
        record_phase("delivery", attempt_started, attempt_id=attempt_id)
        assignment_result = emit_assignment({
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
                    "state": "reported_completed" if task_verified else "unknown",
                    "accepted": None,
                    **(
                        {"source": "herdr_pane", "authoritative": False}
                        if task_verified
                        else {}
                    ),
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
                "task_accepted": None,
                "task_sha256": assignment_task_sha256,
            }
        })
        print(json.dumps(assignment_result, sort_keys=True))
        return int(assignment_result["assignment"]["launcher_exit_code"])
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
