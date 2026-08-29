"""Launch one registry-bound top-level Codex agent through Herdr."""

from __future__ import annotations

import argparse
import hashlib
import json
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


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def _run_checked(command: list[str], *, cwd: Path | None = None) -> str:
    result = _run(command, cwd=cwd)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise LaunchBlocked(f"Command failed ({result.returncode}): {' '.join(command)}: {detail}")
    return result.stdout.strip()


def _json_command(command: list[str]) -> dict[str, Any]:
    output = _run_checked(command)
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


def _version(path: str) -> str:
    output = _run_checked([path, "--version"])
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


def _herdr_pane(cwd: Path, session: str, pane: str, herdr: str) -> dict[str, Any]:
    panes = _result(_json_command([herdr, "--session", session, "pane", "list"]), "panes")
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
        [herdr, "--session", session, "pane", "process-info", "--pane", pane]
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
        redacted.append(value)
        index += 1
    return redacted


def resolve_launch(
    *,
    profile_name: str,
    session: str,
    pane: str,
    cwd: Path,
    expected_base: str,
    name: str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    repo_root = Path(__file__).resolve().parents[1]
    selected = _profile(repo_root / "agents", profile_name)
    herdr = _executable("herdr")
    codex = _executable("codex")
    git = _git_identity(cwd, expected_base)
    pane_state = _herdr_pane(cwd, session, pane, herdr)
    agent_name = name or f"{selected.name}-main"
    codex_arguments = _codex_arguments(selected, cwd)
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
        *codex_arguments,
    ]
    evidence = {
        "registry_launcher": {
            "profile": selected.name,
            "profile_source": str(selected.source),
            "executor": "codex",
            "model_provider": selected.model_provider,
            "model": selected.model,
            "developer_instructions_sha256": _sha256_text(selected.developer_instructions),
            "projected_config_keys": [
                "model_provider",
                "model",
                "developer_instructions",
            ],
            "redacted_codex_argv": _redacted_arguments(codex_arguments),
        },
        "git": git,
        "herdr": {
            "executable": herdr,
            "version": _version(herdr),
            "session": session,
            "pane": pane,
            "agent_name": agent_name,
            "agent_kind": "codex",
            "pane_cwd": str(Path(str(pane_state["pane"].get("cwd"))).resolve()),
        },
        "codex": {
            "executable": codex,
            "version": _version(codex),
            "argv_shape": _redacted_arguments(codex_arguments),
        },
    }
    return command, evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--pane", required=True)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--expected-base", required=True)
    parser.add_argument("--name")
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
            name=args.name,
        )
        print(json.dumps(evidence, sort_keys=True))
        if args.dry_run:
            return 0
        result = _run(command)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return result.returncode
    except LaunchBlocked as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
