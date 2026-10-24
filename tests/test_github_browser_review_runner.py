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
    assert "--cdp-endpoint" in content
    assert "--prompt-file" in content
    assert "promptSubmitted" in content


def test_review_runner_supports_a_non_submitting_probe_mode() -> None:
    content = RUNNER.read_text(encoding="utf-8")

    assert "--probe-only" in content
    assert "probeReviewModelInNewTab" in content
    assert "options.probeOnly ? false : true" in content


def test_review_runner_fails_before_browser_use_for_missing_required_arguments() -> None:
    content = RUNNER.read_text(encoding="utf-8")

    assert "Missing required argument: --cdp-endpoint" in content
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
    assert "Missing required argument: --cdp-endpoint" in result.stderr


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
    assert "Missing required argument: --cdp-endpoint" in result.stderr
    assert "Missing required argument: --prompt-file" not in result.stderr


def test_review_runner_exposes_help_without_connecting_to_a_browser() -> None:
    result = subprocess.run(
        ["node", str(RUNNER), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--cdp-endpoint" in result.stdout
