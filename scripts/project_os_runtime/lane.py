"""Immutable boundary for normalized dispatch lanes."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterator, Mapping, Sequence
from hashlib import sha256
import math
from types import MappingProxyType
from typing import Any

from .attempt import assignment_id, execution_binding_digest, grant_digest, normalize_runtime_grant
from .capabilities import capability_digest, normalize_local_capabilities, DEFAULT_LOCAL_CAPABILITIES

_REQUIRED_FIELDS = (
    "lane_id",
    "repository_identity",
    "plan_identity",
    "task",
    "executor",
    "profile",
    "worktree",
    "expected_base",
    "session",
    "pane",
    "allowed_write_set",
    "dependencies",
    "dependency_ready",
    "fixed_contracts",
    "mutable_resources",
    "grant_turns",
    "grant_wall_clock_seconds",
    "grant_child_agents",
    "mcp_select",
    "remaining_authorized_task_allowance",
)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _text(raw: Mapping[str, Any], name: str) -> str:
    value = raw.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _sequence(raw: Mapping[str, Any], name: str) -> tuple[Any, ...]:
    value = raw.get(name)
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
    ):
        raise ValueError(f"{name} must be a sequence")
    return tuple(_freeze(item) for item in value)


def _remaining_authority(raw: Mapping[str, Any]) -> int | float:
    value = raw["remaining_authorized_task_allowance"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("remaining_authorized_task_allowance must be a finite non-negative number")
    if not math.isfinite(value) or value < 0:
        raise ValueError("remaining_authorized_task_allowance must be a finite non-negative number")
    return value


@dataclass(frozen=True, slots=True)
class PreparedLane(Mapping[str, Any]):
    lane_id: str
    repository_identity: str
    plan_identity: str
    task: str
    executor: str
    profile: str
    expected_base: str
    session: str
    pane: str
    allowed_write_set: tuple[Any, ...]
    dependencies: tuple[Any, ...]
    dependency_ready: bool
    fixed_contracts: tuple[Any, ...]
    mutable_resources: tuple[Any, ...]
    mcp_select: tuple[str, ...]
    assignment_id: str
    task_hash: str
    grant: Mapping[str, Any]
    grant_digest: str
    capabilities: Mapping[str, Any]
    worktree: str
    target: str | None
    remaining_authority: int | float
    name: str | None
    codex_home: str | None
    prior_attempt_known: bool
    attempt_deadline: int | float | None
    plan_revision: str | None
    execution_binding_digest: str | None
    structurally_ready: bool
    accepted_prerequisites: Mapping[str, Any]

    _MAPPING_FIELDS = (
        "lane_id", "repository_identity", "plan_identity", "task", "executor",
        "profile", "worktree", "expected_base", "session", "pane",
        "allowed_write_set", "dependencies", "dependency_ready", "fixed_contracts",
        "mutable_resources", "mcp_select", "assignment_id", "task_sha256",
        "runtime_grant", "grant_digest", "local_capabilities", "target", "name",
        "codex_home", "prior_attempt_known", "attempt_deadline",
        "remaining_authorized_task_allowance", "grant_turns",
        "grant_wall_clock_seconds", "grant_child_agents",
        "plan_revision", "execution_binding_digest", "structurally_ready",
        "accepted_prerequisites",
    )

    def __getitem__(self, key: str) -> Any:
        if key == "task_sha256":
            return self.task_hash
        if key == "runtime_grant":
            return self.grant
        if key == "local_capabilities":
            return self.capabilities
        if key == "remaining_authorized_task_allowance":
            return self.remaining_authority
        if key == "grant_turns":
            return self.grant["turns"]["requested"]
        if key == "grant_wall_clock_seconds":
            return self.grant["wall_clock_seconds"]["requested"]
        if key == "grant_child_agents":
            return self.grant["delegation"]["child_agents"]
        if key in self._MAPPING_FIELDS:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self._MAPPING_FIELDS)

    def __len__(self) -> int:
        return len(self._MAPPING_FIELDS)

    def to_dict(self) -> dict[str, Any]:
        return _thaw(dict(self))

    @property
    def task_sha256(self) -> str:
        return self.task_hash

    @property
    def runtime_grant(self) -> Mapping[str, Any]:
        return self.grant

    @property
    def remaining_authorized_task_allowance(self) -> int | float:
        return self.remaining_authority


def prepare_lane(raw_descriptor: Mapping[str, Any]) -> PreparedLane:
    if not isinstance(raw_descriptor, Mapping):
        raise ValueError("lane descriptor must be an object")
    missing = [field for field in _REQUIRED_FIELDS if field not in raw_descriptor]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")

    lane_id = _text(raw_descriptor, "lane_id")
    repository = _text(raw_descriptor, "repository_identity")
    plan = _text(raw_descriptor, "plan_identity")
    task = _text(raw_descriptor, "task")
    executor = _text(raw_descriptor, "executor")
    profile = _text(raw_descriptor, "profile")
    worktree = _text(raw_descriptor, "worktree")
    expected_base = _text(raw_descriptor, "expected_base")
    session = _text(raw_descriptor, "session")
    pane = _text(raw_descriptor, "pane")
    if not isinstance(raw_descriptor["dependency_ready"], bool):
        raise ValueError("dependency_ready must be boolean")
    prior_attempt_known = raw_descriptor.get("prior_attempt_known", False)
    if not isinstance(prior_attempt_known, bool):
        raise ValueError("prior_attempt_known must be boolean")
    attempt_deadline = raw_descriptor.get("attempt_deadline")
    if attempt_deadline is not None and (
        isinstance(attempt_deadline, bool)
        or not isinstance(attempt_deadline, (int, float))
        or not math.isfinite(float(attempt_deadline))
    ):
        raise ValueError("attempt_deadline must be finite when provided")
    target = raw_descriptor.get("target")
    if target is not None and (not isinstance(target, str) or not target.strip()):
        raise ValueError("target must be a non-empty string when provided")
    plan_revision = raw_descriptor.get("plan_revision")
    if plan_revision is not None and (not isinstance(plan_revision, str) or not plan_revision.strip()):
        raise ValueError("plan_revision must be a non-empty string when provided")
    binding_digest = raw_descriptor.get("execution_binding_digest")
    if binding_digest is not None and (not isinstance(binding_digest, str) or not binding_digest.strip()):
        raise ValueError("execution_binding_digest must be a non-empty string when provided")
    structurally_ready = raw_descriptor.get("structurally_ready", raw_descriptor["dependency_ready"])
    if not isinstance(structurally_ready, bool):
        raise ValueError("structurally_ready must be boolean")
    accepted_prerequisites = raw_descriptor.get("accepted_prerequisites", {})
    if not isinstance(accepted_prerequisites, Mapping):
        raise ValueError("accepted_prerequisites must be a mapping")

    computed_assignment_id = assignment_id(repository, plan, lane_id)
    supplied_assignment_id = raw_descriptor.get("assignment_id")
    if supplied_assignment_id is not None and supplied_assignment_id != computed_assignment_id:
        raise ValueError("assignment_id does not match coordinated identity")

    selectors = raw_descriptor["mcp_select"]
    if not isinstance(selectors, Sequence) or isinstance(selectors, (str, bytes, bytearray)):
        raise ValueError("MCP selectors must be a sequence of strings")
    selectors = [item.strip() for value in selectors for item in value.split(",")] if all(isinstance(item, str) for item in selectors) else selectors
    if not all(isinstance(item, str) and item for item in selectors):
        raise ValueError("MCP selectors cannot be empty")
    selectors = sorted(set(selectors))

    nested = raw_descriptor.get("runtime_grant")
    if isinstance(nested, Mapping) and "mcp_select" in nested:
        nested_selectors = nested["mcp_select"]
        if (
            not isinstance(nested_selectors, Sequence)
            or isinstance(nested_selectors, (str, bytes, bytearray))
            or not all(isinstance(item, str) for item in nested_selectors)
        ):
            raise ValueError("MCP selectors must be a sequence of strings")
        nested_selectors = sorted(
            set(item.strip() for value in nested_selectors for item in value.split(","))
        )
        if nested_selectors != selectors:
            raise ValueError("conflicting top-level and nested MCP selectors")
    grant = normalize_runtime_grant(
        executor=executor,
        grant_turns=raw_descriptor["grant_turns"],
        grant_wall_clock_seconds=raw_descriptor["grant_wall_clock_seconds"],
        mcp_select=selectors,
        grant_child_agents=raw_descriptor["grant_child_agents"],
    )
    requested_value = raw_descriptor.get("local_capabilities", [])
    requested = requested_value.get("requested", []) if isinstance(requested_value, Mapping) else requested_value
    requested = normalize_local_capabilities(requested)
    effective = requested or list(DEFAULT_LOCAL_CAPABILITIES)
    capabilities = MappingProxyType({
        "requested": tuple(requested),
        "effective": tuple(effective),
        "verification_commands": tuple(effective),
        "source_task_sha256": sha256(task.encode("utf-8")).hexdigest(),
        "digest": capability_digest(effective),
    })
    return PreparedLane(
        lane_id=lane_id,
        repository_identity=repository,
        plan_identity=plan,
        task=task,
        executor=executor,
        profile=profile,
        expected_base=expected_base,
        session=session,
        pane=pane,
        allowed_write_set=_sequence(raw_descriptor, "allowed_write_set"),
        dependencies=_sequence(raw_descriptor, "dependencies"),
        dependency_ready=raw_descriptor["dependency_ready"],
        fixed_contracts=_sequence(raw_descriptor, "fixed_contracts"),
        mutable_resources=_sequence(raw_descriptor, "mutable_resources"),
        mcp_select=tuple(selectors),
        assignment_id=computed_assignment_id,
        task_hash=sha256(task.encode("utf-8")).hexdigest(),
        grant=_freeze(grant),
        grant_digest=grant_digest(executor, grant),
        capabilities=capabilities,
        worktree=worktree,
        target=target,
        remaining_authority=_remaining_authority(raw_descriptor),
        name=raw_descriptor.get("name") if isinstance(raw_descriptor.get("name"), str) else None,
        codex_home=raw_descriptor.get("codex_home") if isinstance(raw_descriptor.get("codex_home"), str) else None,
        prior_attempt_known=prior_attempt_known,
        attempt_deadline=attempt_deadline,
        plan_revision=plan_revision,
        execution_binding_digest=binding_digest,
        structurally_ready=structurally_ready,
        accepted_prerequisites=_freeze(accepted_prerequisites),
    )


__all__ = ["PreparedLane", "prepare_lane"]
