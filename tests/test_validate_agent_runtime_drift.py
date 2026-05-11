"""
@meta
name: test_validate_agent_runtime_drift
type: test
scope: unit
domain: validation
covers:
  - Mode/policy-driven deploy target selection in validate_agent_runtime_drift.py
  - CLI override precedence for runtime drift deploy checks
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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_adoption_mode(root: Path, *, mode: str, role: str) -> None:
    _write_text(
        root / "repo_config" / "adoption-mode.yaml",
        f"""adoption_mode: {mode}
repo_role: {role}
managed_architecture_metadata: {str(mode == 'managed_architecture_metadata').lower()}
legacy_feature_contracts: false
architecture_generator: none
""",
    )


def _write_policy(root: Path, content: str) -> None:
    _write_text(root / "repo_config" / "adapter-sync-policy.yaml", content)


def test_resolve_platform_selection_uses_mode_policy_defaults(tmp_path: Path) -> None:
    _write_adoption_mode(tmp_path, mode="starter_method_only", role="consumer_derived")
    _write_policy(
        tmp_path,
        """default_platforms:
  - codex
mode_role_platforms:
  consumer_derived:
    starter_method_only:
      - codex
""",
    )

    namespace = type("Args", (), {"all_platforms": False, "platform": []})()

    selected, reason = VALIDATOR._resolve_platform_selection(tmp_path, namespace)

    assert selected == ["codex"]
    assert reason.startswith("mode-policy(")


def test_resolve_platform_selection_cli_override_wins(tmp_path: Path) -> None:
    _write_adoption_mode(tmp_path, mode="starter_method_only", role="consumer_derived")
    _write_policy(
        tmp_path,
        """default_platforms:
  - codex
""",
    )

    namespace = type("Args", (), {"all_platforms": False, "platform": ["claude", "codex", "claude"]})()

    selected, reason = VALIDATOR._resolve_platform_selection(tmp_path, namespace)

    assert selected == ["claude", "codex"]
    assert reason == "cli-platform"


def test_resolve_platform_selection_all_platforms_override(tmp_path: Path) -> None:
    namespace = type("Args", (), {"all_platforms": True, "platform": ["codex"]})()

    selected, reason = VALIDATOR._resolve_platform_selection(tmp_path, namespace)

    assert selected == ["codex", "claude", "gemini"]
    assert reason == "all-platforms"


def test_normalize_deploy_targets_alias_and_invalid() -> None:
    normalized, invalid = VALIDATOR._normalize_deploy_targets(
        ["codex", "antigravity", "gemini", "CLAUDE", "bad-platform"]
    )

    assert normalized == ["codex", "gemini", "claude"]
    assert invalid == ["bad-platform"]


def test_main_fails_on_invalid_platform(monkeypatch, tmp_path: Path, capsys) -> None:
    _write_adoption_mode(tmp_path, mode="starter_method_only", role="consumer_derived")
    _write_policy(
        tmp_path,
        """default_platforms:
  - codex
""",
    )

    monkeypatch.setattr(
        VALIDATOR,
        "parse_args",
        lambda: type(
            "Args",
            (),
            {
                "repo_root": str(tmp_path),
                "skip_deploy_check": False,
                "all_platforms": False,
                "platform": ["invalid-target"],
            },
        )(),
    )

    status = VALIDATOR.main()
    output = capsys.readouterr().out

    assert status == 1
    assert "Invalid platform(s) for deploy drift checks" in output


def test_main_runs_mode_policy_scoped_deploy_targets(monkeypatch, tmp_path: Path) -> None:
    _write_adoption_mode(tmp_path, mode="starter_method_only", role="consumer_derived")
    _write_policy(
        tmp_path,
        """default_platforms:
  - codex
mode_role_platforms:
  consumer_derived:
    starter_method_only:
      - codex
""",
    )

    monkeypatch.setattr(
        VALIDATOR,
        "parse_args",
        lambda: type(
            "Args",
            (),
            {
                "repo_root": str(tmp_path),
                "skip_deploy_check": False,
                "all_platforms": False,
                "platform": [],
            },
        )(),
    )

    recorded_commands: list[list[str]] = []

    def _fake_run(command: list[str], cwd: Path) -> int:
        recorded_commands.append(command)
        return 0

    monkeypatch.setattr(VALIDATOR, "_run", _fake_run)

    status = VALIDATOR.main()

    assert status == 0
    assert len(recorded_commands) == 2
    assert "sync_agent_adapters.py" in recorded_commands[0][1]
    assert "deploy_agent_runtime.py" in recorded_commands[1][1]
    assert recorded_commands[1][-3:] == ["--target", "codex", "--check"]
