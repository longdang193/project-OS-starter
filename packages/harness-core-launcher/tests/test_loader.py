from __future__ import annotations

import importlib

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
