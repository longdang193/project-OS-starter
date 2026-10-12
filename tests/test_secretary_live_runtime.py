from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

import pytest

from scripts.secretary_live_runtime import (
    SECRETARY_PROVIDER,
    SecretaryNormalRequest,
    SecretaryLaunchRequest,
    _safe_runtime_snapshot,
    _build_codex_runtime_snapshot,
    _extract_codex_semantic_content,
    _normalize_invocation_outcome,
    _observe_submitted_codex,
    _observe_provider_telemetry,
    _redact_semantic_content,
    _release_codex_agent,
    _smoke_receipt,
    build_launcher_command,
    build_normal_launcher_command,
    run_normal,
    run_probe,
    run_smoke,
    sanitize_launcher_result,
    select_launcher_payload,
)


def request(**overrides: object) -> SecretaryLaunchRequest:
    values: dict[str, object] = {
        "task_id": "task-1",
        "plan_revision": "plan-rev-1",
        "attempt_id": "attempt-1",
        "run_id": "run-1",
        "repository_identity": "repo/example",
        "plan_identity": "plan/example",
        "git_revision": "581844d",
        "worktree": Path("C:/worktree"),
        "expected_base": "581844d",
        "task": "Read-only Secretary attention probe.",
        "codex_home": Path("C:/Users/example/.codex"),
    }
    values.update(overrides)
    return SecretaryLaunchRequest(**values)


def normal_request(**overrides: object) -> SecretaryNormalRequest:
    values: dict[str, object] = {
        "worktree": Path("C:/worktree"),
        "task": "Read-only Secretary attention request.",
        "codex_home": Path("C:/Users/example/.codex"),
    }
    values.update(overrides)
    return SecretaryNormalRequest(**values)


def test_normal_request_and_command_do_not_synthesize_governance_identity() -> None:
    command = build_normal_launcher_command(normal_request(), expected_base="head-1")

    assert "--expected-base" in command
    assert command[command.index("--expected-base") + 1] == "head-1"
    assert "--task" in command
    assert "Secretary normal-mode boundary" in command[command.index("--task") + 1]
    assert "--secretary-task-id" not in command
    assert "--secretary-plan-revision" not in command
    assert "--secretary-attempt-id" not in command
    assert "--secretary-run-id" not in command
    assert "--repository-identity" not in command
    assert "--plan-identity" not in command


def test_normal_outcome_requires_correlated_result_reference() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "execution": {"state": "completed"},
                "cleanup": {"state": "removed"},
                "task_result": {"state": "reported_completed"},
            }
        },
        observation={"state": "idle", "output_sha256": "a" * 64},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["execution"]["state"] == "completed"
    assert result["result"]["state"] == "unavailable"
    assert result["resource"]["state"] == "settled"


def test_normal_outcome_reports_failed_result_even_when_execution_failed() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=7,
        payload={
            "assignment": {
                "execution": {"state": "failed", "worker_exit_code": 7},
                "cleanup": {"state": "removed"},
                "task_result": {
                    "state": "reported_failed",
                    "attempt_id": "attempt-1",
                    "result_reference": "task-result://invoke-1",
                    "content": "failure details",
                },
            }
        },
        observation={"state": "failed"},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["execution"]["state"] == "failed"
    assert result["result"] == {
        "state": "reported",
        "status": "failed",
        "reference": "task-result://invoke-1",
        "content": "failure details",
    }


def test_normal_outcome_preserves_reported_result_when_cleanup_is_quarantined() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "execution": {"state": "completed"},
                "cleanup": {"state": "unknown"},
                "task_result": {
                    "state": "reported_completed",
                    "result_reference": "herdr://session/agent/12",
                    "content": "completed response",
                },
            }
        },
        observation={"state": "idle", "cleanup": {"state": "unknown"}},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"]["state"] == "reported"
    assert result["resource"]["state"] == "quarantined"
    assert result["resource"]["reuse_blocked"] is True


def test_normal_outcome_prefers_verified_observation_cleanup() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "execution": {"state": "completed"},
                "cleanup": {"state": "unknown"},
                "task_result": {"state": "unknown"},
            }
        },
        observation={"state": "done", "cleanup": {"state": "removed"}},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["resource"] == {"state": "settled", "reuse_blocked": False}
    assert result["observability"]["cleanup_state"] == "removed"


@pytest.mark.parametrize(
    ("evidence", "expected_state", "expected_evidence_state"),
    [
        ([{"state": "unknown"}, {"state": "removed", "verified": True}], "settled", "removed"),
        ([{"state": "unknown"}, {"state": "present"}], "quarantined", "present"),
        ([{"state": "present"}, {"state": "removed", "verified": True}], "settled", "removed"),
        ([{"state": "removed", "verified": True}, {"state": "removed", "verified": True}], "settled", "removed"),
        ([{"state": "removed", "verified": True}, {"state": "present"}], "quarantined", "conflict"),
        ([{"state": "unknown"}, {"state": "unavailable"}], "quarantined", "unknown"),
    ],
)
def test_resource_evidence_reduction_is_monotonic(
    evidence: list[dict[str, object]],
    expected_state: str,
    expected_evidence_state: str,
) -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._reduce_resource_evidence(*evidence)

    assert result["state"] == expected_state
    assert result["evidence_state"] == expected_evidence_state


def test_run_smoke_is_strict_probe_alias() -> None:
    import scripts.secretary_live_runtime as runtime

    assert runtime.run_smoke is runtime.run_probe


def test_run_normal_does_not_observe_provider_telemetry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "herdr.exe")
    monkeypatch.setattr(
        runtime,
        "_prepare_herdr_target",
        lambda request_value, **kwargs: (request_value, {"selector_mode": "test"}, None),
    )
    monkeypatch.setattr(
        runtime.subprocess,
        "run",
        lambda *args, **kwargs: type(
            "Result",
            (),
            {"returncode": 0, "stdout": '{"assignment":{"execution":{"state":"completed"}}}', "stderr": ""},
        )(),
    )
    monkeypatch.setattr(
        runtime,
        "_observe_submitted_codex",
        lambda *args, **kwargs: {
            "state": "idle",
            "cleanup": {"state": "removed"},
        },
    )
    monkeypatch.setattr(
        runtime,
        "_observe_provider_telemetry",
        lambda *args, **kwargs: pytest.fail("normal run must not query provider telemetry"),
    )

    result = run_normal(normal_request(worktree=tmp_path), output=tmp_path / "normal.json")

    assert result["result"]["state"] == "unavailable"
    assert "provider_telemetry" not in result


def test_normal_outcome_accepts_distinct_assignment_and_attempt_ids() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
                "task_result": {
                    "state": "reported_completed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "content": "answer",
                },
            }
        },
        observation={},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "reported", "status": "completed", "content": "answer"}


def test_normal_outcome_marks_same_field_identity_conflict_ambiguous() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "attempt_id": "attempt-assignment",
                "execution": {"state": "completed"},
                "task_result": {
                    "state": "reported_completed",
                    "attempt_id": "attempt-result",
                    "content": "answer",
                },
            }
        },
        observation={},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "ambiguous", "status": None}


def test_normal_outcome_preserves_long_semantic_content() -> None:
    import scripts.secretary_live_runtime as runtime

    content = "x" * 5000
    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "execution": {"state": "completed"},
                "task_result": {"state": "reported_completed", "content": content},
            }
        },
        observation={},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "reported", "status": "completed", "content": content}


def structured_runtime(request_value: SecretaryLaunchRequest, *, session_id: str, model: str) -> dict[str, object]:
    binding = {
        "pair_id": request_value.run_id,
        "arm": "candidate",
        "run_id": request_value.run_id,
        "attempt_id": request_value.attempt_id,
        "task_id": request_value.task_id,
        "plan_revision": request_value.plan_revision,
        "repository_identity": request_value.repository_identity,
        "plan_identity": request_value.plan_identity,
        "git_revision": request_value.git_revision,
        "worktree": str(request_value.worktree.resolve()),
        "workstream": "secretary-live-runtime",
        "checkpoint": f"{request_value.plan_revision}:{request_value.task_id}",
        "provider": SECRETARY_PROVIDER,
        "model": model,
        "controller_id": "cos-supervised",
        "session_id": session_id,
    }
    producers = {
        "launch": "herdr_main_launcher",
        "secretary": "secretary_live_runtime",
        "task_result": "dcode-project",
        "settlement": "project_os_runtime.attempt",
        "acceptance": "cos",
    }
    sources = {
        name: {"producer": producer, "source_ref": f"runtime://{name}/{request_value.run_id}", "source_digest": "a" * 64, **binding}
        for name, producer in producers.items()
    }
    return {
        **binding,
        "observed": True,
        "timestamps": {
            "run_started": "2026-10-10T10:00:00+00:00",
            "cos_entry": "2026-10-10T10:00:01+00:00",
            "secretary_entry": "2026-10-10T10:00:02+00:00",
            "worker_entry": "2026-10-10T10:00:03+00:00",
            "publication": "2026-10-10T10:00:40+00:00",
            "settlement": "2026-10-10T10:00:50+00:00",
            "acceptance": "2026-10-10T10:01:00+00:00",
            "secretary_exit": "2026-10-10T10:01:05+00:00",
            "cos_exit": "2026-10-10T10:01:08+00:00",
            "run_finished": "2026-10-10T10:01:10+00:00",
        },
        "metrics": {
            "cos_turns": 0,
            "secretary_turns": 1,
            "human_interventions": 0,
            "publication_success": True,
            "settlement_proven": True,
            "acceptance_decision": "PASS",
            "token_usage": "unknown",
            "cost": "unknown",
        },
        "sources": sources,
    }


def test_launch_request_requires_secretary_provider() -> None:
    with pytest.raises(ValueError, match="9router"):
        request(provider="other-provider")


def test_launcher_command_binds_ids_and_configured_codex_home() -> None:
    command = build_launcher_command(request())

    assert "--executor" in command
    assert command[command.index("--executor") + 1] == "codex"
    assert "--codex-home" in command
    assert command[command.index("--codex-home") + 1] == str(Path("C:/Users/example/.codex"))
    task = command[command.index("--task") + 1]
    for value in ("task-1", "plan-rev-1", "attempt-1", "run-1"):
        assert value in task
    for option, value in (
        ("--secretary-task-id", "task-1"),
        ("--secretary-plan-revision", "plan-rev-1"),
        ("--secretary-attempt-id", "attempt-1"),
        ("--secretary-run-id", "run-1"),
    ):
        assert command[command.index(option) + 1] == value
    assert "--assignment-id" not in command


def test_observe_submitted_codex_waits_for_idle_and_releases_owned_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter([
        {"state": "working", "output_chars": 10, "observation_error": None},
        {"state": "idle", "output_chars": 20, "observation_error": None},
    ])
    calls: list[tuple[str, str, str]] = []

    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: calls.append(args[:3]) or {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="live-session", pane="w1:p1"),
        {
            "herdr": {
                "executable": "herdr.exe",
                "session": "live-session",
                "pane": "w1:p1",
                "agent_name": "normal-main-1234",
            }
        },
        env={},
    )

    assert observation["state"] == "idle"
    assert observation["cleanup"] == {"state": "removed"}
    assert calls == [("herdr.exe", "live-session", "normal-main-1234")]


def test_observe_submitted_codex_retries_terminal_state_after_read_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter([
        {
            "state": "idle",
            "state_change_seq": 1,
            "output_chars": 20,
            "observation_error": "agent read transport timeout",
        },
        {"state": "idle", "state_change_seq": 2, "output_chars": 30, "observation_error": None},
    ])
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        {
            "herdr": {
                "executable": "herdr.exe",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
            }
        },
        env={},
    )

    assert observation["state"] == "idle"
    assert "result_reference" not in observation
    assert observation["cleanup"] == {"state": "removed"}


def test_observe_submitted_codex_rejects_recovered_stale_output_without_state_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter([
        {
            "state": "idle",
            "state_change_seq": 1,
            "content": None,
            "output_sha256": "a" * 64,
            "output_chars": 0,
            "observation_error": "agent read transport timeout",
        },
        {
            "state": "idle",
            "state_change_seq": 1,
            "content": "Previous invocation\n• stale answer",
            "output_sha256": "b" * 64,
            "output_chars": 32,
            "observation_error": None,
        },
        {
            "state": "failed",
            "state_change_seq": 2,
            "content": "Previous invocation\n• stale answer",
            "output_sha256": "b" * 64,
            "output_chars": 32,
            "observation_error": None,
        },
    ])
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        {"herdr": {"executable": "herdr.exe", "session": "session", "pane": "pane", "agent_name": "agent"}},
        env={},
    )

    assert observation["state"] == "failed"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_rejects_unknown_recovery_as_activity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter([
        {
            "state": "unknown",
            "state_change_seq": 1,
            "content": None,
            "output_sha256": "a" * 64,
            "output_chars": 0,
            "observation_error": "completion observation deadline expired",
        },
        {
            "state": "idle",
            "state_change_seq": 2,
            "content": "Previous invocation\n• stale answer",
            "output_sha256": "b" * 64,
            "output_chars": 32,
            "observation_error": None,
        },
    ])
    clock = iter([0.0, 0.0, 0.0, 0.0, 0.0, 2.0])
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS",
        1.0,
    )
    monkeypatch.setattr("scripts.secretary_live_runtime.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("scripts.secretary_live_runtime.time.sleep", lambda _: None)

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        {"herdr": {"executable": "herdr.exe", "session": "session", "pane": "pane", "agent_name": "agent"}},
        env={},
    )

    assert observation["state"] == "idle"
    assert observation["observation_error"] == "completion output not observed"
    assert "semantic_content" not in observation


def test_normal_outcome_uses_consistent_cleanup_evidence() -> None:
    payload = {
        "herdr": {"session": "session", "pane": "pane", "agent_name": "agent"},
        "assignment": {
            "execution": {"state": "completed"},
            "cleanup": {"state": "preserved"},
            "task_result": {"state": "reported_completed", "content": "answer"},
        },
    }
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload=payload,
        observation={"state": "done", "cleanup": {"state": "removed"}},
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["resource"] == {"state": "settled", "reuse_blocked": False}
    assert result["owned_resources"]
    assert all(item["state"] == "settled" for item in result["owned_resources"])


def test_observe_submitted_codex_waits_past_initial_idle_until_done(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter([
        {
            "state": "idle",
            "state_change_seq": 1,
            "content": "Codex prompt screen",
            "output_sha256": "a" * 64,
            "output_chars": 18,
            "observation_error": None,
        },
        {
            "state": "done",
            "state_change_seq": 2,
            "content": "Codex screen\n• SECRETARY_PROBE_test\n› Ask Codex to do anything",
            "output_sha256": "b" * 64,
            "output_chars": 65,
            "observation_error": None,
        },
    ])
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        {
            "herdr": {
                "executable": "herdr.exe",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
            }
        },
        env={},
    )

    assert observation["state"] == "done"
    assert observation["semantic_content"] == "SECRETARY_PROBE_test"
    assert observation["cleanup"] == {"state": "removed"}


def test_observe_submitted_codex_does_not_capture_unconfirmed_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter([
        {
            "state": "stopped",
            "state_change_seq": 2,
            "content": "Codex screen\n• partial answer",
            "output_sha256": "b" * 64,
            "output_chars": 30,
            "observation_error": None,
        },
    ])
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "not_attempted"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        {"herdr": {"executable": "herdr.exe", "session": "session", "pane": "pane", "agent_name": "agent"}},
        env={},
    )

    assert observation["state"] == "stopped"
    assert "semantic_content" not in observation


def _submission_anchor() -> dict[str, object]:
    return {
        "state": "idle",
        "state_change_seq": 1,
        "content": "Codex prompt screen",
        "output_sha256": "a" * 64,
        "output_chars": 18,
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
    }


def _correlated_payload() -> dict[str, object]:
    return {
        "herdr": {
            "executable": "herdr.exe",
            "session": "session",
            "pane": "pane",
            "agent_name": "agent",
            "ownership": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
            },
        },
        "assignment": {
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
        },
    }


def test_observe_submitted_codex_accepts_fast_idle_answer_on_first_poll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "idle",
            "state_change_seq": 2,
            "content": "Codex screen\n• SECRETARY_PROBE_fast\n› Ask Codex to do anything",
            "output_sha256": "b" * 64,
            "output_chars": 66,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit=_submission_anchor(),
        env={},
    )

    assert observation["state"] == "idle"
    assert observation["semantic_content"] == "SECRETARY_PROBE_fast"


def test_observe_submitted_codex_rejects_stale_idle_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit=_submission_anchor(),
        env={},
    )

    assert observation["state"] == "idle"
    assert observation["observation_error"] == "submission freshness not proven"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_rejects_read_error_recovery_with_old_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    snapshot_values = [
        {**_submission_anchor(), "observation_error": "agent read transport timeout"},
        {**_submission_anchor(), "observation_error": None},
    ]
    snapshots = iter(snapshot_values)
    last_snapshot = snapshot_values[-1]

    def next_snapshot(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal last_snapshot
        try:
            last_snapshot = next(snapshots)
        except StopIteration:
            pass
        return last_snapshot

    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        next_snapshot,
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit=_submission_anchor(),
        env={},
    )

    assert observation["state"] == "idle"
    assert observation["observation_error"] == "submission freshness not proven"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_accepts_fresh_post_submit_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "done",
            "state_change_seq": 2,
            "content": "Codex screen\n• fresh answer\n› Ask Codex to do anything",
            "output_sha256": "b" * 64,
            "output_chars": 55,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit=_submission_anchor(),
        env={},
    )

    assert observation["state"] == "done"
    assert observation["semantic_content"] == "fresh answer"


def test_observe_submitted_codex_rejects_partial_or_stopped_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "stopped",
            "state_change_seq": 2,
            "content": "Codex screen\n• partial answer",
            "output_sha256": "b" * 64,
            "output_chars": 30,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit=_submission_anchor(),
        env={},
    )

    assert observation["state"] == "stopped"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_rejects_mismatched_attempt_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "done",
            "state_change_seq": 2,
            "attempt_id": "attempt-other",
            "content": "Codex screen\n• unrelated answer\n› Ask Codex to do anything",
            "output_sha256": "b" * 64,
            "output_chars": 61,
            "observation_error": None,
        },
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit=_submission_anchor(),
        env={},
    )

    assert observation["state"] == "unknown"
    assert observation["observation_error"] == "completion identity mismatch"
    assert "semantic_content" not in observation


def test_extract_codex_semantic_content_selects_latest_answer() -> None:
    assert _extract_codex_semantic_content(
        "• I will inspect the code first.\nWorked for 9s\n• FAIL: tests failed.\n› Ask Codex to do anything"
    ) == "FAIL: tests failed."


def test_extract_codex_semantic_content_accepts_prompt_before_answer() -> None:
    assert _extract_codex_semantic_content(
        "› Return exactly PROBE_OK.\n• PROBE_OK\nWorked for 1s\n› Ask Codex to do anything"
    ) == "PROBE_OK"


def test_extract_codex_semantic_content_ignores_prompt_echo_after_completion_marker() -> None:
    assert _extract_codex_semantic_content(
        "› Original request\n"
        "• OLD ANSWER\n"
        "Worked for 1s\n"
        "› Please echo this input:\n"
        "Worked for 2s\n"
        "• USER PROMPT TEXT\n"
        "› Ask Codex to do anything"
    ) == "OLD ANSWER"


def test_extract_codex_semantic_content_ignores_initial_prompt_echo_bullet() -> None:
    assert _extract_codex_semantic_content(
        "› Please echo this input:\n• USER PROMPT TEXT\n› Ask Codex to do anything"
    ) is None


@pytest.mark.parametrize(
    "text",
    [
        "Never put passwords in source code.",
        "Authorization headers should be redacted.",
    ],
)
def test_semantic_redaction_preserves_security_explanations(text: str) -> None:
    assert _redact_semantic_content(text) == text


def test_semantic_redaction_removes_values_and_is_idempotent() -> None:
    text = (
        "Bearer abc.def-123 https://example.test/?token=query-secret "
        "configured=fixture-secret"
    )

    redacted = _redact_semantic_content(text, ("fixture-secret",))

    assert "abc.def-123" not in redacted
    assert "query-secret" not in redacted
    assert "fixture-secret" not in redacted
    assert _redact_semantic_content(redacted, ("fixture-secret",)) == redacted


def test_semantic_redaction_removes_query_secret_with_apostrophe_suffix() -> None:
    assert _redact_semantic_content(
        "https://example.test/?token=PREFIX'SUFFIX"
    ) == "https://example.test/?token=[REDACTED]"


def test_release_codex_agent_interrupts_process_and_verifies_removal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return type(
            "Result",
            (),
            {
                "returncode": 0 if len(calls) == 1 else 1,
                "stdout": "" if len(calls) == 1 else '{"error":{"code":"agent_not_found"}}',
                "stderr": "",
            },
        )()

    monkeypatch.setattr("scripts.secretary_live_runtime._herdr_run", fake_run)

    from scripts.secretary_live_runtime import _release_codex_agent

    assert _release_codex_agent(
        "herdr.exe",
        "live-session",
        "normal-main-1234",
        "w1:p1",
        env={},
    ) == {"state": "removed"}
    assert calls == [
        [
            "herdr.exe", "--session", "live-session", "agent", "send-keys",
            "normal-main-1234", "ctrl+c",
        ],
        ["herdr.exe", "--session", "live-session", "agent", "get", "normal-main-1234"],
    ]


def test_release_codex_agent_does_not_treat_transport_failure_as_removal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if len(calls) == 1:
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        return type(
            "Result",
            (),
            {
                "returncode": 1,
                "stdout": '{"error":{"code":"server_not_running"}}',
                "stderr": "",
            },
        )()

    monkeypatch.setattr("scripts.secretary_live_runtime._herdr_run", fake_run)

    assert _release_codex_agent(
        "herdr.exe",
        "live-session",
        "normal-main-1234",
        "w1:p1",
        env={},
    )["state"] == "unknown"


def test_release_codex_agent_never_raises_for_null_retirement_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        return None

    monkeypatch.setattr("scripts.secretary_live_runtime._herdr_run", fake_run)

    result = _release_codex_agent("herdr", "session", "agent", "pane", env={})

    assert result["state"] == "unknown"
    assert calls == 2


@pytest.mark.parametrize("response", [None, subprocess.CompletedProcess([], 0, "null", "")])
def test_close_workspace_never_raises_for_null_transport_response(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_herdr_run", lambda *args, **kwargs: response)

    result = runtime._close_herdr_workspace("herdr", "workspace-1", env={})

    assert result["verified"] is False


def test_run_probe_preserves_workspace_identity_when_acquisition_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    request_value = request(worktree=tmp_path)
    monkeypatch.setattr(runtime, "_configured_provider", lambda _: SECRETARY_PROVIDER)
    monkeypatch.setattr(runtime, "_configured_model", lambda _: "gpt-test")
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "herdr.exe")

    error = runtime.LaunchBlocked("pane bootstrap failed")
    error.workspace_id = "workspace-1"
    error.workspace_close = {"state": "unknown", "verified": False}

    def fail_prepare(*args, **kwargs):
        raise error

    monkeypatch.setattr(runtime, "_prepare_herdr_target", fail_prepare)
    monkeypatch.setattr(
        runtime,
        "_close_herdr_workspace",
        lambda *args, **kwargs: {"state": "closed", "verified": True},
    )
    monkeypatch.setattr(
        runtime,
        "_observe_provider_telemetry",
        lambda *args, **kwargs: {"disposition": "unavailable"},
    )

    result = runtime.run_probe(request_value, output=tmp_path / "probe.json")

    assert result["disposition"] == "BLOCKED_CAPABILITY"
    assert result["preflight"]["workspace_close"]["verified"] is True
    assert result["owned_resources"][0]["identity"] == "workspace-1"


def test_release_codex_agent_treats_already_retired_agent_as_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if "send-keys" in command:
            return type("Result", (), {"returncode": 1, "stdout": "", "stderr": ""})()
        return type(
            "Result",
            (),
            {"returncode": 1, "stdout": '{"error":{"code":"agent_not_found"}}', "stderr": ""},
        )()

    monkeypatch.setattr("scripts.secretary_live_runtime._herdr_run", fake_run)

    result = _release_codex_agent("herdr", "session", "agent", "pane", env={})

    assert result == {"state": "removed"}
    assert len(calls) == 2


def test_release_codex_agent_checks_for_delayed_retirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    clock = iter([0.0, 0.0, 6.0, 6.0, 9.0])

    def fake_run(command, **kwargs):
        calls.append(command)
        if "send-keys" in command:
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        if len(calls) in {2, 3}:
            return type("Result", (), {"returncode": 0, "stdout": "{}", "stderr": ""})()
        return type(
            "Result",
            (),
            {"returncode": 1, "stdout": '{"error":{"code":"agent_not_found"}}', "stderr": ""},
        )()

    monkeypatch.setattr("scripts.secretary_live_runtime._herdr_run", fake_run)
    monkeypatch.setattr("scripts.secretary_live_runtime.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("scripts.secretary_live_runtime.time.sleep", lambda _: None)

    result = _release_codex_agent("herdr", "session", "agent", "pane", env={})

    assert result == {"state": "removed"}
    assert len(calls) == 4


def test_run_smoke_preserves_ready_result_without_post_submit_downgrade(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request_value = request()
    closed: list[tuple[str, str]] = []
    events: list[str] = []
    monkeypatch.setattr("scripts.secretary_live_runtime._configured_provider", lambda _: "9router")
    monkeypatch.setattr("scripts.secretary_live_runtime._configured_model", lambda _: "gpt-test")
    monkeypatch.setattr("scripts.secretary_live_runtime.shutil.which", lambda _: "herdr.exe")
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._prepare_herdr_target",
        lambda request_value, **kwargs: (request_value, {"selector_mode": "test"}, "w99"),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._close_herdr_workspace",
        lambda herdr, workspace_id, **kwargs: events.append("workspace_close") or closed.append((herdr, workspace_id)) or {"state": "closed", "verified": True},
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime.subprocess.run",
        lambda *args, **kwargs: type(
            "Result",
            (),
            {"returncode": 0, "stdout": '{"herdr":{"session":"live-session"}}', "stderr": ""},
        )(),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime.sanitize_launcher_result",
        lambda *args, **kwargs: {"disposition": "READY", "evidence_provenance": "live-attributed"},
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._observe_submitted_codex",
        lambda *args, **kwargs: pytest.fail("validated READY result must not be re-probed"),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._observe_provider_telemetry",
        lambda *args, **kwargs: events.append("provider_observation") or {"disposition": "inconclusive"},
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._smoke_receipt",
        lambda *args, **kwargs: {"disposition": "READY"},
    )

    result = run_smoke(request_value, output=tmp_path / "smoke.json")

    assert result["disposition"] == "READY"
    assert result["evidence_provenance"] == "live-attributed"
    assert result["preflight"] == {"selector_mode": "test", "workspace_close": {"state": "closed", "verified": True}}
    assert closed == [("herdr.exe", "w99")]
    assert events == ["workspace_close", "provider_observation"]


def test_run_normal_settles_resource_when_owned_workspace_closes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    request_value = normal_request(worktree=tmp_path)
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "herdr.exe")
    monkeypatch.setattr(
        runtime,
        "_prepare_herdr_target",
        lambda request_value, **kwargs: (request_value, {"selector_mode": "test"}, "w99"),
    )
    monkeypatch.setattr(
        runtime.subprocess,
        "run",
        lambda *args, **kwargs: type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps(
                    {
                        "herdr": {
                            "session": "default",
                            "pane": "w99:p1",
                            "agent_name": "normal-main-1234",
                        },
                        "assignment": {
                            "execution": {"state": "completed"},
                            "task_result": {
                                "state": "reported_completed",
                                "result_reference": "herdr://default/normal-main-1234/1",
                                "content": "normal response",
                            },
                        },
                    }
                ),
                "stderr": "",
            },
        )(),
    )
    monkeypatch.setattr(
        runtime,
        "_observe_submitted_codex",
        lambda *args, **kwargs: {"state": "idle", "cleanup": {"state": "removed"}},
    )
    monkeypatch.setattr(
        runtime,
        "_close_herdr_workspace",
        lambda *args, **kwargs: {"state": "closed", "verified": True},
    )

    result = runtime.run_normal(request_value, output=tmp_path / "normal.json")

    assert result["result"]["state"] == "reported"
    assert result["resource"] == {"state": "settled", "reuse_blocked": False}


def test_close_workspace_requires_structured_retirement_proof(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "_herdr_run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, '{"result":{"workspace_id":"w1","state":"closed"}}', ""
        ),
    )
    assert runtime._close_herdr_workspace("herdr", "w1", env={}) == {
        "state": "closed",
        "verified": True,
        "authority": "herdr.workspace.close",
    }

    monkeypatch.setattr(
        runtime,
        "_herdr_run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )
    assert runtime._close_herdr_workspace("herdr", "w1", env={}) == {
        "state": "closed",
        "verified": False,
        "reason": "workspace_still_present",
    }


def test_run_normal_exception_preserves_owned_resource_after_verified_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "herdr.exe")
    monkeypatch.setattr(
        runtime,
        "_prepare_herdr_target",
        lambda request_value, **kwargs: (
            request_value,
            {"selector_mode": "test"},
            "workspace-1",
        ),
    )
    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(runtime, "_close_herdr_workspace", lambda *args, **kwargs: {"state": "closed", "verified": True})

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=tmp_path / "normal.json")

    assert result["execution"]["state"] == "failed"
    assert result["result"] == {"state": "unavailable", "status": None}
    assert result["resource"] == {"state": "settled", "reuse_blocked": False}
    assert result["recovery_required"] is False
    assert result["owned_resources"][0]["identity"] == "workspace-1"


def test_normal_outcome_reports_captured_observation_content() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "execution": {"state": "completed"},
                "task_result": {"state": "unknown"},
            }
        },
        observation={
            "state": "done",
            "semantic_content": "SECRETARY_PROBE_test",
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "content": "SECRETARY_PROBE_test",
    }


def test_normal_outcome_scopes_launcher_observation_error_without_downgrading_result() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "execution": {
                    "state": "completed",
                    "observation_error": "not_observed",
                },
                "task_result": {"state": "unknown"},
            }
        },
        observation={
            "state": "done",
            "semantic_content": "SECRETARY_PROBE_test",
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "content": "SECRETARY_PROBE_test",
    }
    assert result["execution"]["observation_error"] == "not_observed"
    assert result["execution"]["observation_error_scope"] == "launcher"
    assert result["observability"]["launcher_observation_error"] == "not_observed"
    assert result["observability"]["observation_error"] is None


@pytest.mark.parametrize(
    ("state", "observation_error"),
    [("working", None), ("stopped", None), ("idle", "completion output not observed")],
)
def test_normal_outcome_rejects_unconfirmed_observation_content(
    state: str,
    observation_error: str | None,
) -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={"assignment": {"execution": {"state": "completed"}, "task_result": {"state": "unknown"}}},
        observation={
            "state": state,
            "observation_error": observation_error,
            "semantic_content": "partial answer",
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_does_not_report_terminal_screen_as_semantic_content() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={"assignment": {"execution": {"state": "completed"}, "task_result": {"state": "unknown"}}},
        observation={
            "state": "done",
            "content": ">_ OpenAI Codex\n› Return exactly SECRETARY_PROBE_test",
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_run_normal_exception_quarantines_when_cleanup_is_unproven(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "herdr.exe")
    monkeypatch.setattr(
        runtime,
        "_prepare_herdr_target",
        lambda request_value, **kwargs: (request_value, {"selector_mode": "test"}, "workspace-1"),
    )
    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(runtime, "_close_herdr_workspace", lambda *args, **kwargs: {"state": "unknown", "verified": False})

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=tmp_path / "normal.json")

    assert result["execution"]["state"] == "failed"
    assert result["result"] == {"state": "unavailable", "status": None}
    assert result["resource"] == {"state": "quarantined", "reuse_blocked": True}
    assert result["recovery_required"] is True
    assert result["owned_resources"][0]["identity"] == "workspace-1"


def test_run_smoke_does_not_promote_cleanup_without_structured_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request_value = request(session="live-session", pane="w1:p1")
    payload = {
        "herdr": {
            "session": "live-session",
            "pane": "w1:p1",
            "agent_name": "normal-main-1234",
            "version": "herdr-test",
        },
        "codex": {"version": "codex-test"},
        "git": {
            "worktree": str(request_value.worktree.resolve()),
            "repo_root": str(request_value.worktree.resolve()),
            "expected_base": request_value.expected_base,
            "head": request_value.git_revision,
        },
        "registry_launcher": {
            "repository_identity": request_value.repository_identity,
            "plan_identity": request_value.plan_identity,
            "model_provider": SECRETARY_PROVIDER,
            "model": "gpt-test",
        },
        "assignment": {"status": "submitted", "attempt_id": request_value.attempt_id},
    }
    monkeypatch.setattr("scripts.secretary_live_runtime._configured_provider", lambda _: SECRETARY_PROVIDER)
    monkeypatch.setattr("scripts.secretary_live_runtime._configured_model", lambda _: "gpt-test")
    monkeypatch.setattr("scripts.secretary_live_runtime.shutil.which", lambda _: "herdr.exe")
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._prepare_herdr_target",
        lambda request_value, **kwargs: (request_value, {"selector_mode": "exact"}, None),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime.subprocess.run",
        lambda *args, **kwargs: type(
            "Result",
            (),
            {"returncode": 0, "stdout": json.dumps(payload), "stderr": ""},
        )(),
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._observe_submitted_codex",
        lambda *args, **kwargs: {
            "state": "idle",
            "cleanup": {"state": "removed"},
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._observe_provider_telemetry",
        lambda *args, **kwargs: {"disposition": "observed_window", "cost": 0.01},
    )

    result = run_smoke(request_value, output=tmp_path / "smoke.json")

    assert result["disposition"] == "BLOCKED_CAPABILITY"
    assert result["missing_capabilities"] == ["secretary_runtime_receipt"]
    assert result["receipt"]["disposition"] == "BLOCKED_CAPABILITY"


def test_run_smoke_blocks_when_probe_workspace_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    request_value = request()
    monkeypatch.setattr(runtime, "_configured_provider", lambda _: SECRETARY_PROVIDER)
    monkeypatch.setattr(runtime, "_configured_model", lambda _: "gpt-test")
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "herdr.exe")
    monkeypatch.setattr(
        runtime,
        "_prepare_herdr_target",
        lambda request_value, **kwargs: (request_value, {"selector_mode": "bootstrapped"}, "w99"),
    )
    monkeypatch.setattr(
        runtime,
        "_close_herdr_workspace",
        lambda *args, **kwargs: {"state": "unknown", "reason": "close_failed"},
    )
    monkeypatch.setattr(
        runtime.subprocess,
        "run",
        lambda *args, **kwargs: type("Result", (), {"returncode": 0, "stdout": "{}", "stderr": ""})(),
    )
    monkeypatch.setattr(
        runtime,
        "sanitize_launcher_result",
        lambda *args, **kwargs: {"disposition": "READY", "evidence_provenance": "live-attributed"},
    )
    monkeypatch.setattr(runtime, "_observe_provider_telemetry", lambda *args, **kwargs: {"disposition": "inconclusive"})

    result = runtime.run_smoke(request_value, output=tmp_path / "smoke.json")

    assert result["disposition"] == "BLOCKED_CAPABILITY"
    assert result["evidence_provenance"] == "capability-probe"
    assert result["failure_kind"] == "runtime_workspace_cleanup_evidence_missing"
    assert result["receipt"]["disposition"] == "BLOCKED_CAPABILITY"
    assert result["receipt"]["evidence_provenance"] == "capability-probe"


def test_sanitize_launcher_result_excludes_raw_transport_output() -> None:
    result = sanitize_launcher_result(
        request(),
        returncode=0,
        payload={
            "assignment": {
                "status": "completed",
                "attempt_id": "attempt-1",
                "failure_kind": {"raw_body": "REVIEW_ASSIGNMENT_CANARY"},
            },
            "herdr": {"agent_name": {"authorization": "REVIEW_HERDR_CANARY"}},
            "codex": {"version": ["REVIEW_CODEX_CANARY"]},
            "secretary_runtime": {"session_id": "Bearer SYNTHETIC_SESSION_CANARY"},
            "stdout": "Authorization: bearer secret-value",
            "stderr": "raw response body",
            "api_key": "secret-value",
        },
    )

    assert result["provider"] == SECRETARY_PROVIDER
    assert result["task_id"] == "task-1"
    assert result["plan_revision"] == "plan-rev-1"
    assert result["attempt_id"] == "attempt-1"
    assert result["run_id"] == "run-1"
    assert "stdout" not in result
    assert "stderr" not in result
    assert "api_key" not in result
    assert "secret-value" not in str(result)
    assert "REVIEW_ASSIGNMENT_CANARY" not in str(result)
    assert "REVIEW_HERDR_CANARY" not in str(result)
    assert "REVIEW_CODEX_CANARY" not in str(result)
    assert "SYNTHETIC_SESSION_CANARY" not in str(result)


@pytest.mark.parametrize(
    ("launcher_failure", "expected_failure"),
    [
        ("Command failed (1): herdr api snapshot: server_not_running", "herdr_server_unavailable"),
        ("target_resolution=not_found; eligible candidates=0", "target_not_found"),
    ],
)
def test_sanitize_launcher_result_preserves_actionable_launcher_failure(
    launcher_failure: str,
    expected_failure: str,
) -> None:
    result = sanitize_launcher_result(
        request(),
        returncode=2,
        payload={
            "assignment": {
                "status": "blocked",
                "failure_kind": launcher_failure,
                "launcher_exit_code": 2,
            },
        },
    )

    assert result["failure_kind"] == expected_failure


@pytest.mark.parametrize("session_id", [
    '{"raw_bodies":"REVIEW_SESSION_CANARY"}',
    '{"raw_transport_bodies":"REVIEW_SESSION_CANARY"}',
    '{"rawBody":"REVIEW_SESSION_CANARY"}',
])
def test_sanitize_launcher_result_rejects_sensitive_session_payload(session_id: str) -> None:
    result = sanitize_launcher_result(
        request(),
        returncode=1,
        payload={
            "herdr": {"session": session_id},
            "secretary_runtime": {"session_id": session_id},
        },
    )

    assert "REVIEW_SESSION_CANARY" not in str(result)


def test_sanitize_launcher_result_preserves_structured_runtime_binding() -> None:
    result = sanitize_launcher_result(
        request(),
        returncode=0,
        payload={
            "secretary_runtime": {
                "task_id": "task-1",
                "plan_revision": "plan-rev-1",
                "attempt_id": "attempt-1",
                "run_id": "run-1",
            }
        },
    )

    assert result["runtime_identity"]["secretary_runtime"]["run_id"] == "run-1"


def test_safe_runtime_snapshot_preserves_structured_economics() -> None:
    result = _safe_runtime_snapshot(
        {
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "attempt_id": "attempt-1",
            "run_id": "run-1",
            "metrics": {
                "token_usage": {
                    "input_tokens": 883,
                    "output_tokens": 6,
                    "total_tokens": 889,
                    "cache_read_input_tokens": 400,
                    "source": "response.usage",
                    "confidence": "observed",
                },
                "cost": {
                    "value": 0.000543,
                    "kind": "estimated",
                    "currency": "USD",
                    "pricing_source": "published-rate-card",
                    "pricing_effective_date": "2026-10-09",
                    "model": "glm/glm-4.7",
                    "model_resolution": "exact",
                },
            },
            "timestamps": {},
        },
        {
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "attempt_id": "attempt-1",
            "run_id": "run-1",
        },
    )

    assert result["metrics"]["token_usage"]["total_tokens"] == 889
    assert result["metrics"]["token_usage"]["cache_read_input_tokens"] == 400
    assert result["metrics"]["cost"]["kind"] == "estimated"


def test_safe_runtime_snapshot_drops_unobserved_token_provenance() -> None:
    result = _safe_runtime_snapshot(
        {
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "attempt_id": "attempt-1",
            "run_id": "run-1",
            "metrics": {
                "token_usage": {
                    "input_tokens": 883,
                    "output_tokens": 6,
                    "total_tokens": 889,
                    "source": "session-status",
                    "confidence": "estimated",
                }
            },
            "timestamps": {},
        },
        {
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "attempt_id": "attempt-1",
            "run_id": "run-1",
        },
    )

    assert result["metrics"]["token_usage"] == "unknown"


def test_safe_runtime_snapshot_normalizes_9router_usage_fields() -> None:
    result = _safe_runtime_snapshot(
        {
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "attempt_id": "attempt-1",
            "run_id": "run-1",
            "metrics": {
                "token_usage": {
                    "prompt_tokens": 1_000,
                    "completion_tokens": 100,
                    "cached_tokens": 800,
                    "cache_creation_input_tokens": 50,
                }
            },
            "timestamps": {},
        },
        {
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "attempt_id": "attempt-1",
            "run_id": "run-1",
        },
    )

    assert result["metrics"]["token_usage"]["cache_read_input_tokens"] == 800
    assert result["metrics"]["token_usage"]["cache_write_input_tokens"] == 50


def test_safe_runtime_snapshot_preserves_unknown_cost_reason() -> None:
    result = _safe_runtime_snapshot(
        {
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "attempt_id": "attempt-1",
            "run_id": "run-1",
            "metrics": {
                "cost": {
                    "value": "unknown",
                    "reason": "model_rate_unavailable",
                }
            },
            "timestamps": {},
        },
        {
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "attempt_id": "attempt-1",
            "run_id": "run-1",
        },
    )

    assert result["metrics"]["cost"] == {
        "value": "unknown",
        "reason": "model_rate_unavailable",
    }


def test_sanitize_launcher_result_rejects_submission_as_live_execution() -> None:
    result = sanitize_launcher_result(
        request(),
        returncode=0,
        payload={
            "assignment": {
                "status": "submitted",
                "attempt_id": "attempt-1",
            },
            "secretary_runtime": {
                "task_id": "task-1",
                "plan_revision": "plan-rev-1",
                "attempt_id": "attempt-1",
                "run_id": "run-1",
            },
        },
    )

    assert result["disposition"] == "BLOCKED_CAPABILITY"
    assert result["evidence_provenance"] == "capability-probe"
    assert result["metrics"]["secretary_turns"] == "unknown"


def test_sanitize_launcher_result_rejects_mismatched_observed_binding() -> None:
    result = sanitize_launcher_result(
        request(),
        returncode=0,
        payload={
            "assignment": {
                "status": "completed",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
                "task_result": {"state": "reported_completed"},
            },
            "secretary_runtime": {
                "observed": True,
                "task_id": "task-1",
                "plan_revision": "plan-rev-1",
                "attempt_id": "attempt-1",
                "run_id": "run-other",
                "timestamps": {"run_started": "2026-10-08T10:00:00+00:00"},
                "metrics": {"secretary_turns": 1},
            },
        },
    )

    assert result["disposition"] == "BLOCKED_CAPABILITY"
    assert result["evidence_provenance"] == "capability-probe"


def test_sanitize_launcher_result_requires_authoritative_runtime_sources() -> None:
    result = sanitize_launcher_result(
        request(),
        returncode=0,
        configured_model="gpt-test",
        payload={
            "assignment": {
                "status": "completed",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
                "task_result": {"state": "reported_completed"},
            },
            "secretary_runtime": {
                "observed": True,
                "task_id": "task-1",
                "plan_revision": "plan-rev-1",
                "attempt_id": "attempt-1",
                "run_id": "run-1",
                "repository_identity": "repo/example",
                "plan_identity": "plan/example",
                "git_revision": "581844d",
                "worktree": str(Path("C:/worktree").resolve()),
                "provider": "9router",
                "model": "gpt-test",
                "controller_id": "cos-1",
                "session_id": "session-1",
                "timestamps": {"run_started": "2026-10-08T10:00:00+00:00"},
                "metrics": {"secretary_turns": 1},
            },
        },
    )

    assert result["disposition"] == "BLOCKED_CAPABILITY"
    assert result["transport_evidence"] == "unproven"
    assert result["missing_capabilities"] == [
        "transport_completion_or_cleanup",
        "secretary_runtime_receipt",
    ]


def test_completed_transport_names_only_remaining_secretary_blocker() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._classify_capabilities(
        "BLOCKED_CAPABILITY",
        {"state": "idle", "cleanup": {"state": "removed"}},
    )

    assert result == {
        "transport_evidence": "proven",
        "missing_capabilities": ["secretary_runtime_receipt"],
    }


def test_done_transport_names_only_remaining_secretary_blocker() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._classify_capabilities(
        "BLOCKED_CAPABILITY",
        {"state": "done", "cleanup": {"state": "removed"}},
    )

    assert result == {
        "transport_evidence": "proven",
        "missing_capabilities": ["secretary_runtime_receipt"],
    }


def test_completed_codex_transport_produces_bound_runtime_snapshot() -> None:
    request_value = request(session="live-session", pane="w1:p1")
    payload = {
        "herdr": {
            "session": "live-session",
            "pane": "w1:p1",
            "agent_name": "normal-main-1234",
            "version": "herdr-test",
        },
        "codex": {"version": "codex-test"},
        "git": {
            "worktree": str(request_value.worktree.resolve()),
            "repo_root": str(request_value.worktree.resolve()),
            "expected_base": request_value.expected_base,
            "head": request_value.git_revision,
        },
        "registry_launcher": {
            "repository_identity": request_value.repository_identity,
            "plan_identity": request_value.plan_identity,
            "model_provider": SECRETARY_PROVIDER,
            "model": "gpt-test",
        },
        "secretary_runtime": structured_runtime(request_value, session_id="live-session", model="gpt-test"),
    }
    snapshot = _build_codex_runtime_snapshot(
        request_value,
        payload,
        {
            "state": "idle",
            "cleanup": {"state": "removed"},
            "observed_at": "2026-10-10T10:00:05+00:00",
        },
        configured_model="gpt-test",
        started_at="2026-10-10T10:00:00+00:00",
        finished_at="2026-10-10T10:00:06+00:00",
        provider_telemetry={
            "disposition": "observed_window",
            "input_tokens": 100,
            "output_tokens": 10,
            "total_tokens": 110,
            "cache_read_input_tokens": 80,
            "cache_write_input_tokens": 0,
            "cost": 0.01,
        },
    )

    assert snapshot is not None
    assert snapshot["observed"] is True
    assert snapshot["session_id"] == "live-session"
    assert snapshot["metrics"]["token_usage"] == "unknown"
    assert snapshot["metrics"]["cost"] == "unknown"
    assert set(snapshot["sources"]) == {"launch", "secretary", "task_result", "settlement", "acceptance"}
    assert all(source["attempt_id"] == request_value.attempt_id for source in snapshot["sources"].values())


def test_runtime_snapshot_uses_provider_session_not_herdr_control_session() -> None:
    request_value = request(session="herdr-session", pane="w1:p1")
    payload = {
        "herdr": {"session": "herdr-control-session"},
        "git": {
            "worktree": str(request_value.worktree.resolve()),
            "repo_root": str(request_value.worktree.resolve()),
            "expected_base": request_value.expected_base,
            "head": request_value.git_revision,
        },
        "registry_launcher": {
            "repository_identity": request_value.repository_identity,
            "plan_identity": request_value.plan_identity,
            "model_provider": SECRETARY_PROVIDER,
            "model": "gpt-test",
        },
        "secretary_runtime": structured_runtime(request_value, session_id="provider-session", model="gpt-test"),
    }

    snapshot = _build_codex_runtime_snapshot(
        request_value,
        payload,
        {"state": "idle", "cleanup": {"state": "removed"}},
        configured_model="gpt-test",
        started_at="2026-10-10T10:00:00+00:00",
        finished_at="2026-10-10T10:00:06+00:00",
    )

    assert snapshot is not None
    assert snapshot["session_id"] == "provider-session"


def test_runtime_snapshot_rejects_mismatched_top_level_identity() -> None:
    request_value = request(session="live-session", pane="w1:p1")
    runtime = structured_runtime(request_value, session_id="provider-session", model="gpt-test")
    runtime["attempt_id"] = "attempt-other"
    payload = {
        "herdr": {"session": "live-session"},
        "git": {
            "worktree": str(request_value.worktree.resolve()),
            "repo_root": str(request_value.worktree.resolve()),
            "expected_base": request_value.expected_base,
            "head": request_value.git_revision,
        },
        "registry_launcher": {
            "repository_identity": request_value.repository_identity,
            "plan_identity": request_value.plan_identity,
            "model_provider": SECRETARY_PROVIDER,
            "model": "gpt-test",
        },
        "secretary_runtime": runtime,
    }

    assert _build_codex_runtime_snapshot(
        request_value,
        payload,
        {"state": "idle", "cleanup": {"state": "removed"}},
        configured_model="gpt-test",
        started_at="2026-10-10T10:00:00+00:00",
        finished_at="2026-10-10T10:00:06+00:00",
    ) is None


@pytest.mark.parametrize("mutation", ["empty_sources", "wrong_attempt", "wrong_session"])
def test_runtime_snapshot_rejects_untrusted_source_records(mutation: str) -> None:
    request_value = request(session="live-session", pane="w1:p1")
    runtime = structured_runtime(request_value, session_id="provider-session", model="gpt-test")
    if mutation == "empty_sources":
        runtime["sources"] = {name: {} for name in runtime["sources"]}
    elif mutation == "wrong_attempt":
        runtime["sources"]["settlement"]["attempt_id"] = "attempt-other"
    else:
        runtime["sources"]["secretary"]["session_id"] = "provider-other"
    payload = {
        "herdr": {"session": "live-session"},
        "git": {
            "worktree": str(request_value.worktree.resolve()),
            "repo_root": str(request_value.worktree.resolve()),
            "expected_base": request_value.expected_base,
            "head": request_value.git_revision,
        },
        "registry_launcher": {
            "repository_identity": request_value.repository_identity,
            "plan_identity": request_value.plan_identity,
            "model_provider": SECRETARY_PROVIDER,
            "model": "gpt-test",
        },
        "secretary_runtime": runtime,
    }

    assert _build_codex_runtime_snapshot(
        request_value,
        payload,
        {"state": "idle", "cleanup": {"state": "removed"}},
        configured_model="gpt-test",
        started_at="2026-10-10T10:00:00+00:00",
        finished_at="2026-10-10T10:00:06+00:00",
    ) is None


def test_completed_codex_transport_promotes_only_matched_9router_usage() -> None:
    request_value = request(session="live-session", pane="w1:p1")
    payload = {
        "herdr": {"session": "live-session"},
        "git": {
            "worktree": str(request_value.worktree.resolve()),
            "repo_root": str(request_value.worktree.resolve()),
            "expected_base": request_value.expected_base,
            "head": request_value.git_revision,
        },
        "registry_launcher": {
            "repository_identity": request_value.repository_identity,
            "plan_identity": request_value.plan_identity,
            "model_provider": SECRETARY_PROVIDER,
            "model": "gpt-test",
        },
        "secretary_runtime": structured_runtime(request_value, session_id="live-session", model="gpt-test"),
    }
    snapshot = _build_codex_runtime_snapshot(
        request_value,
        payload,
        {"state": "idle", "cleanup": {"state": "removed"}},
        configured_model="gpt-test",
        started_at="2026-10-10T10:00:00+00:00",
        finished_at="2026-10-10T10:00:06+00:00",
        provider_telemetry={
            "disposition": "matched",
            "request_count": 1,
            "input_tokens": 100,
            "output_tokens": 10,
            "total_tokens": 110,
            "cache_read_input_tokens": 80,
            "cache_write_input_tokens": 5,
        },
    )

    assert snapshot is not None
    assert snapshot["metrics"]["token_usage"] == "unknown"
    assert snapshot["metrics"]["secretary_turns"] == 1


def test_sanitize_launcher_result_drops_unapproved_observed_fields() -> None:
    result = sanitize_launcher_result(
        request(),
        returncode=0,
        payload={
            "secretary_runtime": {
                "task_id": "task-1",
                "plan_revision": "plan-rev-1",
                "attempt_id": "attempt-1",
                "run_id": "run-1",
                "observed": True,
                "timestamps": {"run_started": "2026-10-08T10:00:00+00:00", "credentials": "secret"},
                "metrics": {"secretary_turns": 1, "raw_body": "secret"},
            }
        },
    )

    assert "credentials" not in str(result)
    assert "raw_body" not in str(result)


def test_safe_runtime_snapshot_drops_untrusted_producer_payload() -> None:
    snapshot = _safe_runtime_snapshot(
        {
            "sources": {
                "launch": {
                    "producer": {"authorization": "Bearer SYNTHETIC-REVIEW-CANARY"},
                }
            }
        },
        {"pair_id": "run-1", "arm": "candidate", "workstream": "secretary-live-runtime", "checkpoint": "plan-rev-1:task-1"},
    )

    assert "producer" not in snapshot["sources"]["launch"]
    assert "SYNTHETIC-REVIEW-CANARY" not in str(snapshot)


def test_smoke_receipt_preserves_required_source_bindings() -> None:
    request_value = request()
    binding = {
        "pair_id": request_value.run_id,
        "arm": "candidate",
        "run_id": request_value.run_id,
        "attempt_id": request_value.attempt_id,
        "task_id": request_value.task_id,
        "plan_revision": request_value.plan_revision,
        "repository_identity": request_value.repository_identity,
        "plan_identity": request_value.plan_identity,
        "git_revision": request_value.git_revision,
        "worktree": str(request_value.worktree.resolve()),
        "workstream": "secretary-live-runtime",
        "checkpoint": f"{request_value.plan_revision}:{request_value.task_id}",
        "provider": SECRETARY_PROVIDER,
        "model": "gpt-test",
        "controller_id": "cos-supervised",
        "session_id": "session-1",
    }
    producers = {
        "launch": "herdr_main_launcher",
        "secretary": "secretary_live_runtime",
        "task_result": "dcode-project",
        "settlement": "project_os_runtime.attempt",
        "acceptance": "cos",
    }
    sources = {
        name: {"producer": producer, "source_ref": f"runtime://{name}/run-1", "source_digest": "a" * 64, **binding}
        for name, producer in producers.items()
    }
    raw_runtime = {
        **binding,
        "observed": True,
        "timestamps": {
            "run_started": "2026-10-08T10:00:00+00:00",
            "cos_entry": "2026-10-08T10:00:01+00:00",
            "secretary_entry": "2026-10-08T10:00:02+00:00",
            "worker_entry": "2026-10-08T10:00:03+00:00",
            "publication": "2026-10-08T10:00:40+00:00",
            "settlement": "2026-10-08T10:00:50+00:00",
            "acceptance": "2026-10-08T10:01:00+00:00",
            "secretary_exit": "2026-10-08T10:01:05+00:00",
            "cos_exit": "2026-10-08T10:01:08+00:00",
            "run_finished": "2026-10-08T10:01:10+00:00",
        },
        "metrics": {
            "cos_turns": 0,
            "secretary_turns": 1,
            "human_interventions": 0,
            "publication_success": True,
            "settlement_proven": True,
            "acceptance_decision": "PASS",
            "token_usage": "unknown",
            "cost": "unknown",
        },
        "sources": sources,
    }
    expected = {key: binding[key] for key in ("pair_id", "arm", "run_id", "attempt_id", "task_id", "plan_revision", "repository_identity", "plan_identity", "git_revision", "worktree", "workstream", "checkpoint", "provider", "model", "controller_id", "session_id")}
    structured = _safe_runtime_snapshot(raw_runtime, expected)
    receipt = _smoke_receipt(
        request_value,
        {
            "evidence_provenance": "live-attributed",
            "runtime_identity": {
                "provider": SECRETARY_PROVIDER,
                "model": "gpt-test",
                "controller_id": "cos-supervised",
                "session_id": "session-1",
                "secretary_runtime": structured,
            },
        },
    )

    assert receipt["valid"] is True


def test_provider_telemetry_uses_attributed_9router_run_usage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database = tmp_path / "data.sqlite"
    database.write_bytes(b"")
    observed: list[dict[str, str]] = []

    def fake_observe(path: Path, *, start: str, end: str, expected_session_id: str) -> dict[str, object]:
        observed.append({"database": str(path), "start": start, "end": end, "expected_session_id": expected_session_id})
        return {
            "schema_version": "9router-usage-observation-v1",
            "disposition": "matched",
            "source": "9router-local-read-only",
            "attribution": "session",
            "session_id": "session-1",
            "input_tokens": 100,
            "output_tokens": 10,
            "total_tokens": 110,
            "cache_read_input_tokens": 80,
            "cache_write_input_tokens": 0,
            "cost": 0.01,
            "cost_provenance": "provider-reported",
        }

    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "observe_run_usage", fake_observe)
    monkeypatch.setenv("NINEROUTER_DATABASE", str(database))

    result = _observe_provider_telemetry(
        "2026-10-10T00:00:00+00:00",
        "2026-10-10T00:00:01+00:00",
        expected_session_id="session-1",
    )

    assert result["disposition"] == "matched"
    assert result["cache_read_input_tokens"] == 80
    assert result["cost"] == 0.01
    assert observed[0]["database"] == str(database)
    assert result["observation_window"]["lookback_seconds"] == 0.0
    assert observed[0]["start"] == "2026-10-10T00:00:00+00:00"
    assert observed[0]["end"] == "2026-10-10T00:00:01+00:00"
    assert observed[0]["expected_session_id"] == "session-1"


def test_provider_telemetry_keeps_unattributed_window_usage_without_session_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database = tmp_path / "data.sqlite"
    database.write_bytes(b"")
    observed: list[dict[str, str]] = []

    def fake_observe(path: Path, *, start: str, end: str) -> dict[str, object]:
        observed.append({"database": str(path), "start": start, "end": end})
        return {
            "schema_version": "9router-usage-observation-v1",
            "disposition": "observed_window",
            "source": "9router-local-read-only",
            "attribution": "time-window",
            "confidence": "unattributed",
            "input_tokens": 100,
            "output_tokens": 10,
            "total_tokens": 110,
            "cache_read_input_tokens": 80,
            "cache_write_input_tokens": 0,
            "cost": 0.01,
            "cost_provenance": "provider-reported",
        }

    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "observe_window_usage", fake_observe, raising=False)
    monkeypatch.setenv("NINEROUTER_DATABASE", str(database))

    result = runtime._observe_provider_telemetry(
        "2026-10-10T00:00:00+00:00",
        "2026-10-10T00:00:01+00:00",
    )

    assert result["disposition"] == "observed_window"
    assert result["attribution"] == "time-window"
    assert result["confidence"] == "unattributed"
    assert result["cache_read_input_tokens"] == 80
    assert observed[0]["database"] == str(database)


def test_prepare_herdr_target_bootstraps_server_workspace_and_rechecks_pane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    status_calls = 0
    commands: list[list[str]] = []
    started: list[list[str]] = []
    pane_checks = 0

    def fake_run(command, **kwargs):
        nonlocal status_calls
        commands.append(command)
        if command[1:] == ["status", "server"]:
            status_calls += 1
            if status_calls == 1:
                return subprocess.CompletedProcess(command, 1, "", "server_not_running")
            return subprocess.CompletedProcess(command, 0, "status: running\n", "")
        if command[1:3] == ["workspace", "create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "result": {
                            "root_pane": {
                                "cwd": "C:/worktree/",
                                "pane_id": "w99:p1",
                                "workspace_id": "w99",
                            }
                        }
                    }
                ),
                "",
            )
        if command[1:3] == ["workspace", "close"]:
            return subprocess.CompletedProcess(command, 0, '{"result":{"type":"ok"}}', "")
        raise AssertionError(command)

    class FakeProcess:
        pass

    def fake_popen(command, **kwargs):
        started.append(command)
        return FakeProcess()

    def fake_pane(*args, **kwargs):
        nonlocal pane_checks
        pane_checks += 1
        if pane_checks == 1:
            raise runtime.TargetCandidateRejected("pane is initializing")
        return {"pane": {"cwd": "C:/worktree/"}}

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)
    monkeypatch.setattr(runtime.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(runtime, "_herdr_pane", fake_pane, raising=False)
    monkeypatch.setattr(runtime.time, "sleep", lambda _: None)

    launch_request, preflight, workspace_id = runtime._prepare_herdr_target(
        request(worktree=Path("C:/worktree")),
        herdr="herdr",
        env={},
    )

    assert launch_request.session == "default"
    assert launch_request.pane == "w99:p1"
    assert workspace_id == "w99"
    assert preflight["server"] == "ready"
    assert preflight["server_started"] is True
    assert preflight["workspace_created"] is True
    assert preflight["pane_cwd_verified"] is True
    assert pane_checks == 2
    assert started == [["herdr", "server"]]


def test_prepare_herdr_target_preserves_exact_selector_without_workspace_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[1:] == ["status", "server"]:
            return subprocess.CompletedProcess(command, 0, "status: running\n", "")
        raise AssertionError(command)

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)

    original = request(session="default", pane="w1:p1")
    launch_request, preflight, workspace_id = runtime._prepare_herdr_target(
        original,
        herdr="herdr",
        env={},
    )

    assert launch_request == original
    assert preflight["selector_mode"] == "exact"
    assert workspace_id is None
    assert commands == [["herdr", "status", "server"]]


def test_prepare_herdr_target_reuses_named_session_with_auto_pane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[1:] == ["status", "server"]:
            return subprocess.CompletedProcess(command, 0, "status: running\n", "")
        raise AssertionError(command)

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)

    original = request(session="default", pane="auto")
    launch_request, preflight, workspace_id = runtime._prepare_herdr_target(
        original,
        herdr="herdr",
        env={},
    )

    assert launch_request == original
    assert preflight["selector_mode"] == "named-session-auto-pane"
    assert preflight["session"] == "default"
    assert preflight["pane"] == "auto"
    assert preflight["workspace_created"] is False
    assert workspace_id is None
    assert commands == [["herdr", "status", "server"]]


def test_create_herdr_workspace_closes_workspace_when_cwd_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    closed: list[list[str]] = []

    def fake_run(command, **kwargs):
        if command[1:3] == ["workspace", "create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "result": {
                            "root_pane": {
                                "cwd": "C:/wrong-worktree/",
                                "pane_id": "w99:p1",
                                "workspace_id": "w99",
                            }
                        }
                    }
                ),
                "",
            )
        if command[1:3] == ["workspace", "close"]:
            closed.append(command)
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1:3] == ["workspace", "get"]:
            return subprocess.CompletedProcess(
                command,
                1,
                json.dumps({"error": {"code": "workspace_not_found"}}),
                "",
            )
        raise AssertionError(command)

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)

    with pytest.raises(runtime.LaunchBlocked, match="cwd mismatch"):
        runtime._create_herdr_workspace(request(worktree=Path("C:/worktree")), "herdr", env={})

    assert closed == [["herdr", "workspace", "close", "w99"]]


def test_create_herdr_workspace_preserves_identity_on_cwd_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    def fake_run(command, **kwargs):
        if command[1:3] == ["workspace", "create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"root_pane": {"cwd": "C:/wrong-worktree/", "pane_id": "w99:p1", "workspace_id": "w99"}}}),
                "",
            )
        if command[1:3] == ["workspace", "close"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1:3] == ["workspace", "get"]:
            return subprocess.CompletedProcess(command, 0, json.dumps({"result": {"workspace_id": "w99", "state": "present"}}), "")
        raise AssertionError(command)

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)

    with pytest.raises(runtime.LaunchBlocked) as raised:
        runtime._create_herdr_workspace(request(worktree=Path("C:/worktree")), "herdr", env={})

    assert raised.value.workspace_id == "w99"
    assert raised.value.workspace_close["verified"] is False


def test_create_herdr_workspace_preserves_top_level_identity_on_malformed_root_pane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    closed: list[str] = []

    def fake_run(command, **kwargs):
        if command[1:3] == ["workspace", "create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "result": {
                            "workspace_id": "owned-workspace",
                            "root_pane": {
                                "cwd": "C:/worktree/",
                                "pane_id": "owned-workspace:p1",
                                "workspace_id": None,
                            },
                        }
                    }
                ),
                "",
            )
        if command[1:3] == ["workspace", "close"]:
            closed.append(command[-1])
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1:3] == ["workspace", "get"]:
            return subprocess.CompletedProcess(
                command,
                1,
                json.dumps({"error": {"code": "workspace_not_found"}}),
                "",
            )
        raise AssertionError(command)

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)

    with pytest.raises(runtime.LaunchBlocked) as raised:
        runtime._create_herdr_workspace(request(worktree=Path("C:/worktree")), "herdr", env={})

    assert raised.value.workspace_id == "owned-workspace"
    assert closed == ["owned-workspace"]


def test_create_herdr_workspace_rejects_conflicting_root_pane_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    closed: list[str] = []

    def fake_run(command, **kwargs):
        if command[1:3] == ["workspace", "create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "result": {
                            "workspace_id": "owned-workspace",
                            "root_pane": {
                                "cwd": "C:/worktree/",
                                "pane_id": "other-workspace:p1",
                                "workspace_id": "other-workspace",
                            },
                        }
                    }
                ),
                "",
            )
        if command[1:3] == ["workspace", "close"]:
            closed.append(command[-1])
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1:3] == ["workspace", "get"]:
            return subprocess.CompletedProcess(
                command,
                1,
                json.dumps({"error": {"code": "workspace_not_found"}}),
                "",
            )
        raise AssertionError(command)

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)

    with pytest.raises(runtime.LaunchBlocked) as raised:
        runtime._create_herdr_workspace(request(worktree=Path("C:/worktree")), "herdr", env={})

    assert raised.value.workspace_id == "owned-workspace"
    assert closed == ["owned-workspace"]


def test_create_herdr_workspace_preserves_identity_for_non_object_root_pane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    closed: list[str] = []

    def fake_run(command, **kwargs):
        if command[1:3] == ["workspace", "create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"workspace_id": "owned-workspace", "root_pane": None}}),
                "",
            )
        if command[1:3] == ["workspace", "close"]:
            closed.append(command[-1])
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1:3] == ["workspace", "get"]:
            return subprocess.CompletedProcess(
                command,
                1,
                json.dumps({"error": {"code": "workspace_not_found"}}),
                "",
            )
        raise AssertionError(command)

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)

    with pytest.raises(runtime.LaunchBlocked):
        runtime._create_herdr_workspace(request(worktree=Path("C:/worktree")), "herdr", env={})

    assert closed == ["owned-workspace"]


def test_prepare_herdr_target_preserves_workspace_after_pane_oserror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    closed: list[str] = []

    def fake_run(command, **kwargs):
        if command[1:] == ["status", "server"]:
            return subprocess.CompletedProcess(command, 0, "status: running\n", "")
        if command[1:3] == ["workspace", "create"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"root_pane": {"cwd": "C:/worktree/", "pane_id": "w99:p1", "workspace_id": "w99"}}}),
                "",
            )
        if command[1:3] == ["workspace", "close"]:
            closed.append(command[-1])
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1:3] == ["workspace", "get"]:
            return subprocess.CompletedProcess(command, 1, json.dumps({"error": {"code": "workspace_not_found"}}), "")
        raise AssertionError(command)

    monkeypatch.setattr(runtime, "_herdr_run", fake_run)
    monkeypatch.setattr(runtime, "_verify_herdr_pane", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("pane read failed")))

    with pytest.raises(OSError) as raised:
        runtime._prepare_herdr_target(request(worktree=Path("C:/worktree")), herdr="herdr", env={})

    assert getattr(raised.value, "workspace_id") == "w99"
    assert getattr(raised.value, "workspace_close")["verified"] is True
    assert closed == ["w99"]


def test_select_launcher_payload_keeps_launch_identity_and_assignment() -> None:
    payload = select_launcher_payload(
        [
            {
                "herdr": {"agent_name": "secretary-main", "session": "project-os", "pane": "w4:p1"},
                "codex": {"version": "codex-cli 0.154.0"},
                "secretary_runtime": {"run_id": "run-1"},
            },
            {"assignment": {"status": "submitted", "attempt_id": "attempt-1"}},
        ]
    )

    assert payload["herdr"]["agent_name"] == "secretary-main"
    assert payload["secretary_runtime"]["run_id"] == "run-1"
    assert payload["assignment"]["status"] == "submitted"


def test_runtime_script_runs_directly_from_repository_root() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/secretary_live_runtime.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "run" in completed.stdout
    assert "probe" in completed.stdout


def test_observe_submitted_codex_rejects_old_answer_with_unrelated_terminal_churn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale = "Codex screen\n• OLD ANSWER\n› Ask Codex to do anything"
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "content": stale + "\nnew prompt echo",
            "output_sha256": "b" * 64,
            "output_chars": len(stale) + 16,
            "state_change_seq": 2,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit={**_submission_anchor(), "content": stale},
        env={},
    )

    assert observation["observation_error"] == "submission freshness not proven"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_accepts_repeated_answer_with_terminal_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answer = "Codex screen\n• SAME ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "content": answer,
            "output_sha256": "b" * 64,
            "output_chars": len(answer),
            "state_change_seq": 3,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit={**_submission_anchor(), "content": answer},
        env={},
    )

    assert observation["semantic_content"] == "SAME ANSWER"


def test_observe_submitted_codex_rejects_stale_answer_with_historical_completion_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale = "Codex screen\n• OLD ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "content": stale + "\nnew prompt echo",
            "output_sha256": "b" * 64,
            "output_chars": len(stale) + 16,
            "state_change_seq": 2,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit={**_submission_anchor(), "content": stale},
        env={},
    )

    assert observation["observation_error"] == "submission freshness not proven"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_ignores_prompt_echo_bullets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "Codex screen\nWorked for 1s\n"
        "\u203a Please echo this input:\n\u2022 USER PROMPT TEXT\n"
        "\u203a Ask Codex to do anything"
    )
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "content": content,
            "output_sha256": "b" * 64,
            "output_chars": len(content),
            "state_change_seq": 2,
            "observation_error": None,
        },
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit={
            **_submission_anchor(),
            "content": "Codex screen\nWorked for 1s\n\u203a Ask Codex to do anything",
        },
        env={},
    )

    assert "semantic_content" not in observation


def test_observe_submitted_codex_accepts_repeated_answer_with_new_completion_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = "Codex screen\n• SAME ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    snapshot = "Codex screen\n• SAME ANSWER\nWorked for 2s\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "content": snapshot,
            "output_sha256": "b" * 64,
            "output_chars": len(snapshot),
            "state_change_seq": 3,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit={**_submission_anchor(), "content": anchor},
        env={},
    )

    assert observation["semantic_content"] == "SAME ANSWER"


def test_observe_submitted_codex_accepts_repeated_answer_with_prompt_suffix_and_new_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = "› Original request\n• SAME ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    snapshot = "› Original request\n• SAME ANSWER\nWorked for 2s\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "content": snapshot,
            "output_sha256": "b" * 64,
            "output_chars": len(snapshot),
            "state_change_seq": 3,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit={**_submission_anchor(), "content": anchor},
        env={},
    )

    assert observation["semantic_content"] == "SAME ANSWER"


def test_observe_submitted_codex_rejects_prompt_echo_with_completion_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = "› Original request\n• OLD ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    snapshot = (
        "› Original request\n• OLD ANSWER\nWorked for 1s\n"
        "› Please echo this input:\nWorked for 2s\n• USER PROMPT TEXT\n"
        "› Ask Codex to do anything"
    )
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "content": snapshot,
            "output_sha256": "b" * 64,
            "output_chars": len(snapshot),
            "state_change_seq": 2,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit={**_submission_anchor(), "content": anchor},
        env={},
    )

    assert observation["observation_error"] == "submission freshness not proven"
    assert "semantic_content" not in observation


@pytest.mark.parametrize(
    "content",
    [
        "Never put passwords in source code.",
        "Authorization headers should be redacted.",
        "Bearer [REDACTED] is safe to display.",
    ],
)
def test_normal_outcome_preserves_safe_security_prose(content: str) -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={"assignment": {"execution": {"state": "completed"}, "task_result": {"state": "unknown"}}},
        observation={"state": "done", "semantic_content": content, "cleanup": {"state": "removed"}},
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"] == {"state": "reported", "status": "completed", "content": content}


def test_normal_outcome_redacts_quoted_secret_values() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={"assignment": {"execution": {"state": "completed"}, "task_result": {"state": "unknown"}}},
        observation={
            "state": "done",
            "semantic_content": '{"api_key": "SYNTHETIC first second"}',
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"]["content"] == '{"api_key": "[REDACTED]"}'


def test_normal_outcome_redacts_query_secret_inside_quoted_value() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={"assignment": {"execution": {"state": "completed"}, "task_result": {"state": "unknown"}}},
        observation={
            "state": "done",
            "semantic_content": '{"api_key": "SYNTHETIC-prefix?token=SYNTHETIC-suffix"}',
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"]["content"] == '{"api_key": "[REDACTED]"}'
