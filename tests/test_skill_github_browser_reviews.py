from pathlib import Path

from project_os_test_paths import runtime_doc


def read_skill() -> str:
    return runtime_doc(".agents/skills/skill-github-browser-reviews/SKILL.md").read_text(
        encoding="utf-8"
    )


def normalized_skill() -> str:
    return " ".join(read_skill().split()).lower()


def test_skill_defines_push_and_review_evidence() -> None:
    skill = normalized_skill()
    for text in (
        "commit and push",
        "normal chatgpt browser tab",
        "@github",
        "exact branch or commit",
        "exact file url",
        "read-only scope",
        "stable context identifier",
        "one review question",
        "known heading, hash, or other file marker",
        "findings ordered by severity",
    ):
        assert text in skill


def test_skill_defines_model_and_reasoning_selection() -> None:
    skill = normalized_skill()
    for text in (
        "gpt-5.6-sol",
        "gpt-6",
        "instant",
        "medium",
        "high",
        "model: <gpt-5.6-sol|gpt-6>",
        "reasoning: <instant|medium|high>",
    ):
        assert text in skill


def test_skill_rejects_local_only_and_legacy_runtime_review_paths() -> None:
    skill = read_skill()
    for text in (
        "Herdr",
        "CGW",
        "LightRSI",
        "9Router",
        "web-high",
        "web-medium",
        "web-normal",
        "Codex pane",
        "local Windows path as the only review source",
    ):
        if text == "local Windows path as the only review source":
            assert "Do not use a local Windows path as the only review source." in skill
        else:
            assert text not in skill


def test_skill_keeps_review_requests_compact_and_read_only() -> None:
    skill = normalized_skill()
    for text in (
        "keep the browser-tab request compact",
        "do not paste the current chat transcript",
        "do not modify files",
        "do not include credentials",
        "do not include unrelated repository contents",
    ):
        assert text in skill
