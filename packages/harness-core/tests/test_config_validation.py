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
                "version": 2,
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
                "version": 4,
                "harness_core": {"request_api": 4},
                "context_limits": {
                    "objective_max_bytes": 1024,
                    "fact_max_bytes": 4096,
                    "max_facts": 8,
                    "max_artifacts": 8,
                    "artifact_max_bytes": 4096,
                    "outcome_summary_max_bytes": 2048,
                },
                "evidence_artifacts": {
                    "writer_retained_kinds": ["sanitized_command_trace"],
                    "sanitized_command_trace_max_bytes": 1024,
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
                        "retryable_reasons": ["check_failed"],
                        "exhaustion": "block",
                        "approval_resume": "successor_attempt",
                        "approval_ttl_seconds": 3600,
                    },
                },
                "execution_budgets": {
                    "max_turn_timeout_seconds": 900,
                    "profiles": {"default": {"turn_timeout_seconds": 300, "timeout_decisions": ["block"]}},
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
                "runtime_providers": {"codex_app_server": {"contract_version": 4}},
                "friction_policy": {"event_version": 1, "minimum_distinct_runs": 3, "window_days": 14},
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


def test_v4_policy_profiles_validate(tmp_path: Path) -> None:
    write_harness_root(tmp_path)

    assert config_validation.validate(tmp_path) == []


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


def test_context_and_trace_limits_must_bound_artifacts(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["evidence_artifacts"]["sanitized_command_trace_max_bytes"] = 8192
    write_policy(path, policy)

    assert "evidence_artifacts sanitized_command_trace_max_bytes exceeds artifact_max_bytes" in config_validation.validate(tmp_path)


def test_readonly_artifacts_require_readonly_authority(tmp_path: Path) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["routes"]["local_change"]["readonly_artifacts"] = {
        "allowed_kinds": ["terminal_observation"],
        "required_kinds": ["terminal_observation"],
    }
    write_policy(path, policy)

    assert "route `local_change` readonly_artifacts requires read-only authority" in config_validation.validate(tmp_path)


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


@pytest.mark.parametrize("value", [None, "4", 1])
def test_harness_core_request_api_requires_current_integer(tmp_path: Path, value: object) -> None:
    write_harness_root(tmp_path)
    path, policy = load_policy(tmp_path)
    policy["harness_core"]["request_api"] = value
    write_policy(path, policy)

    assert config_validation.validate(tmp_path)
