"""
@meta
name: test_sync_agent_adapters
type: test
scope: unit
domain: docs
covers:
  - Sync adapter check flags stale generated files outside current mapping ownership
  - Sync adapter orphan detection ignores currently owned generated destinations
  - Sync adapter no-mapping behavior is role- and selector-aware
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
import tomllib

import pytest


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


def _write_yaml(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_find_orphan_generated_surfaces_flags_legacy_unowned_files(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    orphan_file = root / "generated_agents" / "gemini" / "prompt_templates" / "legacy.md"
    orphan_file.parent.mkdir(parents=True, exist_ok=True)
    orphan_file.write_text("legacy", encoding="utf-8")

    mappings = [
        _mapping("AGENTS.md", "generated_agents/antigravity/GEMINI.md", mode="copy_file"),
        _mapping("docs/operating_system/rules/global-baseline-contract-rule.md", "generated_agents/antigravity/rules/global-baseline-contract-rule.md", mode="copy_file"),
        _mapping(".agents/skills", "generated_agents/antigravity/skills"),
    ]

    orphans = SYNC._find_orphan_generated_surfaces(root, mappings)

    assert orphans == [orphan_file]


def test_find_orphan_generated_surfaces_ignores_owned_generated_files(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    owned_file = root / "generated_agents" / "codex" / "rules" / "global-baseline-contract.rules"
    owned_file.parent.mkdir(parents=True, exist_ok=True)
    owned_file.write_text("generated", encoding="utf-8")

    mappings = [
        _mapping("AGENTS.md", "generated_agents/codex/AGENTS.md", mode="copy_file"),
        _mapping("docs/operating_system/rules/global-baseline-contract-rule.md", "generated_agents/codex/rules/global-baseline-contract.rules", mode="copy_file"),
        _mapping(".agents/skills", "generated_agents/codex/skills"),
    ]

    orphans = SYNC._find_orphan_generated_surfaces(root, mappings)

    assert orphans == []


def test_find_orphan_generated_surfaces_flags_legacy_docs_tree_after_scope_reduction(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    legacy_file = root / "generated_agents" / "claude" / "docs" / "operating_system" / "prompt_templates" / "legacy.md"
    legacy_file.parent.mkdir(parents=True, exist_ok=True)
    legacy_file.write_text("generated", encoding="utf-8")

    mappings = [
        _mapping("AGENTS.md", "generated_agents/claude/CLAUDE.md", mode="copy_file"),
        _mapping("docs/operating_system/rules/global-baseline-contract-rule.md", "generated_agents/claude/rules/global-baseline-contract-rule.md", mode="copy_file"),
        _mapping(".agents/skills", "generated_agents/claude/skills"),
    ]

    orphans = SYNC._find_orphan_generated_surfaces(root, mappings)

    assert orphans == [legacy_file]



def test_sync_tree_copies_nested_skill_support_files(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    src_root = root / ".agents" / "skills"
    skill_dir = src_root / "skill-sample"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("---\nname: skill-sample\ndescription: Use when sample applies\n---\n", encoding="utf-8")
    (skill_dir / "task-reviewer-prompt.md").write_text("prompt body\n", encoding="utf-8")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "helper.sh").write_text("#!/usr/bin/env bash\necho helper\n", encoding="utf-8")

    mapping = SYNC.Mapping(
        source=".agents/skills",
        destination="generated_agents/codex/skills",
        mode="copy_tree",
        comment_prefix="#",
        include_glob="**/*",
    )

    issues = SYNC._sync_tree(root, mapping, check=False)

    assert issues == []
    assert (root / "generated_agents" / "codex" / "skills" / "skill-sample" / "SKILL.md").exists()
    assert (root / "generated_agents" / "codex" / "skills" / "skill-sample" / "task-reviewer-prompt.md").exists()
    assert (root / "generated_agents" / "codex" / "skills" / "skill-sample" / "scripts" / "helper.sh").exists()


def _write_agent_role(path: Path, *, name: str = "normal", extra: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'''name = "{name}"
model_provider = "9router"
model = "combo-{name}"
description = "Role description"
developer_instructions = "Return ROLE_OK."
{extra}''',
        encoding="utf-8",
    )


def test_sync_codex_agents_tree_generates_parseable_toml_and_removes_stale_output(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    source = root / "agents" / "normal.toml"
    _write_agent_role(source)
    mapping = SYNC.Mapping(
        source="agents",
        destination="generated_agents/codex/agents",
        mode="render_codex_agents_tree",
        comment_prefix="#",
        include_glob="*.toml",
    )

    stale = root / "generated_agents" / "codex" / "agents" / "stale.toml"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")

    assert SYNC._sync_codex_agents_tree(root, mapping, check=False) == []
    rendered = (root / "generated_agents" / "codex" / "agents" / "normal.toml").read_text(encoding="utf-8")
    assert "Source: agents/normal.toml" in rendered
    assert rendered.startswith("# GENERATED FILE - DO NOT EDIT\n")
    assert tomllib.loads(rendered) == {
        "name": "normal",
        "model_provider": "9router",
        "model": "combo-normal",
        "description": "Role description",
        "developer_instructions": "Return ROLE_OK.",
    }
    assert not stale.exists()
    assert SYNC._sync_codex_agents_tree(root, mapping, check=True) == []


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("normal.toml", 'name = "normal"\nmodel_provider = "9router"\nmodel = "combo-normal"\ndescription = "x"\n', "developer_instructions"),
        ("normal.toml", 'name = "wrong"\nmodel_provider = "9router"\nmodel = "combo-normal"\ndescription = "x"\ndeveloper_instructions = "x"\n', "filename must match"),
        ("normal.toml", 'name = "normal"\nmodel_provider = "9router"\ndescription = "x"\ndeveloper_instructions = "x"\n', "`model`"),
        ("normal.toml", 'name = "normal"\nmodel_provider = "9router"\nmodel = "x"\ndescription = "x"\ndeveloper_instructions = "x"\nbase_url = "http://127.0.0.1"\n', "runtime-owned keys"),
        ("normal.toml", 'name = "normal"\nmodel_provider = "9router"\nmodel = "combo-normal"\ndescription = "x"\ndeveloper_instructions = "x"\nextra = "x"\n', "unsupported keys"),
    ],
)
def test_load_agent_roles_rejects_invalid_or_runtime_owned_source(
    tmp_path: Path,
    filename: str,
    content: str,
    message: str,
) -> None:
    source = tmp_path / "agents" / filename
    source.parent.mkdir(parents=True)
    source.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        SYNC._load_agent_roles(source.parent, "*.toml")


def test_run_parses_shared_role_source_once_for_codex(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    _write_agent_role(root / "agents" / "normal.toml")
    template = root / "docs" / "operating_system" / "templates" / "agents" / "root-AGENTS.template.md"
    template.parent.mkdir(parents=True)
    template.write_text("# Root\n", encoding="utf-8")
    _write_yaml(
        root / "adapters" / "codex" / "mapping.yaml",
        """platform: codex
mappings:
  - source: agents
    destination: generated_agents/codex/agents
    mode: render_codex_agents_tree
    include_glob: '*.toml'
    comment_prefix: '#'
""",
    )
    calls = 0
    original = SYNC._load_agent_roles

    def count_load(src_root: Path, pattern: str):
        nonlocal calls
        calls += 1
        return original(src_root, pattern)

    monkeypatch.setattr(SYNC, "repo_root", lambda: root)
    monkeypatch.setattr(
        SYNC,
        "parse_args",
        lambda: type("Args", (), {"check": False, "adapters_root": "adapters", "platform": [], "all_platforms": True})(),
    )
    monkeypatch.setattr(SYNC, "_load_agent_roles", count_load)

    assert SYNC.run() == 0
    assert calls == 1
def test_resolve_platform_selection_defaults_to_codex(tmp_path: Path) -> None:
    args = type("Args", (), {"all_platforms": False, "platform": []})()
    assert SYNC._resolve_platform_selection(tmp_path, args) == ({"codex"}, "default")


def test_resolve_platform_selection_respects_explicit_platforms(tmp_path: Path) -> None:
    args = type("Args", (), {"all_platforms": False, "platform": ["claude"]})()
    assert SYNC._resolve_platform_selection(tmp_path, args) == ({"claude"}, "explicit")


def test_resolve_platform_selection_all_platforms(tmp_path: Path) -> None:
    args = type("Args", (), {"all_platforms": True, "platform": []})()
    assert SYNC._resolve_platform_selection(tmp_path, args) == (set(), "all-platforms")


def test_sync_root_instruction_generates_and_checks_agents(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    template = root / "docs" / "operating_system" / "templates" / "agents" / "root-AGENTS.template.md"
    template.parent.mkdir(parents=True)
    template.write_text("# Root Rules\n", encoding="utf-8")

    assert SYNC._sync_root_instruction(root, check=False) == []
    generated = root / "AGENTS.md"
    content = generated.read_text(encoding="utf-8")
    assert "Source: docs/operating_system/templates/agents/root-AGENTS.template.md" in content
    assert "RUNTIME_MANIFEST" not in content
    assert SYNC._sync_root_instruction(root, check=True) == []

    generated.write_text("stale\n", encoding="utf-8")
    assert SYNC._sync_root_instruction(root, check=True) == [
        f"Drift detected: {generated.as_posix()}"
    ]
