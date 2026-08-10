from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_harness_release_profile",
    ROOT / "scripts" / "validate_harness_release_profile.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_classifies_implementation_only_change() -> None:
    assert MODULE.classify_release_paths(["packages/harness-core/src/harness_core/authority.py"]) == "implementation"


def test_classifies_profile_change() -> None:
    assert MODULE.classify_release_paths(["packages/harness-core/src/harness_core/runtime_profile.py"]) == "profile"


def test_classifies_consumer_schema_change() -> None:
    assert MODULE.classify_release_paths(["repo_config/harness.yaml"]) == "consumer_schema"


def test_validates_current_policy_and_guidance() -> None:
    result = MODULE.validate(ROOT)

    assert result["state"] == "ready"
    assert result["protocol_profile"]["schema_id"] == "harness_runtime_protocol_profile/v1"
