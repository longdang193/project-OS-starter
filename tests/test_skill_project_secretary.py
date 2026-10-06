from pathlib import Path

import yaml

from project_os_test_paths import runtime_doc


ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return runtime_doc(path).read_text(encoding="utf-8")


def test_project_secretary_is_optional_attention_surface() -> None:
    skill = read(".agents/skills/skill-project-secretary/SKILL.md")
    normalized = " ".join(skill.split()).casefold()

    assert "name: skill-project-secretary" in skill
    assert "use when a request needs attention" in normalized
    assert "optional attention-and-continuity layer" in normalized
    assert "when secretary is absent, existing execution-selection policy operates unchanged" in normalized
    assert "does not add a mandatory secretary-to-cos hop" in normalized
    assert "never accepts implementation" in normalized
    assert "explicit-turn" in normalized
    assert "events are hints" in normalized


def test_project_secretary_defines_right_sized_routing() -> None:
    skill = read(".agents/skills/skill-project-secretary/SKILL.md")
    normalized = " ".join(skill.split()).casefold()

    for text in (
        "question or status",
        "local reversible change",
        "one bounded executor",
        "ordinary plan/execution path",
        "sustained independent lanes",
        "unresolved follow-up",
        "cross-workstream conflict",
        "material intent or authority decision",
    ):
        assert text in normalized


def test_secretary_docket_requires_only_minimal_attention_fields() -> None:
    docket = yaml.safe_load(
        (ROOT / "docs/operating_system/templates/secretary-docket.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert docket == [
        {
            "id": "readme-followup",
            "objective": "Recheck README after runtime interface acceptance.",
            "waiting_on": {
                "ref": "docs/superpowers/plans/runtime-refactor.md",
                "outcome": "accepted-runtime-interface",
            },
        }
    ]
    assert set(docket[0]) == {"id", "objective", "waiting_on"}


def test_secretary_restart_and_authority_rules_are_explicit() -> None:
    skill = read(".agents/skills/skill-project-secretary/SKILL.md")
    normalized = " ".join(skill.split()).casefold()

    assert "reconstruct from canonical evidence first" in normalized
    assert "clear when discharged by its canonical source" in normalized
    assert "explicit user decision" in normalized
    assert "owning workflow evidence" in normalized
    assert "docket is not a plan" in normalized
    assert "sessions and notifications are not workflow truth" in normalized
