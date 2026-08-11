from __future__ import annotations

import importlib
import json

import pytest

from harness_core_launcher import cli
from harness_core_launcher.loader import load_core, run_core_cli


def test_missing_core_returns_typed_environment_failure(monkeypatch) -> None:
    def missing(_: str):
        raise ModuleNotFoundError("harness_core")

    monkeypatch.setattr(importlib, "import_module", missing)

    assert load_core() == {
        "ok": False,
        "failure_class": "environment",
        "code": "harness_core_environment_unavailable",
        "package": "harness-core",
    }


def test_core_cli_returns_typed_environment_failure_without_loading_consumer(monkeypatch, capsys) -> None:
    monkeypatch.setattr(importlib, "import_module", lambda _: (_ for _ in ()).throw(ModuleNotFoundError("harness_core")))

    assert run_core_cli(["validate", "--repo-root", "ignored"]) == 1
    assert capsys.readouterr().out.strip() == '{"code": "harness_core_environment_unavailable", "failure_class": "environment", "ok": false, "package": "harness-core"}'


def test_preflight_uses_runtime_manager(monkeypatch, tmp_path, capsys) -> None:
    captured = []

    class FakeManager:
        def __init__(self, root):
            captured.append(root)

        def invoke_host(self, arguments):
            captured.append(arguments)
            return {"state": "ready"}

    monkeypatch.setattr(cli, "RuntimeManager", FakeManager)

    assert cli.main(["--runtime-root", str(tmp_path), "preflight"]) == 0
    assert captured == [tmp_path, ["preflight"]]
    assert json.loads(capsys.readouterr().out) == {"state": "ready"}


def test_executable_decision_uses_active_host_runtime(monkeypatch, tmp_path, capsys) -> None:
    captured = []

    class FakeManager:
        def __init__(self, root):
            captured.append(root)

        def invoke_host(self, arguments):
            captured.append(arguments)
            return {"state": "planned"}

    monkeypatch.setattr(cli, "RuntimeManager", FakeManager)

    assert cli.main([
        "--runtime-root",
        str(tmp_path),
        "decision",
        "--harness-root",
        "repo",
        "--run-id",
        "retry-run",
        "--decision",
        "decision.json",
    ]) == 1
    assert captured == [tmp_path, [
        "decision",
        "--harness-root",
        "repo",
        "--run-id",
        "retry-run",
        "--decision",
        "decision.json",
    ]]
    assert json.loads(capsys.readouterr().out) == {"state": "planned"}

def test_decision_help_identifies_json_file(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        cli.main(["decision", "--help"])

    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert "--decision DECISION_FILE" in help_text
    assert "Path to controller decision JSON file" in help_text
