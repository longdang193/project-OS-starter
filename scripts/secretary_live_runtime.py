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
    return not isinstance(assignment, Mapping) or assignment.get("attempt_id") in (None, request.attempt_id)


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
    if not isinstance(herdr, Mapping):
        return False
    session = herdr.get("session")
    return not isinstance(session, str) or not session.strip() or runtime.get("session_id") == session


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
        elif field in number_fields and isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
            result[field] = value
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
        snapshot["sources"] = {
            name: {
                key: source[key]
                for key in _SOURCE_SAFE_FIELDS
                if isinstance(source, Mapping) and key in source
            }
            for name, source in sources.items()
            if name in _SOURCE_KEYS and isinstance(source, Mapping)
        }
    return snapshot


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
    safe_assignment = {
        key: assignment[key]
        for key in _SAFE_ASSIGNMENT_KEYS
        if isinstance(assignment, Mapping) and key in assignment
    }
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
    }
    if configured_model is not None:
        expected_values["model"] = configured_model
    if isinstance(herdr, Mapping) and isinstance(herdr.get("session"), str) and herdr["session"].strip():
        expected_values["session_id"] = herdr["session"]
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
    )
    observed_metrics = structured_binding.get("metrics") if isinstance(structured_binding, Mapping) else None
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
            "agent_name": herdr.get("agent_name") if isinstance(herdr, Mapping) else None,
            "session": herdr.get("session") if isinstance(herdr, Mapping) else None,
            "pane": herdr.get("pane") if isinstance(herdr, Mapping) else None,
            "codex_version": codex.get("version") if isinstance(codex, Mapping) else None,
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
        "failure_kind": None if live_attributed else "runtime_completion_evidence_missing",
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
    if result.get("evidence_provenance") != "live-attributed":
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


def run_smoke(request: SecretaryLaunchRequest, *, output: Path) -> dict[str, Any]:
    _configured_provider(request.codex_home)
    configured_model = _configured_model(request)
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
        configured_model=configured_model,
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
