"""Launch one registry-bound top-level lane through Herdr."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

try:
    from agent_profile_registry import AgentProfile, load_agent_profiles
except ModuleNotFoundError:
    from scripts.agent_profile_registry import AgentProfile, load_agent_profiles


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
_CODEX_PROMPT_TIMEOUT_MS = "30000"
_HERDR_COMMAND_TIMEOUT = 30.0
_DEEPAGENTS_RUN_TIMEOUT = 1800.0
_CODEX_ASSIGNMENT_TIMEOUT = (float(_CODEX_PROMPT_TIMEOUT_MS) / 1000) + 5.0
_CODEX_WATCHDOG_GRACE_SECONDS = 5.0
_TARGET_DISCOVERY_TIMEOUT = 5.0
_HERDR_DEFAULT_SESSION = "default"
_WATCHDOG_TIMEOUT_EXIT_CODE = 124
_NATIVE_GRANT_VALUE = "native"
_CHILD_AGENT_GRANT_VALUES = {"allow", "deny"}
_SHELL_PROCESS_NAMES = {"powershell.exe", "pwsh.exe", "cmd.exe", "bash", "sh", "zsh", "fish"}
_DEEPAGENTS_SHELL_PROCESS_NAMES = {"powershell.exe", "pwsh.exe"}


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


def _codex_arguments(profile: AgentProfile, cwd: Path) -> list[str]:
    return [
        "-C",
        str(cwd),
        "-c",
        f"model_provider={json.dumps(profile.model_provider)}",
        "-c",
        f"model={json.dumps(profile.model)}",
        "-c",
        f"developer_instructions={json.dumps(profile.developer_instructions)}",
    ]


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


def _codex_assignment_command(
    herdr: str,
    session: str,
    agent_name: str,
    task: str,
    *,
    timeout_ms: int | None = None,
) -> list[str]:
    return [
        herdr,
        "--session",
        session,
        "agent",
        "prompt",
        agent_name,
        task,
        "--wait",
        "--timeout",
        str(timeout_ms or _CODEX_PROMPT_TIMEOUT_MS),
    ]


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
                "outer-watchdog"
                if executor == "codex" and wall_clock_seconds != _NATIVE_GRANT_VALUE
                else "runtime"
                if wall_clock_seconds != _NATIVE_GRANT_VALUE
                else "native"
            ),
        },
        "outer_watchdog_seconds": (
            int(wall_clock_seconds)
            if executor == "codex" and wall_clock_seconds != _NATIVE_GRANT_VALUE
            else int(_DEEPAGENTS_RUN_TIMEOUT)
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
    if executor == "deepagents" and not selected.deepagents_compatible:
        raise LaunchBlocked(
            f"Profile is not compatible with DeepAgents: {selected.name}"
        )
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
    session, pane, target_resolution = _resolve_target_selector(
        cwd,
        session,
        pane,
        herdr,
        executor=executor,
        env=environment,
    )
    pane_state = _herdr_pane(cwd, session, pane, herdr, executor=executor, env=environment)
    agent_name = name or f"{selected.name}-main"
    if executor == "codex":
        runtime_arguments = _codex_arguments(selected, cwd)
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
            "--quiet",
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
    codex_watchdog = runtime_grant["wall_clock_seconds"]["requested"]
    codex_prompt_timeout_ms = (
        codex_watchdog * 1000
        if executor == "codex" and codex_watchdog != _NATIVE_GRANT_VALUE
        else None
    )
    evidence = {
        "registry_launcher": {
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
                    timeout_ms=codex_prompt_timeout_ms,
                )
            ) if executor == "codex" else None,
        },
    }
    if runtime is not None:
        evidence["codex"] = {
            "executable": codex,
            "version": _version(str(codex), env=environment),
            **runtime,
        }
    else:
        evidence["deepagents"] = {
            "executable": dcode,
            "mcp_mode": "direct" if direct_mcp else "disabled",
            "mcp_selection": list(mcp_select or []),
        }
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
            environment = _herdr_environment()
        try:
            result = _run(
                command,
                env=environment,
                timeout=(
                    _DEEPAGENTS_RUN_TIMEOUT
                    if args.executor == "deepagents"
                    else _HERDR_COMMAND_TIMEOUT
                ),
            )
        except CommandTransportTimeout:
            print(json.dumps({
                "assignment": {
                    "agent_name": evidence["herdr"]["agent_name"],
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
            }, sort_keys=True))
            return 2
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        if result.returncode:
            print(json.dumps({
                "assignment": {
                    "agent_name": evidence["herdr"]["agent_name"],
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
            }, sort_keys=True))
            return result.returncode
        if args.executor == "codex":
            herdr = str(evidence["herdr"]["executable"])
            agent_name = str(evidence["herdr"]["agent_name"])
            watchdog_seconds = _codex_watchdog_seconds(evidence)
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
                timeout_ms=(watchdog_seconds * 1000 if watchdog_seconds is not None else None),
            )
            assignment_started = time.monotonic()
            watchdog_expired = False
            transport_timeout: CommandTransportTimeout | None = None
            assignment_result: subprocess.CompletedProcess[str] | None = None
            try:
                assignment_result = _run(
                    assignment,
                    env=environment,
                    timeout=(
                        watchdog_seconds + _CODEX_WATCHDOG_GRACE_SECONDS
                        if watchdog_seconds is not None
                        else _CODEX_ASSIGNMENT_TIMEOUT
                    ),
                )
            except CommandTransportTimeout as exc:
                transport_timeout = exc
            elapsed_seconds = time.monotonic() - assignment_started
            if (
                assignment_result is not None
                and watchdog_seconds is not None
                and assignment_result.returncode != 0
                and elapsed_seconds >= watchdog_seconds
            ):
                watchdog_expired = True
            if transport_timeout is not None:
                if watchdog_seconds is not None and elapsed_seconds >= watchdog_seconds:
                    watchdog_expired = True
                else:
                    launcher = evidence["registry_launcher"]
                    print(json.dumps({
                        "assignment": {
                    "agent_name": agent_name,
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
                    }, sort_keys=True))
                    return 2
            if watchdog_expired:
                cleanup = _terminate_codex_lane(
                    herdr,
                    resolved_session,
                    resolved_pane,
                    env=environment,
                )
                cleanup_verified = bool(cleanup.get("verified"))
                status = "TIMEOUT" if cleanup_verified else "BLOCKED"
                print(json.dumps({
                    "assignment": {
                        "agent_name": agent_name,
                        "delivery_state": "watchdog_expired",
                        "delivery_certainty": "unknown",
                        "delivery_task_sha256": delivery_task_sha256,
                        "exit_code": (
                            _WATCHDOG_TIMEOUT_EXIT_CODE
                            if cleanup_verified
                            else 2
                        ),
                        "phase": "prompt",
                        "prompt_accepted": None,
                        "session": resolved_session,
                        "status": status,
                        "task_sha256": assignment_task_sha256,
                        "failure_kind": "watchdog_expired",
                        "grant_digest": grant_digest,
                        "reconciliation_required": False,
                        "watchdog": {
                            "requested_seconds": watchdog_seconds,
                            "enforcement": "outer-watchdog",
                            "elapsed_seconds": round(elapsed_seconds, 3),
                            "termination": cleanup,
                        },
                    }
                }, sort_keys=True))
                return _WATCHDOG_TIMEOUT_EXIT_CODE if cleanup_verified else 2
            if assignment_result is None:
                raise LaunchBlocked("Codex assignment produced no result.")
            if assignment_result.stdout:
                print(assignment_result.stdout, end="")
            if assignment_result.stderr:
                print(assignment_result.stderr, file=sys.stderr, end="")
            print(json.dumps({
                "assignment": {
                    "agent_name": agent_name,
                    "delivery_state": (
                        "delivered" if assignment_result.returncode == 0 else "delivery_failed"
                    ),
                    "delivery_certainty": (
                        "confirmed" if assignment_result.returncode == 0 else "not_delivered"
                    ),
                    "delivery_task_sha256": delivery_task_sha256,
                    "exit_code": assignment_result.returncode,
                    "failure_kind": None if assignment_result.returncode == 0 else "command_exit",
                    "grant_digest": grant_digest,
                    "phase": "prompt",
                    "prompt_accepted": assignment_result.returncode == 0,
                    "session": resolved_session,
                    "status": "delivered" if assignment_result.returncode == 0 else "failed",
                    "task_sha256": assignment_task_sha256,
                    "reconciliation_required": assignment_result.returncode != 0,
                    "wait": "settled" if assignment_result.returncode == 0 else None,
                }
            }, sort_keys=True))
            return assignment_result.returncode
        if result.returncode:
            print(json.dumps({
                "assignment": {
                    "agent_name": evidence["herdr"]["agent_name"],
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
            }, sort_keys=True))
            return result.returncode
        print(json.dumps({
            "assignment": {
                "agent_name": evidence["herdr"]["agent_name"],
                "delivery_state": "delivered",
                "delivery_certainty": "confirmed",
                "delivery_task_sha256": delivery_task_sha256,
                "exit_code": 0,
                "grant_digest": grant_digest,
                "phase": "pane_run",
                "session": resolved_session,
                "status": "delivered",
                "task_accepted": True,
                "task_sha256": assignment_task_sha256,
                "reconciliation_required": False,
            }
        }, sort_keys=True))
        return 0
    except TargetResolutionBlocked as exc:
        print(json.dumps({"target_resolution": exc.resolution}, sort_keys=True))
        print(f"TARGET_RESOLUTION: {exc}", file=sys.stderr)
        return 2
    except LaunchBlocked as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
