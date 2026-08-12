"""
@meta
name: test_starter_kit_generation
type: test
scope: unit
domain: docs
covers:
  - Starter-kit manifest-driven generation excludes adapter-regeneration and runtime-bundle surfaces
  - Starter-kit verification catches forbidden shipped paths and missing required surfaces
  - Starter-kit generation supports omitted copied subpaths and required empty directories
  - Starter-kit build fails fast when expected generated provider root instruction files are missing
  - Starter-kit validation can detect parity drift between generated export and synced sibling repo trees
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import json
import pytest
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_PATH = REPO_ROOT / "scripts" / "build_starter_kit.py"
VERIFY_PATH = REPO_ROOT / "scripts" / "validate_starter_kit.py"
SCRIPTS_ROOT = str(REPO_ROOT / "scripts")

if SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, SCRIPTS_ROOT)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILD = load_module("build_starter_kit", BUILD_PATH)
VERIFY = load_module("validate_starter_kit", VERIFY_PATH)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def make_manifest(repo_root: Path) -> Path:
    manifest_path = repo_root / "repo_config" / "starter-kit-manifest.json"
    write_json(
        manifest_path,
        {
            "outputRoot": "project-OS-starter-kit",
            "requiredPaths": [
                ".gitignore",
                "AGENTS.md",
                "GEMINI.md",
                "CLAUDE.md",
                ".agents/skills/skill-spec-drafting/SKILL.md",
                "repo_config/planning_artifact_schema.yaml",
                "requirements.txt",
                "docs/superpowers/plans",
            ],
            "forbiddenPaths": [
                ".codex",
                "adapters",
                "scripts/sync_agent_adapters.py",
                "scripts/deploy_agent_runtime.py",
                "tests/test_sync_agent_adapters.py",
                "tests/test_deploy_agent_runtime.py",
            ],
            "copyPaths": [
                ".gitignore",
                "AGENTS.md",
                "generated_agents/antigravity/GEMINI.md",
                "generated_agents/claude/CLAUDE.md",
                ".agents/skills/skill-spec-drafting/SKILL.md",
                "repo_config/planning_artifact_schema.yaml",
                "requirements.txt",
                "docs/operating_system",
            ],
            "omitPaths": [
                "docs/operating_system/runtime",
            ],
            "createEmptyDirs": [
                "docs/superpowers/plans",
            ],
        },
    )
    return manifest_path


def test_build_starter_kit_copies_required_and_excludes_forbidden(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_text(repo_root / "AGENTS.md", "# agents\n")
    write_text(repo_root / ".gitignore", ".env\n")
    write_text(repo_root / "requirements.txt", "pyyaml==6.0.3\n")
    write_text(repo_root / "generated_agents" / "antigravity" / "GEMINI.md", "# gemini\n")
    write_text(repo_root / "generated_agents" / "claude" / "CLAUDE.md", "# claude\n")
    write_text(repo_root / ".agents" / "skills" / "skill-spec-drafting" / "SKILL.md", "# skill\n")
    write_text(repo_root / "repo_config" / "planning_artifact_schema.yaml", "schema_version: 1\n")
    write_text(repo_root / "docs" / "operating_system" / "governance" / "repo-governance.md", "# governance\n")
    write_text(repo_root / "docs" / "operating_system" / "runtime" / "internal.md", "omit me\n")
    write_text(repo_root / ".codex" / "rules" / "bad.rules", "forbidden\n")
    write_text(repo_root / "adapters" / "gemini" / "mapping.yaml", "forbidden: true\n")
    write_text(repo_root / "scripts" / "sync_agent_adapters.py", "print('forbidden')\n")
    manifest_path = make_manifest(repo_root)
    output_root = repo_root / "out"

    BUILD.build_starter_kit(repo_root=repo_root, manifest_path=manifest_path, output_root=output_root)

    kit_root = output_root / "project-OS-starter-kit"
    assert (kit_root / "AGENTS.md").exists()
    assert (kit_root / ".gitignore").exists()
    assert (kit_root / "GEMINI.md").exists()
    assert (kit_root / "CLAUDE.md").exists()
    assert (kit_root / ".agents" / "skills" / "skill-spec-drafting" / "SKILL.md").exists()
    assert (kit_root / "repo_config" / "planning_artifact_schema.yaml").exists()
    assert (kit_root / "requirements.txt").exists()
    assert (kit_root / "docs" / "superpowers" / "plans").is_dir()
    assert not (kit_root / "docs" / "operating_system" / "runtime").exists()
    assert not (kit_root / ".codex").exists()
    assert not (kit_root / "adapters").exists()
    assert not (kit_root / "scripts" / "sync_agent_adapters.py").exists()


def test_validate_starter_kit_reports_missing_required_and_present_forbidden(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    manifest_path = make_manifest(repo_root)
    kit_root = repo_root / "out" / "project-OS-starter-kit"
    write_text(kit_root / "AGENTS.md", "# agents\n")
    write_text(kit_root / "GEMINI.md", "# gemini\n")
    write_text(kit_root / ".codex" / "rules" / "bad.rules", "forbidden\n")
    write_text(kit_root / "docs" / "operating_system" / "runtime" / "internal.md", "should not exist\n")

    errors = VERIFY.validate_starter_kit(kit_root=kit_root, manifest_path=manifest_path)

    assert any("Missing required path" in error for error in errors)
    assert any("Forbidden path present" in error for error in errors)
    assert any("Omitted path still present" in error for error in errors)


def test_validate_starter_kit_reports_forbidden_content_reference(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    manifest_path = make_manifest(repo_root)
    kit_root = repo_root / "out" / "project-OS-starter-kit"
    write_text(kit_root / "AGENTS.md", "# agents\n")
    write_text(kit_root / "GEMINI.md", "# gemini\n")
    write_text(kit_root / "CLAUDE.md", "# claude\n")
    write_text(kit_root / ".agents" / "skills" / "skill-spec-drafting" / "SKILL.md", "# skill\n")
    write_text(kit_root / "repo_config" / "planning_artifact_schema.yaml", "schema_version: 1\n")
    write_text(kit_root / "docs" / "superpowers" / "plans" / ".gitkeep", "")
    write_text(kit_root / "README.md", "see scripts/deploy_agent_runtime.py\n")

    errors = VERIFY.validate_starter_kit(kit_root=kit_root, manifest_path=manifest_path)

    assert any("Forbidden content reference" in error for error in errors)


def test_build_starter_kit_fails_when_generated_root_instruction_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_text(repo_root / "AGENTS.md", "# agents\n")
    write_text(repo_root / ".gitignore", ".env\n")
    write_text(repo_root / "requirements.txt", "pyyaml==6.0.3\n")
    write_text(repo_root / "generated_agents" / "claude" / "CLAUDE.md", "# claude\n")
    write_text(repo_root / ".agents" / "skills" / "skill-spec-drafting" / "SKILL.md", "# skill\n")
    write_text(repo_root / "repo_config" / "planning_artifact_schema.yaml", "schema_version: 1\n")
    write_text(repo_root / "docs" / "operating_system" / "governance" / "repo-governance.md", "# governance\n")
    manifest_path = make_manifest(repo_root)

    with pytest.raises(FileNotFoundError, match="generated_agents/antigravity/GEMINI.md"):
        BUILD.build_starter_kit(
            repo_root=repo_root,
            manifest_path=manifest_path,
            output_root=repo_root / "out",
        )


def test_compare_tree_reports_stale_sibling_files(tmp_path: Path) -> None:
    generated_root = tmp_path / "generated"
    sibling_root = tmp_path / "sibling"
    write_text(generated_root / "docs" / "operating_system" / "templates" / "implementation-plan-template.md", "new\n")
    write_text(generated_root / "tests" / "test_validate_repo_contracts.py", "fresh\n")
    write_text(sibling_root / "docs" / "operating_system" / "templates" / "implementation-plan-template.md", "old\n")
    write_text(sibling_root / "tests" / "test_validate_repo_contracts.py", "fresh\n")
    write_text(sibling_root / "extra.txt", "unexpected\n")

    errors = VERIFY.compare_tree_parity(expected_root=generated_root, actual_root=sibling_root)

    assert any("Content mismatch" in error for error in errors)
    assert any("Unexpected path present" in error for error in errors)


def test_compare_tree_accepts_matching_generated_and_sibling_roots(tmp_path: Path) -> None:
    generated_root = tmp_path / "generated"
    sibling_root = tmp_path / "sibling"
    write_text(generated_root / "AGENTS.md", "# agents\n")
    write_text(generated_root / "docs" / "operating_system" / "templates" / "implementation-plan-template.md", "same\n")
    write_text(sibling_root / "AGENTS.md", "# agents\n")
    write_text(sibling_root / "docs" / "operating_system" / "templates" / "implementation-plan-template.md", "same\n")

    errors = VERIFY.compare_tree_parity(expected_root=generated_root, actual_root=sibling_root)

    assert errors == []
