from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.split())


def test_write_capable_implementation_lanes_have_mandatory_isolated_lanes() -> None:
    worktree = flat(read(".agents/skills/skill-using-git-worktrees/SKILL.md"))
    coordination = flat(read("docs/operating_system/rules/git-tracked-coordination-rule.md"))
    assert "For a write-capable Herdr implementation lane, isolation is mandatory" in worktree
    assert "explicit approved-plan lane authority" in worktree
    assert "launched process cwd" in worktree
    assert "exact base commit recorded by the active plan" in worktree
    assert "A healthy live lane may continue" in worktree
    assert "replacement runtime" in worktree
    assert "A write-capable coordinated implementation lane uses one exact branch and isolated worktree" in coordination


def test_lane_authority_allows_exact_pr_merge_but_not_exceptional_mutation() -> None:
    finishing = flat(read(".agents/skills/skill-finishing-a-development-branch/SKILL.md"))
    template = flat(read("docs/operating_system/templates/implementation-plan-template.md"))
    for text in (
        "exact lane: branch/worktree creation or reuse, lane commits, lane push",
        "designated Codex integration action owns an exact approved PR merge",
        "Direct or exceptional base mutation",
        "force push",
        "PR retargeting",
        "branch-protection bypass",
        "semantic conflict resolution",
        "merging another lane",
    ):
        assert text in finishing
    assert "An active plan may preauthorize an assigned implementation lane" in template
    assert "Independent Codex review lanes own assigned review actions" in template
    assert "A designated Codex integration action owns an exact approved PR merge" in template


def test_coordination_preserves_checkpoint_and_serialized_integration_truth() -> None:
    coordination = flat(read("docs/operating_system/rules/git-tracked-coordination-rule.md"))
    for text in (
        "Lane commits are implementation artifacts, not coordination checkpoints",
        "one dependency-ready integration action at a time to one designated Codex integration lane",
        "expected reviewed head",
        "no post-review lane commit",
        "retire the associated top-level lane process",
        "relevant descendants and task-owned resources",
        "active agent never removes its own worktree",
        "A lane commit cannot mark its task complete",
    ):
        assert text in coordination
    assert "skill-finishing-a-development-branch` owns Git disposition" in coordination


def test_review_dispatch_is_topology_neutral_and_review_is_head_bound() -> None:
    requester = flat(read(".agents/skills/skill-requesting-code-review/SKILL.md"))
    reviewer = flat(read(".agents/skills/skill-reviewing-pull-requests/SKILL.md"))
    assert "Select review topology from the owning coordination method" in requester
    assert "independent Herdr top-level Codex main agent" in requester
    assert "makes the reviewer a merge owner" in requester
    assert "exact reviewed head" in reviewer
    assert "Project OS review is separate from GitHub review state" in reviewer
    assert "differs from PR author when required" in reviewer


def test_finishing_separates_publication_from_final_integration() -> None:
    finishing = flat(read(".agents/skills/skill-finishing-a-development-branch/SKILL.md"))
    assert "accepted task-proof handoff for branch or PR publication" in finishing
    assert "fresh `verified` result" in finishing
    assert "re-read provider PR state immediately before merge" in finishing
    assert "reconciliation-required" in finishing



def test_executor_authority_is_codex_only_across_live_contracts() -> None:
    paths = (
        ".agents/skills/skill-chief-of-staff/SKILL.md",
        ".agents/skills/skill-executing-plans/SKILL.md",
        ".agents/skills/skill-finishing-a-development-branch/SKILL.md",
        "docs/operating_system/procedures/personal-local-worktree-procedure.md",
        "docs/operating_system/rules/git-tracked-coordination-rule.md",
        "docs/operating_system/templates/implementation-plan-template.md",
    )
    for path in paths:
        text = " ".join(read(path).split())
        assert "Independent Codex review lanes own assigned review actions" in text
        assert "designated Codex integration action owns an exact approved PR merge" in text
