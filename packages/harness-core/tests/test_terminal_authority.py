from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from harness_core import authority, managed


ROOT = Path(__file__).resolve().parents[3]


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _public_key(private_key: Ed25519PrivateKey) -> str:
    return _base64url(
        private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
    )


def _write_registry(
    path: Path,
    private_key: Ed25519PrivateKey,
    *,
    status: str = "active",
    roles: list[str] | None = None,
) -> None:
    roles = ["controller_approver"] if roles is None else roles
    path.write_text(
        "[registry]\n"
        "version = 1\n\n"
        "[authorities.controller-1]\n"
        "principal_id = \"controller\"\n"
        f"roles = {json.dumps(roles)}\n"
        "algorithm = \"ed25519\"\n"
        f"public_key = \"{_public_key(private_key)}\"\n"
        f"key_fingerprint = \"{authority.public_key_fingerprint(_public_key(private_key))}\"\n"
        f"status = \"{status}\"\n",
        encoding="utf-8",
    )


def _write_legacy_attesters(path: Path, private_key: Ed25519PrivateKey) -> None:
    public_key = _public_key(private_key)
    path.write_text(
        "[attesters.cleanup-1]\n"
        "attester_id = \"cleanup-operator\"\n"
        "role = \"managed_cleanup_operator\"\n"
        "algorithm = \"ed25519\"\n"
        f"public_key = \"{public_key}\"\n"
        "status = \"active\"\n",
        encoding="utf-8",
    )


def _authorization(private_key: Ed25519PrivateKey, *, now: datetime) -> dict[str, object]:
    unsigned: dict[str, object] = {
        "schema_id": "controller_authorization/v1",
        "authorization_id": "approval-1",
        "run_id": "run-1",
        "attempt_id": "attempt-1",
        "packet_sha256": "a" * 64,
        "outcome_id": "outcome-1",
        "outcome_digest": "b" * 64,
        "requested_decision": "accept",
        "issuer_key_id": "controller-1",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "reason_sha256": "c" * 64,
        "reason_length": 7,
    }
    return authority.sign_document(unsigned, private_key)


def test_signed_document_uses_one_canonical_encoding() -> None:
    value = {"z": [2, 1], "a": "value"}

    assert authority.canonical_json_bytes(value) == b'{"a":"value","z":[2,1]}'


def test_load_registry_rejects_private_key_field(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    path = tmp_path / "harness-authorities.toml"
    _write_registry(path, private_key)
    path.write_text(path.read_text(encoding="utf-8") + 'private_key = "secret"\n', encoding="utf-8")

    with pytest.raises(authority.AuthorityError, match="invalid fields"):
        authority.load_authorities(path)


def test_normalize_controller_authorization_binds_active_registry(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    path = tmp_path / "harness-authorities.toml"
    _write_registry(path, private_key)
    now = datetime.now(UTC)

    normalized = authority.normalize_controller_authorization(
        _authorization(private_key, now=now),
        registry=authority.load_authorities(path),
        policy={
            "max_authorization_bytes": 8192,
            "max_authorization_age_seconds": 900,
            "max_authorization_lifetime_seconds": 900,
            "max_clock_skew_seconds": 60,
            "allowed_controller_roles": ["controller_approver"],
        },
        now=now,
    )

    assert normalized["principal_id"] == "controller"
    assert normalized["authorization_digest"] == authority.document_digest(_authorization(private_key, now=now))


def test_normalize_controller_authorization_rejects_revoked_issuer(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    path = tmp_path / "harness-authorities.toml"
    _write_registry(path, private_key, status="revoked")
    now = datetime.now(UTC)

    with pytest.raises(authority.AuthorityError, match="revoked"):
        authority.normalize_controller_authorization(
            _authorization(private_key, now=now),
            registry=authority.load_authorities(path),
            policy={
                "max_authorization_bytes": 8192,
                "max_authorization_age_seconds": 900,
                "max_authorization_lifetime_seconds": 900,
                "max_clock_skew_seconds": 60,
                "allowed_controller_roles": ["controller_approver"],
            },
            now=now,
        )


@pytest.mark.parametrize(
    ("issued_offset", "max_age_seconds", "error"),
    [
        (-timedelta(seconds=101), 100, "stale"),
        (timedelta(seconds=61), 900, "outside clock skew"),
    ],
)
def test_normalize_controller_authorization_rejects_stale_or_future_authority(
    tmp_path: Path,
    issued_offset: timedelta,
    max_age_seconds: int,
    error: str,
) -> None:
    private_key = Ed25519PrivateKey.generate()
    path = tmp_path / "harness-authorities.toml"
    _write_registry(path, private_key)
    now = datetime.now(UTC)

    with pytest.raises(authority.AuthorityError, match=error):
        authority.normalize_controller_authorization(
            _authorization(private_key, now=now + issued_offset),
            registry=authority.load_authorities(path),
            policy={
                "max_authorization_bytes": 8192,
                "max_authorization_age_seconds": max_age_seconds,
                "max_authorization_lifetime_seconds": 900,
                "max_clock_skew_seconds": 60,
                "allowed_controller_roles": ["controller_approver"],
            },
            now=now,
        )


def test_normalize_controller_authorization_rejects_wrong_role(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    path = tmp_path / "harness-authorities.toml"
    _write_registry(path, private_key, roles=["managed_cleanup_operator"])
    now = datetime.now(UTC)

    with pytest.raises(authority.AuthorityError, match="role is not allowed"):
        authority.normalize_controller_authorization(
            _authorization(private_key, now=now),
            registry=authority.load_authorities(path),
            policy={
                "max_authorization_bytes": 8192,
                "max_authorization_age_seconds": 900,
                "max_authorization_lifetime_seconds": 900,
                "max_clock_skew_seconds": 60,
                "allowed_controller_roles": ["controller_approver"],
            },
            now=now,
        )


def test_migrate_legacy_attesters_writes_current_registry(tmp_path: Path) -> None:
    source = tmp_path / "harness-attesters.toml"
    target = tmp_path / "harness-authorities.toml"
    _write_legacy_attesters(source, Ed25519PrivateKey.generate())

    result = authority.migrate_legacy_attesters(source, target)

    registry = authority.load_authorities(target)
    assert result == {"authority_count": 1, "registry_digest": registry["registry_digest"]}
    assert registry["entries"]["cleanup-1"]["principal_id"] == "cleanup-operator"
    assert registry["entries"]["cleanup-1"]["roles"] == ["managed_cleanup_operator"]


def test_migrate_legacy_attesters_dry_run_and_collision(tmp_path: Path) -> None:
    source = tmp_path / "harness-attesters.toml"
    target = tmp_path / "harness-authorities.toml"
    _write_legacy_attesters(source, Ed25519PrivateKey.generate())

    preview = authority.migrate_legacy_attesters(source, target, dry_run=True)

    assert preview["authority_count"] == 1
    assert not target.exists()
    authority.migrate_legacy_attesters(source, target)
    with pytest.raises(authority.AuthorityError, match="already exists"):
        authority.migrate_legacy_attesters(source, target)


def test_migrate_harness_authorities_cli_uses_explicit_safe_migration(tmp_path: Path) -> None:
    source = tmp_path / "harness-attesters.toml"
    target = tmp_path / "harness-authorities.toml"
    _write_legacy_attesters(source, Ed25519PrivateKey.generate())

    assert managed.main([
        "--repo-root", str(ROOT),
        "migrate-harness-authorities",
        "--source", str(source),
        "--target", str(target),
        "--dry-run",
    ]) == 0
    assert not target.exists()
    assert managed.main([
        "--repo-root", str(ROOT),
        "migrate-harness-authorities",
        "--source", str(source),
        "--target", str(target),
    ]) == 0
    assert authority.load_authorities(target)["entries"]
    assert managed.main([
        "--repo-root", str(ROOT),
        "migrate-harness-authorities",
        "--source", str(source),
        "--target", str(target),
    ]) == 2
