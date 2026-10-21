from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILL = ROOT / ".agents" / "skills" / "skill-cgw-runtime-operations" / "SKILL.md"


REQUIRED_EXECUTION_BOUNDARY_RULES = (
    "Herdr is the only supported CGW execution controller",
    "Native Codex subagents must not select or launch",
    "`web-high` and `web-medium` are Herdr-only",
    "CGW Chat is text-only",
    "optional client `tools` and `tool_choice` metadata",
)

REQUIRED_GITHUB_REVIEW_RULES = (
    "prefer a GitHub-backed source",
    "Commit and push the selected plan or code",
    "the repository and exact branch or commit",
    "the file path or GitHub file URL",
    "Do not send a local Windows path as the only review input.",
    "confirm that it read the requested revision",
)

REQUIRED_LOCAL_FALLBACK_RULES = (
    "Use a local review packet only as a fallback",
    "CGW receives delivered\nprompt content; it cannot resolve a local Windows",
    "The bounded fallback packet must contain:",
    "A GitHub URL is not a fallback",
    "repository identity, exact `HEAD` or base commit, file paths, and content",
    "Apply a request-size budget before sending.",
    "stop on `413 Payload Too\nLarge` rather than blindly retrying",
    "report `incomplete` instead of claiming",
    "the fallback packet is request-scoped evidence, not a second runtime owner.",
)


def test_cgw_skill_requires_herdr_execution_boundary() -> None:
    content = CANONICAL_SKILL.read_text(encoding="utf-8")

    for rule in REQUIRED_EXECUTION_BOUNDARY_RULES:
        assert rule in content
    assert "GitHub, filesystem, or other tools executed inside CGW" in content


def test_cgw_skill_prefers_github_review_source() -> None:
    content = CANONICAL_SKILL.read_text(encoding="utf-8")

    for rule in REQUIRED_GITHUB_REVIEW_RULES:
        assert rule in content


def test_cgw_skill_keeps_bounded_local_fallback() -> None:
    content = CANONICAL_SKILL.read_text(encoding="utf-8")

    for rule in REQUIRED_LOCAL_FALLBACK_RULES:
        assert rule in content


def test_generated_cgw_skill_surfaces_keep_local_review_packet_rule() -> None:
    canonical = CANONICAL_SKILL.read_text(encoding="utf-8")
    canonical_body = canonical.split("---\n", 2)[2].lstrip("\n")

    for platform in ("codex", "claude", "antigravity"):
        generated = (
            ROOT
            / "generated_agents"
            / platform
            / "skills"
            / "skill-cgw-runtime-operations"
            / "SKILL.md"
        )
        generated_content = generated.read_text(encoding="utf-8")
        assert "prefer a GitHub-backed source" in generated_content
        assert "Use a local review packet only as a fallback" in generated_content
        assert "413 Payload Too\nLarge" in generated_content
        assert generated_content.endswith(canonical_body)
