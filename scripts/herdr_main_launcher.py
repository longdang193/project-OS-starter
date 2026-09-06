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
from typing import Any

try:
    from agent_profile_registry import AgentProfile, load_agent_profiles
except ModuleNotFoundError:
    from scripts.agent_profile_registry import AgentProfile, load_agent_profiles


class LaunchBlocked(RuntimeError):
    """Raised when a required runtime binding is unavailable or mismatched."""


_EXECUTORS = {"codex", "deepagents"}
_MAX_TASK_LENGTH = 4096
_CODEX_PROMPT_TIMEOUT_MS = "30000"
_HERDR_COMMAND_TIMEOUT = 30.0
_DEEPAGENTS_RUN_TIMEOUT = 1800.0
_CODEX_ASSIGNMENT_TIMEOUT = (float(_CODEX_PROMPT_TIMEOUT_MS) / 1000) + 5.0
_NATIVE_GRANT_VALUE = "native"


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
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise LaunchBlocked(
            f"Command timed out after {timeout:g}s: {' '.join(command)}"
        ) from exc


def _run_checked(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> str:
    result = _run(command, cwd=cwd, env=env)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise LaunchBlocked(f"Command failed ({result.returncode}): {' '.join(command)}: {detail}")
    return result.stdout.strip()


def _json_command(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    output = _run_checked(command, env=env)
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
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    panes = _result(_json_command([herdr, "--session", session, "pane", "list"], env=env), "panes")
    if not isinstance(panes, list):
        raise LaunchBlocked("Herdr pane list is not an array.")
    selected = next((item for item in panes if item.get("pane_id") == pane), None)
    if not isinstance(selected, dict):
        raise LaunchBlocked(f"Pane is unavailable in session `{session}`: {pane}")
    pane_cwd = Path(str(selected.get("cwd", ""))).resolve()
    if pane_cwd != cwd.resolve():
        raise LaunchBlocked(f"Pane cwd mismatch: expected {cwd}, got {pane_cwd}")
    if selected.get("agent") or selected.get("agent_status") not in (None, "unknown"):
        raise LaunchBlocked(f"Pane already has agent state: {pane}")

    process_payload = _json_command(
        [herdr, "--session", session, "pane", "process-info", "--pane", pane],
        env=env,
    )
    process_info = _result(process_payload, "process_info")
    foreground = process_info.get("foreground_processes", [])
    if not isinstance(foreground, list):
        raise LaunchBlocked("Herdr pane process information is invalid.")
    shell_names = {"powershell.exe", "pwsh.exe", "cmd.exe", "bash", "sh", "zsh", "fish"}
    conflicting = [
        process.get("name", "unknown")
        for process in foreground
        if str(process.get("name", "")).lower() not in shell_names
    ]
    if conflicting:
        raise LaunchBlocked(f"Pane has conflicting foreground process: {', '.join(conflicting)}")
    return {"pane": selected, "process_info": process_info}


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
        "--wait",
        "--timeout",
        _CODEX_PROMPT_TIMEOUT_MS,
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


def _normalize_lane_grant(
    *,
    executor: str,
    grant_turns: str | int | None,
    grant_wall_clock_seconds: str | int | None,
    mcp_select: list[str] | None,
) -> dict[str, Any]:
    turns = _parse_grant_value(grant_turns, "Grant turns")
    wall_clock_seconds = _parse_grant_value(
        grant_wall_clock_seconds,
        "Grant wall-clock seconds",
    )
    if executor == "codex" and turns != _NATIVE_GRANT_VALUE:
        raise LaunchBlocked("Codex strict turn budget is unsupported; use `native`.")
    if executor == "codex" and wall_clock_seconds != _NATIVE_GRANT_VALUE:
        raise LaunchBlocked("Codex strict wall-clock budget is unsupported; use `native`.")
    if (
        executor == "deepagents"
        and wall_clock_seconds != _NATIVE_GRANT_VALUE
        and wall_clock_seconds > int(_DEEPAGENTS_RUN_TIMEOUT)
    ):
        raise LaunchBlocked(
            "DeepAgents wall-clock budget cannot exceed the 1800-second Herdr watchdog."
        )
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
                "runtime"
                if wall_clock_seconds != _NATIVE_GRANT_VALUE
                else "native"
            ),
        },
        "outer_watchdog_seconds": (
            int(_DEEPAGENTS_RUN_TIMEOUT) if executor == "deepagents" else None
        ),
        "mcp_select": list(mcp_select or []),
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
    task: str | None = None,
    name: str | None = None,
    codex_home: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    if executor not in _EXECUTORS:
        raise LaunchBlocked(f"Unsupported executor: {executor}")
    task_text = _validate_task(task)
    lane_grant = _normalize_lane_grant(
        executor=executor,
        grant_turns=grant_turns,
        grant_wall_clock_seconds=grant_wall_clock_seconds,
        mcp_select=mcp_select,
    )
    grant_digest = _sha256_text(
        json.dumps(
            {
                "executor": executor,
                "turns": lane_grant["turns"]["requested"],
                "wall_clock_seconds": lane_grant["wall_clock_seconds"]["requested"],
                "mcp_select": lane_grant["mcp_select"],
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
    pane_state = _herdr_pane(cwd, session, pane, herdr, env=environment)
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
            *(["--max-turns", str(lane_grant["turns"]["requested"])]
              if lane_grant["turns"]["requested"] != _NATIVE_GRANT_VALUE
              else []),
            *(["--timeout", str(lane_grant["wall_clock_seconds"]["requested"])]
              if lane_grant["wall_clock_seconds"]["requested"] != _NATIVE_GRANT_VALUE
              else []),
            *sum(
                (["--mcp-select", _powershell_literal(value)] for value in (mcp_select or [])),
                [],
            ),
            *([] if direct_mcp else ["--no-mcp"]),
            "-n",
            _powershell_literal(task.strip()),
        ]
        command = [herdr, "--session", session, "pane", "run", pane, *runtime_arguments]
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
            "lane_grant": lane_grant,
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
        "observation": {
            "executor": executor,
            "session": session,
            "pane": pane,
            "agent_name": agent_name,
            "task_sha256": _sha256_text(task_text),
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
                _codex_assignment_command(herdr, session, agent_name, task_text)
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
    parser.add_argument("--session", required=True)
    parser.add_argument("--pane", required=True)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--expected-base", required=True)
    parser.add_argument("--executor", choices=sorted(_EXECUTORS), default="codex")
    parser.add_argument("--mcp-select", action="append", default=[])
    parser.add_argument("--grant-turns", default=_NATIVE_GRANT_VALUE)
    parser.add_argument("--grant-wall-clock-seconds", default=_NATIVE_GRANT_VALUE)
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
            task=args.task,
            name=args.name,
            codex_home=args.codex_home,
        )
        print(json.dumps(evidence, sort_keys=True))
        if args.dry_run:
            return 0
        if args.executor == "codex":
            codex_evidence = evidence.get("codex")
            if not isinstance(codex_evidence, dict) or not codex_evidence.get("codex_home"):
                raise LaunchBlocked("Launcher evidence missing codex_home.")
            environment = _codex_environment(Path(str(codex_evidence["codex_home"])))
        else:
            environment = os.environ.copy()
        result = _run(
            command,
            env=environment,
            timeout=(
                _DEEPAGENTS_RUN_TIMEOUT
                if args.executor == "deepagents"
                else _HERDR_COMMAND_TIMEOUT
            ),
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        if result.returncode:
            print(json.dumps({
                "assignment": {
                    "agent_name": evidence["herdr"]["agent_name"],
                    "exit_code": result.returncode,
                    "phase": "start",
                    "session": args.session,
                    "status": "failed",
                    "task_sha256": evidence["registry_launcher"]["assignment_task_sha256"],
                }
            }, sort_keys=True))
            return result.returncode
        if args.executor == "codex":
            herdr = str(evidence["herdr"]["executable"])
            agent_name = str(evidence["herdr"]["agent_name"])
            assignment = _codex_assignment_command(
                herdr,
                args.session,
                agent_name,
                args.task,
            )
            assignment_result = _run(
                assignment,
                env=environment,
                timeout=_CODEX_ASSIGNMENT_TIMEOUT,
            )
            if assignment_result.stdout:
                print(assignment_result.stdout, end="")
            if assignment_result.stderr:
                print(assignment_result.stderr, file=sys.stderr, end="")
            print(json.dumps({
                "assignment": {
                    "agent_name": agent_name,
                    "exit_code": assignment_result.returncode,
                    "phase": "prompt",
                    "prompt_accepted": assignment_result.returncode == 0,
                    "session": args.session,
                    "status": "delivered" if assignment_result.returncode == 0 else "failed",
                    "task_sha256": evidence["registry_launcher"]["assignment_task_sha256"],
                    "wait": "settled" if assignment_result.returncode == 0 else None,
                }
            }, sort_keys=True))
            return assignment_result.returncode
        print(json.dumps({
            "assignment": {
                "agent_name": evidence["herdr"]["agent_name"],
                "exit_code": 0,
                "phase": "pane_run",
                "session": args.session,
                "status": "delivered",
                "task_accepted": True,
                "task_sha256": evidence["registry_launcher"]["assignment_task_sha256"],
            }
        }, sort_keys=True))
        return 0
    except LaunchBlocked as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
