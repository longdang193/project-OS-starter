"""
@meta
type: test
scope: unit
domain: config
covers:
  - Starter repo config validation for publication config, adapter mappings, and runtime configs
excludes:
  - Full publication/export execution
tags:
  - fast
  - ci-safe
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from shutil import rmtree


REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate_repo_config.py"


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_test_root() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"validate-repo-config-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ValidateRepoConfigTests(unittest.TestCase):
    def test_validator_passes_for_current_repo(self) -> None:
        result = run_validator()

        self.assertEqual(result.returncode, 0)
        self.assertIn("repo config validation passed", result.stdout.lower())

    def test_validator_fails_when_publication_config_is_missing_required_keys(self) -> None:
        test_root = make_test_root()
        try:
            publication_config = test_root / "repo_config" / "publication-config.json"
            adapter_mappings = test_root / "repo_config" / "agent-adapter-mappings.json"
            runtime_config = test_root / "configs" / "starter-runtime.yaml"

            write_json(publication_config, {"publicPaths": ["README.md"]})
            write_json(
                adapter_mappings,
                [
                    {
                        "source": "agent-core/adapters/codex/root-AGENTS.template.md",
                        "destination": "AGENTS.md",
                        "prefix": "#",
                    }
                ],
            )
            write_text(runtime_config, "runtime:\n  environment: starter\n")
            write_text(
                test_root / "agent-core" / "adapters" / "codex" / "root-AGENTS.template.md",
                "# template\n",
            )

            result = run_validator(
                "--publication-config",
                str(publication_config),
                "--adapter-mappings",
                str(adapter_mappings),
                "--runtime-config-root",
                str(test_root / "configs"),
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("forbiddenpaths", result.stdout.lower())
        finally:
            rmtree(test_root, ignore_errors=True)

    def test_validator_fails_when_adapter_mapping_source_is_missing(self) -> None:
        test_root = make_test_root()
        try:
            publication_config = test_root / "repo_config" / "publication-config.json"
            adapter_mappings = test_root / "repo_config" / "agent-adapter-mappings.json"
            runtime_config = test_root / "configs" / "starter-runtime.yaml"

            write_json(
                publication_config,
                {
                    "publicPaths": ["README.md"],
                    "forbiddenPaths": [".codex"],
                    "requiredPaths": ["README.md"],
                    "allowedGeneratedPaths": [],
                    "scrubPrivateReferencePaths": ["README.md"],
                },
            )
            write_json(
                adapter_mappings,
                [
                    {
                        "source": "agent-core/adapters/codex/missing.template.md",
                        "destination": "AGENTS.md",
                        "prefix": "#",
                    }
                ],
            )
            write_text(runtime_config, "runtime:\n  environment: starter\n")
            write_text(test_root / "README.md", "# readme\n")

            result = run_validator(
                "--publication-config",
                str(publication_config),
                "--adapter-mappings",
                str(adapter_mappings),
                "--runtime-config-root",
                str(test_root / "configs"),
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("missing adapter source", result.stdout.lower())
        finally:
            rmtree(test_root, ignore_errors=True)

    def test_validator_fails_when_runtime_config_is_not_a_mapping(self) -> None:
        test_root = make_test_root()
        try:
            publication_config = test_root / "repo_config" / "publication-config.json"
            adapter_mappings = test_root / "repo_config" / "agent-adapter-mappings.json"
            runtime_config = test_root / "configs" / "starter-runtime.yaml"

            write_json(
                publication_config,
                {
                    "publicPaths": ["README.md"],
                    "forbiddenPaths": [".codex"],
                    "requiredPaths": ["README.md"],
                    "allowedGeneratedPaths": [],
                    "scrubPrivateReferencePaths": ["README.md"],
                },
            )
            write_json(
                adapter_mappings,
                [
                    {
                        "source": "agent-core/adapters/codex/root-AGENTS.template.md",
                        "destination": "AGENTS.md",
                        "prefix": "#",
                    }
                ],
            )
            write_text(runtime_config, "- just\n- a\n- list\n")
            write_text(test_root / "README.md", "# readme\n")
            write_text(
                test_root / "agent-core" / "adapters" / "codex" / "root-AGENTS.template.md",
                "# template\n",
            )

            result = run_validator(
                "--publication-config",
                str(publication_config),
                "--adapter-mappings",
                str(adapter_mappings),
                "--runtime-config-root",
                str(test_root / "configs"),
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("top-level mapping", result.stdout.lower())
        finally:
            rmtree(test_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
