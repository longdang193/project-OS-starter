from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import time

from scripts.observe_9router_usage import observe_run_usage, observe_usage, observe_window_usage


def _database(path: Path, *, other_session: bool = False) -> None:
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
        """
    )
    rows = [
        ("2026-10-09T14:24:50.000Z", "session-1", "gpt-test", 100, 10, 0.2),
        ("2026-10-09T14:24:55.000Z", "session-1", "gpt-test", 120, 12, 0.24),
    ]
    if other_session:
        rows.append(("2026-10-09T14:24:52.000Z", "session-2", "gpt-test", 90, 9, 0.18))
    for index, (timestamp, session, model, input_tokens, output_tokens, cost) in enumerate(rows):
        data = json.dumps({"providerRequest": {"client_metadata": {"session_id": session}}})
        connection.execute(
            "insert into requestDetails values (?, ?, 'codex', ?, 'connection-1', 'success', ?)",
            (f"request-{index}", timestamp, model, data),
        )
        connection.execute(
            "insert into usageHistory values (?, ?, 'codex', ?, 'connection-1', 'secret', '/v1/responses', ?, ?, ?, 'ok', '{}', ?)",
            (index, timestamp, model, input_tokens, output_tokens, cost, json.dumps({"request_detail_id": f"request-{index}"})),
        )
    connection.commit()
    connection.close()


def test_observer_matches_session_and_aggregates_cost(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["input_tokens"] == 220
    assert result["output_tokens"] == 22
    assert result["total_tokens"] == 242
    assert result["cost"] == 0.44
    assert result["cache_read_input_tokens"] == 0


def test_observer_reads_persisted_client_metadata_session(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.execute(
        "update requestDetails set data = ?",
        (json.dumps({"clientMetadata": {"session_id": "session-1"}}),),
    )
    connection.commit()
    connection.close()

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["request_count"] == 2


def test_run_observer_discovers_one_session_and_attributes_usage(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)

    result = observe_run_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        expected_session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["session_id"] == "session-1"
    assert result["cost"] == 0.44


def test_run_observer_preserves_matching_rows_with_overlapping_sessions(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database, other_session=True)

    result = observe_run_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        expected_session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["reason"] == "overlapping_sessions"
    assert result["availability"] == "partial"
    assert result["coverage"] == "partial"


def test_run_observer_reports_missing_session_attribution(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.execute(
        "update requestDetails set data = ?",
        (json.dumps({"clientMetadata": {}}),),
    )
    connection.commit()
    connection.close()

    result = observe_run_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        expected_session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "session_attribution_missing"


def test_run_observer_rejects_unique_unrelated_session(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)

    result = observe_run_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        expected_session_id="secretary-session",
        connection_id="connection-1",
    )

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "session_attribution_mismatch"


def test_run_observer_requires_expected_session_binding(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)

    result = observe_run_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        connection_id="connection-1",
    )

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "session_binding_missing"


def test_window_observer_reports_cached_tokens_and_provider_cost_without_attribution(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.execute(
        "update usageHistory set tokens = ? where id = 0",
        (json.dumps({"cached_tokens": 80, "cache_creation_input_tokens": 5}),),
    )
    connection.commit()
    connection.close()

    result = observe_window_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
    )

    assert result["disposition"] == "observed_window"
    assert result["confidence"] == "unattributed"
    assert result["input_tokens"] == 220
    assert result["output_tokens"] == 22
    assert result["cache_read_input_tokens"] == 80
    assert result["cache_write_input_tokens"] == 5
    assert result["cost"] == 0.44
    assert result["cost_provenance"] == "provider-reported"
    assert "secret" not in json.dumps(result)


def test_window_observer_stays_inconclusive_without_rows(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)

    result = observe_window_usage(
        database,
        start="2026-10-09T15:00:00Z",
        end="2026-10-09T15:00:01Z",
    )

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "no_usage_rows"


def test_observer_normalizes_timestamp_formats_before_joining(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.execute(
        "update requestDetails set timestamp = ? where id = ?",
        ("2026-10-09T16:24:50+02:00", "request-0"),
    )
    connection.commit()
    connection.close()

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["request_count"] == 2


def test_observer_preserves_valid_rows_when_cost_is_invalid(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.execute("update usageHistory set cost = ? where id = 0", (float("inf"),))
    connection.commit()
    connection.close()

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["reason"] == "invalid_cost"
    assert result["measured_count"] == 1
    assert result["cost"] == 0.24


def test_observer_preserves_matching_rows_with_overlapping_sessions_for_session_query(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database, other_session=True)

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["reason"] == "overlapping_sessions"
    assert result["availability"] == "partial"


def test_observer_reports_rows_inside_requested_window(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)

    result = observe_usage(
        database,
        start="2026-10-09T14:24:51Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["measured_count"] == 1


def test_observer_excludes_unmatched_request_detail_rows(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    data = json.dumps({"providerRequest": {"client_metadata": {"session_id": "session-1"}}})
    connection.execute(
        "insert into requestDetails values (?, ?, 'codex', ?, 'connection-1', 'success', ?)",
        ("request-duplicate", "2026-10-09T14:24:50.000Z", "gpt-test", data),
    )
    connection.commit()
    connection.close()

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["availability"] == "partial"
    assert result["excluded_row_reasons"]["missing_usage"] == 1


def test_observer_excludes_unattributed_request_rows(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.execute(
        "insert into requestDetails values (?, ?, 'codex', ?, 'connection-1', 'success', ?)",
        (
            "request-unattributed",
            "2026-10-09T14:24:50.000Z",
            "gpt-test",
            json.dumps({"providerRequest": {"client_metadata": {}}}),
        ),
    )
    connection.commit()
    connection.close()

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["availability"] == "partial"
    assert result["excluded_row_reasons"]["other_session"] == 1


def test_observer_never_selects_sensitive_columns(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert "secret" not in json.dumps(result)
    assert "data" not in result


def test_observer_keeps_valid_usage_from_failed_requests(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.execute("update requestDetails set status = 'failed' where id = 'request-0'")
    connection.commit()
    connection.close()

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "matched"
    assert result["measured_count"] == 2
    assert result["input_tokens"] == 220


def test_observer_reports_unknown_cache_fields_without_zero_fill(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.execute("update usageHistory set tokens = '' where id = 0")
    connection.commit()
    connection.close()

    result = observe_window_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
    )

    assert result["disposition"] == "observed_window"
    assert result["cache_read_input_tokens"] is None
    assert result["cache_write_input_tokens"] is None
    assert result["coverage"] == "partial"


def test_observer_reports_database_unavailability_as_inconclusive(tmp_path: Path) -> None:
    result = observe_window_usage(
        tmp_path / "missing.sqlite",
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
    )

    assert result["availability"] == "inconclusive"
    assert result["disposition"] == "inconclusive"


def test_observer_returns_within_bound_when_database_is_locked(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    lock = sqlite3.connect(database)
    lock.execute("begin exclusive")
    try:
        started = time.perf_counter()
        result = observe_window_usage(
            database,
            start="2026-10-09T14:24:49Z",
            end="2026-10-09T14:24:56Z",
            observation_budget_ms=50,
        )
        elapsed_ms = (time.perf_counter() - started) * 1_000
    finally:
        lock.rollback()
        lock.close()

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "database_locked"
    assert elapsed_ms < 1_000


def test_observer_uses_timestamp_range_for_large_indexed_history(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        create index idx_usage_provider_timestamp on usageHistory(provider, timestamp);
        create index idx_request_provider_timestamp on requestDetails(provider, timestamp);
        """
    )
    history_rows = []
    request_rows = []
    for index in range(100_000):
        timestamp = f"2025-01-{(index % 28) + 1:02d}T00:00:00.000Z"
        detail_id = f"history-{index}"
        request_rows.append(
            (
                detail_id,
                timestamp,
                "codex",
                "gpt-test",
                "connection-1",
                "success",
                json.dumps({"providerRequest": {"client_metadata": {"session_id": "history"}}}),
            )
        )
        history_rows.append(
            (
                index + 2,
                timestamp,
                "codex",
                "gpt-test",
                "connection-1",
                "secret",
                "/v1/responses",
                1,
                1,
                0.01,
                "ok",
                "{}",
                json.dumps({"request_detail_id": detail_id}),
            )
        )
    connection.executemany("insert into requestDetails values (?, ?, ?, ?, ?, ?, ?)", request_rows)
    connection.executemany("insert into usageHistory values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", history_rows)
    connection.commit()
    connection.close()

    result = observe_window_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        observation_budget_ms=100,
    )

    assert result["disposition"] == "observed_window"
    assert result["measured_count"] == 2
