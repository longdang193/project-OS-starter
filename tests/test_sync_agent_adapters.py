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
from importlib.metadata import version
import sys
from pathlib import Path

import yaml

from harness_core.compatibility import COMPATIBILITY_PROFILES, CURRENT_PACKET_API

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
    policy = yaml.safe_load((REPO_ROOT / "repo_config" / "harness.yaml").read_text(encoding="utf-8"))
    current_profile = next(profile for profile in COMPATIBILITY_PROFILES if profile["packet_api"] == CURRENT_PACKET_API)
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
            "harness-core-launcher preflight",
            "Never dispatch bare `codex-harness-host`",
            "harness-core-launcher terminalize-attempt --input",
        ),
        REPO_ROOT / "docs/operating_system/procedures/managed-execution-adapter-contract.md": (
            "harness-core-launcher upgrade --host-root",
            "harness-core-launcher preflight",
            "provider_configuration_changed",
        ),
        REPO_ROOT / "docs/operating_system/procedures/harness-core-consumer-setup.md": (
            "harness_core.request_api",
            "harness-core-launcher doctor",
            "harness-core-launcher close",
        ),
        REPO_ROOT / "README.md": (
            "harness-core-launcher controller-init",
            "harness-core-launcher decision",
            "harness-core-launcher close",
        ),
    }

    for path in canonical_paths:
        content = path.read_text(encoding="utf-8")
        assert "ws://127.0.0.1:4500" not in content, f"hardcoded endpoint in {path.relative_to(REPO_ROOT)}"
        assert "--server-uri" not in content, f"raw endpoint flag in {path.relative_to(REPO_ROOT)}"
        assert "codex-harness-host preflight" not in content, f"bare host preflight in {path.relative_to(REPO_ROOT)}"

    for path, phrases in required_phrases.items():
        content = " ".join(path.read_text(encoding="utf-8").split())
        for phrase in phrases:
            assert phrase in content, f"missing `{phrase}` in {path.relative_to(REPO_ROOT)}"

    consumer_content = (REPO_ROOT / "docs/operating_system/procedures/harness-core-consumer-setup.md").read_text(encoding="utf-8")
    for phrase in (
        f"harness-core-v{version('harness-core')}",
        f"harness_core.request_api: {policy['harness_core']['request_api']}",
        f"contract_version: {current_profile['provider_contract']}",
        f"packet API {CURRENT_PACKET_API}",
        f"host API {current_profile['dispatch_host_api']}",
    ):
        assert phrase not in consumer_content, f"copied runtime value `{phrase}` in consumer guidance"


def test_agent_profiles_and_live_run_prompt_keep_packet_boundaries() -> None:
    delegation_requirement = (
        "Do not spawn child agents unless immutable packet grants `harness.delegate` "
        "and selects `read_only_research`."
    )
    for profile in ("low", "normal", "high"):
        content = (REPO_ROOT / "agents" / f"{profile}.toml").read_text(encoding="utf-8")
        assert delegation_requirement in content, f"missing packet delegation boundary in agents/{profile}.toml"

    live_run_prompt = (REPO_ROOT / "docs/operating_system/prompt_templates/live-run-prompt.md").read_text(encoding="utf-8")
    assert "harness-core-launcher close" in live_run_prompt
    assert "external signed or legacy closure" in live_run_prompt


def test_guidance_uses_runtime_and_policy_sources_of_truth() -> None:
    root_template = (REPO_ROOT / "docs/operating_system/templates/agents/root-AGENTS.template.md").read_text(encoding="utf-8")
    assert "Historical packet API 3" not in root_template
    assert "Historical packet compatibility is owned by" in root_template

    orchestration_rule = " ".join(
        (REPO_ROOT / "docs/operating_system/rules/multi-agent-orchestration-rule.md")
        .read_text(encoding="utf-8")
        .split()
    )
    assert "finalizes controller-authorized `waive` with reason" in orchestration_rule

    consumer_setup = (REPO_ROOT / "docs/operating_system/procedures/harness-core-consumer-setup.md").read_text(encoding="utf-8")
    assert "finalize controller-authorized waiver with reason" in consumer_setup

    publication_rule = (REPO_ROOT / "docs/operating_system/rules/publication-boundary-rule.md").read_text(encoding="utf-8")
    assert "Repository publication configuration owns exact" in publication_rule
    assert "- `.agents/`" not in publication_rule

    docs_template = (REPO_ROOT / "docs/operating_system/templates/agents/docs-AGENTS.template.md").read_text(encoding="utf-8")
    assert "`repo_config/` owns machine-enforced policy" in docs_template


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
