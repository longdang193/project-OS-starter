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

import ast
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


def read_source(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def normalized_source(path: str) -> str:
    return " ".join(read_source(path).split())


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_completed_migration_plan_has_consistent_historical_status() -> None:
    plan = read_source("docs/superpowers/plans/2026-08-29-openspec-lifecycle-cleanup-plan.md")

    assert "status: completed" in plan
    assert "Execution was approved and completed" in plan
    assert "Plan remains `proposed`" not in plan


def test_starter_onboarding_matches_optional_intent_and_atomic_kit() -> None:
    readme = read_source("README.md")
    intent = read_source("docs/intent/README.md")
    adoption = read_source("docs/operating_system/adoption/project-adoption-migration-guide.md")
    manifest = read_source("repo_config/starter-kit-manifest.json")

    assert "standard project folders" in readme
    assert "create `docs/intent/` when durable project purpose needs more than `README.md`" in readme
    assert "Use this optional layer" in intent
    assert "generated Starter kit as the atomic adoption unit" in adoption
    assert "manual file-by-file copying" in adoption
    assert '"docs/intent"' not in manifest


def test_runtime_docs_use_profile_concept_and_keep_cli_selector_literal() -> None:
    paths = [
        "README.md",
        "docs/operating_system/procedures/personal-local-worktree-procedure.md",
        "docs/operating_system/procedures/runtime-adapter-procedure.md",
        "docs/operating_system/runtime/runtime-surfaces.md",
        "docs/operating_system/templates/agents/root-AGENTS.template.md",
    ]

    for path in paths:
        content = read_source(path)
        assert "role source" not in content, path
        assert "role provider" not in content, path

    assert "--role <profile>" in read_source("README.md")
    assert "--role <profile>" in read_source("docs/operating_system/procedures/runtime-adapter-procedure.md")


def test_runtime_adapter_procedure_preserves_lifecycle_evidence() -> None:
    procedure = normalized_source("docs/operating_system/procedures/runtime-adapter-procedure.md")

    assert "## Runtime Recovery and Proof" in procedure
    assert "Do not trust a stale port, PID, or marker file" in procedure
    assert "Tool-call success is not completion proof" in procedure
    assert "preserve the run record and lifecycle logs" in procedure
    assert "Keep logging best-effort" in procedure


def test_starter_manifest_omits_private_provider_setup() -> None:
    manifest = read_source("repo_config/starter-kit-manifest.json")

    assert "docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md" in manifest
    assert "docs/operating_system/tooling/runtime-tool-resolution.md" in manifest


def _literal_read_references(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    references: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id not in {"read", "normalized"}:
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        if isinstance(node.args[0].value, str):
            references.add(node.args[0].value)
    return references


def test_shipped_tests_read_only_kit_paths(tmp_path: Path) -> None:
    manifest = json.loads(read_source("repo_config/starter-kit-manifest.json"))
    kit_root = BUILD.build_starter_kit(
        repo_root=REPO_ROOT,
        manifest_path=REPO_ROOT / "repo_config" / "starter-kit-manifest.json",
        output_root=tmp_path,
    )
    missing: list[str] = []

    for relative_path in manifest["copyPaths"]:
        if not relative_path.startswith("tests/") or not relative_path.endswith(".py"):
            continue
        test_path = REPO_ROOT / relative_path
        for referenced_path in _literal_read_references(test_path):
            if not (kit_root / referenced_path).exists():
                missing.append(f"{relative_path}: {referenced_path}")

    assert missing == [], "Shipped tests reference paths absent from kit: " + ", ".join(missing)


def make_manifest(repo_root: Path) -> Path:
    manifest_path = repo_root / "repo_config" / "starter-kit-manifest.json"
    write_json(
        manifest_path,
        {
            "outputRoot": "project-OS-starter-kit",
            "requiredPaths": [
                ".gitignore",
                "AGENTS.md",
                "agents",
                "scripts/dcode_project.py",
                "scripts/setup_deepagents_runtime.ps1",
                "GEMINI.md",
                "CLAUDE.md",
                ".agents/skills/skill-spec-drafting/SKILL.md",
                "repo_config/planning_artifact_schema.yaml",
                "docs/operating_system/tooling/runtime-tool-resolution.md",
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
                ".deepagents",
            ],
            "copyPaths": [
                ".gitignore",
                "AGENTS.md",
                "agents",
                "scripts/dcode_project.py",
                "scripts/setup_deepagents_runtime.ps1",
                "tests/test_dcode_project.py",
                "tests/test_starter_lifecycle_contract.py",
                "tests/test_runtime_tool_resolution_contract.py",
                "generated_agents/antigravity/GEMINI.md",
                "generated_agents/claude/CLAUDE.md",
                ".agents/skills/skill-spec-drafting/SKILL.md",
                "repo_config/planning_artifact_schema.yaml",
                "requirements.txt",
                "docs/operating_system",
            ],
            "omitPaths": [
                "docs/operating_system/runtime",
                "docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md",
                "docs/operating_system/procedures/runtime-adapter-procedure.md",
                "docs/operating_system/procedures/starter-kit-procedure.md",
                "docs/operating_system/templates/agents/root-AGENTS.template.md",
            ],
            "createEmptyDirs": [
                "docs/superpowers/plans",
            ],
        },
    )
    return manifest_path


def test_canonical_manifest_ships_herdr_launcher_and_consumers() -> None:
    manifest = json.loads(
        (REPO_ROOT / "repo_config" / "starter-kit-manifest.json").read_text(encoding="utf-8")
    )

    assert "scripts/herdr_main_launcher.py" in manifest["copyPaths"]
    assert "scripts/opendesign_profile_adapter.py" in manifest["copyPaths"]
    assert "tests/test_herdr_main_launcher.py" in manifest["copyPaths"]
    assert "tests/test_opendesign_profile_adapter.py" in manifest["copyPaths"]
    assert "tests/test_skill_chief_of_staff.py" in manifest["copyPaths"]
    assert "scripts/herdr_main_launcher.py" in manifest["requiredPaths"]
    assert "scripts/opendesign_profile_adapter.py" in manifest["requiredPaths"]
    assert "docs/operating_system/runtime" in manifest["omitPaths"]
    assert "docs/operating_system/procedures/runtime-adapter-procedure.md" in manifest["omitPaths"]


def test_build_starter_kit_copies_required_and_excludes_forbidden(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_text(repo_root / "AGENTS.md", "# agents\n")
    write_text(repo_root / "README.md", "# source branding\n")
    write_text(repo_root / "agents" / "normal.toml", 'name = "normal"\n')
    write_text(repo_root / "scripts" / "dcode_project.py", "print('launcher')\n")
    write_text(repo_root / "scripts" / "setup_deepagents_runtime.ps1", "Write-Output launcher\n")
    write_text(repo_root / "tests" / "test_dcode_project.py", "# launcher test\n")
    write_text(repo_root / "tests" / "test_starter_lifecycle_contract.py", "# lifecycle test\n")
    write_text(repo_root / "tests" / "test_runtime_tool_resolution_contract.py", "# runtime test\n")
    write_text(repo_root / ".gitignore", ".env\n")
    write_text(repo_root / "requirements.txt", "pyyaml==6.0.3\n")
    write_text(repo_root / "generated_agents" / "antigravity" / "GEMINI.md", "# gemini\n")
    write_text(repo_root / "generated_agents" / "claude" / "CLAUDE.md", "# claude\n")
    write_text(repo_root / ".agents" / "skills" / "skill-spec-drafting" / "SKILL.md", "# skill\n")
    write_text(repo_root / "repo_config" / "planning_artifact_schema.yaml", "schema_version: 1\n")
    write_text(repo_root / "docs" / "operating_system" / "governance" / "repo-governance.md", "# governance\n")
    write_text(repo_root / "docs" / "operating_system" / "tooling" / "runtime-tool-resolution.md", "# runtime resolution\n")
    write_text(repo_root / "docs" / "operating_system" / "runtime" / "internal.md", "omit me\n")
    write_text(repo_root / "docs" / "operating_system" / "procedures" / "frontend-backend-integration-mcp-setup.md", "provider setup\n")
    write_text(repo_root / "docs" / "operating_system" / "procedures" / "starter-kit-procedure.md", "factory procedure\n")
    write_text(repo_root / "docs" / "operating_system" / "templates" / "agents" / "root-AGENTS.template.md", "factory template\n")
    write_text(repo_root / ".codex" / "rules" / "bad.rules", "forbidden\n")
    write_text(repo_root / "adapters" / "gemini" / "mapping.yaml", "forbidden: true\n")
    write_text(repo_root / "scripts" / "sync_agent_adapters.py", "print('forbidden')\n")
    manifest_path = make_manifest(repo_root)
    output_root = repo_root / "out"

    BUILD.build_starter_kit(repo_root=repo_root, manifest_path=manifest_path, output_root=output_root)

    kit_root = output_root / "project-OS-starter-kit"
    assert (kit_root / "AGENTS.md").exists()
    assert not (kit_root / "README.md").exists()
    assert (kit_root / "agents" / "normal.toml").exists()
    assert (kit_root / "scripts" / "dcode_project.py").exists()
    assert (kit_root / "scripts" / "setup_deepagents_runtime.ps1").exists()
    assert (kit_root / ".gitignore").exists()
    assert (kit_root / "GEMINI.md").exists()
    assert (kit_root / "CLAUDE.md").exists()
    assert (kit_root / ".agents" / "skills" / "skill-spec-drafting" / "SKILL.md").exists()
    assert (kit_root / "repo_config" / "planning_artifact_schema.yaml").exists()
    assert (kit_root / "docs" / "operating_system" / "tooling" / "runtime-tool-resolution.md").exists()
    assert (kit_root / "requirements.txt").exists()
    assert (kit_root / "docs" / "superpowers" / "plans").is_dir()
    assert not (kit_root / "docs" / "operating_system" / "runtime").exists()
    assert not (kit_root / "docs" / "operating_system" / "procedures" / "frontend-backend-integration-mcp-setup.md").exists()
    assert not (kit_root / "docs" / "operating_system" / "procedures" / "starter-kit-procedure.md").exists()
    assert not (kit_root / "docs" / "operating_system" / "templates" / "agents" / "root-AGENTS.template.md").exists()
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


def test_validate_starter_kit_rejects_malformed_profile_registry(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    manifest_path = make_manifest(repo_root)
    kit_root = repo_root / "out" / "project-OS-starter-kit"
    write_text(kit_root / "agents" / "ui.toml", 'name = "broken"\n')

    errors = VERIFY.validate_starter_kit(kit_root=kit_root, manifest_path=manifest_path)

    assert any("Invalid agent profile registry" in error for error in errors)


def test_validate_starter_kit_reports_forbidden_content_reference(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    manifest_path = make_manifest(repo_root)
    kit_root = repo_root / "out" / "project-OS-starter-kit"
    write_text(
        kit_root / "AGENTS.md",
        "\n".join(
            [
                "see scripts/build_starter_kit.py",
                "see scripts/validate_starter_kit.py",
                "see scripts/deploy_agent_runtime.py",
                "see scripts/sync_agent_adapters.py",
                "see generated_exports/project-OS-starter-kit",
            ]
        )
        + "\n",
    )
    write_text(kit_root / "GEMINI.md", "# gemini\n")
    write_text(kit_root / "CLAUDE.md", "# claude\n")
    write_text(kit_root / ".agents" / "skills" / "skill-spec-drafting" / "SKILL.md", "# skill\n")
    write_text(kit_root / "repo_config" / "planning_artifact_schema.yaml", "schema_version: 1\n")
    write_text(kit_root / "docs" / "superpowers" / "plans" / ".gitkeep", "")
    errors = VERIFY.validate_starter_kit(kit_root=kit_root, manifest_path=manifest_path)

    assert sum("Forbidden content reference" in error for error in errors) == 5


def test_build_rewrites_root_headers_and_preserves_instruction_bodies(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    generated_header = (
        "<!--\n"
        "GENERATED FILE - DO NOT EDIT\n"
        "Source: factory template\n"
        "Generated by: factory sync\n"
        "-->\n\n"
    )
    bodies = {
        "AGENTS.md": "# Agents\n\nKeep this body.\n",
        "GEMINI.md": "# Gemini\n\nKeep this body too.\n",
        "CLAUDE.md": "# Claude\n\nKeep this body as well.\n",
    }
    write_text(repo_root / "AGENTS.md", generated_header + bodies["AGENTS.md"])
    write_text(repo_root / "generated_agents" / "antigravity" / "GEMINI.md", generated_header + bodies["GEMINI.md"])
    write_text(repo_root / "generated_agents" / "claude" / "CLAUDE.md", generated_header + bodies["CLAUDE.md"])
    write_text(repo_root / "agents" / "normal.toml", 'name = "normal"\n')
    write_text(repo_root / "scripts" / "dcode_project.py", "print('launcher')\n")
    write_text(repo_root / "scripts" / "setup_deepagents_runtime.ps1", "Write-Output launcher\n")
    write_text(repo_root / "tests" / "test_dcode_project.py", "# launcher test\n")
    write_text(repo_root / "tests" / "test_starter_lifecycle_contract.py", "# lifecycle test\n")
    write_text(repo_root / "tests" / "test_runtime_tool_resolution_contract.py", "# runtime test\n")
    write_text(repo_root / ".gitignore", ".env\n")
    write_text(repo_root / "requirements.txt", "pyyaml==6.0.3\n")
    write_text(repo_root / ".agents" / "skills" / "skill-spec-drafting" / "SKILL.md", "# skill\n")
    write_text(repo_root / "repo_config" / "planning_artifact_schema.yaml", "schema_version: 1\n")
    write_text(repo_root / "docs" / "operating_system" / "governance" / "repo-governance.md", "# governance\n")
    write_text(repo_root / "docs" / "operating_system" / "tooling" / "runtime-tool-resolution.md", "# runtime resolution\n")
    manifest_path = make_manifest(repo_root)

    BUILD.build_starter_kit(repo_root=repo_root, manifest_path=manifest_path, output_root=repo_root / "out")

    expected_header = BUILD.CONSUME_ONLY_HEADER
    for file_name, body in bodies.items():
        content = (repo_root / "out" / "project-OS-starter-kit" / file_name).read_text(encoding="utf-8")
        assert content == expected_header + body
        assert "GENERATED FILE - DO NOT EDIT" not in content
        assert "scripts/sync_agent_adapters.py" not in content


@pytest.mark.parametrize(
    "forbidden_path",
    [
        ".deepagents",
    ],
)
def test_validate_starter_kit_rejects_personal_deepagents_state(
    tmp_path: Path,
    forbidden_path: str,
) -> None:
    repo_root = tmp_path / "repo"
    manifest_path = make_manifest(repo_root)
    kit_root = repo_root / "out" / "project-OS-starter-kit"
    write_text(kit_root / forbidden_path, "private\n")

    errors = VERIFY.validate_starter_kit(kit_root=kit_root, manifest_path=manifest_path)

    assert f"Forbidden path present: {forbidden_path}" in errors


def test_build_starter_kit_fails_when_generated_root_instruction_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_text(repo_root / "AGENTS.md", "# agents\n")
    write_text(repo_root / "agents" / "normal.toml", 'name = "normal"\n')
    write_text(repo_root / "scripts" / "dcode_project.py", "print('launcher')\n")
    write_text(repo_root / "scripts" / "setup_deepagents_runtime.ps1", "Write-Output launcher\n")
    write_text(repo_root / "tests" / "test_dcode_project.py", "# launcher test\n")
    write_text(repo_root / "tests" / "test_starter_lifecycle_contract.py", "# lifecycle test\n")
    write_text(repo_root / "tests" / "test_runtime_tool_resolution_contract.py", "# runtime test\n")
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
