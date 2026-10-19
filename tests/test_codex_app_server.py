from __future__ import annotations

import json
import queue
import threading
from pathlib import Path
from typing import Any

import pytest

from scripts.project_os_runtime.codex_app_server import CodexAppServerClient, NativeAppServerError, NativeTurn


class FakeStdout:
    def __init__(self) -> None:
        self.values: queue.Queue[bytes | None] = queue.Queue()
        self.limits: list[int | None] = []
        self.readers: set[int] = set()
        self.max_concurrent_reads = 0
        self._concurrent_reads = 0
        self._lock = threading.Lock()

    def push(self, value: dict[str, Any]) -> None:
        self.values.put((json.dumps(value) + "\n").encode("utf-8"))

    def close_input(self) -> None:
        self.values.put(None)

    def readline(self, limit: int | None = None) -> bytes:
        self.limits.append(limit)
        reader = threading.get_ident()
        with self._lock:
            self.readers.add(reader)
            self._concurrent_reads += 1
            self.max_concurrent_reads = max(self.max_concurrent_reads, self._concurrent_reads)
        try:
            value = self.values.get(timeout=2)
            return b"" if value is None else value
        finally:
            with self._lock:
                self._concurrent_reads -= 1

    def close(self) -> None:
        self.close_input()


class FakeStdin:
    def __init__(self, process: "FakeProcess") -> None:
        self.process = process
        self.buffer = b""
        self.max_write: int | None = None
        self.zero_progress = False

    def write(self, value: bytes) -> int:
        if self.zero_progress:
            return 0
        chunk = value if self.max_write is None else value[: self.max_write]
        self.buffer += chunk
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            if line:
                self.process.handle(json.loads(line.decode("utf-8")))
        return len(chunk)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


class FakeProcess:
    def __init__(self) -> None:
        self.stdout = FakeStdout()
        self.stderr = FakeStdout()
        self.stdin = FakeStdin(self)
        self.requests: list[dict[str, Any]] = []
        self.returncode: int | None = None
        self.terminated = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0
        self.stdout.close_input()

    def kill(self) -> None:
        self.returncode = -9
        self.stdout.close_input()

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode or 0

    def handle(self, request: dict[str, Any]) -> None:
        self.requests.append(request)
        method = request.get("method")
        request_id = request.get("id")
        if method == "initialize":
            self.stdout.push({"method": "server/info", "params": {"message": "ready"}})
            self.stdout.push({"id": request_id, "result": {"capabilities": {}}})
        elif method == "initialized":
            assert request_id is None
        elif method == "thread/start":
            self.stdout.push({
                "id": request_id,
                "result": {"thread": {
                    "id": "thread-1", "sessionId": "session-1", "ephemeral": True,
                    "status": {"type": "idle"}, "turns": [],
                }},
            })
        elif method == "turn/start":
            self.stdout.push({"id": request_id, "result": {"turn": {"id": "turn-1"}}})
            self.stdout.push({"method": "item/completed", "params": {
                "threadId": "thread-other", "turnId": "turn-other",
                "item": {"id": "other", "type": "agentMessage", "text": "ignore"},
            }})
            self.stdout.push({"method": "item/completed", "params": {
                "threadId": "thread-1", "turnId": "turn-1",
                "item": {"id": "tool", "type": "toolResult", "text": "ignore"},
            }})
            self.stdout.push({"method": "item/completed", "params": {
                "threadId": "thread-1", "turnId": "turn-1",
                "item": {"id": "item-2", "type": "agentMessage", "order": 2, "finalized": True, "provenance": "final_answer", "text": " world"},
            }})
            self.stdout.push({"method": "item/completed", "params": {
                "threadId": "thread-1", "turnId": "turn-1",
                "item": {"id": "item-1", "type": "agentMessage", "order": 1, "finalized": True, "provenance": "final_answer", "text": "hello"},
            }})
            self.stdout.push({"method": "turn/completed", "params": {
                "threadId": "thread-1", "turn": {"id": "turn-1", "status": {"type": "completed"}},
            }})
        else:
            raise AssertionError(f"unexpected method {method}")


def test_close_exposes_structured_retirement_evidence() -> None:
    client = CodexAppServerClient(
        "codex",
        cwd=Path("C:/worktree"),
        codex_home=Path("C:/codex"),
    )
    process = FakeProcess()
    process.returncode = None
    client._process = process
    client._started = True

    evidence = client.close()

    assert evidence["state"] == "retired"
    assert evidence["method"] == "terminate"
    assert evidence["writer"] == "not_started"
    assert evidence["reader"] == "not_started"
    assert client.retirement_evidence == evidence
    assert process.terminated is True


def test_completed_final_answer_item_is_finalized_by_protocol_event() -> None:
    client = CodexAppServerClient(
        "codex",
        cwd=Path("C:/worktree"),
        codex_home=Path("C:/codex"),
    )
    turn = NativeTurn("thread-1", "turn-1")
    client._events.put({
        "method": "item/completed",
        "params": {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "item": {
                "id": "item-1",
                "type": "agentMessage",
                "phase": "final_answer",
                "text": "OK",
            },
        },
    })
    client._events.put({
        "method": "turn/completed",
        "params": {
            "threadId": "thread-1",
            "turn": {"id": "turn-1", "status": {"type": "completed"}},
        },
    })

    evidence = client.wait_for_turn(turn)

    assert evidence.semantic_content == "OK"


def make_client(process: FakeProcess, tmp_path: Path) -> CodexAppServerClient:
    return CodexAppServerClient(
        "codex", cwd=tmp_path, codex_home=tmp_path / "codex-home",
        process_factory=lambda *args, **kwargs: process, timeout_seconds=1,
    )


def test_client_owns_one_reader_and_collects_exact_finalized_assistant_content(tmp_path: Path) -> None:
    process = FakeProcess()
    with make_client(process, tmp_path) as client:
        thread = client.start_thread()
        turn = client.start_turn(thread, "answer")
        evidence = client.wait_for_turn(turn)

    assert [request["method"] for request in process.requests] == [
        "initialize", "initialized", "thread/start", "turn/start",
    ]
    assert evidence.semantic_content == "hello world"
    assert [item["id"] for item in evidence.items] == ["item-1", "item-2"]
    assert process.stdout.max_concurrent_reads == 1
    assert len(process.stdout.readers) == 1
    assert process.terminated is True


def test_client_binds_provider_and_model_to_native_thread(tmp_path: Path) -> None:
    process = FakeProcess()
    client = CodexAppServerClient(
        "codex",
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        provider="9router",
        process_factory=lambda *args, **kwargs: process,
        timeout_seconds=1,
    )

    with client:
        client.start_thread(model="combo-normal")

    thread_request = next(request for request in process.requests if request["method"] == "thread/start")
    assert client.provider == "9router"
    assert thread_request["params"]["model"] == "combo-normal"


def test_client_retries_short_binary_writes(tmp_path: Path) -> None:
    process = FakeProcess()
    process.stdin.max_write = 2

    with make_client(process, tmp_path) as client:
        client.start_thread(model="combo-normal")

    assert any(request["method"] == "thread/start" for request in process.requests)


def test_client_rejects_zero_progress_binary_write(tmp_path: Path) -> None:
    process = FakeProcess()
    process.stdin.zero_progress = True

    with pytest.raises(NativeAppServerError, match="no progress") as error:
        with make_client(process, tmp_path):
            pass

    assert error.value.failure_kind == "NATIVE_SUBMISSION_FAILED"


def test_client_close_retires_owned_writer_and_reader_threads(tmp_path: Path) -> None:
    process = FakeProcess()
    client = make_client(process, tmp_path)
    client.start()

    evidence = client.close()

    assert evidence["state"] == "retired"
    assert client._writer is not None and not client._writer.is_alive()
    assert client._reader is not None and not client._reader.is_alive()


def test_client_writer_rejects_expired_queued_work(tmp_path: Path) -> None:
    process = FakeProcess()
    client = make_client(process, tmp_path)
    client._process = process
    client._started = True
    acknowledgment: queue.Queue[BaseException | None] = queue.Queue(maxsize=1)
    writer = threading.Thread(target=client._write_loop, daemon=True)
    writer.start()
    client._writes.put((b"{}\n", acknowledgment, 0.0))

    error = acknowledgment.get(timeout=1)
    client._writes.put((None, None, 0.0))
    writer.join(timeout=1)

    assert isinstance(error, NativeAppServerError)
    assert "queued write expired" in str(error)
    assert not writer.is_alive()


def test_client_rejects_idle_turn_as_semantic_success(tmp_path: Path) -> None:
    process = FakeProcess()

    def handle(request: dict[str, Any]) -> None:
        process.requests.append(request)
        if request.get("method") == "initialize":
            process.stdout.push({"id": request["id"], "result": {}})
        elif request.get("method") == "thread/start":
            process.stdout.push({"id": request["id"], "result": {"thread": {
                "id": "t", "sessionId": "s", "ephemeral": True,
                "status": {"type": "idle"}, "turns": [],
            }}})
        elif request.get("method") == "turn/start":
            process.stdout.push({"id": request["id"], "result": {"turn": {"id": "turn"}}})
            process.stdout.push({"method": "turn/completed", "params": {
                "threadId": "t", "turn": {"id": "turn", "status": {"type": "idle"}},
            }})

    process.handle = handle  # type: ignore[method-assign]
    with pytest.raises(NativeAppServerError, match="status idle") as error:
        with make_client(process, tmp_path) as client:
            turn = client.start_turn(client.start_thread(), "answer")
            client.wait_for_turn(turn)
    assert error.value.failure_kind == "NATIVE_TURN_FAILED"
    assert process.terminated is True


def test_client_fails_closed_on_unsupported_server_request(tmp_path: Path) -> None:
    process = FakeProcess()

    def handle(request: dict[str, Any]) -> None:
        process.requests.append(request)
        if request.get("method") == "initialize":
            process.stdout.push({"id": request["id"], "result": {}})
        elif request.get("method") == "thread/start":
            process.stdout.push({"id": request["id"], "result": {"thread": {
                "id": "t", "sessionId": "s", "ephemeral": True,
                "status": {"type": "idle"}, "turns": [],
            }}})

    process.handle = handle  # type: ignore[method-assign]
    with pytest.raises(NativeAppServerError, match="Unsupported") as error:
        with make_client(process, tmp_path) as client:
            process.stdout.push({"id": 999, "method": "item/commandExecution/requestApproval", "params": {}})
            client.start_thread()
    assert error.value.failure_kind == "NATIVE_PROTOCOL_INCOMPATIBLE"
    assert process.terminated is True


def test_client_rejects_completed_turn_without_finalized_assistant_content(tmp_path: Path) -> None:
    process = FakeProcess()

    def handle(request: dict[str, Any]) -> None:
        process.requests.append(request)
        if request.get("method") == "initialize":
            process.stdout.push({"id": request["id"], "result": {}})
        elif request.get("method") == "thread/start":
            process.stdout.push({"id": request["id"], "result": {"thread": {
                "id": "t", "sessionId": "s", "ephemeral": True,
                "status": {"type": "idle"}, "turns": [],
            }}})
        elif request.get("method") == "turn/start":
            process.stdout.push({"id": request["id"], "result": {"turn": {"id": "turn"}}})
            process.stdout.push({"method": "turn/completed", "params": {
                "threadId": "t", "turn": {"id": "turn", "status": {"type": "completed"}},
            }})

    process.handle = handle  # type: ignore[method-assign]
    with pytest.raises(NativeAppServerError, match="no finalized assistant") as error:
        with make_client(process, tmp_path) as client:
            turn = client.start_turn(client.start_thread(), "answer")
            client.wait_for_turn(turn)
    assert error.value.failure_kind == "NATIVE_PROTOCOL_INCOMPATIBLE"
    assert process.terminated is True


def test_client_rejects_assistant_content_without_final_answer_provenance(tmp_path: Path) -> None:
    process = FakeProcess()

    def handle(request: dict[str, Any]) -> None:
        process.requests.append(request)
        if request.get("method") == "initialize":
            process.stdout.push({"id": request["id"], "result": {}})
        elif request.get("method") == "thread/start":
            process.stdout.push({"id": request["id"], "result": {"thread": {
                "id": "t", "sessionId": "s", "ephemeral": True,
                "status": {"type": "idle"}, "turns": [],
            }}})
        elif request.get("method") == "turn/start":
            process.stdout.push({"id": request["id"], "result": {"turn": {"id": "turn"}}})
            process.stdout.push({"method": "item/finalized", "params": {
                "threadId": "t", "turnId": "turn",
                "item": {"id": "item", "type": "agentMessage", "text": "commentary"},
            }})
            process.stdout.push({"method": "turn/completed", "params": {
                "threadId": "t", "turn": {"id": "turn", "status": {"type": "completed"}},
            }})

    process.handle = handle  # type: ignore[method-assign]
    with pytest.raises(NativeAppServerError, match="no finalized assistant") as error:
        with make_client(process, tmp_path) as client:
            turn = client.start_turn(client.start_thread(), "answer")
            client.wait_for_turn(turn)
    assert error.value.failure_kind == "NATIVE_PROTOCOL_INCOMPATIBLE"


def test_client_rejects_conflicting_final_answer_item_replay(tmp_path: Path) -> None:
    process = FakeProcess()

    def handle(request: dict[str, Any]) -> None:
        process.requests.append(request)
        if request.get("method") == "initialize":
            process.stdout.push({"id": request["id"], "result": {}})
        elif request.get("method") == "thread/start":
            process.stdout.push({"id": request["id"], "result": {"thread": {
                "id": "t", "sessionId": "s", "ephemeral": True,
                "status": {"type": "idle"}, "turns": [],
            }}})
        elif request.get("method") == "turn/start":
            process.stdout.push({"id": request["id"], "result": {"turn": {"id": "turn"}}})
            for text in ("one", "two"):
                process.stdout.push({"method": "item/finalized", "params": {
                    "threadId": "t", "turnId": "turn",
                    "item": {
                        "id": "item", "type": "agentMessage", "finalized": True,
                        "provenance": "final_answer", "text": text,
                    },
                }})

    process.handle = handle  # type: ignore[method-assign]
    with pytest.raises(NativeAppServerError, match="replay conflicts") as error:
        with make_client(process, tmp_path) as client:
            turn = client.start_turn(client.start_thread(), "answer")
            client.wait_for_turn(turn)
    assert error.value.failure_kind == "NATIVE_PROTOCOL_INCOMPATIBLE"


def test_client_overflow_fails_closed_without_blocking(tmp_path: Path) -> None:
    process = FakeProcess()
    client = make_client(process, tmp_path)
    for _ in range(256):
        client._events.put_nowait({"method": "turn/completed"})

    client._put_event({"method": "turn/completed"})

    assert client._fatal is not None
    assert client._fatal.failure_kind == "NATIVE_RESULT_LIMIT_EXCEEDED"


@pytest.mark.parametrize(
    ("frame_kind", "failure_kind"),
    [
        ("oversized", "NATIVE_RESULT_LIMIT_EXCEEDED"),
        ("malformed", "NATIVE_PROTOCOL_INCOMPATIBLE"),
        ("unterminated", "NATIVE_RESULT_LIMIT_EXCEEDED"),
    ],
)
def test_reader_rejects_malformed_or_oversized_frames(
    tmp_path: Path,
    frame_kind: str,
    failure_kind: str,
) -> None:
    process = FakeProcess()
    line = {
        "oversized": "{" + ("x" * (256 * 1024)) + "}\n",
        "malformed": "not-json\n",
        "unterminated": "unterminated",
    }[frame_kind]

    def handle(request: dict[str, Any]) -> None:
        process.requests.append(request)
        process.stdout.values.put(line.encode("utf-8"))

    process.handle = handle  # type: ignore[method-assign]
    client = make_client(process, tmp_path)
    with pytest.raises(NativeAppServerError) as error:
        client.start()

    assert error.value.failure_kind == failure_kind
    client.close()


def test_duplicate_item_replay_ignores_later_arrival_order(tmp_path: Path) -> None:
    client = CodexAppServerClient(
        "codex",
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
    )
    turn = NativeTurn("thread-1", "turn-1")
    for order in (2, 1):
        client._events.put({
            "method": "item/finalized",
            "params": {
                "threadId": "thread-1",
                "turnId": "turn-1",
                "item": {
                    "id": "item-1",
                    "type": "agentMessage",
                    "finalized": True,
                    "provenance": "final_answer",
                    "order": order,
                    "text": "answer",
                },
            },
        })
    client._events.put({
        "method": "turn/completed",
        "params": {
            "threadId": "thread-1",
            "turn": {"id": "turn-1", "status": {"type": "completed"}},
        },
    })

    evidence = client.wait_for_turn(turn)

    assert evidence.semantic_content == "answer"
    assert evidence.items[0]["order"] == 2


def test_blocked_write_honors_attempt_deadline(tmp_path: Path) -> None:
    process = FakeProcess()
    blocked = threading.Event()

    def write(value: str) -> int:
        blocked.wait(1)
        return len(value)

    process.stdin.write = write  # type: ignore[method-assign]
    client = CodexAppServerClient(
        "codex",
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        process_factory=lambda *args, **kwargs: process,
        timeout_seconds=0.05,
    )
    with pytest.raises(NativeAppServerError, match="transport write") as error:
        client.start()

    assert error.value.failure_kind == "NATIVE_SUBMISSION_FAILED"
    blocked.set()
    client.close()


def test_close_reports_retirement_unknown_after_grace_and_kill_timeout() -> None:
    class StuckProcess(FakeProcess):
        def terminate(self) -> None:
            self.terminated = True

        def kill(self) -> None:
            return None

        def wait(self, timeout: float | None = None) -> int:
            raise subprocess.TimeoutExpired("codex", timeout or 0)

    import subprocess

    client = CodexAppServerClient(
        "codex",
        cwd=Path("C:/worktree"),
        codex_home=Path("C:/codex"),
    )
    process = StuckProcess()
    client._process = process
    client._started = True

    evidence = client.close()

    assert evidence["state"] == "unknown"
    assert evidence["method"] == "kill"
