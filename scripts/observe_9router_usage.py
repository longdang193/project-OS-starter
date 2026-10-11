"""Read attributable 9router usage from its local SQLite database."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
from typing import Any


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def _session_timestamps(connection: sqlite3.Connection, session_id: str) -> list[str]:
    timestamps: list[str] = []
    for (timestamp, row_session) in connection.execute(
        "select timestamp, coalesce(json_extract(data, '$.clientMetadata.session_id'), json_extract(data, '$.providerRequest.client_metadata.session_id')) from requestDetails"
    ):
        if row_session == session_id:
            timestamps.append(timestamp)
    return timestamps


def _tables(connection: sqlite3.Connection) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for table in ("usageHistory", "requestDetails"):
        columns = {row[1] for row in connection.execute(f"pragma table_info({table})")}
        result[table] = columns
    return result


def _token_details(value: object) -> tuple[int, int] | None:
    if not isinstance(value, str) or not value:
        return 0, 0
    try:
        details = json.loads(value)
    except json.JSONDecodeError:
        return None
    if not isinstance(details, dict):
        return None
    cached = details.get("cached_tokens", 0)
    created = details.get("cache_creation_input_tokens", 0)
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in (cached, created)):
        return None
    return cached, created


def _aggregate_usage(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    for row in rows:
        if row["status"] != "ok":
            return None
        if any(
            isinstance(row[field], bool)
            or not isinstance(row[field], int)
            or row[field] < 0
            for field in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_write_input_tokens")
        ):
            return None
        if row["cache_read_input_tokens"] + row["cache_write_input_tokens"] > row["input_tokens"]:
            return None
        if (
            not isinstance(row["cost"], (int, float))
            or isinstance(row["cost"], bool)
            or row["cost"] < 0
            or (isinstance(row["cost"], float) and not math.isfinite(row["cost"]))
        ):
            return None
    input_tokens = sum(row["input_tokens"] for row in rows)
    output_tokens = sum(row["output_tokens"] for row in rows)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cache_read_input_tokens": sum(row["cache_read_input_tokens"] for row in rows),
        "cache_write_input_tokens": sum(row["cache_write_input_tokens"] for row in rows),
        "cost": sum(float(row["cost"]) for row in rows),
        "currency": "USD",
    }


def observe_window_usage(
    database: Path,
    *,
    start: str,
    end: str,
    model: str | None = None,
    connection_id: str | None = None,
) -> dict[str, Any]:
    """Report provider rows in a bounded time window without claiming attribution."""
    start_at = _timestamp(start)
    end_at = _timestamp(end)
    if end_at <= start_at:
        raise ValueError("end must be after start")

    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        tables = _tables(connection)
        required = {"timestamp", "provider", "model", "connectionId", "endpoint", "promptTokens", "completionTokens", "cost", "status", "tokens"}
        if not required <= tables["usageHistory"]:
            return _result("inconclusive", "schema_unavailable", attribution="time-window")
        rows: list[dict[str, Any]] = []
        for row in connection.execute(
            """
            select timestamp, provider, model, connectionId, endpoint,
                   promptTokens, completionTokens, cost, status, tokens
            from usageHistory
            where provider = 'codex'
              and (? is null or model = ?)
              and (? is null or connectionId = ?)
            order by timestamp
            """,
            (model, model, connection_id, connection_id),
        ):
            row_at = _timestamp(row[0])
            if not start_at <= row_at <= end_at:
                continue
            details = _token_details(row[9])
            if details is None:
                return _result("inconclusive", "invalid_token_details", attribution="time-window")
            rows.append(
                {
                    "timestamp": row_at.isoformat(),
                    "provider": row[1],
                    "model": row[2],
                    "connection_id": row[3],
                    "endpoint": row[4],
                    "input_tokens": row[5],
                    "output_tokens": row[6],
                    "cost": row[7],
                    "status": row[8],
                    "cache_read_input_tokens": details[0],
                    "cache_write_input_tokens": details[1],
                }
            )
        if not rows:
            return _result("inconclusive", "no_usage_rows", attribution="time-window", usage_count=0)
        aggregate = _aggregate_usage(rows)
        if aggregate is None:
            return _result("inconclusive", "invalid_usage_row", attribution="time-window", usage_count=len(rows))
        return _result(
            "observed_window",
            None,
            attribution="time-window",
            confidence="unattributed",
            usage_count=len(rows),
            models=sorted({row["model"] for row in rows}),
            first_timestamp=rows[0]["timestamp"],
            last_timestamp=rows[-1]["timestamp"],
            cost_provenance="provider-reported",
            **aggregate,
        )
    finally:
        connection.close()


def observe_usage(
    database: Path,
    *,
    start: str,
    end: str,
    session_id: str,
    connection_id: str | None = None,
) -> dict[str, Any]:
    start_at = _timestamp(start)
    end_at = _timestamp(end)
    if end_at <= start_at:
        raise ValueError("end must be after start")
    if not session_id.strip():
        raise ValueError("session_id is required")

    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        tables = _tables(connection)
        required = {
            "usageHistory": {"timestamp", "provider", "model", "connectionId", "endpoint", "promptTokens", "completionTokens", "cost", "status"},
            "requestDetails": {"timestamp", "provider", "model", "connectionId", "status", "data"},
        }
        if any(not required[name] <= columns for name, columns in tables.items()):
            return _result("inconclusive", "schema_unavailable")

        request_rows = connection.execute(
            """
            select timestamp, provider, model, connectionId, status,
                   coalesce(json_extract(data, '$.clientMetadata.session_id'), json_extract(data, '$.providerRequest.client_metadata.session_id'))
            from requestDetails
            where provider = 'codex'
              and (? is null or connectionId = ?)
            order by timestamp
            """,
            (connection_id, connection_id),
        ).fetchall()
        requests: list[dict[str, Any]] = []
        session_ids: set[str] = set()
        for timestamp, provider, model, row_connection, status, row_session in request_rows:
            row_at = _timestamp(timestamp)
            if not start_at <= row_at <= end_at:
                continue
            session_ids.add(row_session or "<unattributed>")
            if row_session != session_id:
                continue
            requests.append(
                {
                    "timestamp": row_at.isoformat(),
                    "provider": provider,
                    "model": model,
                    "connection_id": row_connection,
                    "status": status,
                }
            )

        usage_rows = connection.execute(
            """
            select timestamp, provider, model, connectionId, endpoint,
                   promptTokens, completionTokens, cost, status, tokens
            from usageHistory
            where provider = 'codex'
              and (? is null or connectionId = ?)
            order by timestamp
            """,
            (connection_id, connection_id),
        ).fetchall()
        usage = []
        for row in usage_rows:
            row_at = _timestamp(row[0])
            if not start_at <= row_at <= end_at:
                continue
            details = _token_details(row[9])
            if details is None:
                return _result("inconclusive", "invalid_token_details")
            usage.append(
                {
                    "timestamp": row_at.isoformat(),
                    "provider": row[1],
                    "model": row[2],
                    "connection_id": row[3],
                    "endpoint": row[4],
                    "input_tokens": row[5],
                    "output_tokens": row[6],
                    "cost": row[7],
                    "status": row[8],
                    "cache_read_input_tokens": details[0],
                    "cache_write_input_tokens": details[1],
                }
            )
        if session_ids != {session_id}:
            if not requests:
                return _result(
                    "inconclusive",
                    "no_session_rows",
                    observed_session_count=len(session_ids),
                    usage_count=len(usage),
                )
            return _result(
                "inconclusive",
                "overlapping_sessions",
                request_count=len(requests),
                usage_count=len(usage),
                observed_session_count=len(session_ids),
            )
        request_keys = [
            (request["timestamp"], request["provider"], request["model"], request["connection_id"])
            for request in requests
        ]
        if len(request_keys) != len(set(request_keys)):
            return _result(
                "inconclusive",
                "usage_join_ambiguous",
                request_count=len(requests),
            )

        if len(usage) != len(requests):
            return _result(
                "inconclusive",
                "usage_join_incomplete",
                request_count=len(requests),
                usage_count=len(usage),
            )
        by_key: dict[tuple[str, str, str, str | None], list[dict[str, Any]]] = {}
        for row in usage:
            key = (row["timestamp"], row["provider"], row["model"], row["connection_id"])
            by_key.setdefault(key, []).append(row)

        matched: list[dict[str, Any]] = []
        for request in requests:
            key = (request["timestamp"], request["provider"], request["model"], request["connection_id"])
            candidates = by_key.get(key, [])
            if len(candidates) != 1:
                return _result("inconclusive", "usage_join_incomplete", request_count=len(requests), matched_count=len(matched))
            row = candidates[0]
            if request["status"] != "success" or row["status"] != "ok":
                return _result("inconclusive", "request_not_successful", request_count=len(requests), matched_count=len(matched))
            if any(
                isinstance(row[field], bool)
                or not isinstance(row[field], int)
                or row[field] < 0
                for field in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_write_input_tokens")
            ) or row["cache_read_input_tokens"] + row["cache_write_input_tokens"] > row["input_tokens"]:
                return _result("inconclusive", "invalid_token_counts", request_count=len(requests), matched_count=len(matched))
            if (
                not isinstance(row["cost"], (int, float))
                or isinstance(row["cost"], bool)
                or row["cost"] < 0
                or (isinstance(row["cost"], float) and not math.isfinite(row["cost"]))
            ):
                return _result("inconclusive", "invalid_cost", request_count=len(requests), matched_count=len(matched))
            matched.append(row)

        if not matched:
            return _result("inconclusive", "no_session_rows", observed_session_count=len(session_ids))
        session_timestamps = [_timestamp(value) for value in _session_timestamps(connection, session_id)]
        if not session_timestamps or min(session_timestamps) < start_at or max(session_timestamps) > end_at:
            return _result(
                "inconclusive",
                "timestamp_boundary_unproven",
                request_count=len(requests),
                matched_count=len(matched),
            )

        aggregate = _aggregate_usage(matched)
        if aggregate is None:
            return _result("inconclusive", "invalid_usage_row", request_count=len(requests), matched_count=len(matched))
        return _result(
            "matched",
            None,
            request_count=len(requests),
            matched_count=len(matched),
            first_timestamp=matched[0]["timestamp"],
            last_timestamp=matched[-1]["timestamp"],
            **aggregate,
        )
    finally:
        connection.close()


def observe_run_usage(
    database: Path,
    *,
    start: str,
    end: str,
    connection_id: str | None = None,
) -> dict[str, Any]:
    """Discover one session in a bounded run window, then enforce the strict join."""
    start_at = _timestamp(start)
    end_at = _timestamp(end)
    if end_at <= start_at:
        raise ValueError("end must be after start")

    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        tables = _tables(connection)
        required = {"timestamp", "provider", "connectionId", "data"}
        if not required <= tables["requestDetails"]:
            return _result("inconclusive", "schema_unavailable")
        sessions: set[str] = set()
        for timestamp, row_session in connection.execute(
            """
            select timestamp,
                   coalesce(json_extract(data, '$.clientMetadata.session_id'), json_extract(data, '$.providerRequest.client_metadata.session_id'))
            from requestDetails
            where provider = 'codex'
              and (? is null or connectionId = ?)
            """,
            (connection_id, connection_id),
        ):
            row_at = _timestamp(timestamp)
            if start_at <= row_at <= end_at:
                sessions.add(row_session or "<unattributed>")
    finally:
        connection.close()

    if not sessions or "<unattributed>" in sessions:
        return _result(
            "inconclusive",
            "no_session_rows" if not sessions else "session_attribution_missing",
            observed_session_count=len(sessions),
        )
    if len(sessions) != 1:
        return _result(
            "inconclusive",
            "overlapping_sessions",
            observed_session_count=len(sessions),
        )

    session_id = next(iter(sessions))
    result = observe_usage(
        database,
        start=start,
        end=end,
        session_id=session_id,
        connection_id=connection_id,
    )
    if result["disposition"] == "matched":
        result["session_id"] = session_id
        result["attribution"] = "session"
    return result


def _result(disposition: str, reason: str | None, **fields: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": "9router-usage-observation-v1",
        "disposition": disposition,
        "source": "9router-local-read-only",
    }
    if reason:
        result["reason"] = reason
    result.update(fields)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--connection-id")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = observe_usage(
            args.database,
            start=args.start,
            end=args.end,
            session_id=args.session_id,
            connection_id=args.connection_id,
        )
    except (OSError, sqlite3.Error, ValueError) as exc:
        result = _result("inconclusive", type(exc).__name__)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"] == "matched" else 2


if __name__ == "__main__":
    raise SystemExit(main())
