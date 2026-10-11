from pathlib import Path

import pytest

from scripts.secretary_evidence_adapter import (
    build_evidence_bundle,
    load_reusable_target,
)


def launcher(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "task_id": "task-1",
        "plan_revision": "plan-1",
        "attempt_id": "attempt-1",
        "run_id": "run-1",
        "provider": "9router",
        "disposition": "BLOCKED_CAPABILITY",
        "evidence_provenance": "capability-probe",
        "receipt": {
            "disposition": "BLOCKED_CAPABILITY",
            "evidence_provenance": "capability-probe",
        },
    }
    value.update(overrides)
    return value


def test_adapter_keeps_unattributed_provider_usage_separate() -> None:
    bundle = build_evidence_bundle(
        launcher(),
        target={
            "session": "default",
            "pane": "auto",
            "pane_id": "w56:p1",
            "workspace_id": "w56",
            "cwd": "C:/worktree",
        },
        provider={
            "source": "9router-local-read-only",
            "disposition": "observed_window",
            "attribution": "time-window",
            "input_tokens": 100,
            "output_tokens": 20,
            "cache_read_input_tokens": 80,
            "cost": 0.01,
        },
    )

    assert bundle["readiness"] == "BLOCKED_CAPABILITY"
    assert bundle["provider_usage"]["secretary_attributed"] is False
    assert bundle["provider_usage"]["economics"] == "partial-unattributed"
    assert bundle["secretary_receipt"]["state"] == "missing"
    assert bundle["probe_target"]["selector"] == {"session": "default", "pane": "auto"}


def test_adapter_only_joins_provider_usage_on_existing_run_identifier() -> None:
    bundle = build_evidence_bundle(
        launcher(disposition="READY", evidence_provenance="live-attributed"),
        provider={
            "provider": "9router",
            "run_id": "run-1",
            "disposition": "matched",
            "input_tokens": 100,
        },
    )

    assert bundle["provider_usage"]["secretary_attributed"] is False
    assert bundle["provider_usage"]["join"]["matching_key"] == "run_id"
    assert bundle["provider_usage"]["economics"] == "partial-unattributed"
    assert bundle["readiness"] == "BLOCKED_CAPABILITY"


def test_adapter_rejects_malformed_live_receipt_before_attribution() -> None:
    bundle = build_evidence_bundle(
        launcher(
            disposition="READY",
            evidence_provenance="live-attributed",
            receipt={"valid": True, "evidence_provenance": "live-attributed"},
        ),
        provider={"provider": "9router", "run_id": "run-1", "input_tokens": 100},
    )

    assert bundle["secretary_receipt"]["state"] == "missing"
    assert bundle["provider_usage"]["secretary_attributed"] is False
    assert bundle["readiness"] == "BLOCKED_CAPABILITY"


def test_load_reusable_target_requires_named_session_and_workspace_pane(tmp_path: Path) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text(
        '{"session":"default","pane":"auto","pane_id":"w56:p1",'
        '"workspace_id":"w56","cwd":"C:/worktree"}',
        encoding="utf-8",
    )

    assert load_reusable_target(target_path)["pane_id"] == "w56:p1"

    target_path.write_text(
        '{"session":"auto","pane":"auto","pane_id":"w56:p1",'
        '"workspace_id":"w56","cwd":"C:/worktree"}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="named session"):
        load_reusable_target(target_path)


def test_adapter_does_not_treat_blocked_receipt_as_present() -> None:
    bundle = build_evidence_bundle(
        launcher(
            receipt={
                "valid": True,
                "disposition": "BLOCKED_CAPABILITY",
                "evidence_provenance": "capability-probe",
            }
        )
    )

    assert bundle["secretary_receipt"] == {
        "state": "missing",
        "reason": "runtime_structured_receipt_missing",
    }
