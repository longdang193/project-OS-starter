from __future__ import annotations

import harness_core

from harness_core.compatibility import (
    CURRENT_PACKET_API,
    CURRENT_RUN_API,
    SUPPORTED_HOST_APIS,
    SUPPORTED_PACKET_READ_APIS,
    SUPPORTED_REQUEST_APIS,
    admit_packet_dispatch,
    admit_host_api,
    admit_request_api,
    can_read_packet_api,
    legacy_role_capabilities,
    static_provider_runtime_binding,
)


def test_protocol_matrix_is_exact() -> None:
    assert SUPPORTED_REQUEST_APIS == frozenset({2, 3, 5})
    assert SUPPORTED_PACKET_READ_APIS == frozenset({3, 4, 5, 6, 7, 8, 9, 10})
    assert CURRENT_PACKET_API == 10
    assert CURRENT_RUN_API == 2
    assert SUPPORTED_HOST_APIS == frozenset({2, 3, 4, 5, 6, 7, 8, 9})


def test_public_package_exports_current_protocol_constants() -> None:
    assert harness_core.CURRENT_PACKET_API == 10
    assert harness_core.CURRENT_RUN_API == 2
    assert harness_core.SUPPORTED_HOST_APIS == frozenset({2, 3, 4, 5, 6, 7, 8, 9})
    assert harness_core.APP_SERVER_MODEL_SELECTION_FIELDS == (
        "model_provider",
        "model",
        "reasoning_effort",
    )
    assert harness_core.APP_SERVER_MODEL_SELECTION_FIELDS == (
        "model_provider",
        "model",
        "reasoning_effort",
    )


def test_static_provider_runtime_binding_omits_host_identity() -> None:
    binding = {
        "provider_id": "codex_app_server",
        "configuration_digest": "a" * 64,
        "host_instance_id": "host-prior",
    }

    assert static_provider_runtime_binding(binding) == {
        "provider_id": "codex_app_server",
        "configuration_digest": "a" * 64,
    }
    assert harness_core.static_provider_runtime_binding(binding) == {
        "provider_id": "codex_app_server",
        "configuration_digest": "a" * 64,
    }


def test_request_and_host_admission_return_typed_results() -> None:
    assert admit_request_api(3) == {"ok": True, "request_api": 3, "packet_api": 3, "profile": "legacy_dispatch"}
    assert admit_request_api(5) == {"ok": True, "request_api": 5, "packet_api": 10, "profile": "optional_tool_bindings"}
    assert admit_request_api("3") == {
        "ok": False,
        "code": "harness_core_request_api_invalid",
        "request_api": "3",
    }
    assert admit_request_api(1) == {
        "ok": False,
        "code": "harness_core_request_api_incompatible",
        "request_api": 1,
        "supported_request_apis": [2, 3, 5],
    }
    assert admit_host_api(2) == {"ok": True, "host_api": 2}
    assert admit_host_api(3) == {"ok": True, "host_api": 3}
    assert admit_host_api(4) == {"ok": True, "host_api": 4}
    assert admit_host_api(5) == {"ok": True, "host_api": 5}
    assert admit_host_api(6) == {"ok": True, "host_api": 6}
    assert admit_host_api(1) == {
        "ok": False,
        "code": "harness_core_host_api_incompatible",
        "host_api": 1,
        "supported_host_apis": [2, 3, 4, 5, 6, 7, 8, 9],
    }


def test_packet_dispatch_uses_matrix_without_host_fallback() -> None:
    assert can_read_packet_api(3) is True
    assert can_read_packet_api(4) is True
    assert can_read_packet_api(5) is True
    assert can_read_packet_api(6) is True
    assert can_read_packet_api(7) is True
    assert admit_packet_dispatch(2, 3, 2) == {"ok": True, "host_api": 2, "packet_api": 3, "profile": "legacy_dispatch"}
    assert admit_packet_dispatch(3, 4, 3) == {"ok": True, "host_api": 3, "packet_api": 4, "profile": "invocation"}
    assert admit_packet_dispatch(4, 5, 4) == {"ok": True, "host_api": 4, "packet_api": 5, "profile": "provider_transport"}
    assert admit_packet_dispatch(5, 6, 5) == {"ok": True, "host_api": 5, "packet_api": 6, "profile": "artifact_handoff_legacy"}
    assert admit_packet_dispatch(6, 7, 6) == {"ok": True, "host_api": 6, "packet_api": 7, "profile": "claim_repair"}
    assert admit_packet_dispatch(3, 3, 2) == {
        "ok": False,
        "code": "harness_core_packet_dispatch_incompatible",
        "host_api": 3,
        "packet_api": 3,
    }
    assert admit_packet_dispatch(3, 4, 4) == {
        "ok": False,
        "code": "harness_core_packet_dispatch_incompatible",
        "host_api": 3,
        "packet_api": 4,
    }
    assert admit_packet_dispatch(4, 5, 3) == {
        "ok": False,
        "code": "harness_core_packet_dispatch_incompatible",
        "host_api": 4,
        "packet_api": 5,
    }
    assert can_read_packet_api(2) is False
    assert can_read_packet_api("3") is False


def test_legacy_role_capabilities_preserve_api3_write_authority() -> None:
    assert legacy_role_capabilities("implement") == ("repo.write",)
    assert legacy_role_capabilities("improve") == ("repo.write",)
    assert legacy_role_capabilities("investigate") == ()
