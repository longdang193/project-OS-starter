from __future__ import annotations

import hashlib
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


def lifecycle_receipt(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": contract.RESULT_SCHEMA,
        "attempt_id": "attempt-1",
        "worker": {"state": "exited", "exit_code": 0, "descendant_state": "terminated"},
        "cleanup": {
            "state": "removed",
            "role_views_state": "removed",
            "remaining_paths": [],
            "marker_state": "removed",
        },
        "recovery_required": False,
    }
    value.update(overrides)
    return value


def capability_evidence(**overrides: object) -> dict[str, object]:
    digest = hashlib.sha256(
        json.dumps(["git"], separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    value: dict[str, object] = {
        "requested": ["git"],
        "passed_to_worker": ["git"],
        "validated_available": ["git"],
        "digest": digest,
        "validation_error": None,
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


def test_result_receipt_preserves_canonical_capability_evidence(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    canonical = capability_evidence()
    compatibility = {"requested": ["git"], "available": ["git"], "effective": ["git"]}
    path.write_text(
        json.dumps(
            lifecycle_receipt(
                capabilities=canonical,
                shell_capabilities=compatibility,
            )
        ),
        encoding="utf-8",
    )

    result = contract.parse_result_receipt(path, "attempt-1")

    assert result["capability_state"] == "confirmed"
    assert result["capabilities"] == canonical
    assert result["shell_capabilities"] == compatibility


def test_result_receipt_keeps_lifecycle_proof_without_capability_proof(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(json.dumps(lifecycle_receipt()), encoding="utf-8")

    result = contract.parse_result_receipt(path, "attempt-1")

    assert result["state"] == "confirmed"
    assert result["capability_state"] == "unavailable"
    assert result["capabilities"] is None


def test_result_receipt_rejects_disagreeing_or_invalid_capability_evidence(
    tmp_path: Path,
) -> None:
    compatibility = {"requested": ["git"], "available": ["git"], "effective": ["git"]}
    for name, canonical in (
        ("disagree.json", capability_evidence(requested=["py"])),
        ("bad-digest.json", capability_evidence(digest="0" * 64)),
    ):
        path = tmp_path / name
        path.write_text(
            json.dumps(
                lifecycle_receipt(
                    capabilities=canonical,
                    shell_capabilities=compatibility,
                )
            ),
            encoding="utf-8",
        )

        result = contract.parse_result_receipt(path, "attempt-1")

        assert result["state"] == "confirmed"
        assert result["capability_state"] == "unavailable"
        assert result["capabilities"] is None
