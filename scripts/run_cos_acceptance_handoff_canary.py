"""Run the deterministic controller-owned acceptance handoff canary."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Callable

try:
    from scripts.benchmark_operational_comparison import load_json, sha256_json, validate_rows
    from scripts.project_os_runtime.acceptance_handoff import handoff_acceptance, replay_acceptance
    from scripts.project_os_runtime.plan_preparation import load_plan
    from scripts.run_live_stability_probe import record_cos_result
    from scripts.secretary_live_runtime import canonical_resource_inventory
except ModuleNotFoundError:
    from benchmark_operational_comparison import load_json, sha256_json, validate_rows
    from project_os_runtime.acceptance_handoff import handoff_acceptance, replay_acceptance
    from project_os_runtime.plan_preparation import load_plan
    from run_live_stability_probe import record_cos_result
    from secretary_live_runtime import canonical_resource_inventory


ROOT = Path(__file__).parents[1]
PROTOCOL_PATH = ROOT / "artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json"

PLAN = """---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: cos-acceptance-handoff-canary
---

# Canary plan

## Goal

Prove one controller-owned acceptance handoff.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`

## Coordination State

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `active` | current | `codex` | none | controller artifact proof | pending |
| Task 2 | `pending` | current | `codex` | Task 1 | dependent preparation proof | pending |

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

- `py -B -m pytest -q tests/test_acceptance_handoff.py tests/test_live_stability_probe.py`
"""


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _binding() -> dict[str, str]:
    return {
        "repository_identity": "project-OS-starter",
        "assignment_id": "canary-assignment-1",
        "attempt_id": "canary-attempt-1",
        "candidate_sha": _git_head(),
        "acceptance_checkpoint_sha": _git_head(),
    }


def _evidence() -> dict[str, bool]:
    return {
        "publication_valid": True,
        "task_completed": True,
        "task_identity_matches": True,
    }


def _owner_result(protocol: dict[str, Any], acceptance_decision: dict[str, Any]) -> dict[str, Any]:
    trial_id = "cos_two_lane:warm:1"
    arm, condition, repetition = trial_id.split(":")
    return {
        "attempted": True,
        "base_identity": protocol["base_revision"],
        "capability_state": "confirmed",
        "lifecycle": {
            "accepted_outcome": "accepted",
            "review": "not_required",
            "integration": "not_required",
            "retirement": "confirmed",
            "cleanup": "removed",
            "reconciliation": "confirmed",
        },
        "metrics": {
            name: {"status": "observed", "value": 1.0}
            for name in protocol["metric_names"]
        },
        "run_identity": "canary-run-1",
        "source_producer": "cos-acceptance-handoff-canary",
        "stage_timestamps": [{"stage": "admission", "started_at_ms": 0, "ended_at_ms": 1}],
        "useful_intervals_ms": [[0, 1]],
        "protocol_id": protocol["protocol_id"],
        "protocol_digest": protocol["protocol_digest"],
        "trial_id": trial_id,
        "arm": arm,
        "condition": condition,
        "repetition": int(repetition),
        "acceptance_decision": acceptance_decision,
        **{
            field: protocol["workload"][field]
            for field in protocol["workload"]["matching_fields"]
        },
    }


def _handoff(
    plan_path: Path,
    record_path: Path,
    artifact: Path,
    binding: dict[str, str],
    **overrides: Any,
) -> dict[str, Any]:
    expected_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    values: dict[str, Any] = {
        "controller_identity": "cos-controller-canary",
        "task_id": "Task 1",
        "binding": binding,
        "required_conditions": {"artifact exists": "controller artifact proof"},
        "evidence": _evidence(),
        "artifact_specs": {"artifact exists": {"path": artifact, "expected_sha256": expected_digest}},
        "verification": {"passed": True},
        "git_proof": {"head_matches": True, "write_scope_matches": True},
        "dependent_task": {
            "task_id": "Task 2",
            "plan_identity": "cos-acceptance-handoff-canary",
            "state": "pending",
            "dependencies": ["Task 1"],
        },
        "dependency_states": {"Task 1": "completed"},
        "record_path": record_path,
    }
    values.update(overrides)
    return handoff_acceptance(plan_path, **values)


def _negative_case(
    name: str,
    run: Callable[[Path, Path, Path, dict[str, str]], dict[str, Any]],
    root: Path,
) -> dict[str, Any]:
    case_dir = root / name
    case_dir.mkdir()
    plan_path = case_dir / "plan.md"
    plan_path.write_text(PLAN, encoding="utf-8")
    artifact = case_dir / "worker-result.json"
    artifact.write_text('{"settled": true}\n', encoding="utf-8")
    result = run(plan_path, case_dir / "acceptance.json", artifact, _binding())
    task_state = load_plan(plan_path).tasks["Task 1"].state
    return {
        "name": name,
        "authorized": result.get("authorized") is True,
        "decision": result.get("decision", {}).get("decision"),
        "reason": result.get("reason"),
        "task_state_after": task_state,
        "transition_applied": task_state != "active",
    }


def run(output: Path) -> dict[str, Any]:
    protocol = load_json(PROTOCOL_PATH)
    implementation_commit = _git_head()
    with tempfile.TemporaryDirectory(prefix="cos-acceptance-handoff-canary-") as temporary:
        temp_root = Path(temporary)
        plan_path = temp_root / "plan.md"
        plan_path.write_text(PLAN, encoding="utf-8")
        artifact_a = temp_root / "worker-result-a.json"
        artifact_b = temp_root / "worker-result-b.json"
        artifact_a.write_text('{"attempt_id":"canary-attempt-1","lane":"a","settled":true}\n', encoding="utf-8")
        artifact_b.write_text('{"attempt_id":"canary-attempt-1","lane":"b","settled":true}\n', encoding="utf-8")
        record_path = temp_root / "acceptance.json"
        binding = _binding()
        accepted = _handoff(
            plan_path,
            record_path,
            artifact_a,
            binding,
            required_conditions={
                "lane a artifact exists": "controller lane-a artifact proof",
                "lane b artifact exists": "controller lane-b artifact proof",
            },
            artifact_specs={
                "lane a artifact exists": {
                    "path": artifact_a,
                    "expected_sha256": hashlib.sha256(artifact_a.read_bytes()).hexdigest(),
                },
                "lane b artifact exists": {
                    "path": artifact_b,
                    "expected_sha256": hashlib.sha256(artifact_b.read_bytes()).hexdigest(),
                },
            },
        )
        graph_after_acceptance = load_plan(plan_path)
        replay = replay_acceptance(plan_path, record_path)
        graph_after_replay = load_plan(plan_path)
        acceptance_decision = accepted["decision"]
        cos_row = record_cos_result(
            protocol,
            _owner_result(protocol, acceptance_decision),
            trial_id="cos_two_lane:warm:1",
            expected_acceptance_binding={
                "task_id": acceptance_decision["task"]["task_id"],
                "plan_identity": acceptance_decision["task"]["plan_identity"],
                "candidate_sha": acceptance_decision["acceptance_proof"]["git"]["candidate_sha"],
                "acceptance_checkpoint_sha": acceptance_decision["acceptance_proof"]["git"]["acceptance_checkpoint_sha"],
                "assignment_id": acceptance_decision["acceptance_proof"]["git"]["assignment_id"],
                "attempt_id": acceptance_decision["acceptance_proof"]["git"]["attempt_id"],
            },
        )
        row_validation = validate_rows(protocol, [cos_row])
        resources = canonical_resource_inventory(
            [
                {"kind": "workspace", "identity": "canary-workspace", "state": "removed", "attempt_id": binding["attempt_id"]},
                {"kind": "workspace", "identity": "canary-workspace", "state": "removed", "attempt_id": binding["attempt_id"]},
                {"kind": "pane", "identity": "canary-pane", "state": "already_absent", "attempt_id": binding["attempt_id"]},
            ],
            attempt_id=binding["attempt_id"],
        )
        resource_conflict = canonical_resource_inventory(
            [
                {"kind": "workspace", "identity": "canary-workspace", "state": "removed", "attempt_id": binding["attempt_id"]},
                {"kind": "workspace", "identity": "canary-workspace", "state": "present", "attempt_id": binding["attempt_id"]},
            ],
            attempt_id=binding["attempt_id"],
        )
        negatives = [
            _negative_case(
                "stale-head",
                lambda plan, record, item, current: _handoff(
                    plan, record, item, current, git_proof={"head_matches": False}
                ),
                temp_root,
            ),
            _negative_case(
                "missing-evidence",
                lambda plan, record, item, current: _handoff(
                    plan, record, item, current, evidence={**_evidence(), "publication_valid": False}
                ),
                temp_root,
            ),
            _negative_case(
                "receipt-mismatch",
                lambda plan, record, item, current: _handoff(
                    plan, record, item, current, evidence={**_evidence(), "task_identity_matches": False}
                ),
                temp_root,
            ),
            _negative_case(
                "verification-failure",
                lambda plan, record, item, current: _handoff(
                    plan, record, item, current, verification={"passed": False}
                ),
                temp_root,
            ),
            _negative_case(
                "artifact-freshness-mismatch",
                lambda plan, record, item, current: _handoff(
                    plan,
                    record,
                    item,
                    current,
                    artifact_specs={"artifact exists": {"path": item, "expected_sha256": "0" * 64}},
                ),
                temp_root,
            ),
            _negative_case(
                "stale-attempt",
                lambda plan, record, item, current: _handoff(
                    plan, record, item, current, git_proof={"attempt_id": "different-attempt"}
                ),
                temp_root,
            ),
            _negative_case(
                "dependent-plan-mismatch",
                lambda plan, record, item, current: _handoff(
                    plan,
                    record,
                    item,
                    current,
                    dependent_task={
                        "task_id": "Task 2",
                        "plan_identity": "different-plan",
                        "state": "pending",
                        "dependencies": ["Task 1"],
                    },
                ),
                temp_root,
            ),
        ]
        try:
            record_cos_result(
                protocol,
                _owner_result(protocol, {}),
                trial_id="cos_two_lane:warm:1",
                expected_acceptance_binding={},
            )
        except ValueError as exc:
            absent_producer = {"authorized": False, "reason": str(exc)}
        else:
            absent_producer = {"authorized": True, "reason": "unexpected producer acceptance"}
        evidence = {
            "schema": "cos-acceptance-handoff-canary/v1",
            "evidence_class": "local-read-only",
            "implementation_commit": implementation_commit,
            "protocol": {
                "path": str(PROTOCOL_PATH.relative_to(ROOT)).replace("\\", "/"),
                "protocol_id": protocol["protocol_id"],
                "protocol_digest": protocol["protocol_digest"],
                "source_digest": sha256_json(protocol),
            },
            "controller": {
                "identity": "cos-controller-canary",
                "authority": "cos",
                "producer": "scripts/project_os_runtime/acceptance_handoff.py:handoff_acceptance",
            },
            "accepted_lifecycle": {
                "decision": acceptance_decision["decision"],
                "plan_task_state_after_acceptance": graph_after_acceptance.tasks["Task 1"].state,
                "dependent_task_state_after_acceptance": graph_after_acceptance.tasks["Task 2"].state,
                "replay": replay,
                "plan_task_state_after_replay": graph_after_replay.tasks["Task 1"].state,
                "dependent_task_state_after_replay": graph_after_replay.tasks["Task 2"].state,
                "attempt_id": binding["attempt_id"],
                "lane_observations": [
                    {"lane_id": "canary-lane-a", "artifact": "worker-result-a.json", "settled": True},
                    {"lane_id": "canary-lane-b", "artifact": "worker-result-b.json", "settled": True},
                ],
                "record_schema": json.loads(record_path.read_text(encoding="utf-8"))["schema"],
                "probe_row": {
                    "status": cos_row["status"],
                    "arm": cos_row["arm"],
                    "acceptance_decision": cos_row["acceptance_decision"]["decision"],
                    "validation_errors": row_validation["invalid_rows"],
                },
            },
            "resource_inventory": resources,
            "resource_conflict_negative": resource_conflict,
            "negative_cases": negatives + [{"name": "absent-cos-producer", **absent_producer}],
            "claims": {
                "semantic_acceptance_owner": "cos",
                "runtime_settlement_owner": "runtime",
                "worker_acceptance_field_used": False,
                "synthetic_acceptance_used": False,
                "provider_execution_proven": False,
                "physical_cleanup_proven": False,
            },
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = run(args.output)
    if evidence["accepted_lifecycle"]["decision"] != "PASS":
        raise SystemExit("canary did not reach CoS PASS")
    if evidence["resource_inventory"]["reuse_blocked"]:
        raise SystemExit("settled canary inventory unexpectedly blocks reuse")
    if any(case.get("authorized") is True or case.get("transition_applied") is True for case in evidence["negative_cases"] if case["name"] != "absent-cos-producer"):
        raise SystemExit("negative canary case authorized an invalid transition")
    if evidence["resource_conflict_negative"]["reuse_blocked"] is not True:
        raise SystemExit("resource conflict did not block reuse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
