from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import tomllib
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class LegacyCleanupError(ValueError):
    pass


_SCHEMA_ID = "legacy_cleanup_attestation/v1"
_UNSIGNED_FIELDS = {
    "schema_id",
    "attestation_id",
    "run_id",
    "attempt_id",
    "packet_sha256",
    "issuer_key_id",
    "absence_observed_at",
    "issued_at",
    "expires_at",
    "cleanup_scope",
    "discovery_method",
    "root_process_identity",
    "process_identities",
    "scope_complete",
    "reason_sha256",
    "reason_length",
}
_TRANSPORT_FIELDS = _UNSIGNED_FIELDS | {"attestation_signature"}
_ATTESTER_FIELDS = {"attester_id", "role", "algorithm", "public_key", "status"}
_OPAQUE_IDENTIFIER = re.compile(r"[A-Za-z0-9._-]+\Z")
_BASE64URL = re.compile(r"[A-Za-z0-9_-]+\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise LegacyCleanupError("legacy cleanup attestation is not JSON") from exc


def _required_mapping(value: Any, fields: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise LegacyCleanupError(f"{name} has invalid fields")
    return value


def _opaque_identifier(value: Any, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or not _OPAQUE_IDENTIFIER.fullmatch(value) or len(value.encode("ascii")) > maximum:
        raise LegacyCleanupError(f"legacy cleanup {name} is invalid")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise LegacyCleanupError(f"legacy cleanup {name} is invalid")
    return value


def _positive_integer(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise LegacyCleanupError(f"legacy cleanup {name} is invalid")
    return value


def _timestamp(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise LegacyCleanupError(f"legacy cleanup {name} is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LegacyCleanupError(f"legacy cleanup {name} is invalid") from exc
    if parsed.tzinfo is None:
        raise LegacyCleanupError(f"legacy cleanup {name} is invalid")
    return parsed.astimezone(UTC)


def _base64url(value: Any, name: str) -> bytes:
    if not isinstance(value, str) or not value or not _BASE64URL.fullmatch(value):
        raise LegacyCleanupError(f"legacy cleanup {name} is invalid")
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, UnicodeEncodeError) as exc:
        raise LegacyCleanupError(f"legacy cleanup {name} is invalid") from exc


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _identity(value: Any, policy: dict[str, Any], name: str) -> dict[str, Any]:
    identity = _required_mapping(value, {"pid", "creation_id", "state"}, f"legacy cleanup {name}")
    pid = _positive_integer(identity["pid"], f"{name} pid")
    creation_id = _opaque_identifier(identity["creation_id"], f"{name} creation_id", policy["max_creation_id_bytes"])
    if identity["state"] != "absent":
        raise LegacyCleanupError(f"legacy cleanup {name} state is invalid")
    return {"pid": pid, "creation_id": creation_id, "state": "absent"}


def legacy_cleanup_trusted_config_path() -> Path:
    return Path.home() / ".codex" / "harness-attesters.toml"


def load_legacy_cleanup_attesters() -> dict[str, dict[str, str]]:
    path = legacy_cleanup_trusted_config_path()
    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise LegacyCleanupError("legacy cleanup attester configuration is unavailable") from exc
    if not isinstance(payload, dict) or set(payload) != {"attesters"} or not isinstance(payload["attesters"], dict):
        raise LegacyCleanupError("legacy cleanup attester configuration is invalid")
    attesters: dict[str, dict[str, str]] = {}
    for issuer_key_id, raw_attester in payload["attesters"].items():
        issuer = _opaque_identifier(issuer_key_id, "issuer_key_id", 128)
        if issuer in attesters or not isinstance(raw_attester, dict) or set(raw_attester) != _ATTESTER_FIELDS:
            raise LegacyCleanupError("legacy cleanup attester configuration is invalid")
        attester_id = _opaque_identifier(raw_attester["attester_id"], "attester_id", 128)
        role = _opaque_identifier(raw_attester["role"], "attester role", 128)
        if raw_attester["algorithm"] != "ed25519" or raw_attester["status"] not in {"active", "revoked"}:
            raise LegacyCleanupError("legacy cleanup attester configuration is invalid")
        public_key = _base64url(raw_attester["public_key"], "attester public_key")
        if len(public_key) != 32:
            raise LegacyCleanupError("legacy cleanup attester configuration is invalid")
        try:
            Ed25519PublicKey.from_public_bytes(public_key)
        except ValueError as exc:
            raise LegacyCleanupError("legacy cleanup attester configuration is invalid") from exc
        attesters[issuer] = {
            "attester_id": attester_id,
            "role": role,
            "algorithm": "ed25519",
            "public_key": raw_attester["public_key"],
            "status": raw_attester["status"],
        }
    if not attesters:
        raise LegacyCleanupError("legacy cleanup attester configuration is invalid")
    return attesters


def legacy_cleanup_evidence_digest(value: Any) -> str:
    attestation = _required_mapping(value, _TRANSPORT_FIELDS, "legacy cleanup attestation")
    _base64url(attestation["attestation_signature"], "attestation signature")
    return hashlib.sha256(_canonical_json_bytes(attestation)).hexdigest()


def _unsigned_attestation(value: Any) -> dict[str, Any]:
    attestation = _required_mapping(value, _TRANSPORT_FIELDS, "legacy cleanup attestation")
    return {key: attestation[key] for key in _UNSIGNED_FIELDS}


def verify_legacy_cleanup_signature(unsigned: dict[str, Any], signature: Any, public_key: str) -> None:
    signature_bytes = _base64url(signature, "attestation signature")
    if len(signature_bytes) != 64:
        raise LegacyCleanupError("legacy cleanup attestation signature is invalid")
    try:
        Ed25519PublicKey.from_public_bytes(_base64url(public_key, "attester public_key")).verify(signature_bytes, _canonical_json_bytes(unsigned))
    except (InvalidSignature, ValueError) as exc:
        raise LegacyCleanupError("legacy cleanup attestation signature is invalid") from exc


def normalize_legacy_cleanup_attestation(value: Any, policy: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    if policy.get("enabled") is not True:
        raise LegacyCleanupError("legacy cleanup is disabled")
    attestation = _required_mapping(value, _TRANSPORT_FIELDS, "legacy cleanup attestation")
    unsigned = _unsigned_attestation(attestation)
    if len(_canonical_json_bytes(attestation)) > policy["max_total_bytes"]:
        raise LegacyCleanupError("legacy cleanup attestation exceeds byte limit")
    maximum_identifier = policy["max_identifier_bytes"]
    if unsigned["schema_id"] != _SCHEMA_ID:
        raise LegacyCleanupError("legacy cleanup schema is invalid")
    attestation_id = _opaque_identifier(unsigned["attestation_id"], "attestation_id", maximum_identifier)
    run_id = _opaque_identifier(unsigned["run_id"], "run_id", maximum_identifier)
    attempt_id = _opaque_identifier(unsigned["attempt_id"], "attempt_id", maximum_identifier)
    issuer_key_id = _opaque_identifier(unsigned["issuer_key_id"], "issuer_key_id", maximum_identifier)
    packet_sha256 = _sha256(unsigned["packet_sha256"], "packet_sha256")
    reason_sha256 = _sha256(unsigned["reason_sha256"], "reason_sha256")
    reason_length = unsigned["reason_length"]
    if not isinstance(reason_length, int) or isinstance(reason_length, bool) or not 0 <= reason_length <= policy["max_reason_length"]:
        raise LegacyCleanupError("legacy cleanup reason_length is invalid")
    absence_observed_at = _timestamp(unsigned["absence_observed_at"], "absence_observed_at")
    issued_at = _timestamp(unsigned["issued_at"], "issued_at")
    expires_at = _timestamp(unsigned["expires_at"], "expires_at")
    clock_skew = timedelta(seconds=policy["max_clock_skew_seconds"])
    if absence_observed_at > issued_at or issued_at >= expires_at:
        raise LegacyCleanupError("legacy cleanup timestamps are invalid")
    if expires_at - issued_at > timedelta(seconds=policy["max_attestation_lifetime_seconds"]):
        raise LegacyCleanupError("legacy cleanup attestation lifetime is invalid")
    if absence_observed_at > now + clock_skew or issued_at > now + clock_skew or now > expires_at + clock_skew:
        raise LegacyCleanupError("legacy cleanup attestation timestamp is outside clock skew")
    if now - absence_observed_at > timedelta(seconds=policy["max_attestation_age_seconds"]):
        raise LegacyCleanupError("legacy cleanup attestation is stale")
    cleanup_scope = unsigned["cleanup_scope"]
    discovery_method = unsigned["discovery_method"]
    if cleanup_scope not in policy["allowed_cleanup_scopes"] or discovery_method not in policy["allowed_discovery_methods"]:
        raise LegacyCleanupError("legacy cleanup scope is invalid")
    if unsigned["scope_complete"] is not True:
        raise LegacyCleanupError("legacy cleanup scope_complete is invalid")
    raw_identities = unsigned["process_identities"]
    if not isinstance(raw_identities, list) or len(raw_identities) > policy["max_process_identities"]:
        raise LegacyCleanupError("legacy cleanup process_identities are invalid")
    identities = [_identity(item, policy, "process identity") for item in raw_identities]
    identity_keys = {(item["pid"], item["creation_id"]) for item in identities}
    if len(identity_keys) != len(identities):
        raise LegacyCleanupError("legacy cleanup process_identities are duplicated")
    root = unsigned["root_process_identity"]
    if cleanup_scope == "operator_discovered_provider_tree":
        normalized_root = _identity(root, policy, "root_process_identity")
        root_key = (normalized_root["pid"], normalized_root["creation_id"])
        if not identities or root_key not in identity_keys:
            raise LegacyCleanupError("legacy cleanup provider tree is incomplete")
    elif cleanup_scope == "operator_attested_no_provider_process":
        if root is not None or identities or discovery_method != "windows_no_process_observation/v1":
            raise LegacyCleanupError("legacy cleanup no-process scope is invalid")
        normalized_root = None
    else:
        raise LegacyCleanupError("legacy cleanup scope is invalid")
    attesters = load_legacy_cleanup_attesters()
    attester = attesters.get(issuer_key_id)
    if attester is None:
        raise LegacyCleanupError("legacy cleanup issuer is unknown")
    if attester["status"] != "active":
        raise LegacyCleanupError("legacy cleanup issuer is revoked")
    if attester["role"] not in policy["allowed_attester_roles"]:
        raise LegacyCleanupError("legacy cleanup issuer role is not allowed")
    verify_legacy_cleanup_signature(unsigned, attestation["attestation_signature"], attester["public_key"])
    return {
        "attestation_id": attestation_id,
        "attester_id": attester["attester_id"],
        "issuer_key_id": issuer_key_id,
        "signed_evidence_sha256": legacy_cleanup_evidence_digest(attestation),
        "run_id": run_id,
        "attempt_id": attempt_id,
        "packet_sha256": packet_sha256,
        "absence_observed_at": absence_observed_at.isoformat(),
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "cleanup_scope": cleanup_scope,
        "discovery_method": discovery_method,
        "root_process_identity": normalized_root,
        "process_identities": identities,
        "scope_complete": True,
        "reason_sha256": reason_sha256,
        "reason_length": reason_length,
    }


def sign_legacy_cleanup_attestation(value: Any, private_key_path: Path) -> dict[str, Any]:
    unsigned = _required_mapping(value, _UNSIGNED_FIELDS, "legacy cleanup attestation")
    try:
        private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    except (OSError, TypeError, ValueError) as exc:
        raise LegacyCleanupError("legacy cleanup private key is invalid") from exc
    if not isinstance(private_key, Ed25519PrivateKey):
        raise LegacyCleanupError("legacy cleanup private key is invalid")
    return {
        **unsigned,
        "attestation_signature": _base64url_encode(private_key.sign(_canonical_json_bytes(unsigned))),
    }
