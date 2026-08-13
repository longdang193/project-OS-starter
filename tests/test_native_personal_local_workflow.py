"""
@meta
name: test_native_personal_local_workflow
type: test
scope: unit
domain: docs
distribution_tier: starter_kit
covers:
  - Native personal-local workflow ships through starter guidance
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent


def run_git(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_native_personal_local_workflow_is_documented_and_shipped() -> None:
    procedure = ROOT / "docs" / "operating_system" / "procedures" / "personal-local-worktree-procedure.md"
    procedure_text = procedure.read_text(encoding="utf-8")
    root_guidance = (ROOT / "docs" / "operating_system" / "templates" / "agents" / "root-AGENTS.template.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "repo_config" / "starter-kit-manifest.json").read_text(encoding="utf-8"))

    assert "native-personal-local" in procedure_text
    assert "Git worktree" in procedure_text
    assert "Codex or DeepAgents" in procedure_text
    assert "Resume In A New Task" in procedure_text
    assert "dcode -r" in procedure_text
    assert "DeepAgents Tool Boundary" in procedure_text
    assert "--no-mcp" in procedure_text
    assert "Codex MCP servers" in procedure_text
    assert "codex.mcp.handoff.v1" in procedure_text
    assert "--handoff-file" in procedure_text
    assert "--mcp-select" in procedure_text
    assert "native-personal-local" in root_guidance
    assert "Codex or DeepAgents" in root_guidance
    assert "native-personal-local" in readme
    assert "Codex or DeepAgents" in readme
    assert "docs/operating_system" in manifest["copyPaths"]
    assert "tests/test_native_personal_local_workflow.py" in manifest["copyPaths"]


def test_native_git_evidence_exposes_tracked_and_untracked_scope_changes(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init", "-q")
    run_git(repository, "config", "user.name", "Test User")
    run_git(repository, "config", "user.email", "test@example.invalid")

    allowed = repository / "allowed.txt"
    allowed.write_text("before\n", encoding="utf-8")
    run_git(repository, "add", "allowed.txt")
    run_git(repository, "commit", "-qm", "baseline")
    base = run_git(repository, "rev-parse", "HEAD").stdout.strip()

    allowed.write_text("after\n", encoding="utf-8")
    (repository / "outside.txt").write_text("outside scope\n", encoding="utf-8")

    tracked = run_git(repository, "diff", "--name-status", "-z", "-M", "-C", "--find-copies-harder", base, "--").stdout.split("\0")
    untracked = run_git(repository, "ls-files", "--others", "--exclude-standard", "-z").stdout.split("\0")

    changed_paths = {tracked[index + 1] for index, entry in enumerate(tracked[:-1]) if entry == "M"}
    untracked_paths = {entry for entry in untracked if entry}

    assert changed_paths == {"allowed.txt"}
    assert untracked_paths == {"outside.txt"}
    assert untracked_paths - {"allowed.txt"}


def test_single_controller_resume_contract_is_documented() -> None:
    procedure_text = (
        ROOT / "docs" / "operating_system" / "procedures" / "personal-local-worktree-procedure.md"
    ).read_text(encoding="utf-8")
    template_text = (
        ROOT / "docs" / "operating_system" / "templates" / "implementation-plan-template.md"
    ).read_text(encoding="utf-8")

    for step in range(1, 8):
        assert f"{step}." in procedure_text
    assert "Coordination State (Optional)" in template_text
    assert "Executor: `codex | deepagents`" in template_text
    assert "current DeepAgents launcher uses no MCP" in template_text
    assert "Exactly one task" in template_text
