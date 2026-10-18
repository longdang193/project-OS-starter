from __future__ import annotations

import json
import queue
import threading
from pathlib import Path
from typing import Any

import pytest

from scripts.project_os_runtime.codex_app_server import CodexAppServerClient, NativeAppServerError


class FakeStdout:
    def __init__(self) -> None:
        self.values: queue.Queue[str | None] = queue.Queue()
        self.readers: set[int] = set()
        self.max_concurrent_reads = 0
        self._concurrent_reads = 0
        self._lock = threading.Lock()

    def push(self, value: dict[str, Any]) -> None:
        self.values.put(json.dumps(value) + "\n")

    def close_input(self) -> None:
        self.values.put(None)

    def readline(self) -> str:
        reader = threading.get_ident()
        with self._lock:
            self.readers.add(reader)
            self._concurrent_reads += 1
            self.max_concurrent_reads = max(self.max_concurrent_reads, self._concurrent_reads)
        try:
            value = self.values.get(timeout=2)
            return "" if value is None else value
        finally:
            with self._lock:
                self._concurrent_reads -= 1

    def close(self) -> None:
        self.close_input()


class FakeStdin:
    def __init__(self, process: "FakeProcess") -> None:
        self.process = process
        self.buffer = ""

    def write(self, value: str) -> int:
        self.buffer += value
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line:
                self.process.handle(json.loads(line))
        return len(value)

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
                "item": {"id": "item-2", "type": "agentMessage", "order": 2, "text": " world"},
            }})
            self.stdout.push({"method": "item/completed", "params": {
                "threadId": "thread-1", "turnId": "turn-1",
                "item": {"id": "item-1", "type": "agentMessage", "order": 1, "text": "hello"},
            }})
            self.stdout.push({"method": "turn/completed", "params": {
                "threadId": "thread-1", "turn": {"id": "turn-1", "status": {"type": "completed"}},
            }})
        else:
            raise AssertionError(f"unexpected method {method}")


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
