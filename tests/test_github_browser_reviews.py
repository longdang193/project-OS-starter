from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILL = ROOT / ".agents" / "skills" / "skill-github-browser-reviews" / "SKILL.md"
MODEL_SELECTION_HELPER = (
    ROOT
    / ".agents"
    / "skills"
    / "skill-github-browser-reviews"
    / "scripts"
    / "select-review-model.mjs"
)
REVIEW_PROMPT_HELPER = (
    ROOT
    / ".agents"
    / "skills"
    / "skill-github-browser-reviews"
    / "scripts"
    / "run-review-prompt.mjs"
)


REQUIRED_BROWSER_REVIEW_RULES = (
    "Use this skill only after the user explicitly invokes it by name",
    "Do not activate this skill merely because",
    "Explicit-invocation invariant",
    "normal ChatGPT browser tab",
    "with `@GitHub`",
    "Commit and push the selected plan or code",
    "the repository and exact branch or commit",
    "the file path or GitHub file URL",
    "Do not use a local Windows path as the only review source.",
    "confirm that it read the requested revision",
    "Return findings ordered by severity and do not modify files.",
)

REQUIRED_MODEL_SELECTION_RULES = (
    "GPT-5.6-Sol",
    "GPT-6",
    "instant",
    "medium",
    "high",
    "Model: <GPT-5.6-Sol|GPT-6>",
    "Reasoning: <instant|medium|high>",
)


FORBIDDEN_LEGACY_RUNTIME_TERMS = (
    "Herdr",
    "CGW",
    "LightRSI",
    "9Router",
    "Codex pane",
)


def test_skill_requires_browser_tab_github_review_workflow() -> None:
    content = CANONICAL_SKILL.read_text(encoding="utf-8")

    for rule in REQUIRED_BROWSER_REVIEW_RULES:
        assert rule in content


def test_skill_requires_explicit_user_invocation() -> None:
    content = CANONICAL_SKILL.read_text(encoding="utf-8")

    assert "Use this skill only after the user explicitly invokes it by name" in content
    assert "Do not activate this skill merely because" in content
    assert "Explicit-invocation invariant" in content


def test_skill_allows_model_and_reasoning_selection() -> None:
    content = CANONICAL_SKILL.read_text(encoding="utf-8")

    for rule in REQUIRED_MODEL_SELECTION_RULES:
        assert rule in content


def test_skill_has_bounded_playwright_model_selection_helper() -> None:
    skill = CANONICAL_SKILL.read_text(encoding="utf-8")
    helper = MODEL_SELECTION_HELPER.read_text(encoding="utf-8")

    assert "scripts/select-review-model.mjs" in skill
    assert "selectReviewModel(page" in skill
    assert 'getByRole("button", { name: "Select ChatGPT model" })' in helper
    assert '[role="menuitemradio"]' in helper
    assert 'getByRole("menuitem", { name: "Power", exact: true })' in helper
    assert 'ArrowLeft' in helper
    assert 'ArrowRight' in helper
    assert "never launches a browser" in helper
    assert "retries indefinitely" in helper


def test_skill_has_bounded_end_to_end_prompt_helper() -> None:
    skill = CANONICAL_SKILL.read_text(encoding="utf-8")
    helper = REVIEW_PROMPT_HELPER.read_text(encoding="utf-8")

    assert "scripts/run-review-prompt.mjs" in skill
    assert "runReviewPrompt(page" in helper
    assert "openReviewTab(context)" in helper
    assert "runReviewPromptInNewTab(context, options)" in helper
    assert 'page.goto(CHATGPT_URL)' in helper
    assert 'getByRole("textbox", { name: "Ask ChatGPT" })' in helper
    assert "promptSubmitted: true" in helper
    assert "never launches a browser" in helper
    assert "retries" in helper


def test_skill_documents_file_backed_helper_execution_boundary() -> None:
    skill = CANONICAL_SKILL.read_text(encoding="utf-8")

    for rule in (
        "Node/Playwright runner",
        "ChatGPT page",
        "Do not import them from `page.evaluate`",
        "file-backed entry point",
        "filename",
        "sourcePath",
        "Prompt submission remains gated",
    ):
        assert rule in skill


def test_skill_removes_legacy_runtime_routing() -> None:
    content = CANONICAL_SKILL.read_text(encoding="utf-8")

    for term in FORBIDDEN_LEGACY_RUNTIME_TERMS:
        assert term not in content


def test_generated_skill_surfaces_match_canonical_browser_workflow() -> None:
    canonical = CANONICAL_SKILL.read_text(encoding="utf-8")
    canonical_body = canonical.split("---\n", 2)[2].lstrip("\n")

    for platform in ("codex", "claude", "antigravity"):
        generated = (
            ROOT
            / "generated_agents"
            / platform
            / "skills"
            / "skill-github-browser-reviews"
            / "SKILL.md"
        )
        generated_content = generated.read_text(encoding="utf-8")
        assert "normal ChatGPT browser tab" in generated_content
        assert "with `@GitHub`" in generated_content
        for rule in REQUIRED_MODEL_SELECTION_RULES:
            assert rule in generated_content
        for term in FORBIDDEN_LEGACY_RUNTIME_TERMS:
            assert term not in generated_content
        assert generated_content.endswith(canonical_body)
