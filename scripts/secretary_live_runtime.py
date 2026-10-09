"""Native Codex capability boundary for live Secretary evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import tomllib
from typing import Any, Callable, Mapping

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from project_os_runtime.secretary_receipts import (
        BLOCKED_CAPABILITY,
        LIVE_RECEIPT_SCHEMA,
        READY,
        sanitize_receipt,
        validate_live_receipt,
    )
except ModuleNotFoundError:
    from scripts.project_os_runtime.secretary_receipts import (
        BLOCKED_CAPABILITY,
        LIVE_RECEIPT_SCHEMA,
        READY,
        sanitize_receipt,
        validate_live_receipt,
    )


class RuntimeConfigurationError(RuntimeError):
    """Raised when native Codex configuration cannot prove capability."""


class SecretaryLaunchError(RuntimeError):
    """Raised when Herdr cannot produce an attributable Secretary receipt."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _powershell_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _parse_json_object(value: str) -> dict[str, Any] | None:
    text = value.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_codex_token_usage(path: Path) -> int | None:
    total = 0
    found = False
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        usage = payload.get("usage") if isinstance(payload, dict) else None
        if not isinstance(usage, Mapping):
            continue
        values = [usage.get(name) for name in ("input_tokens", "output_tokens", "total_tokens")]
        numeric = [value for value in values if isinstance(value, int) and not isinstance(value, bool)]
        if numeric:
            total = max(total, int(usage.get("total_tokens", 0) or 0))
            if not usage.get("total_tokens"):
                total = max(total, sum(numeric))
            found = True
    return total if found else None


def _trial_metrics(*, secretary_enabled: bool, token_usage: int | None) -> dict[str, Any]:
    return {
        "cos_turns": 1,
        "secretary_turns": 1 if secretary_enabled else 0,
        "human_interventions": 0,
        "token_usage": token_usage,
        "cost": None,
    }


def _herdr_json(command: list[str], *, timeout: float) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SecretaryLaunchError("Herdr transport unavailable") from exc
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SecretaryLaunchError(f"Herdr command failed: {detail[:240]}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SecretaryLaunchError("Herdr returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SecretaryLaunchError("Herdr returned non-object JSON")
    return payload


def _owned_secretary_prompt(
    task_id: str,
    plan_revision: str,
    attempt_id: str,
    run_id: str,
    *,
    secretary_enabled: bool,
) -> str:
    role = "Secretary-assisted controller" if secretary_enabled else "CoS-only controller"
    return (
        f"Act as {role} runtime. Do not edit files or call tools. "
        f"Bind task_id={task_id}, plan_revision={plan_revision}, attempt_id={attempt_id}, run_id={run_id}. "
        'Return one JSON object only with keys "publication", "settlement", "acceptance"; '
        'values must be "success", "observed", and "accepted" respectively.'
    )


def launch_secretary_via_herdr(
    runtime: Mapping[str, Any],
    *,
    task_id: str,
    plan_revision: str,
    run_id: str,
    attempt_id: str,
    cwd: Path | None = None,
    herdr: str | None = None,
    timeout: float = 180.0,
    secretary_enabled: bool = True,
) -> dict[str, Any]:
    """Run one bounded Secretary turn through Herdr and native Codex auth."""
    if runtime.get("provider") != "9router":
        raise SecretaryLaunchError("configured provider is not 9router")
    codex_home = str(runtime.get("codex_home") or "")
    model = str(runtime.get("model") or "")
    if not codex_home or not model:
        raise SecretaryLaunchError("native Codex runtime identity incomplete")
    herdr_executable = herdr or shutil.which("herdr")
    codex_executable = shutil.which("codex")
    if not herdr_executable or not codex_executable:
        raise SecretaryLaunchError("Herdr or Codex executable unavailable")

    workdir = (cwd or Path.cwd()).resolve()
    started = _timestamp()
    temp_dir = Path(tempfile.mkdtemp(prefix="project-os-secretary-"))
    last_message = temp_dir / "last-message.txt"
    events = temp_dir / "events.jsonl"
    state = temp_dir / "state.txt"
    script = temp_dir / "run.ps1"
    prompt = _owned_secretary_prompt(
        task_id,
        plan_revision,
        attempt_id,
        run_id,
        secretary_enabled=secretary_enabled,
    )
    script.write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Continue'",
                f"$env:CODEX_HOME = {_powershell_literal(codex_home)}",
                f"& {_powershell_literal(codex_executable)} exec -C {_powershell_literal(str(workdir))} "
                f"-c {_powershell_literal('model_provider=\"9router\"')} "
                f"-c {_powershell_literal('model=' + json.dumps(model))} --ephemeral --json "
                f"-o {_powershell_literal(str(last_message))} {_powershell_literal(prompt)} "
                f"*> {_powershell_literal(str(events))}",
                "$exitCode = $LASTEXITCODE",
                f"Set-Content -LiteralPath {_powershell_literal(str(state))} -Value ([string]$exitCode)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    workspace_id: str | None = None
    try:
        created = _herdr_json(
            [herdr_executable, "workspace", "create", "--cwd", str(workdir), "--label", f"secretary-{attempt_id[:8]}", "--no-focus"],
            timeout=15.0,
        )
        root_pane = created.get("result", {}).get("root_pane", {})
        pane_id = root_pane.get("pane_id") if isinstance(root_pane, dict) else None
        workspace_id = root_pane.get("workspace_id") if isinstance(root_pane, dict) else None
        if not isinstance(pane_id, str) or not isinstance(workspace_id, str):
            raise SecretaryLaunchError("Herdr workspace response missing root pane")
        try:
            completed = subprocess.run(
                [herdr_executable, "pane", "run", pane_id, "powershell", "-NoProfile", "-File", str(script)],
                capture_output=True,
                text=True,
                timeout=15.0,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SecretaryLaunchError("Herdr pane transport unavailable") from exc
        if completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise SecretaryLaunchError(f"Herdr pane run failed: {detail[:240]}")
        deadline = time.monotonic() + timeout
        while not state.is_file() and time.monotonic() < deadline:
            time.sleep(0.2)
        if not state.is_file():
            raise SecretaryLaunchError("Secretary completion receipt timed out")
        exit_code = int(state.read_text(encoding="utf-8").strip())
        if exit_code != 0:
            raise SecretaryLaunchError(f"Secretary Codex command exited {exit_code}")
        response = _parse_json_object(last_message.read_text(encoding="utf-8")) if last_message.is_file() else None
        if response is None:
            raise SecretaryLaunchError("Secretary completion response is not JSON")
        return {
            "schema": LIVE_RECEIPT_SCHEMA,
            "status": READY,
            "task_id": task_id,
            "plan_revision": plan_revision,
            "attempt_id": attempt_id,
            "run_id": run_id,
            "provider": runtime["provider"],
            "model": model,
            "timestamps": {"entry_at": started, "exit_at": _timestamp()},
            "completion": {"observed": True, "operation": "secretary_smoke", "exit_code": exit_code},
            "provenance": {
                "source_type": "runtime",
                "producer": "secretary-live-runtime",
                "source_ref": f"herdr:pane:{pane_id}:attempt:{attempt_id}",
                "observed": True,
            },
            "metrics": _trial_metrics(
                secretary_enabled=secretary_enabled,
                token_usage=_parse_codex_token_usage(events),
            ),
            "outcomes": {
                name: response.get(name) if isinstance(response.get(name), str) else "unknown"
                for name in ("publication", "settlement", "acceptance")
            },
        }
    finally:
        if workspace_id:
            subprocess.run(
                [herdr_executable, "workspace", "close", workspace_id],
                capture_output=True,
                text=True,
                timeout=15.0,
                check=False,
            )
        shutil.rmtree(temp_dir, ignore_errors=True)


def resolve_codex_runtime(codex_home: Path | None = None) -> dict[str, Any]:
    home = Path(codex_home or os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    config_path = home / "config.toml"
    auth_path = home / "auth.json"
    if not config_path.is_file() or not auth_path.is_file():
        raise RuntimeConfigurationError("native Codex config/auth files unavailable")
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeConfigurationError("native Codex configuration unreadable") from exc
    if not isinstance(auth, dict):
        raise RuntimeConfigurationError("native Codex auth shape invalid")
    provider = config.get("model_provider")
    model = config.get("model")
    if not isinstance(provider, str) or not provider:
        raise RuntimeConfigurationError("native Codex provider missing")
    if not isinstance(model, str) or not model:
        raise RuntimeConfigurationError("native Codex model missing")
    return {
        "codex_home": str(home),
        "provider": provider,
        "model": model,
        "auth_present": True,
        "auth_mode": auth.get("auth_mode") if isinstance(auth.get("auth_mode"), str) else "unknown",
    }


def _blocked_receipt(
    *, task_id: str, plan_revision: str, run_id: str, attempt_id: str, runtime: Mapping[str, Any], reason: str
) -> dict[str, Any]:
    return {
        "schema": LIVE_RECEIPT_SCHEMA,
        "status": BLOCKED_CAPABILITY,
        "task_id": task_id,
        "plan_revision": plan_revision,
        "attempt_id": attempt_id,
        "run_id": run_id,
        "provider": runtime.get("provider", "unknown"),
        "model": runtime.get("model", "unknown"),
        "timestamps": {"entry_at": _timestamp(), "exit_at": _timestamp()},
        "completion": {"observed": False, "operation": "secretary_smoke"},
        "provenance": {
            "source_type": "runtime",
            "producer": "secretary-live-runtime",
            "source_ref": "capability-check",
            "observed": True,
        },
        "metrics": {
            "cos_turns": 0,
            "secretary_turns": 0,
            "human_interventions": 0,
            "token_usage": None,
            "cost": None,
        },
        "outcomes": {
            "publication": "not_run",
            "settlement": "unresolved",
            "acceptance": "not_run",
        },
        "capability_reason": reason,
    }


def run_smoke(
    *,
    task_id: str,
    plan_revision: str,
    run_id: str,
    attempt_id: str,
    codex_home: Path | None = None,
    runner: Callable[..., Mapping[str, Any]] | None = launch_secretary_via_herdr,
) -> dict[str, Any]:
    try:
        runtime = resolve_codex_runtime(codex_home)
    except RuntimeConfigurationError as exc:
        runtime = {"provider": "unknown", "model": "unknown"}
        return validate_live_receipt(
            _blocked_receipt(
                task_id=task_id,
                plan_revision=plan_revision,
                run_id=run_id,
                attempt_id=attempt_id,
                runtime=runtime,
                reason=str(exc),
            )
        )
    if runtime["provider"] != "9router":
        return validate_live_receipt(
            _blocked_receipt(
                task_id=task_id,
                plan_revision=plan_revision,
                run_id=run_id,
                attempt_id=attempt_id,
                runtime=runtime,
                reason="configured provider is not 9router",
            )
        )
    if runner is None:
        return validate_live_receipt(
            _blocked_receipt(
                task_id=task_id,
                plan_revision=plan_revision,
                run_id=run_id,
                attempt_id=attempt_id,
                runtime=runtime,
                reason="no owned live Secretary entrypoint",
            )
        )
    try:
        result = dict(
            runner(
                runtime,
                task_id=task_id,
                plan_revision=plan_revision,
                run_id=run_id,
                attempt_id=attempt_id,
            )
        )
    except SecretaryLaunchError as exc:
        return validate_live_receipt(
            _blocked_receipt(
                task_id=task_id,
                plan_revision=plan_revision,
                run_id=run_id,
                attempt_id=attempt_id,
                runtime=runtime,
                reason=str(exc),
            )
        )
    result.setdefault("task_id", task_id)
    result.setdefault("plan_revision", plan_revision)
    result.setdefault("run_id", run_id)
    result.setdefault("attempt_id", attempt_id)
    return validate_live_receipt(result, expected={"attempt_id": attempt_id})


def sanitize_launcher_result(result: Mapping[str, Any]) -> dict[str, Any]:
    return sanitize_receipt(dict(result))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--plan-revision", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--herdr")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--arm", choices=("baseline", "candidate"), default="candidate")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    def runner(runtime: Mapping[str, Any], **identifiers: str) -> Mapping[str, Any]:
        return launch_secretary_via_herdr(
            runtime,
            cwd=args.cwd,
            herdr=args.herdr,
            timeout=args.timeout,
            secretary_enabled=args.arm == "candidate",
            **identifiers,
        )

    receipt = run_smoke(
        task_id=args.task_id,
        plan_revision=args.plan_revision,
        run_id=args.run_id,
        attempt_id=args.attempt_id,
        codex_home=args.codex_home,
        runner=runner,
    )
    safe = sanitize_launcher_result(receipt)
    encoded = json.dumps(safe, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if safe["status"] == READY else 2


__all__ = [
    "RuntimeConfigurationError",
    "SecretaryLaunchError",
    "launch_secretary_via_herdr",
    "main",
    "resolve_codex_runtime",
    "run_smoke",
    "sanitize_launcher_result",
]


if __name__ == "__main__":
    raise SystemExit(main())
