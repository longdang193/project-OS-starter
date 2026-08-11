from __future__ import annotations

import argparse
import json
from pathlib import Path

from .loader import load_core
from .runtime_manager import RuntimeManager, RuntimeManagerError


_MANAGED_SUCCESS_STATES = frozenset({"accepted", "awaiting_decision", "configured", "planned", "ready", "verified"})


def _managed_response_state(payload: dict[str, object]) -> str | None:
    for key in ("state", "status"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def _managed_exit_code(command: str, payload: dict[str, object]) -> int:
    if command == "terminalize-attempt":
        return 1 if payload.get("error") else 0
    return 0 if _managed_response_state(payload) in _MANAGED_SUCCESS_STATES else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage verified harness runtime profiles.")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--runtime-root")
    subparsers = parser.add_subparsers(dest="command")
    upgrade = subparsers.add_parser("upgrade")
    upgrade.add_argument("--host-root", required=True)
    subparsers.add_parser("rollback")
    subparsers.add_parser("doctor")
    subparsers.add_parser("capabilities")
    subparsers.add_parser("preflight")
    run = subparsers.add_parser("run")
    run.add_argument("--harness-root", required=True)
    run_input = run.add_mutually_exclusive_group(required=True)
    run_input.add_argument("--request", metavar="REQUEST_FILE", help="Path to managed request JSON file")
    run_input.add_argument("--run-id")
    decision = subparsers.add_parser("decision")
    decision.add_argument("--harness-root", required=True)
    decision.add_argument("--run-id", required=True)
    decision.add_argument("--decision", metavar="DECISION_FILE", required=True, help="Path to controller decision JSON file")
    terminalize_attempt = subparsers.add_parser("terminalize-attempt")
    terminalize_attempt.add_argument("--harness-root", required=True)
    terminalize_attempt.add_argument("--run-id", required=True)
    terminalize_attempt.add_argument("--input", metavar="ENVELOPE_FILE", required=True, help="Path to terminalization envelope JSON file")
    args = parser.parse_args(argv)
    if args.command:
        manager = RuntimeManager(Path(args.runtime_root) if args.runtime_root else None)
        try:
            if args.command == "upgrade":
                payload = manager.upgrade(Path(args.host_root))
            elif args.command == "rollback":
                payload = manager.rollback()
            elif args.command == "doctor":
                payload = manager.doctor()
            elif args.command == "capabilities":
                payload = manager.invoke_host(["capabilities"])
            elif args.command == "preflight":
                payload = manager.invoke_host(["preflight"])
            elif args.command == "run":
                host_args = ["run", "--harness-root", args.harness_root]
                host_args.extend(["--run-id", args.run_id] if args.run_id else ["--request", args.request])
                payload = manager.invoke_host(host_args)
            elif args.command == "decision":
                payload = manager.invoke_host([
                    "decision",
                    "--harness-root",
                    args.harness_root,
                    "--run-id",
                    args.run_id,
                    "--decision",
                    args.decision,
                ])
            elif args.command == "terminalize-attempt":
                payload = manager.terminalize_attempt(args.harness_root, args.run_id, args.input)
            else:
                raise RuntimeManagerError("harness_runtime_profile_invalid")
        except RuntimeManagerError as error:
            print(json.dumps({"state": error.code}, sort_keys=True))
            return 1
        print(json.dumps(payload, sort_keys=True))
        if args.command in {"capabilities", "preflight", "run", "decision", "terminalize-attempt"}:
            return _managed_exit_code(args.command, payload)
        return 0 if payload.get("state") in {"accepted", "configured", "ready"} else 1
    result = load_core()
    if isinstance(result, dict):
        print(json.dumps(result, sort_keys=True))
        return 1
    if args.probe:
        print(json.dumps({"ok": True, "package": "harness-core"}, sort_keys=True))
    return 0
