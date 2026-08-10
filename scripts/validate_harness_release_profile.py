from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import yaml

from harness_core import runtime_protocol_profile
from harness_core.compatibility import POLICY_SCHEMA_VERSION


_PROFILE_PATH_PREFIXES = (
    "packages/harness-core/src/harness_core/compatibility.py",
    "packages/harness-core/src/harness_core/runtime_profile.py",
    "packages/harness-core/src/harness_core/managed.py",
    "packages/harness-core-launcher/",
    "src/codex_harness_host/",
)
_CONSUMER_PATH_PREFIXES = (
    "repo_config/",
    "docs/operating_system/",
    "scripts/deploy_harness_core_to_host.ps1",
)
_GUIDANCE_PATHS = (
    "docs/operating_system/procedures/harness-core-consumer-setup.md",
    "docs/operating_system/procedures/managed-execution-adapter-contract.md",
    "docs/operating_system/templates/agents/root-AGENTS.template.md",
    "docs/operating_system/rules/multi-agent-orchestration-rule.md",
)


def classify_release_paths(paths: Iterable[str]) -> str:
    normalized = tuple(path.replace("\\", "/") for path in paths)
    if any(path.startswith(_CONSUMER_PATH_PREFIXES) for path in normalized):
        return "consumer_schema"
    if any(path.startswith(_PROFILE_PATH_PREFIXES) for path in normalized):
        return "profile"
    return "implementation"


def validate(root: Path, *, runtime_root: Path | None = None) -> dict[str, object]:
    root = root.resolve()
    policy_path = root / "repo_config" / "harness.yaml"
    try:
        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError("harness_release_profile_policy_invalid") from exc
    if not isinstance(policy, dict) or policy.get("version") != POLICY_SCHEMA_VERSION:
        raise ValueError("harness_release_profile_policy_invalid")
    providers = policy.get("runtime_providers")
    if not isinstance(providers, dict) or not isinstance(providers.get("codex_app_server"), dict):
        raise ValueError("harness_release_profile_policy_invalid")
    if "contract_version" in providers["codex_app_server"]:
        raise ValueError("harness_release_profile_policy_invalid")
    for relative_path in _GUIDANCE_PATHS:
        text = (root / relative_path).read_text(encoding="utf-8")
        if "uv run --locked codex-harness-host" in text:
            raise ValueError("harness_release_profile_guidance_drift")
    result: dict[str, object] = {
        "state": "ready",
        "protocol_profile": runtime_protocol_profile(policy["harness_core"]["request_api"]),
    }
    if runtime_root is not None:
        from harness_core_launcher.runtime_manager import RuntimeManager

        active = RuntimeManager(runtime_root).doctor()
        if active["protocol_profile"] != result["protocol_profile"]:
            raise ValueError("harness_runtime_profile_mismatch")
        result["active_runtime_release_profile"] = active
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate harness release profile SSOT.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--runtime-root")
    parser.add_argument("--changed", action="append", default=[])
    parser.add_argument("--fast", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = validate(
            Path(args.repo_root),
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
        )
    except ValueError as error:
        print(json.dumps({"state": str(error)}, sort_keys=True))
        return 1
    payload["release_tier"] = classify_release_paths(args.changed)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
