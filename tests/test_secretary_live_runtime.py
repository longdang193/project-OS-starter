from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

import pytest

from scripts.secretary_live_runtime import (
    SECRETARY_PROVIDER,
    SecretaryLaunchRequest,
    _safe_runtime_snapshot,
    _build_codex_runtime_snapshot,
    _observe_submitted_codex,
    _observe_provider_telemetry,
    _release_codex_agent,
    _smoke_receipt,
    build_launcher_command,
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


def test_run_smoke_preserves_ready_result_without_post_submit_downgrade(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("scripts.secretary_live_runtime._configured_provider", lambda _: "9router")
    monkeypatch.setattr("scripts.secretary_live_runtime._configured_model", lambda _: "gpt-test")
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
        lambda *args, **kwargs: {"disposition": "inconclusive"},
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._smoke_receipt",
        lambda *args, **kwargs: {"disposition": "READY"},
    )

    result = run_smoke(request(), output=tmp_path / "smoke.json")

    assert result["disposition"] == "READY"
    assert result["evidence_provenance"] == "live-attributed"


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

    assert snapshot is None


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
    assert "smoke" in completed.stdout
