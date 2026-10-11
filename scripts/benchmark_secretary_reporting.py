"""Measure the read-only Secretary reporting observer on synthetic SQLite data."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sqlite3
import statistics
import subprocess
import tempfile
import time
import tracemalloc
from typing import Any, Callable


BASE_REVISION = "50ea7498596f7487f0650f3f6c0737c4d2a740dd"
START = "2026-10-09T14:24:49Z"
END = "2026-10-09T14:24:56Z"
_REPORTING_QUERY = """
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
    from usageHistory indexed by idx_usage_timestamp
    where provider = 'codex'
       and timestamp >= ? and timestamp <= ?
      and (? is null or connectionId = ?)
      and (? is null or model = ?)
)
select r.detail_id, u.usage_timestamp
from request_rows r
left join usage_rows u on u.detail_id = r.detail_id
union all
select u.detail_id, u.usage_timestamp
from usage_rows u
left join request_rows r on r.detail_id = u.detail_id
where r.detail_id is null
"""


def _load_observer(phase: str) -> Callable[..., dict[str, Any]]:
    if phase == "final":
        source = Path(__file__).with_name("observe_9router_usage.py").read_text(encoding="utf-8")
        module_name = "final_observer"
    else:
        source = subprocess.run(
            ["git", "show", f"{BASE_REVISION}:scripts/observe_9router_usage.py"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        module_name = "baseline_observer"
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(module_name, loader=None))
    exec(compile(source, f"{module_name}.py", "exec"), module.__dict__)
    return module.observe_window_usage


def _build_database(path: Path, history_size: int) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        create table usageHistory (
            id integer primary key,
            timestamp text not null,
            provider text,
            model text,
            connectionId text,
            apiKey text,
            endpoint text,
            promptTokens integer,
            completionTokens integer,
            cost real,
            status text,
            tokens text,
            meta text
        );
        create table requestDetails (
            id text primary key,
            timestamp text not null,
            provider text,
            model text,
            connectionId text,
            status text,
            data text not null
        );
        create index idx_usage_timestamp on usageHistory(timestamp);
        create index idx_request_timestamp on requestDetails(timestamp);
        """
    )
    for index in range(2):
        timestamp = f"2026-10-09T14:24:5{index}.000Z"
        detail_id = f"request-{index}"
        connection.execute(
            "insert into requestDetails values (?, ?, 'codex', 'gpt-test', 'connection-1', 'success', ?)",
            (detail_id, timestamp, json.dumps({"providerRequest": {"client_metadata": {"session_id": "session-1"}}})),
        )
        connection.execute(
            "insert into usageHistory values (?, ?, 'codex', 'gpt-test', 'connection-1', 'secret', '/v1/responses', 100, 10, 0.2, 'ok', '{}', ?)",
            (index, timestamp, json.dumps({"request_detail_id": detail_id})),
        )
    for index in range(history_size):
        timestamp = f"2025-01-{(index % 28) + 1:02d}T00:00:00Z"
        detail_id = f"history-{index}"
        connection.execute(
            "insert into requestDetails values (?, ?, 'codex', 'gpt-test', 'connection-1', 'success', ?)",
            (detail_id, timestamp, json.dumps({"providerRequest": {"client_metadata": {"session_id": "history"}}})),
        )
        connection.execute(
            "insert into usageHistory values (?, ?, 'codex', 'gpt-test', 'connection-1', 'secret', '/v1/responses', 1, 1, 0.01, 'ok', '{}', ?)",
            (index + 2, timestamp, json.dumps({"request_detail_id": detail_id})),
        )
    connection.commit()
    connection.close()


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def _inspect_database(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(path)
    try:
        indexes: dict[str, list[dict[str, Any]]] = {}
        for table in ("requestDetails", "usageHistory"):
            indexes[table] = []
            for row in connection.execute(f"pragma index_list({table})"):
                index_name = row[1]
                columns = [item[2] for item in connection.execute(f"pragma index_info({index_name})")]
                indexes[table].append({"name": index_name, "columns": columns, "unique": bool(row[2])})
        plan = [
            {"id": row[0], "parent": row[1], "detail": row[3]}
            for row in connection.execute(
                f"explain query plan {_REPORTING_QUERY}",
                (
                    START, END, None, None, None, None,
                    START, END, None, None, None, None,
                ),
            )
        ]
        return {"indexes": indexes, "query_plan": plan}
    finally:
        connection.close()


def _trial(observer: Callable[..., dict[str, Any]], history_size: int, repetitions: int) -> dict[str, Any]:
    durations: list[float] = []
    peak_memory = 0
    dispositions: list[str] = []
    metrics: dict[str, Any] = {}
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "data.sqlite"
        _build_database(database, history_size)
        inspection = _inspect_database(database)
        for _ in range(repetitions):
            tracemalloc.start()
            started = time.perf_counter()
            result = observer(database, start=START, end=END)
            durations.append((time.perf_counter() - started) * 1_000
            )
            _, peak = tracemalloc.get_traced_memory()
            peak_memory = max(peak_memory, peak)
            tracemalloc.stop()
            dispositions.append(result.get("disposition", "unknown"))
            metrics = result.get("metrics", {}) if isinstance(result.get("metrics"), dict) else {}
        return {
            "history_size": history_size,
            "repetitions": repetitions,
            "p50_ms": _percentile(durations, 0.50),
            "p95_ms": _percentile(durations, 0.95),
            "query_count": metrics.get("query_count", "unknown"),
            "progress_calls": metrics.get("progress_calls", "unknown"),
            "selected_rows": result.get("selected_count", "unknown"),
            "validated_rows": result.get("measured_count", "unknown"),
            "excluded_rows": result.get("excluded_count", "unknown"),
            "peak_memory_bytes": peak_memory,
            "dispositions": dispositions,
            "database_inspection": inspection,
        }


def run_benchmark(*, phase: str, repetitions: int, history_sizes: list[int]) -> dict[str, Any]:
    if repetitions <= 0 or not history_sizes or any(size < 0 for size in history_sizes):
        raise ValueError("repetitions and history sizes must be positive")
    observer = _load_observer(phase)
    return {
        "schema_version": "secretary-reporting-benchmark-v1",
        "phase": phase,
        "baseline_revision": BASE_REVISION,
        "environment": {
            "python": __import__("platform").python_version(),
            "sqlite": sqlite3.sqlite_version,
            "os": __import__("platform").platform(),
        },
        "workload": {"start": START, "end": END, "history_sizes": history_sizes, "repetitions": repetitions},
        "trials": [_trial(observer, size, repetitions) for size in history_sizes],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "final"), required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--history-sizes", default="0,100,1000")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_benchmark(
        phase=args.phase,
        repetitions=args.repetitions,
        history_sizes=[int(value) for value in args.history_sizes.split(",") if value.strip()],
    )
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
