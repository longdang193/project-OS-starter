from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any


COMPATIBILITY_PROFILES = (
    {
        "name": "legacy_dispatch",
        "request_apis": frozenset({2, 3}),
        "packet_api": 3,
        "dispatch_host_api": 2,
        "read_host_apis": frozenset({2, 3}),
    },
    {
        "name": "invocation",
        "request_apis": frozenset({4}),
        "packet_api": 4,
        "dispatch_host_api": 3,
        "read_host_apis": frozenset({3}),
    },
)
SUPPORTED_REQUEST_APIS = frozenset().union(*(profile["request_apis"] for profile in COMPATIBILITY_PROFILES))
SUPPORTED_PACKET_READ_APIS = frozenset(profile["packet_api"] for profile in COMPATIBILITY_PROFILES)
CURRENT_PACKET_API = 4
CURRENT_RUN_API = 2
SUPPORTED_HOST_APIS = frozenset({profile["dispatch_host_api"] for profile in COMPATIBILITY_PROFILES})
TERMINAL_OBSERVATION_VERSION = 1
TIMEOUT_OBSERVATION_VERSION = TERMINAL_OBSERVATION_VERSION
# ponytail: temporary API 2/3 authority map; remove when packet API 3 dispatch support ends.
LEGACY_ROLE_CAPABILITIES = {
    "implement": ("repo.write",),
    "improve": ("repo.write",),
    "investigate": (),
    "review": (),
    "validate": (),
}


def package_release() -> str:
    try:
        return version("harness-core")
    except PackageNotFoundError as exc:
        raise RuntimeError("harness-core package metadata is unavailable") from exc


def admit_request_api(value: Any) -> dict[str, Any]:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        return {
            "ok": False,
            "code": "harness_core_request_api_invalid",
            "request_api": value,
        }
    profile = next((candidate for candidate in COMPATIBILITY_PROFILES if value in candidate["request_apis"]), None)
    if profile is None:
        return {
            "ok": False,
            "code": "harness_core_request_api_incompatible",
            "request_api": value,
            "supported_request_apis": sorted(SUPPORTED_REQUEST_APIS),
        }
    return {"ok": True, "request_api": value, "packet_api": profile["packet_api"], "profile": profile["name"]}


def admit_host_api(value: Any) -> dict[str, Any]:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        return {
            "ok": False,
            "code": "harness_core_host_api_incompatible",
            "host_api": value,
            "supported_host_apis": sorted(SUPPORTED_HOST_APIS),
        }
    if value not in SUPPORTED_HOST_APIS:
        return {
            "ok": False,
            "code": "harness_core_host_api_incompatible",
            "host_api": value,
            "supported_host_apis": sorted(SUPPORTED_HOST_APIS),
        }
    return {"ok": True, "host_api": value}


def can_read_packet_api(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value in SUPPORTED_PACKET_READ_APIS


def legacy_role_capabilities(role: str) -> tuple[str, ...]:
    try:
        return LEGACY_ROLE_CAPABILITIES[role]
    except KeyError as exc:
        raise ValueError(f"legacy role `{role}` has no compatibility authority") from exc


def admit_packet_dispatch(host_api: Any, packet_api: Any) -> dict[str, Any]:
    if not isinstance(host_api, int) or isinstance(host_api, bool) or not isinstance(packet_api, int) or isinstance(packet_api, bool):
        return {
            "ok": False,
            "code": "harness_core_packet_dispatch_incompatible",
            "host_api": host_api,
            "packet_api": packet_api,
        }
    profile = next(
        (
            candidate
            for candidate in COMPATIBILITY_PROFILES
            if candidate["dispatch_host_api"] == host_api and candidate["packet_api"] == packet_api
        ),
        None,
    )
    if profile is None:
        return {
            "ok": False,
            "code": "harness_core_packet_dispatch_incompatible",
            "host_api": host_api,
            "packet_api": packet_api,
        }
    return {"ok": True, "host_api": host_api, "packet_api": packet_api, "profile": profile["name"]}
