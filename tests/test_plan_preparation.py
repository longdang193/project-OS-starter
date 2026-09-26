from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import textwrap
import pytest

from scripts import herdr_parallel_dispatch as dispatcher
from scripts.project_os_runtime.plan_preparation import (
    load_plan,
    parse_plan,
    prepare_lane_inputs,
    prepare_plan_lanes,
    prepare_task,
)
from scripts.project_os_runtime.lane import prepare_lane
from scripts.planning_dependencies import parse_dependency_field, validate_dependency_graph


PLAN = """# Plan

## Goal
Reduce repeated coordination.

## Execution Approach
- Required skills: `skill-backend-verification`, `skill-code-standards`

## Coordination State

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `deepagents` | none | parser proof | evidence-1 |
| Task 2 | `completed` | current | `deepagents` | Task 1 | projection proof | evidence-2 |
| Task 3 | `pending` | current | `deepagents` | Tasks 1, 2 | dispatch proof | pending |
| Task 4 | `pending` | current | `deepagents` | Tasks 1-3 | final proof | pending |

## Task Breakdown

### Task 1: Parse source
**Template Profile:**
- Controller-selected: `normal`

### Task 2: Build projection
**Template Profile:**
- Controller-selected: `normal`

### Task 3: Dispatch work
**Template Profile:**
- Controller-selected: `normal`

### Task 4: Verify result
**Template Profile:**
- Controller-selected: `normal`
"""



def test_repo_runtime_wins_over_shared_runtime_namespace() -> None:
    repo = Path(__file__).resolve().parent.parent
    shared = Path.home() / ".agents" / "project-os"
    probe = """
import importlib
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
shared = Path(sys.argv[2]).resolve()
sys.path[:] = [str(shared), str(repo), *[item for item in sys.path if item not in {str(shared), str(repo)}]]
for name in ("scripts", "scripts.project_os_runtime", "scripts.project_os_runtime.plan_preparation", "scripts.herdr_parallel_dispatch", "scripts.herdr_main_launcher", "scripts.dcode_project", "scripts.deepagents_result_contract", "scripts.herdr_attempt_contract"):
    module = importlib.import_module(name)
    assert Path(module.__file__).resolve().is_relative_to(repo)
assert hasattr(importlib.import_module("scripts.herdr_parallel_dispatch"), "run_parallel_from_plan")
"""
    completed = subprocess.run(
        [sys.executable, "-c", probe, str(repo), str(shared)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

def test_parse_plan_parses_all_supported_dependency_forms() -> None:
    graph = parse_plan(PLAN)

    assert tuple(graph.tasks) == ("Task 1", "Task 2", "Task 3", "Task 4")
    assert graph.tasks["Task 3"].dependencies == ("Task 1", "Task 2")
    assert graph.tasks["Task 4"].dependencies == ("Task 1", "Task 2", "Task 3")
    assert graph.tasks["Task 2"].profile == "normal"

def test_parse_plan_parses_three_named_dependencies() -> None:
    plan = PLAN.replace("Tasks 1-3", "Task 1, Task 2, Task 3")

    assert parse_plan(plan).tasks["Task 4"].dependencies == ("Task 1", "Task 2", "Task 3")


def test_parse_plan_rejects_invalid_graph() -> None:
    invalid_plans = [
        PLAN.replace("| Task 4 |", "| Task 3 |"),
        PLAN.replace("| Task 2 | `completed` | current | `deepagents` | Task 1 |", "| Task 2 | `completed` | current | `deepagents` | Task 9 |"),
        PLAN.replace("| Task 1 | `completed` | current | `deepagents` | none |", "| Task 1 | `completed` | current | `deepagents` | Task 1 |"),
        PLAN.replace("| Task 1 | `completed` | current | `deepagents` | none |", "| Task 1 | `completed` | current | `deepagents` | Task 2 |").replace("| Task 2 | `completed` | current | `deepagents` | Task 1 |", "| Task 2 | `completed` | current | `deepagents` | Task 1 |"),
        PLAN.replace("| Task 2 | `completed` | current | `deepagents` | Task 1 |", "| Task 2 | `completed` | current | `deepagents` | Task 1 and Task 9 |"),
    ]

    for invalid_plan in invalid_plans:
        with pytest.raises(ValueError):
            parse_plan(invalid_plan)


def test_prepare_task_keeps_readiness_separate_from_evidence() -> None:
    graph = parse_plan(PLAN)
    prepared = prepare_task(graph, "Task 3")

    assert prepared.structurally_ready is True
    assert prepared.unresolved_prerequisites == ()
    assert prepared.required_proof == "dispatch proof"
    assert "Plan goal:" in prepared.brief
    assert "Recorded prerequisites: Task 1, Task 2" in prepared.brief

def test_prepare_task_reports_pending_dependency() -> None:
    prepared = prepare_task(parse_plan(PLAN), "Task 4")

    assert prepared.structurally_ready is False
    assert prepared.unresolved_prerequisites == ("Task 3",)


def test_prepare_lane_inputs_merges_plan_and_runtime_ownership() -> None:
    runtime = {
        "repository_identity": "project-OS-starter",
        "worktree": "C:/work/task-3",
        "expected_base": "base",
        "session": "session",
        "pane": "pane-3",
        "allowed_write_set": ["src/task3.py"],
        "fixed_contracts": ["contract-v1"],
        "mutable_resources": ["resource-3"],
        "grant_turns": "native",
        "grant_wall_clock_seconds": "native",
        "grant_child_agents": "deny",
        "mcp_select": [],
        "remaining_authorized_task_allowance": 10,
        "attempt_deadline": 100.0,
        "local_capabilities": {"requested": ["py"]},
        "accepted_prerequisites": {
            "Task 1": {"accepted_revision": "revision-1"},
            "Task 2": {"accepted_revision": "revision-2"},
        },
    }

    lanes = prepare_lane_inputs(PLAN, ["Task 3"], {"Task 3": runtime})

    assert lanes[0]["executor"] == "deepagents"
    assert lanes[0]["profile"] == "normal"
    assert lanes[0]["dependencies"] == ["Task 1", "Task 2"]
    assert lanes[0]["dependency_ready"] is True
    assert lanes[0]["plan_preparation"]["required_proof"] == "dispatch proof"
    assert lanes[0]["allowed_write_set"] == ["src/task3.py"]
    assert lanes[0]["fixed_contracts"] == ["contract-v1"]
    assert lanes[0]["mutable_resources"] == ["resource-3"]
    assert lanes[0]["local_capabilities"]["requested"] == ["py"]
    assert lanes[0]["remaining_authorized_task_allowance"] == 10
    assert lanes[0]["attempt_deadline"] == 100.0


def test_prepare_lane_inputs_rejects_conflicting_runtime_task() -> None:
    with pytest.raises(ValueError, match="plan-derived task"):
        prepare_lane_inputs(
            PLAN,
            ["Task 2"],
            {"Task 2": {"task": "different task"}},
        )




def test_prepare_lane_inputs_rejects_stale_plan_identity() -> None:
    with pytest.raises(ValueError, match="plan identity"):
        prepare_lane_inputs(
            PLAN,
            ["Task 2"],
            {"Task 2": {"plan_identity": "stale-plan"}},
        )


def _active_plan() -> str:
    return textwrap.dedent(
        """
        ---
        artifact_type: plan
        template_id: implementation-plan
        contract_version: "1"
        status: active
        layer: change
        name: demo-plan
        ---

        # Demo

        ## Coordination State

        | Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
        | --- | --- | --- | --- | --- | --- | --- |
        | Task 1 | `completed` | current | `deepagents` | none | proof | recorded |
        | Task 2 | `active` | current | `deepagents` | Task 1 | proof | pending |

        ## Task Breakdown

        ### Task 1: First
        **Template Profile:**
        - Controller-selected: `normal`

        ### Task 2: Second
        **Purpose:**
        - Second task.

        **Template Profile:**
        - Controller-selected: `normal`

        **Files And Symbols:**
        - Modify: `scripts/example.py:run`

        **Authority:**
        - Preauthorized local actions: edit source.
        - Stop for: failed proof.

        ## Verification

        This section must not enter worker task text.
        """
    ).strip() + "\n"


def _binding(tmp_path: Path) -> dict[str, object]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    return {
        "repository_identity": "project-OS-starter",
        "worktree": str(tmp_path),
        "expected_base": head,
        "session": "session",
        "pane": "pane",
        "runtime_grant": {
            "turns": "native",
            "wall_clock_seconds": "native",
            "delegation": {"child_agents": "deny"},
            "mcp_select": [],
        },
        "allowed_write_set": ["scripts"],
        "fixed_contracts": ["contract-v1"],
        "mutable_resources": ["resource-2"],
        "local_capabilities": {"requested": ["py"]},
        "remaining_authorized_task_allowance": 10,
        "attempt_deadline": 100.0,
        "accepted_prerequisites": {
            "Task 1": {"accepted_revision": head}
        },
    }


def test_shared_dependency_parser_rejects_partial_input() -> None:
    assert parse_dependency_field("Tasks 1–2, Task 4") == ["Task 1", "Task 2", "Task 4"]
    with pytest.raises(ValueError):
        parse_dependency_field("Task 1 trailing")
    with pytest.raises(ValueError):
        validate_dependency_graph({"Task 1": ["Task 2"], "Task 2": ["Task 1"]})


def test_prepare_plan_lanes_bounds_worker_text_and_binding_digest(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(_active_plan(), encoding="utf-8")
    lane = prepare_plan_lanes(plan_path, ["Task 2"], {"Task 2": _binding(tmp_path)})[0]

    assert lane["plan_identity"] == "demo-plan"
    assert lane["dependency_ready"] is True
    assert "This section must not enter worker task text" not in lane["task"]
    assert lane["execution_binding_digest"] == prepare_lane(lane)["execution_binding_digest"]


def test_prepare_plan_lanes_rejects_stale_binding(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(_active_plan(), encoding="utf-8")
    lane = prepare_plan_lanes(plan_path, ["Task 2"], {"Task 2": _binding(tmp_path)})[0]
    lane["execution_binding_digest"] = "0" * 64
    prepared = prepare_lane(lane)

    with pytest.raises(ValueError, match="execution_binding_digest"):
        dispatcher.verify_launch_bindings(prepared)


def test_prepare_plan_lanes_rejects_plan_revision_changed_after_admission(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(_active_plan(), encoding="utf-8")
    lane = prepare_plan_lanes(plan_path, ["Task 2"], {"Task 2": _binding(tmp_path)})[0]
    plan_path.write_text(_active_plan() + "\nchanged\n", encoding="utf-8")

    with pytest.raises(ValueError, match="plan revision changed"):
        dispatcher.verify_launch_bindings(prepare_lane(lane))


def test_prepare_plan_lanes_rejects_plan_owned_runtime_fields(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(_active_plan(), encoding="utf-8")
    binding = _binding(tmp_path)
    binding["artifact_available"] = True  # type: ignore[index]

    with pytest.raises(ValueError, match="plan-owned fields"):
        prepare_plan_lanes(plan_path, ["Task 2"], {"Task 2": binding})


def test_prepare_plan_lanes_rejects_missing_runtime_authority(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(_active_plan(), encoding="utf-8")
    binding = _binding(tmp_path)
    binding.pop("mutable_resources")

    with pytest.raises(ValueError, match="runtime binding missing field: mutable_resources"):
        prepare_plan_lanes(plan_path, ["Task 2"], {"Task 2": binding})
