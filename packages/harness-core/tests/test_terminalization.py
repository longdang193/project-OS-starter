from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from harness_core import managed


ROOT = Path(__file__).resolve().parents[3]
BINDING = {
    "run_id": "terminalization-test",
    "attempt_id": "attempt-1",
    "lease_id": "lease-1",
    "lease_epoch": 1,
    "host_instance_id": "host-1",
}


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def request(run_id: str) -> dict[str, object]:
    return {
        "version": 5,
        "run_id": run_id,
        "task_type": "local_change",
        "execution_mode": "single_work_lane",
        "user_request": "Terminalize fixture.",
        "acceptance_criteria": [{"id": "diff", "kind": "check", "check": "diff"}],
        "allowed_paths": ["scripts/**", "tests/**"],
        "planned_write_paths": ["scripts/harness_task.py"],
        "base_ref": "HEAD",
    }


def host_observation(binding: dict[str, object], **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_id": "host_terminal_observation/v2",
        "observation_id": "observation-1",
        **binding,
        "lane_id": "primary",
        "source": "completed",
        "observed_at": "2026-08-09T12:00:00+00:00",
        "elapsed_seconds": 3.5,
        "provider_session_id": "thread-1",
        "provider_turn_id": "turn-1",
        "terminal_status": "completed",
        "item_states": [],
        "command_states": [],
        "final_claim_state": {
            "state": "valid",
            "response_hash": _digest({"kind": "claimed_result"}),
            "response_length": 25,
        },
        "error": None,
        "containment": {
            "state": "stopped",
            "job_id": "job-1",
            "root_processes": [{"pid": 123, "creation_id": "process-1"}],
            "active_process_count": 0,
            "termination_action": "none",
        },
        "stop_proof": {
            "state": "confirmed",
            "observed_at": "2026-08-09T12:00:01+00:00",
            "host_process": {"pid": 456, "creation_id": "host-process-1"},
            "cancellation_request_id": None,
        },
    }
    value.update(overrides)
    return value


def write_running_run(tmp_path: Path) -> tuple[str, dict[str, object]]:
    run_id = tmp_path.name
    current_request = request(run_id)
    packet = managed.resolve_managed_packet(
        ROOT,
        current_request,
        attempt_id="attempt-1",
        provider_runtime_binding={
            "provider_id": "codex_app_server",
            "host_api": 7,
            "contract_version": 7,
            "transport": "stdio",
            "lifecycle": "host_spawn",
            "protocol": "app-server-v1",
            "configuration_digest": "a" * 64,
            "readiness": "ready",
            "host_instance_id": "host-1",
        },
    )
    run = managed._new_run(current_request, run_id)
    attempt = managed._append_attempt(run, packet)
    packet_digest = _digest(packet)
    binding = {**BINDING, "run_id": run_id, "packet_sha256": packet_digest}
    attempt["execution_lease"] = {
        **binding,
        "issued_at": "2026-08-09T11:00:00+00:00",
        "expires_at": "2026-08-09T13:00:00+00:00",
        "state": "active",
    }
    attempt["dispatched_lane_ids"] = ["primary"]
    attempt["evidence"] = {
        "checks": [{"name": "diff", "exit_code": 0}],
        "criteria": [{"id": "diff", "status": "proven"}],
        "blockers": [],
    }
    policy = managed._load_policy(ROOT)
    managed._transition(run, policy["states"], "planned", "fixture")
    managed._transition(run, policy["states"], "running", "fixture")
    managed._write_run(ROOT, run)
    return run_id, binding


def test_terminalize_attempt_applies_and_replays_same_digest(tmp_path: Path) -> None:
    run_id, binding = write_running_run(tmp_path)
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    try:
        evidence = {"attempt_id": "attempt-1", "host_terminal_observations": [host_observation(binding)]}

        applied = managed.terminalize_attempt(ROOT, run_id, evidence)
        after_apply = path.read_bytes()
        replayed = managed.terminalize_attempt(ROOT, run_id, evidence)

        assert applied["terminalization"]["status"] == "applied"
        assert replayed["terminalization"]["status"] == "replayed"
        assert path.read_bytes() == after_apply
        run = json.loads(after_apply)
        assert run["state"] == "awaiting_decision"
        assert run["attempts"][0]["terminal_record"]["classification"] == "completed"
        assert run["attempts"][0]["outcome"]["reason"] == "verification_passed"
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_terminalize_attempt_rejects_conflicting_or_malformed_evidence_without_mutation(tmp_path: Path) -> None:
    run_id, binding = write_running_run(tmp_path)
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    try:
        evidence = {"attempt_id": "attempt-1", "host_terminal_observations": [host_observation(binding)]}
        managed.terminalize_attempt(ROOT, run_id, evidence)
        before = path.read_bytes()

        with pytest.raises(managed.HarnessError, match="attempt_already_terminal"):
            managed.terminalize_attempt(ROOT, run_id, {**evidence, "host_terminal_observations": [host_observation(binding, observation_id="observation-2")]})
        with pytest.raises(managed.HarnessError, match="terminalization evidence"):
            managed.terminalize_attempt(ROOT, run_id, {"attempt_id": "attempt-1", "outcome": "accepted"})

        assert path.read_bytes() == before
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_v2_dispatch_failure_routes_through_terminalization(tmp_path: Path) -> None:
    run_id, binding = write_running_run(tmp_path)
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    try:
        run = json.loads(path.read_text())
        attempt = run["attempts"][0]

        class ProviderFailure(RuntimeError):
            pass

        failure = ProviderFailure("provider failed")
        failure.host_terminal_observation = host_observation(
            binding,
            source="provider_failure",
            terminal_status="failed",
            error=None,
        )
        result = managed._record_dispatch_exception(
            ROOT,
            run,
            managed._load_policy(ROOT),
            attempt,
            failure,
            phase="dispatch",
        )

        stored = json.loads(path.read_text())["attempts"][0]
        assert result["outcome"]["reason"] == "dispatch_failed"
        assert stored["terminal_record"]["classification"] == "provider_failure"
        assert stored["execution_lease"]["state"] == "released"
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_terminalize_attempt_rejects_observation_after_lease_expiry(tmp_path: Path) -> None:
    run_id, binding = write_running_run(tmp_path)
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    try:
        before = path.read_bytes()
        evidence = {
            "attempt_id": "attempt-1",
            "host_terminal_observations": [host_observation(
                binding,
                observed_at="2026-08-09T13:00:01+00:00",
                stop_proof={
                    "state": "confirmed",
                    "observed_at": "2026-08-09T13:00:01+00:00",
                    "host_process": {"pid": 456, "creation_id": "host-process-1"},
                    "cancellation_request_id": None,
                },
            )],
        }

        with pytest.raises(managed.HarnessError, match="lease expiry"):
            managed.terminalize_attempt(ROOT, run_id, evidence)

        assert path.read_bytes() == before
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_cancellation_requires_persisted_request_and_stop_proof(tmp_path: Path) -> None:
    run_id, binding = write_running_run(tmp_path)
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    try:
        first = managed.request_attempt_cancellation(ROOT, run_id, {"attempt_id": "attempt-1", "actor": "operator-1", "reason": "stop"})
        second = managed.request_attempt_cancellation(ROOT, run_id, {"attempt_id": "attempt-1", "actor": "operator-1", "reason": "stop"})
        assert first["cancellation_request_id"] == second["cancellation_request_id"]

        observation = host_observation(
            binding,
            source="cancellation",
            terminal_status="cancelled",
            containment={
                "state": "stopped",
                "job_id": "job-1",
                "root_processes": [{"pid": 123, "creation_id": "process-1"}],
                "active_process_count": 0,
                "termination_action": "job_terminated",
            },
            stop_proof={
                "state": "confirmed",
                "observed_at": "2026-08-09T12:00:01+00:00",
                "host_process": {"pid": 456, "creation_id": "host-process-1"},
                "cancellation_request_id": first["cancellation_request_id"],
            },
        )
        result = managed.terminalize_attempt(ROOT, run_id, {"attempt_id": "attempt-1", "host_terminal_observations": [observation]})

        assert result["terminalization"]["status"] == "applied"
        assert json.loads(path.read_text())["attempts"][0]["outcome"]["reason"] == "cancelled"
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_cancellation_request_id_reaches_active_host_lanes(tmp_path: Path) -> None:
    run_id, _binding = write_running_run(tmp_path)
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    try:
        cancellation = managed.request_attempt_cancellation(
            ROOT,
            run_id,
            {"attempt_id": "attempt-1", "actor": "operator-1", "reason": "stop"},
        )
        run = json.loads(path.read_text())
        calls: list[tuple[object, str | None]] = []

        class Adapter:
            def cancel_lane(self, handle: object, cancellation_request_id: str | None) -> None:
                calls.append((handle, cancellation_request_id))

        lane = {"lane_id": "work"}
        handle = object()
        managed._cancel_active_lanes(ROOT, run, run["attempts"][0], Adapter(), [(lane, handle)], phase="dispatch")

        assert calls == [(handle, cancellation["cancellation_request_id"])]
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_expired_crash_observer_blocks_orphans_then_terminalizes_cleanup_proof(tmp_path: Path) -> None:
    run_id, binding = write_running_run(tmp_path)
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    try:
        run = json.loads(path.read_text())
        run["attempts"][0]["execution_lease"]["expires_at"] = "2026-08-09T11:30:00+00:00"
        managed._write_run(ROOT, run)
        blocked = managed.terminalize_attempt(
            ROOT,
            run_id,
            {
                "attempt_id": "attempt-1",
                "host_terminal_observations": [],
                "recovery_observation": {
                    "lease_id": "lease-1",
                    "lease_epoch": 1,
                    "host_instance_id": "host-1",
                    "observed_at": "2026-08-09T12:00:00+00:00",
                    "host_process_absent": False,
                    "root_processes_absent": False,
                },
            },
        )
        assert blocked["terminalization"]["status"] == "recovery_blocked"
        assert json.loads(path.read_text())["state"] == "orphaned"

        terminalized = managed.terminalize_attempt(
            ROOT,
            run_id,
            {
                "attempt_id": "attempt-1",
                "host_terminal_observations": [],
                "recovery_observation": {
                    "lease_id": "lease-1",
                    "lease_epoch": 1,
                    "host_instance_id": "host-1",
                    "observed_at": "2026-08-09T12:01:00+00:00",
                    "host_process_absent": True,
                    "root_processes_absent": True,
                },
            },
        )
        assert terminalized["terminalization"]["status"] == "applied"
        assert json.loads(path.read_text())["attempts"][0]["terminal_record"]["classification"] == "host_crash"
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_migration_preflight_and_legacy_abandonment_only_accept_unleased_history(tmp_path: Path) -> None:
    run_id = tmp_path.name
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    try:
        legacy = {
            "version": 1,
            "run_id": run_id,
            "request": {},
            "state": "running",
            "state_history": [{"state": "running", "reason": "fixture", "at": "2026-08-09T10:00:00+00:00"}],
            "attempts": [{
                "attempt_id": "attempt-1",
                "packet": {"version": 6, "base_commit": "base"},
                "nodes": [],
                "evidence": {},
                "outcome": None,
                "decision": None,
            }],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(legacy), encoding="utf-8")

        assert {"run_id": run_id, "attempt_id": "attempt-1"} in managed.migration_preflight(ROOT)["active_legacy_attempts"]
        result = managed.abandon_legacy_attempt(
            ROOT,
            run_id,
            {"attempt_id": "attempt-1", "actor": "operator-1", "reason": "cutover", "acknowledged": True},
        )

        assert result["state"] == "blocked"
        assert json.loads(path.read_text())["attempts"][0]["terminal_record"]["classification"] == "legacy_operator_abandoned"
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)
