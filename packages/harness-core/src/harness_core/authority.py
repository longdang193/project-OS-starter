from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import tomllib
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class AuthorityError(ValueError):
    pass


_BASE64URL = re.compile(r"[A-Za-z0-9_-]+\Z")
_IDENTIFIER = re.compile(r"[A-Za-z0-9._-]+\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REGISTRY_FIELDS = {"version"}
_ENTRY_FIELDS = {"principal_id", "roles", "algorithm", "public_key", "key_fingerprint", "status"}
_LEGACY_REGISTRY_FIELDS = {"attesters"}
_LEGACY_ENTRY_FIELDS = {"attester_id", "role", "algorithm", "public_key", "status"}
_AUTHORIZATION_UNSIGNED_FIELDS = {
    "schema_id",
    "authorization_id",
    "run_id",
    "attempt_id",
    "packet_sha256",
    "outcome_id",
    "outcome_digest",
    "requested_decision",
    "issuer_key_id",
    "issued_at",
    "expires_at",
    "reason_sha256",
    "reason_length",
}
_AUTHORIZATION_FIELDS = _AUTHORIZATION_UNSIGNED_FIELDS | {"authorization_signature"}


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AuthorityError("authority document is not JSON") from exc


def document_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _base64url(value: Any, name: str) -> bytes:
    if not isinstance(value, str) or not value or not _BASE64URL.fullmatch(value):
        raise AuthorityError(f"authority {name} is invalid")
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, UnicodeEncodeError) as exc:
        raise AuthorityError(f"authority {name} is invalid") from exc


def base64url_decode(value: Any, name: str) -> bytes:
    return _base64url(value, name)


def base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _identifier(value: Any, name: str, *, maximum: int = 128) -> str:
    if not isinstance(value, str) or not value or not _IDENTIFIER.fullmatch(value) or len(value.encode("ascii")) > maximum:
        raise AuthorityError(f"authority {name} is invalid")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise AuthorityError(f"authority {name} is invalid")
    return value


def _positive_integer(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise AuthorityError(f"authority {name} is invalid")
    return value


def _timestamp(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise AuthorityError(f"authority {name} is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorityError(f"authority {name} is invalid") from exc
    if parsed.tzinfo is None:
        raise AuthorityError(f"authority {name} is invalid")
    return parsed.astimezone(UTC)


def public_key_fingerprint(public_key: Any) -> str:
    raw = _base64url(public_key, "public_key")
    if len(raw) != 32:
        raise AuthorityError("authority public_key is invalid")
    try:
        Ed25519PublicKey.from_public_bytes(raw)
    except ValueError as exc:
        raise AuthorityError("authority public_key is invalid") from exc
    return hashlib.sha256(raw).hexdigest()


def authority_registry_path() -> Path:
    return Path.home() / ".codex" / "harness-authorities.toml"


def legacy_attester_registry_path() -> Path:
    return Path.home() / ".codex" / "harness-attesters.toml"


def _normalize_registry_entry(key_id: Any, value: Any) -> dict[str, Any]:
    key_id = _identifier(key_id, "key_id")
    if not isinstance(value, dict) or set(value) != _ENTRY_FIELDS:
        raise AuthorityError("authority registry entry has invalid fields")
    principal_id = _identifier(value["principal_id"], "principal_id")
    roles = value["roles"]
    if not isinstance(roles, list) or not roles or any(not isinstance(role, str) or not role for role in roles) or len(roles) != len(set(roles)):
        raise AuthorityError("authority roles are invalid")
    if value["algorithm"] != "ed25519":
        raise AuthorityError("authority algorithm is invalid")
    key_fingerprint = public_key_fingerprint(value["public_key"])
    if value["key_fingerprint"] != key_fingerprint:
        raise AuthorityError("authority key_fingerprint is invalid")
    if value["status"] not in {"active", "revoked"}:
        raise AuthorityError("authority status is invalid")
    return {
        "key_id": key_id,
        "principal_id": principal_id,
        "roles": sorted(roles),
        "algorithm": "ed25519",
        "public_key": value["public_key"],
        "key_fingerprint": key_fingerprint,
        "status": value["status"],
    }


def _normalize_authority_registry(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"registry", "authorities"}:
        raise AuthorityError("authority registry has invalid fields")
    registry = payload["registry"]
    authorities = payload["authorities"]
    if not isinstance(registry, dict) or set(registry) != _REGISTRY_FIELDS or registry.get("version") != 1:
        raise AuthorityError("authority registry version is invalid")
    if not isinstance(authorities, dict):
        raise AuthorityError("authority registry entries are invalid")
    entries = {_identifier(key_id, "key_id"): _normalize_registry_entry(key_id, value) for key_id, value in authorities.items()}
    if len(entries) != len(authorities) or not entries:
        raise AuthorityError("authority registry entries are invalid")
    normalized = {"version": 1, "authorities": {key_id: entries[key_id] for key_id in sorted(entries)}}
    return {"entries": entries, "registry_digest": document_digest(normalized)}


def load_authorities(path: Path | None = None) -> dict[str, Any]:
    path = authority_registry_path() if path is None else path
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise AuthorityError("authority registry is unavailable") from exc
    return _normalize_authority_registry(payload)


def _legacy_attester_entries(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise AuthorityError("legacy authority registry is unavailable") from exc
    if not isinstance(payload, dict) or set(payload) != _LEGACY_REGISTRY_FIELDS or not isinstance(payload["attesters"], dict):
        raise AuthorityError("legacy authority registry is invalid")
    entries: dict[str, dict[str, Any]] = {}
    for key_id, value in payload["attesters"].items():
        key_id = _identifier(key_id, "key_id")
        if key_id in entries or not isinstance(value, dict) or set(value) != _LEGACY_ENTRY_FIELDS:
            raise AuthorityError("legacy authority registry is invalid")
        if value["algorithm"] != "ed25519" or value["status"] not in {"active", "revoked"}:
            raise AuthorityError("legacy authority registry is invalid")
        public_key = value["public_key"]
        entries[key_id] = {
            "principal_id": _identifier(value["attester_id"], "principal_id"),
            "roles": [_identifier(value["role"], "role")],
            "algorithm": "ed25519",
            "public_key": public_key,
            "key_fingerprint": public_key_fingerprint(public_key),
            "status": value["status"],
        }
    if not entries:
        raise AuthorityError("legacy authority registry is invalid")
    return entries


def _authority_registry_toml(entries: dict[str, dict[str, Any]]) -> str:
    lines = ["[registry]", "version = 1"]
    for key_id in sorted(entries):
        entry = entries[key_id]
        lines.extend(
            [
                "",
                f'[authorities."{key_id}"]',
                f"principal_id = {json.dumps(entry['principal_id'], ensure_ascii=True)}",
                "roles = [" + ", ".join(json.dumps(role, ensure_ascii=True) for role in entry["roles"]) + "]",
                'algorithm = "ed25519"',
                f"public_key = {json.dumps(entry['public_key'], ensure_ascii=True)}",
                f"key_fingerprint = {json.dumps(entry['key_fingerprint'], ensure_ascii=True)}",
                f"status = {json.dumps(entry['status'], ensure_ascii=True)}",
            ]
        )
    return "\n".join(lines) + "\n"


def migrate_legacy_attesters(
    source: Path | None = None,
    target: Path | None = None,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    source = (legacy_attester_registry_path() if source is None else source).resolve()
    target = (authority_registry_path() if target is None else target).resolve()
    if source == target:
        raise AuthorityError("legacy authority migration source and target must differ")
    entries = _legacy_attester_entries(source)
    payload = {"registry": {"version": 1}, "authorities": entries}
    registry = _normalize_authority_registry(payload)
    result = {"authority_count": len(entries), "registry_digest": registry["registry_digest"]}
    if target.exists() and not overwrite:
        raise AuthorityError("authority registry target already exists")
    if dry_run:
        return result
    target.parent.mkdir(parents=True, exist_ok=True)
    contents = _authority_registry_toml(entries)
    try:
        _normalize_authority_registry(tomllib.loads(contents))
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise AuthorityError("authority registry migration failed") from exc
    return result


def verify_document(unsigned: dict[str, Any], signature: Any, public_key: Any) -> None:
    signature_bytes = _base64url(signature, "signature")
    try:
        Ed25519PublicKey.from_public_bytes(_base64url(public_key, "public_key")).verify(signature_bytes, canonical_json_bytes(unsigned))
    except (InvalidSignature, ValueError) as exc:
        raise AuthorityError("authority signature is invalid") from exc


def sign_document(unsigned: dict[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    if not isinstance(private_key, Ed25519PrivateKey):
        raise AuthorityError("authority private key is invalid")
    signature_field = "authorization_signature" if unsigned.get("schema_id") == "controller_authorization/v1" else "attestation_signature"
    return {**unsigned, signature_field: base64url_encode(private_key.sign(canonical_json_bytes(unsigned)))}


def load_private_ed25519_key(path: Path) -> Ed25519PrivateKey:
    try:
        private_key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    except (OSError, TypeError, ValueError) as exc:
        raise AuthorityError("authority private key is invalid") from exc
    if not isinstance(private_key, Ed25519PrivateKey):
        raise AuthorityError("authority private key is invalid")
    return private_key


def normalize_controller_authorization(value: Any, *, registry: dict[str, Any], policy: dict[str, Any], now: datetime) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _AUTHORIZATION_FIELDS:
        raise AuthorityError("controller authorization has invalid fields")
    if len(canonical_json_bytes(value)) > _positive_integer(policy.get("max_authorization_bytes"), "max_authorization_bytes"):
        raise AuthorityError("controller authorization is oversized")
    unsigned = {field: value[field] for field in _AUTHORIZATION_UNSIGNED_FIELDS}
    if unsigned["schema_id"] != "controller_authorization/v1":
        raise AuthorityError("controller authorization schema_id is invalid")
    authorization_id = _identifier(unsigned["authorization_id"], "authorization_id")
    run_id = _identifier(unsigned["run_id"], "run_id")
    attempt_id = _identifier(unsigned["attempt_id"], "attempt_id")
    packet_sha256 = _sha256(unsigned["packet_sha256"], "packet_sha256")
    outcome_id = _identifier(unsigned["outcome_id"], "outcome_id")
    outcome_digest = _sha256(unsigned["outcome_digest"], "outcome_digest")
    requested_decision = unsigned["requested_decision"]
    if requested_decision not in {"accept", "block", "waive"}:
        raise AuthorityError("controller authorization requested_decision is invalid")
    issuer_key_id = _identifier(unsigned["issuer_key_id"], "issuer_key_id")
    issued_at = _timestamp(unsigned["issued_at"], "issued_at")
    expires_at = _timestamp(unsigned["expires_at"], "expires_at")
    reason_sha256 = _sha256(unsigned["reason_sha256"], "reason_sha256")
    reason_length = _positive_integer(unsigned["reason_length"], "reason_length")
    clock_skew = timedelta(seconds=_positive_integer(policy.get("max_clock_skew_seconds"), "max_clock_skew_seconds"))
    if issued_at >= expires_at or expires_at - issued_at > timedelta(seconds=_positive_integer(policy.get("max_authorization_lifetime_seconds"), "max_authorization_lifetime_seconds")):
        raise AuthorityError("controller authorization lifetime is invalid")
    if issued_at > now + clock_skew or now > expires_at + clock_skew:
        raise AuthorityError("controller authorization timestamp is outside clock skew")
    if now - issued_at > timedelta(seconds=_positive_integer(policy.get("max_authorization_age_seconds"), "max_authorization_age_seconds")):
        raise AuthorityError("controller authorization is stale")
    entries = registry.get("entries") if isinstance(registry, dict) else None
    entry = entries.get(issuer_key_id) if isinstance(entries, dict) else None
    if not isinstance(entry, dict):
        raise AuthorityError("controller authorization issuer is unknown")
    if entry.get("status") != "active":
        raise AuthorityError("controller authorization issuer is revoked")
    allowed_roles = policy.get("allowed_controller_roles")
    if not isinstance(allowed_roles, list) or not set(entry.get("roles", [])) & set(allowed_roles):
        raise AuthorityError("controller authorization issuer role is not allowed")
    verify_document(unsigned, value["authorization_signature"], entry.get("public_key"))
    return {
        "authorization_id": authorization_id,
        "authorization_digest": document_digest(value),
        "run_id": run_id,
        "attempt_id": attempt_id,
        "packet_sha256": packet_sha256,
        "outcome_id": outcome_id,
        "outcome_digest": outcome_digest,
        "requested_decision": requested_decision,
        "issuer_key_id": issuer_key_id,
        "principal_id": entry["principal_id"],
        "key_fingerprint": entry["key_fingerprint"],
        "registry_digest": registry.get("registry_digest"),
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "reason_sha256": reason_sha256,
        "reason_length": reason_length,
    }
