from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def cleanup_skill() -> str:
    return " ".join(
        (ROOT / ".agents/skills/skill-disposable-artifact-cleanup/SKILL.md")
        .read_text(encoding="utf-8")
        .split()
    )


def test_cleanup_skill_uses_exact_resource_identity_and_owner_routing() -> None:
    text = cleanup_skill()
    for phrase in (
        "exact normalized resource identity",
        "filesystem artifact: absolute path or task-owned directory",
        "Git worktree: path, branch or detached state, creation mechanism",
        "Herdr resource: session, pane, agent",
        "browser or application state: isolated profile or storage scope",
        "database: exact database path or instance scope",
        "cleanup mode: `direct` or `delegated`",
        "delegated cleanup owner and actual supported procedure are identified",
    ):
        assert phrase in text


def test_cleanup_skill_separates_eligibility_from_delegated_removal() -> None:
    text = cleanup_skill()
    assert "For `delegated`, `eligible` means the named owner may perform" in text
    assert "it does not mean this skill removed the resource" in text
    assert "Do not report delegated resources as removed until the owner returns verified cleanup evidence" in text
    assert "Reusing an existing Herdr pane or worktree does not grant cleanup authority" in text


def test_cleanup_skill_preserves_protected_state_and_lifecycle_order() -> None:
    text = cleanup_skill()
    for phrase in (
        "databases, backups, uploads, normal profiles, and application state",
        "live or uncertain runtime resources",
        "Direct cleanup runs before the final `verified` snapshot",
        "after verified Git disposition, lane retirement, clean-state proof",
        "Do not call `git clean`",
        "Never recursively delete a worktree directory directly",
        "Missing, stale, or uncertain evidence means `preserve`",
    ):
        assert phrase in text


def test_cleanup_skill_names_supported_runtime_and_producer_procedures() -> None:
    text = cleanup_skill()
    for phrase in (
        "launcher termination logic is not a general cleanup CLI",
        "supported launcher reconciliation procedure",
        "native cleanup for native-managed workspaces",
        "`git worktree remove <path>`",
        "Producer-owned cleanup",
        "producing workflow or lifecycle owner remains authoritative for Herdr runtime",
    ):
        assert phrase in text
