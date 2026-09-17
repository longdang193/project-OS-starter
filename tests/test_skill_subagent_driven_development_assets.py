from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest  # type: ignore[import-not-found]  # pytest stub unavailable in env

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / ".agents" / "skills" / "skill-subagent-driven-development" / "scripts"


def _resolve_bash() -> str | None:
    git_path = shutil.which("git")
    if git_path is not None:
        git_bash = Path(git_path).resolve().parents[1] / "bin" / "bash.exe"
        if git_bash.is_file():
            return str(git_bash)
    return shutil.which("bash")


BASH = _resolve_bash()

pytestmark = pytest.mark.skipif(BASH is None, reason="bash not available")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _run_script(repo: Path, script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    assert BASH is not None
    environment = os.environ.copy()
    return subprocess.run(
        [BASH, str(SCRIPTS_DIR / script_name), *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )


def _init_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")


def test_sdd_workspace_creates_self_ignored_directory(tmp_path: Path) -> None:
    _init_repo(tmp_path)

    completed = _run_script(tmp_path, "sdd-workspace")

    workspace_output = completed.stdout.strip()
    workspace = tmp_path / ".superpowers" / "sdd"
    assert workspace_output.endswith("/.superpowers/sdd")
    assert (workspace / ".gitignore").read_text(encoding="utf-8") == "*\n"
    assert _git(tmp_path, "status", "--short") == ""


def test_task_brief_extracts_single_task(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    plan = tmp_path / "docs" / "superpowers" / "plans" / "sample-plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(
        """# Sample Plan\n\n### Task 1: Alpha\n\nKeep alpha.\n\n### Task 2: Beta\n\nKeep beta only.\n""",
        encoding="utf-8",
    )
    output = tmp_path / "task-2-brief.md"

    _run_script(tmp_path, "task-brief", str(plan), "2", str(output))

    brief = output.read_text(encoding="utf-8")
    assert "Task 2: Beta" in brief
    assert "Keep beta only." in brief
    assert "Task 1: Alpha" not in brief


def test_review_package_writes_commit_log_and_diff(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    target = tmp_path / "demo.txt"
    target.write_text("alpha\n", encoding="utf-8")
    _git(tmp_path, "add", "demo.txt")
    _git(tmp_path, "commit", "-m", "base")
    base_sha = _git(tmp_path, "rev-parse", "HEAD")

    target.write_text("alpha\nbeta\n", encoding="utf-8")
    _git(tmp_path, "commit", "-am", "expand demo")
    head_sha = _git(tmp_path, "rev-parse", "HEAD")

    output = tmp_path / "review.diff"
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        '[{"status":"M","new_path":"demo.txt"}]\n',
        encoding="utf-8",
    )
    policy = tmp_path / "policy.json"
    policy.write_text('{"protected_paths":[],"protected_entries":[]}\n', encoding="utf-8")
    _run_script(
        tmp_path,
        "review-package",
        base_sha,
        head_sha,
        str(output),
        "--inventory",
        str(inventory),
        "--content-policy",
        str(policy),
    )

    package = output.read_text(encoding="utf-8")
    assert f"# Review package: {base_sha}..{head_sha}" in package
    assert "expand demo" in package
    assert "+beta" in package


def test_review_package_scopes_content_and_omits_protected_entries(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    safe = tmp_path / "safe.txt"
    secret = tmp_path / ".env"
    safe.write_text("safe base\n", encoding="utf-8")
    secret.write_text("TOKEN=do-not-disclose\n", encoding="utf-8")
    _git(tmp_path, "add", "safe.txt", ".env")
    _git(tmp_path, "commit", "-m", "base")
    base_sha = _git(tmp_path, "rev-parse", "HEAD")
    safe.write_text("safe changed\n", encoding="utf-8")
    secret.write_text("TOKEN=still-do-not-disclose\n", encoding="utf-8")
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("unrelated-do-not-include\n", encoding="utf-8")
    _git(tmp_path, "add", "safe.txt", ".env")
    _git(tmp_path, "commit", "-m", "change")
    head_sha = _git(tmp_path, "rev-parse", "HEAD")

    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        '[{"status":"M","new_path":"safe.txt"},{"status":"M","new_path":".env"}]\n',
        encoding="utf-8",
    )
    policy = tmp_path / "policy.json"
    policy.write_text(
        '{"protected_paths":[".env"],"protected_entries":[{"status":"M","new_path":".env","reason":".env"}]}\n',
        encoding="utf-8",
    )
    output = tmp_path / "review.diff"
    _run_script(
        tmp_path,
        "review-package",
        base_sha,
        head_sha,
        str(output),
        "--inventory",
        str(inventory),
        "--content-policy",
        str(policy),
    )

    package = output.read_text(encoding="utf-8")
    assert "safe changed" in package
    assert "TOKEN=do-not-disclose" not in package
    assert "TOKEN=still-do-not-disclose" not in package
    assert "unrelated-do-not-include" not in package
    assert "protected content omitted" in package
