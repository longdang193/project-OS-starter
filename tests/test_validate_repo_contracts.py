"""
@meta
name: test_validate_repo_contracts
type: test
scope: unit
domain: docs
covers:
  - Repo contract validator orchestration and fast-mode success on the current starter repo
  - Partial-generated feature history boundary validation
  - Required metadata coverage rules for setup scripts and architecture-aware YAML
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import uuid
from pathlib import Path
from shutil import rmtree


REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_repo_contracts.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_repo_contracts", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load validate_repo_contracts.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator_module()


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_test_root() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"validate-repo-contracts-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_validator_fast_mode_passes_for_current_repo() -> None:
    result = run_validator("--fast")

    assert result.returncode == 0
    assert "repo contract validation passed" in result.stdout.lower()


def test_validate_history_boundaries_reports_missing_human_notes() -> None:
    test_root = make_test_root()
    try:
        write_text(
            test_root / "docs" / "features" / "demo-feature" / "feature.source.yaml",
            "feature_id: demo-feature\nname: Demo\nstatus: active\ntype: workflow\nsummary: Demo\ninvariants: []\ndomains: []\ndepends_on: []\ncapabilities: []\n",
        )
        write_text(
            test_root / "docs" / "features" / "demo-feature" / "history.md",
            "# Demo History\n\n<!-- GENERATED HISTORY START -->\n\nNothing yet.\n\n<!-- GENERATED HISTORY END -->\n",
        )

        issues = VALIDATOR.validate_history_boundaries(test_root)

        assert len(issues) == 1
        assert issues[0].category == "partial_generated_boundary_error"
        assert "human notes" in issues[0].message.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_required_metadata_coverage_allows_leading_comment_before_architecture_block() -> None:
    test_root = make_test_root()
    try:
        write_text(
            test_root / "configs" / "demo.yaml",
            "# Helpful comment.\n# @architecture\n# owner: demo-feature\n# stages:\n#   - fixed_train\n# role: config\nvalue: 1\n",
        )
        write_text(
            test_root / "aml" / "components" / "demo.yaml",
            "# @architecture\n# owner: demo-feature\n# stages:\n#   - fixed_train\n# role: component\ncomponent: true\n",
        )
        write_text(
            test_root / "setup" / "demo.sh",
            "#!/usr/bin/env sh\n# @meta\n# type: script\n# name: demo_setup\n\necho ok\n",
        )

        issues = VALIDATOR.validate_required_metadata_coverage(test_root)

        assert issues == []
    finally:
        rmtree(test_root, ignore_errors=True)


def test_main_propagates_subprocess_failure(monkeypatch) -> None:
    monkeypatch.setattr(VALIDATOR, "validate_required_metadata_coverage", lambda root: [])
    monkeypatch.setattr(VALIDATOR, "validate_history_boundaries", lambda root: [])
    monkeypatch.setattr(
        VALIDATOR,
        "build_subprocess_steps",
        lambda *, root, python_executable, fast: [["python", "fake-step"]],
    )
    monkeypatch.setattr(VALIDATOR, "run_step", lambda command, cwd: 1)

    status = VALIDATOR.main(["--repo-root", str(REPO_ROOT), "--fast"])

    assert status == 1
