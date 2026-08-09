from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import shutil

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from harness_core import legacy_cleanup, managed


ROOT = Path(__file__).resolve().parents[3]


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def write_legacy_run(tmp_path: Path) -> tuple[str, Path, dict[str, object]]:
    run_id = tmp_path.name
    path = ROOT / ".harness" / "runs" / run_id / "run.json"
    packet = {"version": 7, "attempt_id": "attempt-1", "base_commit": "legacy-base"}
    run = {
        "version": 1,
        "run_id": run_id,
        "request": {},
        "state": "running",
        "state_history": [{"state": "running", "reason": "fixture", "at": "2026-08-09T10:00:00+00:00"}],
        "run_revision": 0,
        "attempts": [{
            "attempt_id": "attempt-1",
            "packet": packet,
            "nodes": [],
            "claims": [],
            "node_observations": [],
            "evidence": {},
            "execution_lease": None,
            "host_terminal_observations": [],
            "host_observation_digests": [],
            "terminal_record": None,
            "cancellation_request": None,
            "recovery_blocked": None,
            "outcome": None,
            "decision": None,
            "decision_history": [],
        }],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run), encoding="utf-8")
    return run_id, path, packet


def write_attester(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, status: str = "active") -> Path:
    private_key = Ed25519PrivateKey.generate()
    private_key_path = tmp_path / "operator-private.pem"
    private_key_path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public_key = _base64url(
        private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
    )
    config_path = tmp_path / "harness-attesters.toml"
    config_path.write_text(
        "[attesters.operator-1]\n"
        "attester_id = \"cleanup-operator\"\n"
        "role = \"managed_cleanup_operator\"\n"
        "algorithm = \"ed25519\"\n"
        f"public_key = \"{public_key}\"\n"
        f"status = \"{status}\"\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(legacy_cleanup, "legacy_cleanup_trusted_config_path", lambda: config_path)
    return private_key_path


def signed_attestation(
    run_id: str,
    packet: dict[str, object],
    private_key_path: Path,
    *,
    scope: str = "operator_discovered_provider_tree",
) -> dict[str, object]:
    now = datetime.now(UTC)
    root = {"pid": 28684, "creation_id": "process-01dd27ee451e40b3", "state": "absent"}
    value: dict[str, object] = {
        "schema_id": "legacy_cleanup_attestation/v1",
        "attestation_id": "cleanup-1",
        "run_id": run_id,
        "attempt_id": "attempt-1",
        "packet_sha256": managed._canonical_digest(packet),
        "issuer_key_id": "operator-1",
        "absence_observed_at": (now - timedelta(seconds=20)).isoformat(),
        "issued_at": (now - timedelta(seconds=10)).isoformat(),
        "expires_at": (now + timedelta(seconds=120)).isoformat(),
        "cleanup_scope": scope,
        "discovery_method": "windows_parent_chain/v1",
        "root_process_identity": root,
        "process_identities": [root, {"pid": 31780, "creation_id": "process-01dd27ee45214c4d", "state": "absent"}],
        "scope_complete": True,
        "reason_sha256": hashlib.sha256(b"operator-confirmed cleanup").hexdigest(),
        "reason_length": 26,
    }
    if scope == "operator_attested_no_provider_process":
        value["discovery_method"] = "windows_no_process_observation/v1"
        value["root_process_identity"] = None
        value["process_identities"] = []
    return legacy_cleanup.sign_legacy_cleanup_attestation(value, private_key_path)


@pytest.mark.parametrize("scope", ["operator_discovered_provider_tree", "operator_attested_no_provider_process"])
def test_legacy_cleanup_terminalizes_and_replays_after_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scope: str) -> None:
    run_id, path, packet = write_legacy_run(tmp_path)
    try:
        private_key_path = write_attester(tmp_path, monkeypatch)
        attestation = signed_attestation(run_id, packet, private_key_path, scope=scope)
        evidence = {"attempt_id": "attempt-1", "legacy_cleanup_attestation": attestation}

        applied = managed.terminalize_attempt(ROOT, run_id, evidence)
        recorded = json.loads(path.read_text(encoding="utf-8"))
        record = recorded["attempts"][0]["terminal_record"]

        assert applied["terminalization"]["status"] == "applied"
        assert recorded["state"] == "awaiting_decision"
        assert record["schema_id"] == "attempt_terminal_evidence/v2"
        assert record["classification"] == "legacy_cleanup_attested"
        assert record["source_kind"] == "legacy_cleanup"
        assert record["lease_id"] is None
        assert record["lease_epoch"] is None
        assert record["legacy_cleanup"]["cleanup_scope"] == scope
        assert recorded["attempts"][0]["outcome"]["allowed_decisions"] == ["block"]

        managed.apply_controller_decision(ROOT, run_id, {"kind": "block"})
        after_block = path.read_bytes()
        replayed = managed.terminalize_attempt(ROOT, run_id, evidence)

        assert replayed["terminalization"]["status"] == "replayed"
        assert path.read_bytes() == after_block
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_legacy_cleanup_replay_survives_issuer_revocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id, path, packet = write_legacy_run(tmp_path)
    try:
        private_key_path = write_attester(tmp_path, monkeypatch)
        evidence = {"attempt_id": "attempt-1", "legacy_cleanup_attestation": signed_attestation(run_id, packet, private_key_path)}
        managed.terminalize_attempt(ROOT, run_id, evidence)
        config_path = legacy_cleanup.legacy_cleanup_trusted_config_path()
        config_path.write_text(config_path.read_text(encoding="utf-8").replace('status = "active"', 'status = "revoked"'), encoding="utf-8")

        replayed = managed.terminalize_attempt(ROOT, run_id, evidence)

        assert replayed["terminalization"]["status"] == "replayed"
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_legacy_cleanup_rejects_new_revoked_stale_and_oversized_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id, path, packet = write_legacy_run(tmp_path)
    try:
        private_key_path = write_attester(tmp_path, monkeypatch, status="revoked")
        before = path.read_bytes()
        with pytest.raises(managed.HarnessError, match="issuer is revoked"):
            managed.terminalize_attempt(
                ROOT,
                run_id,
                {"attempt_id": "attempt-1", "legacy_cleanup_attestation": signed_attestation(run_id, packet, private_key_path)},
            )
        assert path.read_bytes() == before

        write_attester(tmp_path, monkeypatch)
        stale = signed_attestation(run_id, packet, private_key_path)
        now = datetime.now(UTC)
        stale.update({
            "absence_observed_at": (now - timedelta(seconds=1000)).isoformat(),
            "issued_at": (now - timedelta(seconds=800)).isoformat(),
            "expires_at": (now + timedelta(seconds=50)).isoformat(),
        })
        stale = legacy_cleanup.sign_legacy_cleanup_attestation(
            {key: value for key, value in stale.items() if key != "attestation_signature"},
            private_key_path,
        )
        with pytest.raises(managed.HarnessError, match="attestation is stale"):
            managed.terminalize_attempt(ROOT, run_id, {"attempt_id": "attempt-1", "legacy_cleanup_attestation": stale})
        assert path.read_bytes() == before

        oversized = signed_attestation(run_id, packet, private_key_path)
        root = oversized["root_process_identity"]
        assert isinstance(root, dict)
        oversized["process_identities"] = [
            root,
            *[
                {"pid": 32000 + index, "creation_id": f"process-{index}-{'x' * 230}", "state": "absent"}
                for index in range(31)
            ],
        ]
        oversized = legacy_cleanup.sign_legacy_cleanup_attestation(
            {key: value for key, value in oversized.items() if key != "attestation_signature"},
            private_key_path,
        )
        with pytest.raises(managed.HarnessError, match="exceeds byte limit"):
            managed.terminalize_attempt(ROOT, run_id, {"attempt_id": "attempt-1", "legacy_cleanup_attestation": oversized})
        assert path.read_bytes() == before
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_legacy_cleanup_rejects_different_signed_evidence_after_terminalization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id, path, packet = write_legacy_run(tmp_path)
    try:
        private_key_path = write_attester(tmp_path, monkeypatch)
        evidence = {"attempt_id": "attempt-1", "legacy_cleanup_attestation": signed_attestation(run_id, packet, private_key_path)}
        managed.terminalize_attempt(ROOT, run_id, evidence)
        before = path.read_bytes()
        conflicting = signed_attestation(run_id, packet, private_key_path)
        conflicting["attestation_id"] = "cleanup-2"
        conflicting = legacy_cleanup.sign_legacy_cleanup_attestation(
            {key: value for key, value in conflicting.items() if key != "attestation_signature"},
            private_key_path,
        )

        with pytest.raises(managed.HarnessError, match="attempt_already_terminal"):
            managed.terminalize_attempt(
                ROOT,
                run_id,
                {"attempt_id": "attempt-1", "legacy_cleanup_attestation": conflicting},
            )

        assert path.read_bytes() == before
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_legacy_cleanup_cli_signs_and_auto_blocks_idempotently(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id, path, packet = write_legacy_run(tmp_path)
    try:
        private_key_path = write_attester(tmp_path, monkeypatch)
        unsigned = signed_attestation(run_id, packet, private_key_path)
        unsigned.pop("attestation_signature")
        unsigned_path = tmp_path / "unsigned.json"
        evidence_path = tmp_path / "signed.json"
        unsigned_path.write_text(json.dumps(unsigned), encoding="utf-8")

        assert managed.main([
            "--repo-root", str(ROOT),
            "sign-legacy-cleanup",
            "--attestation", str(unsigned_path),
            "--private-key-file", str(private_key_path),
            "--output", str(evidence_path),
        ]) == 0
        signed = json.loads(evidence_path.read_text(encoding="utf-8"))
        assert managed.main([
            "--repo-root", str(ROOT),
            "terminalize-attempt",
            "--run-id", run_id,
            "--evidence", str(evidence_path),
            "--auto-block",
        ]) == 0
        assert json.loads(path.read_text(encoding="utf-8"))["state"] == "blocked"
        assert managed.main([
            "--repo-root", str(ROOT),
            "terminalize-attempt",
            "--run-id", run_id,
            "--evidence", str(evidence_path),
            "--auto-block",
        ]) == 0
        assert signed["attestation_signature"]
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


@pytest.mark.parametrize("mutation", ["signature", "scope", "issuer"])
def test_legacy_cleanup_rejects_invalid_new_evidence_without_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    run_id, path, packet = write_legacy_run(tmp_path)
    try:
        private_key_path = write_attester(tmp_path, monkeypatch)
        attestation = signed_attestation(run_id, packet, private_key_path)
        if mutation == "signature":
            attestation["attestation_signature"] = "A" * 86
        elif mutation == "scope":
            attestation["process_identities"] = []
            attestation = legacy_cleanup.sign_legacy_cleanup_attestation(
                {key: value for key, value in attestation.items() if key != "attestation_signature"},
                private_key_path,
            )
        else:
            attestation["issuer_key_id"] = "unknown-issuer"
            attestation = legacy_cleanup.sign_legacy_cleanup_attestation(
                {key: value for key, value in attestation.items() if key != "attestation_signature"},
                private_key_path,
            )
        before = path.read_bytes()

        with pytest.raises(managed.HarnessError):
            managed.terminalize_attempt(ROOT, run_id, {"attempt_id": "attempt-1", "legacy_cleanup_attestation": attestation})

        assert path.read_bytes() == before
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_legacy_cleanup_rejects_claimed_attempt_and_retired_abandonment_keeps_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id, path, packet = write_legacy_run(tmp_path)
    try:
        private_key_path = write_attester(tmp_path, monkeypatch)
        run = json.loads(path.read_text(encoding="utf-8"))
        run["attempts"][0]["claims"] = [{"kind": "claimed_result"}]
        path.write_text(json.dumps(run), encoding="utf-8")
        before = path.read_bytes()

        with pytest.raises(managed.HarnessError, match="legacy cleanup is not allowed"):
            managed.terminalize_attempt(
                ROOT,
                run_id,
                {"attempt_id": "attempt-1", "legacy_cleanup_attestation": signed_attestation(run_id, packet, private_key_path)},
            )
        with pytest.raises(managed.HarnessError, match="legacy_abandonment_retired"):
            managed.abandon_legacy_attempt(ROOT, run_id, {"attempt_id": "attempt-1"})

        assert path.read_bytes() == before
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)
