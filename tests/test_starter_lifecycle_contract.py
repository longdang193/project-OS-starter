"""
@meta
# distribution_tier: starter_kit
name: test_starter_lifecycle_contract
type: test
scope: unit
domain: docs
covers:
  - Conditional delivery lifecycle ownership
  - Specification boundary guidance
  - Separate frontend and backend evidence
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def normalized(path: str) -> str:
    return " ".join(read(path).split())


def test_planning_dispatch_owns_conditional_lifecycle() -> None:
    dispatch = normalized("docs/operating_system/planning/planning-dispatch.md")
    integration = read("docs/operating_system/tooling/frontend-backend-integration-tools.md")

    assert "## Delivery Lifecycle" in dispatch
    assert "Discovery or research when uncertainty exists" in dispatch
    assert "Prototype and iterate when UX or behavior needs validation" in dispatch
    assert "End-to-end verification applies only to cross-boundary journeys" in dispatch
    assert "Lifecycle ownership remains in `docs/operating_system/planning/planning-dispatch.md`." in integration
    assert "## Delivery Lifecycle" not in integration


def test_specification_templates_keep_boundary_guidance_applicable() -> None:
    draft = normalized("docs/operating_system/templates/draft-specification-template.md")
    detailed = normalized("docs/operating_system/templates/detailed-specification-template.md")

    assert "boundary implication when material" in draft
    assert "## Requirements and Behavioral Contract" in detailed
    assert "| Boundary | Owner or canonical contract | Required evidence |" in detailed
    assert "Include only applicable rows" in detailed


def test_review_and_evidence_language_stays_conditional() -> None:
    requesting = read(".agents/skills/skill-requesting-code-review/SKILL.md")
    reviewer = read(".agents/skills/skill-requesting-code-review/code-reviewer.md")
    verification = read(".agents/skills/skill-verification-before-completion/SKILL.md")

    assert "general-purpose" not in requesting
    assert "general-purpose" not in reviewer
    assert "low`, `normal`, `high`, or `xhigh`" in requesting
    assert "each applicable frontend, backend, and E2E evidence class" not in requesting
    assert "direct backend" in verification
