from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any

WHOLE_ATTEMPT_WALL_CLOCK_SECONDS = 1800
NATIVE_WORKER_WALL_CLOCK_SECONDS = 420
SETTLEMENT_RESERVE_SECONDS = 30
NATIVE_GRANT_VALUE = "native"
CHILD_AGENT_GRANT_VALUES = frozenset({"allow", "deny"})
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class AttemptContractError(ValueError):
    """Raised when attempt contract values cannot be normalized."""


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise AttemptContractError(f"{label} must be a positive integer")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
    else:
        raise AttemptContractError(f"{label} must be a positive integer")
    if parsed <= 0:
        raise AttemptContractError(f"{label} must be a positive integer")
    return parsed


def _non_negative_real(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise AttemptContractError(f"{label} must be a finite non-negative number")
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise AttemptContractError(f"{label} must be a finite non-negative number")
    return parsed


def _grant_value(value: object, label: str) -> int | str:
    if value is None or (
        isinstance(value, str) and value.strip().casefold() == NATIVE_GRANT_VALUE
    ):
        return NATIVE_GRANT_VALUE
    return _positive_integer(value, label)


def _selectors(value: object) -> list[str]:
    if value is None:
        return []
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
        or not all(isinstance(item, str) for item in value)
    ):
        raise AttemptContractError("mcp_select must be a sequence of strings")
    selected = [item.strip() for value_item in value for item in value_item.split(",")]
    if not all(selected):
        raise AttemptContractError("mcp_select cannot contain empty selectors")
    return sorted(set(selected))


def _child_agents(value: object) -> str:
    selected = "deny" if value is None else value
    if not isinstance(selected, str) or selected.strip().casefold() not in CHILD_AGENT_GRANT_VALUES:
        raise AttemptContractError("grant_child_agents must be `allow` or `deny`")
    return selected.strip().casefold()


def _requested_value(grant: Mapping[str, Any], name: str, default: object) -> object:
    value = grant.get(name, default)
    if isinstance(value, Mapping):
        return value.get("requested", default)
    return value


def normalize_runtime_grant(
    grant: Mapping[str, Any] | None = None,
    *,
    executor: str = "deepagents",
    grant_turns: object = None,
    grant_wall_clock_seconds: object = None,
    grant_child_agents: object = None,
    mcp_select: object = None,
) -> dict[str, Any]:
    """Normalize stable Runtime Grant fields without reading process or clock state."""
    if grant is not None and not isinstance(grant, Mapping):
        raise AttemptContractError("grant must be a mapping")
    values = {} if grant is None else dict(grant)
    if not isinstance(executor, str) or not executor.strip():
        raise AttemptContractError("executor must be a non-empty string")
    executor = executor.strip()
    turns = _grant_value(
        _requested_value(values, "turns", grant_turns),
        "grant_turns",
    )
    wall_clock = _grant_value(
        _requested_value(values, "wall_clock_seconds", grant_wall_clock_seconds),
        "grant_wall_clock_seconds",
    )
    if executor == "codex" and turns != NATIVE_GRANT_VALUE:
        raise AttemptContractError("Codex numeric turn budget is unsupported; use `native`")
    if executor == "codex" and wall_clock != NATIVE_GRANT_VALUE:
        raise AttemptContractError("Codex numeric wall-clock budget is unsupported; use `native`")
    if (
        wall_clock != NATIVE_GRANT_VALUE
        and wall_clock > WHOLE_ATTEMPT_WALL_CLOCK_SECONDS
    ):
        raise AttemptContractError(
            "grant_wall_clock_seconds cannot exceed the 1800-second whole-attempt ceiling"
        )
    delegation = values.get("delegation")
    nested_child_agents = (
        delegation.get("child_agents")
        if isinstance(delegation, Mapping)
        else grant_child_agents
    )
    selectors = _selectors(values.get("mcp_select", mcp_select))
    return {
        "turns": {
            "requested": turns,
            "effective": turns,
            "enforcement": "native" if turns == NATIVE_GRANT_VALUE else "runtime",
        },
        "wall_clock_seconds": {
            "requested": wall_clock,
            "effective": wall_clock,
            "enforcement": "native" if wall_clock == NATIVE_GRANT_VALUE else "runtime",
        },
        "mcp_select": selectors,
        "delegation": {"child_agents": _child_agents(values.get("child_agents", nested_child_agents))},
    }


def default_runtime_grant(executor: str = "deepagents") -> dict[str, Any]:
    return normalize_runtime_grant(executor=executor)


def _stable_grant_binding(
    executor: str,
    runtime_grant: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = normalize_runtime_grant(runtime_grant, executor=executor)
    canonical_executor = executor.strip()
    return {
        "executor": canonical_executor,
        "turns": normalized["turns"]["requested"],
        "wall_clock_seconds": normalized["wall_clock_seconds"]["requested"],
        "mcp_select": normalized["mcp_select"],
        "delegation": normalized["delegation"],
    }


def grant_digest(executor: str, runtime_grant: Mapping[str, Any]) -> str:
    payload = json.dumps(
        _stable_grant_binding(executor, runtime_grant),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_attempt(attempt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(attempt, Mapping):
        raise AttemptContractError("attempt must be a mapping")
    values = dict(attempt)
    for field in ("lane_id", "attempt_id"):
        value = values.get(field)
        if not isinstance(value, str) or not value.strip():
            raise AttemptContractError(f"{field} must be a non-empty string")
        values[field] = value.strip()
    task = values.get("task")
    if not isinstance(task, str) or not task:
        raise AttemptContractError("task must be a non-empty string")
    task_sha256 = values.get("task_sha256")
    computed_sha256 = hashlib.sha256(task.encode("utf-8")).hexdigest()
    if task_sha256 is None:
        task_sha256 = computed_sha256
    if not isinstance(task_sha256, str) or not _SHA256_PATTERN.fullmatch(task_sha256):
        raise AttemptContractError("task_sha256 must be a lowercase SHA-256 digest")
    if task_sha256 != computed_sha256:
        raise AttemptContractError("task_sha256 does not match task")
    executor = values.get("executor", "deepagents")
    runtime_grant = normalize_runtime_grant(
        values.get("runtime_grant"),
        executor=executor,
        grant_turns=values.get("grant_turns"),
        grant_wall_clock_seconds=values.get("grant_wall_clock_seconds"),
        grant_child_agents=values.get("grant_child_agents"),
        mcp_select=values.get("mcp_select"),
    )
    values.update(
        {
            "task_sha256": task_sha256,
            "runtime_grant": runtime_grant,
            "grant_digest": grant_digest(executor, runtime_grant),
        }
    )
    return values


def remaining_attempt_seconds(
    elapsed_seconds: Real,
    *,
    ceiling_seconds: Real = WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
) -> float:
    ceiling = _non_negative_real(ceiling_seconds, "ceiling_seconds")
    elapsed = _non_negative_real(elapsed_seconds, "elapsed_seconds")
    if elapsed > ceiling:
        raise AttemptContractError("elapsed_seconds exceeds whole-attempt ceiling")
    return ceiling - elapsed


def resolve_attempt_budget(
    grant_wall_clock_seconds: object,
    remaining_authorized_task_allowance: Real,
    remaining_attempt_time: Real,
    settlement_reserve_seconds: Real = SETTLEMENT_RESERVE_SECONDS,
) -> int | float:
    """Resolve worker budget while retaining whole-attempt settlement time."""
    authorized = _non_negative_real(
        remaining_authorized_task_allowance,
        "remaining_authorized_task_allowance",
    )
    remaining = min(
        _non_negative_real(remaining_attempt_time, "remaining_attempt_time"),
        WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
    )
    reserve = _non_negative_real(settlement_reserve_seconds, "settlement_reserve_seconds")
    available = min(authorized, remaining - reserve)
    requested = _grant_value(grant_wall_clock_seconds, "grant_wall_clock_seconds")
    if available <= 0:
        raise AttemptContractError("attempt has no worker budget after settlement reserve")
    if requested == NATIVE_GRANT_VALUE:
        return min(NATIVE_WORKER_WALL_CLOCK_SECONDS, available)
    if requested > available:
        raise AttemptContractError(
            "numeric wall-clock grant does not fit 1800-second whole-attempt ceiling, "
            "remaining authorized allowance, and attempt time"
        )
    return requested


_normalize_runtime_grant = normalize_runtime_grant
_grant_digest = grant_digest
_normalize_attempt = normalize_attempt
_resolve_attempt_budget = resolve_attempt_budget

__all__ = [
    "AttemptContractError",
    "CHILD_AGENT_GRANT_VALUES",
    "NATIVE_GRANT_VALUE",
    "NATIVE_WORKER_WALL_CLOCK_SECONDS",
    "SETTLEMENT_RESERVE_SECONDS",
    "WHOLE_ATTEMPT_WALL_CLOCK_SECONDS",
    "default_runtime_grant",
    "grant_digest",
    "normalize_attempt",
    "normalize_runtime_grant",
    "remaining_attempt_seconds",
    "resolve_attempt_budget",
]
