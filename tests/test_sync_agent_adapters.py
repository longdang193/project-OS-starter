"""
@meta
name: test_sync_agent_adapters
type: test
scope: unit
domain: docs
covers:
  - Sync adapter check flags stale generated files outside current mapping ownership
  - Sync adapter orphan detection ignores currently owned generated destinations
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC_PATH = REPO_ROOT / "scripts" / "sync_agent_adapters.py"
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


SYNC = load_module("sync_agent_adapters", SYNC_PATH)


def _mapping(source: str, destination: str, mode: str = "copy_tree") -> object:
    return SYNC.Mapping(
        source=source,
        destination=destination,
        mode=mode,
        comment_prefix="#",
        include_glob="**/*.md",
    )


def test_find_orphan_generated_surfaces_flags_legacy_unowned_files(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    orphan_file = root / "generated_agents" / "gemini" / "prompt_templates" / "legacy.md"
    orphan_file.parent.mkdir(parents=True, exist_ok=True)
    orphan_file.write_text("legacy", encoding="utf-8")

    mappings = [
        _mapping("docs/operating_system", "generated_agents/antigravity/docs/operating_system"),
        _mapping(".agents/skills", "generated_agents/antigravity/skills"),
    ]

    orphans = SYNC._find_orphan_generated_surfaces(root, mappings)

    assert orphans == [orphan_file]


def test_find_orphan_generated_surfaces_ignores_owned_generated_files(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    owned_file = root / "generated_agents" / "codex" / "docs" / "operating_system" / "rules" / "doc-contracts.rules"
    owned_file.parent.mkdir(parents=True, exist_ok=True)
    owned_file.write_text("generated", encoding="utf-8")

    mappings = [
        _mapping("docs/operating_system/rules", "generated_agents/codex/docs/operating_system/rules", mode="render_codex_rules_tree"),
        _mapping(".agents/skills", "generated_agents/codex/skills"),
    ]

    orphans = SYNC._find_orphan_generated_surfaces(root, mappings)

    assert orphans == []
