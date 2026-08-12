from __future__ import annotations

import pytest

from harness_core.runtime_profile import (
    RuntimeProfileError,
    build_runtime_release_profile,
    normalize_runtime_protocol_profile,
    runtime_protocol_profile,
)


def test_current_runtime_protocol_profile_is_canonical() -> None:
    profile = runtime_protocol_profile(5)

    assert profile == {
        "schema_id": "harness_runtime_protocol_profile/v1",
        "profile_id": "optional_tool_bindings",
        "request_api": 5,
        "packet_api": 10,
        "host_api": 9,
        "provider_id": "codex_app_server",
        "provider_contract": 9,
        "required_capabilities": [
            "execution_lease_duration_model",
            "host_terminal_observation_v3",
            "optional_tool_bindings",
        ],
        "profile_digest": "9251824356559cd4c32cfd945d3d5912937fc8be04856961f1844a0726ff8af0",
    }


def test_release_profile_binds_protocol_and_provenance() -> None:
    release = build_runtime_release_profile(
        protocol_profile=runtime_protocol_profile(5),
        host_package_release="0.1.25",
        host_commit="a" * 40,
        core_package_release="0.1.34",
        core_commit="b" * 40,
    )

    assert release["schema_id"] == "harness_runtime_release/v1"
    assert release["release_profile_id"] == "optional_tool_bindings"
    assert release["protocol_profile"] == runtime_protocol_profile(5)
    assert release["release_profile_digest"] == "4cc04aa935d75041e033f53a530a27c71c967ab236ae36457c375278c620fb66"


@pytest.mark.parametrize(
    "value",
    [
        {"request_api": True},
        runtime_protocol_profile(5) | {"unknown": "value"},
    ],
)
def test_runtime_profile_rejects_invalid_inputs(value: dict[str, object]) -> None:
    with pytest.raises(RuntimeProfileError):
        if "unknown" in value:
            normalize_runtime_protocol_profile(value)
        else:
            runtime_protocol_profile(value.get("request_api"))
