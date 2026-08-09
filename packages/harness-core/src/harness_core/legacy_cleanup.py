from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from . import authority


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
_OPAQUE_IDENTIFIER = re.compile(r"[A-Za-z0-9._-]+\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


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


def _identity(value: Any, policy: dict[str, Any], name: str) -> dict[str, Any]:
    identity = _required_mapping(value, {"pid", "creation_id", "state"}, f"legacy cleanup {name}")
    pid = _positive_integer(identity["pid"], f"{name} pid")
    creation_id = _opaque_identifier(identity["creation_id"], f"{name} creation_id", policy["max_creation_id_bytes"])
    if identity["state"] != "absent":
        raise LegacyCleanupError(f"legacy cleanup {name} state is invalid")
    return {"pid": pid, "creation_id": creation_id, "state": "absent"}


def legacy_cleanup_trusted_config_path() -> Path:
    return authority.authority_registry_path()


def load_legacy_cleanup_attesters() -> dict[str, dict[str, Any]]:
    path = legacy_cleanup_trusted_config_path()
    try:
        registry = authority.load_authorities(path)
    except authority.AuthorityError as exc:
        raise LegacyCleanupError("legacy cleanup attester configuration is unavailable") from exc
    entries = registry["entries"]
    attesters = {
        key_id: {
            "attester_id": entry["principal_id"],
            "roles": entry["roles"],
            "algorithm": entry["algorithm"],
            "public_key": entry["public_key"],
            "status": entry["status"],
            "key_fingerprint": entry["key_fingerprint"],
            "registry_digest": registry["registry_digest"],
        }
        for key_id, entry in entries.items()
    }
    if not attesters:
        raise LegacyCleanupError("legacy cleanup attester configuration is invalid")
    return attesters


def legacy_cleanup_evidence_digest(value: Any) -> str:
    attestation = _required_mapping(value, _TRANSPORT_FIELDS, "legacy cleanup attestation")
    try:
        signature = authority.base64url_encode(authority.base64url_decode(attestation["attestation_signature"], "signature"))
    except authority.AuthorityError as exc:
        raise LegacyCleanupError("legacy cleanup attestation signature is invalid") from exc
    if signature != attestation["attestation_signature"]:
        raise LegacyCleanupError("legacy cleanup attestation signature is invalid")
    return authority.document_digest(attestation)


def _unsigned_attestation(value: Any) -> dict[str, Any]:
    attestation = _required_mapping(value, _TRANSPORT_FIELDS, "legacy cleanup attestation")
    return {key: attestation[key] for key in _UNSIGNED_FIELDS}


def verify_legacy_cleanup_signature(unsigned: dict[str, Any], signature: Any, public_key: str) -> None:
    try:
        signature_bytes = authority.base64url_decode(signature, "signature")
        if len(signature_bytes) != 64:
            raise authority.AuthorityError("authority signature is invalid")
        authority.verify_document(unsigned, signature, public_key)
    except authority.AuthorityError as exc:
        raise LegacyCleanupError("legacy cleanup attestation signature is invalid") from exc


def normalize_legacy_cleanup_attestation(value: Any, policy: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    if policy.get("enabled") is not True:
        raise LegacyCleanupError("legacy cleanup is disabled")
    attestation = _required_mapping(value, _TRANSPORT_FIELDS, "legacy cleanup attestation")
    unsigned = _unsigned_attestation(attestation)
    if len(authority.canonical_json_bytes(attestation)) > policy["max_total_bytes"]:
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
    if not set(attester["roles"]) & set(policy["allowed_attester_roles"]):
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
        return authority.sign_document(unsigned, authority.load_private_ed25519_key(private_key_path))
    except authority.AuthorityError as exc:
        raise LegacyCleanupError("legacy cleanup private key is invalid")
