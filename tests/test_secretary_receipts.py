from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from scripts.project_os_runtime.secretary_receipts import (
    ReceiptValidationError,
    build_live_receipt,
    validate_live_receipt,
)


def _receipt(**overrides: object) -> dict[str, object]:
    start = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
    timestamps = {
        "run_started": start.isoformat(),
        "cos_entry": (start + timedelta(seconds=1)).isoformat(),
        "secretary_entry": (start + timedelta(seconds=2)).isoformat(),
        "worker_entry": (start + timedelta(seconds=3)).isoformat(),
        "publication": (start + timedelta(seconds=4)).isoformat(),
        "settlement": (start + timedelta(seconds=5)).isoformat(),
        "acceptance": (start + timedelta(seconds=6)).isoformat(),
        "secretary_exit": (start + timedelta(seconds=7)).isoformat(),
        "cos_exit": (start + timedelta(seconds=8)).isoformat(),
        "run_finished": (start + timedelta(seconds=9)).isoformat(),
    }
    return build_live_receipt(
        binding={
            "pair_id": "pair-1",
            "arm": "candidate",
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "task_id": "task-1",
            "plan_revision": "plan-rev-1",
            "repository_identity": "repo/example",
            "plan_identity": "plan/example",
            "git_revision": "581844d",
            "worktree": "C:/worktree",
            "workstream": "secretary",
            "checkpoint": "plan-rev-1:task-1",
        },
        runtime={
            "provider": "9router",
            "model": "gpt-test",
            "controller_id": "cos-1",
            "session_id": "session-1",
        },
        timestamps=timestamps,
        metrics={
            "cos_turns": 2,
            "secretary_turns": 1,
            "human_interventions": 0,
            "publication_success": True,
            "settlement_proven": True,
            "acceptance_decision": "PASS",
            "token_usage": "unknown",
            "cost": "unknown",
        },
        sources={
            "launch": {"producer": "herdr_main_launcher"},
            "secretary": {"producer": "secretary_live_runtime"},
            "task_result": {"producer": "dcode-project"},
            "settlement": {"producer": "project_os_runtime.attempt"},
            "acceptance": {"producer": "cos"},
        },
    )


def test_live_receipt_accepts_unknown_economics_and_normalizes_provenance() -> None:
    result = validate_live_receipt(_receipt())

    assert result["valid"] is True
    assert result["evidence_provenance"] == "live-attributed"
    assert result["metrics"]["token_usage"] == "unknown"


def test_live_receipt_rejects_binding_mismatch() -> None:
    receipt = _receipt()
    receipt["sources"]["launch"]["attempt_id"] = "attempt-other"

    with pytest.raises(ReceiptValidationError, match="attempt_id"):
        validate_live_receipt(receipt)


def test_live_receipt_rejects_non_monotonic_timestamps() -> None:
    receipt = _receipt()
    receipt["timestamps"]["acceptance"] = receipt["timestamps"]["publication"]
    receipt["timestamps"]["publication"] = receipt["timestamps"]["acceptance"]
    receipt["timestamps"]["acceptance"] = "2026-10-08T09:59:59+00:00"

    with pytest.raises(ReceiptValidationError, match="timestamps"):
        validate_live_receipt(receipt)


def test_live_receipt_rejects_secret_bearing_payload() -> None:
    receipt = _receipt()
    receipt["sources"]["secretary"]["authorization"] = "Bearer secret"

    with pytest.raises(ReceiptValidationError, match="sensitive"):
        validate_live_receipt(receipt)
