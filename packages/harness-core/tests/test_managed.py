"""
@meta
name: test_harness_task
type: test
domain: harness
"""

from __future__ import annotations

import json
import copy
from datetime import UTC, datetime
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

from harness_core import managed


ROOT = Path(__file__).resolve().parents[3]
MANAGED_COMMAND = [sys.executable, "-m", "harness_core.managed"]
FRICTION_EVENTS_ROOT: Path | None = None


@pytest.fixture(autouse=True)
def isolate_root_friction_events(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    global FRICTION_EVENTS_ROOT
    FRICTION_EVENTS_ROOT = tmp_path / "friction-events.jsonl"
    original_friction_events_path = managed._friction_events_path
    monkeypatch.setattr(
        managed,
        "_friction_events_path",
        lambda root: FRICTION_EVENTS_ROOT if root == ROOT else original_friction_events_path(root),
    )


API6_BINDING = {
    "provider_id": "codex_app_server",
    "host_api": 6,
    "contract_version": 6,
    "transport": "stdio",
    "lifecycle": "host_spawn",
    "protocol": "app-server-v1",
    "configuration_digest": "a" * 64,
    "readiness": "ready",
}


class HarnessModule:
    def __init__(self, module):
        object.__setattr__(self, "_module", module)

    def __getattr__(self, name):
        return getattr(self._module, name)

    def __setattr__(self, name, value):
        setattr(self._module, name, value)

    def __delattr__(self, name):
        delattr(self._module, name)

    def resolve_managed_packet(self, root, request, **kwargs):
        if request.get("version") == 5:
            kwargs.setdefault("provider_runtime_binding", copy.deepcopy(API6_BINDING))
        return self._module.resolve_managed_packet(root, request, **kwargs)


def load_module():
    return HarnessModule(managed)


def task(**overrides):
    payload = {
        "version": 1,
        "task_type": "local_change",
        "acceptance_criteria": ["focused test passes"],
        "allowed_paths": ["scripts/**", "tests/**"],
        "base_ref": "HEAD",
    }
    payload.update(overrides)
    return payload


def claim(**overrides):
    payload = {
        "kind": "claimed_result",
        "changed_files": ["scripts/example.py"],
        "from_state": "verifying",
        "next_state": "accepted",
    }
    payload.update(overrides)
    return payload


def managed_request(**overrides):
    payload = {
        "version": 5,
        "run_id": "managed-test",
        "task_type": "local_change",
        "execution_mode": "single_work_lane",
        "user_request": "Update managed harness fixture.",
        "acceptance_criteria": [{"id": "diff", "kind": "check", "check": "diff"}],
        "allowed_paths": ["scripts/**", "tests/**"],
        "planned_write_paths": ["scripts/harness_task.py"],
        "base_ref": "HEAD",
    }
    payload.update(overrides)
    if "acceptance_criteria" not in overrides and payload["task_type"] in {
        "debugging",
        "harness_diagnosis",
        "research",
        "plan_review",
        "design_exploration",
    }:
        payload["acceptance_criteria"] = [{"id": "validator", "kind": "validator"}]
    return payload


def write_stranded_run(harness, run_id: str) -> None:
    policy = harness._load_policy(ROOT)
    request = managed_request(run_id=run_id)
    packet = harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")
    run = harness._new_run(request, run_id)
    harness._append_attempt(run, packet)
    harness._transition(run, policy["states"], "planned", "test")
    harness._transition(run, policy["states"], "running", "dispatch")
    harness._write_run(ROOT, run)


def recovery_evidence(run_id: str, attempt_id: str = "attempt-1") -> dict[str, str | int]:
    return {
        "version": 1,
        "source": "host",
        "code": "terminal_recording_failed",
        "run_id": run_id,
        "attempt_id": attempt_id,
        "detail": "sanitized command trace exceeds artifact_max_bytes",
        "observed_at": "2026-08-08T19:54:03+00:00",
    }


def plan_coordination(
    *,
    digest="plan-digest",
    execution_mode="single_work_lane",
    paths=("scripts/harness_task.py",),
    allowed_paths=("scripts/**", "tests/**"),
):
    task = SimpleNamespace(
        task_id="task-1",
        execution_mode=execution_mode,
        allowed_paths=allowed_paths,
        planned_write_paths=paths,
    )
    return SimpleNamespace(
        plan_ref="docs/superpowers/plans/fixture.md",
        base_ref="HEAD",
        digest=digest,
        task=lambda task_id: task if task_id == "task-1" else (_ for _ in ()).throw(ValueError(task_id)),
    )


def plan_coordination_with_tasks(*tasks, plan_ref="docs/superpowers/plans/fixture.md", target_branch="main"):
    by_id = {task.task_id: task for task in tasks}
    return SimpleNamespace(
        plan_ref=plan_ref,
        base_ref="HEAD",
        digest=f"digest-{plan_ref}",
        target_branch=target_branch,
        tasks=tuple(tasks),
        task=lambda task_id: by_id[task_id],
    )


def coordinated_task(
    task_id,
    *,
    depends_on=(),
    execution_mode="single_work_lane",
    paths=("scripts/harness_task.py",),
    allowed_paths=("scripts/**", "tests/**"),
):
    return SimpleNamespace(
        task_id=task_id,
        depends_on=depends_on,
        execution_mode=execution_mode,
        allowed_paths=allowed_paths,
        planned_write_paths=paths,
    )


def write_coordinated_run(harness, root, run_id, *, state, plan_ref, task_id, paths=("scripts/harness_task.py",)):
    harness._write_run(root, {
        "version": 1,
        "run_id": run_id,
        "request": {},
        "state": state,
        "state_history": [{"state": state, "reason": "fixture", "at": f"2026-08-06T00:00:0{len(run_id)}+00:00"}],
        "attempts": [{
            "packet": {
                "plan_ref": plan_ref,
                "plan_task_id": task_id,
                "planned_write_paths": list(paths),
            },
        }],
    })


class FakeAdapter:
    def __init__(
        self,
        capabilities,
        claim_payload=None,
        validator_claim=None,
        repair_payload=None,
        repair_terminal_status="completed",
        dispatch_error=None,
        identity=None,
        host_api=6,
        workspace_root=None,
    ):
        self.capabilities_value = capabilities
        self.claim_payload = claim_payload
        self.validator_claim = validator_claim
        self.repair_payload = repair_payload
        self.repair_terminal_status = repair_terminal_status
        self.dispatch_error = dispatch_error
        self.identity_value = identity or {"provider_id": "codex_app_server", "contract_version": 6}
        self.host_api_value = host_api
        self.workspace_root = str(workspace_root or ROOT)
        self.calls = []

    def identity(self):
        return self.identity_value

    def host_api(self):
        return self.host_api_value

    def preflight_evidence(self):
        return copy.deepcopy(API6_BINDING)

    def capabilities(self):
        self.calls.append("capabilities")
        return self.capabilities_value

    def prepare_workspace(self, lane, packet):
        self.calls.append("prepare_workspace")
        baseline = {"kind": "packet_base", "base_commit": packet["base_commit"], "clean": True}
        if lane["dependencies"]:
            baseline = {"kind": "predecessor", "lane_id": lane["dependencies"][0]}
        return {"kind": "current", "path": self.workspace_root, "baseline": baseline}

    def verify_tool_bindings(self, lane, packet, workspace):
        self.calls.append("verify_tool_bindings")
        access_key = "validator_access" if lane["kind"] == "validate" else "writer_access"
        return [{
            "tool": binding["tool"],
            "host_kind": binding["host_kind"],
            "access": binding[access_key],
            "root_probe": binding["root_probe"],
            "workspace_root": workspace["path"],
            "verified": True,
            "runtime_provider": packet["runtime_provider"],
        } for binding in packet["tool_bindings"]]

    def run_checks(self, packet, workspace):
        self.calls.append("run_checks")
        return {
            name: {
                "command": command,
                "workspace_root": workspace["path"],
                "tool": "shell",
                "binding_verified": True,
                "runtime_provider": packet["runtime_provider"],
                "exit_code": 0,
                "stdout": "ok",
                "stderr": "",
            }
            for name, command in packet["checks"].items()
        }

    def dispatch_lane(self, lane, packet, workspace, cancellation_token):
        self.calls.append("dispatch_lane")
        if self.dispatch_error is not None:
            raise self.dispatch_error
        return {"lane_id": lane["lane_id"]}

    def materialize_final_state(self, lane, packet, workspaces):
        self.calls.append("materialize_final_state")
        return {"kind": "isolated", "path": self.workspace_root}

    def cancel_lane(self, handle):
        self.calls.append("cancel_lane")

    def collect_claim(self, handle):
        self.calls.append("collect_claim")
        if handle["lane_id"] == "validate":
            if self.validator_claim is not None:
                payload = self.validator_claim
            else:
                payload = {
                    "kind": "claimed_result",
                    "summary": "validated",
                    "findings": ["ok"],
                    "verdict": "pass",
                }
        elif self.claim_payload is not None:
            payload = self.claim_payload
        else:
            payload = {
                "kind": "claimed_result",
                "summary": "done",
                "changed_files": ["scripts/harness_task.py"],
            }
        return self._claim_observation(handle, payload)

    def repair_claim(self, handle, lane, packet, workspace, request):
        self.calls.append("repair_claim")
        payload = self.repair_payload or {
            "kind": "claimed_result",
            "summary": "repaired",
            "changed_files": ["scripts/harness_task.py"],
        }
        return {
            "claim_observation": self._claim_observation(handle, payload),
            "finalization_evidence": {
                "lane_id": lane["lane_id"],
                "thread_id": "thread",
                "turn_id": f"repair-{lane['lane_id']}",
                "terminal_status": self.repair_terminal_status,
                "sandbox": "read-only",
                "tool_calls": [],
                "command_results": [],
                "workspace_status_before": "",
                "workspace_status_after": "",
                "agent_identity": packet["agent_identity"],
                "prompt_contract_version": 1,
                "prompt_digest": "c" * 64,
                "elapsed_seconds": 1.0,
            },
        }

    def _claim_observation(self, handle, payload):
        if self.host_api_value < 6:
            return payload
        if isinstance(payload, dict) and "state" in payload:
            return {
                "version": 1,
                "lane_id": handle["lane_id"],
                "thread_id": "thread",
                **payload,
            }
        return {
            "version": 1,
            "lane_id": handle["lane_id"],
            "thread_id": "thread",
            "state": "object",
            "candidate_claim": payload,
        }

    def collect_lane_evidence(self, handle, lane, packet, workspace):
        self.calls.append("collect_lane_evidence")
        return {
            "lane_id": lane["lane_id"],
            "workspace_root": workspace["path"],
            "thread_id": "thread",
            "turn_id": f"turn-{lane['lane_id']}",
            "terminal_status": "completed",
            "sandbox": "read-only" if lane["kind"] == "validate" else "workspace-write",
            "selected_tools_used": ["shell"],
            "tool_calls": ["shell"],
            "command_results": [{
                "cwd": workspace["path"],
                "exit_code": 0,
                "runtime_provider": packet["runtime_provider"],
            }],
            "ambient_mcp": False,
            "runtime_provider": packet["runtime_provider"],
            "agent_identity": packet["agent_identity"],
            "workspace_status_before": "",
            "workspace_status_after": "",
        }


def assert_provider_conformance(harness, adapter, run_id, workspace_root):
    run_dir = ROOT / ".harness" / "runs" / run_id
    Path(workspace_root).mkdir(parents=True, exist_ok=True)
    result = harness.run_managed(
        ROOT,
        managed_request(run_id=run_id),
        adapter,
        collect_changes=lambda root, base_commit: [],
    )

    assert result["outcome"]["reason"] == "verification_passed"
    run = json.loads((run_dir / "run.json").read_text())
    attempt = run["attempts"][0]
    provider = attempt["packet"]["runtime_provider"]
    assert provider == adapter.identity()
    assert attempt["adapter_identity"] == provider
    assert [record["sandbox"] for record in attempt["execution_evidence"]] == ["workspace-write", "read-only"]
    assert {record["workspace_root"] for record in attempt["execution_evidence"]} == {str(workspace_root)}
    assert all(record["runtime_provider"] == provider for record in attempt["execution_evidence"])
    assert all(
        command["runtime_provider"] == provider
        for record in attempt["execution_evidence"]
        for command in record["command_results"]
    )
    assert all(
        binding["workspace_root"] == str(workspace_root) and binding["runtime_provider"] == provider
        for record in attempt["tool_binding_evidence"]
        for binding in record["bindings"]
    )
    assert all(
        check["workspace_root"] == str(workspace_root) and check["runtime_provider"] == provider
        for check in attempt["evidence"]["checks"]
    )
    return run


def test_resolve_task_returns_route_packet() -> None:
    harness = load_module()

    packet = harness.resolve_task(ROOT, task())

    assert packet["template"] == "normal"
    assert packet["agent_identity"]["model"] == "combo-normal"
    assert packet["role"] == "implement"
    assert packet["checks"] == {"diff": ["git", "diff", "--check"]}
    assert packet["orchestration"]["name"] == "single_work_lane"


def test_v5_packet_resolves_selected_profiles() -> None:
    harness = load_module()

    packet = harness.resolve_managed_packet(
        ROOT,
        managed_request(
            version=5,
            task_type="local_change",
            execution_mode="single_work_lane",
            planned_write_paths=["scripts/harness_task.py"],
        ),
        attempt_id="attempt-1",
        provider_runtime_binding={"provider_id": "codex_app_server", "contract_version": 6, "host_api": 6},
    )

    assert packet["authority"] == "workspace_write"
    assert packet["toolset"] == "code"
    assert packet["verification_profile"] == "write"
    assert packet["capabilities"] == ["repo.read", "repo.write", "code.search"]
    assert packet["checks"] == {"diff": ["git", "diff", "--check"]}
    assert packet["postconditions"] == []
    assert packet["execution_budget"]["finalization_reserve_seconds"] == 60


def test_fresh_request_api_must_match_policy_request_api(monkeypatch: pytest.MonkeyPatch) -> None:
    harness = load_module()
    policy = harness._load_policy(ROOT)
    policy["harness_core"] = {"request_api": 5}
    monkeypatch.setattr(harness, "_load_policy", lambda _root: policy)

    with pytest.raises(harness.HarnessError, match="managed request API must match policy request_api"):
        harness.resolve_managed_packet(
            ROOT,
            managed_request(version=3, execution_mode="single_work_lane"),
            attempt_id="attempt-1",
        )


def test_composed_packet_resolves_selected_backend_facet_and_operating_profile() -> None:
    harness = load_module()

    packet = harness.resolve_managed_packet(
        ROOT,
        managed_request(
            version=5,
            execution_mode="single_work_lane",
            skill_set_selections=[{"id": "backend_verification", "reason": "route contract changes"}],
            operating_profile_selection={"id": "local_change_extended", "reason": "approved extended range"},
        ),
        attempt_id="attempt-1",
    )

    assert packet["skills"] == [
        "skill-code-standards",
        "skill-executing-plans",
        "skill-test-driven-development",
        "skill-backend-verification",
    ]
    assert packet["skill_sets"] == {
        "required": ["local_change_base"],
        "selected": [{"id": "backend_verification", "reason": "route contract changes"}],
        "resolved": ["local_change_base", "backend_verification"],
    }
    assert packet["operating_profile"]["resolved"] == "local_change_extended"
    assert packet["execution_budget"]["profile"] == "extended"


@pytest.mark.parametrize(
    ("request_overrides", "message"),
    [
        (
            {"skill_set_selections": [{"id": "missing", "reason": "unknown"}]},
            "skill set `missing` is not allowed for task type",
        ),
        (
            {"skill_set_selections": [
                {"id": "backend_verification", "reason": "first"},
                {"id": "backend_verification", "reason": "duplicate"},
            ]},
            "skill set `backend_verification` is not allowed for task type",
        ),
        (
            {"operating_profile_selection": {"id": "missing", "reason": "unknown"}},
            "operating profile `missing` is not allowed for task type",
        ),
    ],
)
def test_composed_packet_rejects_invalid_controller_selection(request_overrides, message) -> None:
    harness = load_module()

    with pytest.raises(harness.HarnessError, match=message):
        harness.resolve_managed_packet(
            ROOT,
            managed_request(version=5, execution_mode="single_work_lane", **request_overrides),
            attempt_id="attempt-1",
        )


def test_v4_packet_rejects_oversized_work_context_before_dispatch() -> None:
    harness = load_module()

    with pytest.raises(harness.HarnessError, match="user_request exceeds objective_max_bytes"):
        harness.resolve_managed_packet(
            ROOT,
            managed_request(
                version=5,
                task_type="local_change",
                execution_mode="single_work_lane",
                user_request="x" * 4097,
                planned_write_paths=["scripts/harness_task.py"],
            ),
            attempt_id="attempt-1",
        )


def test_resolve_task_selects_validated_sequential_orchestration() -> None:
    harness = load_module()

    packet = harness.resolve_task(ROOT, task(execution_mode="sequential_agents"))

    assert packet["orchestration"] == {
        "name": "sequential_work_lanes",
        "work_scheduling": "sequential",
        "max_parallel_writers": 1,
        "workspace_mode": "isolated",
        "validator_role": "validate",
    }
    assert "multi-agent-orchestration-rule" in packet["rules"]


@pytest.mark.parametrize(("task_type", "skills"), [
    ("research", ["skill-repository-research"]),
    ("design_exploration", ["skill-brainstorming"]),
    ("plan_writing", ["skill-writing-plans"]),
    ("skill_authoring", [
        "skill-writing-skills",
        "skill-test-driven-development",
        "skill-verification-before-completion",
    ]),
    ("harness_improvement", [
        "skill-improve-harness",
        "skill-code-standards",
        "skill-test-driven-development",
        "skill-verification-before-completion",
    ]),
])
def test_route_packet_selects_owned_skill_set(task_type, skills) -> None:
    harness = load_module()

    packet = harness.resolve_task(ROOT, task(task_type=task_type))

    assert packet["skills"] == skills


def test_protected_policy_includes_canonical_skill_sources() -> None:
    harness = load_module()

    packet = harness.resolve_task(ROOT, task())

    assert ".agents/skills/**" in packet["approval_gates"]["protected_policy"]


def test_resolve_managed_packet_builds_api7_lane_dag() -> None:
    harness = load_module()

    packet = harness.resolve_managed_packet(ROOT, managed_request(), attempt_id="attempt-1")

    assert packet["version"] == 7
    assert packet["user_request"] == "Update managed harness fixture."
    assert packet["runtime_provider"] == {"provider_id": "codex_app_server", "contract_version": 6}
    assert packet["core_identity"] == {
        **harness.runtime_identity(),
        "request_api": 5,
        "packet_api": 7,
        "host_api": None,
    }
    assert packet["execution_budget"] == {
        "profile": "default",
        "turn_timeout_seconds": 300,
        "finalization_reserve_seconds": 60,
        "timeout_decisions": ["escalate", "block"],
        "escalation_profile": "extended",
    }
    assert packet["agent_identity"] == {
        "template": "normal",
        "model_provider": "9router",
        "model": "combo-normal",
        "reasoning_effort": "medium",
    }
    assert packet["claim_repair"] == {
        "max_repairs_per_lane": 1,
        "admissible_subcodes": [
            "missing_final_claim",
            "claim_not_json",
            "claim_not_object",
            "claim_kind_mismatch",
            "claim_field_missing",
            "claim_field_type_invalid",
            "claim_field_constraint_invalid",
        ],
        "required_host_capability": "claim_repair_same_thread",
    }
    assert packet["lanes"][0]["claim_schema"] == {
        "required_fields": ["summary", "changed_files"],
        "field_types": {"summary": "nonempty_string", "changed_files": "string_list"},
        "optional_field_types": {
            "findings": "string_list",
            "verdict": "nonempty_string",
            "decision": "nonempty_string",
            "frictions": "friction_list",
        },
        "field_constraints": {},
    }
    assert packet["orchestration"]["name"] == "single_work_lane"
    assert [(lane["lane_id"], lane["kind"], lane["dependencies"]) for lane in packet["lanes"]] == [
        ("primary", "work", []),
        ("integrate", "integrate", ["primary"]),
        ("validate", "validate", ["integrate"]),
        ("check", "check", ["validate"]),
    ]
    assert packet["lanes"][2]["role"] == "validate"
    assert packet["lanes"][2]["write_capable"] is False


def test_current_packet_uses_route_capabilities_without_role_writes(monkeypatch) -> None:
    harness = load_module()
    roles = yaml.safe_load((ROOT / "agents" / "roles.yaml").read_text())
    roles["version"] = 2
    for role in roles["roles"].values():
        role.pop("writes", None)
    monkeypatch.setattr(harness, "_load_roles", lambda root: roles["roles"])

    packet = harness.resolve_managed_packet(ROOT, managed_request(), attempt_id="attempt-1")

    assert packet["capabilities"] == ["repo.read", "repo.write", "code.search"]
    assert packet["lanes"][0]["write_capable"] is True


def test_api7_packet_requires_immutable_provider_runtime_binding() -> None:
    harness = load_module()
    binding = copy.deepcopy(API6_BINDING)
    packet = harness.resolve_managed_packet(
        ROOT,
        managed_request(version=5, execution_mode="single_work_lane"),
        attempt_id="attempt-1",
        provider_runtime_binding=binding,
    )

    assert packet["version"] == 7
    assert packet["invocation_id"] == "attempt-1:primary"
    assert packet["parent_invocation_id"] is None
    assert packet["provider_runtime_binding"] == binding


def test_harness_diagnosis_packet_resolves_direct_artifact_handoff(monkeypatch: pytest.MonkeyPatch) -> None:
    harness = load_module()
    terminal_observation = {
        "version": 1,
        "kind": "timeout",
        "source": "host_timeout_interrupt",
        "lane_id": "primary",
        "session_id": "thread-1",
        "turn_id": "turn-1",
        "turn_timeout_seconds": 300,
        "elapsed_seconds": 300.0,
        "terminal_status": "interrupted",
        "interrupt_status": "terminal_confirmed",
        "item_states": [],
        "command_states": [],
        "final_claim_state": {"state": "missing"},
        "error": None,
    }
    monkeypatch.setattr(harness, "_load_run", lambda root, run_id: {
        "run_id": run_id,
        "state": "blocked",
        "attempts": [{
            "attempt_id": "writer-attempt",
            "packet": {
                "base_commit": harness._resolve_commit(ROOT, "HEAD"),
                "lanes": [{"lane_id": "primary"}],
                "execution_budget": {"turn_timeout_seconds": 300},
                "retained_artifacts": [{"kind": "sanitized_command_trace", "max_bytes": 4096}],
            },
            "evidence": {
                "terminal_observation": terminal_observation,
                "artifacts": [{
                    "kind": "sanitized_command_trace",
                    "content": {"version": 1, "commands": [{
                        "item_id": "command-1",
                        "command": "pytest",
                        "output": "failed",
                        "exit_code": 1,
                    }]},
                }],
            },
        }],
    })

    packet = harness.resolve_managed_packet(
        ROOT,
        managed_request(
            version=5,
            task_type="harness_diagnosis",
            execution_mode="single_work_lane",
            planned_write_paths=[],
            artifact_handoff={"source_run_id": "writer-run", "source_attempt_id": "writer-attempt"},
        ),
        attempt_id="attempt-1",
        provider_runtime_binding={"provider_id": "codex_app_server", "contract_version": 6, "host_api": 6},
    )

    assert [(artifact["kind"], artifact["source_run_id"], artifact["source_attempt_id"]) for artifact in packet["readonly_artifacts"]] == [
        ("terminal_observation", "writer-run", "writer-attempt"),
        ("sanitized_command_trace", "writer-run", "writer-attempt"),
    ]
    assert packet["readonly_artifacts"][0]["content"] == terminal_observation
    assert packet["artifact_handoff"]["profile"] == "direct_terminal_diagnosis"
    assert packet["artifact_handoff_audit"]["sources"] == [{"run_id": "writer-run", "attempt_id": "writer-attempt"}]
    attempt = harness._append_attempt(harness._new_run(managed_request(run_id="target-run"), "target-run"), packet)
    assert attempt["artifact_handoff_audit"] == packet["artifact_handoff_audit"]

def test_artifact_handoff_rejects_oversized_required_content(monkeypatch: pytest.MonkeyPatch) -> None:
    harness = load_module()
    monkeypatch.setattr(harness, "_load_run", lambda root, run_id: {
        "run_id": run_id,
        "state": "blocked",
        "attempts": [{
            "attempt_id": "source-attempt",
            "packet": {
                "base_commit": "base",
                "lanes": [{"lane_id": "primary"}],
                "execution_budget": {"turn_timeout_seconds": 300},
            },
            "evidence": {"terminal_observation": {
                "version": 1,
                "kind": "timeout",
                "source": "host_timeout_interrupt",
                "lane_id": "primary",
                "session_id": "thread-1",
                "turn_id": "turn-1",
                "turn_timeout_seconds": 300,
                "elapsed_seconds": 300.0,
                "terminal_status": "interrupted",
                "interrupt_status": "terminal_confirmed",
                "item_states": [
                    {"item_id": f"item-{index}-{'x' * 110}", "type": "y" * 64, "state": "z" * 64}
                    for index in range(16)
                ],
                "command_states": [],
                "final_claim_state": {"state": "missing"},
                "error": None,
            }},
        }],
    })

    with pytest.raises(harness.HarnessError, match="artifact_handoff required artifact exceeds byte limit"):
        harness._resolve_artifact_handoff(ROOT, {
            "workspace_write_access": "read_only",
            "base_commit": "base",
            "artifact_handoff_policy": {
                "allowed_profiles": ["direct_terminal_diagnosis"],
                "default_profile": "direct_terminal_diagnosis",
                "catalog": {
                    "terminal_observation": {"byte_limit": 4096},
                },
                "profiles": {
                    "direct_terminal_diagnosis": {
                        "lineage_mode": "direct",
                        "required_kinds": ["terminal_observation"],
                        "kind_priority": ["terminal_observation"],
                        "count_limit": 1,
                        "total_byte_limit": 4096,
                    },
                },
            },
        }, {
            "source_run_id": "source-run",
            "source_attempt_id": "source-attempt",
        })


def test_artifact_handoff_rejects_source_set_profile_from_public_request() -> None:
    harness = load_module()

    with pytest.raises(harness.HarnessError, match="artifact_handoff requires a direct profile"):
        harness._resolve_artifact_handoff(ROOT, {
            "workspace_write_access": "read_only",
            "base_commit": "base",
            "artifact_handoff_policy": {
                "allowed_profiles": ["friction_terminal_diagnosis"],
                "default_profile": "friction_terminal_diagnosis",
                "catalog": {},
                "profiles": {
                    "friction_terminal_diagnosis": {
                        "lineage_mode": "source_set",
                        "required_kinds": ["terminal_observation"],
                        "kind_priority": ["terminal_observation"],
                        "count_limit": 1,
                        "total_byte_limit": 4096,
                    },
                },
            },
        }, {
            "source_run_id": "source-run",
            "source_attempt_id": "source-attempt",
            "profile": "friction_terminal_diagnosis",
        })


def test_artifact_handoff_rejects_invalid_required_terminal_observation(monkeypatch: pytest.MonkeyPatch) -> None:
    harness = load_module()
    monkeypatch.setattr(harness, "_load_run", lambda root, run_id: {
        "run_id": run_id,
        "state": "blocked",
        "attempts": [{
            "attempt_id": "source-attempt",
            "packet": {
                "base_commit": "base",
                "lanes": [{"lane_id": "primary"}],
                "execution_budget": {"turn_timeout_seconds": 300},
            },
            "evidence": {"terminal_observation": {"version": 1, "kind": "timeout"}},
        }],
    })

    with pytest.raises(harness.HarnessError, match="artifact_handoff required `terminal_observation` is invalid"):
        harness._resolve_artifact_handoff(ROOT, {
            "workspace_write_access": "read_only",
            "base_commit": "base",
            "artifact_handoff_policy": {
                "allowed_profiles": ["direct_terminal_diagnosis"],
                "default_profile": "direct_terminal_diagnosis",
                "catalog": {"terminal_observation": {"byte_limit": 4096}},
                "profiles": {
                    "direct_terminal_diagnosis": {
                        "lineage_mode": "direct",
                        "required_kinds": ["terminal_observation"],
                        "kind_priority": ["terminal_observation"],
                        "count_limit": 1,
                        "total_byte_limit": 4096,
                    },
                },
            },
        }, {
            "source_run_id": "source-run",
            "source_attempt_id": "source-attempt",
        })


def test_artifact_handoff_excludes_duplicate_optional_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    harness = load_module()
    terminal_observation = {
        "version": 1,
        "kind": "timeout",
        "source": "host_timeout_interrupt",
        "lane_id": "primary",
        "session_id": "thread-1",
        "turn_id": "turn-1",
        "turn_timeout_seconds": 300,
        "elapsed_seconds": 300.0,
        "terminal_status": "interrupted",
        "interrupt_status": "terminal_confirmed",
        "item_states": [],
        "command_states": [],
        "final_claim_state": {"state": "missing"},
        "error": None,
    }
    monkeypatch.setattr(harness, "_load_run", lambda root, run_id: {
        "run_id": run_id,
        "state": "blocked",
        "attempts": [{
            "attempt_id": "source-attempt",
            "packet": {
                "base_commit": "base",
                "lanes": [{"lane_id": "primary"}],
                "execution_budget": {"turn_timeout_seconds": 300},
            },
            "evidence": {
                "terminal_observation": terminal_observation,
                "artifacts": [
                    {"kind": "sanitized_command_trace", "content": {"version": 1, "commands": []}},
                    {"kind": "sanitized_command_trace", "content": {"version": 1, "commands": []}},
                ],
            },
        }],
    })

    artifacts, handoff = harness._resolve_artifact_handoff(ROOT, {
        "workspace_write_access": "read_only",
        "base_commit": "base",
        "artifact_handoff_policy": {
            "allowed_profiles": ["direct_terminal_diagnosis"],
            "default_profile": "direct_terminal_diagnosis",
            "catalog": {
                "terminal_observation": {"byte_limit": 4096},
                "sanitized_command_trace": {"byte_limit": 4096},
            },
            "profiles": {
                "direct_terminal_diagnosis": {
                    "lineage_mode": "direct",
                    "required_kinds": ["terminal_observation"],
                    "kind_priority": ["terminal_observation", "sanitized_command_trace"],
                    "count_limit": 2,
                    "total_byte_limit": 8192,
                },
            },
        },
    }, {
        "source_run_id": "source-run",
        "source_attempt_id": "source-attempt",
    })

    assert [artifact["kind"] for artifact in artifacts] == ["terminal_observation"]
    assert handoff is not None
    assert handoff["audit"]["optional_rejections"] == [{"kind": "sanitized_command_trace", "reason": "invalid"}]


def test_artifact_handoff_excludes_invalid_optional_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    harness = load_module()
    terminal_observation = {
        "version": 1,
        "kind": "timeout",
        "source": "host_timeout_interrupt",
        "lane_id": "primary",
        "session_id": "thread-1",
        "turn_id": "turn-1",
        "turn_timeout_seconds": 300,
        "elapsed_seconds": 300.0,
        "terminal_status": "interrupted",
        "interrupt_status": "terminal_confirmed",
        "item_states": [],
        "command_states": [],
        "final_claim_state": {"state": "missing"},
        "error": None,
    }
    monkeypatch.setattr(harness, "_load_run", lambda root, run_id: {
        "run_id": run_id,
        "state": "blocked",
        "attempts": [{
            "attempt_id": "source-attempt",
            "packet": {
                "base_commit": "base",
                "lanes": [{"lane_id": "primary"}],
                "execution_budget": {"turn_timeout_seconds": 300},
                "retained_artifacts": [{"kind": "sanitized_command_trace", "max_bytes": 4096}],
            },
            "evidence": {
                "terminal_observation": terminal_observation,
                "artifacts": [{"kind": "sanitized_command_trace", "content": {"version": 1, "commands": "invalid"}}],
            },
        }],
    })

    artifacts, handoff = harness._resolve_artifact_handoff(ROOT, {
        "workspace_write_access": "read_only",
        "base_commit": "base",
        "artifact_handoff_policy": {
            "allowed_profiles": ["direct_terminal_diagnosis"],
            "default_profile": "direct_terminal_diagnosis",
            "catalog": {
                "terminal_observation": {"byte_limit": 4096},
                "sanitized_command_trace": {"byte_limit": 4096},
            },
            "profiles": {
                "direct_terminal_diagnosis": {
                    "lineage_mode": "direct",
                    "required_kinds": ["terminal_observation"],
                    "kind_priority": ["terminal_observation", "sanitized_command_trace"],
                    "count_limit": 2,
                    "total_byte_limit": 8192,
                },
            },
        },
    }, {
        "source_run_id": "source-run",
        "source_attempt_id": "source-attempt",
    })

    assert [artifact["kind"] for artifact in artifacts] == ["terminal_observation"]
    assert handoff is not None
    assert handoff["audit"]["optional_rejections"] == [{"kind": "sanitized_command_trace", "reason": "invalid"}]


def test_retained_trace_rejects_oversized_serialized_content() -> None:
    class HostFailure(RuntimeError):
        evidence_artifacts = [{
            "kind": "sanitized_command_trace",
            "content": {"version": 1, "commands": [{
                "item_id": "command-1",
                "command": "pytest",
                "output": "x" * 4090,
                "exit_code": 1,
            }]},
        }]

    with pytest.raises(managed.HarnessError, match="sanitized command trace exceeds artifact_max_bytes"):
        managed._normalize_retained_artifacts(HostFailure(), {
            "retained_artifacts": [{"kind": "sanitized_command_trace", "max_bytes": 4096}],
        })


@pytest.mark.parametrize(
    ("task_type", "capabilities", "delegation_profile", "workspace_write_access"),
    [
        ("local_change", ["repo.read", "repo.write", "code.search"], "disabled", "workspace_write"),
        ("debugging", ["repo.read", "code.search", "docs.query"], "disabled", "read_only"),
        ("research", ["repo.read", "code.search", "docs.query", "harness.delegate"], "read_only_research", "read_only"),
        ("harness_diagnosis", ["repo.read", "code.search", "docs.query"], "disabled", "read_only"),
        ("plan_review", ["repo.read", "code.search", "docs.query"], "disabled", "read_only"),
        ("design_exploration", ["repo.read", "code.search", "docs.query"], "disabled", "read_only"),
        ("plan_writing", ["repo.read", "repo.write", "code.search"], "disabled", "workspace_write"),
        ("skill_authoring", ["repo.read", "repo.write", "code.search"], "disabled", "workspace_write"),
        ("harness_improvement", ["repo.read", "repo.write", "code.search"], "disabled", "workspace_write"),
    ],
)
def test_api7_packet_uses_route_owned_capabilities_and_delegation_profile(
    task_type: str,
    capabilities: list[str],
    delegation_profile: str,
    workspace_write_access: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = load_module()
    request = managed_request(
        version=5,
        task_type=task_type,
        execution_mode="single_work_lane",
        planned_write_paths=["scripts/harness_task.py"] if "repo.write" in capabilities else [],
    )
    packet = harness.resolve_managed_packet(
        ROOT,
        request,
        attempt_id="attempt-1",
    )

    assert packet["capabilities"] == capabilities
    assert packet["delegation_profile"] == delegation_profile
    assert packet["workspace_write_access"] == workspace_write_access
    assert packet["runtime_provider"] == {"provider_id": "codex_app_server", "contract_version": 6}

def test_delegate_denies_ungranted_parent_before_child_work(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run = harness._new_run(managed_request(version=5, run_id=run_id, execution_mode="single_work_lane"), run_id)
    packet = harness.resolve_managed_packet(ROOT, run["request"], attempt_id="attempt-1")
    harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "preflight")
    harness._append_attempt(run, packet)
    try:
        harness._write_run(ROOT, run)

        result = harness.delegate(ROOT, run_id, packet["invocation_id"], {"idempotency_key": "child-1"})

        assert result == {"ok": False, "code": "delegation_not_permitted"}
        assert len(harness._load_run(ROOT, run_id)["attempts"]) == 1
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


def test_delegate_derives_one_idempotent_read_only_child(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run = harness._new_run(managed_request(version=5, run_id=run_id, execution_mode="single_work_lane"), run_id)
    packet = harness.resolve_managed_packet(ROOT, run["request"], attempt_id="attempt-1")
    packet["capabilities"] = ["repo.read", "harness.delegate"]
    packet["delegation_profile"] = "read_only_research"
    harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "preflight")
    harness._append_attempt(run, packet)
    harness._transition(run, harness._load_policy(ROOT)["states"], "running", "dispatch")
    try:
        harness._write_run(ROOT, run)
        request = {
            "idempotency_key": "child-1",
            "role": "investigate",
            "capabilities": ["repo.read"],
            "allowed_paths": ["scripts/**"],
            "timeout_seconds": 60,
        }

        first = harness.delegate(ROOT, run_id, packet["invocation_id"], request)
        second = harness.delegate(ROOT, run_id, packet["invocation_id"], request)

        assert first == second
        assert first["ok"] is True
        attempt = harness._load_run(ROOT, run_id)["attempts"][0]
        assert len(attempt["children"]) == 1
        assert attempt["reservation_ledger"] == [{"idempotency_key": "child-1", "timeout_seconds": 60, "released": False}]
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


def test_dispatch_preserves_failed_child_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class DelegatingAdapter(FakeAdapter):
        def __init__(self) -> None:
            super().__init__(
                {"single_work_lane": "enforced"},
                claim_payload={"kind": "claimed_result", "summary": "done", "findings": ["ok"]},
                host_api=6,
                identity={"provider_id": "codex_app_server", "contract_version": 6},
            )
            self.delegation_result = None

        def preflight_evidence(self):
            return copy.deepcopy(API6_BINDING)

        def dispatch_lane(self, lane, packet, workspace, delegation_bridge):
            self.calls.append("dispatch_lane")
            if lane["lane_id"] == "primary":
                self.delegation_result = delegation_bridge["delegate"]({
                    "idempotency_key": "child-1",
                    "role": "investigate",
                    "capabilities": ["repo.read", "code.search"],
                    "allowed_paths": ["docs/**"],
                    "timeout_seconds": 60,
                })
                assert self.delegation_result["ok"] is True
                delegation_bridge["complete"](
                    self.delegation_result["invocation_id"],
                    "failed",
                    None,
                )
            return {"lane_id": lane["lane_id"]}

        def verify_tool_bindings(self, lane, packet, workspace):
            bindings = super().verify_tool_bindings(lane, packet, workspace)
            for binding in bindings:
                binding["access"] = "read_only"
            return bindings

        def collect_lane_evidence(self, handle, lane, packet, workspace):
            evidence = super().collect_lane_evidence(handle, lane, packet, workspace)
            evidence["sandbox"] = "read-only"
            return evidence

    adapter = DelegatingAdapter()
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(
                version=5,
                run_id=run_id,
                task_type="research",
                execution_mode="single_work_lane",
                allowed_paths=["docs/**"],
                planned_write_paths=[],
            ),
            adapter,
            collect_changes=lambda root, base_commit: [],
        )

        assert result["state"] == "awaiting_decision"
        assert result["outcome"] == {
            "reason": "child_failed",
            "allowed_decisions": ["block"],
            "evidence_refs": ["children", "reservation_ledger"],
        }
        assert adapter.delegation_result == {
            "ok": True,
            "invocation_id": "attempt-1:primary/child-1",
            "status": "planned",
        }
        run = json.loads((run_dir / "run.json").read_text())
        children = run["attempts"][0]["children"]
        assert len(children) == 1
        assert children[0]["idempotency_key"] == "child-1"
        assert children[0]["status"] == "failed"
        assert children[0]["terminal_result"] == {
            "ok": True,
            "invocation_id": "attempt-1:primary/child-1",
            "status": "failed",
            "summary": "",
        }
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_delegate_releases_reservation_once_at_child_terminal_state(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run = harness._new_run(managed_request(version=5, run_id=run_id, execution_mode="single_work_lane"), run_id)
    packet = harness.resolve_managed_packet(ROOT, run["request"], attempt_id="attempt-1")
    packet["capabilities"] = ["repo.read", "harness.delegate"]
    packet["delegation_profile"] = "read_only_research"
    harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "preflight")
    harness._append_attempt(run, packet)
    harness._transition(run, harness._load_policy(ROOT)["states"], "running", "dispatch")
    try:
        harness._write_run(ROOT, run)
        child = harness.delegate(ROOT, run_id, packet["invocation_id"], {
            "idempotency_key": "child-1",
            "role": "investigate",
            "capabilities": ["repo.read"],
            "allowed_paths": ["scripts/**"],
            "timeout_seconds": 60,
        })
        assert harness._load_run(ROOT, run_id)["attempts"][0]["nodes"][0]["status"] == "waiting_for_child"
        claim = {"kind": "claimed_result", "summary": "found", "findings": ["ok"]}

        first = harness.complete_delegated_child(ROOT, run_id, child["invocation_id"], "succeeded", claim)
        second = harness.complete_delegated_child(ROOT, run_id, child["invocation_id"], "succeeded", claim)

        assert first == second == {"ok": True, "invocation_id": child["invocation_id"], "status": "succeeded", "summary": "found"}
        attempt = harness._load_run(ROOT, run_id)["attempts"][0]
        assert attempt["children"][0]["status"] == "succeeded"
        assert attempt["nodes"][0]["status"] == "running"
        assert attempt["reservation_ledger"] == [{"idempotency_key": "child-1", "timeout_seconds": 60, "released": True}]

        oversized = harness.delegate(ROOT, run_id, packet["invocation_id"], {
            "idempotency_key": "child-2",
            "role": "investigate",
            "capabilities": ["repo.read"],
            "allowed_paths": ["scripts/**"],
            "timeout_seconds": 60,
        })
        assert harness.complete_delegated_child(
            ROOT,
            run_id,
            oversized["invocation_id"],
            "succeeded",
            {"kind": "claimed_result", "summary": "x" * 4097, "findings": ["ok"]},
        ) == {"ok": False, "code": "delegation_result_invalid"}
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


def test_delegation_bridge_binds_one_parent_and_reads_derived_child_packet(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run = harness._new_run(managed_request(version=5, run_id=run_id, execution_mode="single_work_lane"), run_id)
    packet = harness.resolve_managed_packet(ROOT, run["request"], attempt_id="attempt-1")
    packet["capabilities"] = ["repo.read", "harness.delegate"]
    packet["delegation_profile"] = "read_only_research"
    harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "preflight")
    attempt = harness._append_attempt(run, packet)
    harness._transition(run, harness._load_policy(ROOT)["states"], "running", "dispatch")
    try:
        harness._write_run(ROOT, run)
        bridge = harness._delegation_bridge(ROOT, run, attempt, attempt["nodes"][0])
        child = bridge["delegate"]({
            "idempotency_key": "child-1",
            "role": "investigate",
            "capabilities": ["repo.read"],
            "allowed_paths": ["scripts/**"],
            "timeout_seconds": 60,
        })

        assert {key: bridge[key] for key in ("run_id", "attempt_id", "parent_node_id")} == {
            "run_id": run_id,
            "attempt_id": "attempt-1",
            "parent_node_id": "primary",
        }
        child_packet = bridge["child_packet"](child["invocation_id"])
        assert child_packet["parent_invocation_id"] == packet["invocation_id"]
        assert child_packet["agent_identity"] == packet["agent_identity"]
        assert child_packet["required_claim_kind"] == "claimed_result"
        assert child_packet["claim_schema"] == {
            "required_fields": ["summary", "findings"],
            "field_constraints": {},
        }
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


def test_delegate_cancellation_waits_for_controller_decision(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run = harness._new_run(managed_request(version=5, run_id=run_id, execution_mode="single_work_lane"), run_id)
    packet = harness.resolve_managed_packet(ROOT, run["request"], attempt_id="attempt-1")
    packet["capabilities"] = ["repo.read", "harness.delegate"]
    packet["delegation_profile"] = "read_only_research"
    harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "preflight")
    harness._append_attempt(run, packet)
    harness._transition(run, harness._load_policy(ROOT)["states"], "running", "dispatch")
    try:
        harness._write_run(ROOT, run)
        child = harness.delegate(ROOT, run_id, packet["invocation_id"], {
            "idempotency_key": "child-1",
            "role": "investigate",
            "capabilities": ["repo.read"],
            "allowed_paths": ["scripts/**"],
            "timeout_seconds": 60,
        })

        result = harness.complete_delegated_child(ROOT, run_id, child["invocation_id"], "cancelled", None)

        assert result == {"ok": True, "invocation_id": child["invocation_id"], "status": "cancelled", "summary": ""}
        resumed = harness._load_run(ROOT, run_id)
        assert resumed["state"] == "awaiting_decision"
        assert resumed["attempts"][0]["outcome"] == {
            "reason": "child_cancelled",
            "allowed_decisions": ["block"],
            "evidence_refs": ["children", "reservation_ledger"],
        }
        assert resumed["attempts"][0]["reservation_ledger"][0]["released"] is True
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


@pytest.mark.parametrize(
    ("child_request", "code"),
    [
        ({"idempotency_key": "child-1", "role": "investigate", "capabilities": ["repo.write"], "allowed_paths": ["scripts/**"], "timeout_seconds": 60}, "delegation_capability_exceeded"),
        ({"idempotency_key": "child-1", "role": "investigate", "capabilities": ["repo.read"], "allowed_paths": ["agents/**"], "timeout_seconds": 60}, "delegation_path_exceeded"),
        ({"idempotency_key": "child-1", "role": "investigate", "capabilities": ["repo.read"], "allowed_paths": ["scripts/**"], "timeout_seconds": 121}, "delegation_budget_exceeded"),
    ],
)
def test_delegate_denies_authority_expansion_before_child_creation(tmp_path: Path, child_request: dict[str, object], code: str) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run = harness._new_run(managed_request(version=5, run_id=run_id, execution_mode="single_work_lane"), run_id)
    packet = harness.resolve_managed_packet(ROOT, run["request"], attempt_id="attempt-1")
    packet["capabilities"] = ["repo.read", "harness.delegate"]
    packet["delegation_profile"] = "read_only_research"
    harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "preflight")
    harness._append_attempt(run, packet)
    harness._transition(run, harness._load_policy(ROOT)["states"], "running", "dispatch")
    try:
        harness._write_run(ROOT, run)

        result = harness.delegate(ROOT, run_id, packet["invocation_id"], child_request)

        assert result == {"ok": False, "code": code}
        attempt = harness._load_run(ROOT, run_id)["attempts"][0]
        assert "children" not in attempt
        assert "reservation_ledger" not in attempt
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


@pytest.mark.parametrize(
    ("child_request", "code"),
    [
        ({"idempotency_key": "child-1", "role": "investigate", "capabilities": ["repo.write"], "allowed_paths": ["scripts/**"], "timeout_seconds": 60}, "delegation_capability_exceeded"),
        ({"idempotency_key": "child-1", "role": "investigate", "capabilities": ["repo.read"], "allowed_paths": ["agents/**"], "timeout_seconds": 60}, "delegation_path_exceeded"),
        ({"idempotency_key": "child-1", "role": "investigate", "capabilities": ["repo.read"], "allowed_paths": ["scripts/**"], "timeout_seconds": 121}, "delegation_budget_exceeded"),
    ],
)
def test_delegate_denies_authority_expansion_before_child_creation_again(tmp_path: Path, child_request: dict[str, object], code: str) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run = harness._new_run(managed_request(version=5, run_id=run_id, execution_mode="single_work_lane"), run_id)
    packet = harness.resolve_managed_packet(ROOT, run["request"], attempt_id="attempt-1")
    packet["capabilities"] = ["repo.read", "harness.delegate"]
    packet["delegation_profile"] = "read_only_research"
    harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "preflight")
    harness._append_attempt(run, packet)
    harness._transition(run, harness._load_policy(ROOT)["states"], "running", "dispatch")
    try:
        harness._write_run(ROOT, run)

        result = harness.delegate(ROOT, run_id, packet["invocation_id"], child_request)

        assert result == {"ok": False, "code": code}
        attempt = harness._load_run(ROOT, run_id)["attempts"][0]
        assert "children" not in attempt
        assert "reservation_ledger" not in attempt
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


def test_run_managed_blocks_unsupported_host_api_before_packet_creation(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        with pytest.raises(harness.HarnessError, match="harness_core_host_api_incompatible"):
            harness.run_managed(
                ROOT,
                managed_request(run_id=run_id),
                FakeAdapter({"single_work_lane": "enforced"}, host_api=1),
            )

        assert not run_dir.exists()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_run_managed_records_adapter_host_api_in_packet(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter({"single_work_lane": "unavailable"}),
        )

        assert result["outcome"]["reason"] == "execution_mode_unavailable"
        packet = json.loads((run_dir / "run.json").read_text())["attempts"][0]["packet"]
        assert packet["core_identity"]["host_api"] == 6
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_run_managed_resumes_v3_packet_with_host2(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    request = managed_request(run_id=run_id)
    try:
        packet = harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")
        packet.pop("provider_runtime_binding")
        packet.update({
            "version": 3,
            "runtime_provider": {"provider_id": "codex_app_server", "contract_version": 2},
            "core_identity": {"package_release": "fixture", "request_api": 2, "packet_api": 3, "host_api": 2},
        })
        run = harness._new_run(request, run_id)
        harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "fixture")
        harness._append_attempt(run, packet)
        harness._write_run(ROOT, run)

        result = harness.run_managed(
            ROOT,
            None,
            FakeAdapter(
                {"single_work_lane": "unavailable"},
                host_api=2,
                identity={"provider_id": "codex_app_server", "contract_version": 2},
            ),
            run_id=run_id,
        )

        assert result["outcome"]["reason"] == "execution_mode_unavailable"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)

def test_run_managed_rejects_unreadable_packet_without_mutation(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        packet = harness.resolve_managed_packet(ROOT, managed_request(run_id=run_id), attempt_id="attempt-1")
        packet["core_identity"] = {"packet_api": 2}
        run = harness._new_run(managed_request(run_id=run_id), run_id)
        harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "fixture")
        harness._append_attempt(run, packet)
        harness._write_run(ROOT, run)
        before = (run_dir / "run.json").read_text(encoding="utf-8")

        with pytest.raises(harness.HarnessError, match="harness_core_packet_api_unreadable"):
            harness.run_managed(
                ROOT,
                None,
                FakeAdapter({"single_work_lane": "enforced"}),
                run_id=run_id,
            )

        assert (run_dir / "run.json").read_text(encoding="utf-8") == before
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
    assert packet["tool_bindings"] == [
        {"tool": "shell", "host_kind": "app_server_shell", "writer_access": "workspace_write", "validator_access": "read_only", "root_probe": "shell_root_probe"},
        {"tool": "serena", "host_kind": "local_serena", "writer_access": "workspace_write", "validator_access": "read_only", "root_probe": "serena_root_probe"},
        {"tool": "ast_grep_preview", "host_kind": "local_ast_grep", "writer_access": "read_only", "validator_access": "read_only", "root_probe": "ast_grep_root_probe"},
    ]


def test_resolve_managed_packet_derives_immutable_plan_binding(monkeypatch) -> None:
    harness = load_module()
    coordination = plan_coordination(execution_mode="sequential_work_lanes")
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)
    request = managed_request(
        version=5,
        plan_ref=coordination.plan_ref,
        plan_task_id="task-1",
        lanes=[{
            "lane_id": "work",
            "role": "implement",
            "allowed_paths": ["scripts/**"],
            "dependencies": [],
            "workspace_mode": "isolated",
            "write_capable": True,
        }],
    )
    for field in ("execution_mode", "base_ref", "allowed_paths", "planned_write_paths"):
        request.pop(field)

    packet = harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")

    assert packet["orchestration"]["name"] == "sequential_work_lanes"
    assert packet["base_ref"] == "HEAD"
    assert packet["allowed_paths"] == ["scripts/**", "tests/**"]
    assert packet["planned_write_paths"] == ["scripts/harness_task.py"]
    assert {key: packet[key] for key in ("plan_ref", "plan_task_id", "plan_digest")} == {
        "plan_ref": coordination.plan_ref,
        "plan_task_id": "task-1",
        "plan_digest": "plan-digest",
    }


@pytest.mark.parametrize(
    ("execution_mode", "lanes"),
    [
        ("single_work_lane", None),
        (
            "sequential_work_lanes",
            [
                {"lane_id": "first", "role": "implement", "allowed_paths": ["scripts/**"], "dependencies": [], "workspace_mode": "isolated", "write_capable": True},
                {"lane_id": "second", "role": "implement", "allowed_paths": ["tests/**"], "dependencies": ["first"], "workspace_mode": "isolated", "write_capable": True},
            ],
        ),
        (
            "parallel_work_lanes",
            [
                {"lane_id": "scripts", "role": "implement", "allowed_paths": ["scripts/**"], "dependencies": [], "workspace_mode": "isolated", "write_capable": True},
                {"lane_id": "tests", "role": "implement", "allowed_paths": ["tests/**"], "dependencies": [], "workspace_mode": "isolated", "write_capable": True},
            ],
        ),
    ],
)
def test_plan_bound_packet_uses_same_binding_for_every_canonical_topology(monkeypatch, execution_mode, lanes) -> None:
    harness = load_module()
    coordination = plan_coordination(execution_mode=execution_mode)
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)
    request = managed_request(version=5, plan_ref=coordination.plan_ref, plan_task_id="task-1")
    for field in ("execution_mode", "base_ref", "allowed_paths", "planned_write_paths"):
        request.pop(field)
    if lanes is not None:
        request["lanes"] = lanes

    packet = harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")

    assert packet["orchestration"]["name"] == execution_mode
    assert packet["plan_ref"] == coordination.plan_ref
    assert packet["plan_task_id"] == "task-1"
    assert packet["plan_digest"] == coordination.digest
    assert packet["allowed_paths"] == ["scripts/**", "tests/**"]


def test_resolve_managed_packet_rejects_conflicting_plan_field(monkeypatch) -> None:
    harness = load_module()
    coordination = plan_coordination(execution_mode="sequential_work_lanes")
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)

    with pytest.raises(harness.HarnessError, match="execution_mode.*conflicts"):
        harness.resolve_managed_packet(
            ROOT,
            managed_request(version=5, plan_ref=coordination.plan_ref, plan_task_id="task-1", execution_mode="single_work_lane"),
            attempt_id="attempt-1",
        )


def test_resolve_managed_packet_rejects_conflicting_plan_authorization_scope(monkeypatch) -> None:
    harness = load_module()
    coordination = plan_coordination()
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)

    with pytest.raises(harness.HarnessError, match="allowed_paths.*conflicts"):
        harness.resolve_managed_packet(
            ROOT,
            managed_request(
                version=5,
                plan_ref=coordination.plan_ref,
                plan_task_id="task-1",
                execution_mode="single_work_lane",
                allowed_paths=["repo_config/**"],
            ),
            attempt_id="attempt-1",
        )


def test_resolve_managed_packet_rejects_plan_path_outside_allowed_scope(monkeypatch) -> None:
    harness = load_module()
    coordination = plan_coordination(paths=("repo_config/harness.yaml",))
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)
    request = managed_request(version=5, plan_ref=coordination.plan_ref, plan_task_id="task-1")
    for field in ("execution_mode", "base_ref", "planned_write_paths"):
        request.pop(field)

    with pytest.raises(harness.HarnessError, match="planned_write_paths.*allowed_paths"):
        harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")


def test_successor_re_resolves_coordinated_manifest_fields() -> None:
    harness = load_module()
    request = managed_request(version=5, plan_ref="docs/superpowers/plans/fixture.md", plan_task_id="task-1")
    run = {"run_id": "run-1", "request": request, "attempts": [{"packet": {"plan_ref": request["plan_ref"]}}]}

    successor = harness._successor_request(run, {"plan_task_id": "task-2"})

    assert successor["plan_task_id"] == "task-2"
    assert {"execution_mode", "base_ref", "allowed_paths", "planned_write_paths"}.isdisjoint(successor)


def test_managed_continuation_blocks_changed_plan_digest_before_dispatch(monkeypatch, tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    original = plan_coordination(digest="original")
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: original)
    request = managed_request(
        version=5,
        run_id=run_id,
        execution_mode="single_work_lane",
        plan_ref=original.plan_ref,
        plan_task_id="task-1",
    )
    packet = harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")
    policy = harness._load_policy(ROOT)
    run = harness._new_run(request, run_id)
    harness._transition(run, policy["states"], "planned", "preflight")
    harness._append_attempt(run, packet)
    harness._write_run(ROOT, run)
    adapter = FakeAdapter({"single_work_lane": "enforced"})
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: plan_coordination(digest="changed"))
    try:
        result = harness.run_managed(ROOT, None, adapter, run_id=run_id)

        assert result["state"] == "awaiting_decision"
        assert result["outcome"]["reason"] == "plan_binding_changed"
        assert adapter.calls == []
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


def test_managed_continuation_blocks_changed_plan_base_commit_before_dispatch(monkeypatch, tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    coordination = plan_coordination(digest="stable")
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)
    request = managed_request(
        version=5,
        run_id=run_id,
        execution_mode="single_work_lane",
        plan_ref=coordination.plan_ref,
        plan_task_id="task-1",
    )
    packet = harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")
    policy = harness._load_policy(ROOT)
    run = harness._new_run(request, run_id)
    harness._transition(run, policy["states"], "planned", "preflight")
    harness._append_attempt(run, packet)
    harness._write_run(ROOT, run)
    adapter = FakeAdapter({"single_work_lane": "enforced"})
    monkeypatch.setattr(harness, "_resolve_commit", lambda *_args: "different-base")
    try:
        result = harness.run_managed(ROOT, None, adapter, run_id=run_id)

        assert result["state"] == "awaiting_decision"
        assert result["outcome"]["reason"] == "plan_binding_changed"
        assert adapter.calls == []
    finally:
        shutil.rmtree(ROOT / ".harness" / "runs" / run_id, ignore_errors=True)


def test_coordination_status_derives_dependency_and_active_states(monkeypatch, tmp_path: Path) -> None:
    harness = load_module()
    first = coordinated_task("task-1")
    second = coordinated_task("task-2", depends_on=("task-1",))
    coordination = plan_coordination_with_tasks(first, second)
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)
    write_coordinated_run(harness, tmp_path, "done", state="accepted", plan_ref=coordination.plan_ref, task_id="task-1")

    status = harness.coordination_status(tmp_path, coordination.plan_ref)

    assert [(task["id"], task["state"]) for task in status["tasks"]] == [("task-1", "done"), ("task-2", "ready")]
    write_coordinated_run(harness, tmp_path, "active", state="planned", plan_ref=coordination.plan_ref, task_id="task-2")
    status = harness.coordination_status(tmp_path, coordination.plan_ref)
    assert status["tasks"][1]["state"] == "active"


def test_controller_handoff_is_run_owned_and_rejects_terminal_run(monkeypatch, tmp_path: Path) -> None:
    harness = load_module()
    coordination = plan_coordination_with_tasks(coordinated_task("task-1"))
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)
    write_coordinated_run(harness, tmp_path, "handoff", state="planned", plan_ref=coordination.plan_ref, task_id="task-1")

    result = harness.record_controller_handoff(tmp_path, "handoff", {
        "last_verified_fact": "packet is valid",
        "next_action": "dispatch",
        "blocker_or_decision": "none",
    })

    assert result["handoff"]["next_action"] == "dispatch"
    assert result["handoff"]["timestamp"]
    write_coordinated_run(harness, tmp_path, "terminal", state="accepted", plan_ref=coordination.plan_ref, task_id="task-1")
    with pytest.raises(harness.HarnessError, match="terminal"):
        harness.record_controller_handoff(tmp_path, "terminal", {
            "last_verified_fact": "complete",
            "next_action": "none",
            "blocker_or_decision": "accepted",
        })


def test_coordination_status_and_handoff_cli_use_run_owned_state(tmp_path: Path) -> None:
    root = tmp_path / "harness"
    (root / "repo_config").mkdir(parents=True)
    shutil.copy2(ROOT / "repo_config" / "harness.yaml", root / "repo_config" / "harness.yaml")
    shutil.copy2(ROOT / "repo_config" / "planning_artifact_schema.yaml", root / "repo_config" / "planning_artifact_schema.yaml")
    plan_ref = "docs/superpowers/plans/fixture.md"
    plan_path = root / plan_ref
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(
        "---\nartifact_type: plan\nstatus: active\nlayer: change\ncoordination:\n"
        "  target_branch: main\n  base_ref: HEAD\n  tasks:\n"
        "    - id: task-1\n      depends_on: []\n"
            "      execution_mode: single_work_lane\n      allowed_paths: [scripts/**]\n      planned_write_paths: [scripts/**]\n"
        "---\n# Fixture\n\n### Task 1: Fixture\n\n**Coordination ID:** `task-1`\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", plan_ref], cwd=root, check=True)
    run_path = root / ".harness" / "runs" / "run-1" / "run.json"
    run_path.parent.mkdir(parents=True)
    run_path.write_text(json.dumps({
        "version": 1,
        "run_id": "run-1",
        "request": {},
        "state": "planned",
        "state_history": [{"state": "planned", "reason": "fixture", "at": "2026-08-06T00:00:00+00:00"}],
        "attempts": [{"packet": {"plan_ref": plan_ref, "plan_task_id": "task-1", "planned_write_paths": ["scripts/**"]}}],
    }), encoding="utf-8")

    status = subprocess.run(
        [*MANAGED_COMMAND, "--repo-root", str(root), "coordination-status", "--plan", plan_ref],
        capture_output=True,
        text=True,
        check=False,
    )
    handoff = subprocess.run(
        [
            *MANAGED_COMMAND,
            "--repo-root",
            str(root),
            "handoff",
            "--run-id",
            "run-1",
            "--handoff",
            json.dumps({"last_verified_fact": "packet valid", "next_action": "dispatch", "blocker_or_decision": "none"}),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert status.returncode == 0
    assert json.loads(status.stdout)["tasks"][0]["state"] == "active"
    assert handoff.returncode == 0
    assert json.loads(handoff.stdout)["handoff"]["next_action"] == "dispatch"
    assert json.loads(run_path.read_text(encoding="utf-8"))["attempts"][0]["handoff"]["timestamp"]


def test_coordinated_admission_blocks_unmet_dependencies_and_path_conflicts(monkeypatch, tmp_path: Path) -> None:
    harness = load_module()
    first = coordinated_task("task-1")
    second = coordinated_task("task-2", depends_on=("task-1",))
    current = plan_coordination_with_tasks(first, second)
    other = plan_coordination_with_tasks(
        coordinated_task("other-task"),
        plan_ref="docs/superpowers/plans/other.md",
    )
    manifests = {current.plan_ref: current, other.plan_ref: other}
    monkeypatch.setattr(harness, "load_plan_coordination", lambda _root, plan_ref, **_kwargs: manifests[plan_ref])
    packet = {
        "plan_ref": current.plan_ref,
        "plan_task_id": "task-2",
        "planned_write_paths": ["scripts/harness_task.py"],
    }

    with pytest.raises(harness.HarnessError, match="waiting_dependencies"):
        harness._admit_coordinated_packet(tmp_path, packet)

    write_coordinated_run(harness, tmp_path, "done", state="accepted", plan_ref=current.plan_ref, task_id="task-1")
    harness._admit_coordinated_packet(tmp_path, packet)
    write_coordinated_run(harness, tmp_path, "other", state="planned", plan_ref=other.plan_ref, task_id="other-task")
    with pytest.raises(harness.HarnessError, match="paths conflict"):
        harness._admit_coordinated_packet(tmp_path, packet)


def test_recover_stranded_running_run_records_external_failure_then_allows_block(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    write_stranded_run(harness, run_id)

    try:
        result = harness.recover_stranded_run(
            ROOT,
            run_id,
            "attempt-1",
            "host terminal evidence could not be recorded",
            recovery_evidence(run_id),
        )

        assert result["state"] == "awaiting_decision"
        run = json.loads((run_dir / "run.json").read_text())
        attempt = run["attempts"][0]
        assert attempt["outcome"] == {
            "reason": "stranded_running_recovered",
            "allowed_decisions": ["block"],
            "evidence_refs": ["evidence.failure", "evidence.external_failure", "evidence.recovery"],
            "detail": "host terminal evidence could not be recorded",
        }
        assert attempt["evidence"]["external_failure"] == recovery_evidence(run_id)
        assert attempt["evidence"]["recovery"]["run_id"] == run_id
        assert attempt["evidence"]["recovery"]["attempt_id"] == "attempt-1"
        assert len(attempt["evidence"]["recovery"]["packet_sha256"]) == 64

        blocked = harness.apply_controller_decision(ROOT, run_id, {"kind": "block"})
        assert blocked["state"] == "blocked"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_legacy_incompatible_request_can_block_but_not_retry(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    write_stranded_run(harness, run_id)

    try:
        harness.recover_stranded_run(
            ROOT,
            run_id,
            "attempt-1",
            "historical request cannot retry",
            recovery_evidence(run_id),
        )
        policy = harness._load_policy(ROOT)
        run = json.loads((run_dir / "run.json").read_text())
        run["version"] = 1
        run["request"]["version"] = 4
        run["attempts"][0]["packet"].pop("provider_runtime_binding", None)
        run["attempts"][0]["packet"]["version"] = 4
        harness._set_outcome(run["attempts"][0], "verification_failed", ["retry", "block"], [])
        harness._transition(run, policy["states"], "awaiting_decision", "verification_failed")
        harness._write_run(ROOT, run)
        before = json.loads((run_dir / "run.json").read_text())

        with pytest.raises(harness.HarnessError, match="harness_core_request_api_incompatible"):
            harness.apply_controller_decision(ROOT, run_id, {"kind": "retry"})

        assert json.loads((run_dir / "run.json").read_text()) == before
        blocked = harness.apply_controller_decision(ROOT, run_id, {"kind": "block"})
        persisted = json.loads((run_dir / "run.json").read_text())
        assert blocked["state"] == "blocked"
        assert persisted["request"]["version"] == 4
        assert len(persisted["attempts"]) == 1
        assert persisted["attempts"][0]["decision"]["kind"] == "block"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_recover_stranded_running_run_rejects_invalid_or_product_evidence(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    write_stranded_run(harness, run_id)

    try:
        with pytest.raises(harness.HarnessError, match="external recovery evidence is invalid"):
            harness.recover_stranded_run(ROOT, run_id, "attempt-1", "host record failure", None)

        with pytest.raises(harness.HarnessError, match="recovery attempt identity does not match run"):
            harness.recover_stranded_run(ROOT, run_id, "attempt-2", "host record failure", recovery_evidence(run_id))

        mismatched_evidence = recovery_evidence("other-run")
        with pytest.raises(harness.HarnessError, match="external recovery evidence identity does not match run"):
            harness.recover_stranded_run(ROOT, run_id, "attempt-1", "host record failure", mismatched_evidence)

        product_evidence = recovery_evidence(run_id)
        product_evidence["source"] = "product"
        with pytest.raises(harness.HarnessError, match="external recovery evidence source is invalid"):
            harness.recover_stranded_run(ROOT, run_id, "attempt-1", "host record failure", product_evidence)

        run = json.loads((run_dir / "run.json").read_text())
        run["attempts"][0]["claims"] = [{"kind": "claimed_result"}]
        (run_dir / "run.json").write_text(json.dumps(run), encoding="utf-8")
        with pytest.raises(harness.HarnessError, match="run is not stranded"):
            harness.recover_stranded_run(ROOT, run_id, "attempt-1", "host record failure", recovery_evidence(run_id))
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_resolve_managed_packet_rejects_disallowed_runtime_provider() -> None:
    harness = load_module()

    with pytest.raises(harness.HarnessError, match="runtime provider `missing` is not allowed"):
        harness.resolve_managed_packet(
            ROOT,
            managed_request(runtime_provider_id="missing"),
            attempt_id="attempt-1",
        )


def test_resolve_managed_packet_accepts_allowed_runtime_provider() -> None:
    harness = load_module()

    packet = harness.resolve_managed_packet(
        ROOT,
        managed_request(runtime_provider_id="codex_app_server"),
        attempt_id="attempt-1",
    )

    assert packet["runtime_provider"] == {"provider_id": "codex_app_server", "contract_version": 6}


@pytest.mark.parametrize(("task_type", "template", "model"), [
    ("research", "low", "combo-low"),
    ("local_change", "normal", "combo-normal"),
    ("plan_review", "high", "combo-high"),
])
def test_managed_packet_copies_template_model_identity(task_type, template, model) -> None:
    harness = load_module()

    packet = harness.resolve_managed_packet(
        ROOT,
        managed_request(task_type=task_type),
        attempt_id="attempt-1",
    )

    assert packet["agent_identity"] == {
        "template": template,
        "model_provider": "9router",
        "model": model,
        "reasoning_effort": "medium",
    }


def test_resolve_managed_packet_adds_system_lanes_after_api7_work_lane() -> None:
    harness = load_module()

    packet = harness.resolve_managed_packet(
        ROOT,
        managed_request(
            version=5,
            execution_mode="sequential_work_lanes",
            lanes=[{
                "lane_id": "work",
                "role": "implement",
                "allowed_paths": ["scripts/**"],
                "dependencies": [],
                "workspace_mode": "isolated",
                "write_capable": True,
            }],
        ),
        attempt_id="attempt-1",
    )

    assert [(lane["lane_id"], lane["kind"], lane["dependencies"]) for lane in packet["lanes"]] == [
        ("work", "work", []),
        ("integrate", "integrate", ["work"]),
        ("validate", "validate", ["integrate"]),
        ("check", "check", ["validate"]),
    ]


def test_preflight_cli_prints_only_packet_json(tmp_path: Path) -> None:
    task_path = tmp_path / "task.json"
    task_path.write_text(json.dumps(task()), encoding="utf-8")

    result = subprocess.run(
        [*MANAGED_COMMAND, "--repo-root", str(ROOT), "preflight", "--task", str(task_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(result.stdout)["template"] == "normal"


@pytest.mark.parametrize(
    "payload",
    [
        task(task_type="missing"),
        task(acceptance_criteria=[]),
        task(allowed_paths=["../escape"]),
        task(execution_mode="missing"),
    ],
)
def test_resolve_task_rejects_invalid_input(payload) -> None:
    harness = load_module()

    with pytest.raises(harness.HarnessError):
        harness.resolve_task(ROOT, payload)


def test_verify_rejects_scope_escape_and_approval_gate() -> None:
    harness = load_module()
    protected = task(allowed_paths=["repo_config/**"])

    result = harness.verify_task(
        ROOT,
        protected,
        claim(changed_files=["repo_config/harness.yaml"]),
        changed_paths=["repo_config/harness.yaml"],
        run_check=lambda command: (0, "", ""),
    )

    assert result["status"] == "observed"
    assert result["blockers"] == [
        {"kind": "approval", "gate": "protected_policy", "path": "repo_config/harness.yaml"}
    ]


def test_verify_produces_verified_evidence_and_optional_run_file(tmp_path: Path) -> None:
    harness = load_module()
    run_dir = ROOT / ".harness" / "runs" / tmp_path.name
    try:
        result = harness.verify_task(
            ROOT,
            task(run_dir=str(run_dir)),
            claim(),
            changed_paths=["scripts/example.py"],
            run_check=lambda command: (0, "ok", ""),
        )

        assert result["status"] == "verified"
        assert result["acceptance"] == [{"criterion": "focused test passes", "proven": True}]
        assert (run_dir / "evidence.json").is_file()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_verify_rejects_run_path_outside_harness(tmp_path: Path) -> None:
    harness = load_module()

    with pytest.raises(harness.HarnessError, match="run_dir must stay under"):
        harness.verify_task(
            ROOT,
            task(run_dir=str(tmp_path)),
            claim(),
            changed_paths=["scripts/example.py"],
            run_check=lambda command: (0, "", ""),
        )


def test_verify_rejects_failed_check_and_invalid_transition() -> None:
    harness = load_module()

    result = harness.verify_task(
        ROOT,
        task(),
        claim(from_state="running", next_state="accepted"),
        changed_paths=["scripts/example.py"],
        run_check=lambda command: (1, "", "failed"),
    )

    assert result["status"] == "observed"
    assert {blocker["kind"] for blocker in result["blockers"]} == {"check", "transition"}


def test_run_managed_blocks_unavailable_mode_without_dispatch(tmp_path: Path) -> None:
    harness = load_module()
    adapter = FakeAdapter({"single_work_lane": "enforced"})
    run_dir = ROOT / ".harness" / "runs" / tmp_path.name
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(
                    execution_mode="sequential_work_lanes",
                run_id=tmp_path.name,
                lanes=[{
                    "lane_id": "primary",
                    "role": "implement",
                    "allowed_paths": ["scripts/**", "tests/**"],
                    "dependencies": [],
                    "workspace_mode": "isolated",
                    "write_capable": True,
                }],
            ),
            adapter,
        )

        assert result["state"] == "awaiting_decision"
        assert result["outcome"]["reason"] == "execution_mode_unavailable"
        assert adapter.calls == ["capabilities"]
        assert (run_dir / "run.json").is_file()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_adapter_identity_mismatch_blocks_before_workspace_preparation(tmp_path: Path) -> None:
    harness = load_module()
    adapter = FakeAdapter(
        {"single_work_lane": "enforced"},
        identity={"provider_id": "codex_app_server", "contract_version": 1},
    )
    run_dir = ROOT / ".harness" / "runs" / tmp_path.name
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=tmp_path.name), adapter)

        assert result["outcome"]["reason"] == "dispatch_failed"
        assert adapter.calls == ["capabilities"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_unavailable_managed_run_requires_explicit_unvalidated_waiver(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=run_id), FakeAdapter({}))

        assert result["outcome"]["reason"] == "execution_mode_unavailable"
        assert result["outcome"]["allowed_decisions"] == ["waive", "block"]
        with pytest.raises(harness.HarnessError, match="waiver reason"):
            harness.apply_controller_decision(ROOT, run_id, {"kind": "waive"})

        waived = harness.apply_controller_decision(
            ROOT,
            run_id,
            {"kind": "waive", "reason": "host adapter unavailable"},
        )

        assert waived["state"] == "unvalidated"
        run = json.loads((run_dir / "run.json").read_text())
        assert run["attempts"][0]["decision"]["reason"] == "host adapter unavailable"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_generic_cli_records_unavailable_adapter_proof(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    task_path = tmp_path / "task.json"
    decision_path = tmp_path / "decision.json"
    task_path.write_text(json.dumps(managed_request(run_id=run_id)), encoding="utf-8")
    decision_path.write_text(
        json.dumps({"kind": "waive", "reason": "generic CLI has no host adapter"}),
        encoding="utf-8",
    )
    try:
        assert harness.main(["--repo-root", str(ROOT), "run-unavailable", "--task", str(task_path)]) == 1
        assert harness.main(
            ["--repo-root", str(ROOT), "decision", "--run-id", run_id, "--decision", str(decision_path)]
        ) == 1

        run = json.loads((run_dir / "run.json").read_text())
        assert run["state"] == "unvalidated"
        assert run["attempts"][0]["outcome"]["reason"] == "execution_mode_unavailable"
        assert run["attempts"][0]["outcome"]["detail"] == (
            "Generic harness CLI has no injected host adapter; use a provider host entrypoint."
        )
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_generic_cli_rejects_managed_run_command(tmp_path: Path) -> None:
    harness = load_module()
    run_dir = ROOT / ".harness" / "runs" / tmp_path.name
    task_path = tmp_path / "task.json"
    task_path.write_text(json.dumps(managed_request(run_id=tmp_path.name)), encoding="utf-8")
    shutil.rmtree(run_dir, ignore_errors=True)
    try:
        with pytest.raises(SystemExit) as error:
            harness.main(["--repo-root", str(ROOT), "run", "--task", str(task_path)])

        assert error.value.code == 2
        assert not (run_dir / "run.json").exists()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_run_managed_records_evidence_then_controller_accepts(tmp_path: Path) -> None:
    harness = load_module()
    adapter = FakeAdapter({"single_work_lane": "enforced"})
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            adapter,
            run_check=lambda command: (0, "ok", ""),
            collect_changes=lambda root, base_commit: [],
        )

        assert result["state"] == "awaiting_decision"
        assert result["outcome"]["reason"] == "verification_passed"
        assert adapter.calls == [
            "capabilities",
            "prepare_workspace",
            "verify_tool_bindings",
            "dispatch_lane",
            "collect_lane_evidence",
            "collect_claim",
            "materialize_final_state",
            "verify_tool_bindings",
            "dispatch_lane",
            "collect_lane_evidence",
            "collect_claim",
        ]

        accepted = harness.apply_controller_decision(ROOT, run_id, {"kind": "accept"})

        assert accepted["state"] == "accepted"
        run = json.loads((run_dir / "run.json").read_text())
        assert [item["state"] for item in run["state_history"]] == [
            "classified", "planned", "running", "observed", "verifying", "awaiting_decision", "accepted"
        ]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_run_managed_requires_ready_provider_binding_before_packet_creation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    harness = load_module()

    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        class MissingBindingAdapter(FakeAdapter):
            preflight_evidence = None

        with pytest.raises(harness.HarnessError, match="provider preflight evidence is required"):
            harness.run_managed(
                ROOT,
                managed_request(version=5, run_id=run_id),
                MissingBindingAdapter(
                    {"single_work_lane": "enforced"},
                    host_api=6,
                    identity={"provider_id": "codex_app_server", "contract_version": 6},
                ),
            )

        assert not run_dir.exists()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_run_managed_blocks_dirty_workspace_before_writer_dispatch(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class DirtyWorkspaceAdapter(FakeAdapter):
        def prepare_workspace(self, lane, packet):
            workspace = super().prepare_workspace(lane, packet)
            workspace["baseline"]["clean"] = False
            return workspace

    adapter = DirtyWorkspaceAdapter({"single_work_lane": "enforced"})
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            adapter,
        )

        assert result["state"] == "awaiting_decision"
        assert result["outcome"]["reason"] == "workspace_baseline_invalid"
        assert adapter.calls == ["capabilities", "prepare_workspace"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_provider_conformance_vector_accepts_adapter_implementation(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    workspace = tmp_path / "adapter-workspace"
    adapter = FakeAdapter({"single_work_lane": "enforced"}, workspace_root=workspace)
    try:
        run = assert_provider_conformance(harness, adapter, run_id, workspace)

        accepted = harness.apply_controller_decision(ROOT, run_id, {"kind": "accept"})

        assert accepted["state"] == "accepted"
        assert run["state"] == "awaiting_decision"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_unverified_packet_tool_blocks_before_writer_dispatch(tmp_path: Path) -> None:
    class UnboundToolAdapter(FakeAdapter):
        def verify_tool_bindings(self, lane, packet, workspace):
            self.calls.append("verify_tool_bindings")
            raise RuntimeError("packet-scoped native tool roots unavailable: serena")

    harness = load_module()
    adapter = UnboundToolAdapter({"single_work_lane": "enforced"})
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=run_id), adapter)

        assert result["state"] == "awaiting_decision"
        assert result["outcome"]["reason"] == "dispatch_failed"
        assert result["outcome"]["detail"] == "packet-scoped native tool roots unavailable: serena"
        run = json.loads((run_dir / "run.json").read_text())
        assert run["attempts"][0]["evidence"]["failure"] == {
            "detail": "packet-scoped native tool roots unavailable: serena",
            "phase": "dispatch",
            "reason": "dispatch_failed",
        }
        assert adapter.calls == ["capabilities", "prepare_workspace", "verify_tool_bindings"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_read_only_work_evidence_uses_effective_packet_access() -> None:
    harness = load_module()
    runtime_provider = {"provider_id": "codex_app_server", "contract_version": 5}
    workspace = {"path": "C:\\workspace"}
    packet = {
        "workspace_write_access": "read_only",
        "runtime_provider": runtime_provider,
        "agent_identity": {"template": "low"},
        "tool_bindings": [{
            "tool": "shell",
            "host_kind": "app_server_shell",
            "writer_access": "workspace_write",
            "validator_access": "read_only",
            "root_probe": "shell_root_probe",
        }],
    }
    lane = {"lane_id": "primary", "kind": "work"}
    bindings = [{
        "tool": "shell",
        "host_kind": "app_server_shell",
        "access": "read_only",
        "root_probe": "shell_root_probe",
        "workspace_root": workspace["path"],
        "verified": True,
        "runtime_provider": runtime_provider,
    }]
    evidence = {
        "lane_id": "primary",
        "workspace_root": workspace["path"],
        "sandbox": "read-only",
        "ambient_mcp": False,
        "runtime_provider": runtime_provider,
        "agent_identity": packet["agent_identity"],
        "thread_id": "thread",
        "turn_id": "turn",
        "workspace_status_before": "",
        "workspace_status_after": "",
        "selected_tools_used": ["shell"],
        "tool_calls": ["shell"],
        "command_results": [{"cwd": workspace["path"], "runtime_provider": runtime_provider}],
    }
    attempt: dict[str, object] = {}

    harness._record_tool_binding_evidence(attempt, lane, packet, workspace, bindings)
    harness._record_lane_execution_evidence(attempt, lane, packet, workspace, evidence)

    assert attempt["tool_binding_evidence"][0]["bindings"] == bindings
    assert attempt["execution_evidence"] == [evidence]

def test_mismatched_tool_binding_provider_blocks_before_writer_dispatch(tmp_path: Path) -> None:
    class MismatchedProviderAdapter(FakeAdapter):
        def verify_tool_bindings(self, lane, packet, workspace):
            bindings = super().verify_tool_bindings(lane, packet, workspace)
            bindings[0]["runtime_provider"] = {"provider_id": "other", "contract_version": 1}
            return bindings

    harness = load_module()
    adapter = MismatchedProviderAdapter({"single_work_lane": "enforced"})
    run_dir = ROOT / ".harness" / "runs" / tmp_path.name
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=tmp_path.name), adapter)

        assert result["outcome"]["reason"] == "dispatch_failed"
        assert adapter.calls == ["capabilities", "prepare_workspace", "verify_tool_bindings"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_missing_command_result_provider_blocks_before_verification(tmp_path: Path) -> None:
    class MissingCommandProviderAdapter(FakeAdapter):
        def collect_lane_evidence(self, handle, lane, packet, workspace):
            evidence = super().collect_lane_evidence(handle, lane, packet, workspace)
            del evidence["command_results"][0]["runtime_provider"]
            return evidence

    harness = load_module()
    adapter = MissingCommandProviderAdapter({"single_work_lane": "enforced"})
    run_dir = ROOT / ".harness" / "runs" / tmp_path.name
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=tmp_path.name), adapter)

        assert result["outcome"]["reason"] == "dispatch_failed"
        assert adapter.calls == [
            "capabilities",
            "prepare_workspace",
            "verify_tool_bindings",
            "dispatch_lane",
            "collect_lane_evidence",
            "cancel_lane",
        ]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


@pytest.mark.parametrize("field", ["agent_identity", "model", "reasoning_effort"])
def test_missing_or_mismatched_agent_identity_blocks_before_verification(tmp_path: Path, field: str) -> None:
    class MismatchedAgentAdapter(FakeAdapter):
        def collect_lane_evidence(self, handle, lane, packet, workspace):
            evidence = super().collect_lane_evidence(handle, lane, packet, workspace)
            if field == "agent_identity":
                del evidence[field]
            else:
                evidence["agent_identity"] = dict(evidence["agent_identity"])
                evidence["agent_identity"][field] = "wrong"
            return evidence

    harness = load_module()
    run_dir = ROOT / ".harness" / "runs" / tmp_path.name
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=tmp_path.name),
            MismatchedAgentAdapter({"single_work_lane": "enforced"}),
        )

        assert result["outcome"]["reason"] == "dispatch_failed"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_cancellation_failure_records_normalized_friction(tmp_path: Path) -> None:
    class CancellationFailureAdapter(FakeAdapter):
        def collect_lane_evidence(self, handle, lane, packet, workspace):
            raise RuntimeError("evidence unavailable")

        def cancel_lane(self, handle):
            super().cancel_lane(handle)
            raise RuntimeError("cancellation unavailable")

    harness = load_module()
    run_dir = ROOT / ".harness" / "runs" / tmp_path.name
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=tmp_path.name),
            CancellationFailureAdapter({"single_work_lane": "enforced"}),
        )

        assert result["outcome"]["reason"] == "dispatch_failed"
        events = [json.loads(line) for line in FRICTION_EVENTS_ROOT.read_text().splitlines()]
        assert [event["code"] for event in events] == ["cancellation_failed", "dispatch_failed"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_managed_run_uses_host_check_evidence(tmp_path: Path) -> None:
    harness = load_module()
    adapter = FakeAdapter({"single_work_lane": "enforced"})
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            adapter,
            collect_changes=lambda root, base_commit: [],
        )

        assert result["outcome"]["reason"] == "verification_passed"
        run = json.loads((run_dir / "run.json").read_text())
        assert len(run["attempts"][0]["tool_binding_evidence"]) == 2
        assert [record["lane_id"] for record in run["attempts"][0]["execution_evidence"]] == ["primary", "validate"]
        assert [record["lane_id"] for record in run["attempts"][0]["claims"]] == ["primary", "validate"]
        assert [record["node_id"] for record in run["attempts"][0]["node_observations"]] == ["integrate", "check"]
        assert run["attempts"][0]["evidence"]["checks"][0]["workspace_root"] == str(ROOT)
        assert adapter.calls.count("dispatch_lane") == 2
        assert adapter.calls.count("collect_claim") == 2
        assert "run_checks" in adapter.calls
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_managed_validator_fail_blocks_acceptance(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter(
                {"single_work_lane": "enforced"},
                validator_claim={
                    "kind": "claimed_result",
                    "summary": "validation failed",
                    "findings": ["failure"],
                    "verdict": "fail",
                },
            ),
            run_check=lambda command: (0, "ok", ""),
            collect_changes=lambda root, base_commit: [],
        )

        assert result["outcome"]["reason"] == "verification_failed"
        evidence = json.loads((run_dir / "run.json").read_text())["attempts"][0]["evidence"]
        assert evidence["criteria"][-1] == {
            "id": "validator",
            "kind": "validator",
            "status": "failed",
            "evidence_ref": "validator_claim",
        }
        with pytest.raises(harness.HarnessError, match="not allowed for current outcome"):
            harness.apply_controller_decision(ROOT, run_id, {"kind": "accept"})
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_managed_validator_rejects_invalid_verdict(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter(
                {"single_work_lane": "enforced"},
                validator_claim={
                    "kind": "claimed_result",
                    "summary": "invalid validation",
                    "findings": ["invalid"],
                    "verdict": "unknown",
                },
            ),
        )

        assert result["outcome"]["reason"] == "claim_invalid"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


@pytest.mark.parametrize(
    ("execution_mode", "lanes", "work_lane_ids"),
    [
        ("single_work_lane", None, ["primary"]),
        (
            "sequential_work_lanes",
            [
                {
                    "lane_id": "first",
                    "role": "implement",
                    "allowed_paths": ["scripts/**"],
                    "dependencies": [],
                    "workspace_mode": "isolated",
                    "write_capable": True,
                },
                {
                    "lane_id": "second",
                    "role": "implement",
                    "allowed_paths": ["tests/**"],
                    "dependencies": ["first"],
                    "workspace_mode": "isolated",
                    "write_capable": True,
                },
            ],
            ["first", "second"],
        ),
        (
            "parallel_work_lanes",
            [
                {
                    "lane_id": "scripts",
                    "role": "implement",
                    "allowed_paths": ["scripts/**"],
                    "dependencies": [],
                    "workspace_mode": "isolated",
                    "write_capable": True,
                },
                {
                    "lane_id": "tests",
                    "role": "implement",
                    "allowed_paths": ["tests/**"],
                    "dependencies": [],
                    "workspace_mode": "isolated",
                    "write_capable": True,
                },
            ],
            ["scripts", "tests"],
        ),
    ],
)
def test_plan_bound_managed_scheduler_proves_every_canonical_topology(
    tmp_path: Path,
    monkeypatch,
    execution_mode: str,
    lanes: list[dict[str, object]] | None,
    work_lane_ids: list[str],
) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    coordination = plan_coordination_with_tasks(
        coordinated_task("task-1", execution_mode=execution_mode),
    )
    monkeypatch.setattr(harness, "load_plan_coordination", lambda *_args, **_kwargs: coordination)
    request = managed_request(version=5, run_id=run_id, plan_ref=coordination.plan_ref, plan_task_id="task-1")
    for field in ("execution_mode", "base_ref", "allowed_paths", "planned_write_paths"):
        request.pop(field)
    if lanes is not None:
        request["lanes"] = lanes
    try:
        result = harness.run_managed(
            ROOT,
            request,
            FakeAdapter({execution_mode: "enforced"}),
            run_check=lambda command: (0, "ok", ""),
            collect_changes=lambda root, base_commit: [],
        )

        assert result["outcome"]["reason"] == "verification_passed"
        attempt = json.loads((run_dir / "run.json").read_text())["attempts"][0]
        assert {key: attempt["packet"][key] for key in ("plan_ref", "plan_task_id", "plan_digest")} == {
            "plan_ref": coordination.plan_ref,
            "plan_task_id": "task-1",
            "plan_digest": coordination.digest,
        }
        assert [node["lane_id"] for node in attempt["nodes"]] == [
            *work_lane_ids,
            "integrate",
            "validate",
            "check",
        ]
        assert [record["lane_id"] for record in attempt["claims"]] == [
            *work_lane_ids,
            "validate",
        ]
        assert [record["node_id"] for record in attempt["node_observations"]] == [
            "integrate",
            "check",
        ]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_managed_verification_rejects_forged_claim_approval(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    claim_payload = {
        "kind": "claimed_result",
        "summary": "done",
        "changed_files": ["repo_config/harness.yaml"],
        "approved_gates": ["protected_policy"],
    }
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(
                run_id=run_id,
                allowed_paths=["scripts/**", "repo_config/**"],
            ),
            FakeAdapter({"single_work_lane": "enforced"}, claim_payload),
            run_check=lambda command: (0, "ok", ""),
            collect_changes=lambda root, base_commit: [{"path": "repo_config/harness.yaml", "kind": "modified"}],
        )

        assert result["outcome"]["reason"] == "approval_required"
        with pytest.raises(harness.HarnessError, match="not allowed"):
            harness.apply_controller_decision(ROOT, run_id, {"kind": "accept"})
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_managed_review_criterion_never_auto_proves(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(
                run_id=run_id,
                acceptance_criteria=[
                    {"id": "diff", "kind": "check", "check": "diff"},
                    {"id": "review", "kind": "review"},
                ],
            ),
            FakeAdapter({"single_work_lane": "enforced"}),
            run_check=lambda command: (0, "ok", ""),
            collect_changes=lambda root, base_commit: [],
        )

        assert result["outcome"]["reason"] == "review_required"
        evidence = json.loads((run_dir / "run.json").read_text())["attempts"][0]["evidence"]
        assert [criterion["status"] for criterion in evidence["criteria"]] == [
            "proven",
            "review_required",
            "proven",
        ]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_retry_creates_immutable_successor_then_exhausts(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        first = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter({"single_work_lane": "enforced"}),
            run_check=lambda command: (1, "", "failed"),
            collect_changes=lambda root, base_commit: [],
        )
        assert first["outcome"]["reason"] == "verification_failed"

        retry = harness.apply_controller_decision(ROOT, run_id, {"kind": "retry"})
        assert retry["state"] == "planned"
        before = json.loads((run_dir / "run.json").read_text())["attempts"][0]["packet"]

        second = harness.run_managed(
            ROOT,
            None,
            FakeAdapter({"single_work_lane": "enforced"}),
            run_id=run_id,
            run_check=lambda command: (1, "", "failed"),
            collect_changes=lambda root, base_commit: [],
        )
        assert second["outcome"]["reason"] == "verification_failed"
        exhausted = harness.apply_controller_decision(ROOT, run_id, {"kind": "retry"})

        run = json.loads((run_dir / "run.json").read_text())
        assert exhausted["state"] == "blocked"
        assert len(run["attempts"]) == 2
        assert run["attempts"][0]["packet"]["runtime_provider"] == {
            "provider_id": "codex_app_server",
            "contract_version": 6,
        }
        assert run["attempts"][1]["packet"]["runtime_provider"] == run["attempts"][0]["packet"]["runtime_provider"]
        assert run["attempts"][1]["packet"]["provider_runtime_binding"] == run["attempts"][0]["packet"]["provider_runtime_binding"]
        assert run["attempts"][0]["packet"] == before
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_collect_changes_includes_untracked_paths(tmp_path: Path) -> None:
    harness = load_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    (repo / "untracked.txt").write_text("new\n", encoding="utf-8")

    changes = harness._collect_changes(repo, "HEAD")

    assert changes == [{"path": "untracked.txt", "kind": "untracked"}]


def test_managed_planned_gate_blocks_before_dispatch_and_accepts_controller_approval(tmp_path: Path) -> None:
    harness = load_module()
    now = datetime.now(UTC)
    blocked_id = f"{tmp_path.name}-blocked"
    blocked_dir = ROOT / ".harness" / "runs" / blocked_id
    approved_id = f"{tmp_path.name}-approved"
    approved_dir = ROOT / ".harness" / "runs" / approved_id
    request = {
        "allowed_paths": ["repo_config/**"],
        "planned_write_paths": ["repo_config/harness.yaml"],
    }
    try:
        blocked_adapter = FakeAdapter({"single_work_lane": "enforced"})
        blocked = harness.run_managed(
            ROOT,
            managed_request(run_id=blocked_id, **request),
            blocked_adapter,
            now=now,
        )
        assert blocked["outcome"]["reason"] == "approval_required"
        assert blocked_adapter.calls == []

        approved = harness.run_managed(
            ROOT,
            managed_request(
                run_id=approved_id,
                **request,
                approvals=[{
                    "gate": "protected_policy",
                    "approver": "controller",
                    "paths": ["repo_config/**"],
                    "attempt_id": "attempt-1",
                    "issued_at": now.isoformat(),
                }],
            ),
            FakeAdapter({"single_work_lane": "enforced"}),
            run_check=lambda command: (0, "ok", ""),
            collect_changes=lambda root, base_commit: [],
            now=now,
        )
        assert approved["outcome"]["reason"] == "verification_passed"
    finally:
        shutil.rmtree(blocked_dir, ignore_errors=True)
        shutil.rmtree(approved_dir, ignore_errors=True)


def test_managed_dispatch_failure_becomes_retryable_outcome(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter({"single_work_lane": "enforced"}, dispatch_error=RuntimeError("offline")),
        )

        assert result["state"] == "awaiting_decision"
        assert result["outcome"]["reason"] == "dispatch_failed"
        assert result["outcome"]["allowed_decisions"] == ["retry", "escalate", "block"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


@pytest.mark.parametrize(
    ("field_type", "valid_value", "invalid_value"),
    [
        ("nonempty_string", "ok", ""),
        ("string_list", ["ok"], [""]),
        ("friction_list", [{"category": "blocked"}], [{"category": ""}]),
    ],
)
def test_v7_claim_validation_uses_packet_field_types(field_type, valid_value, invalid_value) -> None:
    harness = load_module()
    schema = {
        "required_fields": ["value"],
        "field_types": {"value": field_type},
        "optional_field_types": {},
        "field_constraints": {},
    }

    assert harness._validate_managed_claim(
        {"kind": "claimed_result", "value": valid_value},
        required_claim_kind="claimed_result",
        claim_schema=schema,
    )["value"] == valid_value
    with pytest.raises(harness.ClaimError, match="managed claim field `value` has invalid type"):
        harness._validate_managed_claim(
            {"kind": "claimed_result", "value": invalid_value},
            required_claim_kind="claimed_result",
            claim_schema=schema,
        )


@pytest.mark.parametrize(
    ("role_name", "field_types"),
    [
        ("implement", {"summary": "nonempty_string", "changed_files": "string_list"}),
        ("investigate", {"summary": "nonempty_string", "findings": "string_list"}),
        ("review", {"summary": "nonempty_string", "findings": "string_list"}),
        ("validate", {"summary": "nonempty_string", "findings": "string_list", "verdict": "nonempty_string"}),
        ("improve", {"summary": "nonempty_string", "changed_files": "string_list", "decision": "nonempty_string"}),
    ],
)
def test_v7_claim_schema_projects_typed_catalog_for_every_role(role_name, field_types) -> None:
    harness = load_module()
    roles, claim_fields = harness._load_role_catalog(ROOT)

    schema = harness._claim_schema(roles[role_name], claim_fields)

    assert schema["field_types"] == field_types
    assert schema["optional_field_types"]["frictions"] == "friction_list"


@pytest.mark.parametrize(
    ("observation", "subcode"),
    [
        ({"state": "missing"}, "missing_final_claim"),
        ({"state": "non_json"}, "claim_not_json"),
        ({"state": "json_non_object"}, "claim_not_object"),
        ({"state": "object", "candidate_claim": {"kind": "wrong"}}, "claim_kind_mismatch"),
    ],
)
def test_v7_repairs_each_unusable_claim_once(tmp_path: Path, observation, subcode) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    adapter = FakeAdapter(
        {"single_work_lane": "enforced", "claim_repair_same_thread": "enforced"},
        claim_payload=observation,
    )
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=run_id), adapter)
        run = json.loads((run_dir / "run.json").read_text())
        repair = run["attempts"][0]["evidence"]["claim_repair"][0]

        assert result["outcome"]["reason"] != "claim_invalid"
        assert len(run["attempts"]) == 1
        assert adapter.calls.count("repair_claim") == 1
        assert repair["subcode"] == subcode
        assert repair["admission"] == {"admitted": True, "reason": "eligible"}
        assert repair["repair_count"] == 1
        assert repair["finalization_identity"] == {"thread_id": "thread", "turn_id": "repair-primary"}
        assert repair["repeated_validation"] == {"status": "valid"}
        assert "candidate_claim" not in repair
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_v7_repairs_validator_claim_on_same_attempt(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    adapter = FakeAdapter(
        {"single_work_lane": "enforced", "claim_repair_same_thread": "enforced"},
        validator_claim={"state": "missing"},
        repair_payload={
            "kind": "claimed_result",
            "summary": "repaired validation",
            "findings": ["ok"],
            "verdict": "pass",
        },
    )
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            adapter,
            run_check=lambda command: (0, "ok", ""),
            collect_changes=lambda root, base_commit: [],
        )
        repair = json.loads((run_dir / "run.json").read_text())["attempts"][0]["evidence"]["claim_repair"][0]

        assert result["outcome"]["reason"] == "verification_passed"
        assert adapter.calls.count("repair_claim") == 1
        assert repair["lane_id"] == "validate"
        assert repair["repeated_validation"] == {"status": "valid"}
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_v7_repair_budget_rejects_repeat_for_same_lane() -> None:
    harness = load_module()
    packet = harness.resolve_managed_packet(ROOT, managed_request(), attempt_id="attempt-1")
    lane = packet["lanes"][0]
    attempt = {"evidence": {"claim_repair": [{
        "lane_id": "primary",
        "admission": {"admitted": True, "reason": "eligible"},
        "repair_count": 1,
    }]}}
    evidence = {"terminal_status": "completed", "thread_id": "thread"}

    admitted, reason, repair_count = harness._claim_repair_admission(
        attempt,
        lane,
        packet,
        evidence,
        {"claim_repair_same_thread": "enforced"},
    )

    assert (admitted, reason, repair_count) == (False, "repair_budget_exhausted", 1)


def test_v7_failed_repair_records_one_friction_then_claim_invalid(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    adapter = FakeAdapter(
        {"single_work_lane": "enforced", "claim_repair_same_thread": "enforced"},
        claim_payload={"state": "missing"},
        repair_payload={"state": "object", "candidate_claim": {"kind": "wrong"}},
    )
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=run_id), adapter)
        run = json.loads((run_dir / "run.json").read_text())
        events = [json.loads(line) for line in FRICTION_EVENTS_ROOT.read_text().splitlines()]

        assert result["outcome"]["reason"] == "claim_invalid"
        assert adapter.calls.count("repair_claim") == 1
        assert [event["code"] for event in events].count("claim_repair_failed") == 1
        assert run["attempts"][0]["evidence"]["claim_repair"][0]["repeated_validation"] == {
            "status": "invalid",
            "subcode": "claim_kind_mismatch",
        }
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_v7_timed_out_repair_records_claim_invalid(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    adapter = FakeAdapter(
        {"single_work_lane": "enforced", "claim_repair_same_thread": "enforced"},
        claim_payload={"state": "missing"},
        repair_payload={"state": "missing"},
        repair_terminal_status="timed_out",
    )
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=run_id), adapter)
        run = json.loads((run_dir / "run.json").read_text())
        events = [json.loads(line) for line in FRICTION_EVENTS_ROOT.read_text().splitlines()]

        assert result["outcome"]["reason"] == "claim_invalid"
        assert adapter.calls.count("repair_claim") == 1
        assert [event["code"] for event in events].count("claim_repair_failed") == 1
        assert run["attempts"][0]["evidence"]["claim_repair"][0]["repeated_validation"] == {
            "status": "invalid",
            "subcode": "missing_final_claim",
        }
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_v7_missing_repair_capability_records_no_repair(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    adapter = FakeAdapter({"single_work_lane": "enforced"}, claim_payload={"state": "missing"})
    try:
        result = harness.run_managed(ROOT, managed_request(run_id=run_id), adapter)
        repair = json.loads((run_dir / "run.json").read_text())["attempts"][0]["evidence"]["claim_repair"][0]

        assert result["outcome"]["reason"] == "claim_invalid"
        assert adapter.calls.count("repair_claim") == 0
        assert repair["admission"] == {
            "admitted": False,
            "reason": "required_host_capability_unavailable",
        }
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)

def test_readonly_managed_run_blocks_mutation_that_passes_diff_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class ReadOnlyAdapter(FakeAdapter):
        def __init__(self) -> None:
            super().__init__(
                {"single_work_lane": "enforced"},
                claim_payload={"kind": "claimed_result", "summary": "done", "findings": ["ok"]},
                host_api=6,
                identity={"provider_id": "codex_app_server", "contract_version": 6},
            )

        def preflight_evidence(self):
            return copy.deepcopy(API6_BINDING)

        def verify_tool_bindings(self, lane, packet, workspace):
            bindings = super().verify_tool_bindings(lane, packet, workspace)
            for binding in bindings:
                binding["access"] = "read_only"
            return bindings

        def collect_lane_evidence(self, handle, lane, packet, workspace):
            evidence = super().collect_lane_evidence(handle, lane, packet, workspace)
            evidence["sandbox"] = "read-only"
            return evidence

    try:
        result = harness.run_managed(
            ROOT,
            managed_request(
                version=5,
                run_id=run_id,
                task_type="research",
                execution_mode="single_work_lane",
                allowed_paths=["docs/**"],
                planned_write_paths=[],
            ),
            ReadOnlyAdapter(),
            collect_changes=lambda root, base_commit: [{"path": "docs/mutation.md", "kind": "modified"}],
        )

        assert result["outcome"]["reason"] == "verification_failed"
        evidence = json.loads((run_dir / "run.json").read_text())["attempts"][0]["evidence"]
        assert evidence["checks"] == []
        assert evidence["postconditions"] == [{"name": "workspace_unchanged", "status": "failed"}]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_managed_continuation_migrates_planned_lane_record(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    request = managed_request(run_id=run_id)
    packet = harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")
    run = harness._new_run(request, run_id)
    harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "preflight")
    attempt = harness._append_attempt(run, packet)
    attempt["lanes"] = [node for node in attempt.pop("nodes") if node["lane_id"] != "check"]
    attempt.pop("node_observations")
    try:
        harness._write_run(ROOT, run)

        result = harness.run_managed(
            ROOT,
            None,
            FakeAdapter({"single_work_lane": "enforced"}),
            run_id=run_id,
            run_check=lambda command: (0, "ok", ""),
            collect_changes=lambda root, base_commit: [],
        )

        assert result["outcome"]["reason"] == "verification_passed"
        resumed = json.loads((run_dir / "run.json").read_text())["attempts"][0]
        assert [node["lane_id"] for node in resumed["nodes"]] == ["primary", "integrate", "validate", "check"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_timeout_escalation_uses_packet_named_budget_profile(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class TimedOutTurn(RuntimeError):
        timeout_observation = {
            "version": 1,
            "lane_id": "primary",
            "session_id": "thread-1",
            "turn_id": "turn-1",
            "turn_timeout_seconds": 300,
            "elapsed_seconds": 300.0,
            "terminal_status": "interrupted",
            "interrupt_status": "terminal_confirmed",
            "item_states": [],
            "command_states": [],
            "final_claim_state": {"state": "missing"},
        }

    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter({"single_work_lane": "enforced"}, dispatch_error=TimedOutTurn("turn timed out")),
        )

        assert result["outcome"] == {
            "reason": "dispatch_timeout",
            "allowed_decisions": ["escalate", "block"],
            "evidence_refs": ["friction_event_ids", "evidence.failure", "evidence.terminal_observation"],
            "detail": "turn timed out",
        }
        with pytest.raises(harness.HarnessError, match="decision `retry` is not allowed"):
            harness.apply_controller_decision(ROOT, run_id, {"kind": "retry"})

        resumed = harness.apply_controller_decision(ROOT, run_id, {"kind": "escalate"})
        run = json.loads((run_dir / "run.json").read_text())

        assert resumed["state"] == "planned"
        assert run["attempts"][0]["packet"]["execution_budget"]["profile"] == "default"
        assert run["attempts"][1]["packet"]["execution_budget"]["profile"] == "extended"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_api5_timeout_escalation_preserves_provider_runtime_binding(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class TimedOutTurn(RuntimeError):
        timeout_observation = {
            "version": 1,
            "lane_id": "primary",
            "session_id": "thread-1",
            "turn_id": "turn-1",
            "turn_timeout_seconds": 300,
            "elapsed_seconds": 300.0,
            "terminal_status": "interrupted",
            "interrupt_status": "terminal_confirmed",
            "item_states": [],
            "command_states": [],
            "final_claim_state": {"state": "missing"},
        }

    class BoundTimeoutAdapter(FakeAdapter):
        def preflight_evidence(self):
            return copy.deepcopy(API6_BINDING)

    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id, version=5, execution_mode="single_work_lane"),
            BoundTimeoutAdapter(
                {"single_work_lane": "enforced"},
                dispatch_error=TimedOutTurn("turn timed out"),
                host_api=6,
                identity={"provider_id": "codex_app_server", "contract_version": 6},
            ),
        )

        assert result["outcome"]["reason"] == "dispatch_timeout"
        harness.apply_controller_decision(ROOT, run_id, {"kind": "escalate"})
        attempts = json.loads((run_dir / "run.json").read_text())["attempts"]

        assert [attempt["packet"]["version"] for attempt in attempts] == [harness.CURRENT_PACKET_API] * 2
        assert attempts[1]["packet"]["operating_profile"]["resolved"] == "local_change_extended"
        assert attempts[1]["packet"]["provider_runtime_binding"] == attempts[0]["packet"]["provider_runtime_binding"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_writer_completion_missing_blocks_without_timeout_escalation(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class MissingWriterCompletion(RuntimeError):
        timeout_observation = {
            "version": 1,
            "lane_id": "primary",
            "session_id": "thread-1",
            "turn_id": "turn-1",
            "turn_timeout_seconds": 300,
            "elapsed_seconds": 300.0,
            "terminal_status": "interrupted",
            "interrupt_status": "terminal_confirmed",
            "item_states": [{"item_id": "command-1", "type": "commandExecution", "state": "completed"}],
            "command_states": [{
                "item_id": "command-1",
                "state": "completed",
                "command_hash": "a" * 64,
                "command_length": 12,
                "response_hash": "b" * 64,
                "response_length": 7,
                "exit_code": 1,
            }],
            "final_claim_state": {"state": "missing"},
        }
        evidence_artifacts = [{
            "kind": "sanitized_command_trace",
            "content": {
                "version": 1,
                "commands": [{
                    "item_id": "command-1",
                    "command": "pytest -q",
                    "output": "failed",
                    "exit_code": 1,
                }],
            },
        }]

    try:
        adapter = FakeAdapter({"single_work_lane": "enforced"}, dispatch_error=MissingWriterCompletion("writer turn incomplete"))
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            adapter,
        )

        assert result["outcome"] == {
            "reason": "writer_completion_missing",
            "allowed_decisions": ["block"],
            "evidence_refs": ["friction_event_ids", "evidence.failure", "evidence.terminal_observation", "evidence.artifacts"],
            "detail": "writer turn incomplete",
        }
        run = json.loads((run_dir / "run.json").read_text())
        assert run["attempts"][0]["evidence"]["terminal_observation"]["command_states"][-1]["exit_code"] == 1
        assert run["attempts"][0]["evidence"]["artifacts"][0]["kind"] == "sanitized_command_trace"
        assert adapter.calls.count("repair_claim") == 0
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_writer_completion_missing_records_terminal_evidence_when_trace_is_oversized(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class MissingWriterCompletion(RuntimeError):
        timeout_observation = {
            "version": 1,
            "lane_id": "primary",
            "session_id": "thread-1",
            "turn_id": "turn-1",
            "turn_timeout_seconds": 300,
            "elapsed_seconds": 300.0,
            "terminal_status": "interrupted",
            "interrupt_status": "terminal_confirmed",
            "item_states": [{"item_id": "command-1", "type": "commandExecution", "state": "completed"}],
            "command_states": [{
                "item_id": "command-1",
                "state": "completed",
                "command_hash": "a" * 64,
                "command_length": 12,
                "response_hash": "b" * 64,
                "response_length": 4090,
                "exit_code": 1,
            }],
            "final_claim_state": {"state": "missing"},
        }
        evidence_artifacts = [{
            "kind": "sanitized_command_trace",
            "content": {
                "version": 1,
                "commands": [{
                    "item_id": "command-1",
                    "command": "pytest -q",
                    "output": "x" * 4090,
                    "exit_code": 1,
                }],
            },
        }]

    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter({"single_work_lane": "enforced"}, dispatch_error=MissingWriterCompletion("writer turn incomplete")),
        )

        assert result["outcome"]["reason"] == "writer_completion_missing"
        run = json.loads((run_dir / "run.json").read_text())
        assert run["state"] == "awaiting_decision"
        assert run["attempts"][0]["evidence"]["terminal_observation"]["kind"] == "timeout"
        assert run["attempts"][0]["evidence"]["artifact_rejections"] == [{
            "reason": "sanitized command trace exceeds artifact_max_bytes",
        }]
        assert "artifacts" not in run["attempts"][0]["evidence"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_provider_failure_records_terminal_observation_without_timeout_escalation(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class FailedTurn(RuntimeError):
        terminal_observation = {
            "version": 1,
            "kind": "provider_failure",
            "source": "provider_terminal",
            "lane_id": "primary",
            "session_id": "thread-1",
            "turn_id": "turn-1",
            "turn_timeout_seconds": None,
            "elapsed_seconds": 3.0,
            "terminal_status": "failed",
            "interrupt_status": None,
            "item_states": [],
            "command_states": [],
            "final_claim_state": {"state": "missing"},
            "error": {
                "field_names": ["message"],
                "code_hash": None,
                "code_length": None,
                "message_hash": "a" * 64,
                "message_length": 15,
            },
        }

    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter({"single_work_lane": "enforced"}, dispatch_error=FailedTurn("provider failed")),
        )
        run = json.loads((run_dir / "run.json").read_text())

        assert result["outcome"] == {
            "reason": "dispatch_failed",
            "allowed_decisions": ["retry", "escalate", "block"],
            "evidence_refs": ["friction_event_ids", "evidence.failure", "evidence.terminal_observation"],
            "detail": "provider failed",
        }
        assert run["attempts"][0]["evidence"]["terminal_observation"]["kind"] == "provider_failure"
        assert "timeout" not in run["attempts"][0]["evidence"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


@pytest.mark.parametrize(("kind", "source", "session_id", "turn_id", "error"), [
    ("approval_required", "approval_request", "thread-1", "turn-1", None),
    ("protocol_failure", "transport_exception", None, None, {
        "field_names": ["message"],
        "code_hash": None,
        "code_length": None,
        "message_hash": "b" * 64,
        "message_length": 14,
    }),
])
def test_non_timeout_terminal_observation_stays_dispatch_failed(
    tmp_path: Path,
    kind: str,
    source: str,
    session_id: str | None,
    turn_id: str | None,
    error: dict[str, object] | None,
) -> None:
    harness = load_module()
    run_id = f"{tmp_path.name}-{kind}"
    run_dir = ROOT / ".harness" / "runs" / run_id

    class AbnormalTurn(RuntimeError):
        terminal_observation = {
            "version": 1,
            "kind": kind,
            "source": source,
            "lane_id": "primary",
            "session_id": session_id,
            "turn_id": turn_id,
            "turn_timeout_seconds": None,
            "elapsed_seconds": 1.0,
            "terminal_status": None,
            "interrupt_status": None,
            "item_states": [],
            "command_states": [],
            "final_claim_state": {"state": "missing"},
            "error": error,
        }

    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id),
            FakeAdapter({"single_work_lane": "enforced"}, dispatch_error=AbnormalTurn(kind)),
        )
        run = json.loads((run_dir / "run.json").read_text())

        assert result["outcome"]["reason"] == "dispatch_failed"
        assert result["outcome"]["allowed_decisions"] == ["retry", "escalate", "block"]
        assert run["attempts"][0]["evidence"]["terminal_observation"]["kind"] == kind
        assert "timeout" not in run["attempts"][0]["evidence"]
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_admit_managed_operation_returns_core_identity_before_packet_work() -> None:
    harness = load_module()

    identity = harness.admit_managed_operation(
        ROOT,
        FakeAdapter({"single_work_lane": "enforced"}, host_api=6),
    )

    assert identity["request_api"] == 5
    assert identity["packet_api"] == 7
    assert identity["host_api"] == 6
    assert isinstance(identity["package_release"], str)


def test_run_managed_resumes_planned_api4_packet_with_host3_only(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    request = managed_request(run_id=run_id)
    try:
        packet = harness.resolve_managed_packet(ROOT, request, attempt_id="attempt-1")
        packet.pop("provider_runtime_binding")
        packet.update({
            "version": 4,
            "runtime_provider": {"provider_id": "codex_app_server", "contract_version": 3},
            "core_identity": {"package_release": "fixture", "request_api": 4, "packet_api": 4, "host_api": 3},
            "invocation_id": "attempt-1:primary",
            "parent_invocation_id": None,
        })
        run = harness._new_run(request, run_id)
        harness._transition(run, harness._load_policy(ROOT)["states"], "planned", "fixture")
        harness._append_attempt(run, packet)
        harness._write_run(ROOT, run)

        result = harness.run_managed(
            ROOT,
            None,
            FakeAdapter(
                {"single_work_lane": "unavailable"},
                host_api=3,
                identity={"provider_id": "codex_app_server", "contract_version": 3},
            ),
            run_id=run_id,
        )

        assert result["outcome"]["reason"] == "execution_mode_unavailable"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_failed_integration_skips_validator_dispatch(tmp_path: Path) -> None:
    harness = load_module()
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id

    class IntegrationFailureAdapter(FakeAdapter):
        def __init__(self):
            super().__init__({"sequential_work_lanes": "enforced"})
            self.dispatched_lanes = []

        def dispatch_lane(self, lane, packet, workspace, cancellation_token):
            self.dispatched_lanes.append(lane["lane_id"])
            return super().dispatch_lane(lane, packet, workspace, cancellation_token)

        def materialize_final_state(self, lane, packet, workspaces):
            self.calls.append("materialize_final_state")
            raise RuntimeError("integration conflict")

    lanes = [
        {"lane_id": "first", "role": "implement", "allowed_paths": ["scripts/**"], "dependencies": [], "workspace_mode": "isolated", "write_capable": True},
        {"lane_id": "second", "role": "implement", "allowed_paths": ["tests/**"], "dependencies": ["first"], "workspace_mode": "isolated", "write_capable": True},
    ]
    adapter = IntegrationFailureAdapter()
    try:
        result = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id, execution_mode="sequential_work_lanes", lanes=lanes),
            adapter,
        )

        assert result["outcome"]["reason"] == "dispatch_failed"
        assert adapter.dispatched_lanes == ["first", "second"]
        assert "run_checks" not in adapter.calls
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_approval_resume_creates_successor_attempt(tmp_path: Path) -> None:
    harness = load_module()
    now = datetime.now(UTC)
    run_id = tmp_path.name
    run_dir = ROOT / ".harness" / "runs" / run_id
    request = {
        "allowed_paths": ["repo_config/**"],
        "planned_write_paths": ["repo_config/harness.yaml"],
    }
    try:
        first = harness.run_managed(
            ROOT,
            managed_request(run_id=run_id, **request),
            FakeAdapter({"single_work_lane": "enforced"}),
            now=now,
        )
        assert first["outcome"]["reason"] == "approval_required"

        waiting = harness.apply_controller_decision(ROOT, run_id, {"kind": "request_approval"})
        assert waiting["state"] == "awaiting_decision"
        resumed = harness.apply_controller_decision(
            ROOT,
            run_id,
            {"kind": "retry", "successor": {"approvals": [{
                "gate": "protected_policy",
                "approver": "controller",
                "paths": ["repo_config/**"],
                "attempt_id": "attempt-2",
                "issued_at": now.isoformat(),
            }]}},
        )
        assert resumed["state"] == "planned"

        run = json.loads((run_dir / "run.json").read_text())
        assert [decision["kind"] for decision in run["attempts"][0]["decision_history"]] == ["request_approval", "retry"]
        assert run["attempts"][1]["packet"]["approvals"][0]["attempt_id"] == "attempt-2"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_friction_report_uses_distinct_runs_and_accepted_resolution(tmp_path: Path) -> None:
    harness = load_module()
    root = tmp_path / "harness"
    (root / "repo_config").mkdir(parents=True)
    shutil.copy2(ROOT / "repo_config" / "harness.yaml", root / "repo_config" / "harness.yaml")
    packet = {
        "task_type": "local_change",
        "runtime_provider": {"provider_id": "codex_app_server", "contract_version": 2},
        "orchestration": {"name": "single_work_lane"},
    }
    now = datetime(2026, 8, 6, tzinfo=UTC)

    first = harness.record_friction_event(
        root,
        run_id="run-1",
        attempt_id="attempt-1",
        packet=packet,
        lane={"kind": "work"},
        source="host",
        phase="dispatch",
        code="tool_unavailable",
        evidence_ref="attempt.execution_evidence[0]",
        occurred_at=now,
    )
    harness.record_friction_event(
        root,
        run_id="run-1",
        attempt_id="attempt-1",
        packet=packet,
        lane={"kind": "work"},
        source="host",
        phase="dispatch",
        code="tool_unavailable",
        evidence_ref="attempt.execution_evidence[1]",
        occurred_at=now,
    )
    harness.record_friction_event(
        root,
        run_id="run-2",
        attempt_id="attempt-1",
        packet=packet,
        lane={"kind": "work"},
        source="host",
        phase="dispatch",
        code="tool_unavailable",
        evidence_ref="attempt.execution_evidence[0]",
        occurred_at=now,
    )
    assert harness.friction_report(root, now=now)["candidates"] == []
    for run_id in ("run-3",):
        harness.record_friction_event(
            root,
            run_id=run_id,
            attempt_id="attempt-1",
            packet=packet,
            lane={"kind": "work"},
            source="host",
            phase="dispatch",
            code="tool_unavailable",
            evidence_ref="attempt.execution_evidence[0]",
            occurred_at=now,
        )

    report = harness.friction_report(root, now=now)

    assert [candidate["fingerprint"] for candidate in report["candidates"]] == [first["fingerprint"]]
    assert report["candidates"][0]["distinct_run_count"] == 3
    assert report["candidates"][0]["event_count"] == 4
    resolution_run = root / ".harness" / "runs" / "improvement"
    resolution_run.mkdir(parents=True)
    (resolution_run / "run.json").write_text(json.dumps({
        "version": 1,
        "run_id": "improvement",
        "request": {"task_type": "local_change"},
        "state": "accepted",
        "attempts": [{}],
    }), encoding="utf-8")
    with pytest.raises(harness.HarnessError, match="accepted harness_improvement"):
        harness.resolve_friction(root, "improvement", first["fingerprint"], "keep", now=now)
    (resolution_run / "run.json").write_text(json.dumps({
        "version": 1,
        "run_id": "improvement",
        "request": {"task_type": "harness_improvement"},
        "state": "planned",
        "attempts": [{}],
    }), encoding="utf-8")
    with pytest.raises(harness.HarnessError, match="accepted harness_improvement"):
        harness.resolve_friction(root, "improvement", first["fingerprint"], "keep", now=now)
    (resolution_run / "run.json").write_text(json.dumps({
        "version": 1,
        "run_id": "improvement",
        "request": {"task_type": "harness_improvement"},
        "state": "accepted",
        "attempts": [{}],
    }), encoding="utf-8")

    resolution = harness.resolve_friction(
        root,
        "improvement",
        first["fingerprint"],
        "keep",
        now=now,
    )

    assert resolution["kind"] == "resolution"
    assert harness.friction_report(root, now=now)["candidates"] == []


def test_friction_report_recommends_read_only_diagnosis_for_writer_completion_missing(tmp_path: Path) -> None:
    harness = load_module()
    root = tmp_path / "harness"
    (root / "repo_config").mkdir(parents=True)
    shutil.copy2(ROOT / "repo_config" / "harness.yaml", root / "repo_config" / "harness.yaml")
    packet = {
        "task_type": "local_change",
        "runtime_provider": {"provider_id": "codex_app_server", "contract_version": 5},
        "orchestration": {"name": "single_work_lane"},
    }
    now = datetime(2026, 8, 7, tzinfo=UTC)
    for run_id in ("run-1", "run-2", "run-3"):
        run_dir = root / ".harness" / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps({
            "version": 1,
                "run_id": run_id,
                "state": "blocked",
                "attempts": [{
                    "attempt_id": "attempt-1",
                    "packet": {
                        "base_commit": "base",
                        "lanes": [{"lane_id": "primary"}],
                        "execution_budget": {"turn_timeout_seconds": 300},
                        "retained_artifacts": [{"kind": "sanitized_command_trace", "max_bytes": 4096}],
                    },
                    "evidence": {
                        "terminal_observation": {
                            "version": 1,
                            "kind": "timeout",
                            "source": "host_timeout_interrupt",
                            "lane_id": "primary",
                            "session_id": "thread-1",
                            "turn_id": "turn-1",
                            "turn_timeout_seconds": 300,
                            "elapsed_seconds": 300.0,
                            "terminal_status": "interrupted",
                            "interrupt_status": "terminal_confirmed",
                            "item_states": [],
                            "command_states": [],
                            "final_claim_state": {"state": "missing"},
                            "error": None,
                        },
                    "artifacts": [{
                        "kind": "sanitized_command_trace",
                        "content": {"version": 1, "commands": []},
                    }],
                },
            }],
        }), encoding="utf-8")
        harness.record_friction_event(
            root,
            run_id=run_id,
            attempt_id="attempt-1",
            packet=packet,
            lane={"kind": "work"},
            source="host",
            phase="dispatch",
            code="writer_completion_missing",
            evidence_ref="evidence.terminal_observation",
            occurred_at=now,
        )

    report = harness.friction_report(root, now=now)

    follow_up = report["candidates"][0]["follow_up"]
    assert follow_up["task_type"] == "harness_diagnosis"
    assert follow_up["execution_mode"] == "single_work_lane"
    assert follow_up["workspace_write_access"] == "read_only"
    assert follow_up["artifact_handoff"] == {"profile": "friction_terminal_diagnosis"}
    assert "readonly_artifacts" not in follow_up


def test_friction_report_blocks_diagnosis_without_required_artifacts(tmp_path: Path) -> None:
    harness = load_module()
    root = tmp_path / "harness"
    (root / "repo_config").mkdir(parents=True)
    shutil.copy2(ROOT / "repo_config" / "harness.yaml", root / "repo_config" / "harness.yaml")
    packet = {
        "task_type": "local_change",
        "runtime_provider": {"provider_id": "codex_app_server", "contract_version": 5},
        "orchestration": {"name": "single_work_lane"},
    }
    now = datetime(2026, 8, 7, tzinfo=UTC)
    for run_id in ("run-1", "run-2", "run-3"):
        harness.record_friction_event(
            root,
            run_id=run_id,
            attempt_id="attempt-1",
            packet=packet,
            lane={"kind": "work"},
            source="host",
            phase="dispatch",
            code="writer_completion_missing",
            evidence_ref="evidence.terminal_observation",
            occurred_at=now,
        )

    candidate = harness.friction_report(root, now=now)["candidates"][0]

    assert candidate["follow_up_blocked"] == "missing_required_readonly_artifacts"
    assert "follow_up" not in candidate


def test_friction_report_cli_is_read_only(tmp_path: Path) -> None:
    root = tmp_path / "harness"
    (root / "repo_config").mkdir(parents=True)
    shutil.copy2(ROOT / "repo_config" / "harness.yaml", root / "repo_config" / "harness.yaml")

    result = subprocess.run(
        [*MANAGED_COMMAND, "--repo-root", str(root), "friction-report"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["candidates"] == []
    assert not (root / ".harness").exists()


def test_friction_report_rejects_malformed_event(tmp_path: Path) -> None:
    harness = load_module()
    root = tmp_path / "harness"
    (root / "repo_config").mkdir(parents=True)
    shutil.copy2(ROOT / "repo_config" / "harness.yaml", root / "repo_config" / "harness.yaml")
    events_path = root / ".harness" / "friction-events.jsonl"
    events_path.parent.mkdir()
    events_path.write_text(json.dumps({
        "version": 1,
        "kind": "observed",
        "event_id": "friction-malformed",
        "run_id": "run-1",
        "attempt_id": "attempt-1",
        "route": "local_change",
        "provider": "codex_app_server:1",
        "mode": "single_work_lane",
        "lane_kind": "work",
        "phase": "dispatch",
        "source": [],
        "code": "tool_unavailable",
        "evidence_ref": "evidence",
        "fingerprint": "fingerprint",
        "occurred_at": "2026-08-06T00:00:00+00:00",
    }) + "\n", encoding="utf-8")

    with pytest.raises(harness.HarnessError, match="invalid friction event at line 1"):
        harness.friction_report(root)
