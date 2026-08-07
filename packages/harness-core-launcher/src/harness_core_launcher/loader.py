from __future__ import annotations

import importlib
import json
from types import ModuleType
from typing import Any


def load_core() -> ModuleType | dict[str, Any]:
    try:
        return importlib.import_module("harness_core")
    except (ImportError, RuntimeError):
        return {
            "ok": False,
            "failure_class": "environment",
            "code": "harness_core_environment_unavailable",
            "package": "harness-core",
        }


def run_core_cli(argv: list[str] | None = None) -> int:
    core = load_core()
    if isinstance(core, dict):
        print(json.dumps(core, sort_keys=True))
        return 1
    return importlib.import_module("harness_core.cli").main(argv)
