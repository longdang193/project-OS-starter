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
        "herdr -> codex pane -> lightrsi adapter :17667 -> 9router :20128 -> cgw :17841",
        "20129",
        "direct diagnostic compatibility cgw shim boundary",
        "never route `cgw/*` through native `codex exec`",
        "authenticated inference is reserved for an explicit installation acceptance or diagnostic operation",
        "one real, minimal model-producing request",
        "20128",
        "20129",
        "17841",
        "requested and observed model",
        "reasoning_effort",
        "chat mode",
        "local queue saturation",
        "600-second cgw request budget",
        "900-second herdr attempt budget",
        "1800-second outer watchdog",
        "does not authorize a late extension",
        "retired and its lifecycle evidence is reconciled",
    ):
        assert text in skill


def test_cgw_skill_keeps_scheduler_transport_and_installation_ownership_separate() -> None:
    skill = normalized_skill()
    for text in (
        "herdr owns scheduling and pane lifecycle",
        "9router owns transport and error classification",
        "persistent patch hub owns installation and rollback",
        "compatible_profile",
        "no_conflicting_live_process",
        "agent_status == done",
        "the shim queue is only a defensive boundary",
        "npm install -g 9router",
        "package version or git base is unknown",
    ):
        assert text in skill


def test_cgw_skill_requires_single_submission_after_reused_pane_verification() -> None:
    skill = normalized_skill()
    for text in (
        "reused codex panes perform ownership and profile verification only",
        "one canonical `agent prompt` submission path",
        "exactly one prompt",
        "no second submission",
        "post-dispatch retry",
        "profile fallback",
    ):
        assert text in skill


def test_cgw_skill_distinguishes_non_inference_preflight_from_delivery_inference() -> None:
    skill = normalized_skill()
    for text in (
        "check readiness without creating a second model request",
        "without dispatching a prompt",
        "must not authorize both a readiness inference and a delivery inference",
        "authenticated inference is reserved for an explicit installation acceptance or diagnostic operation",
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


def test_cgw_skill_requires_compact_review_packets() -> None:
    skill = normalized_skill()
    for text in (
        "keep the herdr task itself compact",
        "do not paste the current chat transcript",
        "codex_context_json",
        "413 payload too large",
        "rebuild the request instead of truncating or retrying it",
    ):
        assert text in skill
