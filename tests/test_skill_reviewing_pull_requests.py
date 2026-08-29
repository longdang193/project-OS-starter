from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pull_request_review_is_head_bound_and_has_project_os_verdict() -> None:
    skill = read(".agents/skills/skill-reviewing-pull-requests/SKILL.md")
    for text in (
        "exact reviewed head",
        "repository, PR number, base ref and SHA when material",
        "head ref and SHA",
        "`PASS`:",
        "`FAIL`:",
        "`BLOCKED`:",
        "New commits invalidate prior review evidence",
    ):
        assert text in skill


def test_pull_request_review_separates_github_identity_and_mutation() -> None:
    skill = read(".agents/skills/skill-reviewing-pull-requests/SKILL.md")
    assert "Project OS review is separate from GitHub review state" in skill
    assert "differs from PR author when" in skill
    assert "Required distinct-identity approval returns" in skill
    assert "do not create another account" in skill
    assert "Do not mutate the PR" in skill
    assert "does not complete a task or update the active plan ledger" in skill
