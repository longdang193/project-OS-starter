from pathlib import Path

import pytest

from scripts.project_os_runtime.secretary_results import (
    NATIVE_RESULT_PRODUCER,
    NativeResultConflictError,
    native_result_path,
    parse_native_result,
    publish_native_result,
)


def payload(content: str = "native answer") -> dict[str, object]:
    return {
        "schema": "secretary-native-result.v1",
        "producer": NATIVE_RESULT_PRODUCER,
        "attempt_id": "attempt-1",
        "session": "session",
        "pane": "pane",
        "agent_name": "agent",
        "completion_seq": 8,
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