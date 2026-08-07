from __future__ import annotations

from harness_core.compatibility import (
    CURRENT_PACKET_API,
    SUPPORTED_HOST_APIS,
    SUPPORTED_PACKET_READ_APIS,
    SUPPORTED_REQUEST_APIS,
    admit_host_api,
    admit_request_api,
    can_read_packet_api,
)


def test_protocol_matrix_is_exact() -> None:
    assert SUPPORTED_REQUEST_APIS == frozenset({2, 3})
    assert SUPPORTED_PACKET_READ_APIS == frozenset({3})
    assert CURRENT_PACKET_API == 3
    assert SUPPORTED_HOST_APIS == frozenset({2})


def test_request_and_host_admission_return_typed_results() -> None:
    assert admit_request_api(3) == {"ok": True, "request_api": 3, "packet_api": 3}
    assert admit_request_api("3") == {
        "ok": False,
        "code": "harness_core_request_api_invalid",
        "request_api": "3",
    }
    assert admit_request_api(1) == {
        "ok": False,
        "code": "harness_core_request_api_incompatible",
        "request_api": 1,
        "supported_request_apis": [2, 3],
    }
    assert admit_host_api(2) == {"ok": True, "host_api": 2}
    assert admit_host_api(1) == {
        "ok": False,
        "code": "harness_core_host_api_incompatible",
        "host_api": 1,
        "supported_host_apis": [2],
    }


def test_only_current_packet_api_is_readable() -> None:
    assert can_read_packet_api(3) is True
    assert can_read_packet_api(2) is False
    assert can_read_packet_api("3") is False
