from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import subprocess
import signal

import pytest

_OWNED_PROCESS_PATH = Path(__file__).resolve().parents[1] / "scripts" / "owned_process.py"
_OWNED_PROCESS_SPEC = importlib.util.spec_from_file_location(
    "repo_owned_process", _OWNED_PROCESS_PATH
)
if _OWNED_PROCESS_SPEC is None or _OWNED_PROCESS_SPEC.loader is None:
    raise RuntimeError(f"Unable to load {_OWNED_PROCESS_PATH.name}")
owned_process = importlib.util.module_from_spec(_OWNED_PROCESS_SPEC)
sys.modules[_OWNED_PROCESS_SPEC.name] = owned_process
_OWNED_PROCESS_SPEC.loader.exec_module(owned_process)
run_owned_process = owned_process.run_owned_process


def test_run_owned_process_captures_bytes_and_status(tmp_path) -> None:
    result = run_owned_process(
        [sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr)"],
        cwd=tmp_path,
        timeout=5,
    )

    assert result.status == "success"
    assert result.stdout.replace(b"\r\n", b"\n") == b"out\n"
    assert result.stderr.replace(b"\r\n", b"\n") == b"err\n"


def test_run_owned_process_verifies_descendants_after_normal_parent_exit(tmp_path, monkeypatch) -> None:
    class FakeProcess:
        pid = 42
        returncode = 0

        def wait(self, timeout=None):
            return self.returncode

        def poll(self):
            return self.returncode

    group_checks = iter([False, True])
    kill_calls = []
    monkeypatch.setattr(owned_process, "_group_gone", lambda pid: next(group_checks))
    monkeypatch.setattr(owned_process.os, "killpg", lambda pid, sig: kill_calls.append((pid, sig)), raising=False)
    result = run_owned_process(
        ["worker"],
        cwd=tmp_path,
        timeout=5,
        capture_output=False,
        platform_name="posix",
        popen_factory=lambda *args, **kwargs: FakeProcess(),
    )

    assert result.status == "success"
    assert result.cleanup_confirmed is True
    assert kill_calls == [(42, signal.SIGTERM)]


def test_run_owned_process_captures_output_and_verifies_descendants_after_parent_exit(tmp_path, monkeypatch) -> None:
    class Pipe:
        def read(self, size):
            return b""

    class FakeProcess:
        pid = 42
        returncode = 0
        stdout = Pipe()
        stderr = Pipe()

        def wait(self, timeout=None):
            return self.returncode

        def poll(self):
            return self.returncode

    confirmation_calls = []
    monkeypatch.setattr(
        owned_process,
        "_confirm_process_tree_retired",
        lambda process, **kwargs: confirmation_calls.append(process.pid) or True,
    )

    result = owned_process.run_owned_process(
        ["worker"],
        cwd=tmp_path,
        timeout=5,
        platform_name="posix",
        popen_factory=lambda *args, **kwargs: FakeProcess(),
    )

    assert result.status == "success"
    assert result.cleanup_confirmed is True
    assert confirmation_calls == [42]


def test_run_owned_process_rejects_output_overflow(tmp_path) -> None:
    result = run_owned_process(
        [sys.executable, "-c", "print('x' * 100)"],
        cwd=tmp_path,
        timeout=5,
        max_output_bytes=10,
    )

    assert result.status == "output_limit"
    assert result.cleanup_confirmed is True


def test_run_owned_process_blocks_when_tree_cleanup_is_unconfirmed(tmp_path) -> None:
    class FakeProcess:
        pid = 42
        returncode = None

        def wait(self, timeout=None):
            if self.returncode is None:
                raise subprocess.TimeoutExpired(["worker"], timeout)
            return self.returncode

        def poll(self):
            return self.returncode

    process = FakeProcess()
    result = run_owned_process(
        ["worker"],
        cwd=tmp_path,
        timeout=1,
        capture_output=False,
        platform_name="nt",
        popen_factory=lambda *args, **kwargs: process,
        create_job=lambda value: None,
        kill_tree=lambda pid: False,
    )

    assert result.status == "BLOCKED"
    assert result.cleanup_confirmed is False


def test_run_owned_process_blocks_when_windows_job_close_fails(tmp_path) -> None:
    class FakeProcess:
        pid = 42
        returncode = 0

        def wait(self, timeout=None):
            return self.returncode

    result = run_owned_process(
        ["worker"],
        cwd=tmp_path,
        timeout=1,
        capture_output=False,
        platform_name="nt",
        popen_factory=lambda *args, **kwargs: FakeProcess(),
        create_job=lambda process: "job",
        close_job=lambda job: False,
        kill_tree=lambda pid: False,
    )

    assert result.status == "BLOCKED"
    assert result.cleanup_confirmed is False
    assert result.reason == "cleanup_unconfirmed"


def test_run_owned_process_closes_windows_job_once_after_timeout(tmp_path) -> None:
    class FakeProcess:
        pid = 42
        returncode = None

        def wait(self, timeout=None):
            if self.returncode is None:
                raise subprocess.TimeoutExpired(["worker"], timeout)
            return self.returncode

    process = FakeProcess()
    close_calls = []

    def close_job(job):
        close_calls.append(job)
        process.returncode = -9
        return True

    result = run_owned_process(
        ["worker"],
        cwd=tmp_path,
        timeout=1,
        capture_output=False,
        platform_name="nt",
        popen_factory=lambda *args, **kwargs: process,
        create_job=lambda process: "job",
        close_job=close_job,
        kill_tree=lambda pid: False,
    )

    assert result.status == "timeout"
    assert close_calls == ["job"]


def test_run_owned_process_accepts_text_input_while_capturing(tmp_path) -> None:
    result = run_owned_process(
        [sys.executable, "-c", "print('out')"],
        cwd=tmp_path,
        timeout=5,
        input_data="",
    )

    assert result.status == "success"
    assert result.stdout.replace(b"\r\n", b"\n") == b"out\n"
