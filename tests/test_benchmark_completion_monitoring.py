from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.benchmark_completion_monitoring as benchmark


def test_completion_rows_label_fake_boundary_evidence_and_unavailable_metrics(
    tmp_path: Path,
) -> None:
    output = tmp_path / "completion.json"

    result = benchmark.main([
        "--baseline-revision",
        "HEAD",
        "--repetitions",
        "1",
        "--output",
        str(output),
    ])

    assert result == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["evidence_kind"] == "fake_boundary_observation"
    assert payload["implementation_delta"]["status"] == "characterization_only"
    assert payload["implementation_delta"]["optimization_claim_allowed"] is False
    assert payload["retention_gate"]["status"] == "not_evaluated"
    assert payload["repetitions_per_case_and_side"] == 1
    assert "busy_worker_three_intervals_late_receipt" in payload["cases"]
    busy_rows = [
        row for row in payload["rows"]
        if row["case"] == "busy_worker_three_intervals_late_receipt"
    ]
    assert busy_rows
    assert all(row["busy_process_observations"] >= 3 for row in busy_rows)
    unresolved_rows = [
        row for row in payload["rows"]
        if row["case"] == "unresolved_retirement"
    ]
    assert all(row["lifecycle"] == "no-report" for row in unresolved_rows)
    assert all(row["cleanup"] == "missing-receipt-fallback" for row in unresolved_rows)
    status = payload["summary"]["candidate"]["measurement_status"]
    assert status["subprocess_total"] == "observed"
    assert status["time_to_receipt_ms"] == "observed"
    assert status["receipt_to_completion_return_ms"] == "observed"
    assert all(row["evidence_kind"] == "fake_boundary_observation" for row in payload["rows"])


def test_completion_monitoring_returns_nonzero_for_incorrect_row(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(benchmark, "source_at_revision", lambda _: Path(benchmark.__file__).read_text(encoding="utf-8"))
    monkeypatch.setattr(benchmark, "revision", lambda: "candidate")
    monkeypatch.setattr(
        benchmark,
        "run_case",
        lambda _module, case: {
            "subprocess_counts": {},
            "subprocess_total": 0,
            "timeout_count": 0,
            "receipt_checks": 0,
            "diagnostic_probe_count": 0,
            "time_to_receipt_ms": None,
            "receipt_to_completion_return_ms": None,
            "lifecycle": "wrong",
            "expected_lifecycle": case["expected"],
            "outcome_match": False,
            "cleanup": "unavailable",
            "reconciliation": "unavailable",
            "elapsed_seconds": 0.0,
            "measurement_status": {
                "subprocess_total": "observed",
                "timeout_count": "observed",
                "receipt_checks": "observed",
                "diagnostic_probe_count": "observed",
                "time_to_receipt_ms": "unavailable",
                "receipt_to_completion_return_ms": "unavailable",
                "elapsed_seconds": "observed",
            },
        },
    )

    assert benchmark.main([
        "--baseline-revision",
        "HEAD",
        "--repetitions",
        "1",
        "--output",
        str(tmp_path / "mismatch.json"),
    ]) == 1


def test_completion_monitoring_marks_different_sources_as_before_after(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output = tmp_path / "different.json"
    monkeypatch.setattr(
        benchmark,
        "source_at_revision",
        lambda _: Path(benchmark.__file__).read_text(encoding="utf-8") + "\n# baseline revision\n",
    )
    monkeypatch.setattr(benchmark, "revision", lambda: "candidate")
    monkeypatch.setattr(
        benchmark,
        "run_case",
        lambda _module, case: {
            "subprocess_counts": {},
            "subprocess_total": 0,
            "timeout_count": 0,
            "busy_process_observations": 0,
            "receipt_checks": 0,
            "diagnostic_probe_count": 0,
            "time_to_receipt_ms": None,
            "receipt_to_completion_return_ms": None,
            "lifecycle": case["expected"],
            "expected_lifecycle": case["expected"],
            "outcome_match": True,
            "cleanup": "unavailable",
            "reconciliation": "unavailable",
            "elapsed_seconds": 0.0,
            "measurement_status": {
                field: "unavailable"
                for field in (
                    "subprocess_total",
                    "timeout_count",
                    "receipt_checks",
                    "diagnostic_probe_count",
                    "busy_process_observations",
                    "time_to_receipt_ms",
                    "receipt_to_completion_return_ms",
                    "elapsed_seconds",
                )
            },
        },
    )

    assert benchmark.main([
        "--baseline-revision",
        "BASELINE",
        "--repetitions",
        "1",
        "--output",
        str(output),
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["implementation_delta"]["status"] == "before_after"
    assert payload["implementation_delta"]["optimization_claim_allowed"] is True
    assert payload["retention_gate"]["status"] == "eligible_for_before_after"
