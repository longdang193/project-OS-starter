from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILL = ROOT / ".agents" / "skills" / "skill-cgw-runtime-operations" / "SKILL.md"


REQUIRED_PACKET_RULES = (
    "CGW receives the delivered prompt content; it cannot resolve a local Windows",
    "A path-only instruction",
    "The bounded packet must contain:",
    "repository identity, exact `HEAD` or base commit, file paths, and content",
    "Apply a request-size budget before sending.",
    "stop on `413 Payload Too\nLarge` rather than blindly retrying",
    "report `incomplete` instead of claiming",
    "Do not\nadd a filesystem service, packet queue, scheduler, or reconciliation framework",
)


def test_cgw_skill_requires_local_review_packet() -> None:
    content = CANONICAL_SKILL.read_text(encoding="utf-8")

    for rule in REQUIRED_PACKET_RULES:
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
        assert "A path-only instruction" in generated_content
        assert "413 Payload Too\nLarge" in generated_content
        assert generated_content.endswith(canonical_body)
