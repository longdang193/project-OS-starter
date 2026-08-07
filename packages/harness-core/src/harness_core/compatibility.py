from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any


SUPPORTED_REQUEST_APIS = frozenset({2, 3})
SUPPORTED_PACKET_READ_APIS = frozenset({3})
CURRENT_PACKET_API = 3
SUPPORTED_HOST_APIS = frozenset({2})
TERMINAL_OBSERVATION_VERSION = 1
TIMEOUT_OBSERVATION_VERSION = TERMINAL_OBSERVATION_VERSION


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
    if value not in SUPPORTED_REQUEST_APIS:
        return {
            "ok": False,
            "code": "harness_core_request_api_incompatible",
            "request_api": value,
            "supported_request_apis": sorted(SUPPORTED_REQUEST_APIS),
        }
    return {"ok": True, "request_api": value, "packet_api": CURRENT_PACKET_API}


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
