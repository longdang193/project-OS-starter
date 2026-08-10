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
        "profile_id": "runtime_profile",
        "request_api": 5,
        "packet_api": 9,
        "host_api": 8,
        "provider_id": "codex_app_server",
        "provider_contract": 8,
        "required_capabilities": [
            "execution_lease_duration_model",
            "host_terminal_observation_v3",
        ],
        "profile_digest": "e4221ea715f52289ad99d2775fe15156f9f3d3fb8d2b6dda1a886ab0f7f69fee",
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
    assert release["release_profile_id"] == "runtime_profile"
    assert release["protocol_profile"] == runtime_protocol_profile(5)
    assert release["release_profile_digest"] == "28fe85505cb2a22ce3dea39cd4f1c06b47b1f554d8791476de29be33a22f35a6"


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
