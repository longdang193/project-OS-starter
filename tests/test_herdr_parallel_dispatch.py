from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

import pytest

from scripts import herdr_parallel_dispatch as dispatcher


def lane(
    lane_id: str,
    root: Path,
    *,
    pane: str | None = None,
    writes: list[str] | None = None,
    dependency_ready: bool = True,
) -> dict[str, object]:
    return {
        "lane_id": lane_id,
        "task": f"task {lane_id}",
        "executor": "deepagents",
        "profile": "normal",
        "worktree": str(root / lane_id),
        "expected_base": "c086339c08bb396d32be44a2b848b1ab473fa52c",
        "session": "session",
        "pane": pane or lane_id,
        "allowed_write_set": writes or [f"pilot-artifacts/{lane_id}.txt"],
        "dependencies": [],
        "dependency_ready": dependency_ready,
        "fixed_contracts": ["parallel-dispatch-v1"],
        "mutable_resources": [f"resource-{lane_id}"],
    }


def write_lanes(tmp_path: Path, lanes: list[dict[str, object]]) -> Path:
    path = tmp_path / "lanes.json"
    path.write_text(json.dumps(lanes), encoding="utf-8")
    return path


def test_load_lane_descriptors_admits_two_isolated_lanes(tmp_path: Path) -> None:
    result = dispatcher.load_lane_descriptors(
        write_lanes(tmp_path, [lane("a", tmp_path), lane("b", tmp_path)])
    )

    assert [item["lane_id"] for item in result["admitted"]] == ["a", "b"]
    assert result["rejected"] == []


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (lambda lanes, root: lanes[1].update({"worktree": lanes[0]["worktree"]}), "worktree"),
        (
            lambda lanes, root: lanes[1].update({"allowed_write_set": lanes[0]["allowed_write_set"]}),
            "write set",
        ),
        (lambda lanes, root: lanes[1].update({"pane": lanes[0]["pane"]}), "pane"),
    ],
)
def test_load_lane_descriptors_rejects_shared_resources(
    tmp_path: Path,
    change,
    reason: str,
) -> None:
    lanes = [lane("a", tmp_path), lane("b", tmp_path)]
    change(lanes, tmp_path)

    result = dispatcher.load_lane_descriptors(write_lanes(tmp_path, lanes))

    assert result["admitted"] == []
    assert all(reason in item["reason"] for item in result["rejected"])


def test_load_lane_descriptors_rejects_unready_dependency(tmp_path: Path) -> None:
    result = dispatcher.load_lane_descriptors(
        write_lanes(tmp_path, [lane("a", tmp_path, dependency_ready=False)])
    )

    assert result["admitted"] == []
    assert result["rejected"][0]["reason"] == "dependency not ready"


def test_load_lane_descriptors_caps_capacity_and_reports_queued_lane(tmp_path: Path) -> None:
    result = dispatcher.load_lane_descriptors(
        write_lanes(tmp_path, [lane("a", tmp_path), lane("b", tmp_path), lane("c", tmp_path)])
    )

    assert [item["lane_id"] for item in result["admitted"]] == ["a", "b"]
    assert result["rejected"] == [{"lane_id": "c", "reason": "capacity limit 2"}]


def test_run_parallel_starts_both_lanes_before_either_finishes(tmp_path: Path, monkeypatch) -> None:
    lanes = [lane("a", tmp_path), lane("b", tmp_path)]
    started: set[str] = set()
    finished: set[str] = set()
    barrier = threading.Barrier(2)

    def fake_run_lane(item, **kwargs):
        started.add(item["lane_id"])
        barrier.wait(timeout=2)
        finished.add(item["lane_id"])
        return {"lane_id": item["lane_id"], "unresolved": False, "capacity": "retired"}

    monkeypatch.setattr(dispatcher, "run_lane", fake_run_lane)
    result = dispatcher.run_parallel(lanes)

    assert started == {"a", "b"}
    assert finished == {"a", "b"}
    assert [item["lane_id"] for item in result["results"]] == ["a", "b"]


def test_run_parallel_preserves_sibling_failure(monkeypatch, tmp_path: Path) -> None:
    lanes = [lane("a", tmp_path), lane("b", tmp_path)]

    def fake_run_lane(item, **kwargs):
        if item["lane_id"] == "a":
            return {
                "lane_id": "a",
                "unresolved": False,
                "capacity": "retired",
                "failure_kind": "command_exit",
            }
        return {"lane_id": "b", "unresolved": False, "capacity": "retired"}

    monkeypatch.setattr(dispatcher, "run_lane", fake_run_lane)
    result = dispatcher.run_parallel(lanes)

    assert [item["lane_id"] for item in result["results"]] == ["a", "b"]
    assert result["results"][0]["failure_kind"] == "command_exit"
    assert result["results"][1]["unresolved"] is False


def test_parse_launcher_records_separates_preparation_and_assignment() -> None:
    parsed = dispatcher.parse_launcher_records(
        '\n'.join(
            [
                json.dumps({"registry_launcher": {"dispatch_id": "d", "attempt_id": "a"}}),
                json.dumps({"assignment": {"attempt_id": "a", "status": "completed"}}),
                "not-json",
            ]
        ),
        lane_id="a",
    )

    assert parsed["preparation"]["registry_launcher"]["attempt_id"] == "a"
    assert parsed["assignment"]["status"] == "completed"
    assert [item["tag"] for item in parsed["records"]] == ["preparation", "final_assignment"]
    assert parsed["malformed"] == ["not-json"]


def test_run_lane_timeout_keeps_capacity_occupied(tmp_path: Path) -> None:
    class HangingProcess:
        returncode = None

        def communicate(self, *, timeout):
            raise subprocess.TimeoutExpired("launcher", timeout)

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: HangingProcess(),
        timeout_seconds=0.01,
    )

    assert result["unresolved"] is True
    assert result["capacity"] == "occupied"
    assert result["failure_kind"] == "transport_timeout"


def test_run_lane_start_failure_is_settled_without_retiring_siblings(tmp_path: Path) -> None:
    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: (_ for _ in ()).throw(OSError("pane unavailable")),
    )

    assert result["failure_kind"] == "launch_failed"
    assert result["unresolved"] is False
    assert result["capacity"] == "retired"


def test_run_lane_tags_child_exit_and_capacity(tmp_path: Path) -> None:
    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                json.dumps({"registry_launcher": {"attempt_id": "a"}})
                + "\n"
                + json.dumps({"assignment": {"attempt_id": "a", "status": "completed"}}),
                "",
            )

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert [item["tag"] for item in result["records"]] == [
        "preparation",
        "final_assignment",
        "child_exit",
        "capacity",
    ]
    assert result["capacity"] == "retired"


def test_run_parallel_interruption_stops_admission(monkeypatch, tmp_path: Path) -> None:
    stop_event = threading.Event()
    stop_event.set()
    launched = []

    def fake_run_lane(item, **kwargs):
        launched.append(item["lane_id"])
        return {"lane_id": item["lane_id"], "unresolved": False, "capacity": "retired"}

    monkeypatch.setattr(dispatcher, "run_lane", fake_run_lane)
    result = dispatcher.run_parallel(
        [lane("a", tmp_path), lane("b", tmp_path)],
        stop_event=stop_event,
    )

    assert result["interrupted"] is True
    assert launched == []
    assert result["results"] == []
