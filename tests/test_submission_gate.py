from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest

from scripts.project_os_runtime.submission_gate import (
    SubmissionGateConflict,
    claim_submission,
    derive_logical_operation_id,
    gate_path,
    inherit_submission,
    prepare_submission,
    settle_submission,
)


def binding() -> dict[str, str]:
    return {
        "task_sha256": "task-digest",
        "repository_identity": "repo/example",
        "plan_identity": "plan/example",
        "profile": "normal",
        "model_identity": "9router/combo-normal",
        "grant_digest": "grant-digest",
    }


def operation_identity() -> dict[str, str]:
    return {
        "task_id": "task-1",
        "plan_revision": "plan-rev-1",
        "run_id": "run-1",
    }


def test_logical_operation_id_is_stable_and_not_binding_scoped() -> None:
    first = derive_logical_operation_id(**operation_identity())
    second = derive_logical_operation_id(**operation_identity())

    assert first == second
    assert first.startswith("operation-")


def test_claim_persists_intent_and_blocks_restart_after_submission(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)

    claimed = claim_submission(
        path,
        operation_id=operation_id,
        attempt_id="attempt-1",
        binding=binding(),
    )
    assert claimed["state"] == "claimed"
    assert path.is_file()

    settle_submission(path, attempt_id="attempt-1", state="submitted")

    blocked = claim_submission(
        path,
        operation_id=operation_id,
        attempt_id="attempt-2",
        binding=binding(),
    )
    assert blocked["state"] == "blocked"
    assert blocked["reason"] == "submission already recorded"
    assert blocked["record"]["attempt_id"] == "attempt-1"


def test_admission_phase_can_be_reclaimed_after_lease_expiry(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)
    claim_submission(path, operation_id=operation_id, attempt_id="attempt-1", binding=binding())

    record = json.loads(path.read_text(encoding="utf-8"))
    record["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
    path.write_text(json.dumps(record), encoding="utf-8")

    recovered = claim_submission(
        path,
        operation_id=operation_id,
        attempt_id="attempt-2",
        binding=binding(),
    )

    assert recovered["state"] == "claimed"
    assert recovered["record"]["attempt_id"] == "attempt-2"
    assert recovered["record"]["phase"] == "admission"
    assert recovered["record"]["generation"] == 2


def test_delivery_phase_expiry_remains_blocked_for_reconciliation(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)
    claim_submission(path, operation_id=operation_id, attempt_id="attempt-1", binding=binding())
    prepare_submission(path, attempt_id="attempt-1")

    record = json.loads(path.read_text(encoding="utf-8"))
    record["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
    path.write_text(json.dumps(record), encoding="utf-8")

    blocked = claim_submission(
        path,
        operation_id=operation_id,
        attempt_id="attempt-2",
        binding=binding(),
    )

    assert blocked["state"] == "blocked"
    assert blocked["reason"] == "delivery is uncertain"


def test_not_delivered_settlement_allows_a_later_admission_claim(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)
    claim_submission(path, operation_id=operation_id, attempt_id="attempt-1", binding=binding())
    settle_submission(path, attempt_id="attempt-1", state="not_delivered")

    recovered = claim_submission(
        path,
        operation_id=operation_id,
        attempt_id="attempt-2",
        binding=binding(),
    )

    assert recovered["state"] == "claimed"
    assert recovered["record"]["attempt_id"] == "attempt-2"
    assert recovered["record"]["phase"] == "admission"


def test_prepare_submission_persists_delivery_phase(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)
    claim_submission(path, operation_id=operation_id, attempt_id="attempt-1", binding=binding())

    prepared = prepare_submission(path, attempt_id="attempt-1")

    assert prepared["phase"] == "delivery"
    assert prepared["lease_owner"] == "attempt-1"
    assert prepared["lease_expires_at"]


def test_inherit_submission_requires_the_active_parent_delivery_claim(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)
    claim_submission(path, operation_id=operation_id, attempt_id="attempt-1", binding=binding())
    prepare_submission(path, attempt_id="attempt-1")

    inherited = inherit_submission(
        path,
        operation_id=operation_id,
        attempt_id="attempt-1",
        binding=binding(),
    )

    assert inherited["state"] == "inherited"
    assert inherited["record"]["phase"] == "delivery"

    with pytest.raises(SubmissionGateConflict, match="parent attempt mismatch"):
        inherit_submission(
            path,
            operation_id=operation_id,
            attempt_id="attempt-2",
            binding=binding(),
        )


def test_uncertain_submission_blocks_retry_until_reconciled(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)
    claim_submission(path, operation_id=operation_id, attempt_id="attempt-1", binding=binding())
    settle_submission(path, attempt_id="attempt-1", state="delivery_uncertain")

    blocked = claim_submission(
        path,
        operation_id=operation_id,
        attempt_id="attempt-2",
        binding=binding(),
    )

    assert blocked["state"] == "blocked"
    assert blocked["reason"] == "delivery is uncertain"


def test_concurrent_claims_have_one_owner(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)

    def claim(attempt_id: str) -> dict[str, object]:
        return claim_submission(
            path,
            operation_id=operation_id,
            attempt_id=attempt_id,
            binding=binding(),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, ("attempt-1", "attempt-2")))

    assert sorted(result["state"] for result in results) == ["blocked", "claimed"]


def test_conflicting_binding_fails_closed(tmp_path: Path) -> None:
    operation_id = derive_logical_operation_id(**operation_identity())
    path = gate_path(operation_id, root=tmp_path)
    claim_submission(path, operation_id=operation_id, attempt_id="attempt-1", binding=binding())

    with pytest.raises(SubmissionGateConflict, match="binding mismatch"):
        claim_submission(
            path,
            operation_id=operation_id,
            attempt_id="attempt-2",
            binding={**binding(), "grant_digest": "different"},
        )
