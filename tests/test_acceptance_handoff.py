from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.project_os_runtime.acceptance_handoff import handoff_acceptance, replay_acceptance
from scripts.project_os_runtime.plan_preparation import load_plan


PLAN = """---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: handoff-plan
---

# Handoff plan

## Goal

Prove one controller-owned acceptance handoff.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`

## Coordination State

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `active` | current | `codex` | none | artifact proof | pending |
| Task 2 | `pending` | current | `codex` | Task 1 | dependent proof | pending |

## Task Breakdown

### Task 1: Produce evidence

**Purpose:**
- Produce a controller-inspectable artifact.

**Template Profile:**
- Controller-selected: `normal`

### Task 2: Consume evidence

**Purpose:**
- Consume the accepted prerequisite.

**Template Profile:**
- Controller-selected: `normal`

## Verification

- `python -m pytest -q`
"""


def _binding() -> dict[str, str]:
    return {
        "repository_identity": "repo",
        "assignment_id": "assignment-1",
        "attempt_id": "attempt-1",
        "candidate_sha": "candidate-1",
        "acceptance_checkpoint_sha": "checkpoint-1",
    }


def _evidence() -> dict[str, bool]:
    return {
        "publication_valid": True,
        "task_completed": True,
        "task_identity_matches": True,
    }


def test_handoff_inspects_artifact_applies_dependent_transition_and_replays(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(PLAN, encoding="utf-8")
    artifact = tmp_path / "worker-result.json"
    artifact.write_text(json.dumps({"worker": "settled", "result": "ok"}), encoding="utf-8")
    record_path = tmp_path / "acceptance.json"
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    result = handoff_acceptance(
        plan_path,
        controller_identity="cos-controller-1",
        task_id="Task 1",
        binding=_binding(),
        required_conditions={"artifact exists": "artifact proof"},
        evidence=_evidence(),
        artifact_specs={"artifact exists": {"path": artifact, "expected_sha256": digest}},
        verification={"passed": True},
        git_proof={"head_matches": True, "write_scope_matches": True},
        dependent_task={
            "task_id": "Task 2",
            "plan_identity": "handoff-plan",
            "state": "pending",
            "dependencies": ["Task 1"],
        },
        dependency_states={"Task 1": "completed"},
        record_path=record_path,
    )

    assert result["authorized"] is True
    assert result["decision"]["decision"] == "PASS"
    assert result["artifact_observations"]["artifact exists"]["matches"] is True
    graph = load_plan(plan_path)
    assert graph.tasks["Task 1"].state == "completed"
    assert graph.tasks["Task 2"].state == "active"

    replay = replay_acceptance(plan_path, record_path)

    assert replay["authorized"] is True
    assert replay["replayed"] is True
    replayed_graph = load_plan(plan_path)
    assert replayed_graph.tasks["Task 1"].state == "completed"
    assert replayed_graph.tasks["Task 2"].state == "active"


def test_handoff_fails_closed_when_controller_observation_does_not_match(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(PLAN, encoding="utf-8")
    artifact = tmp_path / "worker-result.json"
    artifact.write_text("worker output", encoding="utf-8")

    result = handoff_acceptance(
        plan_path,
        controller_identity="cos-controller-1",
        task_id="Task 1",
        binding=_binding(),
        required_conditions={"artifact exists": "artifact proof"},
        evidence=_evidence(),
        artifact_specs={"artifact exists": {"path": artifact, "expected_sha256": "0" * 64}},
        verification={"passed": True},
        git_proof={"head_matches": True, "write_scope_matches": True},
    )

    assert result["authorized"] is False
    assert result["decision"]["decision"] == "FAIL"
    assert result["validation_reasons"]
    assert load_plan(plan_path).tasks["Task 1"].state == "active"


def test_handoff_fails_closed_when_git_freshness_is_missing(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(PLAN, encoding="utf-8")
    artifact = tmp_path / "worker-result.json"
    artifact.write_text("worker output", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    result = handoff_acceptance(
        plan_path,
        controller_identity="cos-controller-1",
        task_id="Task 1",
        binding=_binding(),
        required_conditions={"artifact exists": "artifact proof"},
        evidence=_evidence(),
        artifact_specs={"artifact exists": {"path": artifact, "expected_sha256": digest}},
        verification={"passed": True},
    )

    assert result["authorized"] is False
    assert result["decision"]["decision"] == "BLOCKED"
    assert "acceptance freshness" in result["validation_reasons"]
    assert load_plan(plan_path).tasks["Task 1"].state == "active"


def test_handoff_blocks_mismatched_attempt_proof(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(PLAN, encoding="utf-8")
    artifact = tmp_path / "worker-result.json"
    artifact.write_text("worker output", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    result = handoff_acceptance(
        plan_path,
        controller_identity="cos-controller-1",
        task_id="Task 1",
        binding=_binding(),
        required_conditions={"artifact exists": "artifact proof"},
        evidence=_evidence(),
        artifact_specs={"artifact exists": {"path": artifact, "expected_sha256": digest}},
        verification={"passed": True},
        git_proof={"attempt_id": "attempt-2"},
    )

    assert result["authorized"] is False
    assert result["decision"]["decision"] == "BLOCKED"
    assert "attempt binding" in result["validation_reasons"]
    assert load_plan(plan_path).tasks["Task 1"].state == "active"
