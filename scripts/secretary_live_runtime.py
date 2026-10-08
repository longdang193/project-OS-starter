"""Run one bounded, supervised Secretary attempt through Herdr and Codex."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
from typing import Any, Mapping

try:
    from project_os_runtime.secretary_receipts import (
        build_live_receipt,
        validate_live_receipt,
    )
except ModuleNotFoundError:
    from scripts.project_os_runtime.secretary_receipts import (
        build_live_receipt,
        validate_live_receipt,
    )


SECRETARY_PROVIDER = "9router"
_SAFE_ASSIGNMENT_KEYS = {
    "status",
    "launcher_exit_code",
    "attempt_id",
    "agent_name",
    "failure_kind",
    "reconciliation_required",
}


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


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
        if any(key in payload for key in ("herdr", "codex", "runtime", "assignment", "secretary_runtime")):
            for key in ("herdr", "codex", "runtime", "assignment", "secretary_runtime"):
                value = payload.get(key)
                if isinstance(value, Mapping):
                    selected[key] = dict(value)
    return selected


def sanitize_launcher_result(
    request: SecretaryLaunchRequest,
    *,
    returncode: int,
    payload: Mapping[str, Any] | None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> dict[str, Any]:
    assignment = payload.get("assignment") if isinstance(payload, Mapping) else None
    safe_assignment = {
        key: assignment[key]
        for key in _SAFE_ASSIGNMENT_KEYS
        if isinstance(assignment, Mapping) and key in assignment
    }
    codex = payload.get("codex") if isinstance(payload, Mapping) else None
    herdr = payload.get("herdr") if isinstance(payload, Mapping) else None
    structured_binding = payload.get("secretary_runtime") if isinstance(payload, Mapping) else None
    if isinstance(structured_binding, Mapping):
        structured_binding = {
            field: structured_binding.get(field)
            for field in ("task_id", "plan_revision", "attempt_id", "run_id")
        }
    else:
        structured_binding = None
    return {
        "schema_version": "secretary-live-runtime-v1",
        "evidence_provenance": "live-attributed" if returncode == 0 else "capability-probe",
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
            "agent_name": herdr.get("agent_name") if isinstance(herdr, Mapping) else None,
            "session": herdr.get("session") if isinstance(herdr, Mapping) else None,
            "pane": herdr.get("pane") if isinstance(herdr, Mapping) else None,
            "codex_version": codex.get("version") if isinstance(codex, Mapping) else None,
            "secretary_runtime": structured_binding,
        },
        "timestamps": {
            "run_started": started_at,
            "run_finished": finished_at,
        },
        "metrics": {
            "cos_turns": "unknown",
            "secretary_turns": 1 if returncode == 0 else 0,
            "human_interventions": "unknown",
            "publication_success": "unknown",
            "settlement_proven": "unknown",
            "acceptance_decision": "unknown",
            "token_usage": "unknown",
            "cost": "unknown",
        },
        "disposition": "READY" if returncode == 0 else "BLOCKED_CAPABILITY",
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
        "provider": request.provider,
        "model": _configured_model(request),
        "controller_id": "cos-supervised",
        "session_id": runtime_identity.get("session") or "unknown",
    }
    timestamps = result.get("timestamps")
    if not isinstance(timestamps, Mapping):
        timestamps = {}
    return validate_live_receipt(
        build_live_receipt(
            binding=binding,
            runtime=runtime,
            timestamps={
                "run_started": timestamps.get("run_started"),
                "cos_entry": None,
                "secretary_entry": timestamps.get("run_started"),
                "worker_entry": None,
                "publication": None,
                "settlement": None,
                "acceptance": None,
                "secretary_exit": timestamps.get("run_finished"),
                "cos_exit": None,
                "run_finished": timestamps.get("run_finished"),
            },
            metrics={
                "cos_turns": "unknown",
                "secretary_turns": result.get("metrics", {}).get("secretary_turns", "unknown"),
                "human_interventions": "unknown",
                "publication_success": "unknown",
                "settlement_proven": "unknown",
                "acceptance_decision": "unknown",
                "token_usage": "unknown",
                "cost": "unknown",
            },
            sources={
                "launch": {"producer": "herdr_main_launcher", **binding, **runtime},
                "secretary": {"producer": "secretary_live_runtime", **binding, **runtime},
            },
        )
    )


def run_smoke(request: SecretaryLaunchRequest, *, output: Path) -> dict[str, Any]:
    _configured_provider(request.codex_home)
    _configured_model(request)
    started = datetime.now(timezone.utc).isoformat()
    environment = dict(os.environ)
    environment["CODEX_HOME"] = str(request.codex_home.resolve())
    completed = subprocess.run(
        build_launcher_command(request),
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
        started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )
    result["receipt"] = _smoke_receipt(request, result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    smoke = subparsers.add_parser("smoke")
    smoke.add_argument("--output", type=Path, required=True)
    smoke.add_argument("--task-id", required=True)
    smoke.add_argument("--plan-revision", required=True)
    smoke.add_argument("--attempt-id", required=True)
    smoke.add_argument("--run-id", required=True)
    smoke.add_argument("--repository-identity", required=True)
    smoke.add_argument("--plan-identity", required=True)
    smoke.add_argument("--git-revision", required=True)
    smoke.add_argument("--cwd", type=Path, default=Path.cwd())
    smoke.add_argument("--expected-base", required=True)
    smoke.add_argument("--task", required=True)
    smoke.add_argument("--codex-home", type=Path)
    smoke.add_argument("--profile", default="normal")
    smoke.add_argument("--session", default="auto")
    smoke.add_argument("--pane", default="auto")
    args = parser.parse_args(argv)
    if args.command == "smoke":
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
            result = run_smoke(request, output=args.output)
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
