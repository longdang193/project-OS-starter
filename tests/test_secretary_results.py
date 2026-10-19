import json
from pathlib import Path

import pytest

from scripts.project_os_runtime.secretary_results import (
    NATIVE_BINDING_SCHEMA,
    NATIVE_RESULT_SCHEMA,
    NATIVE_APP_SERVER_AUTHORITY,
    NATIVE_RESULT_AUTHORITY,
    NATIVE_RESULT_PRODUCER,
    NATIVE_RESULT_MAX_BYTES,
    NATIVE_SUBMISSION_SCHEMA,
    native_binding_path,
    native_submission_path,
    parse_native_binding,
    parse_native_submission,
    publish_native_binding,
    publish_native_submission,
    NativeResultConflictError,
    native_result_path,
    parse_native_result,
    publish_native_result,
    request_fingerprint,
)


FINGERPRINT = request_fingerprint(
    {
        "task_sha256": "task",
        "repository_identity": "repo",
        "git_revision": "rev",
        "execution_role": "secretary",
        "model_identity": "model",
        "runtime_grant_digest": "",
    }
)


def payload(content: str = "native answer") -> dict[str, object]:
    return {
        "schema": NATIVE_RESULT_SCHEMA,
        "producer": NATIVE_RESULT_PRODUCER,
        "attempt_id": "attempt-1",
        "logical_operation_id": "operation-1",
        "request_fingerprint": FINGERPRINT,
        "session": "session",
        "pane": "pane",
        "agent_name": "agent",
        "native_authority": NATIVE_APP_SERVER_AUTHORITY,
        "native_session_id": "session",
        "native_thread_id": "thread",
        "native_turn_id": "session:t1",
        "content_source": "native_app_server_completed_turn",
        "answer_provenance": "native_final_answer",
        "terminal_status": "completed",
        "semantic_complete": True,
        "semantic_content": content,
        "freshness_proven": True,
        "assistant_owned": True,
        "observed_at": "2026-10-18T10:00:00+00:00",
    }


def test_native_result_publishes_and_fresh_reader_confirms(tmp_path: Path) -> None:
    path = native_result_path(tmp_path / "normal.json")

    publication = publish_native_result(path, payload())
    parsed = parse_native_result(path, attempt_id="attempt-1")

    assert publication["state"] == "published"
    assert parsed["state"] == "confirmed"
    assert parsed["semantic_content"] == "native answer"
    assert parsed["result_reference"] == str(path)


def test_native_result_replay_is_idempotent_and_conflict_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "native-result.json"
    first = publish_native_result(path, payload())
    replay = publish_native_result(path, payload())

    assert first["digest"] == replay["digest"]
    assert replay["state"] == "idempotent"

    with pytest.raises(NativeResultConflictError):
        publish_native_result(path, payload("different answer"))


def test_native_result_replay_preserves_first_observation_metadata(tmp_path: Path) -> None:
    path = tmp_path / "native-result.json"
    first = payload()
    publish_native_result(path, first)

    replay = payload()
    replay["observed_at"] = "2026-10-18T11:00:00+00:00"
    publication = publish_native_result(path, replay)

    assert publication["state"] == "idempotent"
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["observed_at"] == first["observed_at"]


def test_native_result_does_not_require_transport_session_to_equal_native_session(
    tmp_path: Path,
) -> None:
    value = payload()
    value["session"] = "herdr-session"
    value["native_session_id"] = "lightrsi-session"
    value["native_turn_id"] = "lightrsi-session:t1"

    publication = publish_native_result(tmp_path / "native-result.json", value)

    assert publication["state"] == "published"


def test_native_result_redacts_secret_values_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SECRETARY_SEMANTIC_SECRETS", "configured-secret")
    value = payload(
        "Authorization: Bearer abc123 configured-secret https://example.test/?token=url-secret"
    )

    publish_native_result(tmp_path / "native-result.json", value)
    persisted = json.loads((tmp_path / "native-result.json").read_text(encoding="utf-8"))

    assert "abc123" not in persisted["semantic_content"]
    assert "configured-secret" not in persisted["semantic_content"]
    assert "url-secret" not in persisted["semantic_content"]
    assert persisted["semantic_content"] != value["semantic_content"]


def test_native_result_readback_uses_persisted_content_when_environment_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "native-result.json"
    monkeypatch.setenv("SECRETARY_SEMANTIC_SECRETS", "initial-secret")
    publish_native_result(path, payload("initial-secret answer"))

    monkeypatch.setenv("SECRETARY_SEMANTIC_SECRETS", "answer")
    parsed = parse_native_result(path, attempt_id="attempt-1")

    assert parsed["state"] == "confirmed"
    assert parsed["semantic_content"] == "[REDACTED] answer"


def test_native_result_allows_missing_transport_metadata(tmp_path: Path) -> None:
    value = payload()
    for field in ("session", "pane", "agent_name"):
        value.pop(field)

    publication = publish_native_result(tmp_path / "native-result.json", value)

    assert publication["state"] == "published"


def test_native_result_does_not_publish_legacy_completed_turn_source(tmp_path: Path) -> None:
    value = payload()
    value["content_source"] = "native_completed_turn"

    with pytest.raises(ValueError, match="content source"):
        publish_native_result(tmp_path / "native-result.json", value)


def test_native_result_reads_legacy_completed_turn_artifact_without_republishing(
    tmp_path: Path,
) -> None:
    value = payload("legacy answer")
    value["schema"] = "secretary-native-result.v1"
    value["content_source"] = "native_completed_turn"
    value.pop("request_fingerprint")
    value.pop("native_thread_id")
    value.pop("terminal_status")
    value.pop("content_sha256", None)
    path = tmp_path / "native-result.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    parsed = parse_native_result(path, attempt_id="attempt-1")

    assert parsed["state"] == "confirmed"
    assert parsed["content_source"] == "native_completed_turn"
    assert parsed["semantic_content"] == "legacy answer"


def test_native_result_writer_does_not_republish_legacy_artifact(tmp_path: Path) -> None:
    path = tmp_path / "native-result.json"
    legacy = payload("legacy answer")
    legacy["schema"] = "secretary-native-result.v1"
    legacy["content_source"] = "native_completed_turn"
    legacy.pop("request_fingerprint")
    legacy.pop("native_thread_id")
    legacy.pop("terminal_status")
    path.write_text(json.dumps(legacy), encoding="utf-8")

    with pytest.raises(NativeResultConflictError, match="malformed existing evidence"):
        publish_native_result(path, payload("new answer"))


def test_native_result_rejects_missing_new_semantic_contract_fields(tmp_path: Path) -> None:
    value = payload()
    value.pop("request_fingerprint")

    with pytest.raises(ValueError, match="request_fingerprint"):
        publish_native_result(tmp_path / "native-result.json", value)


def test_native_result_requires_terminal_completion(tmp_path: Path) -> None:
    value = payload()
    value["terminal_status"] = "idle"

    with pytest.raises(ValueError, match="terminal status"):
        publish_native_result(tmp_path / "native-result.json", value)


def test_request_fingerprint_uses_fixed_field_order_and_empty_values() -> None:
    assert FINGERPRINT == "b01dc2a65f02a764cab922b85643028fe8ba23f9fbf67a81a52f3e8d23904262"
    assert request_fingerprint({"task_sha256": "task", "repository_identity": "repo", "git_revision": "rev", "execution_role": "secretary", "model_identity": "model"}) == FINGERPRINT


def test_native_result_rejects_oversized_encoded_payload(tmp_path: Path) -> None:
    value = payload("x" * NATIVE_RESULT_MAX_BYTES)

    with pytest.raises(ValueError, match="exceeds"):
        publish_native_result(tmp_path / "native-result.json", value)


def test_native_binding_is_atomic_attempt_bound_and_immutable(tmp_path: Path) -> None:
    path = native_binding_path(tmp_path / "normal.json")
    value = {
        "schema": NATIVE_BINDING_SCHEMA,
        "attempt_id": "attempt-1",
        "logical_operation_id": "operation-1",
        "request_fingerprint": FINGERPRINT,
        "native_session_id": "session",
        "native_thread_id": "thread",
        "pre_submit_cursor": "cursor",
        "lightrsi_cli_path": "C:/pinned/cli.js",
        "created_at": "2026-10-18T10:00:00+00:00",
        "transport": {"session": "herdr", "pane": "pane", "agent_name": "agent"},
    }

    first = publish_native_binding(path, value)
    parsed = parse_native_binding(path, attempt_id="attempt-1")
    assert first["state"] == "published"
    assert parsed["state"] == "confirmed"
    assert parsed["created_at"] == value["created_at"]
    with pytest.raises(NativeResultConflictError):
        publish_native_binding(path, {**value, "created_at": "2026-10-18T11:00:00+00:00"})


def test_native_submission_ack_is_attempt_bound_and_idempotent(tmp_path: Path) -> None:
    path = native_submission_path(tmp_path / "normal.json")
    value = {
        "schema": NATIVE_SUBMISSION_SCHEMA,
        "attempt_id": "attempt-1",
        "logical_operation_id": "operation-1",
        "request_fingerprint": FINGERPRINT,
        "native_session_id": "session",
        "native_thread_id": "thread",
        "native_turn_id": "turn",
        "accepted_at": "2026-10-18T10:00:00+00:00",
        "status": "accepted",
    }

    first = publish_native_submission(path, value)
    replay = publish_native_submission(path, value)

    assert first["state"] == "published"
    assert replay["state"] == "idempotent"
    assert parse_native_submission(path, attempt_id="attempt-1")["state"] == "confirmed"
    assert parse_native_submission(path, attempt_id="attempt-2") == {
        "state": "unknown",
        "detail": "native submission attempt mismatch",
    }
    with pytest.raises(NativeResultConflictError):
        publish_native_submission(path, {**value, "native_turn_id": "other-turn"})



def test_native_result_rejects_conflicting_content_digest(tmp_path: Path) -> None:
    path = tmp_path / "native-result.json"
    invalid = payload()
    invalid["content_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="content digest"):
        publish_native_result(path, invalid)

def test_native_result_rejects_wrong_attempt(tmp_path: Path) -> None:
    path = tmp_path / "native-result.json"
    publish_native_result(path, payload())

    parsed = parse_native_result(path, attempt_id="attempt-2")

    assert parsed == {"state": "unknown", "detail": "native result attempt mismatch"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("native_authority", "terminal-screen"),
        ("native_session_id", ""),
        ("native_turn_id", ""),
        ("content_source", "agent"),
    ],
)
def test_native_result_rejects_non_native_provenance(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    invalid = payload()
    invalid[field] = value

    with pytest.raises(ValueError):
        publish_native_result(tmp_path / "native-result.json", invalid)
