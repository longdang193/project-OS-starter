"""Read attributable 9router usage from its local SQLite database."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
import time
from typing import Any


OBSERVATION_BUDGET_MS = 1_000
_PROGRESS_INTERVAL = 1_000


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def _sql_timestamp(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _timestamp_index(connection: sqlite3.Connection, table: str) -> str | None:
    for row in connection.execute(f"pragma index_list({table})"):
        index_name = row[1]
        columns = [item[2] for item in connection.execute(f"pragma index_info({index_name})")]
        if columns == ["timestamp"]:
            return index_name
    return None


def _tables(connection: sqlite3.Connection) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for table in ("usageHistory", "requestDetails"):
        columns = {row[1] for row in connection.execute(f"pragma table_info({table})")}
        result[table] = columns
    return result


def _token_details(value: object) -> tuple[int, int] | None:
    if not isinstance(value, str) or not value:
        return None
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
        if any(
            isinstance(row[field], bool)
            or not isinstance(row[field], int)
            or row[field] < 0
            for field in ("input_tokens", "output_tokens")
        ):
            return None
        if (
            row["cache_read_input_tokens"] is not None
            and row["cache_write_input_tokens"] is not None
            and row["cache_read_input_tokens"] + row["cache_write_input_tokens"] > row["input_tokens"]
        ):
            return None
    input_tokens = sum(row["input_tokens"] for row in rows)
    output_tokens = sum(row["output_tokens"] for row in rows)
    costs = [row["cost"] for row in rows]
    cache_read = [row["cache_read_input_tokens"] for row in rows]
    cache_write = [row["cache_write_input_tokens"] for row in rows]
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cache_read_input_tokens": sum(cache_read) if all(value is not None for value in cache_read) else None,
        "cache_write_input_tokens": sum(cache_write) if all(value is not None for value in cache_write) else None,
        "cost": sum(float(value) for value in costs) if all(value is not None for value in costs) else None,
        "currency": "USD",
    }


def _connect(database: Path, *, budget_ms: int) -> tuple[sqlite3.Connection, float, dict[str, int]]:
    if budget_ms <= 0:
        raise ValueError("observation budget must be positive")
    budget_seconds = budget_ms / 1_000
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=budget_seconds)
    connection.execute(f"pragma busy_timeout={budget_ms}")
    metrics = {"query_count": 0, "progress_calls": 0}
    deadline = time.monotonic() + budget_seconds

    def progress() -> int:
        metrics["progress_calls"] += 1
        return int(time.monotonic() >= deadline)

    connection.set_progress_handler(progress, _PROGRESS_INTERVAL)
    connection.execute("begin")
    return connection, deadline, metrics


def _canonical_read(
    database: Path,
    *,
    start: str,
    end: str,
    model: str | None = None,
    connection_id: str | None = None,
    observation_budget_ms: int = OBSERVATION_BUDGET_MS,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, Any] | None]:
    start_at = _timestamp(start)
    end_at = _timestamp(end)
    if end_at <= start_at:
        raise ValueError("end must be after start")

    connection: sqlite3.Connection | None = None
    metrics: dict[str, int] = {"query_count": 0, "progress_calls": 0}
    try:
        connection, deadline, metrics = _connect(database, budget_ms=observation_budget_ms)
        tables = _tables(connection)
        metrics["query_count"] += 2
        required = {
            "usageHistory": {"timestamp", "provider", "model", "connectionId", "endpoint", "promptTokens", "completionTokens", "cost", "status", "tokens", "meta"},
            "requestDetails": {"id", "timestamp", "provider", "model", "connectionId", "status", "data"},
        }
        if any(not required[name] <= columns for name, columns in tables.items()):
            return [], metrics, _result("inconclusive", "schema_unavailable", metrics=metrics)
        usage_source = "usageHistory"
        usage_timestamp_index = _timestamp_index(connection, "usageHistory")
        if usage_timestamp_index:
            usage_source += f" indexed by {usage_timestamp_index}"
        start_sql = _sql_timestamp(start_at)
        end_sql = _sql_timestamp(end_at)
        rows = connection.execute(
            f"""
            with request_rows as (
                select id as detail_id, timestamp as request_timestamp, provider as request_provider,
                       model as request_model, connectionId as request_connection, status as request_status,
                       case when json_valid(data) then coalesce(
                           json_extract(data, '$.clientMetadata.session_id'),
                           json_extract(data, '$.providerRequest.client_metadata.session_id')
                       ) end as session_id
                 from requestDetails
                where provider = 'codex'
                   and datetime(timestamp) between datetime(?) and datetime(?)
                  and (? is null or connectionId = ?)
                  and (? is null or model = ?)
            ), usage_rows as (
                select timestamp as usage_timestamp, provider as usage_provider,
                       model as usage_model, connectionId as usage_connection, endpoint,
                       promptTokens, completionTokens, cost, status as usage_status, tokens,
                       case when json_valid(meta) then json_extract(meta, '$.request_detail_id') end as detail_id
                 from {usage_source}
                where provider = 'codex'
                   and timestamp >= ? and timestamp <= ?
                  and (? is null or connectionId = ?)
                  and (? is null or model = ?)
            )
            select 'joined', r.detail_id, r.request_timestamp, r.request_provider,
                   r.request_model, r.request_connection, r.request_status, r.session_id,
                   u.usage_timestamp, u.usage_provider, u.usage_model, u.usage_connection,
                   u.endpoint, u.promptTokens, u.completionTokens, u.cost, u.usage_status, u.tokens
            from request_rows r
            left join usage_rows u on u.detail_id = r.detail_id
            union all
            select 'unjoined', null, null, null, null, null, null, null,
                   u.usage_timestamp, u.usage_provider, u.usage_model, u.usage_connection,
                   u.endpoint, u.promptTokens, u.completionTokens, u.cost, u.usage_status, u.tokens
            from usage_rows u
            left join request_rows r on r.detail_id = u.detail_id
            where r.detail_id is null
            """,
            (
                start, end, connection_id, connection_id, model, model,
                start_sql, end_sql, connection_id, connection_id, model, model,
            ),
        ).fetchall()
        metrics["query_count"] += 1
        if time.monotonic() > deadline:
            return [], metrics, _result("inconclusive", "observation_deadline", metrics=metrics)
        normalized: list[dict[str, Any]] = []
        for row in rows:
            request_timestamp = row[2]
            usage_timestamp = row[8]
            normalized.append(
                {
                    "detail_id": row[1],
                    "request_timestamp": _timestamp(request_timestamp).isoformat() if request_timestamp else None,
                    "request_provider": row[3],
                    "request_model": row[4],
                    "request_connection": row[5],
                    "request_status": row[6],
                    "session_id": row[7] or "<unattributed>",
                    "usage_timestamp": _timestamp(usage_timestamp).isoformat() if usage_timestamp else None,
                    "usage_provider": row[9],
                    "usage_model": row[10],
                    "usage_connection": row[11],
                    "endpoint": row[12],
                    "input_tokens": row[13],
                    "output_tokens": row[14],
                    "cost": row[15],
                    "usage_status": row[16],
                    "token_details": _token_details(row[17]),
                }
            )
        normalized = [
            row
            for row in normalized
            if all(
                value is None or _timestamp(value) >= start_at and _timestamp(value) <= end_at
                for value in (row["request_timestamp"], row["usage_timestamp"])
            )
        ]
        return normalized, metrics, None
    except sqlite3.OperationalError as exc:
        reason = "observation_deadline" if "interrupt" in str(exc).casefold() else "database_locked" if "locked" in str(exc).casefold() else type(exc).__name__
        return [], metrics, _result("inconclusive", reason, metrics=metrics)
    except (OSError, sqlite3.Error) as exc:
        return [], metrics, _result("inconclusive", type(exc).__name__, metrics=metrics)
    finally:
        if connection is not None:
            connection.set_progress_handler(None, 0)
            connection.close()


def _validate_rows(rows: list[dict[str, Any]], *, session_id: str | None = None) -> tuple[list[dict[str, Any]], dict[str, int], set[str], int]:
    excluded: dict[str, int] = {}
    valid: list[dict[str, Any]] = []
    session_ids = {row["session_id"] for row in rows if row["request_timestamp"] is not None}
    selected_count = sum(1 for row in rows if row["usage_timestamp"] is not None)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if session_id is not None and row["session_id"] != session_id:
            if row["request_timestamp"] is not None or row["usage_timestamp"] is not None:
                excluded["other_session"] = excluded.get("other_session", 0) + 1
            continue
        if row["usage_timestamp"] is None:
            excluded["missing_usage"] = excluded.get("missing_usage", 0) + 1
            continue
        if not row["detail_id"]:
            excluded["unattributed_request"] = excluded.get("unattributed_request", 0) + 1
            continue
        grouped.setdefault(row["detail_id"], []).append(row)
    for detail_id, candidates in grouped.items():
        if len(candidates) != 1:
            excluded["ambiguous_join"] = excluded.get("ambiguous_join", 0) + len(candidates)
            continue
        row = candidates[0]
        if (row["usage_provider"], row["usage_model"], row["usage_connection"]) != (
            row["request_provider"], row["request_model"], row["request_connection"]
        ):
            excluded["identity_mismatch"] = excluded.get("identity_mismatch", 0) + 1
            continue
        token_fields = ("input_tokens", "output_tokens")
        if any(isinstance(row[field], bool) or not isinstance(row[field], int) or row[field] < 0 for field in token_fields):
            excluded["invalid_token_counts"] = excluded.get("invalid_token_counts", 0) + 1
            continue
        cache_read, cache_write = row["token_details"] if row["token_details"] is not None else (None, None)
        if cache_read is not None and cache_write is not None and cache_read + cache_write > row["input_tokens"]:
            excluded["invalid_token_counts"] = excluded.get("invalid_token_counts", 0) + 1
            continue
        cost = row["cost"]
        if cost is not None and (
            not isinstance(cost, (int, float))
            or isinstance(cost, bool)
            or cost < 0
            or (isinstance(cost, float) and not math.isfinite(cost))
        ):
            excluded["invalid_cost"] = excluded.get("invalid_cost", 0) + 1
            continue
        valid.append(
            {
                "timestamp": row["usage_timestamp"],
                "status": row["usage_status"],
                "input_tokens": row["input_tokens"],
                "output_tokens": row["output_tokens"],
                "cost": cost,
                "cache_read_input_tokens": cache_read,
                "cache_write_input_tokens": cache_write,
            }
        )
        if row["request_status"] != "success" or row["usage_status"] != "ok":
            excluded["failed_request_with_usage"] = excluded.get("failed_request_with_usage", 0)
    return valid, excluded, session_ids, selected_count


def _project(
    rows: list[dict[str, Any]],
    *,
    attribution: str,
    session_id: str | None = None,
    metrics: dict[str, int] | None = None,
) -> dict[str, Any]:
    valid, excluded, session_ids, selected_count = _validate_rows(rows, session_id=session_id)
    if not valid:
        reason = "no_usage_rows" if not selected_count else next(iter(excluded), "no_verified_rows")
        return _result(
            "inconclusive",
            reason,
            attribution=attribution,
            observed_session_count=len(session_ids),
            selected_count=selected_count,
            measured_count=0,
            excluded_count=sum(excluded.values()),
            excluded_row_reasons=excluded,
            metrics=metrics or {},
        )
    aggregate = _aggregate_usage(valid)
    timestamps = [row["timestamp"] for row in valid]
    cache_unknown = any(
        row["cache_read_input_tokens"] is None or row["cache_write_input_tokens"] is None
        for row in valid
    )
    result = _result(
        "observed_window" if attribution == "window" else "matched",
        None,
        attribution=attribution,
        confidence="unattributed" if attribution == "window" else "identity-bound",
        session_id=session_id,
        request_count=len({row["detail_id"] for row in rows if row["detail_id"] and (session_id is None or row["session_id"] == session_id)}),
        usage_count=selected_count,
        selected_count=selected_count,
        measured_count=len(valid),
        excluded_count=sum(excluded.values()),
        excluded_row_reasons=excluded,
        observed_session_count=len(session_ids),
        availability="partial" if excluded or cache_unknown else "available",
        coverage="partial" if excluded or cache_unknown else "complete",
        cache_coverage="partial" if cache_unknown else "complete",
        first_timestamp=min(timestamps),
        last_timestamp=max(timestamps),
        cost_provenance="provider-reported" if aggregate and aggregate.get("cost") is not None else "unavailable",
        metrics=metrics or {},
        **(aggregate or {}),
    )
    if session_id is not None and len(session_ids - {session_id}) > 0:
        result["reason"] = "overlapping_sessions"
    elif excluded:
        result["reason"] = next(iter(excluded))
    return result


def observe_window_usage(
    database: Path,
    *,
    start: str,
    end: str,
    model: str | None = None,
    connection_id: str | None = None,
    observation_budget_ms: int = OBSERVATION_BUDGET_MS,
) -> dict[str, Any]:
    """Report verified provider rows in a bounded time window."""
    rows, metrics, failure = _canonical_read(
        database,
        start=start,
        end=end,
        model=model,
        connection_id=connection_id,
        observation_budget_ms=observation_budget_ms,
    )
    if failure:
        failure["attribution"] = "window"
        return failure
    return _project(rows, attribution="window", metrics=metrics)


def observe_usage(
    database: Path,
    *,
    start: str,
    end: str,
    session_id: str,
    connection_id: str | None = None,
    observation_budget_ms: int = OBSERVATION_BUDGET_MS,
) -> dict[str, Any]:
    if not session_id.strip():
        raise ValueError("session_id is required")
    rows, metrics, failure = _canonical_read(
        database,
        start=start,
        end=end,
        connection_id=connection_id,
        observation_budget_ms=observation_budget_ms,
    )
    if failure:
        return failure
    return _project(rows, attribution="session", session_id=session_id, metrics=metrics)


def observe_run_usage(
    database: Path,
    *,
    start: str,
    end: str,
    expected_session_id: str | None = None,
    connection_id: str | None = None,
    observation_budget_ms: int = OBSERVATION_BUDGET_MS,
) -> dict[str, Any]:
    """Attribute a bounded run only to the caller-provided provider session."""
    start_at = _timestamp(start)
    end_at = _timestamp(end)
    if end_at <= start_at:
        raise ValueError("end must be after start")
    if not isinstance(expected_session_id, str) or not expected_session_id.strip():
        return _result("inconclusive", "session_binding_missing")

    rows, metrics, failure = _canonical_read(
        database,
        start=start,
        end=end,
        connection_id=connection_id,
        observation_budget_ms=observation_budget_ms,
    )
    if failure:
        return failure
    sessions = {row["session_id"] for row in rows if row["request_timestamp"] is not None}
    if not sessions or expected_session_id not in sessions:
        reason = "no_session_rows"
        if sessions:
            reason = "session_attribution_missing" if "<unattributed>" in sessions else "session_attribution_mismatch"
        return _result("inconclusive", reason, observed_session_count=len(sessions))
    return _project(rows, attribution="session", session_id=expected_session_id, metrics=metrics)


def _result(disposition: str, reason: str | None, **fields: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": "9router-usage-observation-v1",
        "disposition": disposition,
        "source": "9router-local-read-only",
    }
    if "availability" not in fields:
        if disposition in {"matched", "observed_window"}:
            fields["availability"] = "partial" if fields.get("excluded_count", 0) else "available"
        elif reason in {"no_usage_rows", "no_session_rows"}:
            fields["availability"] = "missing"
        else:
            fields["availability"] = "inconclusive"
    if "coverage" not in fields:
        fields["coverage"] = "complete" if not fields.get("excluded_count", 0) else "partial"
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
