from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.split())


def test_write_capable_main_agents_have_mandatory_isolated_lanes() -> None:
    worktree = flat(read(".agents/skills/skill-using-git-worktrees/SKILL.md"))
    coordination = flat(read("docs/operating_system/rules/git-tracked-coordination-rule.md"))
    assert "For a write-capable Herdr main-agent lane, isolation is mandatory" in worktree
    assert "explicit approved-plan lane grant" in worktree
    assert "launched process cwd" in worktree
    assert "A write-capable main-agent lane uses one exact branch and isolated worktree" in coordination


def test_lane_authority_allows_exact_pr_merge_but_not_exceptional_mutation() -> None:
    finishing = flat(read(".agents/skills/skill-finishing-a-development-branch/SKILL.md"))
    template = flat(read("docs/operating_system/templates/implementation-plan-template.md"))
    for text in (
        "exact lane: branch/worktree creation or reuse, lane commits, lane push",
        "exact approved PR merge into declared base after gates",
        "Direct or exceptional base mutation",
        "force push",
        "PR retargeting",
        "branch-protection bypass",
        "semantic conflict resolution",
        "merging another lane",
    ):
        assert text in finishing
    assert "An active plan may preauthorize an assigned lane main agent" in template
    assert "merge the exact approved PR into its declared base after gates" in template


def test_coordination_preserves_checkpoint_and_serialized_integration_truth() -> None:
    coordination = flat(read("docs/operating_system/rules/git-tracked-coordination-rule.md"))
    for text in (
        "Lane commits are implementation artifacts, not coordination checkpoints",
        "one dependency-ready integration action at a time to one designated main agent",
        "expected reviewed head",
        "no post-review lane commit",
        "retire the associated main-agent process",
        "active agent never removes its own worktree",
    ):
        assert text in coordination


def test_review_dispatch_is_topology_neutral_and_review_is_head_bound() -> None:
    requester = flat(read(".agents/skills/skill-requesting-code-review/SKILL.md"))
    reviewer = flat(read(".agents/skills/skill-reviewing-pull-requests/SKILL.md"))
    assert "Select review topology from the owning coordination method" in requester
    assert "independent Herdr top-level Codex main agent" in requester
    assert "makes the reviewer a merge owner" in requester
    assert "exact reviewed head" in reviewer
    assert "Project OS review is separate from GitHub review state" in reviewer
    assert "differs from PR author when required" in reviewer
