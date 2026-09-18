from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
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
        "repository_identity": "project-OS-starter",
        "plan_identity": "test-plan",
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
        "grant_turns": "native",
        "grant_wall_clock_seconds": "native",
        "grant_child_agents": "deny",
        "mcp_select": [],
        "remaining_authorized_task_allowance": 1800,
        "attempt_deadline": time.monotonic() + 1800,
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

    assert [item["lane_id"] for item in result["admitted"]] == ["a"]
    assert [item["lane_id"] for item in result["blocked"]] == ["b"]
    assert result["rejected"] == []


def test_load_lane_descriptors_rejects_unready_dependency(tmp_path: Path) -> None:
    result = dispatcher.load_lane_descriptors(
        write_lanes(tmp_path, [lane("a", tmp_path, dependency_ready=False)])
    )

    assert result["admitted"] == []
    assert result["rejected"] == []


def test_load_lane_descriptors_requires_remaining_authorized_allowance(tmp_path: Path) -> None:
    item = lane("a", tmp_path)
    item.pop("remaining_authorized_task_allowance")
    result = dispatcher.load_lane_descriptors(
        write_lanes(tmp_path, [item])
    )

    assert result["admitted"] == []
    assert "remaining_authorized_task_allowance" in result["rejected"][0]["reason"]


def test_launcher_command_preserves_boolean_prior_attempt_known(
    tmp_path: Path,
) -> None:
    item = lane("a", tmp_path)
    item["prior_attempt_known"] = "false"

    with pytest.raises(ValueError, match="prior_attempt_known"):
        dispatcher._launcher_command(
            item,
            python_executable="python",
            launcher_path="launcher.py",
        )


def test_load_lane_descriptors_caps_capacity_and_reports_queued_lane(tmp_path: Path) -> None:
    result = dispatcher.load_lane_descriptors(
        write_lanes(tmp_path, [lane("a", tmp_path), lane("b", tmp_path), lane("c", tmp_path)])
    )

    assert [item["lane_id"] for item in result["admitted"]] == ["a", "b"]
    assert result["rejected"] == []
    assert [item["lane_id"] for item in result["deferred"]] == ["c"]


def test_later_conflict_does_not_invalidate_ready_lane(tmp_path: Path) -> None:
    first = lane("a", tmp_path, writes=["shared/file.txt"])
    conflicting = lane("b", tmp_path, writes=["shared/file.txt"])

    result = dispatcher.load_lane_descriptors_from_items([first, conflicting])

    assert [item["lane_id"] for item in result["admitted"]] == ["a"]
    assert [item["lane_id"] for item in result["blocked"]] == ["b"]
    assert result["rejected"] == []


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
    assert {item["lane_id"] for item in result["results"]} == {"a", "b"}


def test_run_parallel_emits_admission_and_terminal_events_once(tmp_path: Path, monkeypatch) -> None:
    events: list[dict[str, object]] = []

    def fake_run_lane(item, **kwargs):
        return {"lane_id": item["lane_id"], "unresolved": False, "capacity": "retired"}

    monkeypatch.setattr(dispatcher, "run_lane", fake_run_lane)
    result = dispatcher.run_parallel(
        [lane("a", tmp_path), lane("b", tmp_path), lane("c", tmp_path)],
        event_callback=events.append,
    )

    assert [event["category"] for event in events[:3]] == [
        "admitted",
        "admitted",
        "deferred",
    ]
    assert [event["tag"] for event in events[3:]] == ["lane_result", "lane_result"]
    assert {event["lane_id"] for event in events[3:]} == {"a", "b"}
    assert len(result["results"]) == 2
    assert result["callback_errors"] == []


def test_duplicate_lane_id_has_one_canonical_admission_and_one_event(
    tmp_path: Path, monkeypatch
) -> None:
    events: list[dict[str, object]] = []
    duplicate = lane("a", tmp_path)

    monkeypatch.setattr(
        dispatcher,
        "run_lane",
        lambda item, **kwargs: {"lane_id": item["lane_id"], "unresolved": False, "capacity": "retired"},
    )
    result = dispatcher.run_parallel([duplicate, dict(duplicate)], event_callback=events.append)

    assert result["admitted"] == []
    assert result["rejected"] == [{"lane_id": "a", "reason": "duplicate lane ID"}]
    assert [event["lane_id"] for event in events] == ["a"]


def test_run_parallel_preserves_callback_errors_without_replacing_result(
    tmp_path: Path, monkeypatch
) -> None:
    def fake_run_lane(item, **kwargs):
        return {"lane_id": item["lane_id"], "unresolved": False, "capacity": "retired"}

    monkeypatch.setattr(dispatcher, "run_lane", fake_run_lane)

    def callback(event):
        if event["tag"] == "lane_result":
            raise RuntimeError("observer failed")

    result = dispatcher.run_parallel([lane("a", tmp_path)], event_callback=callback)

    assert result["results"][0]["lane_id"] == "a"
    assert result["callback_errors"][0]["error"] == "observer failed"


def test_run_parallel_observes_fast_lane_before_slow_sibling_finishes(
    tmp_path: Path, monkeypatch
) -> None:
    slow_started = threading.Event()
    release_slow = threading.Event()
    fast_observed = threading.Event()

    def fake_run_lane(item, **kwargs):
        if item["lane_id"] == "b":
            slow_started.set()
            assert release_slow.wait(timeout=2)
        else:
            assert slow_started.wait(timeout=2)
        return {"lane_id": item["lane_id"], "unresolved": False, "capacity": "retired"}

    def callback(event):
        if event["tag"] == "lane_result" and event["lane_id"] == "a":
            fast_observed.set()
            release_slow.set()

    monkeypatch.setattr(dispatcher, "run_lane", fake_run_lane)
    result = dispatcher.run_parallel(
        [lane("a", tmp_path), lane("b", tmp_path)],
        event_callback=callback,
    )

    assert fast_observed.is_set()
    assert {item["lane_id"] for item in result["results"]} == {"a", "b"}


def test_run_parallel_preserves_pre_admitted_mapping_categories(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        dispatcher,
        "run_lane",
        lambda item, **kwargs: {
            "lane_id": item["lane_id"],
            "unresolved": False,
            "capacity": "retired",
        },
    )
    deferred = {"lane_id": "deferred", "reason": "capacity limit 2"}
    blocked = {"lane_id": "blocked", "reason": "resource conflict"}
    result = dispatcher.run_parallel({
        "admitted": [lane("a", tmp_path)],
        "deferred": [deferred],
        "blocked": [blocked],
        "rejected": [],
    })

    assert result["deferred"] == [deferred]
    assert result["blocked"] == [blocked]


def test_dispatch_cli_flushes_fast_result_before_slow_sibling(tmp_path: Path) -> None:
    lanes_file = write_lanes(tmp_path, [lane("fast", tmp_path), lane("slow", tmp_path)])
    child_code = """
import sys
import time
from scripts import herdr_parallel_dispatch as dispatcher

def fake_run_lane(item, **kwargs):
    if item["lane_id"] == "slow":
        time.sleep(1.0)
    return {"lane_id": item["lane_id"], "unresolved": False, "capacity": "retired"}

dispatcher.run_lane = fake_run_lane
raise SystemExit(dispatcher.main(["--lanes-file", sys.argv[1]]))
"""
    process = subprocess.Popen(
        [sys.executable, "-c", child_code, str(lanes_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    try:
        admissions = [json.loads(process.stdout.readline()) for _ in range(2)]
        fast_result = json.loads(process.stdout.readline())
        assert all(item["tag"] == "lane_admission" for item in admissions)
        assert fast_result["tag"] == "lane_result"
        assert fast_result["lane_id"] == "fast"
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=3)


def test_run_lane_expired_dispatch_deadline_retires_unowned_capacity(tmp_path: Path) -> None:
    launched = False

    def popen(*args, **kwargs):
        nonlocal launched
        launched = True
        raise AssertionError("expired dispatch launched")

    item = lane("a", tmp_path)
    item["attempt_deadline"] = time.monotonic() - 1
    result = dispatcher.run_lane(item, popen_factory=popen)

    assert launched is False
    assert result["capacity"] == "retired"
    assert result["unresolved"] is False
    assert result["failure_kind"] == "dispatch_deadline_exceeded"


def test_run_lane_capability_projection_does_not_prove_worker_capability(
    tmp_path: Path,
) -> None:
    item = lane("a", tmp_path)
    item["local_capabilities"] = ["git"]
    dispatcher._bind_requested_grant(item)
    parsed = {
        "preparation": {
            "registry_launcher": {
                "runtime_grant": item["runtime_grant"],
                "grant_digest": item["grant_digest"],
                "local_capabilities": item["local_capabilities"],
            }
        },
        "assignment": {
            "grant_digest": item["grant_digest"],
            "local_capabilities": item["local_capabilities"],
            "capability_state": "unavailable",
        },
    }

    assert dispatcher._grant_evidence_matches(item, parsed) is False


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
        "unresolved",
    ]
    assert result["capacity"] == "occupied"


def test_run_lane_zero_exit_without_final_assignment_stays_occupied(tmp_path: Path) -> None:
    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return json.dumps({"registry_launcher": {"attempt_id": "a"}}), ""

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert result["unresolved"] is True
    assert result["capacity"] == "occupied"


@pytest.mark.parametrize(
    ("assignment", "expected_reason"),
    [
        ({"attempt_id": "a", "execution": {"state": "unknown"}}, "execution"),
        ({"attempt_id": "a", "cleanup": {"state": "unverified"}}, "cleanup"),
        ({"attempt_id": "a", "reconciliation_required": True}, "reconciliation"),
    ],
)
def test_run_lane_uncertain_final_assignment_stays_occupied(
    tmp_path: Path,
    assignment: dict[str, object],
    expected_reason: str,
) -> None:
    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                "\n".join(
                    [
                        json.dumps({"registry_launcher": {"attempt_id": "a"}}),
                        json.dumps({"assignment": assignment}),
                    ]
                ),
                "",
            )

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert result["unresolved"] is True, expected_reason
    assert result["capacity"] == "occupied"


def test_run_lane_valid_settled_assignment_retires_capacity(tmp_path: Path) -> None:
    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                json.dumps({"registry_launcher": {"attempt_id": "a"}})
                + "\n"
                + json.dumps(
                    {
                        "assignment": {
                            "attempt_id": "a",
                            "execution": {"state": "exited"},
                            "cleanup": {"state": "removed"},
                            "reconciliation_required": False,
                        }
                    }
                ),
                "",
            )

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert result["unresolved"] is True
    assert result["capacity"] == "occupied"


def test_run_lane_task_uncertainty_does_not_keep_settled_resources_occupied(
    tmp_path: Path,
) -> None:
    item = lane("a", tmp_path)
    dispatcher._bind_requested_grant(item)
    class CompletedProcess:
        returncode = 2

        def communicate(self, *, timeout):
            return (
                "\n".join(
                    [
                            json.dumps({"registry_launcher": {"attempt_id": "a", "runtime_grant": item["runtime_grant"], "grant_digest": item["grant_digest"]}}),
                        json.dumps(
                            {
                                    "assignment": {
                                        "attempt_id": "a",
                                        "grant_digest": item["grant_digest"],
                                        "execution": {
                                            "state": "exited",
                                            "descendant_state": "terminated",
                                        },
                                        "lifecycle_receipt": {
                                            "worker_state": "exited",
                                            "descendant_state": "terminated",
                                            "cleanup_state": "removed",
                                            "recovery_required": False,
                                        },
                                    "task_result": {"state": "unverified", "accepted": None},
                                    "cleanup": {"state": "removed", "recovery_required": False},
                                    "reconciliation_required": True,
                                }
                            }
                        ),
                    ]
                ),
                "",
            )

    result = dispatcher.run_lane(
        item,
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert result["unresolved"] is True
    assert result["capacity"] == "retired"


def test_run_lane_malformed_evidence_keeps_capacity_occupied(tmp_path: Path) -> None:
    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                "\n".join(
                    [
                        json.dumps({"registry_launcher": {"attempt_id": "a"}}),
                        json.dumps(
                            {
                                "assignment": {
                                    "attempt_id": "a",
                                    "execution": {"state": "exited"},
                                    "cleanup": {"state": "removed"},
                                    "reconciliation_required": False,
                                }
                            }
                        ),
                        "not-json",
                    ]
                ),
                "",
            )

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert result["unresolved"] is True
    assert result["capacity"] == "occupied"


def test_run_lane_rejects_unsupported_executor_before_launch(tmp_path: Path) -> None:
    rejected = lane("a", tmp_path)
    rejected["executor"] = "codex"
    launched = False

    def popen(*args, **kwargs):
        nonlocal launched
        launched = True
        raise AssertionError("unsupported executor launched")

    result = dispatcher.run_lane(rejected, popen_factory=popen)

    assert result["failure_kind"] == "unsupported_executor"
    assert result["unresolved"] is False
    assert result["capacity"] == "retired"
    assert launched is False


def test_run_parallel_revalidates_mapping_admission_bypass(tmp_path: Path, monkeypatch) -> None:
    rejected = lane("a", tmp_path)
    rejected["executor"] = "codex"
    launched = False

    def fake_run_lane(*args, **kwargs):
        nonlocal launched
        launched = True
        raise AssertionError("mapping admission bypass launched")

    monkeypatch.setattr(dispatcher, "run_lane", fake_run_lane)
    result = dispatcher.run_parallel({"admitted": [rejected], "rejected": []})

    assert result["admitted"] == []
    assert result["results"] == []
    assert result["rejected"] == [
        {"lane_id": "a", "reason": "unsupported executor: codex"}
    ]
    assert launched is False


def test_parse_launcher_records_mismatched_attempt_preserves_evidence_without_settling() -> None:
    parsed = dispatcher.parse_launcher_records(
        "\n".join(
            [
                json.dumps({"registry_launcher": {"attempt_id": "preparation"}}),
                json.dumps(
                    {
                        "assignment": {
                            "attempt_id": "foreign",
                            "status": "completed",
                        }
                    }
                ),
            ]
        ),
        lane_id="a",
    )

    assert parsed["assignment"] is None
    assert [item["tag"] for item in parsed["records"]] == [
        "preparation",
        "final_assignment",
    ]
    assert parsed["records"][1]["payload"]["attempt_id"] == "foreign"


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


def test_run_lane_zero_exit_without_final_assignment_stays_unresolved(tmp_path: Path) -> None:
    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (json.dumps({"registry_launcher": {"attempt_id": "a"}}), "")

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert result["unresolved"] is True
    assert result["capacity"] == "occupied"


def test_run_lane_final_assignment_attempt_mismatch_preserves_evidence(tmp_path: Path) -> None:
    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                json.dumps({"registry_launcher": {"attempt_id": "prep"}})
                + "\n"
                + json.dumps({"assignment": {"attempt_id": "final", "status": "completed"}}),
                "",
            )

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert result["records"][0]["tag"] == "preparation"
    assert result["records"][1]["tag"] == "final_assignment"
    assert result["capacity"] == "occupied"
    assert result["unresolved"] is True


def test_run_lane_timeout_before_preparation_preserves_partial_streams(tmp_path: Path) -> None:
    class TimedOut:
        pid = 417
        returncode = None

        def communicate(self, *, timeout):
            raise subprocess.TimeoutExpired(
                "launcher",
                timeout,
                output=b'{"registry_launcher":{"attempt_id":"attempt-before"}}\n',
                stderr=b"prep warning",
            )

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: TimedOut(),
        timeout_seconds=0.01,
    )

    assert result["preparation"]["registry_launcher"]["attempt_id"] == "attempt-before"
    assert result["stdout"] == '{"registry_launcher":{"attempt_id":"attempt-before"}}\n'
    assert result["stderr"] == "prep warning"
    assert result["attempt_id"] == "attempt-before"
    assert result["process_identity"] == {"pid": 417}
    assert result["reconciliation_required"] is True
    assert result["capacity"] == "occupied"


def test_run_lane_timeout_after_preparation_preserves_partial_streams_and_ownership(
    tmp_path: Path,
) -> None:
    class TimedOut:
        pid = 418
        returncode = None

        def communicate(self, *, timeout):
            raise subprocess.TimeoutExpired(
                "launcher",
                timeout,
                output='{"registry_launcher":{"attempt_id":"attempt-after"}}\n',
                stderr="worker warning",
            )

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: TimedOut(),
        timeout_seconds=0.01,
    )

    assert result["attempt_id"] == "attempt-after"
    assert result["stdout"].endswith("\n")
    assert result["stderr"] == "worker warning"
    assert result["ownership"] == "reconciliation_required"
    assert result["capacity"] == "occupied"


def test_run_lane_decodes_byte_streams_and_reports_incomplete_trailing_json(
    tmp_path: Path,
) -> None:
    class CompletedProcess:
        pid = 419
        returncode = 0

        def communicate(self, *, timeout):
            return (
                b'{"registry_launcher":{"attempt_id":"a"}}\n{"assignment":{"attempt_id":"a"',
                b"byte stderr",
            )

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: CompletedProcess(),
    )

    assert result["malformed"] == ['{"assignment":{"attempt_id":"a"']
    assert result["stderr"] == "byte stderr"
    assert result["process_identity"] == {"pid": 419}
    assert result["capacity"] == "occupied"


@pytest.mark.parametrize("descendant_state", [None, "unknown"])
def test_run_lane_missing_or_unknown_descendant_state_stays_occupied(
    tmp_path: Path, descendant_state: str | None,
) -> None:
    assignment = {
        "attempt_id": "a",
        "execution": {"state": "exited", **({"descendant_state": descendant_state} if descendant_state else {})},
        "lifecycle_receipt": {
            "worker_state": "exited",
            "descendant_state": descendant_state or "unknown",
            "cleanup_state": "removed",
            "recovery_required": False,
        },
        "cleanup": {"state": "removed", "recovery_required": False},
        "reconciliation_required": False,
    }

    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                json.dumps({"registry_launcher": {"attempt_id": "a"}})
                + "\n"
                + json.dumps({"assignment": assignment}),
                "",
            )

    result = dispatcher.run_lane(lane("a", tmp_path), popen_factory=lambda *args, **kwargs: CompletedProcess())

    assert result["capacity"] == "occupied"
    assert result["unresolved"] is True


@pytest.mark.parametrize("descendant_state", ["terminated", "not_started"])
def test_run_lane_explicit_descendant_retirement_requires_cleanup(
    tmp_path: Path, descendant_state: str,
) -> None:
    item = lane("a", tmp_path)
    dispatcher._bind_requested_grant(item)
    assignment = {
        "attempt_id": "a",
        "grant_digest": item["grant_digest"],
        "execution": {"state": "exited", "descendant_state": descendant_state},
        "lifecycle_receipt": {
            "worker_state": "exited",
            "descendant_state": descendant_state,
            "cleanup_state": "removed",
            "recovery_required": False,
        },
        "cleanup": {"state": "removed", "recovery_required": False},
        "reconciliation_required": False,
    }

    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                    json.dumps({"registry_launcher": {"attempt_id": "a", "runtime_grant": item["runtime_grant"], "grant_digest": item["grant_digest"]}})
                + "\n"
                + json.dumps({"assignment": assignment}),
                "",
            )

    result = dispatcher.run_lane(item, popen_factory=lambda *args, **kwargs: CompletedProcess())

    assert result["capacity"] == "retired"
    assert result["unresolved"] is True


def test_launcher_command_forwards_admitted_runtime_grant_and_mcp_select(tmp_path: Path) -> None:
    item = lane("a", tmp_path)
    item.update({
        "grant_turns": 8,
        "grant_wall_clock_seconds": 600,
        "grant_child_agents": "allow",
        "mcp_select": ["context7.query_docs"],
        "prior_attempt_known": True,
    })

    command = dispatcher._launcher_command(item, python_executable="python", launcher_path="launcher.py")

    assert command[command.index("--grant-turns") + 1] == "8"
    assert command[command.index("--grant-wall-clock-seconds") + 1] == "600"
    assert command[command.index("--grant-child-agents") + 1] == "allow"
    assert command[command.index("--mcp-select") + 1] == "context7.query_docs"
    assert command[command.index("--prior-attempt-known") + 1] == "true"
    assert command[command.index("--repository-identity") + 1] == "project-OS-starter"
    assert command[command.index("--plan-identity") + 1] == "test-plan"
    assert command[command.index("--task-sha256") + 1] == dispatcher._sha256_text("task a")
    assert command[command.index("--assignment-id") + 1] == dispatcher._assignment_id(
        "project-OS-starter", "test-plan", "a"
    )


def test_effective_budget_accepts_contained_explicit_grant_above_native_default() -> None:
    requested = {
        "turns": {"requested": 8},
        "wall_clock_seconds": {"requested": 600},
    }
    observed = {
        "turns": {"requested": 8, "effective": 8},
        "wall_clock_seconds": {"requested": 600, "effective": 600},
    }

    assert dispatcher._effective_budget_is_contained(requested, observed)


def test_run_lane_grant_digest_mismatch_keeps_settled_capacity_reusable(tmp_path: Path) -> None:
    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                "\n".join([
                    json.dumps({"registry_launcher": {
                        "attempt_id": "a",
                        "runtime_grant": {"turns": {"requested": 8}},
                        "grant_digest": "prep-digest",
                    }}),
                    json.dumps({"assignment": {
                        "attempt_id": "a",
                        "grant_digest": "final-digest",
                        "execution": {"state": "exited", "descendant_state": "terminated"},
                        "lifecycle_receipt": {
                            "worker_state": "exited",
                            "descendant_state": "terminated",
                            "cleanup_state": "removed",
                            "recovery_required": False,
                        },
                        "cleanup": {"state": "removed", "recovery_required": False},
                        "reconciliation_required": False,
                    }}),
                ]),
                "",
            )

    result = dispatcher.run_lane(lane("a", tmp_path), popen_factory=lambda *args, **kwargs: CompletedProcess())

    assert result["capacity"] == "retired"
    assert result["unresolved"] is True
    assert result["grant_verification"] == "unverified"
    assert result["verification_failure"] == "grant_mismatch"


def test_run_lane_stale_assignment_identity_keeps_capacity_occupied(tmp_path: Path) -> None:
    item = lane("a", tmp_path)
    dispatcher._bind_requested_grant(item)
    task_sha256 = dispatcher._sha256_text(str(item["task"]))

    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                "\n".join([
                    json.dumps({"registry_launcher": {
                        "attempt_id": "a",
                        "assignment_id": "stale-assignment",
                        "assignment_task_sha256": task_sha256,
                        "runtime_grant": item["runtime_grant"],
                        "grant_digest": item["grant_digest"],
                    }}),
                    json.dumps({"assignment": {
                        "attempt_id": "a",
                        "assignment_id": "stale-assignment",
                        "task_sha256": task_sha256,
                        "grant_digest": item["grant_digest"],
                        "execution": {"state": "exited", "descendant_state": "terminated"},
                        "lifecycle_receipt": {
                            "worker_state": "exited",
                            "descendant_state": "terminated",
                            "cleanup_state": "removed",
                            "recovery_required": False,
                        },
                        "cleanup": {"state": "removed", "recovery_required": False},
                    }}),
                ]),
                "",
            )

    result = dispatcher.run_lane(item, popen_factory=lambda *args, **kwargs: CompletedProcess())

    assert result["capacity"] == "occupied"
    assert result["unresolved"] is True
    assert result["failure_kind"] == "receipt_correlation_mismatch"


def test_admission_rejects_conflicting_top_level_and_nested_mcp_selectors(tmp_path: Path) -> None:
    item = lane("a", tmp_path)
    item.update({"mcp_select": ["context7"], "runtime_grant": {"mcp_select": ["playwright"]}})

    result = dispatcher.load_lane_descriptors(write_lanes(tmp_path, [item]))

    assert result["admitted"] == []
    assert "MCP" in result["rejected"][0]["reason"]


def test_dispatcher_consumes_actual_launcher_assignment_json_with_pending_cos_acceptance(
    tmp_path: Path,
) -> None:
    from scripts import herdr_main_launcher as launcher

    item = lane("a", tmp_path)
    dispatcher._bind_requested_grant(item)

    classified = launcher._classify_deepagents_outcome(
        delivery={"state": "delivered", "certainty": "confirmed", "prompt_accepted": True},
        observation={"state": "completed", "report_present": True, "observation_error": None},
        receipt={
            "state": "confirmed",
            "worker_state": "exited",
            "worker_exit_code": 0,
            "descendant_state": "terminated",
            "cleanup_state": "removed",
        },
        fallback_failure_kind=None,
    )
    emitted = launcher._build_assignment_result(
        dispatch_id="dispatch",
        attempt_id="a",
        agent_name="normal-main",
        delivery=classified["delivery"],
        execution=classified["execution"],
        observation=classified["observation"],
        task_result=classified["task_result"],
        cleanup=classified["cleanup"],
        performance={"status": "measured"},
        launcher_exit_code=classified["launcher_exit_code"],
        legacy={"status": classified["status"], "reconciliation_required": classified["reconciliation_required"]},
    )
    emitted["assignment"]["grant_digest"] = item["grant_digest"]
    emitted["assignment"]["lifecycle_receipt"] = {
        "worker_state": "exited",
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "recovery_required": False,
    }

    class CompletedProcess:
        returncode = 0

        def communicate(self, *, timeout):
            return (
                    json.dumps({"registry_launcher": {"attempt_id": "a", "runtime_grant": item["runtime_grant"], "grant_digest": item["grant_digest"]}})
                + "\n"
                + json.dumps(emitted),
                "",
            )

    result = dispatcher.run_lane(item, popen_factory=lambda *args, **kwargs: CompletedProcess())

    assert result["assignment"]["task_result"]["state"] == "reported_completed"
    assert result["assignment"]["task_result"]["accepted"] is None
    assert result["capacity"] == "retired"
    assert result["unresolved"] is False
    assert result["acceptance_pending"] is True


def test_finish_timed_out_process_drains_closes_and_reaps() -> None:
    class Pipe:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class TimedOut:
        pid = 420
        returncode = None

        def __init__(self) -> None:
            self.stdout = Pipe()
            self.stderr = Pipe()
            self.calls = 0

        def communicate(self, *, timeout):
            self.calls += 1
            self.returncode = 0
            return (b"tail", b"err-tail")

        def wait(self, *, timeout):
            self.returncode = 0
            return 0

    process = TimedOut()
    stdout, stderr, reaped = dispatcher._finish_timed_out_process(
        process,
        subprocess.TimeoutExpired("launcher", 0.01, output=b"head", stderr=b"err"),
    )

    assert (stdout, stderr, reaped) == ("headtail", "err-tail", True)
    assert process.calls == 1
    assert process.stdout.closed is True
    assert process.stderr.closed is True


def test_runtime_completion_does_not_equal_acceptance() -> None:
    assert dispatcher.runtime_completion_is_not_acceptance({"status": "reported_completed"})


def test_timeout_owner_is_worker_runtime() -> None:
    assert dispatcher.TIMEOUT_OWNER == "dcode-project"


def test_local_capabilities_admission_normalizes_without_host_availability_check(
    tmp_path: Path,
) -> None:
    item = lane("a", tmp_path)
    item["local_capabilities"] = ["Node"]
    dispatcher._bind_requested_grant(item)
    assert item["local_capabilities"]["effective"] == ["node"]
    assert "--local-capability" in dispatcher._launcher_command(
        item, python_executable="python", launcher_path="launcher.py"
    )


def test_local_capability_evidence_mismatch_stays_unverified(tmp_path: Path) -> None:
    item = lane("a", tmp_path)
    item["local_capabilities"] = ["git"]
    dispatcher._bind_requested_grant(item)
    parsed = {
        "preparation": {"registry_launcher": {
            "runtime_grant": item["runtime_grant"], "grant_digest": item["grant_digest"],
            "local_capabilities": {**item["local_capabilities"], "digest": "wrong"},
        }},
        "assignment": {"grant_digest": item["grant_digest"], "local_capabilities": item["local_capabilities"]},
    }
    assert dispatcher._grant_evidence_matches(item, parsed) is False


def test_grant_evidence_uses_stable_requested_binding_for_dynamic_budget(tmp_path: Path) -> None:
    item = lane("a", tmp_path)
    dispatcher._bind_requested_grant(item)
    effective = dict(item["runtime_grant"])
    effective["turns"] = {"requested": "native", "effective": 8, "enforcement": "runtime"}
    effective["wall_clock_seconds"] = {
        "requested": "native", "effective": 420, "enforcement": "runtime"
    }
    parsed = {
        "preparation": {"registry_launcher": {
            "runtime_grant": effective,
            "grant_digest": item["grant_digest"],
        }},
        "assignment": {"grant_digest": item["grant_digest"]},
    }
    assert dispatcher._grant_evidence_matches(item, parsed) is True


def test_mismatched_stable_grant_digest_stays_unverified(tmp_path: Path) -> None:
    item = lane("a", tmp_path)
    dispatcher._bind_requested_grant(item)
    parsed = {
        "preparation": {"registry_launcher": {
            "runtime_grant": item["runtime_grant"], "grant_digest": "wrong",
        }},
        "assignment": {"grant_digest": "wrong"},
    }
    assert dispatcher._grant_evidence_matches(item, parsed) is False


def test_empty_capability_evidence_defaults_without_rejection(tmp_path: Path) -> None:
    item = lane("a", tmp_path)
    dispatcher._bind_requested_grant(item)
    parsed = {
        "preparation": {"registry_launcher": {
            "runtime_grant": item["runtime_grant"],
            "grant_digest": item["grant_digest"],
            "local_capabilities": {},
        }},
        "assignment": {
            "grant_digest": item["grant_digest"],
            "local_capabilities": {},
        },
    }
    assert "local_capabilities" not in item
    assert dispatcher._grant_evidence_matches(item, parsed) is True


def test_run_lane_timeout_preserves_file_backed_late_output(tmp_path: Path) -> None:
    class TimedOut:
        pid = 421
        returncode = None

        def __init__(self, stdout, stderr) -> None:
            self.stdout_file = stdout
            self.stderr_file = stderr
            self.calls = 0

        def communicate(self, *, timeout):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired(
                    "launcher",
                    timeout,
                    output='{"registry_launcher":{"attempt_id":"attempt-late"}}\n',
                )
            self.stdout_file.write(
                '{"assignment":{"attempt_id":"attempt-late","status":"reported_completed"}}\n'
            )
            self.stdout_file.flush()
            raise subprocess.TimeoutExpired("launcher", timeout)

    process = None

    def popen_factory(*args, **kwargs):
        nonlocal process
        process = TimedOut(kwargs["stdout"], kwargs["stderr"])
        return process

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=popen_factory,
        timeout_seconds=0.01,
    )

    assert process is not None
    collector = result["timeout_evidence"]
    assert collector["owner"] == dispatcher.TIMEOUT_OWNER
    assert collector["pid"] == 421
    assert collector["attempt_id"] == "attempt-late"
    assert collector["capacity"] == "occupied"
    assert Path(collector["paths"]["stdout"]).read_text(encoding="utf-8").endswith(
        '"attempt_id":"attempt-late","status":"reported_completed"}}\n'
    )
    assert Path(collector["paths"]["handoff"]).is_file()
    assert result["capacity"] == "occupied"


def test_run_lane_timeout_without_reaping_keeps_capacity_occupied(tmp_path: Path) -> None:
    class NotReaped:
        pid = 422
        returncode = None

        def communicate(self, *, timeout):
            return ("late output", "")

    result = dispatcher.run_lane(
        lane("a", tmp_path),
        popen_factory=lambda *args, **kwargs: NotReaped(),
        timeout_seconds=0.01,
    )

    assert result["reaped"] is False
    assert result["capacity"] == "occupied"
    assert result["timeout_evidence"]["capacity"] == "occupied"
