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
    "tools",
    "workspace",
    "checks",
    "retry_policy",
    "execution_budget_profile",
    "execution_modes",
    "runtime_providers",
    "default_runtime_provider",
    "capabilities",
    "delegation_profile",
}
READONLY_ARTIFACT_KINDS = {"terminal_observation", "sanitized_command_trace"}
READONLY_ARTIFACT_POLICY_FIELDS = {"allowed_kinds", "required_kinds"}
EVIDENCE_ARTIFACT_POLICY_FIELDS = {"writer_retained_kinds", "sanitized_command_trace_max_bytes"}
ROLE_FIELDS = {"accepts", "result_kind", "required_fields"}
ORCHESTRATION_FIELDS = {
    "aliases",
    "work_scheduling",
    "max_parallel_writers",
    "workspace_mode",
    "validator_role",
    "review_required",
    "rules",
}
RETRY_POLICY_FIELDS = {"max_attempts", "retryable_reasons", "exhaustion", "approval_resume", "approval_ttl_seconds"}
TOOL_FIELDS = {"optional", "fallback", "host_kind", "writer_access", "validator_access", "root_probe"}
REQUIRED_STATES = {"classified", "planned", "running", "observed", "verifying", "awaiting_decision", "accepted", "unvalidated", "blocked"}
RUNTIME_PROVIDER_FIELDS = {"contract_version"}
CAPABILITY_POLICY_FIELDS = {"catalog", "sets"}
CONTEXT_LIMIT_FIELDS = {"objective_max_bytes", "fact_max_bytes", "max_facts", "max_artifacts", "outcome_summary_max_bytes"}
DELEGATION_PROFILE_FIELDS = {"max_depth", "max_children", "max_concurrent_children", "per_child_timeout_seconds", "total_child_timeout_seconds", "allowed_roles", "capability_ceiling", "workspace_write_access", "verification"}
FRICTION_POLICY_FIELDS = {"event_version", "minimum_distinct_runs", "window_days"}
FRICTION_POLICY_OPTIONAL_FIELDS = {"follow_up_routes"}
EXECUTION_BUDGET_FIELDS = {"max_turn_timeout_seconds", "profiles"}
EXECUTION_BUDGET_PROFILE_FIELDS = {"turn_timeout_seconds", "timeout_decisions"}
EXECUTION_BUDGET_PROFILE_OPTIONAL_FIELDS = {"escalation_profile"}
TIMEOUT_DECISIONS = {"escalate", "block"}


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def list_templates(root: Path) -> set[str]:
    templates: set[str] = set()
    for path in (root / "agents").glob("*.toml"):
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
        name = payload.get("name")
        if isinstance(name, str) and name == path.stem:
            templates.add(name)
    return templates


def valid_string_list(value: Any) -> bool:
    return bool(value) and isinstance(value, list) and all(
        isinstance(item, str) and item for item in value
    )


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    roles_path = root / "agents" / "roles.yaml"
    policy_path = root / "repo_config" / "harness.yaml"
    if not roles_path.is_file():
        return ["missing roles file `agents/roles.yaml`"]
    if not policy_path.is_file():
        return ["missing harness policy `repo_config/harness.yaml`"]

    roles_payload = load_yaml(roles_path)
    policy = load_yaml(policy_path)
    templates = list_templates(root)
    rules = {path.stem for path in (root / "docs" / "operating_system" / "rules").glob("*.md")}
    skills = {path.parent.name for path in (root / ".agents" / "skills").glob("*/SKILL.md")}

    roles_version = roles_payload.get("version") if isinstance(roles_payload, dict) else None
    if roles_version not in {1, 2}:
        return ["roles version must be 1 or 2"]
    roles = roles_payload.get("roles") if isinstance(roles_payload, dict) else None
    if not isinstance(roles, dict):
        return ["roles must be a mapping"]
    for name, role in roles.items():
        if not isinstance(name, str) or not isinstance(role, dict):
            errors.append("roles must map names to mappings")
            continue
        required_fields = ROLE_FIELDS | ({"writes"} if roles_version == 1 else set())
        missing = required_fields - role.keys()
        if missing:
            errors.append(f"role `{name}` missing fields: {', '.join(sorted(missing))}")
        if roles_version == 1 and not isinstance(role.get("writes"), bool):
            errors.append(f"role `{name}` writes must be a boolean")
        if roles_version == 2 and "writes" in role:
            errors.append(f"role `{name}` must not define writes in role schema v2")
        if not valid_string_list(role.get("accepts")):
            errors.append(f"role `{name}` accepts must be a list of strings")
        if not isinstance(role.get("result_kind"), str) or not role["result_kind"]:
            errors.append(f"role `{name}` result_kind must be a non-empty string")
        if not valid_string_list(role.get("required_fields")):
            errors.append(f"role `{name}` required_fields must be a list of strings")
        constraints = role.get("field_constraints")
        if constraints is not None:
            if not isinstance(constraints, dict):
                errors.append(f"role `{name}` field_constraints must be a mapping")
            else:
                for field, values in constraints.items():
                    if field not in role.get("required_fields", []) or not valid_string_list(values):
                        errors.append(f"role `{name}` field constraint `{field}` must target a required string field")

    if not isinstance(policy, dict):
        return [*errors, "harness policy must be a mapping"]
    if not isinstance(policy.get("version"), int):
        errors.append("harness policy version must be an integer")

    core_policy = policy.get("harness_core")
    request_api = core_policy.get("request_api") if isinstance(core_policy, dict) else None
    request_admission = admit_request_api(request_api)
    if not request_admission["ok"]:
        errors.append(request_admission["code"])

    capability_catalog: set[str] = set()
    delegation_profiles: set[str] = set()
    if request_api == 4:
        capability_policy = policy.get("capabilities")
        if not isinstance(capability_policy, dict) or set(capability_policy) != CAPABILITY_POLICY_FIELDS:
            errors.append("capabilities must define catalog and sets")
        else:
            catalog = capability_policy["catalog"]
            if not valid_string_list(catalog) or len(set(catalog)) != len(catalog):
                errors.append("capabilities catalog must be unique non-empty strings")
            else:
                capability_catalog = set(catalog)
            sets = capability_policy["sets"]
            if not isinstance(sets, dict) or not sets or any(not isinstance(name, str) or not valid_string_list(values) or not set(values) <= capability_catalog for name, values in sets.items()):
                errors.append("capabilities sets must reference catalog values")
        context_limits = policy.get("context_limits")
        if not isinstance(context_limits, dict) or set(context_limits) != CONTEXT_LIMIT_FIELDS or any(not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in context_limits.values()):
            errors.append("context_limits must define positive integer limits")
        evidence_artifacts = policy.get("evidence_artifacts", {})
        if evidence_artifacts and (
            not isinstance(evidence_artifacts, dict)
            or set(evidence_artifacts) != EVIDENCE_ARTIFACT_POLICY_FIELDS
        ):
            errors.append("evidence_artifacts has invalid fields")
        elif evidence_artifacts:
            retained_kinds = evidence_artifacts["writer_retained_kinds"]
            if (
                not isinstance(retained_kinds, list)
                or len(set(retained_kinds)) != len(retained_kinds)
                or not set(retained_kinds) <= READONLY_ARTIFACT_KINDS
            ):
                errors.append("evidence_artifacts writer_retained_kinds is invalid")
            max_bytes = evidence_artifacts["sanitized_command_trace_max_bytes"]
            if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
                errors.append("evidence_artifacts sanitized_command_trace_max_bytes must be positive")
        profiles = policy.get("delegation_profiles")
        if not isinstance(profiles, dict) or not profiles:
            errors.append("delegation_profiles must be a non-empty mapping")
        else:
            delegation_profiles = set(profiles)
            for name, profile in profiles.items():
                if not isinstance(name, str) or not isinstance(profile, dict) or set(profile) != DELEGATION_PROFILE_FIELDS:
                    errors.append(f"delegation profile `{name}` is invalid")
                    continue
                if not isinstance(profile["capability_ceiling"], list) or not set(profile["capability_ceiling"]) <= capability_catalog:
                    errors.append(f"delegation profile `{name}` capability_ceiling is invalid")
                if profile["verification"] not in {"none", "schema", "checks", "validator"} or profile["workspace_write_access"] not in {"read_only", "workspace_write"}:
                    errors.append(f"delegation profile `{name}` has invalid workspace or verification")

    states = policy.get("states")
    if not isinstance(states, dict):
        errors.append("states must be a mapping")
        states = {}
    for state, next_states in states.items():
        if not valid_string_list(next_states) and next_states != []:
            errors.append(f"state `{state}` transitions must be a list of strings")
            continue
        for next_state in next_states:
            if next_state not in states:
                errors.append(f"state `{state}` references unknown state `{next_state}`")
    for state in sorted(REQUIRED_STATES - states.keys()):
        errors.append(f"missing required state `{state}`")
    for state in ("accepted", "unvalidated", "blocked"):
        if states.get(state) not in ([], None):
            errors.append(f"state `{state}` must be terminal")

    checks = policy.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks must be a mapping")
        checks = {}
    for name, check in checks.items():
        command = check.get("command") if isinstance(check, dict) else None
        if not valid_string_list(command):
            errors.append(f"check `{name}` command must be a non-empty list of strings")

    tools = policy.get("tools")
    if not isinstance(tools, dict):
        errors.append("tools must be a mapping")
        tools = {}
    for name, tool in tools.items():
        if not isinstance(tool, dict):
            errors.append(f"tool `{name}` must be a mapping")
            continue
        missing = {"host_kind", "writer_access", "validator_access", "root_probe"} - tool.keys()
        unknown = set(tool) - TOOL_FIELDS
        if missing:
            errors.append(f"tool `{name}` missing fields: {', '.join(sorted(missing))}")
        if unknown:
            errors.append(f"tool `{name}` has unknown fields: {', '.join(sorted(unknown))}")
        if not isinstance(tool.get("host_kind"), str) or not tool["host_kind"]:
            errors.append(f"tool `{name}` host_kind must be a non-empty string")
        if tool.get("writer_access") not in {"workspace_write", "read_only"}:
            errors.append(f"tool `{name}` writer_access must be `workspace_write` or `read_only`")
        if tool.get("validator_access") != "read_only":
            errors.append(f"tool `{name}` validator_access must be `read_only`")
        if not isinstance(tool.get("root_probe"), str) or not tool["root_probe"]:
            errors.append(f"tool `{name}` root_probe must be a non-empty string")

    runtime_providers = policy.get("runtime_providers")
    if not isinstance(runtime_providers, dict) or not runtime_providers:
        errors.append("runtime_providers must be a non-empty mapping")
        runtime_providers = {}
    for provider_id, provider in runtime_providers.items():
        if not isinstance(provider_id, str) or not provider_id or not isinstance(provider, dict):
            errors.append("runtime_providers must map non-empty IDs to mappings")
            continue
        missing = RUNTIME_PROVIDER_FIELDS - provider.keys()
        unknown = set(provider) - RUNTIME_PROVIDER_FIELDS
        if missing:
            errors.append(f"runtime provider `{provider_id}` missing fields: {', '.join(sorted(missing))}")
        if unknown:
            errors.append(f"runtime provider `{provider_id}` has unknown fields: {', '.join(sorted(unknown))}")
        version = provider.get("contract_version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            errors.append(f"runtime provider `{provider_id}` contract_version must be a positive integer")

    follow_up_routes: dict[str, str] = {}
    friction_policy = policy.get("friction_policy")
    if not isinstance(friction_policy, dict):
        errors.append("friction_policy must be a mapping")
    else:
        missing = FRICTION_POLICY_FIELDS - friction_policy.keys()
        unknown = set(friction_policy) - FRICTION_POLICY_FIELDS - FRICTION_POLICY_OPTIONAL_FIELDS
        if missing:
            errors.append(f"friction policy missing fields: {', '.join(sorted(missing))}")
        if unknown:
            errors.append(f"friction policy has unknown fields: {', '.join(sorted(unknown))}")
        if friction_policy.get("event_version") != 1:
            errors.append("friction policy `event_version` must be 1")
        for name in ("minimum_distinct_runs", "window_days"):
            value = friction_policy.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                errors.append(f"friction policy `{name}` must be a positive integer")
        raw_follow_up_routes = friction_policy.get("follow_up_routes", {})
        if not isinstance(raw_follow_up_routes, dict) or not all(
            isinstance(code, str) and code and isinstance(task_type, str) and task_type
            for code, task_type in raw_follow_up_routes.items()
        ):
            errors.append("friction policy `follow_up_routes` must map codes to task types")
        else:
            follow_up_routes = raw_follow_up_routes

    gates = policy.get("approval_gates", {})
    if not isinstance(gates, dict):
        errors.append("approval_gates must be a mapping")
        gates = {}
    for name, gate in gates.items():
        paths = gate.get("paths") if isinstance(gate, dict) else None
        if not valid_string_list(paths):
            errors.append(f"approval gate `{name}` paths must be a non-empty list of strings")

    retry_policies = policy.get("retry_policies")
    if not isinstance(retry_policies, dict) or not retry_policies:
        errors.append("retry_policies must be a non-empty mapping")
        retry_policies = {}
    for name, retry_policy in retry_policies.items():
        if not isinstance(retry_policy, dict):
            errors.append(f"retry policy `{name}` must be a mapping")
            continue
        missing = RETRY_POLICY_FIELDS - retry_policy.keys()
        if missing:
            errors.append(f"retry policy `{name}` missing fields: {', '.join(sorted(missing))}")
            continue
        attempts = retry_policy["max_attempts"]
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
            errors.append(f"retry policy `{name}` max_attempts must be a positive integer")
        if not valid_string_list(retry_policy["retryable_reasons"]):
            errors.append(f"retry policy `{name}` retryable_reasons must be a non-empty list of strings")
        if retry_policy["exhaustion"] != "block":
            errors.append(f"retry policy `{name}` exhaustion must be `block`")
        if retry_policy["approval_resume"] != "successor_attempt":
            errors.append(f"retry policy `{name}` approval_resume must be `successor_attempt`")
        ttl_seconds = retry_policy["approval_ttl_seconds"]
        if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or ttl_seconds < 1:
            errors.append(f"retry policy `{name}` approval_ttl_seconds must be a positive integer")

    execution_budgets = policy.get("execution_budgets")
    profiles: dict[str, dict[str, Any]] = {}
    if not isinstance(execution_budgets, dict):
        errors.append("execution_budgets must be a mapping")
    else:
        missing = EXECUTION_BUDGET_FIELDS - execution_budgets.keys()
        unknown = set(execution_budgets) - EXECUTION_BUDGET_FIELDS
        if missing:
            errors.append(f"execution_budgets missing fields: {', '.join(sorted(missing))}")
        if unknown:
            errors.append(f"execution_budgets has unknown fields: {', '.join(sorted(unknown))}")
        maximum = execution_budgets.get("max_turn_timeout_seconds")
        if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 1:
            errors.append("execution_budgets max_turn_timeout_seconds must be a positive integer")
        raw_profiles = execution_budgets.get("profiles")
        if not isinstance(raw_profiles, dict) or not raw_profiles:
            errors.append("execution_budgets profiles must be a non-empty mapping")
        else:
            for name, profile in raw_profiles.items():
                if not isinstance(name, str) or not name or not isinstance(profile, dict):
                    errors.append("execution budget profiles must map names to mappings")
                    continue
                profiles[name] = profile
                missing = EXECUTION_BUDGET_PROFILE_FIELDS - profile.keys()
                unknown = set(profile) - EXECUTION_BUDGET_PROFILE_FIELDS - EXECUTION_BUDGET_PROFILE_OPTIONAL_FIELDS
                if missing:
                    errors.append(f"execution budget profile `{name}` missing fields: {', '.join(sorted(missing))}")
                if unknown:
                    errors.append(f"execution budget profile `{name}` has unknown fields: {', '.join(sorted(unknown))}")
                timeout = profile.get("turn_timeout_seconds")
                if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
                    errors.append(f"execution budget profile `{name}` turn_timeout_seconds must be a positive integer")
                elif isinstance(maximum, int) and not isinstance(maximum, bool) and timeout > maximum:
                    errors.append(f"execution budget profile `{name}` turn_timeout_seconds exceeds maximum")
                decisions = profile.get("timeout_decisions")
                if not valid_string_list(decisions) or len(set(decisions)) != len(decisions):
                    errors.append(f"execution budget profile `{name}` timeout_decisions must be a unique non-empty list of strings")
                elif set(decisions) - TIMEOUT_DECISIONS or "block" not in decisions:
                    errors.append(f"execution budget profile `{name}` has invalid timeout decisions")
        for name, profile in profiles.items():
            decisions = profile.get("timeout_decisions")
            successor = profile.get("escalation_profile")
            if successor is not None and (not isinstance(successor, str) or successor not in profiles):
                errors.append(f"execution budget profile `{name}` has unknown escalation_profile")
            if isinstance(decisions, list) and "escalate" in decisions and successor is None:
                errors.append(f"execution budget profile `{name}` escalation requires escalation_profile")
            if successor is not None and (not isinstance(decisions, list) or "escalate" not in decisions):
                errors.append(f"execution budget profile `{name}` escalation_profile requires escalate decision")
        for name in profiles:
            seen: set[str] = set()
            current = name
            while current in profiles and profiles[current].get("escalation_profile") is not None:
                if current in seen:
                    errors.append(f"execution budget profiles contain escalation cycle at `{current}`")
                    break
                seen.add(current)
                current = profiles[current]["escalation_profile"]

    orchestration = policy.get("orchestration")
    if not isinstance(orchestration, dict) or not orchestration:
        errors.append("orchestration must be a non-empty mapping")
        orchestration = {}
    aliases: dict[str, str] = {}
    for name, mode in orchestration.items():
        if not isinstance(mode, dict):
            errors.append(f"orchestration `{name}` must be a mapping")
            continue
        missing = ORCHESTRATION_FIELDS - mode.keys()
        unknown = set(mode) - ORCHESTRATION_FIELDS
        if missing:
            errors.append(f"orchestration `{name}` missing fields: {', '.join(sorted(missing))}")
            continue
        if unknown:
            errors.append(f"orchestration `{name}` has unknown fields: {', '.join(sorted(unknown))}")
        if not valid_string_list(mode["aliases"]):
            errors.append(f"orchestration `{name}` aliases must be a non-empty list of strings")
        else:
            for alias in mode["aliases"]:
                if alias in orchestration or alias in aliases:
                    errors.append(f"orchestration alias `{alias}` is ambiguous")
                aliases[alias] = name
        scheduling = mode["work_scheduling"]
        if scheduling not in {"single", "sequential", "parallel"}:
            errors.append(f"orchestration `{name}` work_scheduling must be `single`, `sequential`, or `parallel`")
        writers = mode["max_parallel_writers"]
        if not isinstance(writers, int) or isinstance(writers, bool) or writers < 1:
            errors.append(f"orchestration `{name}` max_parallel_writers must be a positive integer")
        if scheduling != "parallel" and writers != 1:
            errors.append(f"orchestration `{name}` non-parallel scheduling requires one writer")
        if scheduling == "parallel" and writers < 2:
            errors.append(f"orchestration `{name}` parallel scheduling requires at least two writers")
        if mode["workspace_mode"] != "isolated":
            errors.append(f"orchestration `{name}` workspace_mode must be `isolated`")
        validator_role = mode["validator_role"]
        if validator_role not in roles:
            errors.append(f"orchestration `{name}` has unknown validator role `{validator_role}`")
        elif roles_version == 1 and roles[validator_role].get("writes") is not False:
            errors.append(f"orchestration `{name}` validator role `{validator_role}` must not write")
        if not isinstance(mode["review_required"], bool):
            errors.append(f"orchestration `{name}` review_required must be a boolean")
        if not isinstance(mode["rules"], list) or not all(isinstance(rule, str) and rule for rule in mode["rules"]):
            errors.append(f"orchestration `{name}` rules must be a list of strings")
        else:
            for rule in mode["rules"]:
                if rule not in rules:
                    errors.append(f"unknown rule `{rule}`")

    routes = policy.get("routes")
    if not isinstance(routes, dict) or not routes:
        errors.append("routes must be a non-empty mapping")
        return errors
    for name, route in routes.items():
        if not isinstance(route, dict):
            errors.append(f"route `{name}` must be a mapping")
            continue
        missing = (ROUTE_FIELDS - {"capabilities", "delegation_profile"}) - route.keys()
        if missing:
            errors.append(f"route `{name}` missing fields: {', '.join(sorted(missing))}")
            continue
        if request_api == 4 and "capabilities" not in route:
            errors.append(f"route `{name}` missing capabilities")
            continue
        if request_api == 4:
            for capability in route["capabilities"] if isinstance(route["capabilities"], list) else []:
                if capability not in capability_catalog:
                    errors.append(f"route `{name}` capability `{capability}` is unknown")
            if route["delegation_profile"] not in delegation_profiles:
                errors.append(f"route `{name}` has unknown delegation profile `{route['delegation_profile']}`")
        capabilities = route.get("capabilities", [])
        if "capabilities" in route and (
            not isinstance(capabilities, list)
            or not capabilities
            or not all(isinstance(capability, str) and capability for capability in capabilities)
            or len(set(capabilities)) != len(capabilities)
        ):
            errors.append(f"route `{name}` capabilities must be a non-empty list of unique strings")
        template = route["template"]
        role_name = route["role"]
        if template not in templates:
            errors.append(f"unknown template `{template}`")
        if role_name not in roles:
            errors.append(f"unknown role `{role_name}`")
        elif template not in roles[role_name].get("accepts", []):
            errors.append(f"role `{role_name}` does not accept template `{template}`")
        for rule in route["rules"]:
            if rule not in rules:
                errors.append(f"unknown rule `{rule}`")
        for skill in route["skills"]:
            if skill not in skills:
                errors.append(f"unknown skill `{skill}`")
        for check in route["checks"]:
            if check not in checks:
                errors.append(f"unknown check `{check}`")
        for tool in route["tools"]:
            if tool not in tools:
                errors.append(f"unknown tool `{tool}`")
        for gate in route.get("approval_gates", []):
            if gate not in gates:
                errors.append(f"unknown approval gate `{gate}`")
        if route["retry_policy"] not in retry_policies:
            errors.append(f"unknown retry policy `{route['retry_policy']}`")
        profile = route["execution_budget_profile"]
        if not isinstance(profile, str) or profile not in profiles:
            errors.append(f"route `{name}` has unknown execution budget profile `{profile}`")
        for mode in route["execution_modes"]:
            if mode not in orchestration:
                errors.append(f"unknown execution mode `{mode}`")
        for field in ("rules", "skills", "tools", "checks", "execution_modes", "runtime_providers"):
            if not valid_string_list(route[field]):
                errors.append(f"route `{name}` {field} must be a non-empty list of strings")
            elif len(set(route[field])) != len(route[field]):
                errors.append(f"route `{name}` {field} must not contain duplicates")
        for provider_id in route["runtime_providers"]:
            if provider_id not in runtime_providers:
                errors.append(f"route `{name}` has unknown runtime provider `{provider_id}`")
        default_provider = route["default_runtime_provider"]
        if not isinstance(default_provider, str) or not default_provider:
            errors.append(f"route `{name}` default_runtime_provider must be a non-empty string")
        elif default_provider not in route["runtime_providers"]:
            errors.append(f"route `{name}` default_runtime_provider must be allowed")
        if not isinstance(route["workspace"], str) or not route["workspace"]:
            errors.append(f"route `{name}` workspace must be a non-empty string")
        readonly_artifacts = route.get("readonly_artifacts")
        if readonly_artifacts is None:
            continue
        if not isinstance(readonly_artifacts, dict) or set(readonly_artifacts) != READONLY_ARTIFACT_POLICY_FIELDS:
            errors.append(f"route `{name}` readonly_artifacts must define allowed_kinds and required_kinds")
            continue
        allowed_kinds = readonly_artifacts["allowed_kinds"]
        required_kinds = readonly_artifacts["required_kinds"]
        if (
            not isinstance(allowed_kinds, list)
            or len(set(allowed_kinds)) != len(allowed_kinds)
            or not set(allowed_kinds) <= READONLY_ARTIFACT_KINDS
            or not isinstance(required_kinds, list)
            or len(set(required_kinds)) != len(required_kinds)
            or not set(required_kinds) <= set(allowed_kinds)
        ):
            errors.append(f"route `{name}` readonly_artifacts is invalid")
        if "repo.write" in capabilities and (allowed_kinds or required_kinds):
            errors.append(f"route `{name}` readonly_artifacts requires read-only capabilities")
    for code, task_type in follow_up_routes.items():
        route = routes.get(task_type)
        if not isinstance(route, dict):
            errors.append(f"friction follow-up route `{task_type}` for `{code}` is unknown")
            continue
        capabilities = route.get("capabilities")
        execution_modes = route.get("execution_modes")
        if not isinstance(capabilities, list) or "repo.write" in capabilities or not isinstance(execution_modes, list) or "single_work_lane" not in execution_modes:
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
