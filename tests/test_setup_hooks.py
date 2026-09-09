"""
@meta
name: test_setup_hooks
type: test
scope: unit
domain: docs
covers:
  - Local hook setup scripts install the canonical repo-contract validator entrypoint.
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT_PATHS = [
    REPO_ROOT / "scripts" / "setup_hooks.ps1",
    REPO_ROOT / "scripts" / "setup_hooks.sh",
]


def test_hook_setup_scripts_install_repo_contract_validator_entrypoint() -> None:
    for script_path in HOOK_SCRIPT_PATHS:
        script_text = script_path.read_text(encoding="utf-8")

        assert "validate_repo_contracts.py" in script_text
        assert "--repo-root" in script_text
        assert "--fast" in script_text
        assert ".venv" in script_text


def test_hook_setup_scripts_resolve_runtime_paths_and_preserve_existing_hooks() -> None:
    for script_path in HOOK_SCRIPT_PATHS:
        script_text = script_path.read_text(encoding="utf-8")

        assert "rev-parse --path-format=absolute --git-path hooks" in script_text
        assert "repo_root=\"$(git rev-parse --show-toplevel)\"" in script_text
        assert "pre-commit.project-os.previous" in script_text
        assert "project-os-pre-commit-v1" in script_text
