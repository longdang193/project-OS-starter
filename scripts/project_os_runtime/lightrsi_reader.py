"""Bounded adapter for the pinned LightRSI completed-turn CLI."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any

LIGHTRSI_COMPLETED_TURN_SCHEMA = "lightrsi.codex.completed-turn/v1"
LIGHTRSI_AUTHORITY = "lightrsi"
LIGHTRSI_MAX_OUTPUT_BYTES = 64 * 1024
LIGHTRSI_STATES = frozenset({"completed", "pending", "unavailable", "conflict"})
LIGHTRSI_REASONS = frozenset(
    {
        "aborted_turn",
        "assistant_output_unavailable",
        "incomplete_history",
        "invalid_cursor",
        "multiple_candidates",
        "no_candidate",
        "reader_error",
        "reader_malformed_output",
        "reader_process_failed",
        "reader_timeout",
        "session_unavailable",
        "source_disagreement",
        "stale_cursor",
        "turn_boundary_unavailable",
        "unresolved_tool_calls",
        "wrong_session",
    }
)


def _failure(
    session_id: str,
    reason: str,
    *,
    exit_code: int | None = None,
) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {"kind": "reader_error", "reason": reason}
    if exit_code is not None:
        diagnostic["exit_code"] = exit_code
    return {
        "schema": LIGHTRSI_COMPLETED_TURN_SCHEMA,
        "state": "unavailable",
        "retryable": False,
        "sessionId": session_id,
        "authority": LIGHTRSI_AUTHORITY,
        "reason": reason,
        "diagnostics": [diagnostic],
    }


def _valid_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_result(payload: object, session_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("result payload invalid")
    if payload.get("schema") != LIGHTRSI_COMPLETED_TURN_SCHEMA:
        raise ValueError("result schema mismatch")
    state = payload.get("state")
    if state not in LIGHTRSI_STATES:
        raise ValueError("result state invalid")
    if payload.get("authority") != LIGHTRSI_AUTHORITY:
        raise ValueError("result authority invalid")
    if payload.get("sessionId") != session_id:
        return {
            "schema": LIGHTRSI_COMPLETED_TURN_SCHEMA,
            "state": "conflict",
            "retryable": False,
            "sessionId": session_id,
            "authority": LIGHTRSI_AUTHORITY,
            "reason": "wrong_session",
        }
    if payload.get("retryable") is not (state == "pending"):
        raise ValueError("result retryability invalid")
    if state == "completed":
        turn_seq = payload.get("turnSeq")
        if isinstance(turn_seq, bool) or not isinstance(turn_seq, int) or turn_seq < 1:
            raise ValueError("completed turn sequence invalid")
        if not _valid_text(payload.get("turnId")):
            raise ValueError("completed turn id invalid")
        if not _valid_text(payload.get("content")):
            raise ValueError("completed content invalid")
        if not _valid_digest(payload.get("contentDigest")):
            raise ValueError("completed content digest invalid")
        if payload.get("semanticComplete") is not True:
            raise ValueError("completed semantic proof missing")
    elif any(key in payload for key in ("content", "contentDigest")):
        raise ValueError("non-completed result contains semantic content")
    if "reason" in payload and payload["reason"] not in LIGHTRSI_REASONS:
        raise ValueError("result reason invalid")
    if state != "completed" and not _valid_text(payload.get("reason")):
        raise ValueError("non-completed result reason missing")
    return dict(payload)


class LightRSIResultReader:
    """Read one attempt-bound completed-turn result from a pinned CLI build."""

    def __init__(
        self,
        cli_path: Path | str,
        *,
        timeout_seconds: float = 5.0,
        node_executable: str = "node",
        environment: dict[str, str] | None = None,
    ) -> None:
        self.cli_path = Path(cli_path)
        if not self.cli_path.is_absolute():
            raise ValueError("LightRSI CLI path must be absolute")
        if timeout_seconds <= 0:
            raise ValueError("LightRSI reader timeout must be positive")
        if not _valid_text(node_executable):
            raise ValueError("LightRSI node executable must be non-empty")
        self.timeout_seconds = timeout_seconds
        self.node_executable = node_executable
        self.environment = (
            None
            if environment is None
            else {**os.environ, **environment}
        )

    def capability_check(self, *, expected_artifact_sha256: str | None = None) -> dict[str, Any]:
        if not self.cli_path.is_file():
            return {"state": "unavailable", "reason": "reader_error"}
        artifact_sha256 = hashlib.sha256(self.cli_path.read_bytes()).hexdigest()
        if expected_artifact_sha256 and artifact_sha256 != expected_artifact_sha256:
            return {
                "state": "unavailable",
                "reason": "artifact_mismatch",
                "artifact_sha256": artifact_sha256,
            }
        try:
            completed = subprocess.run(
                [
                    self.node_executable,
                    str(self.cli_path),
                    "codex",
                    "completed-turn",
                    "--session",
                    "__project_os_capability__",
                    "--after",
                    "__project_os_capability_cursor__",
                    "--json",
                ],
                capture_output=True,
                check=False,
                text=True,
                timeout=self.timeout_seconds,
                env=self.environment,
            )
        except subprocess.TimeoutExpired:
            return {"state": "unavailable", "reason": "reader_timeout", "artifact_sha256": artifact_sha256}
        except OSError:
            return {"state": "unavailable", "reason": "reader_error", "artifact_sha256": artifact_sha256}
        if completed.returncode != 0:
            return {"state": "unavailable", "reason": "reader_process_failed", "artifact_sha256": artifact_sha256}
        try:
            payload = json.loads(completed.stdout)
            _validate_result(payload, "__project_os_capability__")
        except (UnicodeError, json.JSONDecodeError, ValueError):
            return {"state": "unavailable", "reason": "reader_malformed_output", "artifact_sha256": artifact_sha256}
        return {
            "state": "ready",
            "schema": LIGHTRSI_COMPLETED_TURN_SCHEMA,
            "artifact_sha256": artifact_sha256,
        }

    def read(
        self,
        *,
        session_id: str,
        after_cursor: str,
        request_id: str | None = None,
        turn_id: str | None = None,
    ) -> dict[str, Any]:
        if not _valid_text(session_id) or not _valid_text(after_cursor):
            return _failure(session_id, "invalid_cursor")
        command = [
            self.node_executable,
            str(self.cli_path),
            "codex",
            "completed-turn",
            "--session",
            session_id,
            "--after",
            after_cursor,
        ]
        if request_id is not None:
            if not _valid_text(request_id):
                return _failure(session_id, "invalid_cursor")
            command.extend(["--request", request_id])
        if turn_id is not None:
            if not _valid_text(turn_id):
                return _failure(session_id, "invalid_cursor")
            command.extend(["--turn", turn_id])
        command.append("--json")
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
                timeout=self.timeout_seconds,
                env=self.environment,
            )
        except subprocess.TimeoutExpired:
            return _failure(session_id, "reader_timeout")
        except OSError:
            return _failure(session_id, "reader_error")
        if completed.returncode != 0:
            return _failure(session_id, "reader_process_failed", exit_code=completed.returncode)
        stdout = completed.stdout
        if not isinstance(stdout, str) or len(stdout.encode("utf-8")) > LIGHTRSI_MAX_OUTPUT_BYTES:
            return _failure(session_id, "reader_malformed_output")
        try:
            payload = json.loads(stdout)
            return _validate_result(payload, session_id)
        except (UnicodeError, json.JSONDecodeError, ValueError):
            return _failure(session_id, "reader_malformed_output")


__all__ = [
    "LIGHTRSI_AUTHORITY",
    "LIGHTRSI_COMPLETED_TURN_SCHEMA",
    "LIGHTRSI_MAX_OUTPUT_BYTES",
    "LightRSIResultReader",
]
