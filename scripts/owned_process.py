"""Bounded subprocess execution with owned process-tree cleanup."""

from __future__ import annotations

import ctypes
import os
import queue
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Callable, Literal

ProcessStatus = Literal["success", "timeout", "output_limit", "nonzero_exit", "command_failed", "spawn_failed", "BLOCKED"]


@dataclass(frozen=True)
class OwnedProcessResult:
    status: ProcessStatus
    returncode: int | None = None
    stdout: bytes = b""
    stderr: bytes = b""
    cleanup_confirmed: bool = True
    error: BaseException | None = None
    reason: str | None = None


def _create_windows_job(process: subprocess.Popen[bytes]) -> object | None:
    if os.name != "nt":
        return None
    from ctypes import wintypes

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

    class IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", BasicLimitInformation), ("IoInfo", IoCounters), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.CloseHandle.restype = wintypes.BOOL
    job = kernel32.CreateJobObjectW(None, None)
    process_handle = getattr(process, "_handle", None)
    if not job or process_handle is None:
        if job:
            kernel32.CloseHandle(job)
        return None
    limits = ExtendedLimitInformation()
    limits.BasicLimitInformation.LimitFlags = 0x2000
    if not kernel32.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not kernel32.AssignProcessToJobObject(job, process_handle):
        kernel32.CloseHandle(job)
        return None
    return job


def _close_windows_job(job: object | None) -> bool:
    if job is None or os.name != "nt":
        return True
    return bool(ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(job))


def _kill_windows_process_tree(pid: int) -> bool:
    if os.name != "nt":
        return False
    try:
        result = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, capture_output=True, timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _group_gone(pid: int) -> bool:
    if not hasattr(os, "killpg"):
        return False
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _terminate_process_tree(process: subprocess.Popen[bytes], job: object | None, *, platform_name: str, close_job: Callable[[object | None], bool], kill_tree: Callable[[int], bool]) -> bool:
    if platform_name == "nt":
        confirmed = close_job(job) if job is not None else kill_tree(process.pid)
        try:
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return confirmed and _returncode(process) is not None
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            return False
    except (OSError, AttributeError):
        try:
            process.kill()
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            return False
    return _returncode(process) is not None and _group_gone(process.pid)


def _confirm_process_tree_retired(process: subprocess.Popen[bytes], *, platform_name: str, job: object | None, close_job: Callable[[object | None], bool], kill_tree: Callable[[int], bool]) -> bool:
    if platform_name == "nt":
        return True
    if _group_gone(process.pid):
        return True
    return _terminate_process_tree(process, job, platform_name=platform_name, close_job=close_job, kill_tree=kill_tree)


def _returncode(process: object) -> int | None:
    value = getattr(process, "poll", lambda: getattr(process, "returncode", None))()
    return value if isinstance(value, int) else None


def _read_pipe(pipe: object, stream: str, output: queue.Queue[tuple[str, bytes]]) -> None:
    try:
        while True:
            chunk = pipe.read(8192)  # type: ignore[attr-defined]
            if not chunk:
                break
            output.put((stream, chunk))
    finally:
        output.put(("done", b""))


def run_owned_process(argv: list[str], *, cwd: str | os.PathLike[str], env: dict[str, str] | None = None, timeout: float, max_output_bytes: int = 4 * 1024 * 1024, input_data: bytes | str | None = None, capture_output: bool = True, popen_factory: Callable[..., subprocess.Popen[bytes]] | None = None, platform_name: str | None = None, create_job: Callable[[subprocess.Popen[bytes]], object | None] | None = None, close_job: Callable[[object | None], bool] | None = None, kill_tree: Callable[[int], bool] | None = None) -> OwnedProcessResult:
    if timeout <= 0 or max_output_bytes < 0:
        raise ValueError("timeout and max_output_bytes must be non-negative, timeout positive")
    platform_name = platform_name or os.name
    popen_factory = popen_factory or subprocess.Popen
    create_job = create_job or _create_windows_job
    close_job = close_job or _close_windows_job
    kill_tree = kill_tree or _kill_windows_process_tree
    kwargs: dict[str, object] = {"cwd": cwd, "env": env, "stdin": subprocess.PIPE if input_data is not None else None, "stdout": subprocess.PIPE if capture_output else None, "stderr": subprocess.PIPE if capture_output else None, "close_fds": True}
    if isinstance(input_data, str) and capture_output:
        input_data = input_data.encode()
    elif isinstance(input_data, str):
        kwargs["text"] = True
    if platform_name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
    try:
        process = popen_factory(argv, **kwargs)
    except OSError as exc:
        return OwnedProcessResult("spawn_failed", error=exc)
    job = create_job(process) if platform_name == "nt" else None
    if platform_name == "nt" and job is None:
        confirmed = kill_tree(process.pid)
        try:
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            confirmed = False
        return OwnedProcessResult("BLOCKED", returncode=_returncode(process), cleanup_confirmed=confirmed, reason="cleanup_unconfirmed")
    if not capture_output:
        result: OwnedProcessResult
        try:
            if input_data is None:
                returncode = process.wait(timeout=timeout)
            else:
                process.communicate(input=input_data, timeout=timeout)
                returncode = process.returncode
            result = OwnedProcessResult("success" if returncode == 0 else "nonzero_exit", returncode=returncode)
        except subprocess.TimeoutExpired:
            confirmed = _terminate_process_tree(process, job, platform_name=platform_name, close_job=close_job, kill_tree=kill_tree)
            job = None
            result = OwnedProcessResult("timeout" if confirmed else "BLOCKED", returncode=_returncode(process), cleanup_confirmed=confirmed, reason="timeout")
        except OSError as exc:
            result = OwnedProcessResult("command_failed", returncode=_returncode(process), cleanup_confirmed=False, error=exc)
        if platform_name != "nt" and not _confirm_process_tree_retired(process, platform_name=platform_name, job=job, close_job=close_job, kill_tree=kill_tree):
            return OwnedProcessResult(
                "BLOCKED",
                returncode=_returncode(process),
                cleanup_confirmed=False,
                error=result.error,
                reason=result.reason or "cleanup_unconfirmed",
            )
        if platform_name == "nt" and job is not None:
            try:
                closed = bool(close_job(job))
            except (OSError, ValueError):
                closed = False
            if not closed:
                return OwnedProcessResult("BLOCKED", returncode=_returncode(process), cleanup_confirmed=False, error=result.error, reason="cleanup_unconfirmed")
        return result
    started = time.monotonic()
    output: queue.Queue[tuple[str, bytes]] = queue.Queue()
    threads = []
    if process.stdout is not None:
        threads.append(threading.Thread(target=_read_pipe, args=(process.stdout, "stdout", output), daemon=True))
    if process.stderr is not None:
        threads.append(threading.Thread(target=_read_pipe, args=(process.stderr, "stderr", output), daemon=True))
    for thread in threads:
        thread.start()
    if input_data is not None and process.stdin is not None:
        try:
            process.stdin.write(input_data)
            process.stdin.close()
        except OSError:
            pass
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    done = 0
    overflow = False
    timed_out = False
    while done < len(threads):
        remaining = timeout - (time.monotonic() - started)
        if remaining <= 0:
            timed_out = True
            break
        try:
            name, chunk = output.get(timeout=min(remaining, 0.05))
        except queue.Empty:
            continue
        if name == "done":
            done += 1
            continue
        buffers[name].extend(chunk)
        if len(buffers["stdout"]) + len(buffers["stderr"]) > max_output_bytes:
            overflow = True
            break
    if timed_out or overflow:
        confirmed = _terminate_process_tree(process, job, platform_name=platform_name, close_job=close_job, kill_tree=kill_tree)
        job = None
        status: ProcessStatus = "output_limit" if overflow else "timeout"
        if not confirmed:
            status = "BLOCKED"
        for thread in threads:
            thread.join(timeout=2)
        return OwnedProcessResult(status, _returncode(process), bytes(buffers["stdout"]), bytes(buffers["stderr"]), confirmed, reason="output_limit" if overflow else "timeout")
    for thread in threads:
        thread.join(timeout=max(0.0, timeout - (time.monotonic() - started)))
    try:
        returncode = process.wait(timeout=max(0.0, timeout - (time.monotonic() - started)))
    except subprocess.TimeoutExpired:
        confirmed = _terminate_process_tree(process, job, platform_name=platform_name, close_job=close_job, kill_tree=kill_tree)
        job = None
        return OwnedProcessResult("timeout" if confirmed else "BLOCKED", _returncode(process), bytes(buffers["stdout"]), bytes(buffers["stderr"]), confirmed, reason="timeout")
    if platform_name == "nt" and job is not None:
        try:
            closed = bool(close_job(job))
        except (OSError, ValueError):
            closed = False
        if not closed:
            return OwnedProcessResult("BLOCKED", _returncode(process), bytes(buffers["stdout"]), bytes(buffers["stderr"]), False, reason="cleanup_unconfirmed")
    return OwnedProcessResult("success" if returncode == 0 else "nonzero_exit", returncode, bytes(buffers["stdout"]), bytes(buffers["stderr"]))
