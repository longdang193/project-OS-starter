"""
@meta
name: validate_repo_contracts
type: script
domain: docs
distribution_tier: starter_kit
responsibility:
  - Validate active repository contracts through one canonical command.
  - Orchestrate focused schema, planning, prompt, runtime, and repository checks.
inputs:
  - docs/superpowers/specs/*.md
  - docs/superpowers/plans/*.md
  - repo_config/*.json
outputs:
  - Exit status and human-readable repo contract validation results.
tags:
  - docs
  - validation
  - metadata
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
import importlib.util
import inspect
import os
from pathlib import Path
import re
import subprocess
import sys
from types import ModuleType

import json

try:
    from agent_profile_registry import load_agent_profiles
except ModuleNotFoundError:
    from scripts.agent_profile_registry import load_agent_profiles
try:
    from project_root import resolve_repo_root
except ModuleNotFoundError:
    from scripts.project_root import resolve_repo_root

STARTER_KIT_CLASSIFICATION_ENFORCEMENT = "fail"
STARTER_KIT_DISTRIBUTION_TIER = "starter_kit"


@dataclass(frozen=True)
class ValidationIssue:
    category: str
    path: str
    message: str


def relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate active repository schemas, planning contracts, generated "
            "agent surfaces, and starter-kit classification."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root. Defaults to this script's repository.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run the hook-facing subset without validator-specific pytest.",
    )
    parser.add_argument(
        "--sync-starter-kit-tier",
        action="store_true",
        help=(
            "Auto-apply distribution_tier marker on metadata-capable manifest files "
            "before classification validation"
        ),
    )
    return parser


def pytest_basetemp(default_relative: str) -> str:
    override = os.environ.get("REPO_VALIDATOR_PYTEST_BASETEMP")
    if override:
        return override
    return default_relative


IN_PROCESS_SCRIPT_NAMES = {
    "validate_planning_lifecycle.py",
    "validate_template_required_sections.py",
    "validate_learning_materials_format.py",
    "validate_prompt_metadata_schema.py",
    "validate_agent_metadata_schema.py",
    "validate_generated_header_format.py",
    "validate_agent_runtime_drift.py",
    "validate_repo_config.py",
}

@lru_cache(maxsize=64)
def _load_script_module(script_path: Path) -> ModuleType:
    module_name = f"_repo_contract_step_{script_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load script module: {script_path.as_posix()}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def _run_script_main_in_process(script_path: Path, args: list[str], cwd: Path) -> int:
    module = _load_script_module(script_path)
    if not hasattr(module, "main"):
        raise RuntimeError(f"Script has no main(): {script_path.as_posix()}")
    main_callable = getattr(module, "main")
    original_cwd = Path.cwd()
    original_argv = sys.argv[:]
    try:
        os.chdir(cwd)
        sys.argv = [script_path.as_posix(), *args]
        parameter_count = len(inspect.signature(main_callable).parameters)
        if parameter_count == 0:
            result = main_callable()
        else:
            result = main_callable(args)
        return int(result) if isinstance(result, int) else 0
    finally:
        sys.argv = original_argv
        os.chdir(original_cwd)

def _can_run_in_process(command: list[str], repo_root_path: Path) -> bool:
    if len(command) < 2:
        return False
    python_exe = Path(command[0]).name.lower()
    if python_exe not in {"python", "python.exe", Path(sys.executable).name.lower()}:
        return False
    if command[1] == "-m":
        return False
    script_path = Path(command[1]).resolve()
    scripts_root = (repo_root_path / "scripts").resolve()
    try:
        script_path.relative_to(scripts_root)
    except ValueError:
        return False
    return script_path.name in IN_PROCESS_SCRIPT_NAMES

def run_step(command: list[str], *, cwd: Path) -> int:
    rendered = " ".join(command)
    print(f"> {rendered}")
    if _can_run_in_process(command, cwd):
        script_path = Path(command[1]).resolve()
        script_args = command[2:]
        return _run_script_main_in_process(script_path, script_args, cwd)
    completed = subprocess.run(command, cwd=cwd, check=False)
    return completed.returncode


def ensure_pytest_basetemp(command: list[str], *, cwd: Path) -> None:
    try:
        index = command.index("--basetemp")
    except ValueError:
        return
    basetemp = Path(command[index + 1])
    if not basetemp.is_absolute():
        basetemp = cwd / basetemp
    basetemp.parent.mkdir(parents=True, exist_ok=True)


def build_subprocess_steps(
    *,
    root: Path,
    python_executable: str,
    fast: bool,
) -> list[list[str]]:
    project_scripts_root = root / "scripts"
    shared_scripts_root = Path(__file__).resolve().parent

    def script_path(name: str) -> Path:
        project_path = project_scripts_root / name
        return project_path if project_path.is_file() else shared_scripts_root / name

    planning_lifecycle_script = str(script_path("validate_planning_lifecycle.py"))
    template_sections_script = str(script_path("validate_template_required_sections.py"))
    learning_format_script = str(script_path("validate_learning_materials_format.py"))
    prompt_metadata_schema_script = str(script_path("validate_prompt_metadata_schema.py"))
    repo_config_script = str(script_path("validate_repo_config.py"))
    agent_metadata_schema_script = str(script_path("validate_agent_metadata_schema.py"))
    env_gitignore_contract_script = str(script_path("validate_env_gitignore_contract.py"))
    switchyard_script = root / "scripts" / "manage_switchyard_runtime.py"

    steps: list[list[str]] = [
        [python_executable, planning_lifecycle_script, "--repo-root", str(root)],
        [python_executable, template_sections_script, "--repo-root", str(root), "--require-template-selection"],
        [python_executable, learning_format_script, "--repo-root", str(root)],
        [python_executable, prompt_metadata_schema_script, "--repo-root", str(root)],
        [python_executable, agent_metadata_schema_script, "--repo-root", str(root)],
        [python_executable, env_gitignore_contract_script, "--repo-root", str(root)],
    ]
    generated_header_script = root / "scripts" / "validate_generated_header_format.py"
    if generated_header_script.is_file():
        steps.append([python_executable, str(generated_header_script)])
    agent_runtime_drift_script = root / "scripts" / "validate_agent_runtime_drift.py"
    if agent_runtime_drift_script.is_file():
        steps.append(
            [
                python_executable,
                str(agent_runtime_drift_script),
                "--all-platforms",
                "--skip-deploy-check",
            ]
        )
    steps.append([python_executable, repo_config_script, "--repo-root", str(root)])
    if switchyard_script.is_file():
        steps.append(
            [
                python_executable,
                str(switchyard_script),
                "validate",
                "--manifest",
                str(root / "repo_config" / "switchyard-routing.toml"),
            ]
        )
    if not fast:
        pytest_targets = [
            path
            for path in (
                "tests/test_manage_switchyard_runtime.py",
                "tests/test_validate_repo_config.py",
                "tests/test_validate_planning_lifecycle.py",
                "tests/test_validate_repo_contracts.py",
            )
            if (root / path).is_file()
        ]
        if pytest_targets:
            steps.append(
                [
                    python_executable,
                    "-m",
                    "pytest",
                    "--basetemp",
                    pytest_basetemp(".tmp-tests/repo-contract-pytest"),
                    *pytest_targets,
                    "-q",
                ]
            )
    return steps


def _load_starter_kit_manifest(root: Path) -> dict | None:
    path = root / "repo_config" / "starter-kit-manifest.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def validate_agent_profile_registry(root: Path) -> list[ValidationIssue]:
    try:
        load_agent_profiles(root / "agents")
    except (OSError, ValueError) as exc:
        return [ValidationIssue("agent_profile_registry", "agents", str(exc))]
    return []


def validate_ssot_contracts(root: Path) -> list[ValidationIssue]:
    paths = {
        "runtime": root / "docs" / "operating_system" / "runtime" / "runtime-surfaces.md",
        "tooling": root / "docs" / "operating_system" / "tooling" / "runtime-tool-resolution.md",
        "adoption": root / "docs" / "operating_system" / "adoption" / "project-adoption-migration-guide.md",
        "governance": root / "docs" / "operating_system" / "governance" / "repo-governance.md",
        "coordination": root / "docs" / "operating_system" / "rules" / "git-tracked-coordination-rule.md",
        "adapter": root / "docs" / "operating_system" / "procedures" / "runtime-adapter-procedure.md",
    }
    if not all(path.is_file() for path in paths.values()):
        return []

    texts = {name: path.read_text(encoding="utf-8", errors="ignore") for name, path in paths.items()}
    normalized = {name: " ".join(text.split()) for name, text in texts.items()}
    issues: list[ValidationIssue] = []

    def add_issue(name: str, message: str) -> None:
        issues.append(ValidationIssue("ssot_drift", paths[name].relative_to(root).as_posix(), message))

    def require(name: str, marker: str, message: str, *, use_normalized: bool = False) -> None:
        if marker not in (normalized[name] if use_normalized else texts[name]):
            add_issue(name, message)

    authoring_match = re.search(
        r"(?ms)^## Authoring SSOT\s*$\n(.*?)(?=^## |\Z)",
        texts["runtime"],
    )
    if authoring_match is None:
        add_issue("runtime", "requires `## Authoring SSOT`")
    elif "~/.agents/project-os/" in authoring_match.group(1):
        add_issue("runtime", "deployed `~/.agents/project-os/` paths must not be listed under authoring SSOT")
    require("runtime", "## Deployed Runtime Projections", "requires `## Deployed Runtime Projections`")
    require("runtime", "MCP `headers` values must be `${VAR}` references", "headers policy must require `${VAR}` references", use_normalized=True)
    require("runtime", "MCP `env` values may be `${VAR}` references or non-sensitive literals", "env policy must allow `${VAR}` references or non-sensitive literals", use_normalized=True)
    if "MCP `env` and `headers` values must be `${VAR}` references" in normalized["runtime"]:
        add_issue("runtime", "runtime policy must not require `${VAR}` references for `env` values")
    require("tooling", "`headers` values must be `${VAR}` references", "tool-resolution SSOT must define headers policy", use_normalized=True)
    require("tooling", "`env` values may be `${VAR}` references or non-sensitive literals", "tool-resolution SSOT must define env policy", use_normalized=True)

    adoption_markers = (
        "py -3 scripts/deploy_agent_runtime.py --target all",
        "py -3 scripts/deploy_agent_runtime.py --target all --check",
        "Build and validate generated Starter kit",
        "validate_repo_contracts.py",
    )
    adoption_positions = [texts["adoption"].find(marker) for marker in adoption_markers]
    if any(position == -1 for position in adoption_positions) or adoption_positions != sorted(adoption_positions):
        add_issue("adoption", "adoption order must deploy and validate shared runtime before Starter kit adoption")

    for marker in (
        "downstream projects own their adopted root instructions, project-local documentation, configuration, code, and tests",
        "Shared Project OS docs, scripts, and skills remain upstream-authored and user-global",
    ):
        if marker not in normalized["governance"]:
            add_issue("governance", "downstream ownership must keep project-local state separate from shared runtime assets")
            break
    require("coordination", "durable Git-tracked coordination SSOT", "coordination SSOT must be durable and Git-tracked, not static")
    require("adapter", "- `.agents/rules/`", "adapter outputs must include `.agents/rules/`")
    return issues


def validate_runtime_boundary_guidance(root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    dispatcher = root / "scripts" / "herdr_parallel_dispatch.py"
    launcher = root / "scripts" / "herdr_main_launcher.py"
    dcode = root / "scripts" / "dcode_project.py"
    contract = root / "scripts" / "herdr_attempt_contract.py"
    if not all(path.is_file() for path in (dispatcher, launcher, dcode, contract)):
        return issues

    dispatcher_text = dispatcher.read_text(encoding="utf-8", errors="ignore")
    launcher_text = launcher.read_text(encoding="utf-8", errors="ignore")
    dcode_text = dcode.read_text(encoding="utf-8", errors="ignore")
    contract_text = contract.read_text(encoding="utf-8", errors="ignore")
    if "_normalize_runtime_grant" in dispatcher_text or "_normalize_runtime_grant" in launcher_text:
        issues.append(ValidationIssue(
            "runtime_boundary", "scripts/herdr_parallel_dispatch.py",
            "production launcher and dispatcher must use public normalize_runtime_grant",
        ))
    if re.search(r"^_ADMISSION_RESULTS\s*=", dcode_text, re.MULTILINE):
        issues.append(ValidationIssue(
            "runtime_boundary", "scripts/dcode_project.py",
            "admission results must come from herdr_attempt_contract",
        ))
    if "ADMISSION_RESULTS" not in contract_text:
        issues.append(ValidationIssue(
            "runtime_boundary", "scripts/herdr_attempt_contract.py",
            "shared attempt contract must define ADMISSION_RESULTS",
        ))
    canonical = root / "docs" / "operating_system" / "runtime" / "runtime-surfaces.md"
    if canonical.is_file():
        text = canonical.read_text(encoding="utf-8", errors="ignore")
        for marker in (
            "scripts/herdr_attempt_contract.py",
            "scripts/dcode_project.py",
            "Herdr owns top-level lane/session/pane lifecycle and diagnostic observation",
        ):
            if marker not in text:
                issues.append(ValidationIssue(
                    "runtime_boundary", relative_path(canonical, root),
                    f"canonical runtime guidance must reference `{marker}`",
                ))
    return issues


def _is_metadata_capable(path: Path) -> bool:
    analysis = _analyze_metadata_file(path)
    return analysis[0]


def _analyze_metadata_file(path: Path) -> tuple[bool, bool]:
    is_metadata_capable = False
    metadata_text = ""
    if path.suffix == ".py":
        metadata_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore").splitlines()[:30]
        )
        is_metadata_capable = "@meta" in metadata_text
        if is_metadata_capable:
            meta_offset = metadata_text.index("@meta")
            for delimiter in ('"""', "'''"):
                start = metadata_text.rfind(delimiter, 0, meta_offset)
                end = metadata_text.find(delimiter, meta_offset)
                if start != -1 and end != -1:
                    metadata_text = metadata_text[start:end]
                    break
    elif path.suffix == ".md":
        text = path.read_text(encoding="utf-8", errors="ignore")
        marker_end = text.find("\n---", 3)
        is_metadata_capable = text.startswith("---\n") and marker_end != -1
        if is_metadata_capable:
            metadata_text = text[: marker_end + 4]
    has_starter_kit_tier = False
    if is_metadata_capable:
        pattern = re.compile(
            rf"^\s*(?:#\s*)?distribution_tier:\s*{re.escape(STARTER_KIT_DISTRIBUTION_TIER)}\s*$",
            re.MULTILINE,
        )
        has_starter_kit_tier = bool(pattern.search(metadata_text))
    return is_metadata_capable, has_starter_kit_tier


def _iter_files_pruned(root: Path) -> list[Path]:
    excluded_dirs = {
        ".git",
        ".worktrees",
        ".tmp-tests",
        "generated_exports",
        "generated_agents",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".deepagents",
        ".nox",
        "out",
        ".tox",
        ".venv",
        "node_modules",
    }
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        if current_path == root / ".agents":
            dirnames[:] = [name for name in dirnames if name != "rules"]
        dirnames[:] = [name for name in dirnames if name not in excluded_dirs]
        for filename in filenames:
            files.append(current_path / filename)
    return files


def _has_distribution_tier(path: Path, tier: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        rf"^\s*(?:#\s*)?distribution_tier:\s*{re.escape(tier)}\s*$",
        re.MULTILINE,
    )
    return bool(pattern.search(text))


def _has_starter_kit_distribution_tier_from_analysis(analysis: tuple[bool, bool]) -> bool:
    return analysis[1]


def _manifest_distributed_paths(root: Path, manifest: dict) -> set[str]:
    declared: list[str] = []
    copy_paths = manifest.get("copyPaths", [])
    if isinstance(copy_paths, list):
        declared.extend(item for item in copy_paths if isinstance(item, str))
    shared_paths = manifest.get("sharedPaths", {})
    if isinstance(shared_paths, dict):
        for bundle_paths in shared_paths.values():
            if isinstance(bundle_paths, list):
                declared.extend(item for item in bundle_paths if isinstance(item, str))
    owned: set[str] = set()
    for item in declared:
        rel = item.replace("\\", "/")
        target = root / rel
        if target.is_file():
            owned.add(rel)
        elif target.is_dir():
            owned.update(relative_path(file, root) for file in target.rglob("*") if file.is_file())
    return owned


def sync_starter_kit_distribution_tier(root: Path) -> int:
    manifest = _load_starter_kit_manifest(root)
    if manifest is None:
        return 0

    distributed_paths = _manifest_distributed_paths(root, manifest)

    patched = 0
    for rel in sorted(distributed_paths):
        if rel.startswith("docs/operating_system/templates/"):
            continue
        file_path = root / rel
        if not file_path.exists() or not _is_metadata_capable(file_path):
            continue
        if _has_distribution_tier(file_path, STARTER_KIT_DISTRIBUTION_TIER):
            continue

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if file_path.suffix == ".md":
            lines = text.splitlines()
            if lines and lines[0].strip() == "---":
                try:
                    end = lines.index("---", 1)
                except ValueError:
                    continue
                lines.insert(end, f"distribution_tier: {STARTER_KIT_DISTRIBUTION_TIER}")
                file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                patched += 1
        elif file_path.suffix == ".py":
            if "@meta" in text and "distribution_tier:" not in text:
                lines = text.splitlines()
                for idx, line in enumerate(lines[:30]):
                    if line.strip().startswith("#") and "@meta" in line:
                        insert_at = idx + 1
                        while insert_at < len(lines) and lines[insert_at].strip().startswith("#"):
                            if "distribution_tier:" in lines[insert_at]:
                                break
                            insert_at += 1
                        else:
                            lines.insert(insert_at, f"# distribution_tier: {STARTER_KIT_DISTRIBUTION_TIER}")
                            file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                            patched += 1
                        break
    return patched


def validate_starter_kit_classification(root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = _load_starter_kit_manifest(root)
    if manifest is None:
        return issues

    distributed_paths = _manifest_distributed_paths(root, manifest)

    for rel in sorted(distributed_paths):
        if rel.startswith("docs/operating_system/templates/"):
            continue
        file_path = root / rel
        if not file_path.exists():
            continue
        analysis = _analyze_metadata_file(file_path)
        if not analysis[0]:
            continue
        if _has_starter_kit_distribution_tier_from_analysis(analysis):
            continue
        issues.append(
            ValidationIssue(
                category="starter_kit_classification_drift",
                path=rel,
                message=(
                    "metadata-capable file is in starter-kit manifest but missing "
                    f"`distribution_tier: {STARTER_KIT_DISTRIBUTION_TIER}`"
                ),
            )
        )

    for path in _iter_files_pruned(root):
        if not path.is_file():
            continue
        analysis = _analyze_metadata_file(path)
        if not analysis[0]:
            continue
        rel = relative_path(path, root)
        if rel in distributed_paths:
            continue
        if _has_starter_kit_distribution_tier_from_analysis(analysis):
            issues.append(
                ValidationIssue(
                    category="starter_kit_classification_drift",
                    path=rel,
                    message=(
                        "file declares starter-kit distribution tier but is not included "
                        "in starter-kit distribution manifest"
                    ),
                )
            )

    return issues


def report_issues(issues: list[ValidationIssue]) -> int:
    if not issues:
        return 0
    print("Repo contract validation failed:")
    for issue in issues:
        print(f"- {issue.category}: {issue.path} - {issue.message}")
    return 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = resolve_repo_root(args.repo_root)
    except RuntimeError as exc:
        print(f"Repository contract validation blocked: {exc}")
        return 2

    profile_issues = validate_agent_profile_registry(root)
    if profile_issues:
        return report_issues(profile_issues)

    ssot_issues = validate_ssot_contracts(root)
    if ssot_issues:
        return report_issues(ssot_issues)

    boundary_issues = validate_runtime_boundary_guidance(root)
    if boundary_issues:
        return report_issues(boundary_issues)

    if args.sync_starter_kit_tier:
        patched = sync_starter_kit_distribution_tier(root)
        if patched:
            print(f"Starter-kit distribution tier sync patched {patched} file(s).")

    classification_issues = validate_starter_kit_classification(root)

    if classification_issues:
        if STARTER_KIT_CLASSIFICATION_ENFORCEMENT == "fail":
            return report_issues(classification_issues)
        print("Repo contract warning:")
        for issue in classification_issues:
            print(f"- {issue.category}: {issue.path} - {issue.message}")

    for step in build_subprocess_steps(
        root=root,
        python_executable=sys.executable,
        fast=args.fast,
    ):
        ensure_pytest_basetemp(step, cwd=root)
        status = run_step(step, cwd=root)
        if status != 0:
            return status

    print(
        "Repo contract validation passed (hook subset)."
        if args.fast
        else "Repo contract validation passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
