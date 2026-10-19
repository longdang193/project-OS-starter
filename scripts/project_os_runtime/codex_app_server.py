"""Owned JSON-RPC client for a bounded Codex app-server turn."""

from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .secretary_results import NATIVE_RESULT_CONTENT_MAX_BYTES


class NativeAppServerError(RuntimeError):
    """A fail-closed app-server protocol or lifecycle error."""

    def __init__(self, message: str, *, failure_kind: str = "NATIVE_PROTOCOL_INCOMPATIBLE") -> None:
        super().__init__(message)
        self.failure_kind = failure_kind


@dataclass(frozen=True)
class NativeThread:
    thread_id: str
    session_id: str
    ephemeral: bool
    pre_submit_boundary: str


@dataclass(frozen=True)
class NativeTurn:
    thread_id: str
    turn_id: str


@dataclass(frozen=True)
class NativeTurnEvidence:
    thread_id: str
    turn_id: str
    status: str
    items: tuple[dict[str, Any], ...]
    semantic_content: str


_EOF = object()
_ERROR = object()
_ASSISTANT_ITEM_TYPES = frozenset(
    {"agentMessage", "assistantMessage", "agent_message", "assistant_message"}
)
_EXCLUDED_ITEM_TYPES = frozenset(
    {"reasoning", "toolCall", "tool_call", "toolResult", "tool_result", "progress", "status"}
)
_RELEVANT_EVENT_METHODS = frozenset({"item/completed", "item/finalized", "turn/completed"})
_MAX_MESSAGE_BYTES = 256 * 1024
_MAX_ITEMS = 256
_MAX_ITEM_TEXT_BYTES = 64 * 1024
_MAX_TOTAL_CONTENT_BYTES = NATIVE_RESULT_CONTENT_MAX_BYTES
_MAX_QUEUED_EVENTS = 256
_RETIREMENT_GRACE_SECONDS = 1.0
_RETIREMENT_KILL_SECONDS = 1.0


def _serialize_message(payload: Mapping[str, Any]) -> bytes:
    encoded = (json.dumps(dict(payload), ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > _MAX_MESSAGE_BYTES:
        raise NativeAppServerError(
            "Codex app-server outgoing message exceeds the content limit.",
            failure_kind="NATIVE_RESULT_LIMIT_EXCEEDED",
        )
    return encoded


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NativeAppServerError(f"Codex app-server {label} is missing.")
    return value.strip()


def _status_type(value: object) -> str | None:
    if isinstance(value, Mapping):
        status = value.get("type")
        return status.strip() if isinstance(status, str) and status.strip() else None
    return value.strip() if isinstance(value, str) and value.strip() else None


def _item_text(item: Mapping[str, Any]) -> str:
    content = item.get("content")
    parts: list[str] = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for part in content:
            if not isinstance(part, Mapping) or part.get("type") not in {None, "text", "output_text", "input_text"}:
                continue
            text = part.get("text")
            if isinstance(text, str):
                parts.append(text)
    text = item.get("text")
    if isinstance(text, str):
        parts.append(text)
    result = "".join(parts)
    if not result.strip():
        raise NativeAppServerError(
            "Codex app-server finalized assistant item has no text.", failure_kind="NATIVE_TURN_FAILED"
        )
    return result


def _is_final_answer_item(item: Mapping[str, Any], params: Mapping[str, Any]) -> bool:
    provenance = item.get("provenance", params.get("provenance"))
    if provenance == "final_answer":
        return True
    if isinstance(provenance, Mapping) and provenance.get("phase") == "final_answer":
        return True
    if item.get("phase") == "final_answer" or item.get("finalAnswer") is True:
        return True
    return False


class CodexAppServerClient:
    """Own one app-server process and one stdout reader until publication ends."""

    def __init__(
        self,
        executable: str,
        *,
        cwd: Path,
        codex_home: Path,
        environment: Mapping[str, str] | None = None,
        timeout_seconds: float = 120.0,
        attempt_deadline: float | None = None,
        process_factory: Callable[..., Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.executable = executable
        self.cwd = cwd
        self.codex_home = codex_home
        self.environment = dict(os.environ if environment is None else environment)
        self.environment["CODEX_HOME"] = str(codex_home.resolve())
        self.timeout_seconds = timeout_seconds
        self._attempt_deadline = attempt_deadline
        self._process_factory = process_factory or subprocess.Popen
        self._clock = clock
        self._process: Any | None = None
        self._reader: threading.Thread | None = None
        self._stderr_reader: threading.Thread | None = None
        self._writer: threading.Thread | None = None
        self._writes: queue.Queue[tuple[bytes, queue.Queue[BaseException | None]]] = queue.Queue(maxsize=1)
        self._state_lock = threading.Lock()
        self._responses: dict[int, queue.Queue[object]] = {}
        self._events: queue.Queue[object] = queue.Queue(maxsize=_MAX_QUEUED_EVENTS)
        self._next_request_id = 1
        self._fatal: NativeAppServerError | None = None
        self._started = False
        self._retired = False
        self._retirement_evidence: dict[str, Any] = {"state": "not_attempted"}

    @property
    def process(self) -> Any:
        if self._process is None:
            raise NativeAppServerError("Codex app-server process is not started.")
        return self._process

    @property
    def retirement_evidence(self) -> dict[str, Any]:
        return dict(self._retirement_evidence)

    def __enter__(self) -> "CodexAppServerClient":
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def start(self) -> None:
        if self._started:
            return
        try:
            self._process = self._process_factory(
                [self.executable, "app-server", "--stdio"],
                cwd=self.cwd,
                env=self.environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=False,
                bufsize=0,
            )
        except OSError as exc:
            raise NativeAppServerError(
                "Codex app-server executable unavailable.", failure_kind="NATIVE_INITIALIZATION_FAILED"
            ) from exc
        self._started = True
        if getattr(self.process, "stdout", None) is None:
            raise NativeAppServerError(
                "Codex app-server stdout is unavailable.", failure_kind="NATIVE_INITIALIZATION_FAILED"
            )
        if getattr(self.process, "stdin", None) is None:
            raise NativeAppServerError(
                "Codex app-server stdin is unavailable.", failure_kind="NATIVE_INITIALIZATION_FAILED"
            )
        self._writer = threading.Thread(target=self._write_loop, name="codex-app-server-writer", daemon=True)
        self._writer.start()
        self._reader = threading.Thread(target=self._read_stdout, name="codex-app-server-reader", daemon=True)
        self._reader.start()
        try:
            self._request("initialize", {"clientInfo": {"name": "project-os-secretary", "version": "1"}})
            self._notify("initialized", {})
        except NativeAppServerError:
            self.close()
            raise

    def start_thread(self, *, ephemeral: bool = True, sandbox: str = "read-only") -> NativeThread:
        result = self._request(
            "thread/start", {"cwd": str(self.cwd.resolve()), "ephemeral": ephemeral, "sandbox": sandbox}
        )
        thread = result.get("thread")
        if not isinstance(thread, Mapping):
            raise NativeAppServerError(
                "Codex app-server thread/start returned no thread.", failure_kind="NATIVE_BINDING_FAILED"
            )
        thread_id = _required_text(thread.get("id"), "thread identity")
        session_id = _required_text(thread.get("sessionId"), "session identity")
        if thread.get("cwd") and Path(str(thread["cwd"])).resolve() != self.cwd.resolve():
            raise NativeAppServerError(
                "Codex app-server thread cwd does not match the launched lane.", failure_kind="NATIVE_BINDING_FAILED"
            )
        if ephemeral and thread.get("ephemeral") is not True:
            raise NativeAppServerError("Codex app-server thread is not ephemeral.", failure_kind="NATIVE_BINDING_FAILED")
        if ephemeral and thread.get("turns") not in ([], None):
            raise NativeAppServerError(
                "Codex app-server fresh thread already contains turns.", failure_kind="NATIVE_BINDING_FAILED"
            )
        if _status_type(thread.get("status")) not in {None, "idle"}:
            raise NativeAppServerError(
                "Codex app-server thread is not idle before binding.", failure_kind="NATIVE_BINDING_FAILED"
            )
        return NativeThread(
            thread_id=thread_id,
            session_id=session_id,
            ephemeral=bool(thread.get("ephemeral", ephemeral)),
            pre_submit_boundary="fresh-zero-prior-turn" if ephemeral else "provider-owned-resumed-thread",
        )

    def start_turn(self, thread: NativeThread, task: str) -> NativeTurn:
        result = self._request(
            "turn/start",
            {"threadId": thread.thread_id, "input": [{"type": "text", "text": _required_text(task, "turn task")}]},
        )
        turn = result.get("turn")
        if not isinstance(turn, Mapping):
            raise NativeAppServerError(
                "Codex app-server turn/start returned no turn.", failure_kind="NATIVE_SUBMISSION_FAILED"
            )
        return NativeTurn(thread_id=thread.thread_id, turn_id=_required_text(turn.get("id"), "turn identity"))

    def wait_for_turn(self, turn: NativeTurn) -> NativeTurnEvidence:
        deadline = self._deadline()
        items: dict[str, tuple[int, dict[str, Any]]] = {}
        completion: Mapping[str, Any] | None = None
        arrival = 0
        while self._clock() < deadline:
            message = self._next_event(deadline)
            if message is _EOF:
                raise NativeAppServerError(
                    "Codex app-server closed before turn completion.", failure_kind="NATIVE_TURN_INTERRUPTED"
                )
            if message is _ERROR:
                self._raise_fatal()
            if not isinstance(message, Mapping):
                continue
            method = message.get("method")
            params = message.get("params")
            if method == "turn/completed":
                if not isinstance(params, Mapping) or not self._matches_turn(params, turn):
                    continue
                completion = params.get("turn") if isinstance(params.get("turn"), Mapping) else params
                status = _status_type(completion.get("status")) if isinstance(completion, Mapping) else None
                if status != "completed":
                    raise NativeAppServerError(
                        f"Codex app-server turn ended with status {status or 'unknown'}",
                        failure_kind="NATIVE_TURN_FAILED" if status else "NATIVE_PROTOCOL_INCOMPATIBLE",
                    )
                break
            if method not in {"item/completed", "item/finalized"} or not isinstance(params, Mapping):
                continue
            item = params.get("item")
            if not isinstance(item, Mapping) or not self._matches_turn(params, turn):
                continue
            item_type = item.get("type")
            if item_type in _EXCLUDED_ITEM_TYPES or item_type not in _ASSISTANT_ITEM_TYPES:
                continue
            if method != "item/completed" and item.get("finalized") is not True:
                continue
            if not _is_final_answer_item(item, params):
                continue
            item_id = _required_text(item.get("id"), "assistant item identity")
            order_value = item.get("order", item.get("index", arrival))
            order = order_value if isinstance(order_value, int) else arrival
            text = _item_text(item)
            if len(text.encode("utf-8")) > _MAX_ITEM_TEXT_BYTES:
                raise NativeAppServerError(
                    "Codex app-server assistant item exceeds the content limit.",
                    failure_kind="NATIVE_RESULT_LIMIT_EXCEEDED",
                )
            record = {"id": item_id, "text": text}
            existing = items.get(item_id)
            if existing is not None:
                if existing[1] != record:
                    raise NativeAppServerError(
                        "Codex app-server assistant item replay conflicts.",
                        failure_kind="NATIVE_PROTOCOL_INCOMPATIBLE",
                    )
                continue
            if len(items) >= _MAX_ITEMS:
                raise NativeAppServerError(
                    "Codex app-server finalized item limit exceeded.",
                    failure_kind="NATIVE_RESULT_LIMIT_EXCEEDED",
                )
            if sum(len(value[1]["text"].encode("utf-8")) for value in items.values()) + len(text.encode("utf-8")) > _MAX_TOTAL_CONTENT_BYTES:
                raise NativeAppServerError(
                    "Codex app-server semantic content limit exceeded.",
                    failure_kind="NATIVE_RESULT_LIMIT_EXCEEDED",
                )
            items[item_id] = (order, record)
            arrival += 1
        if completion is None:
            raise NativeAppServerError(
                "Timed out waiting for Codex app-server turn completion.", failure_kind="NATIVE_RESULT_TIMEOUT"
            )
        ordered = tuple(
            {**value[1], "order": value[0]}
            for value in sorted(items.values(), key=lambda entry: (entry[0], entry[1]["id"]))
        )
        if not ordered:
            raise NativeAppServerError(
                "Codex app-server completed turn has no finalized assistant content.",
                failure_kind="NATIVE_PROTOCOL_INCOMPATIBLE",
            )
        return NativeTurnEvidence(
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
            status="completed",
            items=ordered,
            semantic_content="".join(item["text"] for item in ordered),
        )

    def close(self) -> dict[str, Any]:
        if self._retired:
            return self.retirement_evidence
        self._retired = True
        process = self._process
        if process is None:
            self._retirement_evidence = {"state": "retired", "method": "not_started"}
            return self.retirement_evidence
        method = "already_exited"
        state = "retired"
        error: str | None = None
        try:
            if process.poll() is None:
                method = "terminate"
                process.terminate()
                try:
                    process.wait(timeout=_RETIREMENT_GRACE_SECONDS)
                except (OSError, subprocess.TimeoutExpired):
                    method = "kill"
                    process.kill()
                    try:
                        process.wait(timeout=_RETIREMENT_KILL_SECONDS)
                    except (OSError, subprocess.TimeoutExpired):
                        state = "unknown"
                        error = "process remained alive after kill"
            if process.poll() is None:
                state = "unknown"
                error = "process remained alive after retirement"
        except (OSError, subprocess.TimeoutExpired) as exc:
            state = "unknown"
            error = type(exc).__name__
        finally:
            for stream_name in ("stdin", "stdout", "stderr"):
                stream = getattr(process, stream_name, None)
                close = getattr(stream, "close", None)
                if callable(close):
                    close()
        self._retirement_evidence = {"state": state, "method": method}
        if error is not None:
            self._retirement_evidence["error"] = error
        return self.retirement_evidence

    def _request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        request_id = self._next_request_id
        self._next_request_id += 1
        response_queue: queue.Queue[object] = queue.Queue(maxsize=1)
        with self._state_lock:
            self._raise_fatal()
            self._responses[request_id] = response_queue
        try:
            self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": dict(params)})
            response = self._wait_queue(response_queue, self._deadline())
            if response is _EOF:
                raise NativeAppServerError(
                    f"Codex app-server {method} closed without a response.", failure_kind="NATIVE_INITIALIZATION_FAILED"
                )
            if response is _ERROR:
                self._raise_fatal()
            if not isinstance(response, Mapping):
                raise NativeAppServerError(f"Codex app-server {method} returned an invalid response.")
            error = response.get("error")
            if isinstance(error, Mapping):
                raise NativeAppServerError(
                    f"Codex app-server {method} failed: {error.get('code', 'unknown')} {error.get('message', '')}".strip(),
                    failure_kind="NATIVE_SUBMISSION_FAILED" if method == "turn/start" else "NATIVE_INITIALIZATION_FAILED",
                )
            result = response.get("result")
            if not isinstance(result, Mapping):
                raise NativeAppServerError(f"Codex app-server {method} returned no result.")
            return result
        finally:
            with self._state_lock:
                self._responses.pop(request_id, None)

    def _notify(self, method: str, params: Mapping[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": dict(params)})

    def _send(self, payload: Mapping[str, Any]) -> None:
        encoded = _serialize_message(payload)
        deadline = self._deadline()
        acknowledgment: queue.Queue[BaseException | None] = queue.Queue(maxsize=1)
        try:
            self._writes.put((encoded, acknowledgment), timeout=max(0.001, deadline - self._clock()))
            error = acknowledgment.get(timeout=max(0.001, deadline - self._clock()))
            if error is not None:
                raise error
        except (OSError, ValueError, queue.Full, queue.Empty) as exc:
            raise NativeAppServerError(
                "Codex app-server transport write failed.", failure_kind="NATIVE_SUBMISSION_FAILED"
            ) from exc

    def _write_loop(self) -> None:
        stdin = getattr(self.process, "stdin", None)
        if stdin is None:
            return
        while True:
            encoded, acknowledgment = self._writes.get()
            if encoded == b"":
                return
            error: BaseException | None = None
            try:
                try:
                    stdin.write(encoded)
                except TypeError:
                    stdin.write(encoded.decode("utf-8"))
                stdin.flush()
            except BaseException as exc:
                error = exc
            try:
                acknowledgment.put_nowait(error)
            except queue.Full:
                pass
            if error is not None:
                return

    def _read_stdout(self) -> None:
        stdout = self.process.stdout
        try:
            while True:
                try:
                    line = stdout.readline(_MAX_MESSAGE_BYTES + 1)
                except TypeError:
                    line = stdout.readline()
                if not line:
                    self._put_event(_EOF)
                    with self._state_lock:
                        for response in self._responses.values():
                            try:
                                response.put_nowait(_EOF)
                            except queue.Full:
                                pass
                    return
                if isinstance(line, str):
                    line = line.encode("utf-8")
                if not isinstance(line, bytes) or len(line) > _MAX_MESSAGE_BYTES or not line.endswith(b"\n"):
                    self._set_fatal(
                        "Codex app-server frame exceeds the content limit or is unterminated.",
                        failure_kind="NATIVE_RESULT_LIMIT_EXCEEDED",
                    )
                    return
                try:
                    message = json.loads(line[:-1].decode("utf-8"))
                except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
                    self._set_fatal("Codex app-server emitted malformed JSON.")
                    return
                if not isinstance(message, Mapping):
                    self._set_fatal("Codex app-server emitted a non-object message.")
                    return
                message_id = message.get("id")
                method = message.get("method")
                if isinstance(method, str) and message_id is not None:
                    self._set_fatal(
                        f"Unsupported Codex app-server request: {method}",
                        failure_kind="NATIVE_PROTOCOL_INCOMPATIBLE",
                    )
                    return
                if method is None and isinstance(message_id, int) and message_id in self._responses:
                    self._responses[message_id].put_nowait(message)
                    continue
                if isinstance(method, str):
                    if method not in _RELEVANT_EVENT_METHODS:
                        continue
                    self._put_event(message)
                    continue
                self._set_fatal("Codex app-server emitted an unsupported JSON-RPC envelope.")
                return
        except Exception as exc:
            self._set_fatal("Codex app-server stdout reader failed.", cause=exc)

    @staticmethod
    def _drain_stderr(stderr: Any) -> None:
        try:
            while stderr.readline():
                pass
        except Exception:
            return

    def _set_fatal(
        self,
        message: str,
        *,
        failure_kind: str = "NATIVE_PROTOCOL_INCOMPATIBLE",
        cause: BaseException | None = None,
    ) -> None:
        error = NativeAppServerError(message, failure_kind=failure_kind)
        if cause is not None:
            error.__cause__ = cause
        response_queues: tuple[queue.Queue[object], ...] = ()
        publish = False
        with self._state_lock:
            if self._fatal is None:
                self._fatal = error
                response_queues = tuple(self._responses.values())
                publish = True
        if publish:
            for response in response_queues:
                try:
                    response.put_nowait(_ERROR)
                except queue.Full:
                    pass
            self._put_event(_ERROR)

    def _put_event(self, event: object) -> None:
        try:
            self._events.put_nowait(event)
        except queue.Full:
            self._set_fatal(
                "Codex app-server event queue limit exceeded.",
                failure_kind="NATIVE_RESULT_LIMIT_EXCEEDED",
            )

    def _deadline(self) -> float:
        return self._attempt_deadline if self._attempt_deadline is not None else self._clock() + self.timeout_seconds

    def _raise_fatal(self) -> None:
        if self._fatal is not None:
            raise self._fatal

    def _wait_queue(self, values: queue.Queue[object], deadline: float) -> object:
        self._raise_fatal()
        try:
            return values.get(timeout=max(0.001, deadline - self._clock()))
        except queue.Empty as exc:
            raise NativeAppServerError(
                "Timed out waiting for Codex app-server response.", failure_kind="NATIVE_RESULT_TIMEOUT"
            ) from exc

    def _next_event(self, deadline: float) -> object:
        self._raise_fatal()
        try:
            return self._events.get(timeout=max(0.001, deadline - self._clock()))
        except queue.Empty as exc:
            self._raise_fatal()
            raise NativeAppServerError(
                "Timed out waiting for Codex app-server event.", failure_kind="NATIVE_RESULT_TIMEOUT"
            ) from exc

    def _matches_turn(self, params: Mapping[str, Any], turn: NativeTurn) -> bool:
        turn_value = params.get("turn") if isinstance(params.get("turn"), Mapping) else params
        observed_turn_id = params.get("turnId")
        if observed_turn_id is None and isinstance(turn_value, Mapping):
            observed_turn_id = turn_value.get("id")
        observed_thread_id = params.get("threadId")
        if observed_thread_id is None and isinstance(turn_value, Mapping):
            observed_thread_id = turn_value.get("threadId")
        return observed_turn_id == turn.turn_id and observed_thread_id == turn.thread_id


__all__ = ["CodexAppServerClient", "NativeAppServerError", "NativeThread", "NativeTurn", "NativeTurnEvidence"]
