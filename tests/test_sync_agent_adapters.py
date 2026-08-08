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


def test_harness_guidance_requires_research_before_write_dispatch() -> None:
    required_phrases = {
        REPO_ROOT / "docs/operating_system/templates/agents/root-AGENTS.template.md": (
            "write-capable packet",
            "read-only research",
        ),
        REPO_ROOT / ".agents/skills/skill-executing-plans/SKILL.md": (
            "write-capable packet",
            "read-only research",
        ),
        REPO_ROOT / ".agents/skills/skill-subagent-driven-development/SKILL.md": (
            "write-capable implementer lane",
            "read-only research",
        ),
        REPO_ROOT / "docs/operating_system/rules/multi-agent-orchestration-rule.md": (
            "write-capable lane",
            "read-only research",
        ),
    }

    for path, phrases in required_phrases.items():
        content = " ".join(path.read_text(encoding="utf-8").split())
        for phrase in phrases:
            assert phrase in content, f"missing `{phrase}` in {path.relative_to(REPO_ROOT)}"


def test_harness_guidance_uses_canonical_modes_and_terminal_recovery() -> None:
    required_phrases = {
        REPO_ROOT / ".agents/skills/skill-dispatching-parallel-agents/SKILL.md": (
            "parallel_work_lanes",
            "one immutable packet",
        ),
        REPO_ROOT / ".agents/skills/skill-executing-plans/SKILL.md": (
            "run state is `planned`",
            "approved successor plan/task identity",
        ),
        REPO_ROOT / ".agents/skills/skill-systematic-debugging/SKILL.md": (
            "run state `planned`",
            "approved successor plan/task identity",
        ),
        REPO_ROOT / ".agents/skills/skill-subagent-driven-development/SKILL.md": (
            "terminal coordinated task",
            "approved successor plan/task identity",
        ),
        REPO_ROOT / "docs/operating_system/rules/multi-agent-orchestration-rule.md": (
            "run state is `planned`",
            "approved successor plan/task identity",
        ),
        REPO_ROOT / "docs/operating_system/templates/agents/root-AGENTS.template.md": (
            "run state is `planned`",
            "approved successor plan/task identity",
        ),
        REPO_ROOT / "docs/operating_system/tooling/frontend-backend-integration-tools.md": (
            "sequential_work_lanes",
        ),
    }

    for path, phrases in required_phrases.items():
        content = " ".join(path.read_text(encoding="utf-8").split())
        for phrase in phrases:
            assert phrase in content, f"missing `{phrase}` in {path.relative_to(REPO_ROOT)}"

    tooling = (REPO_ROOT / "docs/operating_system/tooling/frontend-backend-integration-tools.md").read_text(encoding="utf-8")
    assert "sequential_agents" not in tooling


def test_harness_guidance_requires_clean_workspace_baseline() -> None:
    required_phrases = {
        REPO_ROOT / "docs/operating_system/procedures/managed-execution-adapter-contract.md": (
            "workspace_baseline_invalid",
            "before lane dispatch",
            "packet_base",
            "predecessor",
            "baseline evidence",
        ),
        REPO_ROOT / "docs/operating_system/rules/multi-agent-orchestration-rule.md": (
            "workspace_baseline_invalid",
            "packet base",
            "packet_base",
            "predecessor",
        ),
        REPO_ROOT / "docs/operating_system/templates/agents/root-AGENTS.template.md": (
            "workspace_baseline_invalid",
            "before lane dispatch",
            "packet_base",
            "predecessor",
        ),
        REPO_ROOT / ".agents/skills/skill-executing-plans/SKILL.md": (
            "workspace_baseline_invalid",
            "host/environment",
            "packet_base",
            "predecessor",
        ),
    }

    for path, phrases in required_phrases.items():
        content = " ".join(path.read_text(encoding="utf-8").split())
        for phrase in phrases:
            assert phrase in content, f"missing `{phrase}` in {path.relative_to(REPO_ROOT)}"


def test_harness_guidance_handles_missing_writer_completion() -> None:
    required_phrases = {
        REPO_ROOT / "docs/operating_system/procedures/managed-execution-adapter-contract.md": (
            "writer_completion_missing",
            "harness_diagnosis",
        ),
        REPO_ROOT / "docs/operating_system/rules/multi-agent-orchestration-rule.md": (
            "writer_completion_missing",
            "harness_diagnosis",
        ),
        REPO_ROOT / "docs/operating_system/templates/agents/root-AGENTS.template.md": (
            "writer_completion_missing",
            "harness_diagnosis",
        ),
        REPO_ROOT / ".agents/skills/skill-improve-harness/SKILL.md": (
            "writer_completion_missing",
            "harness_diagnosis",
        ),
        REPO_ROOT / ".agents/skills/skill-executing-plans/SKILL.md": (
            "Git staging directive",
            "blocked or unaccepted",
        ),
    }

    for path, phrases in required_phrases.items():
        content = " ".join(path.read_text(encoding="utf-8").split())
        for phrase in phrases:
            assert phrase in content, f"missing `{phrase}` in {path.relative_to(REPO_ROOT)}"


def test_harness_guidance_scopes_child_delegation_to_packet_policy() -> None:
    required_phrases = {
        REPO_ROOT / "docs/operating_system/templates/agents/root-AGENTS.template.md": (
            "harness.delegate",
            "read_only_research",
            "must not spawn child agents",
        ),
        REPO_ROOT / "docs/operating_system/rules/multi-agent-orchestration-rule.md": (
            "harness.delegate",
            "read_only_research",
            "must not spawn child agents",
        ),
        REPO_ROOT / ".agents/skills/skill-subagent-driven-development/SKILL.md": (
            "harness.delegate",
            "read_only_research",
            "must not spawn child agents",
        ),
        REPO_ROOT / ".agents/skills/skill-dispatching-parallel-agents/SKILL.md": (
            "harness.delegate",
            "read_only_research",
            "must not spawn child agents",
        ),
    }

    for path, phrases in required_phrases.items():
        content = " ".join(path.read_text(encoding="utf-8").split())
        for phrase in phrases:
            assert phrase in content, f"missing `{phrase}` in {path.relative_to(REPO_ROOT)}"


def test_codex_provider_guidance_uses_host_owned_transport_config() -> None:
    canonical_paths = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs/operating_system/templates/agents/root-AGENTS.template.md",
        REPO_ROOT / "docs/operating_system/procedures/managed-execution-adapter-contract.md",
        REPO_ROOT / "docs/operating_system/procedures/harness-core-consumer-setup.md",
        REPO_ROOT / ".agents/skills/skill-executing-plans/SKILL.md",
        REPO_ROOT / ".agents/skills/skill-subagent-driven-development/SKILL.md",
        REPO_ROOT / ".agents/skills/skill-systematic-debugging/SKILL.md",
    ]
    required_phrases = {
        REPO_ROOT / "docs/operating_system/templates/agents/root-AGENTS.template.md": (
            "harness-providers.toml",
            "codex-harness-host preflight",
        ),
        REPO_ROOT / "docs/operating_system/procedures/managed-execution-adapter-contract.md": (
            "config init",
            "config validate",
            "codex-harness-host preflight",
            "provider_configuration_changed",
        ),
        REPO_ROOT / "docs/operating_system/procedures/harness-core-consumer-setup.md": (
            "harness-core-v0.1.14",
            "contract_version: 4",
            "packet API 5",
        ),
    }

    for path in canonical_paths:
        content = path.read_text(encoding="utf-8")
        assert "ws://127.0.0.1:4500" not in content, f"hardcoded endpoint in {path.relative_to(REPO_ROOT)}"
        assert "--server-uri" not in content, f"raw endpoint flag in {path.relative_to(REPO_ROOT)}"

    for path, phrases in required_phrases.items():
        content = " ".join(path.read_text(encoding="utf-8").split())
        for phrase in phrases:
            assert phrase in content, f"missing `{phrase}` in {path.relative_to(REPO_ROOT)}"


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
def test_resolve_platform_selection_defaults_to_all_platforms(tmp_path: Path) -> None:
    args = type("Args", (), {"all_platforms": False, "platform": []})()
    assert SYNC._resolve_platform_selection(tmp_path, args) == (set(), "all-platforms")


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
    assert "## Runtime Extension Manifest (Generated)" not in content
    assert SYNC._sync_root_instruction(root, check=True) == []

    generated.write_text("stale\n", encoding="utf-8")
    assert SYNC._sync_root_instruction(root, check=True) == [
        f"Drift detected: {generated.as_posix()}"
    ]
