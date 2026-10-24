from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
RUNNER = (
    ROOT
    / ".agents"
    / "skills"
    / "skill-github-browser-reviews"
    / "scripts"
    / "run-review-prompt-cli.mjs"
)


def test_review_runner_is_a_real_node_entrypoint() -> None:
    content = RUNNER.read_text(encoding="utf-8")

    assert content.startswith("#!/usr/bin/env node")
    assert "runReviewPromptInNewTab" in content
    assert "connectOverCDP" in content
    assert "launchPersistentContext" in content
    assert "--cdp-endpoint" in content
    assert "--user-data-dir" in content
    assert "--prompt-file" in content
    assert "--output-dir" in content
    assert "--expected-sha" not in content
    assert "promptSubmitted" in content
    assert "submission_attempted" in content
    assert "await mkdir(outputDir, { recursive: true })" in content
    assert "if (!context) {\n      throw new Error" in content
    assert "result.json" in content
    assert "response.md" in content


def test_review_runner_supports_a_non_submitting_probe_mode() -> None:
    content = RUNNER.read_text(encoding="utf-8")

    assert "--probe-only" in content
    assert "probeReviewModelInNewTab" in content
    assert "result.promptSubmitted !== false" in content


def test_review_runner_requires_a_supported_browser_attachment_mode() -> None:
    content = RUNNER.read_text(encoding="utf-8")

    assert "Missing one of: --cdp-endpoint or --user-data-dir" in content
    assert "Missing required argument: --model" in content
    assert "Missing required argument: --effort" in content
    assert "Missing required argument: --prompt-file" in content


def test_review_runner_reports_missing_endpoint_before_loading_browser_runtime() -> None:
    result = subprocess.run(
        [
            "node",
            str(RUNNER),
            "--model",
            "GPT-6",
            "--effort",
            "High",
            "--prompt-file",
            str(ROOT / "missing-review-prompt.txt"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Missing one of: --cdp-endpoint or --user-data-dir" in result.stderr


def test_probe_only_mode_does_not_require_prompt_file() -> None:
    result = subprocess.run(
        [
            "node",
            str(RUNNER),
            "--probe-only",
            "--model",
            "GPT-6",
            "--effort",
            "High",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Missing one of: --cdp-endpoint or --user-data-dir" in result.stderr
    assert "Missing required argument: --prompt-file" not in result.stderr


def test_review_runner_does_not_require_release_audit_arguments() -> None:
    content = RUNNER.read_text(encoding="utf-8")

    assert "--expected-sha" not in content
    assert "--expected-file-url" not in content
    assert "--expected-marker" not in content
    assert "acquireTransactionLock" not in content
    assert "GITHUB_REVIEW_" not in content


def test_review_runner_exposes_help_without_connecting_to_a_browser() -> None:
    result = subprocess.run(
        ["node", str(RUNNER), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--cdp-endpoint" in result.stdout
    assert "--user-data-dir" in result.stdout
