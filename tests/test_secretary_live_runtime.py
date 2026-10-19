from __future__ import annotations

from pathlib import Path
import json
import os
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
    _snapshot_result_content,
    _smoke_receipt,
    build_launcher_command,
    _reconcile_native_artifacts,
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


def test_normal_request_excludes_herdr_selectors_and_builder() -> None:
    import scripts.secretary_live_runtime as runtime

    request_value = normal_request()

    assert not hasattr(request_value, "session")
    assert not hasattr(request_value, "pane")
    assert not hasattr(runtime, "build_normal_launcher_command")


def test_reconcile_native_artifacts_requires_current_request_fingerprint(
    tmp_path: Path,
) -> None:
    from scripts.project_os_runtime.secretary_results import (
        native_binding_path,
        native_result_path,
        native_submission_path,
        publish_native_binding,
        publish_native_result,
        publish_native_submission,
        request_fingerprint,
    )
    import scripts.secretary_live_runtime as runtime

    fingerprint = request_fingerprint(
        {
            "task_sha256": "task",
            "repository_identity": "repo",
            "git_revision": "rev",
            "execution_role": "secretary",
            "provider_identity": "9router",
            "model_identity": "model",
            "runtime_grant_digest": "",
            "workspace_change_digest": "workspace",
        }
    )
    output = tmp_path / "normal.json"
    publish_native_binding(
        native_binding_path(output),
        {
            "schema": "secretary-native-binding.v3",
            "attempt_id": "attempt-1",
            "logical_operation_id": "operation-1",
            "request_fingerprint": fingerprint,
            "native_session_id": "session",
            "native_thread_id": "thread",
            "pre_submit_boundary": "fresh-zero-prior-turn",
            "created_at": "2026-10-18T10:00:00+00:00",
            "transport": {"session": "codex-app-server", "pane": "native", "agent_name": "normal-secretary"},
        },
    )
    publish_native_submission(
        native_submission_path(output),
        {
            "schema": "secretary-native-submission.v3",
            "attempt_id": "attempt-1",
            "logical_operation_id": "operation-1",
            "request_fingerprint": fingerprint,
            "native_session_id": "session",
            "native_thread_id": "thread",
            "native_turn_id": "turn",
            "accepted_at": "2026-10-18T10:00:01+00:00",
            "status": "accepted",
        },
    )
    publish_native_result(
        native_result_path(output),
        {
            "schema": "secretary-native-result.v3",
            "producer": "codex-native",
            "attempt_id": "attempt-1",
            "logical_operation_id": "operation-1",
            "request_fingerprint": fingerprint,
            "observed_at": "2026-10-18T10:00:02+00:00",
            "native_authority": "codex-app-server",
            "native_session_id": "session",
            "native_thread_id": "thread",
            "native_turn_id": "turn",
            "terminal_status": "completed",
            "content_source": "native_app_server_completed_turn",
            "answer_provenance": "native_final_answer",
            "semantic_complete": True,
            "freshness_proven": True,
            "assistant_owned": True,
            "semantic_content": "answer",
        },
    )

    reconciled = _reconcile_native_artifacts(
        output=output,
        invocation_id="invocation-1",
        started_at="2026-10-18T10:00:03+00:00",
        request_fingerprint_value=fingerprint,
        logical_operation_id="operation-1",
        resume=False,
    )
    assert reconciled is not None
    assert reconciled["execution"]["state"] == "completed"
    assert reconciled["logical_operation_id"] == "operation-1"
    assert reconciled["request_fingerprint"] == fingerprint

    with pytest.raises(runtime.NativeAppServerError, match="request fingerprint"):
        _reconcile_native_artifacts(
            output=output,
            invocation_id="invocation-2",
            started_at="2026-10-18T10:00:04+00:00",
            request_fingerprint_value="0" * 64,
            logical_operation_id="operation-1",
            resume=True,
        )

    legacy_fields = {
        "task_sha256": "task",
        "repository_identity": "repo",
        "git_revision": "rev",
        "execution_role": "secretary",
        "model_identity": "model",
        "runtime_grant_digest": "",
    }
    legacy_fingerprint = runtime.hashlib.sha256(
        json.dumps(legacy_fields, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    ).hexdigest()
    assert legacy_fingerprint != fingerprint
    for path in (
        native_binding_path(output),
        native_submission_path(output),
        native_result_path(output),
    ):
        path.write_text(path.read_text(encoding="utf-8").replace(fingerprint, legacy_fingerprint), encoding="utf-8")

    with pytest.raises(runtime.NativeAppServerError, match="request fingerprint"):
        _reconcile_native_artifacts(
            output=output,
            invocation_id="invocation-3",
            started_at="2026-10-18T10:00:05+00:00",
            request_fingerprint_value=fingerprint,
            logical_operation_id="operation-1",
            resume=True,
        )


def test_reconcile_native_artifacts_rejects_unattributed_existing_output(
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    fingerprint = "a" * 64
    output = tmp_path / "normal.json"
    runtime.publish_native_binding(
        runtime.native_binding_path(output),
        {
            "schema": runtime.NATIVE_BINDING_SCHEMA,
            "attempt_id": "attempt-1",
            "logical_operation_id": "operation-1",
            "request_fingerprint": fingerprint,
            "native_session_id": "session",
            "native_thread_id": "thread",
            "pre_submit_boundary": "fresh-zero-prior-turn",
            "created_at": "2026-10-18T10:00:00+00:00",
        },
    )
    runtime.publish_native_submission(
        runtime.native_submission_path(output),
        {
            "schema": runtime.NATIVE_SUBMISSION_SCHEMA,
            "attempt_id": "attempt-1",
            "logical_operation_id": "operation-1",
            "request_fingerprint": fingerprint,
            "native_session_id": "session",
            "native_thread_id": "thread",
            "native_turn_id": "turn",
            "accepted_at": "2026-10-18T10:00:01+00:00",
            "status": "accepted",
        },
    )
    runtime.publish_native_result(
        runtime.native_result_path(output),
        {
            "schema": runtime.NATIVE_RESULT_SCHEMA,
            "producer": "codex-native",
            "attempt_id": "attempt-1",
            "logical_operation_id": "operation-1",
            "request_fingerprint": fingerprint,
            "observed_at": "2026-10-18T10:00:02+00:00",
            "native_authority": "codex-app-server",
            "native_session_id": "session",
            "native_thread_id": "thread",
            "native_turn_id": "turn",
            "terminal_status": "completed",
            "content_source": "native_app_server_completed_turn",
            "answer_provenance": "native_final_answer",
            "semantic_complete": True,
            "freshness_proven": True,
            "assistant_owned": True,
            "semantic_content": "answer",
        },
    )

    for payload in (
        {"logical_operation_id": "other", "request_fingerprint": fingerprint},
        {"logical_operation_id": "operation-1"},
        {
            "logical_operation_id": "operation-1",
            "request_fingerprint": fingerprint,
            "attempt_id": "attempt-other",
        },
        {
            "logical_operation_id": "operation-1",
            "request_fingerprint": fingerprint,
            "preflight": {"attempt_id": "attempt-other"},
        },
    ):
        original = json.dumps(payload).encode("utf-8")
        output.write_bytes(original)

        with pytest.raises(runtime.NativeAppServerError) as exc_info:
            runtime._reconcile_native_artifacts(
                output=output,
                invocation_id="invocation-1",
                started_at="2026-10-18T10:00:03+00:00",
                request_fingerprint_value=fingerprint,
                logical_operation_id="operation-1",
                resume=True,
            )

        assert exc_info.value.failure_kind == "NATIVE_RESULT_CONFLICT"
        assert output.read_bytes() == original


def test_reconcile_native_artifacts_rejects_logical_operation_mismatch(
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    fingerprint = "a" * 64
    for path, payload in (
        (
            runtime.native_binding_path(output),
            {
                "schema": "secretary-native-binding.v3",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "native_session_id": "session",
                "native_thread_id": "thread",
                "pre_submit_boundary": "fresh-zero-prior-turn",
                "created_at": "2026-10-18T10:00:00+00:00",
            },
        ),
        (
            runtime.native_submission_path(output),
            {
                "schema": "secretary-native-submission.v3",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "native_session_id": "session",
                "native_thread_id": "thread",
                "native_turn_id": "turn",
                "accepted_at": "2026-10-18T10:00:01+00:00",
                "status": "accepted",
            },
        ),
        (
            runtime.native_result_path(output),
            {
                "schema": "secretary-native-result.v3",
                "producer": "codex-native",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "observed_at": "2026-10-18T10:00:02+00:00",
                "native_authority": "codex-app-server",
                "native_session_id": "session",
                "native_thread_id": "thread",
                "native_turn_id": "turn",
                "terminal_status": "completed",
                "content_source": "native_app_server_completed_turn",
                "answer_provenance": "native_final_answer",
                "semantic_complete": True,
                "freshness_proven": True,
                "assistant_owned": True,
                "semantic_content": "answer",
                "content_sha256": runtime.hashlib.sha256(b"answer").hexdigest(),
                "session": "codex-app-server",
                "pane": "native",
                "agent_name": "normal-secretary",
            },
        ),
    ):
        if path.name.endswith("native-result.json"):
            runtime.publish_native_result(path, payload)
        elif path.name.endswith("native-binding.json"):
            runtime.publish_native_binding(path, payload)
        else:
            runtime.publish_native_submission(path, payload)

    with pytest.raises(runtime.NativeAppServerError, match="logical_operation"):
        runtime._reconcile_native_artifacts(
            output=output,
            invocation_id="invocation-1",
            started_at="2026-10-18T10:00:03+00:00",
            request_fingerprint_value=fingerprint,
            logical_operation_id="operation-2",
            resume=True,
        )


def test_reconcile_native_artifacts_blocks_unknown_identity_reuse(tmp_path: Path) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    runtime.native_result_path(output).write_text("{}\n", encoding="utf-8")

    with pytest.raises(runtime.NativeAppServerError, match="identity is unknown"):
        runtime._reconcile_native_artifacts(
            output=output,
            invocation_id="invocation-1",
            started_at="2026-10-18T10:00:03+00:00",
            request_fingerprint_value="a" * 64,
            logical_operation_id="operation-1",
            reuse_allowed=False,
            resume=True,
        )


def test_reconcile_native_artifacts_discovers_operation_identity_on_resume(
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    fingerprint = "a" * 64
    for path, payload in (
        (
            runtime.native_binding_path(output),
            {
                "schema": "secretary-native-binding.v3",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "native_session_id": "session",
                "native_thread_id": "thread",
                "pre_submit_boundary": "fresh-zero-prior-turn",
                "created_at": "2026-10-18T10:00:00+00:00",
            },
        ),
        (
            runtime.native_submission_path(output),
            {
                "schema": "secretary-native-submission.v3",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "native_session_id": "session",
                "native_thread_id": "thread",
                "native_turn_id": "turn",
                "accepted_at": "2026-10-18T10:00:01+00:00",
                "status": "accepted",
            },
        ),
    ):
        if path == runtime.native_result_path(output):
            runtime.publish_native_result(path, payload)
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")

    discovered = runtime._discover_native_logical_operation(output)

    assert discovered == "operation-1"


def test_discover_native_logical_operation_treats_missing_evidence_as_absent(
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    assert runtime._discover_native_logical_operation(tmp_path / "normal.json") is None


@pytest.mark.parametrize("occupant", ["symlink", "oversized", "malformed", "disappeared"])
def test_discover_native_logical_operation_fails_closed_for_uncertain_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    occupant: str,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    binding_path = runtime.native_binding_path(output)
    payload = {
        "schema": runtime.NATIVE_BINDING_SCHEMA,
        "attempt_id": "attempt-1",
        "logical_operation_id": "operation-1",
        "request_fingerprint": "a" * 64,
        "native_session_id": "session",
        "native_thread_id": "thread",
    }
    if occupant == "symlink":
        target = tmp_path / "target.json"
        target.write_text(json.dumps(payload), encoding="utf-8")
        binding_path.symlink_to(target)
    elif occupant == "oversized":
        binding_path.write_bytes(b"x" * (runtime.NATIVE_RESULT_MAX_BYTES + 1))
    elif occupant == "malformed":
        binding_path.write_text("{not-json", encoding="utf-8")
    else:
        binding_path.write_text(json.dumps(payload), encoding="utf-8")
        monkeypatch.setattr(runtime, "_read_bounded_regular_file", lambda *args, **kwargs: None)

    with pytest.raises(runtime.NativeAppServerError) as exc_info:
        runtime._discover_native_logical_operation(output)

    assert exc_info.value.failure_kind == "NATIVE_RESULT_CONFLICT"


def test_discover_native_logical_operation_rejects_special_file(
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO creation is unavailable on this platform")
    output = tmp_path / "normal.json"
    os.mkfifo(runtime.native_binding_path(output))

    with pytest.raises(runtime.NativeAppServerError) as exc_info:
        runtime._discover_native_logical_operation(output)

    assert exc_info.value.failure_kind == "NATIVE_RESULT_CONFLICT"


def test_native_resume_binds_discovered_operation_before_request_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    runtime.native_binding_path(output).write_text(
        json.dumps(
            {
                "schema": "secretary-native-binding.v3",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": "a" * 64,
                "native_session_id": "session",
                "native_thread_id": "thread",
                "pre_submit_boundary": "fresh-zero-prior-turn",
                "created_at": "2026-10-18T10:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    seen: dict[str, object] = {}

    def fake_resolve(
        request: SecretaryNormalRequest,
        environment: object,
        *,
        output: Path | None = None,
    ) -> object:
        seen["logical_operation_id"] = request.logical_operation_id
        raise runtime.NativeAppServerError("stop after binding", failure_kind="NATIVE_RESULT_CONFLICT")

    monkeypatch.setattr(runtime, "_resolve_normal_request", fake_resolve)

    runtime._run_normal_via_native_app_server(
        normal_request(worktree=tmp_path, resume=True),
        output=output,
        environment={},
        invocation_id="invocation-1",
    )

    assert seen["logical_operation_id"] == "operation-1"


def test_native_v3_projection_ignores_legacy_semantic_sources() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_native_v3_outcome(
        invocation_id="invocation-1",
        persisted={
            "result_reference": "native-result://turn-1",
            "semantic_content": "canonical native answer",
        },
        payload={
            "assignment": {
                "attempt_id": "attempt-1",
                "session": "codex-app-server",
                "pane": "native",
                "agent_name": "normal-secretary",
                "execution": {"state": "completed"},
                "task_result": {
                    "state": "reported_failed",
                    "assignment_id": "wrong-assignment",
                    "attempt_id": "wrong-attempt",
                    "producer": "terminal-screen",
                    "content": "legacy conflicting answer",
                },
            }
        },
        started_at="2026-10-18T10:00:00+00:00",
        finished_at="2026-10-18T10:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "reference": "native-result://turn-1",
        "content": "canonical native answer",
    }


def test_rejected_native_invocation_does_not_overwrite_existing_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    prior = {"invocation_id": "prior", "failure_kind": "authoritative"}
    output.write_text(json.dumps(prior), encoding="utf-8")
    runtime.native_result_path(output).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "_read_only_workspace_identity", lambda _, output=None: (False, None, ()))

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=output)

    assert result["failure_kind"] == "NATIVE_RESULT_CONFLICT"
    assert json.loads(output.read_text(encoding="utf-8")) == prior


def test_foreign_output_without_sidecars_is_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    prior_bytes = b'{"foreign":true}\n'
    output.write_bytes(prior_bytes)
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "_read_only_workspace_identity", lambda _, output=None: (False, None, ()))
    monkeypatch.setattr(runtime.shutil, "which", lambda _: pytest.fail("foreign output must not launch"))

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=output)

    assert result["failure_kind"] == "NATIVE_RESULT_CONFLICT"
    assert output.read_bytes() == prior_bytes


@pytest.mark.parametrize("occupant", ["directory", "symlink"])
def test_non_regular_output_occupants_are_foreign_and_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    occupant: str,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    if occupant == "directory":
        output.mkdir()
    else:
        target = tmp_path / "foreign-target.json"
        target.write_bytes(b'{"foreign":true}\n')
        output.symlink_to(target)
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "_read_only_workspace_identity", lambda _, output=None: (False, None, ()))
    monkeypatch.setattr(runtime.shutil, "which", lambda _: pytest.fail("occupied namespace must not launch"))

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=output)

    assert result["failure_kind"] == "NATIVE_RESULT_CONFLICT"


def test_complete_current_evidence_with_unknown_identity_does_not_reconcile_or_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    normal = normal_request(
        worktree=tmp_path,
        repository_identity="repo",
        git_revision="head-1",
        model_identity="model",
        runtime_grant_digest="grant",
        logical_operation_id="operation-existing",
    )
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(
        runtime,
        "_read_only_workspace_identity",
        lambda _, output=None: (True, None, ("workspace_identity",)),
    )
    resolved = runtime._resolve_normal_request(normal, {}, output=output)
    fingerprint = resolved.request_fingerprint
    binding = {
        "schema": runtime.NATIVE_BINDING_SCHEMA,
        "attempt_id": "attempt-existing",
        "logical_operation_id": "operation-existing",
        "request_fingerprint": fingerprint,
        "native_session_id": "session-existing",
        "native_thread_id": "thread-existing",
        "pre_submit_boundary": "fresh-zero-prior-turn",
        "created_at": "2026-10-18T10:00:00+00:00",
    }
    submission = {
        "schema": runtime.NATIVE_SUBMISSION_SCHEMA,
        "attempt_id": "attempt-existing",
        "logical_operation_id": "operation-existing",
        "request_fingerprint": fingerprint,
        "native_session_id": "session-existing",
        "native_thread_id": "thread-existing",
        "native_turn_id": "turn-existing",
        "accepted_at": "2026-10-18T10:00:01+00:00",
        "status": "accepted",
    }
    result_payload = {
        "schema": runtime.NATIVE_RESULT_SCHEMA,
        "producer": runtime.NATIVE_RESULT_PRODUCER,
        "attempt_id": "attempt-existing",
        "logical_operation_id": "operation-existing",
        "request_fingerprint": fingerprint,
        "observed_at": "2026-10-18T10:00:02+00:00",
        "native_authority": runtime.NATIVE_APP_SERVER_AUTHORITY,
        "native_session_id": "session-existing",
        "native_thread_id": "thread-existing",
        "native_turn_id": "turn-existing",
        "terminal_status": "completed",
        "content_source": "native_app_server_completed_turn",
        "answer_provenance": "native_final_answer",
        "semantic_complete": True,
        "freshness_proven": True,
        "assistant_owned": True,
        "semantic_content": "already published",
    }
    runtime.publish_native_binding(runtime.native_binding_path(output), binding)
    runtime.publish_native_submission(runtime.native_submission_path(output), submission)
    runtime.publish_native_result(runtime.native_result_path(output), result_payload)
    sidecar_bytes = {
        path: path.read_bytes()
        for path in (
            runtime.native_binding_path(output),
            runtime.native_submission_path(output),
            runtime.native_result_path(output),
        )
    }
    monkeypatch.setattr(runtime.shutil, "which", lambda _: pytest.fail("unknown identity must not launch"))

    result = runtime.run_normal(normal, output=output)

    assert result["failure_kind"] == "NATIVE_RESULT_CONFLICT"
    assert result["recovery_required"] is True
    assert not output.exists()
    assert {path: path.read_bytes() for path in sidecar_bytes} == sidecar_bytes


def test_current_binding_without_result_requires_recovery_without_starting_turn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    runtime.publish_native_binding(
        runtime.native_binding_path(output),
        {
            "schema": runtime.NATIVE_BINDING_SCHEMA,
            "attempt_id": "attempt-existing",
            "logical_operation_id": "operation-existing",
            "request_fingerprint": "a" * 64,
            "native_session_id": "session-existing",
            "native_thread_id": "thread-existing",
            "pre_submit_boundary": "fresh-zero-prior-turn",
            "created_at": "2026-10-18T10:00:00+00:00",
        },
    )
    monkeypatch.setattr(runtime, "CodexAppServerClient", lambda *args, **kwargs: pytest.fail("must not start a turn"))

    with pytest.raises(runtime.NativeAppServerError) as error:
        runtime._reconcile_native_artifacts(
            output=output,
            invocation_id="invocation-1",
            started_at="2026-10-18T10:00:03+00:00",
            request_fingerprint_value="a" * 64,
            logical_operation_id="operation-existing",
            resume=False,
        )

    assert error.value.failure_kind == "NATIVE_SUBMISSION_FAILED"


def test_binding_claim_race_does_not_persist_losing_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime
    from scripts.project_os_runtime.codex_app_server import NativeThread

    output = tmp_path / "normal.json"
    binding_path = runtime.native_binding_path(output)
    winner_bytes = b'{"winner":true}\n'
    binding_path.write_bytes(winner_bytes)
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "_read_only_workspace_identity", lambda _, output=None: (False, None, ()))
    monkeypatch.setattr(runtime, "_reconcile_native_artifacts", lambda **_: None)
    monkeypatch.setattr(runtime.shutil, "which", lambda name: "codex.exe" if name == "codex" else None)
    monkeypatch.setattr(runtime, "_configured_provider", lambda _: runtime.SECRETARY_PROVIDER)

    class FakeNativeClient:
        retirement_evidence = {"state": "retired"}

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "FakeNativeClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def start_thread(self, *, model: str | None = None) -> NativeThread:
            return NativeThread("thread", "session", True, "fresh-zero-prior-turn")

    monkeypatch.setattr(runtime, "CodexAppServerClient", FakeNativeClient)
    monkeypatch.setattr(
        runtime,
        "publish_native_binding",
        lambda *args, **kwargs: (_ for _ in ()).throw(runtime.NativeResultConflictError("claim lost")),
    )

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=output)

    assert result["failure_kind"] == "NATIVE_RESULT_CONFLICT"
    assert not output.exists()
    assert binding_path.read_bytes() == winner_bytes


def test_reconcile_native_artifacts_rejects_mismatched_retirement_identity(
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    fingerprint = "a" * 64
    for path, payload in (
        (
            runtime.native_binding_path(output),
            {
                "schema": "secretary-native-binding.v3",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "native_session_id": "session",
                "native_thread_id": "thread",
                "pre_submit_boundary": "fresh-zero-prior-turn",
                "created_at": "2026-10-18T10:00:00+00:00",
            },
        ),
        (
            runtime.native_submission_path(output),
            {
                "schema": "secretary-native-submission.v3",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "native_session_id": "session",
                "native_thread_id": "thread",
                "native_turn_id": "turn",
                "accepted_at": "2026-10-18T10:00:01+00:00",
                "status": "accepted",
            },
        ),
        (
            runtime.native_result_path(output),
            {
                "schema": "secretary-native-result.v3",
                "producer": "codex-native",
                "attempt_id": "attempt-1",
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "observed_at": "2026-10-18T10:00:02+00:00",
                "native_authority": "codex-app-server",
                "native_session_id": "session",
                "native_thread_id": "thread",
                "native_turn_id": "turn",
                "terminal_status": "completed",
                "content_source": "native_app_server_completed_turn",
                "answer_provenance": "native_final_answer",
                "semantic_complete": True,
                "freshness_proven": True,
                "assistant_owned": True,
                "semantic_content": "answer",
                "content_sha256": runtime.hashlib.sha256(b"answer").hexdigest(),
                "session": "codex-app-server",
                "pane": "native",
                "agent_name": "normal-secretary",
            },
        ),
    ):
        path.write_text(json.dumps(payload), encoding="utf-8")
    result_path = runtime.native_result_path(output)
    runtime.publish_native_result(result_path, json.loads(result_path.read_text(encoding="utf-8")))
    output.write_text(
        json.dumps(
            {
                "logical_operation_id": "operation-1",
                "request_fingerprint": fingerprint,
                "attempt_id": "attempt-1",
                "preflight": {
                    "attempt_id": "attempt-1",
                    "retirement": {
                        "state": "retired",
                        "logical_operation_id": "operation-1",
                        "request_fingerprint": fingerprint,
                        "attempt_id": "attempt-other",
                        "native_session_id": "session",
                        "native_thread_id": "thread",
                        "native_turn_id": "turn",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    original = output.read_bytes()

    with pytest.raises(runtime.NativeAppServerError) as exc_info:
        runtime._reconcile_native_artifacts(
            output=output,
            invocation_id="invocation-1",
            started_at="2026-10-18T10:00:03+00:00",
            request_fingerprint_value=fingerprint,
            logical_operation_id="operation-1",
            resume=True,
        )

    assert exc_info.value.failure_kind == "NATIVE_RESULT_CONFLICT"
    assert output.read_bytes() == original


def test_resolved_request_marks_unknown_identity_and_disables_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "_configured_provider", lambda _: runtime.SECRETARY_PROVIDER)
    resolved = runtime._resolve_normal_request(normal_request(worktree=tmp_path), {})

    assert "model_identity" in resolved.unknown_fields
    assert "runtime_grant_digest" not in resolved.unknown_fields
    assert resolved.runtime_grant_digest == "not_applicable"
    assert resolved.reuse_allowed is False


def test_resolved_request_uses_profile_model_and_git_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "normal.toml").write_text(
        'model_provider = "9router"\nmodel = "combo-normal"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "git-head"))
    monkeypatch.setattr(runtime, "_canonical_repository_identity", lambda _: "origin/repo")
    monkeypatch.setattr(runtime, "_read_only_workspace_identity", lambda _, output=None: (False, None, ()))

    resolved = runtime._resolve_normal_request(
        normal_request(worktree=tmp_path, git_revision="stale", repository_identity="stale-repo"),
        {},
    )

    assert resolved.repository_identity == "origin/repo"
    assert resolved.git_revision == "git-head"
    assert resolved.model_identity == "combo-normal"
    assert resolved.runtime_grant_digest == "not_applicable"
    assert resolved.reuse_allowed is True


def test_configured_provider_requires_active_secretary_route(tmp_path: Path) -> None:
    import scripts.secretary_live_runtime as runtime

    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text("{}", encoding="utf-8")
    (codex_home / "config.toml").write_text(
        'model_provider = "other"\n[model_providers.9router]\nbase_url = "http://localhost"\n',
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="active provider must be 9router"):
        runtime._configured_provider(codex_home)


def test_configured_provider_requires_secretary_mapping(tmp_path: Path) -> None:
    import scripts.secretary_live_runtime as runtime

    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text("{}", encoding="utf-8")
    (codex_home / "config.toml").write_text(
        'model_provider = "9router"\n[model_providers.other]\nbase_url = "http://localhost"\n',
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="provider 9router unavailable"):
        runtime._configured_provider(codex_home)


def test_run_normal_resolves_git_anchor_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.secretary_live_runtime as runtime

    calls = 0

    def read_anchor(_: Path) -> tuple[Path, str]:
        nonlocal calls
        calls += 1
        return tmp_path, "head-1"

    monkeypatch.setattr(runtime, "_read_only_git_anchor", read_anchor)
    monkeypatch.setattr(runtime, "_read_only_workspace_identity", lambda _, output=None: (False, None, ()))
    monkeypatch.setattr(runtime, "_configured_provider", lambda _: runtime.SECRETARY_PROVIDER)
    monkeypatch.setattr(runtime.shutil, "which", lambda name: "codex.exe" if name == "codex" else None)

    class FailingNativeClient:
        retirement_evidence = {"state": "retired"}

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "FailingNativeClient":
            raise runtime.NativeAppServerError(
                "stop after resolution", failure_kind="NATIVE_INITIALIZATION_FAILED"
            )

        def __exit__(self, *args: object) -> None:
            pass

    monkeypatch.setattr(runtime, "CodexAppServerClient", FailingNativeClient)

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=tmp_path / "normal.json")

    assert calls == 1
    assert result["failure_kind"] == "NATIVE_INITIALIZATION_FAILED"


def test_resolved_request_keeps_operation_and_reuse_state_out_of_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "git-head"))
    monkeypatch.setattr(runtime, "_read_only_workspace_identity", lambda _: (False, None, ()))

    first = runtime._resolve_normal_request(
        normal_request(
            worktree=tmp_path,
            repository_identity="repo",
            model_identity="model",
            logical_operation_id="operation-1",
        ), {}
    )
    second = runtime._resolve_normal_request(
        normal_request(
            worktree=tmp_path,
            repository_identity="repo",
            model_identity="model",
            logical_operation_id="operation-2",
        ), {}
    )

    assert first.request_fingerprint == second.request_fingerprint
    assert first.logical_operation_id != second.logical_operation_id
    assert first.reuse_allowed is True


def test_resolved_request_uses_deterministic_dirty_workspace_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "git-head"))
    monkeypatch.setattr(
        runtime,
        "_read_only_workspace_identity",
        lambda _, output=None: (True, "change-digest", ()),
    )

    resolved = runtime._resolve_normal_request(
        normal_request(worktree=tmp_path, repository_identity="repo", model_identity="model"), {}
    )

    assert resolved.workspace_dirty is True
    assert resolved.workspace_change_digest == "change-digest"
    assert resolved.reuse_allowed is True
    assert resolved.request_fingerprint != runtime.request_fingerprint(
        {
            "task_sha256": resolved.task_sha256,
            "repository_identity": resolved.repository_identity,
            "git_revision": resolved.git_revision,
            "execution_role": resolved.execution_role,
            "provider_identity": resolved.provider_identity,
            "model_identity": resolved.model_identity,
            "runtime_grant_digest": resolved.runtime_grant_digest,
        }
    )


def test_workspace_identity_excludes_all_native_runtime_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    status = b"\0".join(
        [
            b"?? normal.json",
            b"?? normal.json.native-binding.json",
            b"?? normal.json.native-submission.json",
            b"?? normal.json.native-result.json",
            b"?? .normal.json.123.tmp",
            b"?? .normal.json.native-binding.json.abc.tmp",
            b"?? .normal.json.native-submission.json.release.lock",
            b"?? .normal.json.native-result.json.release.lock",
            b"?? input.txt",
            b"",
        ]
    )
    (tmp_path / "input.txt").write_text("task input", encoding="utf-8")

    def bounded_output(command: object, **_: object) -> tuple[bytes, None]:
        return (status if "status" in list(command) else b"tracked diff", None)

    monkeypatch.setattr(runtime, "_bounded_git_output", bounded_output)

    dirty, digest, unknown = runtime._read_only_workspace_identity(tmp_path, output)

    assert dirty is True
    assert digest is not None
    assert unknown == ()

    status_without_runtime = b"?? input.txt\0"
    monkeypatch.setattr(
        runtime,
        "_bounded_git_output",
        lambda command, **_: (status_without_runtime if "status" in list(command) else b"tracked diff", None),
    )
    _, expected_digest, _ = runtime._read_only_workspace_identity(tmp_path, output)
    assert digest == expected_digest


def test_workspace_identity_does_not_exclude_symlink_alias_to_runtime_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    alias = tmp_path / "alias.json"
    alias.symlink_to(output)
    monkeypatch.setattr(
        runtime,
        "_bounded_git_output",
        lambda command, **_: (b"?? alias.json\0" if "status" in list(command) else b"", None),
    )

    dirty, digest, unknown = runtime._read_only_workspace_identity(tmp_path, output)

    assert dirty is True
    assert digest is None
    assert unknown == ("workspace_identity",)


def test_workspace_identity_disables_reuse_for_special_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO creation is unavailable on this platform")
    fifo = tmp_path / "input.fifo"
    os.mkfifo(fifo)
    monkeypatch.setattr(
        runtime,
        "_bounded_git_output",
        lambda command, **_: (b"?? input.fifo\0" if "status" in list(command) else b"", None),
    )

    dirty, digest, unknown = runtime._read_only_workspace_identity(tmp_path)

    assert dirty is True
    assert digest is None
    assert unknown == ("workspace_identity",)


def test_workspace_identity_disables_reuse_when_git_output_exceeds_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "_bounded_git_output",
        lambda command, **_: (None, "output_limit"),
    )

    dirty, digest, unknown = runtime._read_only_workspace_identity(tmp_path)

    assert dirty is False
    assert digest is None
    assert unknown == ("workspace_identity",)


def test_workspace_identity_disables_reuse_for_large_untracked_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    large_file = tmp_path / "large.bin"
    large_file.write_bytes(b"x" * (runtime._WORKSPACE_UNTRACKED_FILE_MAX_BYTES + 1))
    monkeypatch.setattr(
        runtime,
        "_bounded_git_output",
        lambda command, **_: (b"?? large.bin\0" if "status" in list(command) else b"", None),
    )

    dirty, digest, unknown = runtime._read_only_workspace_identity(tmp_path)

    assert dirty is True
    assert digest is None
    assert unknown == ("workspace_identity",)


def test_bounded_git_output_stops_after_output_limit() -> None:
    import scripts.secretary_live_runtime as runtime

    output, error = runtime._bounded_git_output(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000)"],
        max_bytes=1024,
        timeout_seconds=2,
    )

    assert output is None
    assert error == "output_limit"


def test_tracked_runtime_path_is_rejected_before_native_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    (tmp_path / ".git").mkdir()
    output = tmp_path / "normal.json"
    monkeypatch.setattr(runtime, "_bounded_git_output", lambda *args, **kwargs: (b"normal.json\0", None))

    with pytest.raises(runtime.LaunchBlocked, match="runtime output or sidecar path"):
        runtime._reject_tracked_runtime_paths(tmp_path, output)


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


def test_run_normal_native_app_server_uses_bound_turn_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "_configured_provider", lambda _: runtime.SECRETARY_PROVIDER)
    monkeypatch.setattr(runtime.shutil, "which", lambda name: "codex.exe" if name == "codex" else None)
    monkeypatch.setattr(runtime, "_prepare_herdr_target", lambda *args, **kwargs: pytest.fail("normal path must not use Herdr"))
    from scripts.project_os_runtime.codex_app_server import NativeThread, NativeTurn, NativeTurnEvidence

    class FakeNativeClient:
        retirement_evidence = {"state": "retired", "method": "fake"}

        def __init__(self, *args: object, **kwargs: object) -> None:
            return None

        def __enter__(self) -> "FakeNativeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def start_thread(self, *, model: str | None = None) -> NativeThread:
            assert model == "<unknown:model_identity>"
            return NativeThread("thread-1", "session-1", True, "fresh-zero-prior-turn")

        def start_turn(self, thread: NativeThread, task: str) -> NativeTurn:
            assert thread.thread_id == "thread-1"
            assert task
            return NativeTurn("thread-1", "turn-1")

        def wait_for_turn(self, turn: NativeTurn) -> NativeTurnEvidence:
            return NativeTurnEvidence("thread-1", "turn-1", "completed", (), "native answer")

    monkeypatch.setattr(runtime, "CodexAppServerClient", FakeNativeClient)
    result = runtime.run_normal(normal_request(worktree=tmp_path), output=tmp_path / "normal.json")

    assert result["result"]["state"] == "reported"
    assert result["resource"] == {"state": "settled", "reuse_blocked": False}
    assert result["resource_inventory"]["state"] == "settled"
    assert result["resource_inventory"]["reuse_blocked"] is False
    assert result["resource_inventory"]["recovery_required"] is False
    persisted = json.loads((tmp_path / "normal.json.native-result.json").read_text(encoding="utf-8"))
    binding = json.loads((tmp_path / "normal.json.native-binding.json").read_text(encoding="utf-8"))
    assert persisted["native_turn_id"] == "turn-1"
    assert persisted["native_authority"] == runtime.NATIVE_APP_SERVER_AUTHORITY
    assert "session" not in persisted
    assert "pane" not in persisted
    assert "agent_name" not in persisted
    assert binding["provider"] == runtime.SECRETARY_PROVIDER
    assert "transport" not in binding
    assert binding["model"] == "<unknown:model_identity>"


def test_native_client_entry_failure_preserves_retirement_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "_configured_provider", lambda _: runtime.SECRETARY_PROVIDER)
    monkeypatch.setattr(runtime.shutil, "which", lambda name: "codex.exe" if name == "codex" else None)

    class FailingNativeClient:
        retirement_evidence = {"state": "retired", "method": "entry-failure-cleanup"}

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "FailingNativeClient":
            raise runtime.NativeAppServerError(
                "native initialization failed",
                failure_kind="NATIVE_INITIALIZATION_FAILED",
            )

        def __exit__(self, *args: object) -> None:
            pass

    monkeypatch.setattr(runtime, "CodexAppServerClient", FailingNativeClient)
    output = tmp_path / "normal.json"

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=output)

    assert result["failure_kind"] == "NATIVE_INITIALIZATION_FAILED"
    assert result["preflight"]["retirement"]["state"] == "retired"
    assert result["recovery_required"] is False
    assert not output.exists()


def test_run_normal_native_result_survives_unverified_retirement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime.shutil, "which", lambda name: "codex.exe" if name == "codex" else None)
    monkeypatch.setattr(runtime, "_configured_provider", lambda _: runtime.SECRETARY_PROVIDER)

    from scripts.project_os_runtime.codex_app_server import NativeThread, NativeTurn, NativeTurnEvidence

    class FakeNativeClient:
        retirement_evidence = {"state": "unknown", "method": "kill", "error": "still alive"}

        def __init__(self, *args: object, **kwargs: object) -> None:
            return None

        def __enter__(self) -> "FakeNativeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def start_thread(self, *, model: str | None = None) -> NativeThread:
            assert model == "<unknown:model_identity>"
            return NativeThread("thread-1", "session-1", True, "fresh-zero-prior-turn")

        def start_turn(self, thread: NativeThread, task: str) -> NativeTurn:
            return NativeTurn(thread.thread_id, "turn-1")

        def wait_for_turn(self, turn: NativeTurn) -> NativeTurnEvidence:
            return NativeTurnEvidence(turn.thread_id, turn.turn_id, "completed", (), "native answer")

    monkeypatch.setattr(runtime, "CodexAppServerClient", FakeNativeClient)

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=tmp_path / "normal.json")

    assert result["result"]["state"] == "reported"
    assert result["result"]["status"] == "completed"
    assert result["result"]["content"] == "native answer"
    assert result["failure_kind"] == "NATIVE_RETIREMENT_UNVERIFIED"
    assert result["recovery_required"] is True
    assert result["resource"] == {"state": "quarantined", "reuse_blocked": True}
    assert result["finalization_outcome"] == {"state": "recovery_required", "recovery_required": True}
    assert result["preflight"]["retirement"]["state"] == "unknown"


def test_native_run_reconciles_published_result_without_starting_new_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    normal = normal_request(
        worktree=tmp_path,
        repository_identity="repo",
        git_revision="head-1",
        model_identity="model",
        runtime_grant_digest="grant",
    )
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "_read_only_workspace_identity", lambda _, output=None: (False, None, ()))
    fingerprint = runtime._resolve_normal_request(normal, {}).request_fingerprint
    runtime.publish_native_binding(
        runtime.native_binding_path(output),
        {
            "schema": "secretary-native-binding.v3",
            "attempt_id": "attempt-existing",
            "logical_operation_id": "operation-existing",
            "request_fingerprint": fingerprint,
            "native_session_id": "session-existing",
            "native_thread_id": "thread-existing",
            "pre_submit_boundary": "fresh-zero-prior-turn",
            "created_at": "2026-10-18T10:00:00+00:00",
            "transport": {"session": "codex-app-server", "pane": "native", "agent_name": "normal-secretary"},
        },
    )
    runtime.publish_native_submission(
        runtime.native_submission_path(output),
        {
            "schema": "secretary-native-submission.v3",
            "attempt_id": "attempt-existing",
            "logical_operation_id": "operation-existing",
            "request_fingerprint": fingerprint,
            "native_session_id": "session-existing",
            "native_thread_id": "thread-existing",
            "native_turn_id": "turn-existing",
            "accepted_at": "2026-10-18T10:00:00+00:00",
            "status": "accepted",
        },
    )
    persisted = {
        "schema": "secretary-native-result.v3",
        "producer": runtime.NATIVE_RESULT_PRODUCER,
        "attempt_id": "attempt-existing",
        "logical_operation_id": "operation-existing",
        "request_fingerprint": fingerprint,
        "observed_at": "2026-10-18T10:00:00+00:00",
        "native_authority": runtime.NATIVE_APP_SERVER_AUTHORITY,
        "native_session_id": "session-existing",
        "native_thread_id": "thread-existing",
        "native_turn_id": "turn-existing",
        "terminal_status": "completed",
        "content_source": "native_app_server_completed_turn",
        "answer_provenance": "native_final_answer",
        "semantic_complete": True,
        "freshness_proven": True,
        "assistant_owned": True,
        "semantic_content": "already published",
        "session": "codex-app-server",
        "pane": "native",
        "agent_name": "normal-secretary",
    }
    runtime.publish_native_result(runtime.native_result_path(output), persisted)
    normal = normal_request(
        worktree=tmp_path,
        repository_identity="repo",
        git_revision="head-1",
        model_identity="model",
        runtime_grant_digest="grant",
        logical_operation_id="operation-existing",
        resume=True,
    )
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime.shutil, "which", lambda _: pytest.fail("client must not start"))

    result = runtime.run_normal(normal, output=output)

    assert result["result"]["state"] == "reported"
    assert result["preflight"]["reconciled"] is True
    assert result["preflight"]["attempt_id"] == "attempt-existing"


def test_native_run_does_not_resubmit_uncertain_submission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.secretary_live_runtime as runtime

    output = tmp_path / "normal.json"
    runtime.native_submission_path(output).write_text(
        json.dumps({"schema": "secretary-native-submission.v1"}), encoding="utf-8"
    )
    monkeypatch.setattr(runtime, "_read_only_git_anchor", lambda _: (tmp_path, "head-1"))
    monkeypatch.setattr(runtime, "CodexAppServerClient", lambda *args, **kwargs: pytest.fail("must not resubmit"))

    result = runtime.run_normal(normal_request(worktree=tmp_path), output=output)

    assert result["failure_kind"] == "NATIVE_SUBMISSION_FAILED"
    assert result["recovery_required"] is True


def test_native_not_required_cleanup_does_not_quarantine_empty_inventory() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={"assignment": {"attempt_id": "attempt-1", "execution": {"state": "completed"}}},
        observation={"state": "done", "cleanup": {"state": "not_required"}},
        started_at="2026-10-18T10:00:00+00:00",
        finished_at="2026-10-18T10:00:01+00:00",
    )

    assert result["resource"] == {"state": "settled", "reuse_blocked": False}
    assert result["resource_inventory"]["resources"] == []
    assert result["resource_inventory"]["state"] == "settled"
    assert result["resource_inventory"]["reuse_blocked"] is False
    assert result["resource_inventory"]["recovery_required"] is False


def test_normal_outcome_uses_launcher_attempt_not_project_os_alias() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="secretary-invocation",
        returncode=0,
        payload={
            "assignment": {
                "attempt_id": "launcher-attempt",
                "project_os_attempt_id": "secretary-invocation",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "execution": {"state": "completed"},
            }
        },
        observation={
            "state": "done",
            "attempt_id": "launcher-attempt",
            "session": "session",
            "pane": "pane",
            "agent_name": "agent",
            "producer": "codex-native",
            "content_source": "lightrsi_completed_turn",
            "native_authority": "lightrsi-codex-context-history",
            "native_session_id": "session",
            "native_turn_id": "session:t1",
            "turn_seq": 1,
            "semantic_complete": True,
            "freshness_proven": True,
            "assistant_owned": True,
            "semantic_content": "native answer",
            "result_reference": "native-result://launcher-attempt",
        },
        started_at="2026-10-18T10:00:00+00:00",
        finished_at="2026-10-18T10:00:01+00:00",
    )

    assert result["result"]["state"] == "reported"


def test_normal_outcome_rejects_task_result_without_attempt_provenance() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "execution": {"state": "completed"},
                "task_result": {
                    "state": "reported_completed",
                    "result_reference": "task-result://unbound",
                    "content": "unbound answer",
                },
            }
        },
        observation={},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_rejects_unaccepted_task_result_producer() -> None:
    result = _normalize_invocation_outcome(
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
                    "producer": "terminal-screen",
                    "result_reference": "task-result://untrusted",
                    "content": "untrusted answer",
                },
            }
        },
        observation={},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_rejects_partially_bound_task_result() -> None:
    result = _normalize_invocation_outcome(
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
                    "content": "partially bound answer",
                },
            }
        },
        observation={},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_rejects_unbound_assistant_owned_observation() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={"assignment": {"execution": {"state": "completed"}}},
        observation={
            "state": "done",
            "semantic_content": "unbound answer",
            "assistant_owned": True,
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_rejects_explicitly_non_assistant_observation() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
            }
        },
        observation={
            "state": "done",
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "assistant_owned": False,
            "semantic_content": "user-authored message",
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_ignores_rejected_task_result_status_for_bound_observation() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
                "task_result": {
                    "state": "reported_failed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "producer": "terminal-screen",
                    "content": "rejected failure",
                },
            }
        },
        observation={
            "state": "done",
            "semantic_content": "accepted answer",
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "assistant_owned": True,
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "content": "accepted answer",
    }


def test_normal_outcome_preserves_authoritative_failure_with_richer_observation() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
                "task_result": {
                    "state": "reported_failed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "producer": "dcode-project",
                    "result_reference": "task-result://failed",
                    "result_resolver": "herdr",
                    "result_retrieved": True,
                },
            }
        },
        observation={
            "state": "done",
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "assistant_owned": True,
            "result_reference": "task-result://failed",
            "semantic_content": "failure details",
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "failed",
        "reference": "task-result://failed",
        "content": "failure details",
    }


def test_normal_outcome_rejects_bound_observation_without_assistant_provenance() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
                "task_result": {"state": "unknown"},
            }
        },
        observation={
            "state": "done",
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "semantic_content": "unowned answer",
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


@pytest.mark.parametrize("producer", [{"name": "malformed"}, ["malformed"]])
def test_normal_outcome_ignores_malformed_task_result_producer(
    producer: object,
) -> None:
    result = _normalize_invocation_outcome(
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
                    "producer": producer,
                    "result_reference": "task-result://malformed",
                    "content": "malformed answer",
                },
            }
        },
        observation={
            "state": "done",
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "assistant_owned": True,
            "source_ref": "task-result://trusted",
            "semantic_content": "trusted answer",
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "reference": "task-result://trusted",
        "content": "trusted answer",
    }


def test_normal_outcome_accepts_correlated_task_result_with_accepted_provenance() -> None:
    result = _normalize_invocation_outcome(
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
                    "producer": "dcode-project",
                    "source_ref": "task-result://invoke-1",
                    "source_digest": "a" * 64,
                    "content": "correlated answer",
                },
            }
        },
        observation={},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "reference": "task-result://invoke-1",
        "content": "correlated answer",
    }


def test_normal_outcome_does_not_mix_reference_and_content_from_different_sources() -> None:
    result = _normalize_invocation_outcome(
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
                    "producer": "dcode-project",
                    "result_reference": "task-result://A",
                    "result_resolver": "secretary",
                    "result_retrieved": True,
                },
            }
        },
        observation={
            "state": "done",
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "assistant_owned": True,
            "semantic_content": "answer from B",
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "ambiguous", "status": None}


def test_normal_outcome_rejects_assignment_level_prompt_content() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
                "content": "user prompt bullets",
                "task_result": {"state": "unknown"},
            }
        },
        observation={},
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_reports_failed_result_even_when_execution_failed() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=7,
        payload={
            "assignment": {
                "execution": {"state": "failed", "worker_exit_code": 7},
                "cleanup": {"state": "removed"},
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "task_result": {
                    "state": "reported_failed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "producer": "dcode-project",
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


def test_main_exception_path_uses_canonical_failure_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import scripts.secretary_live_runtime as runtime

    def fail_run(*args: object, **kwargs: object) -> dict[str, object]:
        raise RuntimeError("boom")

    monkeypatch.setattr(runtime, "run_normal", fail_run)
    output = tmp_path / "normal.json"

    assert runtime.main(["run", "--output", str(output), "--cwd", str(tmp_path), "--task", "read-only"]) == 2
    result = json.loads(output.read_text(encoding="utf-8"))

    assert result["result"] == {"state": "unavailable", "status": None}
    assert result["semantic_outcome"] == {
        "state": "unavailable",
        "status": None,
        "reference": None,
        "content": None,
    }
    assert result["execution"] == {"state": "failed", "error": "RuntimeError"}
    assert result["finalization_outcome"] == {
        "state": "recovery_required",
        "recovery_required": True,
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
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "task_result": {
                    "state": "reported_completed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "producer": "dcode-project",
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


def test_canonical_resource_inventory_deduplicates_same_attempt() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime.canonical_resource_inventory(
        [
            {"kind": "workspace", "identity": "workspace-1", "state": "settled"},
            {"kind": "workspace", "identity": "workspace-1", "state": "settled"},
        ],
        attempt_id="attempt-1",
    )

    assert result["state"] == "settled"
    assert result["reuse_blocked"] is False
    assert len(result["resources"]) == 1
    assert result["resources"][0]["attempt_id"] == "attempt-1"


def test_canonical_resource_inventory_quarantines_conflicting_or_cross_attempt_entries() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime.canonical_resource_inventory(
        [
            {"kind": "workspace", "identity": "workspace-1", "state": "settled"},
            {"kind": "workspace", "identity": "workspace-1", "state": "quarantined"},
            {"kind": "pane", "identity": "pane-1", "state": "settled", "attempt_id": "attempt-2"},
        ],
        attempt_id="attempt-1",
    )

    assert result["state"] == "quarantined"
    assert result["reuse_blocked"] is True
    assert result["recovery_required"] is True
    assert all(item["state"] == "quarantined" for item in result["resources"])


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


def test_normal_outcome_accepts_attempt_bound_native_result_without_worker_identity() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "attempt_id": "attempt-1",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "execution": {"state": "completed"},
            }
        },
        observation={
            "state": "idle",
            "attempt_id": "attempt-1",
            "session": "session",
            "pane": "pane",
            "agent_name": "agent",
            "producer": "codex-native",
            "content_source": "native_completed_turn",
            "native_authority": "lightrsi-codex-context-history",
            "native_session_id": "session",
            "native_turn_id": "turn-1",
            "completion_seq": 5,
            "freshness_proven": True,
            "assistant_owned": True,
            "semantic_content": "native answer",
            "result_reference": "C:/tmp/native-result.json",
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-18T10:00:00+00:00",
        finished_at="2026-10-18T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_rejects_native_result_with_mismatched_execution_context() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "attempt_id": "attempt-1",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "execution": {"state": "completed"},
            }
        },
        observation={
            "state": "idle",
            "attempt_id": "attempt-1",
            "session": "other-session",
            "pane": "pane",
            "agent_name": "agent",
            "producer": "codex-native",
            "content_source": "native_completed_turn",
            "native_authority": "lightrsi-codex-context-history",
            "native_session_id": "other-session",
            "native_turn_id": "turn-1",
            "completion_seq": 5,
            "freshness_proven": True,
            "assistant_owned": True,
            "semantic_content": "native answer",
            "result_reference": "C:/tmp/native-result.json",
        },
        started_at="2026-10-18T10:00:00+00:00",
        finished_at="2026-10-18T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}


def test_normal_outcome_rejects_pane_only_native_result() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "attempt_id": "attempt-1",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "execution": {"state": "completed"},
            }
        },
        observation={
            "state": "idle",
            "attempt_id": "attempt-1",
            "session": "session",
            "pane": "pane",
            "agent_name": "agent",
            "producer": "codex-native",
            "content_source": "pane",
            "completion_seq": 5,
            "freshness_proven": True,
            "assistant_owned": True,
            "semantic_content": "pane text",
            "result_reference": "C:/tmp/pane-result.json",
        },
        started_at="2026-10-18T10:00:00+00:00",
        finished_at="2026-10-18T10:00:01+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}

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
                    "producer": "dcode-project",
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
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-assignment",
                "execution": {"state": "completed"},
                "task_result": {
                    "state": "reported_completed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-result",
                    "producer": "terminal-screen",
                    "content": "answer",
                },
            },
        },
        observation={
            "state": "done",
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-assignment",
            "producer": "dcode-project",
            "assistant_owned": True,
            "semantic_content": "accepted answer",
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "content": "accepted answer",
    }


def test_normal_outcome_preserves_long_semantic_content() -> None:
    import scripts.secretary_live_runtime as runtime

    content = "x" * 5000
    result = runtime._normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "execution": {"state": "completed"},
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "task_result": {
                    "state": "reported_completed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "producer": "dcode-project",
                    "content": content,
                },
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
        "attempt_id": "attempt-1",
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


def test_launch_request_does_not_require_caller_attempt_id() -> None:
    values = {
        "task_id": "task-1",
        "plan_revision": "plan-rev-1",
        "run_id": "run-1",
        "repository_identity": "repo/example",
        "plan_identity": "plan/example",
        "git_revision": "581844d",
        "worktree": Path("C:/worktree"),
        "expected_base": "581844d",
        "task": "Read-only Secretary attention probe.",
        "codex_home": Path("C:/Users/example/.codex"),
    }

    request_value = SecretaryLaunchRequest(**values)

    assert request_value.task_id == "task-1"


def test_launcher_command_keeps_machine_binding_out_of_worker_task() -> None:
    command = build_launcher_command(request())

    assert "--executor" in command
    assert command[command.index("--executor") + 1] == "codex"
    assert "--codex-home" in command
    assert command[command.index("--codex-home") + 1] == str(Path("C:/Users/example/.codex"))
    task = command[command.index("--task") + 1]
    assert task == "Read-only Secretary attention probe."
    for option, value in (
        ("--secretary-task-id", "task-1"),
        ("--secretary-plan-revision", "plan-rev-1"),
        ("--secretary-run-id", "run-1"),
    ):
        assert command[command.index(option) + 1] == value
    assert "--secretary-attempt-id" not in command
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
                },
                "assignment": {
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "task_result": {
                        "state": "reported_completed",
                        "assignment_id": "assignment-1",
                        "attempt_id": "attempt-1",
                        "producer": "dcode-project",
                        "result_reference": "task-result://attempt-1",
                    },
                },
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

    assert observation["state"] == "idle"
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
    assert observation["observation_error"] == "submission freshness not proven"
    assert "semantic_content" not in observation


def test_normal_outcome_uses_consistent_cleanup_evidence() -> None:
    payload = {
        "herdr": {"session": "session", "pane": "pane", "agent_name": "agent"},
        "assignment": {
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "execution": {"state": "completed"},
            "cleanup": {"state": "preserved"},
            "task_result": {
                "state": "reported_completed",
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "producer": "dcode-project",
                "content": "answer",
            },
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


def test_observe_submitted_codex_waits_past_initial_idle_without_semantic_promotion(
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
            "content": "Codex screen\n• SECRETARY_PROBE_test\nWorked for 1s\n› Ask Codex to do anything",
            "output_sha256": "b" * 64,
            "output_chars": 65,
            "observation_error": None,
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "assistant_owned": True,
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
            },
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "task_result": {
                    "state": "reported_completed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "producer": "dcode-project",
                    "result_reference": "task-result://attempt-1",
                },
            },
        },
        env={},
    )

    assert observation["state"] == "idle"
    assert "semantic_content" not in observation
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


def test_observe_submitted_codex_passes_bound_pane_to_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.01)
    seen: dict[str, object] = {}

    def snapshot(*args: object, **kwargs: object) -> dict[str, object]:
        seen.update(kwargs)
        return {"state": "working", "observation_error": None}

    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        snapshot,
    )

    _observe_submitted_codex(
        request(session="session", pane="pane"),
        _correlated_payload(),
        pre_submit=_submission_anchor(),
        env={},
    )

    assert seen["pane"] == "pane"



def test_observe_submitted_codex_keeps_legacy_native_result_diagnostic_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "_codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "idle",
            "completion_seq": 5,
            "semantic_content": "fresh native answer",
            "content": "",
            "output_sha256": "b" * 64,
            "output_chars": 0,
            "observation_error": None,
            "content_source": "agent",
            "native_completed_turn": {
                "kind": "completed",
                "authority": "lightrsi-codex-context-history",
                "sessionId": "session",
                "turnId": "turn-1",
                "assistantText": "fresh native answer",
                "requestId": "request-1",
                "responseId": "response-1",
            },
        },
    )
    monkeypatch.setattr(
        runtime,
        "_release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )
    payload = {
        "herdr": {
            "executable": "herdr.exe",
            "session": "session",
            "pane": "pane",
            "agent_name": "agent",

        },
        "assignment": {"attempt_id": "attempt-1", "pre_submit_completion_seq": 4},
    }
    result_path = tmp_path / "native-result.json"

    observation = runtime._observe_submitted_codex(
        request(session="session", pane="pane"),
        payload,
        env={},
    )

    assert observation["diagnostic_content_source"] == "native_completed_turn"
    assert "semantic_content" not in observation
    assert "publication" not in observation
    assert observation["cleanup"] == {"state": "removed"}
    assert not result_path.exists()


def test_observe_submitted_codex_keeps_legacy_result_diagnostic_when_read_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "_codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "idle",
            "completion_seq": 5,
            "observation_error": "agent read failed",
            "content_source": "agent",
            "native_completed_turn": {
                "kind": "completed",
                "authority": "lightrsi-codex-context-history",
                "sessionId": "session",
                "turnId": "turn-1",
                "assistantText": "fresh native answer",
            },
        },
    )
    monkeypatch.setattr(
        runtime,
        "_release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )
    result_path = tmp_path / "native-result.json"
    observation = runtime._observe_submitted_codex(
        request(session="session", pane="pane"),
        {
            "herdr": {
                "executable": "herdr.exe",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "pre_submit_completion_seq": 4,
            },
            "assignment": {"attempt_id": "attempt-1"},
        },
        env={},
    )

    assert observation["observation_error"] == "agent read failed"
    assert observation["diagnostic_content_source"] == "native_completed_turn"
    assert "semantic_content" not in observation
    assert not result_path.exists()


def test_observe_submitted_codex_rejects_persisted_result_without_fresh_reader_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "_codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "idle",
            "completion_seq": 5,
            "semantic_content": "fresh native answer",
            "content": "",
            "output_sha256": "b" * 64,
            "output_chars": 0,
            "observation_error": None,
            "content_source": "agent",
            "native_completed_turn": {
                "kind": "completed",
                "authority": "lightrsi-codex-context-history",
                "sessionId": "session",
                "turnId": "turn-1",
                "assistantText": "fresh native answer",
            },
        },
    )
    monkeypatch.setattr(
        runtime,
        "parse_native_result",
        lambda *args, **kwargs: {"state": "unknown", "detail": "native result unavailable"},
    )
    monkeypatch.setattr(
        runtime,
        "_release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = runtime._observe_submitted_codex(
        request(session="session", pane="pane"),
        {
            "herdr": {
                "executable": "herdr.exe",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "pre_submit_completion_seq": 4,
            },
            "assignment": {"attempt_id": "attempt-1"},
        },
        env={},
    )

    assert observation["observation_error"] is None
    assert observation["diagnostic_content_source"] == "native_completed_turn"
    assert "semantic_content" not in observation
    assert observation["cleanup"] == {"state": "removed"}


def test_observe_submitted_codex_blocks_when_native_publication_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "_codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "idle",
            "completion_seq": 5,
            "semantic_content": "fresh native answer",
            "content": "",
            "output_sha256": "b" * 64,
            "output_chars": 0,
            "observation_error": None,
            "content_source": "agent",
            "native_completed_turn": {
                "kind": "completed",
                "authority": "lightrsi-codex-context-history",
                "sessionId": "session",
                "turnId": "turn-1",
                "assistantText": "fresh native answer",
            },
        },
    )
    monkeypatch.setattr(
        runtime,
        "publish_native_result",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr(
        runtime,
        "_release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = runtime._observe_submitted_codex(
        request(session="session", pane="pane"),
        {
            "herdr": {
                "executable": "herdr.exe",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "pre_submit_completion_seq": 4,
            },
            "assignment": {"attempt_id": "attempt-1"},
        },
        env={},
    )

    assert observation["observation_error"] is None
    assert observation["diagnostic_content_source"] == "native_completed_turn"
    assert "semantic_content" not in observation
    assert observation["cleanup"] == {"state": "removed"}


@pytest.mark.parametrize(
    "native_turn",
    [
        {"kind": "rejected", "reason": "turn_aborted"},
        {
            "kind": "completed",
            "authority": "lightrsi-codex-context-history",
            "sessionId": "other-session",
            "turnId": "turn-1",
            "assistantText": "stale answer",
        },
        {
            "kind": "completed",
            "authority": "lightrsi-codex-context-history",
            "sessionId": "session",
            "turnId": "turn-1",
            "assistantText": "tool call continuation",
            "toolCallContinuation": True,
        },
        {
            "kind": "completed",
            "sessionId": "session",
            "turnId": "turn-1",
            "assistantText": "missing authority",
        },
    ],
)
def test_observe_submitted_codex_rejects_invalid_native_completed_turn(
    native_turn: dict[str, object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "_codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "idle",
            "completion_seq": 5,
            "native_completed_turn": native_turn,
            "content": "diagnostic pane text",
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        runtime,
        "_release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    observation = runtime._observe_submitted_codex(
        request(session="session", pane="pane"),
        {
            "herdr": {
                "executable": "herdr.exe",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "pre_submit_completion_seq": 4,
            },
            "assignment": {"attempt_id": "attempt-1"},
        },
        env={},
    )

    assert "semantic_content" not in observation
    assert observation["cleanup"] == {"state": "removed"}

def _submission_anchor() -> dict[str, object]:
    return {
        "state": "idle",
        "state_change_seq": 1,
        "content": "Codex prompt screen",
        "output_sha256": "a" * 64,
        "output_chars": 18,
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
        "producer": "dcode-project",
    }


def test_submission_freshness_requires_a_new_native_completion_sequence() -> None:
    import scripts.secretary_live_runtime as runtime
    anchor = {**_submission_anchor(), "completion_seq": 4}
    snapshot = {
        **anchor,
        "state": "idle",
        "content": "Codex screen\n• FRESH ANSWER",
        "output_sha256": "b" * 64,
        "output_chars": 29,
    }

    assert runtime._submission_freshness_proven(anchor, snapshot) is False

    snapshot["completion_seq"] = 5
    assert runtime._submission_freshness_proven(anchor, snapshot) is True



@pytest.mark.parametrize("baseline", [None, True, -1, "4"])
def test_submission_freshness_rejects_invalid_native_baseline(baseline: object) -> None:
    import scripts.secretary_live_runtime as runtime

    anchor = {"completion_seq": baseline}
    snapshot = {"completion_seq": 5}

    assert runtime._submission_freshness_proven(anchor, snapshot) is False


def test_observe_submitted_codex_does_not_treat_null_baseline_as_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.secretary_live_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "_codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "idle",
            "completion_seq": 0,
            "native_completed_turn": {
                "kind": "completed",
                "authority": runtime.NATIVE_RESULT_AUTHORITY,
                "sessionId": "session",
                "turnId": "turn-1",
                "assistantText": "fresh answer",
            },
        },
    )
    monkeypatch.setattr(runtime, "_release_codex_agent", lambda *args, **kwargs: {"state": "removed"})

    observation = runtime._observe_submitted_codex(
        request(session="session", pane="pane"),
        {
            "herdr": {
                "executable": "herdr.exe",
                "session": "session",
                "pane": "pane",
                "agent_name": "agent",
                "pre_submit_completion_seq": None,
            },
            "assignment": {"attempt_id": "attempt-1"},
        },
        env={},
    )

    assert observation["freshness_proven"] is False
    assert observation["observation_error"] == "submission freshness not proven"

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
            "task_result": {
                "state": "reported_completed",
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "producer": "dcode-project",
                "result_reference": "task-result://attempt-1",
            },
        },
    }


def test_observe_submitted_codex_keeps_fast_idle_terminal_answer_diagnostic_only(
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
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "assistant_owned": True,
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
    assert "semantic_content" not in observation
    assert observation["producer"] == "dcode-project"


def test_observe_submitted_codex_uses_bound_structured_content_over_terminal_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terminal_content = "Codex screen\n• USER-INJECTED TERMINAL TEXT\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "content": terminal_content,
            "output_sha256": "b" * 64,
            "output_chars": len(terminal_content),
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
        {
            **_correlated_payload(),
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "task_result": {
                    "state": "reported_completed",
                    "assignment_id": "assignment-1",
                    "attempt_id": "attempt-1",
                    "producer": "dcode-project",
                    "result_reference": "task-result://attempt-1",
                    "content": "structured answer",
                },
            },
        },
        pre_submit=_submission_anchor(),
        env={},
    )

    assert "semantic_content" not in observation


def test_observe_submitted_codex_uses_bound_snapshot_semantic_content_without_terminal_bullet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
            "semantic_content": "accepted snapshot answer",
            "source_ref": "task-result://snapshot",
            "content": "Codex screen without a semantic bullet",
            "output_sha256": "b" * 64,
            "output_chars": 36,
            "state_change_seq": 2,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    payload = _correlated_payload()
    payload["assignment"] = {
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
    }
    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        payload,
        pre_submit=_submission_anchor(),
        env={},
    )

    assert "semantic_content" not in observation
    assert "source_ref" not in observation


def test_observe_submitted_codex_rejects_terminal_content_without_snapshot_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "Previous completion\nWorked for 1s\n"
        "› Summarize these notes:\n• USER PROMPT TEXT\n"
        "› Ask Codex to do anything"
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
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    payload = _correlated_payload()
    payload["assignment"] = {
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
        "task_result": {"state": "unknown"},
    }
    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        payload,
        pre_submit=_submission_anchor(),
        env={},
    )

    assert observation["observation_error"] == "completion output not observed"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_preserves_snapshot_conflict_for_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
            "result_reference": "task-result://B",
            "semantic_content": "answer from B",
            "content": "Codex structured result",
            "output_sha256": "b" * 64,
            "output_chars": 24,
            "state_change_seq": 2,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    payload = _correlated_payload()
    payload["assignment"]["task_result"] = {
        "state": "reported_completed",
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
        "producer": "dcode-project",
        "result_reference": "task-result://A",
        "content": "answer from A",
    }
    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        payload,
        pre_submit=_submission_anchor(),
        env={},
    )
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload=payload,
        observation=observation,
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert "semantic_content" not in observation
    assert "result_reference" not in observation
    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "reference": "task-result://A",
        "content": "answer from A",
    }


def test_observe_submitted_codex_does_not_publish_unrelated_terminal_bullet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terminal_content = "Codex screen\n• unrelated terminal text\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
            "semantic_content": "accepted snapshot answer",
            "source_ref": "task-result://snapshot",
            "content": terminal_content,
            "output_sha256": "b" * 64,
            "output_chars": len(terminal_content),
            "state_change_seq": 2,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    payload = _correlated_payload()
    payload["assignment"] = {
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
    }
    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        payload,
        pre_submit=_submission_anchor(),
        env={},
    )

    assert "semantic_content" not in observation


def test_observe_submitted_codex_keeps_task_result_source_ref_over_rejected_snapshot_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terminal_content = "Codex screen\n• unrelated terminal text\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "producer": "terminal-screen",
            "result_reference": "task-result://unrelated",
            "content": terminal_content,
            "output_sha256": "b" * 64,
            "output_chars": len(terminal_content),
            "state_change_seq": 2,
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._release_codex_agent",
        lambda *args, **kwargs: {"state": "removed"},
    )

    payload = _correlated_payload()
    payload["assignment"]["task_result"] = {
        "state": "reported_completed",
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
        "producer": "dcode-project",
        "source_ref": "task-result://trusted",
        "content": "trusted answer",
    }
    observation = _observe_submitted_codex(
        request(session="session", pane="pane"),
        payload,
        pre_submit=_submission_anchor(),
        env={},
    )
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload=payload,
        observation=observation,
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:01+00:00",
    )

    assert result["result"] == {
        "state": "reported",
        "status": "completed",
        "reference": "task-result://trusted",
        "content": "trusted answer",
    }


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
    assert observation["observation_error"] == "agent read transport timeout"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_keeps_fresh_terminal_output_diagnostic_only(
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
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "assistant_owned": True,
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
    assert "semantic_content" not in observation


def test_observe_submitted_codex_accepts_fresh_terminal_completion_without_structured_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "Codex screen\n"
        "› Reply with exactly SECRETARY_CLOSURE_INSTRUMENTED_20261012.\n"
        "\n"
        "• SECRETARY_CLOSURE_INSTRUMENTED_20261012\n"
        "\n"
        "Worked for 16s • 11:16\n"
        "› Ask Codex to do anything"
    )
    payload = _correlated_payload()
    assignment = payload["assignment"]
    assert isinstance(assignment, dict)
    assignment["task_result"] = {"state": "unverified"}
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "done",
            "content": content,
            "output_sha256": "b" * 64,
            "output_chars": len(content),
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
        payload,
        pre_submit=_submission_anchor(),
        env={},
    )

    assert "semantic_content" not in observation


def test_observe_submitted_codex_selects_last_completed_bullet_after_multiline_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nonce = "SECRETARY_PROBE_B_TEST"
    content = (
        "Codex screen\n"
        "› User notes:\n"
        "• The bullets are user-provided content.\n"
        "• Do not echo these notes as the answer.\n"
        f"Return exactly {nonce}. Do not edit the repository or create child workers.\n"
        "Secretary normal-mode boundary: inspect, reason, prioritize, route, or summarize only.\n"
        "• "
        f"{nonce}\n"
        "Worked for 16s • 11:16\n"
        "› Ask Codex to do anything"
    )
    payload = _correlated_payload()
    assignment = payload["assignment"]
    assert isinstance(assignment, dict)
    assignment["task_result"] = {"state": "unverified"}
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            "state": "done",
            "content": content,
            "output_sha256": "b" * 64,
            "output_chars": len(content),
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
        payload,
        pre_submit=_submission_anchor(),
        env={},
    )

    assert "semantic_content" not in observation


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


def test_extract_codex_semantic_content_rejects_initial_prompt_bullet_without_marker() -> None:
    assert _extract_codex_semantic_content(
        "› Summarize these notes:\n• USER PROMPT TEXT\n› Ask Codex to do anything"
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


@pytest.mark.parametrize(
    "text",
    [
        "https://example.test/?token=PREFIX'SUFFIX",
        "https://example.test/?token=PREFIX''SUFFIX",
        "https://example.test/?token=PREFIX',SUFFIX",
    ],
)
def test_semantic_redaction_removes_query_secret_with_apostrophe_suffix(text: str) -> None:
    assert _redact_semantic_content(
        text
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


def test_normal_outcome_reports_captured_observation_content() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
                "execution": {"state": "completed"},
                "task_result": {"state": "unknown"},
            }
        },
        observation={
            "state": "done",
            "semantic_content": "SECRETARY_PROBE_test",
            "assistant_owned": True,
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
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


def test_snapshot_result_content_rejects_terminal_content_without_structured_field() -> None:
    assert _snapshot_result_content(
        {
            "content": "Codex screen\n• terminal-only answer\nWorked for 1s",
        }
    ) is None


def test_normal_outcome_scopes_launcher_observation_error_without_downgrading_result() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={
            "assignment": {
                "assignment_id": "assignment-1",
                "attempt_id": "attempt-1",
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
            "assistant_owned": True,
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
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


def test_normal_outcome_timeout_without_cleanup_proof_blocks_reuse() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-timeout",
        returncode=0,
        payload={
            "assignment": {
                "execution": {"state": "running"},
                "cleanup": {"state": "unknown"},
            }
        },
        observation={
            "state": "unknown",
            "observation_error": "completion observation deadline expired",
        },
        started_at="2026-10-11T10:00:00+00:00",
        finished_at="2026-10-11T10:00:02+00:00",
    )

    assert result["result"] == {"state": "unavailable", "status": None}
    assert result["resource"] == {"state": "quarantined", "reuse_blocked": True}
    assert result["recovery_required"] is True


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
        "assignment": {"status": "submitted", "attempt_id": "attempt-1"},
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


def test_transport_observation_error_keeps_completion_capability_blocked() -> None:
    import scripts.secretary_live_runtime as runtime

    result = runtime._classify_capabilities(
        "BLOCKED_CAPABILITY",
        {
            "state": "done",
            "cleanup": {"state": "removed"},
            "observation_error": "pane read transport timeout",
        },
    )

    assert result == {
        "transport_evidence": "unproven",
        "missing_capabilities": [
            "transport_completion_or_cleanup",
            "secretary_runtime_receipt",
        ],
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
    assert all(source["attempt_id"] == "attempt-1" for source in snapshot["sources"].values())


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
        "attempt_id": "attempt-1",
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


def test_observe_submitted_codex_keeps_repeated_terminal_answer_diagnostic_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answer = "Codex screen\n• SAME ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
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

    assert "semantic_content" not in observation


def test_observe_submitted_codex_reports_untrusted_terminal_content_as_provenance_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answer = "Codex screen\n• UNTRUSTED ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "done",
            "content": answer,
            "output_sha256": "b" * 64,
            "output_chars": len(answer),
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
        pre_submit={**_submission_anchor(), "content": "Codex prompt screen"},
        env={},
    )

    assert observation["observation_error"] == "completion provenance not established"
    assert "semantic_content" not in observation


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


def test_observe_submitted_codex_rejects_initial_prompt_bullet_without_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = "› Summarize these notes:\n• USER PROMPT TEXT\n› Ask Codex to do anything"
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

    assert observation["observation_error"] == "completion output not observed"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_rejects_initial_prompt_bullet_with_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "› Please echo this input:\n• USER PROMPT TEXT\n"
        "Worked for 2s\n› Ask Codex to do anything"
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

    assert observation["observation_error"] == "completion output not observed"
    assert "semantic_content" not in observation


def test_observe_submitted_codex_keeps_single_bullet_terminal_answer_diagnostic_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "› Reply with exactly PROBE_OK.\n• PROBE_OK\n"
        "Worked for 1s\n› Ask Codex to do anything"
    )
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
            "content": content,
            "output_sha256": "b" * 64,
            "output_chars": len(content),
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
        pre_submit=_submission_anchor(),
        env={},
    )

    assert "semantic_content" not in observation


def test_observe_submitted_codex_keeps_prompt_commentary_terminal_answer_diagnostic_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "› Summarize these notes:\n• I will inspect the code first.\n"
        "Worked for 1s\n• PROBE_OK\n› Ask Codex to do anything"
    )
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
            "content": content,
            "output_sha256": "b" * 64,
            "output_chars": len(content),
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
        pre_submit=_submission_anchor(),
        env={},
    )

    assert "semantic_content" not in observation


def test_observe_submitted_codex_keeps_later_terminal_answer_diagnostic_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "› Original request\n• OLD ANSWER\nWorked for 1s\n"
        "› Summarize these notes:\n• I will inspect the code first.\n"
        "Worked for 2s\n• PROBE_OK\n› Ask Codex to do anything"
    )
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr("scripts.secretary_live_runtime._CODEX_OBSERVATION_POLL_SECONDS", 0.001)
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
            "content": content,
            "output_sha256": "b" * 64,
            "output_chars": len(content),
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
        pre_submit={
            **_submission_anchor(),
            "content": "› Original request\n• OLD ANSWER\nWorked for 1s\n› Ask Codex to do anything",
        },
        env={},
    )

    assert "semantic_content" not in observation


def test_observe_submitted_codex_keeps_repeated_terminal_answer_diagnostic_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = "Codex screen\n• SAME ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    snapshot = "Codex screen\n• SAME ANSWER\nWorked for 2s\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
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

    assert "semantic_content" not in observation


def test_observe_submitted_codex_keeps_repeated_prompt_suffix_terminal_answer_diagnostic_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = "› Original request\n• SAME ANSWER\nWorked for 1s\n› Ask Codex to do anything"
    snapshot = "› Original request\n• SAME ANSWER\nWorked for 2s\n› Ask Codex to do anything"
    monkeypatch.setattr(
        "scripts.secretary_live_runtime._codex_completion_snapshot",
        lambda *args, **kwargs: {
            **_submission_anchor(),
            "state": "idle",
            "assistant_owned": True,
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

    assert "semantic_content" not in observation


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
        payload={"assignment": {"assignment_id": "assignment-1", "attempt_id": "attempt-1", "execution": {"state": "completed"}, "task_result": {"state": "unknown"}}},
        observation={"state": "done", "semantic_content": content, "assistant_owned": True, "assignment_id": "assignment-1", "attempt_id": "attempt-1", "producer": "dcode-project", "cleanup": {"state": "removed"}},
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"] == {"state": "reported", "status": "completed", "content": content}


def test_normal_outcome_redacts_quoted_secret_values() -> None:
    result = _normalize_invocation_outcome(
        invocation_id="invoke-1",
        returncode=0,
        payload={"assignment": {"assignment_id": "assignment-1", "attempt_id": "attempt-1", "execution": {"state": "completed"}, "task_result": {"state": "unknown"}}},
        observation={
            "state": "done",
            "semantic_content": '{"api_key": "SYNTHETIC first second"}',
            "assistant_owned": True,
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
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
        payload={"assignment": {"assignment_id": "assignment-1", "attempt_id": "attempt-1", "execution": {"state": "completed"}, "task_result": {"state": "unknown"}}},
        observation={
            "state": "done",
            "semantic_content": '{"api_key": "SYNTHETIC-prefix?token=SYNTHETIC-suffix"}',
            "assistant_owned": True,
            "assignment_id": "assignment-1",
            "attempt_id": "attempt-1",
            "producer": "dcode-project",
            "cleanup": {"state": "removed"},
        },
        started_at="2026-10-11T00:00:00+00:00",
        finished_at="2026-10-11T00:00:01+00:00",
    )

    assert result["result"]["content"] == '{"api_key": "[REDACTED]"}'
