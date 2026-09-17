from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "local_herdr_attempt_contract", ROOT / "scripts" / "herdr_attempt_contract.py"
)
assert _SPEC is not None and _SPEC.loader is not None
contract = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(contract)


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


def test_assignment_id_uses_repository_plan_and_lane_identity() -> None:
    first = contract.assignment_id("repo", "plan", "lane-7")
    second = contract.assignment_id("repo", "plan", "lane-7")

    assert first == second
    assert first != contract.assignment_id("other-repo", "plan", "lane-7")
    assert first != contract.assignment_id("repo", "other-plan", "lane-7")
    assert first != contract.assignment_id("repo", "plan", "lane-8")


def test_normalize_attempt_adds_coordinated_assignment_identity() -> None:
    attempt = contract.normalize_attempt(
        {
            "lane_id": "lane-7",
            "task": "run verification",
            "attempt_id": "attempt-3",
            "repository_identity": "repo",
            "plan_identity": "plan",
        }
    )

    assert attempt["assignment_id"] == contract.assignment_id("repo", "plan", "lane-7")


@pytest.mark.parametrize(
    ("claim", "prior_attempt_known", "receipt", "cleanup_confirmed", "descendants_retired", "expected"),
    [
        (None, False, None, None, None, "UNCLAIMED"),
        (None, True, None, None, None, "RECOVERY_REQUIRED"),
        ({"state": "active"}, False, None, None, None, "ACTIVE"),
        ({"state": "active"}, False, {"state": "unknown"}, None, None, "ACTIVE"),
        ({"state": "active"}, False, {"state": "confirmed", "worker_state": "exited", "worker_exit_code": 0, "cleanup_state": "removed", "descendant_state": "terminated", "recovery_required": False}, True, True, "SETTLED"),
        ({"state": "settled"}, False, {"state": "confirmed", "worker_state": "exited", "worker_exit_code": 0, "cleanup_state": "removed", "descendant_state": "terminated", "recovery_required": False}, True, True, "SETTLED"),
        ({"state": "settled"}, False, None, None, None, "RECOVERY_REQUIRED"),
        ({"state": "invalid"}, False, None, None, None, "RECOVERY_REQUIRED"),
    ],
)
def test_derive_lifecycle_state_preserves_unknown_evidence(
    claim, prior_attempt_known, receipt, cleanup_confirmed, descendants_retired, expected
) -> None:
    assert contract.derive_lifecycle_state(
        claim,
        prior_attempt_known=prior_attempt_known,
        receipt=receipt,
        cleanup_confirmed=cleanup_confirmed,
        descendants_retired=descendants_retired,
    ) == expected


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("UNCLAIMED", "ELIGIBLE"),
        ("ACTIVE", "BLOCKED"),
        ("SETTLED", "ELIGIBLE"),
        ("RECOVERY_REQUIRED", "RECONCILE"),
    ],
)
def test_eligibility_action_mapping(state: str, expected: str) -> None:
    assert contract.eligibility_action(state) == expected


def test_same_attempt_is_idempotent_only_for_full_binding_match() -> None:
    binding = {
        "attempt_id": "attempt-3",
        "assignment_id": "assignment-1",
        "repository_identity": "repo",
        "executor": "deepagents",
        "task_sha256": "task",
        "grant_digest": "grant",
    }

    assert contract.same_attempt_binding(binding, dict(binding)) is True
    changed = dict(binding, assignment_id="assignment-2")
    assert contract.same_attempt_binding(binding, changed) is False
    incomplete = dict(binding)
    del incomplete["grant_digest"]
    assert contract.same_attempt_binding(binding, incomplete) is False


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


def test_normalize_attempt_rejects_string_prior_attempt_known() -> None:
    with pytest.raises(contract.AttemptContractError, match="prior_attempt_known"):
        contract.normalize_attempt(
            {
                "lane_id": "lane-7",
                "task": "run verification",
                "attempt_id": "attempt-3",
                "prior_attempt_known": "false",
            }
        )
