from pathlib import Path

from project_os_test_paths import runtime_doc



def read_skill() -> str:
    return runtime_doc(".agents/skills/skill-cgw-runtime-operations/SKILL.md").read_text(
        encoding="utf-8"
    )


def normalized_skill() -> str:
    return " ".join(read_skill().split()).lower()


def test_cgw_skill_defines_transport_readiness_and_quota_invariants() -> None:
    skill = normalized_skill()
    for text in (
        "direct chat-to-cgw responses shim",
        "never route `cgw/*` through native `codex exec`",
        "authenticated inference probe",
        "20128",
        "20129",
        "17841",
        "requested and observed model",
        "reasoning_effort",
        "chat mode",
        "local queue saturation",
    ):
        assert text in skill


def test_cgw_skill_keeps_scheduler_transport_and_installation_ownership_separate() -> None:
    skill = normalized_skill()
    for text in (
        "herdr owns scheduling and pane lifecycle",
        "9router owns transport and error classification",
        "persistent patch hub owns installation and rollback",
        "reuse = idle && same_context && compatible_profile",
        "the shim queue is only a defensive boundary",
        "npm install -g 9router",
        "package version or git base is unknown",
    ):
        assert text in skill


def test_cgw_skill_requires_direct_evidence_and_existing_debugging_workflows() -> None:
    skill = normalized_skill()
    for text in (
        "skill-systematic-debugging",
        "skill-test-driven-development",
        "skill-backend-verification",
        "no-native-process evidence",
        "requested and observed model",
        "requested and observed `reasoning_effort`",
        "native quota is unchanged",
    ):
        assert text in skill
