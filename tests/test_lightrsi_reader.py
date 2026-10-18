import json
import subprocess
from pathlib import Path

import pytest

from scripts.project_os_runtime.lightrsi_reader import LightRSIResultReader


def completed_payload() -> dict[str, object]:
    return {
        "schema": "lightrsi.codex.completed-turn/v1",
        "state": "completed",
        "retryable": False,
        "sessionId": "native-session",
        "turnSeq": 4,
        "turnId": "native-session:t4",
        "requestId": "request-4",
        "responseId": "response-4",
        "content": "answer",
        "contentDigest": "a" * 64,
        "semanticComplete": True,
        "authority": "lightrsi",
    }


def test_reader_invokes_pinned_cli_and_returns_completed_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = tmp_path / "cli.js"
    cli.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        assert kwargs["timeout"] == 2.5
        return subprocess.CompletedProcess(command, 0, json.dumps(completed_payload()), "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = LightRSIResultReader(cli, timeout_seconds=2.5).read(
        session_id="native-session",
        after_cursor="cursor-1",
        request_id="request-4",
        turn_id="native-session:t4",
    )

    assert result["state"] == "completed"
    assert result["turnSeq"] == 4
    assert calls == [[
        "node",
        str(cli),
        "codex",
        "completed-turn",
        "--session",
        "native-session",
        "--after",
        "cursor-1",
        "--request",
        "request-4",
        "--turn",
        "native-session:t4",
        "--json",
    ]]


def test_reader_capability_check_validates_pinned_cli_schema_and_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = tmp_path / "cli.js"
    cli.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    digest = __import__("hashlib").sha256(cli.read_bytes()).hexdigest()
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({
                "schema": "lightrsi.codex.completed-turn/v1",
                "state": "pending",
                "retryable": True,
                "sessionId": "__project_os_capability__",
                "authority": "lightrsi",
                "reason": "no_candidate",
            }),
            "",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = LightRSIResultReader(cli).capability_check(expected_artifact_sha256=digest)

    assert result["state"] == "ready"
    assert result["artifact_sha256"] == digest
    assert calls[0][-1] == "--json"


def test_reader_returns_one_diagnostic_record_for_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = tmp_path / "cli.js"
    cli.write_text("#!/usr/bin/env node\n", encoding="utf-8")

    def fake_run(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(kwargs.get("args") or args[0], 1.0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = LightRSIResultReader(cli).read(session_id="native-session", after_cursor="cursor-1")

    assert result["state"] == "unavailable"
    assert result["reason"] == "reader_timeout"
    assert result["diagnostics"] == [{"kind": "reader_error", "reason": "reader_timeout"}]


def test_reader_rejects_malformed_or_wrong_session_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = tmp_path / "cli.js"
    cli.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    payload = completed_payload()
    payload["sessionId"] = "other-session"

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, json.dumps(payload), ""),
    )

    result = LightRSIResultReader(cli).read(session_id="native-session", after_cursor="cursor-1")

    assert result["state"] == "conflict"
    assert result["reason"] == "wrong_session"


def test_reader_rejects_non_json_process_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = tmp_path / "cli.js"
    cli.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "not json", ""),
    )

    result = LightRSIResultReader(cli).read(session_id="native-session", after_cursor="cursor-1")

    assert result["state"] == "unavailable"
    assert result["reason"] == "reader_malformed_output"
    assert len(result["diagnostics"]) == 1


def test_reader_accepts_pending_without_semantic_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = tmp_path / "cli.js"
    cli.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    payload = {
        "schema": "lightrsi.codex.completed-turn/v1",
        "state": "pending",
        "retryable": True,
        "sessionId": "native-session",
        "authority": "lightrsi",
        "reason": "no_candidate",
    }
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, json.dumps(payload), ""),
    )

    result = LightRSIResultReader(cli).read(session_id="native-session", after_cursor="cursor-1")

    assert result["state"] == "pending"
    assert "content" not in result


def test_reader_rejects_oversized_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = tmp_path / "cli.js"
    cli.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    oversized = json.dumps({**completed_payload(), "content": "x" * (64 * 1024)})
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, oversized, ""),
    )

    result = LightRSIResultReader(cli).read(session_id="native-session", after_cursor="cursor-1")

    assert result["state"] == "unavailable"
    assert result["reason"] == "reader_malformed_output"

