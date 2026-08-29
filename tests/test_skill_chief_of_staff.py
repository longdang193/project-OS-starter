from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_chief_of_staff_has_single_required_read_and_clear_ownership() -> None:
    skill = read(".agents/skills/skill-chief-of-staff/SKILL.md")
    assert "name: skill-chief-of-staff" in skill
    assert "required_reads:\n  - docs/operating_system/rules/git-tracked-coordination-rule.md" in skill
    assert "`skill-executing-plans` owns\napproved-plan execution" in skill
    assert "CoS has no direct Git or PR authority" in skill
    assert "`deepagents` uses\n`dcode-project`" in skill
    assert "`tura` uses `project-delegate`" in skill


def test_chief_of_staff_has_deterministic_binding_runtime_and_status_contract() -> None:
    skill = read(".agents/skills/skill-chief-of-staff/SKILL.md")
    for text in (
        "explicit supplied plan path",
        "plan already bound by the current execution context",
        "exactly one active plan matching the current repository and worktree",
        "otherwise return `BLOCKED`",
        "expected `herdr` executable and version",
        "expected `codex` executable and version",
        "`CODEX_HOME`",
        "required MCP and tool surface",
        "launched process cwd",
        "DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT |",
        "PASS | FAIL | BLOCKED",
    ):
        assert text in skill


def test_chief_of_staff_preserves_lifecycle_boundaries() -> None:
    skill = read(".agents/skills/skill-chief-of-staff/SKILL.md")
    for text in (
        "one exact branch and isolated worktree",
        "merge the exact approved PR into its\ndeclared base after gates pass",
        "Project OS\nreview is separate from GitHub review state",
        "Required distinct-identity approval returns\n`BLOCKED`",
        "retire or stop the\nHerdr main-agent session",
        "Never let an agent remove the worktree\nfrom which it is running",
        "Do not require, create, or treat `identity.md`",
        "Herdr owns transient\nprocess observation only",
    ):
        assert text in skill
    assert "event-driven" not in skill.lower()


def test_executor_skill_keeps_cos_as_codex_coordination_only() -> None:
    skill = read(".agents/skills/skill-executing-plans/SKILL.md")
    assert "`skill-chief-of-staff` as its coordination method" in skill
    assert "Herdr-supervised top-level Codex main\nagent" in skill
    assert "`dcode-project` for `deepagents`" in skill
    assert "project-delegate` for `tura`" in skill


def test_planning_dispatch_selects_cos_only_for_sustained_codex_coordination() -> None:
    dispatch = read("docs/operating_system/planning/planning-dispatch.md")
    assert "## Coordination Method Selection" in dispatch
    assert "optional coordination specialization of" in dispatch
    assert "sustained\nhandoffs, independent top-level Codex main-agent lanes" in dispatch
    assert "does not add an executor, profile, plan field, or durable state artifact" in dispatch
    assert "Herdr is runtime observation and\nmain-agent supervision" in dispatch
    assert "`deepagents`\nand `tura` retain their existing peer executor paths" in dispatch
