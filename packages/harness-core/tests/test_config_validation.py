"""
@meta
name: test_validate_harness_config
type: test
domain: harness
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from harness_core import config_validation


def write_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_harness_root(root: Path) -> None:
    for name in ("low", "normal", "high"):
        write_text(root, f"agents/{name}.toml", f'name = "{name}"\n')
    write_text(
        root,
        "agents/roles.yaml",
        yaml.safe_dump(
            {
                "version": 3,
                "claim_fields": {
                    "summary": "nonempty_string",
                    "changed_files": "string_list",
                    "findings": "string_list",
                    "verdict": "nonempty_string",
                    "decision": "nonempty_string",
                    "frictions": "friction_list",
                },
                "roles": {
                    "implement": {
                        "accepts": ["low", "normal", "high"],
                        "result_kind": "claimed_result",
                        "required_fields": ["changed_files"],
                    },
                    "validate": {
                        "accepts": ["low", "normal", "high"],
                        "result_kind": "claimed_result",
                        "required_fields": ["summary", "findings", "verdict"],
                    },
                    "investigate": {
                        "accepts": ["low", "normal", "high"],
                        "result_kind": "claimed_result",
                        "required_fields": ["summary", "findings"],
                    },
                },
            },
            sort_keys=False,
        ),
    )
    write_text(root, "docs/operating_system/rules/command-execution-rule.md", "# Command Execution\n")
    write_text(root, ".agents/skills/skill-code-standards/SKILL.md", "---\nname: skill-code-standards\ndescription: Use when standards apply.\n---\n")
    write_text(
        root,
        "repo_config/harness.yaml",
        yaml.safe_dump(
            {
                "version": 9,
                "harness_core": {"request_api": 5},
                "context_limits": {
                    "objective_max_bytes": 1024,
                    "fact_max_bytes": 4096,
                    "max_facts": 8,
                    "max_artifacts": 8,
                    "artifact_max_bytes": 4096,
                    "outcome_summary_max_bytes": 2048,
                },
                "evidence_artifacts": {
                    "catalog": {
                        "terminal_observation": {
                            "schema_id": "host_terminal_observation/v2",
                            "producer": "host",
                            "retention": "terminal",
                            "byte_limit": 4096,
                        },
                        "sanitized_command_trace": {
                            "schema_id": "sanitized_command_trace/v1",
                            "producer": "writer",
                            "retention": "writer_retained",
                            "byte_limit": 4096,
                        },
                    },
                    "profiles": {
                        "direct_terminal_diagnosis": {
                            "lineage_mode": "direct",
                            "allowed_kinds": ["terminal_observation", "sanitized_command_trace"],
                            "required_kinds": ["terminal_observation"],
                            "kind_priority": ["terminal_observation", "sanitized_command_trace"],
                            "base_compatibility": "exact_packet_base",
                            "count_limit": 2,
                            "total_byte_limit": 8192,
                        },
                        "friction_terminal_diagnosis": {
                            "lineage_mode": "source_set",
                            "allowed_kinds": ["terminal_observation", "sanitized_command_trace"],
                            "required_kinds": ["terminal_observation"],
                            "kind_priority": ["terminal_observation", "sanitized_command_trace"],
                            "base_compatibility": "same_repository",
                            "count_limit": 6,
                            "total_byte_limit": 24576,
                        },
                    },
                },
                "delegation_profiles": {
                    "disabled": {
                        "max_depth": 0,
                        "max_children": 0,
                        "max_concurrent_children": 0,
                        "per_child_timeout_seconds": 0,
                        "total_child_timeout_seconds": 0,
                        "allowed_roles": [],
                        "capability_ceiling": [],
                        "workspace_write_access": "read_only",
                        "verification": "none",
                    },
                },
                "defaults": {
                    "source_workspace": "current_repo",
                    "runtime_provider": "codex_app_server",
                    "retry_policy": "bounded",
                    "execution_budget_profile": "default",
                    "approval_gates": [],
                },
                "authorities": {
                    "workspace_write": {
                        "capabilities": ["repo.read", "repo.write", "code.search"],
                        "workspace_write_access": "workspace_write",
                    },
                    "read_only": {
                        "capabilities": ["repo.read", "code.search"],
                        "workspace_write_access": "read_only",
                    },
                },
                "toolsets": {"code": ["shell"]},
                "verification_profiles": {
                    "write": {"postconditions": [], "checks": ["diff"]},
                    "read_only": {"postconditions": ["workspace_unchanged"], "checks": []},
                },
                "retry_policies": {
                    "bounded": {
                        "max_attempts": 2,
                        "retryable_reasons": ["check_failed", "claim_invalid"],
                        "exhaustion": "block",
                        "approval_resume": "successor_attempt",
                        "approval_ttl_seconds": 3600,
                    },
                },
                "execution_budgets": {
                    "max_turn_timeout_seconds": 900,
                    "finalization_reserve_seconds": 60,
                    "lease_duration_model": {
                        "id": "codex_app_server.v1",
                        "max_turns_per_lane": 2,
                        "per_turn_overhead_seconds": 15,
                        "stop_proof_seconds": 30,
                        "check_timeout_seconds": 60,
                        "core_verification_seconds": 45,
                        "cleanup_grace_seconds": 30,
                    },
                    "profiles": {"default": {"turn_timeout_seconds": 300, "timeout_decisions": ["block"]}},
                },
                "claim_repair": {
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
                },
                "terminalization": {
                    "auto_finalize_single_terminal_outcome": True,
                    "pending_outcome_ttl_seconds": 3600,
                    "allowed_controller_roles": ["controller_approver"],
                    "max_authorization_age_seconds": 900,
                    "max_authorization_lifetime_seconds": 900,
                    "max_clock_skew_seconds": 60,
                    "max_authorization_bytes": 8192,
                    "allow_same_issuer_evidence_and_authorization": False,
                },
                "checks": {"diff": {"command": ["git", "diff", "--check"]}},
                "tools": {
                    "shell": {
                        "optional": False,
                        "host_kind": "app_server_shell",
                        "writer_access": "workspace_write",
                        "validator_access": "read_only",
                        "root_probe": "shell_root_probe",
                    },
                },
                "runtime_providers": {
                    "codex_app_server": {
                        "contract_version": 6,
                        "terminal_observation_capability": "host_terminal_observation_v2",
                        "execution_lease_duration_model_id": "codex_app_server.v1",
                    },
                },
                "friction_policy": {
                    "event_version": 1,
                    "minimum_distinct_runs": 3,
                    "window_days": 14,
                    "follow_up_routes": {
                        "writer_completion_missing": "harness_diagnosis",
                        "claim_repair_failed": "harness_diagnosis",
                    },
                },
                "approval_gates": {"protected": {"paths": ["repo_config/harness.yaml"]}},
                "orchestration": {
                    "single_work_lane": {
                        "aliases": ["single_agent"],
                        "work_scheduling": "single",
                        "max_parallel_writers": 1,
                        "workspace_mode": "isolated",
                        "validator_role": "validate",
                        "rules": [],
                    },
                },
                "routes": {
                    "local_change": {
                        "template": "normal",
                        "role": "implement",
                        "rules": ["command-execution-rule"],
                        "skills": ["skill-code-standards"],
                        "authority": "workspace_write",
                        "toolset": "code",
                        "verification_profile": "write",
                        "delegation_profile": "disabled",
                        "approval_gates": ["protected"],
                        "execution_modes": ["single_work_lane"],
                    },
                    "harness_diagnosis": {
                        "template": "normal",
                        "role": "investigate",
                        "rules": ["command-execution-rule"],
                        "skills": ["skill-code-standards"],
                        "authority": "read_only",
                        "toolset": "code",
                        "verification_profile": "read_only",
                        "delegation_profile": "disabled",
                        "execution_modes": ["single_work_lane"],
                    },
                },
            },
            sort_keys=False,
        ),
    )


def load_policy(root: Path) -> tuple[Path, dict[str, object]]:
    path = root / "repo_config/harness.yaml"
    return path, yaml.safe_load(path.read_text(encoding="utf-8"))


def write_policy(path: Path, policy: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")


def composed_policy(root: Path) -> tuple[Path, dict[str, object]]:
    write_harness_root(root)
    for skill_name in ("skill-executing-plans", "skill-test-driven-development", "skill-backend-verification"):
        skill_dir = root / ".agents" / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    path, policy = load_policy(root)
    policy["execution_budgets"]["profiles"]["extended"] = {
        "turn_timeout_seconds": 600,
        "timeout_decisions": ["block"],
    }
    policy["skill_sets"] = {
        "local_change_base": {
            "skills": ["skill-code-standards", "skill-executing-plans", "skill-test-driven-development"],
            "selection_guidance": "Use for every planned code change.",
        },
        "backend_verification": {
            "skills": ["skill-backend-verification"],
            "selection_guidance": "Use for material backend behavior.",
        },
    }
    policy["operating_profiles"] = {
        "local_change_standard": {
            "template": "normal",
            "authority": "workspace_write",
            "toolset": "code",
            "verification_profile": "write",
            "runtime_provider": "codex_app_server",
            "execution_budget_profile": "default",
        },
        "local_change_extended": {
            "extends": "local_change_standard",
            "execution_budget_profile": "extended",
        },
    }
    policy["routes"]["local_change"] = {
        "role": "implement",
        "rules": ["command-execution-rule"],
        "required_skill_sets": ["local_change_base"],
        "allowed_skill_sets": ["backend_verification"],
        "default_operating_profile": "local_change_standard",
        "allowed_operating_profiles": ["local_change_standard", "local_change_extended"],
        "escalation_transitions": [{"from": "local_change_standard", "on": "dispatch_timeout", "to": "local_change_extended"}],
        "delegation_profile": "disabled",
        "approval_gates": ["protected"],
        "execution_modes": ["single_work_lane"],
    }
    write_policy(path, policy)
    return path, policy


def test_v6_policy_catalog_profiles_and_claim_repair_validate(tmp_path: Path) -> None:
    write_harness_root(tmp_path)

    assert config_validation.validate(tmp_path) == []


def test_v6_rejects_claim_repair_without_typed_role_contract(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    roles_path = tmp_path / "agents" / "roles.yaml"
    roles = yaml.safe_load(roles_path.read_text(encoding="utf-8"))
    del roles["claim_fields"]["findings"]
    roles_path.write_text(yaml.safe_dump(roles, sort_keys=False), encoding="utf-8")

    assert config_validation.validate(tmp_path) == [
        "role `validate` references unknown claim field `findings`",
        "role `investigate` references unknown claim field `findings`",
    ]


def test_v6_rejects_constraint_on_non_string_claim_field(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    roles_path = tmp_path / "agents" / "roles.yaml"
    roles = yaml.safe_load(roles_path.read_text(encoding="utf-8"))
    roles["roles"]["validate"]["field_constraints"] = {"findings": ["pass"]}
    roles_path.write_text(yaml.safe_dump(roles, sort_keys=False), encoding="utf-8")

    assert config_validation.validate(tmp_path) == [
        "role `validate` field_constraints must target required string fields"
    ]


def test_v6_rejects_invalid_claim_repair_contract(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["claim_repair"]["max_repairs_per_lane"] = 2
    policy["claim_repair"]["admissible_subcodes"][-1] = "unknown_claim_failure"
    write_policy(path, policy)

    assert config_validation.validate(tmp_path) == [
        "claim_repair max_repairs_per_lane must be 1",
        "claim_repair admissible_subcodes are invalid",
    ]


def test_every_budget_profile_must_exceed_finalization_reserve(tmp_path: Path) -> None:
    path, policy = composed_policy(tmp_path)
    policy["execution_budgets"]["profiles"]["extended"]["turn_timeout_seconds"] = 60
    write_policy(path, policy)

    assert config_validation.validate(tmp_path) == [
        "execution budget profile `extended` must exceed finalization_reserve_seconds"
    ]


def test_execution_lease_duration_model_requires_finite_values(tmp_path: Path) -> None:
    path, policy = composed_policy(tmp_path)
    policy["execution_budgets"]["lease_duration_model"]["cleanup_grace_seconds"] = 0
    write_policy(path, policy)

    assert config_validation.validate(tmp_path) == [
        "execution_budgets lease_duration_model has invalid cleanup_grace_seconds"
    ]


def test_composed_route_uses_shared_profile_resolver(tmp_path: Path) -> None:
    _, policy = composed_policy(tmp_path)

    assert config_validation.validate(tmp_path) == []
    assert config_validation.resolve_operating_profile(policy, "local_change", "local_change_extended") == {
        "template": "normal",
        "authority": "workspace_write",
        "toolset": "code",
        "verification_profile": "write",
        "runtime_provider": "codex_app_server",
        "execution_budget_profile": "extended",
    }


def test_composed_route_rejects_cross_provider_profiles(tmp_path: Path) -> None:
    path, policy = composed_policy(tmp_path)
    policy["runtime_providers"]["other"] = {
        "contract_version": 4,
        "terminal_observation_capability": "host_terminal_observation_v2",
        "execution_lease_duration_model_id": "codex_app_server.v1",
    }
    policy["operating_profiles"]["local_change_extended"]["runtime_provider"] = "other"
    write_policy(path, policy)

    assert "route `local_change` operating profiles must resolve default runtime provider" in config_validation.validate(tmp_path)


def test_duplicate_profile_key_fails_before_validation(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path = tmp_path / "repo_config/harness.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("authorities:\n", "authorities:\n  read_only: {}\n  read_only: {}\n"), encoding="utf-8")

    assert config_validation.validate(tmp_path) == ["invalid YAML: duplicate YAML key `read_only`"]


def test_v4_rejects_deleted_policy_fields(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["states"] = {}
    policy["routes"]["local_change"]["tools"] = ["shell"]
    write_policy(path, policy)

    errors = config_validation.validate(tmp_path)

    assert "harness policy has unknown fields: states" in errors
    assert "route `local_change` has unknown fields: tools" in errors


def test_legacy_cleanup_rejects_partial_policy(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["legacy_cleanup"] = {"enabled": True}
    write_policy(path, policy)

    assert "legacy_cleanup has invalid fields" in config_validation.validate(tmp_path)


def test_legacy_cleanup_rejects_future_packet_cap(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["legacy_cleanup"] = {
        "enabled": True,
        "historical_packet_max_api": 9,
        "allowed_cleanup_scopes": ["operator_discovered_provider_tree", "operator_attested_no_provider_process"],
        "allowed_discovery_methods": ["windows_parent_chain/v1", "windows_no_process_observation/v1"],
        "max_attestation_age_seconds": 900,
        "max_attestation_lifetime_seconds": 900,
        "max_clock_skew_seconds": 60,
        "max_total_bytes": 8192,
        "max_identifier_bytes": 128,
        "max_creation_id_bytes": 256,
        "max_reason_length": 4096,
        "max_process_identities": 32,
        "allowed_attester_roles": ["managed_cleanup_operator"],
    }
    write_policy(path, policy)

    assert "legacy_cleanup historical_packet_max_api exceeds current packet API" in config_validation.validate(tmp_path)


def test_route_requires_known_one_hop_profiles(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["routes"]["local_change"]["authority"] = "missing"
    write_policy(path, policy)

    assert "route `local_change` has unknown authority `missing`" in config_validation.validate(tmp_path)


def test_defaults_cannot_grant_approval_bypass(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["defaults"]["approval_gates"] = ["protected"]
    write_policy(path, policy)

    assert "defaults must contain only safe route defaults" in config_validation.validate(tmp_path)


def test_v1_catalog_rejects_invalid_fixed_contract(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["evidence_artifacts"]["catalog"]["terminal_observation"]["schema_id"] = "arbitrary/v1"
    write_policy(path, policy)

    assert "evidence artifact catalog `terminal_observation` has invalid current contract" in config_validation.validate(tmp_path)


def test_artifact_handoff_profiles_require_readonly_authority(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["routes"]["local_change"]["artifact_handoff_profiles"] = ["direct_terminal_diagnosis"]
    write_policy(path, policy)

    assert "route `local_change` artifact_handoff_profiles require read-only authority" in config_validation.validate(tmp_path)


def test_tool_fallback_is_rejected(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["tools"]["shell"]["fallback"] = ["other"]
    write_policy(path, policy)

    assert "tool `shell` has invalid fields" in config_validation.validate(tmp_path)


def test_unknown_template_skill_and_rule_fail(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    route = policy["routes"]["local_change"]
    route["template"] = "missing"
    route["skills"] = ["missing"]
    route["rules"] = ["missing"]
    write_policy(path, policy)

    errors = config_validation.validate(tmp_path)

    assert "unknown template `missing`" in errors
    assert "route `local_change` has unknown skills" in errors
    assert "route `local_change` has unknown rules" in errors


@pytest.mark.parametrize("value", [None, "5", 4, 1])
def test_harness_core_request_api_requires_current_integer(tmp_path: Path, value: object) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["harness_core"]["request_api"] = value
    write_policy(path, policy)

    assert config_validation.validate(tmp_path)
