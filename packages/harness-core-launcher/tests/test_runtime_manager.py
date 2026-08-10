from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness_core import build_runtime_release_profile, runtime_protocol_profile
import harness_core_launcher.runtime_manager as runtime_manager
from harness_core_launcher.runtime_manager import RuntimeManager, RuntimeManagerError


def _profile(host_commit: str) -> dict[str, object]:
    return build_runtime_release_profile(
        protocol_profile=runtime_protocol_profile(5),
        host_package_release="0.1.34",
        host_commit=host_commit,
        core_package_release="0.1.34",
        core_commit="a" * 40,
    )


def _write_profile(root: Path, profile: dict[str, object]) -> Path:
    profile_root = root / "profiles" / str(profile["release_profile_digest"])
    (profile_root / "host").mkdir(parents=True)
    (profile_root / "release.json").write_text(json.dumps(profile), encoding="utf-8")
    return profile_root


def test_doctor_rejects_missing_pointer(tmp_path: Path) -> None:
    with pytest.raises(RuntimeManagerError, match="harness_runtime_profile_unavailable"):
        RuntimeManager(tmp_path).doctor()


def test_activation_does_not_require_launcher_core_import(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = _profile("b" * 40)
    _write_profile(tmp_path, profile)
    monkeypatch.setattr(runtime_manager, "load_core", lambda: {"missing": True}, raising=False)

    assert RuntimeManager(tmp_path).activate(profile)["state"] == "ready"


def test_activate_is_idempotent_keeps_previous_and_rolls_back(tmp_path: Path) -> None:
    manager = RuntimeManager(tmp_path)
    first = _profile("b" * 40)
    second = _profile("c" * 40)
    _write_profile(tmp_path, first)

    assert manager.activate(first)["changed"] is True
    pointer_bytes = (tmp_path / "current.json").read_bytes()
    assert manager.activate(first)["changed"] is False
    assert (tmp_path / "current.json").read_bytes() == pointer_bytes

    _write_profile(tmp_path, second)
    manager.activate(second)
    pointer = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert pointer["current"]["release_profile_digest"] == second["release_profile_digest"]
    assert pointer["previous"]["release_profile_digest"] == first["release_profile_digest"]

    assert manager.rollback()["release_profile_digest"] == first["release_profile_digest"]


def test_activation_removes_unreferenced_profiles_only(tmp_path: Path) -> None:
    manager = RuntimeManager(tmp_path)
    first = _profile("b" * 40)
    second = _profile("c" * 40)
    third = _profile("d" * 40)
    _write_profile(tmp_path, first)
    manager.activate(first)
    _write_profile(tmp_path, second)
    manager.activate(second)
    _write_profile(tmp_path, third)
    manager.activate(second)

    assert (tmp_path / "profiles" / str(first["release_profile_digest"])).is_dir()
    assert (tmp_path / "profiles" / str(second["release_profile_digest"])).is_dir()
    assert not (tmp_path / "profiles" / str(third["release_profile_digest"])).exists()


def test_host_invocation_uses_active_profile_project_not_path(tmp_path: Path) -> None:
    profile = _profile("b" * 40)
    profile_root = _write_profile(tmp_path, profile)
    manager = RuntimeManager(tmp_path)
    manager.activate(profile)
    calls: list[list[str]] = []

    def run(command: list[str], **_kwargs: object):
        calls.append(command)

        class Result:
            returncode = 0
            stdout = json.dumps(profile if "release-profile" in command else {"state": "ready", "runtime_release_profile": profile})
            stderr = ""

        return Result()

    result = manager.invoke_host(["capabilities"], runner=run)

    assert result == {"state": "ready", "runtime_release_profile": profile}
    assert calls == [
        [
            "uv", "--project", str(profile_root / "host"), "run", "--locked",
            "codex-harness-host", "release-profile", "--staging-root", str(profile_root), "--verify",
        ],
        [
            "uv", "--project", str(profile_root / "host"), "run", "--locked",
            "codex-harness-host", "--release-profile", str(profile_root / "release.json"),
            "capabilities",
        ],
    ]


def test_host_run_invocation_defers_timeout_to_packet_owner(tmp_path: Path) -> None:
    profile = _profile("b" * 40)
    profile_root = _write_profile(tmp_path, profile)
    manager = RuntimeManager(tmp_path)
    manager.activate(profile)
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run(command: list[str], **kwargs: object):
        calls.append((command, kwargs))

        class Result:
            returncode = 0
            stdout = json.dumps(
                profile if "--verify" in command else {"state": "ready", "runtime_release_profile": profile}
            )
            stderr = ""

        return Result()

    manager.invoke_host(["run", "--harness-root", "repo", "--request", "request.json"], runner=run)
    manager.invoke_host(["capabilities"], runner=run)

    assert calls[1][0] == [
        "uv", "--project", str(profile_root / "host"), "run", "--locked",
        "codex-harness-host", "--release-profile", str(profile_root / "release.json"),
        "run", "--harness-root", "repo", "--request", "request.json",
    ]
    assert calls[1][1]["timeout"] is None
    assert calls[3][1]["timeout"] == 90


def test_host_invocation_returns_structured_error_on_nonzero_exit(tmp_path: Path) -> None:
    profile = _profile("b" * 40)
    _write_profile(tmp_path, profile)
    manager = RuntimeManager(tmp_path)
    manager.activate(profile)

    def run(command: list[str], **_kwargs: object):
        class Result:
            returncode = 2 if command[-1] == "run" else 0
            stdout = json.dumps(profile if "--verify" in command else {"status": "blocked", "error": "provider_configuration_changed"})
            stderr = "runtime changed"

        return Result()

    assert manager.invoke_host(["run"], runner=run) == {
        "status": "blocked",
        "error": "provider_configuration_changed",
    }


def test_host_invocation_uses_generic_error_for_malformed_nonzero_output(tmp_path: Path) -> None:
    profile = _profile("b" * 40)
    _write_profile(tmp_path, profile)
    manager = RuntimeManager(tmp_path)
    manager.activate(profile)

    def run(command: list[str], **_kwargs: object):
        class Result:
            returncode = 2 if command[-1] == "run" else 0
            stdout = json.dumps(profile) if "--verify" in command else "not-json"
            stderr = "runtime changed"

        return Result()

    with pytest.raises(RuntimeManagerError, match="harness_runtime_profile_preflight_failed"):
        manager.invoke_host(["run"], runner=run)


def test_pointer_rejects_profile_outside_profile_directory(tmp_path: Path) -> None:
    manager = RuntimeManager(tmp_path)
    profile = _profile("b" * 40)
    (tmp_path / "current.json").write_text(
        json.dumps({
            "schema_id": "harness_runtime_pointer/v1",
            "current": {"release_profile_digest": profile["release_profile_digest"]},
            "previous": None,
        }),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeManagerError, match="harness_runtime_profile_invalid"):
        manager.doctor()
