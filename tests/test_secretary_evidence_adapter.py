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


def valid_receipt(*, session_id: str = "session-1") -> dict[str, object]:
    binding = {
        "pair_id": "run-1",
        "arm": "candidate",
        "run_id": "run-1",
        "attempt_id": "attempt-1",
        "task_id": "task-1",
        "plan_revision": "plan-1",
        "repository_identity": "repo-1",
        "plan_identity": "plan-identity-1",
        "git_revision": "a" * 40,
        "worktree": "C:/worktree",
        "workstream": "secretary-live-runtime",
        "checkpoint": "plan-1:task-1",
        "provider": "9router",
        "model": "gpt-test",
        "controller_id": "cos-supervised",
        "session_id": session_id,
    }
    producers = {
        "launch": "herdr_main_launcher",
        "secretary": "secretary_live_runtime",
        "task_result": "dcode-project",
        "settlement": "project_os_runtime.attempt",
        "acceptance": "cos",
    }
    sources = {
        name: {
            "producer": producer,
            "source_ref": f"runtime://{name}/run-1",
            "source_digest": "a" * 64,
            **binding,
        }
        for name, producer in producers.items()
    }
    return {
        **binding,
        "valid": True,
        "evidence_provenance": "live-attributed",
        "timestamps": {
            "run_started": "2026-10-10T10:00:00+00:00",
            "cos_entry": "2026-10-10T10:00:01+00:00",
            "secretary_entry": "2026-10-10T10:00:02+00:00",
            "worker_entry": "2026-10-10T10:00:03+00:00",
            "publication": "2026-10-10T10:00:04+00:00",
            "settlement": "2026-10-10T10:00:05+00:00",
            "acceptance": "2026-10-10T10:00:06+00:00",
            "secretary_exit": "2026-10-10T10:00:07+00:00",
            "cos_exit": "2026-10-10T10:00:08+00:00",
            "run_finished": "2026-10-10T10:00:09+00:00",
        },
        "metrics": {
            "cos_turns": 0,
            "secretary_turns": 1,
            "human_interventions": 0,
            "publication_success": True,
            "settlement_proven": True,
            "acceptance_decision": "PASS",
            "token_usage": "unknown",
            "cost": "unknown",
        },
        "sources": sources,
    }


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
    assert bundle["probe_readiness"] == "BLOCKED_CAPABILITY"
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


def test_adapter_reports_valid_session_only_evidence_without_promoting_it() -> None:
    bundle = build_evidence_bundle(
        launcher(disposition="READY", evidence_provenance="live-attributed"),
        provider={
            "provider": "9router",
            "session_id": "session-1",
            "attribution": "session",
            "coverage": "complete",
            "input_tokens": 100,
        },
    )

    assert bundle["provider_usage"]["state"] == "observed"
    assert bundle["provider_usage"]["attribution"] == "session"
    assert bundle["provider_usage"]["secretary_attributed"] is False
    assert bundle["provider_usage"]["economics"] == "partial-unattributed"


def test_adapter_does_not_promote_valid_receipt_without_session_bridge() -> None:
    bundle = build_evidence_bundle(
        launcher(
            disposition="READY",
            evidence_provenance="live-attributed",
            receipt=valid_receipt(session_id="secretary-session"),
        ),
        provider={
            "provider": "9router",
            "session_id": "other-session",
            "attribution": "session",
            "coverage": "complete",
            "input_tokens": 100,
        },
    )

    assert bundle["secretary_receipt"]["state"] == "present"
    assert bundle["provider_usage"]["session_bridge"] is False
    assert bundle["provider_usage"]["secretary_attributed"] is False


def test_adapter_keeps_session_bridge_at_session_attribution_without_run_or_attempt() -> None:
    bundle = build_evidence_bundle(
        launcher(
            disposition="READY",
            evidence_provenance="live-attributed",
            receipt=valid_receipt(session_id="session-1"),
        ),
        provider={
            "provider": "9router",
            "session_id": "session-1",
            "attribution": "session",
            "coverage": "complete",
            "input_tokens": 100,
        },
    )

    assert bundle["provider_usage"]["session_bridge"] is True
    assert bundle["provider_usage"]["secretary_attributed"] is False
    assert bundle["provider_usage"]["attribution"] == "session"
    assert bundle["provider_usage"]["economics"] == "partial-unattributed"


def test_adapter_promotes_exact_run_join_with_complete_session_coverage() -> None:
    bundle = build_evidence_bundle(
        launcher(
            disposition="READY",
            evidence_provenance="live-attributed",
            receipt=valid_receipt(session_id="session-1"),
        ),
        provider={
            "provider": "9router",
            "session_id": "session-1",
            "run_id": "run-1",
            "attribution": "run",
            "coverage": "complete",
            "input_tokens": 100,
        },
    )

    assert bundle["provider_usage"]["secretary_attributed"] is True
    assert bundle["provider_usage"]["join"]["matching_key"] == "run_id"
    assert bundle["provider_usage"]["economics"] == "run-bound"


@pytest.mark.parametrize(
    "provider_identity",
    [
        {"run_id": "other-run", "attempt_id": "attempt-1"},
        {"run_id": "run-1", "attempt_id": "other-attempt"},
    ],
)
def test_adapter_does_not_promote_conflicting_provider_identifiers(
    provider_identity: dict[str, str],
) -> None:
    bundle = build_evidence_bundle(
        launcher(
            disposition="READY",
            evidence_provenance="live-attributed",
            receipt=valid_receipt(session_id="session-1"),
        ),
        provider={
            "provider": "9router",
            "session_id": "session-1",
            **provider_identity,
            "attribution": "run",
            "coverage": "complete",
            "input_tokens": 100,
        },
    )

    assert bundle["provider_usage"]["secretary_attributed"] is False
    assert bundle["provider_usage"]["join"]["state"] == "mismatch"
    assert bundle["provider_usage"]["economics"] == "partial-unattributed"


def test_adapter_does_not_promote_partial_session_coverage() -> None:
    bundle = build_evidence_bundle(
        launcher(
            disposition="READY",
            evidence_provenance="live-attributed",
            receipt=valid_receipt(session_id="session-1"),
        ),
        provider={
            "provider": "9router",
            "session_id": "session-1",
            "attribution": "session",
            "coverage": "partial",
            "input_tokens": 100,
        },
    )

    assert bundle["provider_usage"]["session_bridge"] is True
    assert bundle["provider_usage"]["secretary_attributed"] is False
    assert bundle["provider_usage"]["economics"] == "partial-unattributed"
