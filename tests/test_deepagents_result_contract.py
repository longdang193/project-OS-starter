from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "local_deepagents_result_contract", ROOT / "scripts" / "deepagents_result_contract.py"
)
assert SPEC is not None and SPEC.loader is not None
contract = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = contract
SPEC.loader.exec_module(contract)
TASK_RESULT_SCHEMA = contract.TASK_RESULT_SCHEMA
encode_task_result = contract.encode_task_result
parse_task_result = contract.parse_task_result
publish_task_result = contract.publish_task_result


def task_result(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": TASK_RESULT_SCHEMA,
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
        "task_sha256": "a" * 64,
        "grant_digest": "b" * 64,
        "producer": "deepagents",
        "status": "completed",
        "progress": {"completed": ["step-1"]},
        "checkpoint": {"revision": "abc123"},
        "remaining_work": ["acceptance"],
        "verification": {"references": ["tests/test_example.py"]},
        "continuation": {"requested": False},
    }
    value.update(overrides)
    return value


def test_task_result_round_trip_is_identity_bound(tmp_path: Path) -> None:
    path = tmp_path / "task-result.json"
    publish_task_result(path, task_result())

    assert parse_task_result(
        path,
        assignment_id="assignment-1",
        attempt_id="attempt-1",
        task_sha256="a" * 64,
        grant_digest="b" * 64,
    )["state"] == "confirmed"
    assert json.loads(path.read_text(encoding="utf-8"))["accepted"] is None


def test_task_result_rejects_identity_mismatch() -> None:
    with pytest.raises(ValueError, match="assignment_id"):
        encode_task_result(task_result(assignment_id=""))


def test_task_result_parse_unknown_does_not_authorize_continuation(tmp_path: Path) -> None:
    path = tmp_path / "task-result.json"
    path.write_text(json.dumps(task_result()), encoding="utf-8")

    result = parse_task_result(
        path,
        assignment_id="assignment-1",
        attempt_id="attempt-1",
        task_sha256="c" * 64,
        grant_digest="b" * 64,
    )

    assert result["state"] == "unknown"
    assert result["continuation_eligible"] is False
