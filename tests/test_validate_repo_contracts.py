"""
@meta
name: test_validate_repo_contracts
type: test
scope: unit
domain: docs
covers:
  - Repo contract validator orchestration and fast-mode success on the current starter repo
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_repo_contracts.py"
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


VALIDATOR = load_module("validate_repo_contracts", VALIDATOR_PATH)
ENV_GITIGNORE_VALIDATOR = load_module(
    "validate_env_gitignore_contract",
    REPO_ROOT / "scripts" / "validate_env_gitignore_contract.py",
)


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_validator_fast_mode_passes_for_current_repo() -> None:
    result = run_validator("--fast")

    assert result.returncode == 0
    assert "repo contract validation passed" in result.stdout.lower()


def test_ssot_contracts_pass_for_current_repo() -> None:
    assert VALIDATOR.validate_ssot_contracts(REPO_ROOT) == []


def test_ssot_contracts_reject_runtime_policy_drift(tmp_path: Path) -> None:
    shutil.copytree(REPO_ROOT / "docs" / "operating_system", tmp_path / "docs" / "operating_system")
    runtime_path = tmp_path / "docs" / "operating_system" / "runtime" / "runtime-surfaces.md"
    runtime_path.write_text(
        runtime_path.read_text(encoding="utf-8").replace(
            "MCP `env` values may be `${VAR}` references or\n  non-sensitive literals.",
            "MCP `env` and `headers` values must be `${VAR}` references.",
        ),
        encoding="utf-8",
    )

    issues = VALIDATOR.validate_ssot_contracts(tmp_path)

    assert any(issue.path.endswith("runtime-surfaces.md") for issue in issues)
    assert any("env policy" in issue.message for issue in issues)


def test_main_propagates_subprocess_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        VALIDATOR,
        "build_subprocess_steps",
        lambda *, root, python_executable, fast: [["python", "fake-step"]],
    )
    monkeypatch.setattr(VALIDATOR, "run_step", lambda command, cwd: 1)

    status = VALIDATOR.main(["--repo-root", str(REPO_ROOT), "--fast"])

    assert status == 1


def test_main_creates_pytest_basetemp_parent(tmp_path: Path, monkeypatch) -> None:
    write_text(
        tmp_path / "agents" / "normal.toml",
        """name = \"normal\"
model_provider = \"openai\"
model = \"combo-normal\"
description = \"normal\"
developer_instructions = \"normal\"
""",
    )
    basetemp = tmp_path / ".tmp-tests" / "repo-contract-pytest"
    monkeypatch.setattr(
        VALIDATOR,
        "build_subprocess_steps",
        lambda *, root, python_executable, fast: [
            [python_executable, "-m", "pytest", "--basetemp", str(basetemp)]
        ],
    )
    monkeypatch.setattr(VALIDATOR, "run_step", lambda command, cwd: 0)

    assert not basetemp.parent.exists()
    assert VALIDATOR.main(["--repo-root", str(tmp_path), "--fast"]) == 0
    assert basetemp.parent.is_dir()


def test_profile_registry_validation_rejects_malformed_profile(tmp_path: Path) -> None:
    write_text(tmp_path / "agents" / "ui.toml", 'name = "ui"\n')

    issues = VALIDATOR.validate_agent_profile_registry(tmp_path)

    assert len(issues) == 1
    assert issues[0].category == "agent_profile_registry"
    assert "must be a non-empty string" in issues[0].message


def test_build_subprocess_steps_excludes_retired_metadata_validators() -> None:
    steps = VALIDATOR.build_subprocess_steps(
        root=REPO_ROOT,
        python_executable="python",
        fast=True,
    )

    rendered = [" ".join(step) for step in steps]

    assert any("validate_template_required_sections.py" in step for step in rendered)
    assert any(
        "validate_template_required_sections.py" in step
        and "--repo-root" in step
        and "--require-template-selection" in step
        for step in rendered
    )
    assert any("validate_prompt_metadata_schema.py" in step for step in rendered)
    assert any("validate_env_gitignore_contract.py" in step for step in rendered)
    assert any("validate_repo_config.py" in step for step in rendered)
    assert any(
        "manage_switchyard_runtime.py validate" in step
        and "repo_config/switchyard-routing.toml" in step.replace("\\", "/")
        for step in rendered
    )
    assert not any("validate_adoption_shape.py" in step for step in rendered)
    assert not any("validate_python_meta_headers.py" in step for step in rendered)


def test_build_subprocess_steps_includes_manager_regressions() -> None:
    steps = VALIDATOR.build_subprocess_steps(
        root=REPO_ROOT,
        python_executable="python",
        fast=False,
    )

    rendered = [" ".join(step) for step in steps]

    assert any("tests/test_manage_switchyard_runtime.py" in step for step in rendered)


def test_build_subprocess_steps_checks_all_adapter_platforms() -> None:
    steps = VALIDATOR.build_subprocess_steps(
        root=REPO_ROOT,
        python_executable="python",
        fast=True,
    )

    assert any(
        "validate_agent_runtime_drift.py --all-platforms --skip-deploy-check" in " ".join(step)
        for step in steps
    )


def test_build_subprocess_steps_skips_factory_only_validators_when_absent(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in (
        "validate_planning_lifecycle.py",
        "validate_template_required_sections.py",
        "validate_learning_materials_format.py",
        "validate_prompt_metadata_schema.py",
        "validate_agent_metadata_schema.py",
        "validate_env_gitignore_contract.py",
        "validate_repo_config.py",
    ):
        write_text(scripts / name, "")

    steps = VALIDATOR.build_subprocess_steps(
        root=tmp_path,
        python_executable="python",
        fast=True,
    )

    rendered = [" ".join(step) for step in steps]
    assert not any("validate_generated_header_format.py" in step for step in rendered)
    assert not any("validate_agent_runtime_drift.py" in step for step in rendered)


def test_starter_kit_classification_constants_match_contract() -> None:
    assert VALIDATOR.STARTER_KIT_DISTRIBUTION_TIER == "starter_kit"
    assert VALIDATOR.STARTER_KIT_CLASSIFICATION_ENFORCEMENT == "fail"


def test_validate_env_gitignore_contract_passes_with_required_entries(tmp_path: Path) -> None:
    write_text(
        tmp_path / ".gitignore",
        """.env
.env.*
!.env.example
*.private.*
*.local.*
""",
    )
    write_text(tmp_path / ".env.example", "API_KEY=placeholder\n")

    issues = ENV_GITIGNORE_VALIDATOR.validate_env_gitignore_contract(tmp_path)

    assert issues == []
def test_validate_env_gitignore_contract_reports_missing_entries(tmp_path: Path) -> None:
    write_text(tmp_path / ".gitignore", "node_modules/\n")
    write_text(tmp_path / ".env.example", "API_KEY=placeholder\n")

    issues = ENV_GITIGNORE_VALIDATOR.validate_env_gitignore_contract(tmp_path)

    assert "missing required .gitignore entry: .env" in issues
    assert "missing required .gitignore entry: .env.*" in issues
    assert "missing required .gitignore entry: *.private.*" in issues
    assert "missing required .gitignore entry: *.local.*" in issues
    assert "missing required .gitignore entry when .env.example exists: !.env.example" in issues


def test_starter_kit_classification_detects_missing_distribution_tier(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        """{
  "copyPaths": ["scripts"]
}
""",
    )
    write_text(
        tmp_path / "scripts" / "demo.py",
        """\"\"\"
@meta
name: demo
type: script
\"\"\"
""",
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert any("missing `distribution_tier: starter_kit`" in issue.message for issue in issues)


def test_runtime_dependency_boundaries_reject_forbidden_import(tmp_path: Path) -> None:
    write_text(tmp_path / "scripts" / "dcode_project.py", "from scripts.herdr_main_launcher import launch\n")

    issues = VALIDATOR.validate_runtime_dependency_boundaries(tmp_path)

    assert len(issues) == 1
    assert "forbidden runtime dependency" in issues[0].message


def test_runtime_dependency_boundaries_ignore_prose_and_allow_shared_modules(tmp_path: Path) -> None:
    write_text(
        tmp_path / "scripts" / "dcode_project.py",
        "from scripts.project_os_runtime.attempt import normalize_attempt\n"
        "# scripts.herdr_main_launcher is prose, not an import\n",
    )

    assert VALIDATOR.validate_runtime_dependency_boundaries(tmp_path) == []


def test_runtime_dependency_boundaries_normalize_import_spellings(tmp_path: Path) -> None:
    for index, source in enumerate(
        (
            "import herdr_main_launcher\n",
            "import scripts.herdr_main_launcher\n",
            "from scripts import herdr_main_launcher\n",
            "from . import herdr_main_launcher\n",
        )
    ):
        root = tmp_path / str(index)
        write_text(root / "scripts" / "dcode_project.py", source)

        issues = VALIDATOR.validate_runtime_dependency_boundaries(root)

        assert len(issues) == 1
        assert "scripts.herdr_main_launcher" in issues[0].message


def test_runtime_dependency_boundaries_reject_pure_core_process_imports(tmp_path: Path) -> None:
    for module in ("attempt", "lane", "admission", "capabilities"):
        write_text(tmp_path / "scripts" / "project_os_runtime" / f"{module}.py", "import subprocess\n")

    issues = VALIDATOR.validate_runtime_dependency_boundaries(tmp_path)

    assert len(issues) == 4
    assert all("subprocess" in issue.message for issue in issues)


def test_runtime_boundary_guidance_accepts_shared_contract_sources(tmp_path: Path) -> None:
    for relative in (
        "scripts/herdr_parallel_dispatch.py",
        "scripts/herdr_main_launcher.py",
        "scripts/dcode_project.py",
        "scripts/herdr_attempt_contract.py",
    ):
        write_text(tmp_path / relative, "ADMISSION_RESULTS\nnormalize_runtime_grant\n")
    write_text(
        tmp_path / "docs" / "operating_system" / "runtime" / "runtime-surfaces.md",
        "scripts/herdr_attempt_contract.py scripts/dcode_project.py scripts/project_os_runtime/ Herdr owns target selection, transport, and diagnostic observation",
    )

    assert VALIDATOR.validate_runtime_boundary_guidance(tmp_path) == []


def test_runtime_boundary_guidance_rejects_private_launcher_policy(tmp_path: Path) -> None:
    for relative in (
        "scripts/herdr_parallel_dispatch.py",
        "scripts/herdr_main_launcher.py",
        "scripts/dcode_project.py",
        "scripts/herdr_attempt_contract.py",
    ):
        write_text(tmp_path / relative, "ADMISSION_RESULTS\nnormalize_runtime_grant\n")
    write_text(tmp_path / "scripts" / "herdr_main_launcher.py", "_normalize_runtime_grant\n")
    write_text(
        tmp_path / "docs" / "operating_system" / "runtime" / "runtime-surfaces.md",
        "scripts/herdr_attempt_contract.py scripts/dcode_project.py scripts/project_os_runtime/ Herdr owns target selection, transport, and diagnostic observation",
    )

    issues = VALIDATOR.validate_runtime_boundary_guidance(tmp_path)

    assert any("public normalize_runtime_grant" in issue.message for issue in issues)


def test_parallel_dispatch_spec_requires_runtime_boundary_amendment(tmp_path: Path) -> None:
    spec_path = tmp_path / "docs" / "superpowers" / "specs" / "2026-09-14-parallel-deepagents-dispatch-spec.md"
    write_text(spec_path, "## Runtime Boundary Amendment\n\nCONTINUATION_ELIGIBLE\n")

    assert VALIDATOR.validate_parallel_dispatch_spec(tmp_path) == []


def test_parallel_dispatch_spec_rejects_missing_runtime_boundary_amendment(tmp_path: Path) -> None:
    spec_path = tmp_path / "docs" / "superpowers" / "specs" / "2026-09-14-parallel-deepagents-dispatch-spec.md"
    write_text(spec_path, "# Parallel DeepAgents Dispatch\n")

    issues = VALIDATOR.validate_parallel_dispatch_spec(tmp_path)

    assert any("Runtime Boundary Amendment" in issue.message for issue in issues)


def test_starter_kit_classification_detects_out_of_manifest_tier(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        """{
  "copyPaths": ["docs"]
}
""",
    )
    write_text(
        tmp_path / "scripts" / "demo.py",
        """\"\"\"
@meta
name: demo
type: script
distribution_tier: starter_kit
\"\"\"
""",
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert any("not included in starter-kit distribution manifest" in issue.message for issue in issues)


def test_starter_kit_classification_ignores_tier_literals_outside_metadata(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        '{"copyPaths": ["docs"]}\n',
    )
    write_text(
        tmp_path / "tests" / "test_fixture.py",
        '''"""
@meta
name: fixture
type: test
"""

TIER_LITERAL = """
distribution_tier: starter_kit
"""
''',
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert issues == []


def test_starter_kit_classification_ignores_tmp_tests_tree(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        """{
  "copyPaths": ["docs"]
}
""",
    )
    write_text(
        tmp_path / ".tmp-tests" / "scratch.py",
        """\"\"\"
@meta
name: scratch
type: script
distribution_tier: starter_kit
\"\"\"
""",
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert issues == []


def test_starter_kit_classification_prunes_dependency_trees_but_keeps_manifest_paths(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        '{"copyPaths": ["node_modules/owned.py"]}\n',
    )
    write_text(
        tmp_path / "node_modules" / "owned.py",
        '"""\n@meta\nname: owned\ntype: script\n"""\n',
    )
    write_text(
        tmp_path / "node_modules" / "ignored.py",
        '"""\n@meta\nname: ignored\ntype: script\ndistribution_tier: starter_kit\n"""\n',
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert [issue.path for issue in issues] == ["node_modules/owned.py"]


def test_sync_starter_kit_distribution_tier_patches_manifest_files(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        '{"copyPaths": ["scripts"]}\n',
    )
    path = tmp_path / "scripts" / "demo.py"
    write_text(
        path,
        "# @meta\n# name: demo\n# type: script\n",
    )

    assert VALIDATOR.sync_starter_kit_distribution_tier(tmp_path) == 1
    assert "distribution_tier: starter_kit" in path.read_text(encoding="utf-8")


def test_starter_kit_classification_ignores_generated_local_rule_mirror(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        '{"copyPaths": ["docs/operating_system/rules"]}\n',
    )
    write_text(
        tmp_path / "docs" / "operating_system" / "rules" / "sample-rule.md",
        "---\ndistribution_tier: starter_kit\n---\n# Rule\n",
    )
    write_text(
        tmp_path / ".agents" / "rules" / "sample-rule.md",
        "---\ndistribution_tier: starter_kit\n---\n# Generated Rule\n",
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert issues == []
