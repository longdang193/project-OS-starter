import json
from pathlib import Path

from scripts.secretary_live_runtime import (
    _parse_codex_token_usage,
    _parse_json_object,
    _trial_metrics,
    resolve_codex_runtime,
    run_smoke,
)


def test_resolve_codex_runtime_uses_native_home_and_redacts_auth(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        'model_provider = "9router"\nmodel = "combo-high"\n', encoding="utf-8"
    )
    (tmp_path / "auth.json").write_text(
        json.dumps({"auth_mode": "apikey", "OPENAI_API_KEY": "secret"}), encoding="utf-8"
    )
    runtime = resolve_codex_runtime(tmp_path)
    assert runtime["provider"] == "9router"
    assert runtime["model"] == "combo-high"
    assert runtime["auth_present"] is True
    assert "OPENAI_API_KEY" not in json.dumps(runtime)


def test_run_smoke_blocks_without_owned_secretary_runtime(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        'model_provider = "9router"\nmodel = "combo-high"\n', encoding="utf-8"
    )
    (tmp_path / "auth.json").write_text('{"auth_mode":"apikey"}', encoding="utf-8")
    result = run_smoke(
        task_id="task-1",
        plan_revision="plan-1",
        run_id="run-1",
        attempt_id="attempt-1",
        codex_home=tmp_path,
        runner=None,
    )
    assert result["status"] == "BLOCKED_CAPABILITY"
    assert result["provider"] == "9router"


def test_run_smoke_blocks_provider_mismatch_without_fallback(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        'model_provider = "other"\nmodel = "combo-high"\n', encoding="utf-8"
    )
    (tmp_path / "auth.json").write_text('{"auth_mode":"apikey"}', encoding="utf-8")
    result = run_smoke(
        task_id="task-1",
        plan_revision="plan-1",
        run_id="run-1",
        attempt_id="attempt-1",
        codex_home=tmp_path,
        runner=None,
    )
    assert result["status"] == "BLOCKED_CAPABILITY"
    assert result["capability_reason"] == "configured provider is not 9router"


def test_runtime_parses_machine_response_and_codex_usage(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        '{"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":8}}\n',
        encoding="utf-8",
    )
    assert _parse_json_object('{"publication":"success"}') == {"publication": "success"}
    assert _parse_codex_token_usage(events) == 20


def test_runner_receives_all_runtime_identity_fields(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        'model_provider = "9router"\nmodel = "combo-high"\n', encoding="utf-8"
    )
    (tmp_path / "auth.json").write_text('{"auth_mode":"apikey"}', encoding="utf-8")
    captured = {}

    def runner(runtime, **identifiers):
        captured.update(runtime=runtime, identifiers=identifiers)
        return {
            "schema": "project-os.secretary-live-receipt.v1",
            "status": "READY",
            **identifiers,
            "provider": runtime["provider"],
            "model": runtime["model"],
            "timestamps": {"entry_at": "2026-10-09T10:00:00Z", "exit_at": "2026-10-09T10:00:01Z"},
            "completion": {"observed": True, "operation": "secretary_smoke"},
            "provenance": {"source_type": "runtime", "producer": "test", "source_ref": "test", "observed": True},
            "metrics": {"cos_turns": 1, "secretary_turns": 1, "human_interventions": 0, "token_usage": None, "cost": None},
            "outcomes": {"publication": "success", "settlement": "observed", "acceptance": "accepted"},
        }

    result = run_smoke(
        task_id="task-1",
        plan_revision="plan-1",
        run_id="run-1",
        attempt_id="attempt-1",
        codex_home=tmp_path,
        runner=runner,
    )
    assert result["status"] == "READY"
    assert result["metrics"]["cos_turns"] == 1
    assert captured["identifiers"] == {
        "task_id": "task-1",
        "plan_revision": "plan-1",
        "run_id": "run-1",
        "attempt_id": "attempt-1",
    }


def test_baseline_arm_has_no_secretary_turn(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        'model_provider = "9router"\nmodel = "combo-high"\n', encoding="utf-8"
    )
    (tmp_path / "auth.json").write_text('{"auth_mode":"apikey"}', encoding="utf-8")

    def runner(runtime, **identifiers):
        return {
            "schema": "project-os.secretary-live-receipt.v1",
            "status": "READY",
            **identifiers,
            "provider": runtime["provider"],
            "model": runtime["model"],
            "timestamps": {"entry_at": "2026-10-09T10:00:00Z", "exit_at": "2026-10-09T10:00:01Z"},
            "completion": {"observed": True, "operation": "secretary_smoke"},
            "provenance": {"source_type": "runtime", "producer": "test", "source_ref": "test", "observed": True},
            "metrics": {"cos_turns": 1, "secretary_turns": 0, "human_interventions": 0, "token_usage": None, "cost": None},
            "outcomes": {"publication": "success", "settlement": "observed", "acceptance": "accepted"},
        }

    result = run_smoke(
        task_id="task-1",
        plan_revision="plan-1",
        run_id="run-1",
        attempt_id="attempt-1",
        codex_home=tmp_path,
        runner=runner,
    )
    assert result["metrics"]["secretary_turns"] == 0


def test_trial_metrics_always_counts_controller_turn() -> None:
    assert _trial_metrics(secretary_enabled=False, token_usage=None) == {
        "cos_turns": 1,
        "secretary_turns": 0,
        "human_interventions": 0,
        "token_usage": None,
        "cost": None,
    }


def test_default_runner_converts_missing_herdr_to_blocked(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "config.toml").write_text(
        'model_provider = "9router"\nmodel = "combo-high"\n', encoding="utf-8"
    )
    (tmp_path / "auth.json").write_text('{"auth_mode":"apikey"}', encoding="utf-8")
    monkeypatch.setattr("scripts.secretary_live_runtime.shutil.which", lambda name: None)
    result = run_smoke(
        task_id="task-1",
        plan_revision="plan-1",
        run_id="run-1",
        attempt_id="attempt-1",
        codex_home=tmp_path,
    )
    assert result["status"] == "BLOCKED_CAPABILITY"
    assert result["capability_reason"] == "Herdr or Codex executable unavailable"
