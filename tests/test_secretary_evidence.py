from __future__ import annotations

from scripts.project_os_runtime.secretary_evidence import CURRENT, MISSING, STALE, build_evidence_snapshot


def _facts() -> dict[str, object]:
    return {
        "task_ref": "task-result.json",
        "canonical_consequence_ref": "plan-commit.json",
        "reconciled_result_ref": "reconcile.json",
        "project_consequence": "dependency released",
        "attention_delta": {"kind": "dependency_changed"},
        "reconciled_result": {"phase": "integrate", "eligible": True, "complete": True},
    }


def test_build_evidence_snapshot_preserves_references_and_normalized_outcome() -> None:
    snapshot = build_evidence_snapshot(**_facts())

    assert snapshot.status == CURRENT
    assert snapshot.task_ref == "task-result.json"
    assert snapshot.canonical_consequence_ref == "plan-commit.json"
    assert snapshot.to_dict()["sources"]["task"] == "task-result.json"
    assert snapshot.reconciliation == _facts()["reconciled_result"]


def test_build_evidence_snapshot_marks_missing_references_without_revalidation() -> None:
    facts = _facts()
    facts["canonical_consequence_ref"] = None

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == MISSING
    assert "missing canonical consequence reference" in snapshot.reasons


def test_build_evidence_snapshot_marks_blocking_references_stale() -> None:
    facts = _facts()
    facts["blocking_refs"] = ["incident-1", "incident-1"]

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == STALE
    assert snapshot.blocking_refs == ("incident-1",)


def test_build_evidence_snapshot_does_not_recompute_reconciled_result() -> None:
    facts = _facts()
    facts["reconciled_result"] = {"phase": "integrate", "eligible": False, "complete": False}

    snapshot = build_evidence_snapshot(**facts)

    assert snapshot.status == CURRENT
    assert snapshot.reconciliation == facts["reconciled_result"]
