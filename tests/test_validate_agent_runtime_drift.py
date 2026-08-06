"""
@meta
name: test_validate_agent_runtime_drift
type: test
scope: unit
domain: validation
covers:
  - Default and explicit deploy target selection
  - Deploy target normalization and invalid-platform rejection paths
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_agent_runtime_drift.py"
SCRIPTS_ROOT = str(REPO_ROOT / "scripts")

if SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, SCRIPTS_ROOT)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_module("validate_agent_runtime_drift", SCRIPT_PATH)


def test_resolve_platform_selection_defaults_to_codex(tmp_path: Path) -> None:
    args = type("Args", (), {"all_platforms": False, "platform": []})()
    assert VALIDATOR._resolve_platform_selection(tmp_path, args) == (["codex"], "default")


def test_resolve_platform_selection_respects_explicit_platforms(tmp_path: Path) -> None:
    args = type("Args", (), {"all_platforms": False, "platform": ["claude", "codex"]})()
    assert VALIDATOR._resolve_platform_selection(tmp_path, args) == (["claude", "codex"], "explicit")


def test_resolve_platform_selection_all_platforms(tmp_path: Path) -> None:
    args = type("Args", (), {"all_platforms": True, "platform": ["codex"]})()
    assert VALIDATOR._resolve_platform_selection(tmp_path, args) == (["codex", "claude", "gemini"], "all-platforms")


def test_normalize_deploy_targets_alias_and_invalid() -> None:
    normalized, invalid = VALIDATOR._normalize_deploy_targets(
        ["codex", "antigravity", "gemini", "CLAUDE", "bad-platform"]
    )
    assert normalized == ["codex", "gemini", "claude"]
    assert invalid == ["bad-platform"]


def test_main_fails_on_invalid_platform(monkeypatch, tmp_path: Path, capsys) -> None:
    (tmp_path / "adapters").mkdir()
    deploy_script = tmp_path / "scripts" / "deploy_agent_runtime.py"
    deploy_script.parent.mkdir()
    deploy_script.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        VALIDATOR,
        "parse_args",
        lambda: type("Args", (), {"repo_root": str(tmp_path), "skip_deploy_check": False, "all_platforms": False, "platform": ["invalid-target"]})(),
    )
    assert VALIDATOR.main() == 1
    assert "Invalid platform(s) for deploy drift checks" in capsys.readouterr().out


def test_main_runs_default_codex_deploy_target(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "adapters").mkdir()
    deploy_script = tmp_path / "scripts" / "deploy_agent_runtime.py"
    deploy_script.parent.mkdir()
    deploy_script.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        VALIDATOR,
        "parse_args",
        lambda: type("Args", (), {"repo_root": str(tmp_path), "skip_deploy_check": False, "all_platforms": False, "platform": []})(),
    )
    commands: list[list[str]] = []
    monkeypatch.setattr(VALIDATOR, "_run", lambda command, cwd: commands.append(command) or 0)
    assert VALIDATOR.main() == 0
    assert len(commands) == 2
    assert commands[1][-3:] == ["--target", "codex", "--check"]


def test_main_skips_consume_only_kit_runtime_checks(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(
        VALIDATOR,
        "parse_args",
        lambda: type("Args", (), {"repo_root": str(tmp_path), "skip_deploy_check": False, "all_platforms": False, "platform": []})(),
    )
    commands: list[list[str]] = []
    monkeypatch.setattr(VALIDATOR, "_run", lambda command, cwd: commands.append(command) or 0)

    assert VALIDATOR.main() == 0
    assert commands == []
    assert "consume-only kit" in capsys.readouterr().out
