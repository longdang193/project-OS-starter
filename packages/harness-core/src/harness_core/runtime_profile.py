from __future__ import annotations

import copy
import hashlib
import re
from typing import Any

from .authority import canonical_json_bytes
from .compatibility import COMPATIBILITY_PROFILES


class RuntimeProfileError(ValueError):
    pass


_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40,64}\Z")
_PROTOCOL_FIELDS = {
    "schema_id",
    "profile_id",
    "request_api",
    "packet_api",
    "host_api",
    "provider_id",
    "provider_contract",
    "required_capabilities",
    "profile_digest",
}
_RELEASE_FIELDS = {
    "schema_id",
    "release_profile_id",
    "release_profile_digest",
    "protocol_profile",
    "host_package_release",
    "host_commit",
    "core_package_release",
    "core_commit",
}


def _digest(payload: dict[str, Any], field: str) -> str:
    normalized = {key: value for key, value in payload.items() if key != field}
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def _positive_integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RuntimeProfileError(f"runtime profile has invalid {field}")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise RuntimeProfileError(f"runtime profile has invalid {field}")
    return value


def _commit(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _COMMIT.fullmatch(value):
        raise RuntimeProfileError(f"runtime profile has invalid {field}")
    return value


def _capabilities(value: Any) -> list[str]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or value != sorted(set(value))
    ):
        raise RuntimeProfileError("runtime profile has invalid required_capabilities")
    return list(value)


def normalize_runtime_protocol_profile(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _PROTOCOL_FIELDS:
        raise RuntimeProfileError("runtime protocol profile has invalid fields")
    if value.get("schema_id") != "harness_runtime_protocol_profile/v1":
        raise RuntimeProfileError("runtime protocol profile has unsupported schema_id")
    normalized = {
        "schema_id": "harness_runtime_protocol_profile/v1",
        "profile_id": _string(value.get("profile_id"), "profile_id"),
        "request_api": _positive_integer(value.get("request_api"), "request_api"),
        "packet_api": _positive_integer(value.get("packet_api"), "packet_api"),
        "host_api": _positive_integer(value.get("host_api"), "host_api"),
        "provider_id": _string(value.get("provider_id"), "provider_id"),
        "provider_contract": _positive_integer(value.get("provider_contract"), "provider_contract"),
        "required_capabilities": _capabilities(value.get("required_capabilities")),
        "profile_digest": value.get("profile_digest"),
    }
    if not isinstance(normalized["profile_digest"], str) or not _DIGEST.fullmatch(normalized["profile_digest"]):
        raise RuntimeProfileError("runtime profile has invalid profile_digest")
    if normalized["profile_digest"] != _digest(normalized, "profile_digest"):
        raise RuntimeProfileError("runtime profile digest conflicts with fields")
    return normalized


def runtime_protocol_profile(request_api: Any) -> dict[str, Any]:
    _positive_integer(request_api, "request_api")
    profile = next((item for item in COMPATIBILITY_PROFILES if request_api in item["request_apis"]), None)
    if profile is None:
        raise RuntimeProfileError("runtime profile has unsupported request_api")
    payload = {
        "schema_id": "harness_runtime_protocol_profile/v1",
        "profile_id": profile["name"],
        "request_api": request_api,
        "packet_api": profile["packet_api"],
        "host_api": profile["dispatch_host_api"],
        "provider_id": "codex_app_server",
        "provider_contract": profile["provider_contract"],
        "required_capabilities": sorted(profile.get("required_capabilities", ())),
    }
    payload["profile_digest"] = _digest(payload, "profile_digest")
    return normalize_runtime_protocol_profile(payload)


def runtime_protocol_profile_for_packet_api(packet_api: Any) -> dict[str, Any]:
    _positive_integer(packet_api, "packet_api")
    profile = next((item for item in COMPATIBILITY_PROFILES if item["packet_api"] == packet_api), None)
    if profile is None or not profile["request_apis"]:
        raise RuntimeProfileError("runtime profile has unsupported packet_api")
    return runtime_protocol_profile(min(profile["request_apis"]))


def normalize_runtime_release_profile(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _RELEASE_FIELDS:
        raise RuntimeProfileError("runtime release profile has invalid fields")
    if value.get("schema_id") != "harness_runtime_release/v1":
        raise RuntimeProfileError("runtime release profile has unsupported schema_id")
    normalized = {
        "schema_id": "harness_runtime_release/v1",
        "release_profile_id": _string(value.get("release_profile_id"), "release_profile_id"),
        "protocol_profile": normalize_runtime_protocol_profile(value.get("protocol_profile")),
        "host_package_release": _string(value.get("host_package_release"), "host_package_release"),
        "host_commit": _commit(value.get("host_commit"), "host_commit"),
        "core_package_release": _string(value.get("core_package_release"), "core_package_release"),
        "core_commit": _commit(value.get("core_commit"), "core_commit"),
        "release_profile_digest": value.get("release_profile_digest"),
    }
    if normalized["release_profile_id"] != normalized["protocol_profile"]["profile_id"]:
        raise RuntimeProfileError("runtime release profile conflicts with protocol profile")
    if not isinstance(normalized["release_profile_digest"], str) or not _DIGEST.fullmatch(normalized["release_profile_digest"]):
        raise RuntimeProfileError("runtime profile has invalid release_profile_digest")
    if normalized["release_profile_digest"] != _digest(normalized, "release_profile_digest"):
        raise RuntimeProfileError("runtime release profile digest conflicts with fields")
    return normalized


def build_runtime_release_profile(
    *,
    protocol_profile: Any,
    host_package_release: Any,
    host_commit: Any,
    core_package_release: Any,
    core_commit: Any,
) -> dict[str, Any]:
    protocol = normalize_runtime_protocol_profile(protocol_profile)
    payload = {
        "schema_id": "harness_runtime_release/v1",
        "release_profile_id": protocol["profile_id"],
        "protocol_profile": copy.deepcopy(protocol),
        "host_package_release": host_package_release,
        "host_commit": host_commit,
        "core_package_release": core_package_release,
        "core_commit": core_commit,
    }
    payload["release_profile_digest"] = _digest(payload, "release_profile_digest")
    return normalize_runtime_release_profile(payload)
