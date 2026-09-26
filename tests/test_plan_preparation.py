from __future__ import annotations

import json
import subprocess
import sys
import time
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
    assert prepared.execution_eligible is True
    assert prepared.eligibility_reason is None
    assert prepared.unresolved_prerequisites == ()
    assert prepared.required_proof == "dispatch proof"
    assert "Plan goal:" in prepared.brief
    assert "Recorded prerequisites: Task 1, Task 2" in prepared.brief

def test_prepare_task_reports_pending_dependency() -> None:
    prepared = prepare_task(parse_plan(PLAN), "Task 4")

    assert prepared.structurally_ready is False
    assert prepared.unresolved_prerequisites == ("Task 3",)


@pytest.mark.parametrize("state", ["blocked", "completed"])
def test_prepare_plan_lanes_rejects_ineligible_selected_task(tmp_path: Path, state: str) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(_active_plan().replace("| Task 2 | `active` |", f"| Task 2 | `{state}` |"), encoding="utf-8")

    with pytest.raises(ValueError, match=f"selected task is not execution-eligible: {state}"):
        prepare_plan_lanes(plan_path, ["Task 2"], {"Task 2": _binding(tmp_path)})


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

        ## Goal

        Preserve complete selected task context.

        ## Execution Approach
        - Required skills: `skill-backend-verification`

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

        **Verification:**
        - `python -m pytest -q tests/test_example.py`

        **Exit Criteria:**
        - Task 2 proof is recorded.

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
        "worktree": str(Path(__file__).resolve().parents[1]),
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
    assert "Plan objective:\nPreserve complete selected task context." in lane["task"]
    assert "python -m pytest -q tests/test_example.py" in lane["task"]
    assert "Task 2 proof is recorded." in lane["task"]
    assert "This section must not enter worker task text" not in lane["task"]
    assert lane["execution_binding_digest"] == prepare_lane(lane)["execution_binding_digest"]


def test_launcher_task_argument_contains_complete_selected_contract(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(_active_plan(), encoding="utf-8")
    lane = prepare_plan_lanes(plan_path, ["Task 2"], {"Task 2": _binding(tmp_path)})[0]

    command = dispatcher._launcher_command(lane, python_executable="python", launcher_path="launcher.py")
    task_text = command[command.index("--task") + 1]

    assert "Plan objective:\nPreserve complete selected task context." in task_text
    assert "**Verification:**" in task_text
    assert "**Exit Criteria:**" in task_text
    assert "Applicable explicit shared constraints:\n`skill-backend-verification`" in task_text
    assert task_text.count("**Purpose:**") == 1
    assert task_text.count("**Authority:**") == 1
    assert task_text.count("**Verification:**") == 1
    assert task_text.count("**Exit Criteria:**") == 1
    assert "Task 3:" not in task_text
    assert "This section must not enter worker task text" not in task_text


def test_manual_and_plan_inputs_record_equivalent_dispatch_evidence(tmp_path: Path, monkeypatch) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(_active_plan(), encoding="utf-8")
    runtime = _binding(tmp_path)
    runtime["attempt_deadline"] = time.monotonic() + 60
    plan_lane = prepare_plan_lanes(plan_path, ["Task 2"], {"Task 2": runtime})[0]
    manual_lane = dict(plan_lane)
    for field in ("plan_source", "plan_revision", "plan_preparation", "execution_binding_digest"):
        manual_lane.pop(field, None)

    counters = {"source_parts": 0, "prepare_task": 0}
    from scripts.project_os_runtime import plan_preparation

    original_source_parts = plan_preparation._source_parts
    original_prepare_task = plan_preparation.prepare_task

    def counted_source_parts(source):
        counters["source_parts"] += 1
        return original_source_parts(source)

    def counted_prepare_task(graph, task_id):
        counters["prepare_task"] += 1
        return original_prepare_task(graph, task_id)

    monkeypatch.setattr(plan_preparation, "_source_parts", counted_source_parts)
    monkeypatch.setattr(plan_preparation, "prepare_task", counted_prepare_task)

    def run_case(source, expected_lane, plan_mode: bool) -> dict[str, object]:
        commands: list[list[str]] = []
        expected = dispatcher.prepare_lane(expected_lane).to_dict()

        def fake_popen(command, **kwargs):
            commands.append(command)
            assignment_id = expected["assignment_id"]
            task_hash = expected["task_sha256"]
            grant = expected["runtime_grant"]
            digest = expected["grant_digest"]
            capabilities = expected["local_capabilities"]
            assignment = {
                "attempt_id": "evidence-attempt",
                "assignment_id": assignment_id,
                "task_sha256": task_hash,
                "grant_digest": digest,
                "capability_state": "confirmed",
                "capabilities": {
                    "requested": capabilities["requested"],
                    "passed_to_worker": capabilities["effective"],
                    "validated_available": capabilities["effective"],
                    "digest": capabilities["digest"],
                    "validation_error": None,
                },
                "lifecycle_receipt": {
                    "state": "confirmed",
                    "worker_state": "exited",
                    "descendant_state": "terminated",
                    "cleanup_state": "removed",
                    "recovery_required": False,
                },
                "task_result": {"state": "reported_completed", "accepted": None},
            }
            output = {
                "registry_launcher": {
                    "attempt_id": "evidence-attempt",
                    "assignment_id": assignment_id,
                    "assignment_task_sha256": task_hash,
                    "runtime_grant": grant,
                    "grant_digest": digest,
                    "local_capabilities": capabilities,
                }
            }

            class CompletedProcess:
                pid = 401
                returncode = 0

                def communicate(self, *, timeout):
                    return json.dumps(output) + "\n" + json.dumps({"assignment": assignment}), ""

            return CompletedProcess()

        started = time.perf_counter()
        if plan_mode:
            result = dispatcher.run_parallel_from_plan(
                plan_path,
                ["Task 2"],
                {"Task 2": runtime},
                max_concurrency=1,
                popen_factory=fake_popen,
            )
        else:
            result = dispatcher.run_parallel(
                [source],
                max_concurrency=1,
                popen_factory=fake_popen,
            )
        elapsed = time.perf_counter() - started
        assert result["results"][0]["unresolved"] is False
        return {
            "caller_supplied_fields": len(expected_lane),
            "launcher_commands": len(commands),
            "launcher_subprocesses": len(commands),
            "model_calls": 0,
            "missing_context_requests": 0,
            "recovery_paths": 0,
            "elapsed_seconds": elapsed,
            "result": result,
        }

    manual_metrics = run_case(manual_lane, manual_lane, False)
    plan_metrics = run_case(plan_lane, plan_lane, True)
    plan_owned_fields = set(plan_lane) - set(runtime)

    semantic_fields = (
        "task",
        "runtime_grant",
        "remaining_authorized_task_allowance",
        "attempt_deadline",
        "local_capabilities",
        "allowed_write_set",
        "fixed_contracts",
        "mutable_resources",
        "accepted_prerequisites",
    )
    assert all(manual_lane[field] == plan_lane[field] for field in semantic_fields)
    assert len(plan_owned_fields) > 0
    assert manual_metrics["launcher_commands"] == plan_metrics["launcher_commands"] == 1
    assert manual_metrics["launcher_subprocesses"] == plan_metrics["launcher_subprocesses"] == 1
    assert manual_metrics["model_calls"] == plan_metrics["model_calls"] == 0
    assert manual_metrics["missing_context_requests"] == plan_metrics["missing_context_requests"] == 0
    assert manual_metrics["recovery_paths"] == plan_metrics["recovery_paths"] == 0
    assert manual_metrics["elapsed_seconds"] >= 0
    assert plan_metrics["elapsed_seconds"] >= 0

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
