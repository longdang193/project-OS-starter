from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from scripts.secretary_live_runtime import (
    SECRETARY_PROVIDER,
    SecretaryLaunchRequest,
    _safe_runtime_snapshot,
    _smoke_receipt,
    build_launcher_command,
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
