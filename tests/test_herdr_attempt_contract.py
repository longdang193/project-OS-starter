from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from scripts import herdr_attempt_contract as contract


ROOT = Path(__file__).parents[1]


def test_contract_module_uses_stdlib_only() -> None:
    tree = ast.parse(
        (ROOT / "scripts" / "herdr_attempt_contract.py").read_text(encoding="utf-8")
    )
    allowed = {"__future__", "hashlib", "json", "math", "re", "collections", "numbers", "typing"}
    imports = [
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ] + [
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]
    assert all(name in allowed for name in imports)


def test_default_runtime_grant_is_stable_and_native() -> None:
    assert contract.default_runtime_grant() == {
        "turns": {"requested": "native", "effective": "native", "enforcement": "native"},
        "wall_clock_seconds": {
            "requested": "native",
            "effective": "native",
            "enforcement": "native",
        },
        "mcp_select": [],
        "delegation": {"child_agents": "deny"},
    }


def test_normalize_attempt_keeps_identity_fields_separate() -> None:
    attempt = contract.normalize_attempt(
        {
            "lane_id": "lane-7",
            "task": "run verification",
            "attempt_id": "attempt-3",
            "grant_child_agents": "allow",
        }
    )

    assert attempt["lane_id"] == "lane-7"
    assert attempt["attempt_id"] == "attempt-3"
    assert attempt["task_sha256"] == hashlib.sha256(b"run verification").hexdigest()
    assert attempt["lane_id"] != attempt["attempt_id"]
    assert attempt["runtime_grant"]["delegation"] == {"child_agents": "allow"}


def test_normalize_attempt_rejects_task_hash_mismatch() -> None:
    with pytest.raises(contract.AttemptContractError, match="does not match"):
        contract.normalize_attempt(
            {
                "lane_id": "lane-7",
                "task": "run verification",
                "task_sha256": "0" * 64,
                "attempt_id": "attempt-3",
            }
        )


def test_grant_digest_ignores_dynamic_timing_fields() -> None:
    grant = contract.normalize_runtime_grant(
        {
            "turns": {"requested": "native"},
            "wall_clock_seconds": {"requested": "native"},
            "mcp_select": ["z.query", "a.query"],
            "delegation": {"child_agents": "allow"},
            "attempt_started_at": 10,
            "attempt_deadline": 1810,
        },
        executor="deepagents",
    )
    changed_timing = dict(grant, attempt_started_at=999, settlement_deadline=2000)

    assert contract.grant_digest("deepagents", grant) == contract.grant_digest(
        "deepagents", changed_timing
    )
    assert contract.grant_digest("codex", grant) != contract.grant_digest("deepagents", grant)


def test_grant_digest_changes_for_stable_grant_binding() -> None:
    native = contract.default_runtime_grant()
    changed = contract.normalize_runtime_grant(
        {"wall_clock_seconds": {"requested": 600}}, executor="deepagents"
    )

    assert contract.grant_digest("deepagents", native) != contract.grant_digest(
        "deepagents", changed
    )


@pytest.mark.parametrize(
    ("allowance", "remaining", "reserve", "expected"),
    [
        (1000, 1000, 30, 420),
        (300, 1000, 30, 300),
        (1000, 450, 30, 420),
        (1000, 29, 30, 0),
    ],
)
def test_resolve_attempt_budget_native_minimum(
    allowance: int,
    remaining: int,
    reserve: int,
    expected: int,
) -> None:
    if expected == 0:
        with pytest.raises(contract.AttemptContractError, match="no worker budget"):
            contract.resolve_attempt_budget("native", allowance, remaining, reserve)
    else:
        assert contract.resolve_attempt_budget("native", allowance, remaining, reserve) == expected


def test_resolve_attempt_budget_rejects_numeric_grant_that_does_not_fit() -> None:
    with pytest.raises(contract.AttemptContractError, match="does not fit"):
        contract.resolve_attempt_budget(500, 1000, 450, 30)


def test_resolve_attempt_budget_rejects_numeric_grant_over_whole_attempt_ceiling() -> None:
    with pytest.raises(contract.AttemptContractError, match="1800"):
        contract.resolve_attempt_budget(1800, 2000, 1800, 30)


def test_resolve_attempt_budget_caps_remaining_time_to_whole_attempt_ceiling() -> None:
    assert contract.resolve_attempt_budget("native", 2000, 5000, 30) == 420


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, "1.5", ""])
def test_resolve_attempt_budget_rejects_non_strict_numeric_grants(value: object) -> None:
    with pytest.raises(contract.AttemptContractError):
        contract.resolve_attempt_budget(value, 1000, 1000, 30)


def test_remaining_attempt_seconds_enforces_ceiling_boundary() -> None:
    assert contract.remaining_attempt_seconds(0) == 1800
    assert contract.remaining_attempt_seconds(1800) == 0
    with pytest.raises(contract.AttemptContractError, match="ceiling"):
        contract.remaining_attempt_seconds(1801)
