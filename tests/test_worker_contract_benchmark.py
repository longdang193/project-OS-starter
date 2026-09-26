from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

import scripts.benchmark_worker_contract as benchmark


FIXTURE = Path(__file__).parent / "fixtures" / "worker_contract_benchmark"


def test_offline_rows_have_two_modes_and_pinned_counts() -> None:
    rows = benchmark.measure_offline(FIXTURE / "manifest.json")

    assert len(rows) == 12
    assert {row["mode"] for row in rows} == {"baseline", "bounded"}
    assert {row["task_id"] for row in rows} == {
        "Task 3", "Task 4", "Task 5", "Task 6", "Task 7", "Task 8"
    }
    for row in rows:
        assert row["tokenizer"] == "cl100k_base"
        assert row["tokenizer_version"]
        assert row["text_sha256"]
        assert row["estimated_tokens"] > 0
        assert row["utf8_bytes"] > 0
        assert row["characters"] > 0


def test_reconstructed_baseline_stays_within_launcher_limit() -> None:
    rows = benchmark.measure_offline(FIXTURE / "manifest.json")

    baseline = [row for row in rows if row["mode"] == "baseline"]

    assert all(row["delivered_handoff_characters"] <= 4096 for row in baseline)
    assert all(row["baseline_name"] == "task-scoped reconstructed baseline" for row in baseline)


def test_fixture_tasks_define_concrete_expected_changes() -> None:
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    plan = (FIXTURE / "benchmark-plan.md").read_text(encoding="utf-8")

    for task in manifest["tasks"]:
        changes = task["required_changes"]
        assert changes
        for path, content in changes.items():
            assert path in plan
            assert content in plan


def test_offline_measurement_is_deterministic() -> None:
    first = benchmark.measure_offline(FIXTURE / "manifest.json")
    second = benchmark.measure_offline(FIXTURE / "manifest.json")

    assert first == second


def test_manifest_rejects_unknown_task(tmp_path: Path) -> None:
    payload = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    payload["tasks"][0]["task_id"] = "Task 99"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    shutil.copy(FIXTURE / "benchmark-plan.md", tmp_path / "benchmark-plan.md")

    with pytest.raises(ValueError, match="unknown selected task"):
        benchmark.measure_offline(path)


def test_binding_leaves_worker_budget_for_native_execution() -> None:
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    binding = benchmark._binding(manifest["tasks"][0], manifest, FIXTURE)

    assert binding["remaining_authorized_task_allowance"] >= 420
