"""
@meta
name: validate_harness_config
type: script
domain: harness
responsibility:
  - Validate canonical harness policy references.
inputs:
  - agents/*.toml
  - agents/roles.yaml
  - repo_config/harness.yaml
outputs:
  - Exit status and configuration findings.
tags:
  - harness
  - validation
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from pathlib import Path
import tomllib
from typing import Any

import yaml

from .compatibility import admit_request_api


ROUTE_FIELDS = {
    "template",
    "role",
    "rules",
    "skills",
    "authority",
    "toolset",
    "verification_profile",
    "delegation_profile",
    "execution_modes",
}
ROUTE_OPTIONAL_FIELDS = {"approval_gates", "readonly_artifacts"}
COMPOSED_ROUTE_FIELDS = {
    "role",
    "rules",
    "required_skill_sets",
    "allowed_skill_sets",
    "default_operating_profile",
    "allowed_operating_profiles",
    "delegation_profile",
    "execution_modes",
}
COMPOSED_ROUTE_OPTIONAL_FIELDS = ROUTE_OPTIONAL_FIELDS | {"escalation_transitions"}
OPERATING_PROFILE_FIELDS = {
    "template",
    "authority",
    "toolset",
    "verification_profile",
    "runtime_provider",
    "execution_budget_profile",
}
OPERATING_PROFILE_OPTIONAL_FIELDS = {"extends"}
READONLY_ARTIFACT_KINDS = {"terminal_observation", "sanitized_command_trace"}
READONLY_ARTIFACT_POLICY_FIELDS = {"allowed_kinds", "required_kinds"}
EVIDENCE_ARTIFACT_POLICY_FIELDS = {"writer_retained_kinds"}
EVIDENCE_ARTIFACT_POLICY_OPTIONAL_FIELDS = {"sanitized_command_trace_max_bytes"}
ROLE_FIELDS = {"accepts", "result_kind", "required_fields"}
ORCHESTRATION_FIELDS = {
    "aliases",
    "work_scheduling",
    "max_parallel_writers",
    "workspace_mode",
    "validator_role",
    "rules",
}
RETRY_POLICY_FIELDS = {"max_attempts", "retryable_reasons", "exhaustion", "approval_resume", "approval_ttl_seconds"}
TOOL_FIELDS = {"optional", "host_kind", "writer_access", "validator_access", "root_probe"}
RUNTIME_PROVIDER_FIELDS = {"contract_version"}
CONTEXT_LIMIT_FIELDS = {
    "objective_max_bytes",
    "fact_max_bytes",
    "max_facts",
    "max_artifacts",
    "artifact_max_bytes",
    "outcome_summary_max_bytes",
}
DELEGATION_PROFILE_FIELDS = {
    "max_depth",
    "max_children",
    "max_concurrent_children",
    "per_child_timeout_seconds",
    "total_child_timeout_seconds",
    "allowed_roles",
    "capability_ceiling",
    "workspace_write_access",
    "verification",
}
AUTHORITY_FIELDS = {"capabilities", "workspace_write_access"}
VERIFICATION_PROFILE_FIELDS = {"postconditions", "checks"}
DEFAULT_FIELDS = {
    "source_workspace",
    "runtime_provider",
    "retry_policy",
    "execution_budget_profile",
    "approval_gates",
}
FRICTION_POLICY_FIELDS = {"event_version", "minimum_distinct_runs", "window_days"}
FRICTION_POLICY_OPTIONAL_FIELDS = {"follow_up_routes"}
EXECUTION_BUDGET_FIELDS = {"max_turn_timeout_seconds", "profiles"}
EXECUTION_BUDGET_PROFILE_FIELDS = {"turn_timeout_seconds", "timeout_decisions"}
EXECUTION_BUDGET_PROFILE_OPTIONAL_FIELDS = {"escalation_profile"}
TIMEOUT_DECISIONS = {"escalate", "block"}
POSTCONDITIONS = {"workspace_unchanged"}
CAPABILITIES = {"repo.read", "repo.write", "code.search", "docs.query", "harness.delegate"}
POLICY_FIELDS = {
    "version",
    "harness_core",
    "context_limits",
    "evidence_artifacts",
    "delegation_profiles",
    "defaults",
    "authorities",
    "toolsets",
    "verification_profiles",
    "retry_policies",
    "execution_budgets",
    "checks",
    "tools",
    "runtime_providers",
    "friction_policy",
    "approval_gates",
    "orchestration",
    "routes",
}
POLICY_OPTIONAL_FIELDS = {"skill_sets", "operating_profiles"}


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key `{key}`")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=_UniqueKeyLoader)


def list_templates(root: Path) -> set[str]:
    templates: set[str] = set()
    for path in (root / "agents").glob("*.toml"):
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
        name = payload.get("name")
        if isinstance(name, str) and name == path.stem:
            templates.add(name)
    return templates


def valid_string_list(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and item for item in value)
    )


def positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def resolve_operating_profile(policy: dict[str, Any], route_name: str, profile_name: str) -> dict[str, Any]:
    routes = policy.get("routes")
    profiles = policy.get("operating_profiles")
    if not isinstance(routes, dict) or not isinstance(profiles, dict):
        raise ValueError("operating profiles are unavailable")
    route = routes.get(route_name)
    if not isinstance(route, dict):
        raise ValueError(f"unknown route `{route_name}`")
    allowed = route.get("allowed_operating_profiles")
    if not isinstance(allowed, list) or profile_name not in allowed:
        raise ValueError(f"route `{route_name}` disallows operating profile `{profile_name}`")

    resolving: set[str] = set()

    def resolve(name: str) -> dict[str, Any]:
        if name in resolving:
            raise ValueError(f"operating profile `{name}` inheritance cycle")
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            raise ValueError(f"unknown operating profile `{name}`")
        unknown = set(profile) - OPERATING_PROFILE_FIELDS - OPERATING_PROFILE_OPTIONAL_FIELDS
        if unknown:
            raise ValueError(f"operating profile `{name}` has unknown fields")
        resolving.add(name)
        parent_name = profile.get("extends")
        parent = {} if parent_name is None else resolve(parent_name) if isinstance(parent_name, str) and parent_name else (_ for _ in ()).throw(ValueError(f"operating profile `{name}` has invalid extends"))
        resolving.remove(name)
        resolved = {**parent, **{key: value for key, value in profile.items() if key != "extends"}}
        if set(resolved) != OPERATING_PROFILE_FIELDS:
            raise ValueError(f"operating profile `{name}` is incomplete")
        return resolved

    return resolve(profile_name)


def _validate_roles(roles_payload: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    version = roles_payload.get("version") if isinstance(roles_payload, dict) else None
    if version not in {1, 2}:
        errors.append("roles version must be 1 or 2")
        return {}
    roles = roles_payload.get("roles")
    if not isinstance(roles, dict):
        errors.append("roles must be a mapping")
        return {}
    for name, role in roles.items():
        if not isinstance(name, str) or not isinstance(role, dict):
            errors.append("roles must map names to mappings")
            continue
        required_fields = ROLE_FIELDS | ({"writes"} if version == 1 else set())
        missing = required_fields - role.keys()
        if missing:
            errors.append(f"role `{name}` missing fields: {', '.join(sorted(missing))}")
        if version == 1 and not isinstance(role.get("writes"), bool):
            errors.append(f"role `{name}` writes must be a boolean")
        if version == 2 and "writes" in role:
            errors.append(f"role `{name}` must not define writes in role schema v2")
        if not valid_string_list(role.get("accepts")):
            errors.append(f"role `{name}` accepts must be a list of strings")
        if not isinstance(role.get("result_kind"), str) or not role["result_kind"]:
            errors.append(f"role `{name}` result_kind must be a non-empty string")
        if not valid_string_list(role.get("required_fields")):
            errors.append(f"role `{name}` required_fields must be a list of strings")
        constraints = role.get("field_constraints")
        if constraints is not None and (
            not isinstance(constraints, dict)
            or any(field not in role.get("required_fields", []) or not valid_string_list(values) for field, values in constraints.items())
        ):
            errors.append(f"role `{name}` field_constraints must target required string fields")
    return roles


def _validate_named_commands(policy: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    checks = policy.get("checks")
    if not isinstance(checks, dict) or not checks:
        errors.append("checks must be a non-empty mapping")
        return {}
    for name, check in checks.items():
        command = check.get("command") if isinstance(check, dict) else None
        if not isinstance(name, str) or not name or not valid_string_list(command):
            errors.append(f"check `{name}` command must be a non-empty list of strings")
    return checks


def _validate_execution_budgets(policy: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    budgets = policy.get("execution_budgets")
    if not isinstance(budgets, dict) or set(budgets) != EXECUTION_BUDGET_FIELDS:
        errors.append("execution_budgets must define max_turn_timeout_seconds and profiles")
        return {}
    maximum = budgets.get("max_turn_timeout_seconds")
    if not positive_integer(maximum):
        errors.append("execution_budgets max_turn_timeout_seconds must be a positive integer")
    profiles = budgets.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        errors.append("execution_budgets profiles must be a non-empty mapping")
        return {}
    for name, profile in profiles.items():
        if not isinstance(name, str) or not name or not isinstance(profile, dict):
            errors.append("execution budget profiles must map names to mappings")
            continue
        allowed = EXECUTION_BUDGET_PROFILE_FIELDS | EXECUTION_BUDGET_PROFILE_OPTIONAL_FIELDS
        if set(profile) - allowed or EXECUTION_BUDGET_PROFILE_FIELDS - profile.keys():
            errors.append(f"execution budget profile `{name}` has invalid fields")
            continue
        timeout = profile.get("turn_timeout_seconds")
        if not positive_integer(timeout) or (positive_integer(maximum) and timeout > maximum):
            errors.append(f"execution budget profile `{name}` has invalid turn_timeout_seconds")
        decisions = profile.get("timeout_decisions")
        if not valid_string_list(decisions) or len(set(decisions)) != len(decisions) or set(decisions) - TIMEOUT_DECISIONS or "block" not in decisions:
            errors.append(f"execution budget profile `{name}` has invalid timeout_decisions")
        successor = profile.get("escalation_profile")
        if successor is not None and not isinstance(successor, str):
            errors.append(f"execution budget profile `{name}` has invalid escalation_profile")
        if isinstance(decisions, list) and "escalate" in decisions and successor is None:
            errors.append(f"execution budget profile `{name}` escalation requires escalation_profile")
    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        successor = profile.get("escalation_profile")
        if successor is not None and successor not in profiles:
            errors.append(f"execution budget profile `{name}` has unknown escalation_profile")
    return profiles


def _validate_orchestration(policy: dict[str, Any], errors: list[str], roles: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    orchestration = policy.get("orchestration")
    if not isinstance(orchestration, dict) or not orchestration:
        errors.append("orchestration must be a non-empty mapping")
        return {}
    aliases: set[str] = set()
    for name, topology in orchestration.items():
        if not isinstance(name, str) or not name or not isinstance(topology, dict):
            errors.append("orchestration must map names to mappings")
            continue
        if set(topology) != ORCHESTRATION_FIELDS:
            errors.append(f"orchestration `{name}` has invalid fields")
            continue
        mode_aliases = topology["aliases"]
        if not valid_string_list(mode_aliases) or len(set(mode_aliases)) != len(mode_aliases) or aliases.intersection(mode_aliases):
            errors.append(f"orchestration `{name}` has invalid aliases")
        aliases.update(mode_aliases if isinstance(mode_aliases, list) else [])
        if topology["work_scheduling"] not in {"single", "sequential", "parallel"}:
            errors.append(f"orchestration `{name}` has invalid work_scheduling")
        if not positive_integer(topology["max_parallel_writers"]):
            errors.append(f"orchestration `{name}` max_parallel_writers must be positive")
        if topology["workspace_mode"] not in {"current", "isolated"}:
            errors.append(f"orchestration `{name}` has invalid workspace_mode")
        if topology["work_scheduling"] == "parallel" and topology["workspace_mode"] != "isolated":
            errors.append(f"orchestration `{name}` parallel writers require isolated workspace")
        if topology["validator_role"] not in roles:
            errors.append(f"orchestration `{name}` has unknown validator_role")
        if not isinstance(topology["rules"], list) or not all(isinstance(rule, str) and rule for rule in topology["rules"]):
            errors.append(f"orchestration `{name}` rules must be a list of strings")
    return orchestration


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    roles_path = root / "agents" / "roles.yaml"
    policy_path = root / "repo_config" / "harness.yaml"
    if not roles_path.is_file():
        return ["missing roles file `agents/roles.yaml`"]
    if not policy_path.is_file():
        return ["missing harness policy `repo_config/harness.yaml`"]
    try:
        roles_payload = load_yaml(roles_path)
        policy = load_yaml(policy_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"invalid YAML: {exc}"]

    roles = _validate_roles(roles_payload, errors)
    if not isinstance(policy, dict):
        return [*errors, "harness policy must be a mapping"]
    if policy.get("version") != 4:
        errors.append("harness policy version must be 4")
    unknown_policy_fields = set(policy) - POLICY_FIELDS - POLICY_OPTIONAL_FIELDS
    missing_policy_fields = POLICY_FIELDS - policy.keys()
    if missing_policy_fields:
        errors.append(f"harness policy missing fields: {', '.join(sorted(missing_policy_fields))}")
    if unknown_policy_fields:
        errors.append(f"harness policy has unknown fields: {', '.join(sorted(unknown_policy_fields))}")

    core_policy = policy.get("harness_core")
    request_api = core_policy.get("request_api") if isinstance(core_policy, dict) else None
    if not isinstance(core_policy, dict) or set(core_policy) != {"request_api"}:
        errors.append("harness_core must define request_api")
    request_admission = admit_request_api(request_api)
    if not request_admission["ok"]:
        errors.append(request_admission["code"])
    elif request_api != 4:
        errors.append("harness_core request_api must be 4")

    templates = list_templates(root)
    rules = {path.stem for path in (root / "docs" / "operating_system" / "rules").glob("*.md")}
    skills = {path.parent.name for path in (root / ".agents" / "skills").glob("*/SKILL.md")}
    context_limits = policy.get("context_limits")
    if not isinstance(context_limits, dict) or set(context_limits) != CONTEXT_LIMIT_FIELDS or not all(positive_integer(value) for value in context_limits.values()):
        errors.append("context_limits must define positive integer limits")

    evidence_artifacts = policy.get("evidence_artifacts")
    if (
        not isinstance(evidence_artifacts, dict)
        or not EVIDENCE_ARTIFACT_POLICY_FIELDS <= set(evidence_artifacts)
        or not set(evidence_artifacts) <= EVIDENCE_ARTIFACT_POLICY_FIELDS | EVIDENCE_ARTIFACT_POLICY_OPTIONAL_FIELDS
    ):
        errors.append("evidence_artifacts has invalid fields")
    else:
        retained = evidence_artifacts["writer_retained_kinds"]
        if not isinstance(retained, list) or len(set(retained)) != len(retained) or not set(retained) <= READONLY_ARTIFACT_KINDS:
            errors.append("evidence_artifacts writer_retained_kinds is invalid")
        legacy_max_bytes = evidence_artifacts.get("sanitized_command_trace_max_bytes")
        if legacy_max_bytes is not None and (
            not positive_integer(legacy_max_bytes)
            or not isinstance(context_limits, dict)
            or legacy_max_bytes != context_limits.get("artifact_max_bytes")
        ):
            errors.append("evidence_artifacts legacy sanitized_command_trace_max_bytes must match artifact_max_bytes")

    checks = _validate_named_commands(policy, errors)
    tools = policy.get("tools")
    if not isinstance(tools, dict) or not tools:
        errors.append("tools must be a non-empty mapping")
        tools = {}
    for name, tool in tools.items():
        if not isinstance(name, str) or not name or not isinstance(tool, dict) or set(tool) != TOOL_FIELDS:
            errors.append(f"tool `{name}` has invalid fields")
            continue
        if not isinstance(tool["optional"], bool):
            errors.append(f"tool `{name}` optional must be a boolean")
        if not isinstance(tool["host_kind"], str) or not tool["host_kind"]:
            errors.append(f"tool `{name}` host_kind must be a non-empty string")
        if tool["writer_access"] not in {"workspace_write", "read_only"}:
            errors.append(f"tool `{name}` writer_access must be `workspace_write` or `read_only`")
        if tool["validator_access"] != "read_only":
            errors.append(f"tool `{name}` validator_access must be `read_only`")
        if not isinstance(tool["root_probe"], str) or not tool["root_probe"]:
            errors.append(f"tool `{name}` root_probe must be a non-empty string")

    runtime_providers = policy.get("runtime_providers")
    if not isinstance(runtime_providers, dict) or not runtime_providers:
        errors.append("runtime_providers must be a non-empty mapping")
        runtime_providers = {}
    for name, provider in runtime_providers.items():
        if not isinstance(name, str) or not name or not isinstance(provider, dict) or set(provider) != RUNTIME_PROVIDER_FIELDS or not positive_integer(provider.get("contract_version")):
            errors.append(f"runtime provider `{name}` is invalid")

    defaults = policy.get("defaults")
    if not isinstance(defaults, dict) or set(defaults) != DEFAULT_FIELDS:
        errors.append("defaults has invalid fields")
        defaults = {}
    elif (
        defaults["source_workspace"] != "current_repo"
        or defaults["runtime_provider"] not in runtime_providers
        or not isinstance(defaults["retry_policy"], str)
        or not isinstance(defaults["execution_budget_profile"], str)
        or defaults["approval_gates"] != []
    ):
        errors.append("defaults must contain only safe route defaults")

    authorities = policy.get("authorities")
    if not isinstance(authorities, dict) or not authorities:
        errors.append("authorities must be a non-empty mapping")
        authorities = {}
    for name, authority in authorities.items():
        capabilities = authority.get("capabilities") if isinstance(authority, dict) else None
        access = authority.get("workspace_write_access") if isinstance(authority, dict) else None
        if not isinstance(name, str) or not name or not isinstance(authority, dict) or set(authority) != AUTHORITY_FIELDS:
            errors.append(f"authority `{name}` has invalid fields")
        elif not valid_string_list(capabilities) or len(set(capabilities)) != len(capabilities) or not set(capabilities) <= CAPABILITIES:
            errors.append(f"authority `{name}` has invalid capabilities")
        elif access not in {"read_only", "workspace_write"} or (("repo.write" in capabilities) != (access == "workspace_write")):
            errors.append(f"authority `{name}` has invalid workspace_write_access")

    toolsets = policy.get("toolsets")
    if not isinstance(toolsets, dict) or not toolsets:
        errors.append("toolsets must be a non-empty mapping")
        toolsets = {}
    for name, selected_tools in toolsets.items():
        if not isinstance(name, str) or not name or not valid_string_list(selected_tools) or len(set(selected_tools)) != len(selected_tools) or not set(selected_tools) <= set(tools):
            errors.append(f"toolset `{name}` is invalid")

    verification_profiles = policy.get("verification_profiles")
    if not isinstance(verification_profiles, dict) or not verification_profiles:
        errors.append("verification_profiles must be a non-empty mapping")
        verification_profiles = {}
    for name, profile in verification_profiles.items():
        if not isinstance(name, str) or not name or not isinstance(profile, dict) or set(profile) != VERIFICATION_PROFILE_FIELDS:
            errors.append(f"verification profile `{name}` has invalid fields")
            continue
        postconditions = profile["postconditions"]
        profile_checks = profile["checks"]
        if not valid_string_list(postconditions, allow_empty=True) or len(set(postconditions)) != len(postconditions) or not set(postconditions) <= POSTCONDITIONS:
            errors.append(f"verification profile `{name}` has invalid postconditions")
        if not valid_string_list(profile_checks, allow_empty=True) or len(set(profile_checks)) != len(profile_checks) or not set(profile_checks) <= set(checks):
            errors.append(f"verification profile `{name}` has invalid checks")
        if not postconditions and not profile_checks:
            errors.append(f"verification profile `{name}` must select a postcondition or check")

    delegation_profiles = policy.get("delegation_profiles")
    if not isinstance(delegation_profiles, dict) or not delegation_profiles:
        errors.append("delegation_profiles must be a non-empty mapping")
        delegation_profiles = {}
    for name, profile in delegation_profiles.items():
        if not isinstance(name, str) or not name or not isinstance(profile, dict) or set(profile) != DELEGATION_PROFILE_FIELDS:
            errors.append(f"delegation profile `{name}` is invalid")
            continue
        numeric_fields = ("max_depth", "max_children", "max_concurrent_children", "per_child_timeout_seconds", "total_child_timeout_seconds")
        if not all(isinstance(profile[field], int) and not isinstance(profile[field], bool) and profile[field] >= 0 for field in numeric_fields):
            errors.append(f"delegation profile `{name}` has invalid limits")
        if not valid_string_list(profile["allowed_roles"], allow_empty=True) or not set(profile["allowed_roles"]) <= set(roles):
            errors.append(f"delegation profile `{name}` allowed_roles is invalid")
        if not valid_string_list(profile["capability_ceiling"], allow_empty=True) or not set(profile["capability_ceiling"]) <= CAPABILITIES:
            errors.append(f"delegation profile `{name}` capability_ceiling is invalid")
        if profile["workspace_write_access"] not in {"read_only", "workspace_write"} or profile["verification"] not in {"none", "schema", "checks", "validator"}:
            errors.append(f"delegation profile `{name}` has invalid workspace or verification")

    retry_policies = policy.get("retry_policies")
    if not isinstance(retry_policies, dict) or not retry_policies:
        errors.append("retry_policies must be a non-empty mapping")
        retry_policies = {}
    for name, retry in retry_policies.items():
        if not isinstance(name, str) or not name or not isinstance(retry, dict) or set(retry) != RETRY_POLICY_FIELDS:
            errors.append(f"retry policy `{name}` has invalid fields")
            continue
        if not positive_integer(retry["max_attempts"]) or not valid_string_list(retry["retryable_reasons"]) or retry["exhaustion"] != "block" or retry["approval_resume"] != "successor_attempt" or not positive_integer(retry["approval_ttl_seconds"]):
            errors.append(f"retry policy `{name}` is invalid")

    budget_profiles = _validate_execution_budgets(policy, errors)
    orchestration = _validate_orchestration(policy, errors, roles)

    friction_policy = policy.get("friction_policy")
    follow_up_routes: dict[str, str] = {}
    if not isinstance(friction_policy, dict) or set(friction_policy) - (FRICTION_POLICY_FIELDS | FRICTION_POLICY_OPTIONAL_FIELDS) or FRICTION_POLICY_FIELDS - friction_policy.keys():
        errors.append("friction_policy has invalid fields")
    else:
        if friction_policy["event_version"] != 1 or not positive_integer(friction_policy["minimum_distinct_runs"]) or not positive_integer(friction_policy["window_days"]):
            errors.append("friction_policy is invalid")
        raw_follow_up_routes = friction_policy.get("follow_up_routes", {})
        if not isinstance(raw_follow_up_routes, dict) or not all(isinstance(code, str) and code and isinstance(route, str) and route for code, route in raw_follow_up_routes.items()):
            errors.append("friction policy `follow_up_routes` must map codes to task types")
        else:
            follow_up_routes = raw_follow_up_routes

    gates = policy.get("approval_gates")
    if not isinstance(gates, dict):
        errors.append("approval_gates must be a mapping")
        gates = {}
    for name, gate in gates.items():
        if not isinstance(name, str) or not name or not isinstance(gate, dict) or set(gate) != {"paths"} or not valid_string_list(gate.get("paths")):
            errors.append(f"approval gate `{name}` is invalid")

    skill_sets = policy.get("skill_sets", {})
    if not isinstance(skill_sets, dict):
        errors.append("skill_sets must be a mapping")
        skill_sets = {}
    for set_name, skill_set in skill_sets.items():
        if not isinstance(set_name, str) or not set_name or not isinstance(skill_set, dict) or set(skill_set) != {"skills", "selection_guidance"}:
            errors.append(f"skill set `{set_name}` is invalid")
            continue
        selected_skills = skill_set["skills"]
        if not valid_string_list(selected_skills) or len(set(selected_skills)) != len(selected_skills) or not set(selected_skills) <= skills:
            errors.append(f"skill set `{set_name}` has invalid skills")
        if not isinstance(skill_set["selection_guidance"], str) or not skill_set["selection_guidance"].strip():
            errors.append(f"skill set `{set_name}` has invalid selection_guidance")

    operating_profiles = policy.get("operating_profiles", {})
    if not isinstance(operating_profiles, dict):
        errors.append("operating_profiles must be a mapping")
        operating_profiles = {}

    routes = policy.get("routes")
    if not isinstance(routes, dict) or not routes:
        errors.append("routes must be a non-empty mapping")
        routes = {}
    for name, route in routes.items():
        if not isinstance(name, str) or not name or not isinstance(route, dict):
            errors.append("routes must map names to mappings")
            continue
        composed = any(field in route for field in {"required_skill_sets", "allowed_skill_sets", "default_operating_profile", "allowed_operating_profiles"})
        if composed:
            missing = COMPOSED_ROUTE_FIELDS - route.keys()
            unknown = set(route) - COMPOSED_ROUTE_FIELDS - COMPOSED_ROUTE_OPTIONAL_FIELDS
            if missing:
                errors.append(f"route `{name}` missing fields: {', '.join(sorted(missing))}")
            if unknown:
                errors.append(f"route `{name}` has unknown fields: {', '.join(sorted(unknown))}")
            role_name = route.get("role")
            if role_name not in roles:
                errors.append(f"unknown role `{role_name}`")
            for field, available in (("rules", rules),):
                values = route.get(field)
                if not valid_string_list(values) or len(set(values)) != len(values):
                    errors.append(f"route `{name}` {field} must be a unique non-empty list of strings")
                elif not set(values) <= available:
                    errors.append(f"route `{name}` has unknown {field}")
            for field in ("required_skill_sets", "allowed_skill_sets", "allowed_operating_profiles"):
                values = route.get(field)
                if not valid_string_list(values) or len(set(values)) != len(values):
                    errors.append(f"route `{name}` {field} must be a unique non-empty list of strings")
            required_sets = route.get("required_skill_sets", [])
            allowed_sets = route.get("allowed_skill_sets", [])
            if isinstance(required_sets, list) and isinstance(allowed_sets, list):
                if set(required_sets).intersection(allowed_sets) or not set(required_sets).union(allowed_sets) <= set(skill_sets):
                    errors.append(f"route `{name}` has invalid skill sets")
            default_profile = route.get("default_operating_profile")
            allowed_profiles = route.get("allowed_operating_profiles", [])
            if not isinstance(default_profile, str) or default_profile not in allowed_profiles:
                errors.append(f"route `{name}` has invalid default_operating_profile")
            if isinstance(allowed_profiles, list):
                for profile_name in allowed_profiles:
                    try:
                        profile = resolve_operating_profile(policy, name, profile_name)
                    except ValueError as exc:
                        errors.append(str(exc))
                        continue
                    if profile["template"] not in templates or role_name not in roles or profile["template"] not in roles[role_name].get("accepts", []):
                        errors.append(f"route `{name}` has invalid operating profile `{profile_name}`")
                    if profile["authority"] not in authorities or profile["toolset"] not in toolsets or profile["verification_profile"] not in verification_profiles or profile["runtime_provider"] not in runtime_providers or profile["execution_budget_profile"] not in budget_profiles:
                        errors.append(f"route `{name}` has invalid operating profile `{profile_name}`")
                    if profile["runtime_provider"] != defaults.get("runtime_provider"):
                        errors.append(f"route `{name}` operating profiles must resolve default runtime provider")
            transitions = route.get("escalation_transitions", [])
            seen_transitions: set[tuple[str, str]] = set()
            if not isinstance(transitions, list):
                errors.append(f"route `{name}` escalation_transitions must be a list")
            else:
                for transition in transitions:
                    if not isinstance(transition, dict) or set(transition) != {"from", "on", "to"} or transition.get("on") != "dispatch_timeout" or transition.get("from") not in allowed_profiles or transition.get("to") not in allowed_profiles or (transition.get("from"), transition.get("on")) in seen_transitions:
                        errors.append(f"route `{name}` has invalid escalation_transitions")
                        continue
                    seen_transitions.add((transition["from"], transition["on"]))
            for field, available in (("delegation_profile", delegation_profiles),):
                if route.get(field) not in available:
                    errors.append(f"route `{name}` has unknown {field} `{route.get(field)}`")
            modes = route.get("execution_modes")
            if not valid_string_list(modes) or len(set(modes)) != len(modes):
                errors.append(f"route `{name}` execution_modes must be a unique non-empty list of strings")
            elif not set(modes) <= set(orchestration):
                errors.append(f"route `{name}` has unknown execution mode")
            continue
        missing = ROUTE_FIELDS - route.keys()
        unknown = set(route) - ROUTE_FIELDS - ROUTE_OPTIONAL_FIELDS
        if missing:
            errors.append(f"route `{name}` missing fields: {', '.join(sorted(missing))}")
        if unknown:
            errors.append(f"route `{name}` has unknown fields: {', '.join(sorted(unknown))}")
        template = route.get("template")
        role_name = route.get("role")
        if template not in templates:
            errors.append(f"unknown template `{template}`")
        if role_name not in roles:
            errors.append(f"unknown role `{role_name}`")
        elif template not in roles[role_name].get("accepts", []):
            errors.append(f"role `{role_name}` does not accept template `{template}`")
        for field, available in (("rules", rules), ("skills", skills)):
            values = route.get(field)
            if not valid_string_list(values) or len(set(values)) != len(values):
                errors.append(f"route `{name}` {field} must be a unique non-empty list of strings")
            elif not set(values) <= available:
                errors.append(f"route `{name}` has unknown {field}")
        for field, available in (("authority", authorities), ("toolset", toolsets), ("verification_profile", verification_profiles), ("delegation_profile", delegation_profiles)):
            if route.get(field) not in available:
                errors.append(f"route `{name}` has unknown {field} `{route.get(field)}`")
        modes = route.get("execution_modes")
        if not valid_string_list(modes) or len(set(modes)) != len(modes):
            errors.append(f"route `{name}` execution_modes must be a unique non-empty list of strings")
        elif not set(modes) <= set(orchestration):
            errors.append(f"route `{name}` has unknown execution mode")
        route_gates = route.get("approval_gates", defaults.get("approval_gates", []))
        if not valid_string_list(route_gates, allow_empty=True) or len(set(route_gates)) != len(route_gates) or not set(route_gates) <= set(gates):
            errors.append(f"route `{name}` has invalid approval_gates")
        readonly_artifacts = route.get("readonly_artifacts")
        if readonly_artifacts is not None:
            if not isinstance(readonly_artifacts, dict) or set(readonly_artifacts) != READONLY_ARTIFACT_POLICY_FIELDS:
                errors.append(f"route `{name}` readonly_artifacts must define allowed_kinds and required_kinds")
            else:
                allowed = readonly_artifacts["allowed_kinds"]
                required = readonly_artifacts["required_kinds"]
                if not isinstance(allowed, list) or len(set(allowed)) != len(allowed) or not set(allowed) <= READONLY_ARTIFACT_KINDS or not isinstance(required, list) or len(set(required)) != len(required) or not set(required) <= set(allowed):
                    errors.append(f"route `{name}` readonly_artifacts is invalid")
                authority = authorities.get(route.get("authority"), {})
                if authority.get("workspace_write_access") != "read_only":
                    errors.append(f"route `{name}` readonly_artifacts requires read-only authority")
    for code, task_type in follow_up_routes.items():
        route = routes.get(task_type)
        authority = authorities.get(route.get("authority"), {}) if isinstance(route, dict) else {}
        modes = route.get("execution_modes") if isinstance(route, dict) else None
        if authority.get("workspace_write_access") != "read_only" or not isinstance(modes, list) or "single_work_lane" not in modes:
            errors.append(f"friction follow-up route `{task_type}` for `{code}` must be single-lane read-only")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate canonical harness policy.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = validate(Path(args.repo_root))
    if errors:
        print("Harness configuration validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Harness configuration validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
