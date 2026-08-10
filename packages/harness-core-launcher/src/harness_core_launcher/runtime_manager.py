from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from typing import Any, Callable, Iterator, Sequence

_POINTER_SCHEMA = "harness_runtime_pointer/v1"
CONTROL_PLANE_TIMEOUT_SECONDS = 90


class RuntimeManagerError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _result_json(result: Any, *, failure: str) -> dict[str, Any]:
    if getattr(result, "returncode", 1) != 0:
        raise RuntimeManagerError(failure)
    try:
        payload = json.loads(getattr(result, "stdout", ""))
    except json.JSONDecodeError as exc:
        raise RuntimeManagerError(failure) from exc
    if not isinstance(payload, dict):
        raise RuntimeManagerError(failure)
    return payload


def _profile_digest(value: Any) -> str:
    if not isinstance(value, dict):
        raise RuntimeManagerError("harness_runtime_profile_invalid")
    digest = value.get("release_profile_digest")
    if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RuntimeManagerError("harness_runtime_profile_invalid")
    return digest


class RuntimeManager:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or Path.home() / ".codex" / "harness").resolve()

    @property
    def pointer_path(self) -> Path:
        return self.root / "current.json"

    @property
    def profiles_root(self) -> Path:
        return self.root / "profiles"

    @property
    def staging_root(self) -> Path:
        return self.root / "staging"

    @property
    def lock_path(self) -> Path:
        return self.root / "activation.lock"

    def _profile_root(self, digest: str) -> Path:
        return self.profiles_root / digest

    @contextmanager
    def _activation_lock(self) -> Iterator[None]:
        self.root.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+b")
        try:
            handle.seek(0)
            if not handle.read(1):
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeManagerError("harness_runtime_profile_activation_busy") from exc
            yield
        finally:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            handle.close()

    @staticmethod
    def _pointer_entry(profile: dict[str, Any]) -> dict[str, str]:
        return {"release_profile_digest": _profile_digest(profile)}

    def _write_pointer(self, pointer: dict[str, Any]) -> None:
        temporary = self.pointer_path.with_name(f".{self.pointer_path.name}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(_json(pointer), encoding="utf-8")
        with temporary.open("r+b") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, self.pointer_path)

    def _load_pointer(self) -> dict[str, Any]:
        if not self.pointer_path.is_file():
            raise RuntimeManagerError("harness_runtime_profile_unavailable")
        try:
            pointer = json.loads(self.pointer_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeManagerError("harness_runtime_profile_invalid") from exc
        if not isinstance(pointer, dict) or set(pointer) != {"schema_id", "current", "previous"}:
            raise RuntimeManagerError("harness_runtime_profile_invalid")
        if pointer["schema_id"] != _POINTER_SCHEMA:
            raise RuntimeManagerError("harness_runtime_profile_invalid")
        for key in ("current", "previous"):
            entry = pointer[key]
            if entry is None and key == "previous":
                continue
            if not isinstance(entry, dict) or set(entry) != {"release_profile_digest"}:
                raise RuntimeManagerError("harness_runtime_profile_invalid")
            digest = entry["release_profile_digest"]
            if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise RuntimeManagerError("harness_runtime_profile_invalid")
        if pointer["previous"] == pointer["current"]:
            raise RuntimeManagerError("harness_runtime_profile_invalid")
        return pointer

    def _load_profile(self, entry: dict[str, str]) -> tuple[dict[str, Any], Path]:
        digest = entry["release_profile_digest"]
        profile_root = self._profile_root(digest)
        release_path = profile_root / "release.json"
        host_root = profile_root / "host"
        try:
            profile = json.loads(release_path.read_text(encoding="utf-8"))
            profile_digest = _profile_digest(profile)
        except (OSError, RuntimeManagerError, json.JSONDecodeError) as exc:
            raise RuntimeManagerError("harness_runtime_profile_invalid") from exc
        if profile_digest != digest or not host_root.is_dir():
            raise RuntimeManagerError("harness_runtime_profile_invalid")
        return profile, profile_root

    def _active_profile(self) -> tuple[dict[str, Any], Path]:
        return self._load_profile(self._load_pointer()["current"])

    def _clean_profiles(self, pointer: dict[str, Any]) -> None:
        retained = {pointer["current"]["release_profile_digest"]}
        if pointer["previous"] is not None:
            retained.add(pointer["previous"]["release_profile_digest"])
        if not self.profiles_root.is_dir():
            return
        for path in self.profiles_root.iterdir():
            if path.is_dir() and path.name not in retained:
                shutil.rmtree(path)

    def _activate_locked(self, profile: dict[str, Any]) -> dict[str, Any]:
        profile_root = self._profile_root(_profile_digest(profile))
        if not (profile_root / "host").is_dir() or not (profile_root / "release.json").is_file():
            raise RuntimeManagerError("harness_runtime_profile_invalid")
        try:
            previous_pointer = self._load_pointer()
        except RuntimeManagerError as error:
            if error.code != "harness_runtime_profile_unavailable":
                raise
            previous_pointer = None
        entry = self._pointer_entry(profile)
        if previous_pointer is not None and previous_pointer["current"] == entry:
            self._clean_profiles(previous_pointer)
            return {"state": "ready", "changed": False, **profile}
        pointer = {
            "schema_id": _POINTER_SCHEMA,
            "current": entry,
            "previous": previous_pointer["current"] if previous_pointer is not None else None,
        }
        self._write_pointer(pointer)
        self._clean_profiles(pointer)
        return {"state": "ready", "changed": True, **profile}

    def activate(self, profile: dict[str, Any]) -> dict[str, Any]:
        with self._activation_lock():
            return self._activate_locked(profile)

    def rollback(self) -> dict[str, Any]:
        with self._activation_lock():
            pointer = self._load_pointer()
            previous = pointer["previous"]
            if previous is None:
                raise RuntimeManagerError("harness_runtime_profile_rollback_unavailable")
            profile, _ = self._load_profile(previous)
            return self._activate_locked(profile)

    def doctor(
        self,
        *,
        runner: Callable[..., Any] = subprocess.run,
    ) -> dict[str, Any]:
        profile, profile_root = self.verify_active_profile(runner=runner)
        return {"state": "ready", "host_root": str(profile_root / "host"), **profile}

    def verify_active_profile(
        self,
        *,
        runner: Callable[..., Any] = subprocess.run,
    ) -> tuple[dict[str, Any], Path]:
        profile, profile_root = self._active_profile()
        result = runner(
            [
                "uv", "--project", str(profile_root / "host"), "run", "--locked",
                "codex-harness-host", "release-profile", "--staging-root", str(profile_root), "--verify",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        verified = _result_json(result, failure="harness_runtime_profile_untrusted")
        if verified != profile:
            raise RuntimeManagerError("harness_runtime_profile_mismatch")
        return profile, profile_root

    def invoke_host(
        self,
        arguments: Sequence[str],
        *,
        runner: Callable[..., Any] = subprocess.run,
    ) -> dict[str, Any]:
        profile, profile_root = self.verify_active_profile(runner=runner)
        result = runner(
            [
                "uv", "--project", str(profile_root / "host"), "run", "--locked",
                "codex-harness-host", "--release-profile", str(profile_root / "release.json"), *arguments,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=None if arguments[0] == "run" else CONTROL_PLANE_TIMEOUT_SECONDS,
        )
        payload = _result_json(result, failure="harness_runtime_profile_preflight_failed")
        runtime_release_profile = payload.get("runtime_release_profile")
        if arguments[0] in {"capabilities", "preflight"} and runtime_release_profile != profile:
            raise RuntimeManagerError("harness_runtime_profile_mismatch")
        return payload

    def _stage_command(self, host_root: Path, *arguments: str, runner: Callable[..., Any]) -> Any:
        return runner(
            ["uv", "--project", str(host_root), "run", "--locked", "codex-harness-host", *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=CONTROL_PLANE_TIMEOUT_SECONDS,
        )

    def upgrade(
        self,
        host_source: Path,
        *,
        runner: Callable[..., Any] = subprocess.run,
    ) -> dict[str, Any]:
        source = host_source.resolve()
        if not (source / "uv.lock").is_file():
            raise RuntimeManagerError("harness_runtime_profile_untrusted")
        lock_text = (source / "uv.lock").read_text(encoding="utf-8")
        if "harness-core" not in lock_text or "editable = true" in lock_text:
            raise RuntimeManagerError("harness_runtime_profile_untrusted")
        status = runner(["git", "status", "--porcelain"], cwd=source, capture_output=True, text=True, check=False)
        if getattr(status, "returncode", 1) or getattr(status, "stdout", "").strip():
            raise RuntimeManagerError("harness_runtime_profile_untrusted")
        head = runner(["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True, check=False)
        if getattr(head, "returncode", 1) or len(getattr(head, "stdout", "").strip()) != 40:
            raise RuntimeManagerError("harness_runtime_profile_untrusted")
        with self._activation_lock():
            stage = self.staging_root / uuid.uuid4().hex
            staged_host = stage / "host"
            try:
                stage.mkdir(parents=True)
                worktree = runner(
                    ["git", "worktree", "add", "--detach", str(staged_host), getattr(head, "stdout").strip()],
                    cwd=source,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if getattr(worktree, "returncode", 1):
                    raise RuntimeManagerError("harness_runtime_profile_untrusted")
                synced = runner(["uv", "sync", "--locked"], cwd=staged_host, capture_output=True, text=True, check=False, timeout=300)
                if getattr(synced, "returncode", 1):
                    raise RuntimeManagerError("harness_runtime_profile_untrusted")
                profile = _result_json(
                    self._stage_command(staged_host, "release-profile", "--staging-root", str(stage), runner=runner),
                    failure="harness_runtime_profile_untrusted",
                )
                _profile_digest(profile)
                verified = _result_json(
                    self._stage_command(staged_host, "release-profile", "--staging-root", str(stage), "--verify", runner=runner),
                    failure="harness_runtime_profile_untrusted",
                )
                if verified != profile:
                    raise RuntimeManagerError("harness_runtime_profile_mismatch")
                preflight = _result_json(
                    self._stage_command(staged_host, "--release-profile", str(stage / "release.json"), "preflight", runner=runner),
                    failure="harness_runtime_profile_preflight_failed",
                )
                if preflight.get("runtime_release_profile") != profile:
                    raise RuntimeManagerError("harness_runtime_profile_mismatch")
                profile_root = self._profile_root(profile["release_profile_digest"])
                if profile_root.exists():
                    runner(["git", "worktree", "remove", "--force", str(staged_host)], cwd=source, capture_output=True, text=True, check=False)
                    return self._activate_locked(profile)
                profile_root.mkdir(parents=True)
                moved = runner(
                    ["git", "worktree", "move", str(staged_host), str(profile_root / "host")],
                    cwd=source,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if getattr(moved, "returncode", 1):
                    raise RuntimeManagerError("harness_runtime_profile_untrusted")
                os.replace(stage / "release.json", profile_root / "release.json")
                return self._activate_locked(profile)
            except (OSError, ValueError, RuntimeManagerError):
                if staged_host.exists():
                    runner(["git", "worktree", "remove", "--force", str(staged_host)], cwd=source, capture_output=True, text=True, check=False)
                raise
            finally:
                if stage.exists():
                    shutil.rmtree(stage, ignore_errors=True)
