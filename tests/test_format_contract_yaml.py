"""
@meta
type: test
scope: unit
domain: docs
covers:
  - Starter YAML contract formatting normalization for docs/features and docs/stages
  - Check mode vs rewrite mode behavior for the starter contract YAML formatter
excludes:
  - Full-repo end-to-end normalization runs
tags:
  - fast
  - ci-safe
"""

from __future__ import annotations

import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from shutil import rmtree


REPO_ROOT = Path(__file__).resolve().parent.parent
FORMATTER = REPO_ROOT / "scripts" / "format_contract_yaml.py"

SAMPLE_YAML = """feature_id: sample-feature
name: Sample feature
version: 1
status: active
type: workflow
summary: Example contract
invariants:
  - "Training behavior is controlled by `configs/runtime.yaml`."
  - Production retraining remains distinct from the optimization workflow.
capabilities:
  - "Apply experiment metadata from `configs/runtime.yaml`."
  - Accept an explicit training config path.
"""


def run_formatter(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FORMATTER), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_test_root() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"format-contract-yaml-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


class FormatContractYamlTests(unittest.TestCase):
    def test_check_mode_detects_drift_without_rewriting(self) -> None:
        test_root = make_test_root()
        try:
            target = test_root / "docs" / "features" / "sample" / "sample.yaml"
            target.parent.mkdir(parents=True)
            target.write_text(SAMPLE_YAML, encoding="utf-8")

            result = run_formatter("--check", str(target))

            self.assertEqual(result.returncode, 1)
            self.assertEqual(target.read_text(encoding="utf-8"), SAMPLE_YAML)
            self.assertIn("would reformat", result.stdout.lower())
        finally:
            rmtree(test_root, ignore_errors=True)

    def test_rewrite_mode_normalizes_optional_quotes_and_is_idempotent(self) -> None:
        test_root = make_test_root()
        try:
            target = test_root / "docs" / "stages" / "sample.yaml"
            target.parent.mkdir(parents=True)
            target.write_text(SAMPLE_YAML, encoding="utf-8")

            first = run_formatter(str(target))
            self.assertEqual(first.returncode, 0)

            normalized_once = target.read_text(encoding="utf-8")
            self.assertNotIn(
                '"Training behavior is controlled by `configs/runtime.yaml`."',
                normalized_once,
            )
            self.assertNotIn(
                '"Apply experiment metadata from `configs/runtime.yaml`."',
                normalized_once,
            )

            second = run_formatter(str(target))
            self.assertEqual(second.returncode, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), normalized_once)
        finally:
            rmtree(test_root, ignore_errors=True)

    def test_check_mode_passes_after_normalization(self) -> None:
        test_root = make_test_root()
        try:
            target = test_root / "docs" / "features" / "sample" / "sample.yaml"
            target.parent.mkdir(parents=True)
            target.write_text(SAMPLE_YAML, encoding="utf-8")

            rewrite = run_formatter(str(target))
            self.assertEqual(rewrite.returncode, 0)

            check = run_formatter("--check", str(target))
            self.assertEqual(check.returncode, 0)
            self.assertIn("already normalized", check.stdout.lower())
        finally:
            rmtree(test_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
