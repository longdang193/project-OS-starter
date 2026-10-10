from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.observe_9router_usage import observe_usage, observe_window_usage


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
            "insert into usageHistory values (?, ?, 'codex', ?, 'connection-1', 'secret', '/v1/responses', ?, ?, ?, 'ok', '{}', '{}')",
            (index, timestamp, model, input_tokens, output_tokens, cost),
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


def test_observer_rejects_non_finite_cost(tmp_path: Path) -> None:
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

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "invalid_cost"


def test_observer_rejects_overlapping_sessions(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database, other_session=True)

    result = observe_usage(
        database,
        start="2026-10-09T14:24:49Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "overlapping_sessions"


def test_observer_rejects_session_rows_outside_window(tmp_path: Path) -> None:
    database = tmp_path / "data.sqlite"
    _database(database)

    result = observe_usage(
        database,
        start="2026-10-09T14:24:51Z",
        end="2026-10-09T14:24:56Z",
        session_id="session-1",
        connection_id="connection-1",
    )

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "timestamp_boundary_unproven"


def test_observer_rejects_duplicate_request_join_keys(tmp_path: Path) -> None:
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

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "usage_join_ambiguous"


def test_observer_rejects_unattributed_request_rows(tmp_path: Path) -> None:
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

    assert result["disposition"] == "inconclusive"
    assert result["reason"] == "overlapping_sessions"


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
