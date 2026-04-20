"""
@meta
name: validate_adoption_shape
type: script
domain: docs
responsibility:
  - Validate the explicit starter adoption mode and architecture-doc shape.
  - Catch mixed legacy/managed feature metadata states and method-layer pseudo-features.
inputs:
  - repo_config/adoption-mode.yaml
  - docs/features/
  - docs/stages/
  - docs/generated/
  - docs/superpowers/specs/*.md
  - docs/superpowers/plans/*.md
outputs:
  - Exit status and human-readable adoption-shape validation results.
tags:
  - docs
  - validation
  - adoption
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


ALLOWED_MODES = {
    "starter_method_only",
    "managed_architecture_metadata",
    "legacy_compatibility",
}
METHOD_FEATURE_IDS = {"repo-operating-system"}
METHOD_FEATURE_PREFIXES = (
    "repo-",
    "agent-",
    "adapter-",
    "publication-",
    "docs-governance",
)
GENERATED_INDEX_NAMES = {
    "architecture_dag.yaml",
    "capability_lineage.yaml",
    "feature_capabilities_index.yaml",
    "feature_dependency_graph.yaml",
    "feature_overview.md",
    "features_by_status.yaml",
    "features_index.yaml",
}
METADATA_SCAN_SUFFIXES = {".py", ".yaml", ".yml", ".sql", ".md"}
METADATA_SCAN_SKIP_DIRS = {
    ".git",
    ".venv",
    ".agents",
    "venv",
    "node_modules",
    "docs",
    "agent-core",
    "repo_config",
    "scripts",
    "tests",
    "tools",
}
FEATURE_METADATA_PATTERNS = (
    "@capability",
    "@proves",
    "explains.features",
    "capability_id:",
    "capability_ids:",
)


@dataclass(frozen=True)
class Finding:
    level: str
    path: str
    message: str
    fix: str


@dataclass(frozen=True)
class AdoptionConfig:
    mode: str
    managed_architecture_metadata: bool
    legacy_feature_contracts: bool
    architecture_generator: str
    payload: dict[str, Any]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate starter adoption mode and architecture-doc shape."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to validate. Defaults to this script's repository.",
    )
    parser.add_argument(
        "--adoption-mode",
        default="repo_config/adoption-mode.yaml",
        help="Path to adoption-mode.yaml relative to repo root.",
    )
    return parser


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def add_error(findings: list[Finding], path: str, message: str, fix: str) -> None:
    findings.append(Finding("ERROR", path, message, fix))


def add_warning(findings: list[Finding], path: str, message: str, fix: str) -> None:
    findings.append(Finding("WARN", path, message, fix))


def parse_adoption_config(path: Path, findings: list[Finding], root: Path) -> AdoptionConfig | None:
    if not path.exists():
        add_error(
            findings,
            relpath(path, root),
            "Missing adoption mode source file.",
            "Create repo_config/adoption-mode.yaml and choose an adoption_mode.",
        )
        return None

    try:
        payload = load_yaml(path)
    except yaml.YAMLError as exc:
        add_error(
            findings,
            relpath(path, root),
            f"Could not parse adoption mode YAML: {exc}",
            "Fix YAML syntax.",
        )
        return None

    if not isinstance(payload, dict):
        add_error(
            findings,
            relpath(path, root),
            "Adoption mode file must be a top-level mapping.",
            "Use keys such as adoption_mode, managed_architecture_metadata, and legacy_feature_contracts.",
        )
        return None

    mode = payload.get("adoption_mode")
    managed = payload.get("managed_architecture_metadata")
    legacy = payload.get("legacy_feature_contracts")
    generator = payload.get("architecture_generator", "none")

    if mode not in ALLOWED_MODES:
        add_error(
            findings,
            relpath(path, root),
            f"Invalid adoption_mode: {mode!r}.",
            "Use one of: " + ", ".join(sorted(ALLOWED_MODES)) + ".",
        )
        return None

    if not isinstance(managed, bool):
        add_error(
            findings,
            relpath(path, root),
            "managed_architecture_metadata must be a boolean.",
            "Set managed_architecture_metadata to true or false.",
        )
        return None

    if not isinstance(legacy, bool):
        add_error(
            findings,
            relpath(path, root),
            "legacy_feature_contracts must be a boolean.",
            "Set legacy_feature_contracts to true or false.",
        )
        return None

    if not isinstance(generator, str):
        add_error(
            findings,
            relpath(path, root),
            "architecture_generator must be a string path or `none`.",
            "Set architecture_generator to none or a generator script path.",
        )
        return None

    config = AdoptionConfig(mode, managed, legacy, generator, payload)
    validate_mode_consistency(config, relpath(path, root), findings)
    return config


def validate_mode_consistency(config: AdoptionConfig, path: str, findings: list[Finding]) -> None:
    expected = {
        "starter_method_only": (False, False),
        "managed_architecture_metadata": (True, False),
        "legacy_compatibility": (False, True),
    }[config.mode]
    if (config.managed_architecture_metadata, config.legacy_feature_contracts) != expected:
        add_error(
            findings,
            path,
            "Adoption mode booleans do not match adoption_mode.",
            (
                f"For {config.mode}, set managed_architecture_metadata={str(expected[0]).lower()} "
                f"and legacy_feature_contracts={str(expected[1]).lower()}."
            ),
        )


def feature_roots(root: Path) -> list[Path]:
    features_root = root / "docs" / "features"
    if not features_root.exists():
        return []
    return sorted(path for path in features_root.iterdir() if path.is_dir())


def flat_feature_files(root: Path) -> list[Path]:
    features_root = root / "docs" / "features"
    if not features_root.exists():
        return []
    return sorted(path for path in features_root.glob("*.yaml") if path.is_file())


def managed_feature_contracts(root: Path) -> list[Path]:
    contracts: list[Path] = []
    for folder in feature_roots(root):
        contract = folder / f"{folder.name}.yaml"
        if contract.exists():
            contracts.append(contract)
    return sorted(contracts)


def feature_source_files(root: Path) -> list[Path]:
    return sorted((root / "docs" / "features").glob("*/feature.source.yaml"))


def generated_architecture_files(root: Path) -> list[Path]:
    generated_root = root / "docs" / "generated"
    if not generated_root.exists():
        return []
    return sorted(
        path for path in generated_root.iterdir() if path.is_file() and path.name in GENERATED_INDEX_NAMES
    )


def is_empty_generated_scaffold(path: Path) -> bool:
    try:
        payload = load_yaml(path)
    except yaml.YAMLError:
        return False
    if path.name == "architecture_dag.yaml" and payload == {"nodes": [], "edges": []}:
        return True
    if path.name == "capability_lineage.yaml" and payload == {"features": {}}:
        return True
    return False


def is_empty_generated_scaffold(path: Path) -> bool:
    try:
        payload = load_yaml(path)
    except yaml.YAMLError:
        return False
    if path.name == "architecture_dag.yaml" and payload == {"nodes": [], "edges": []}:
        return True
    if path.name == "capability_lineage.yaml" and payload == {"features": {}}:
        return True
    return False


def feature_ids_from_shape(root: Path) -> set[str]:
    ids = {path.stem for path in flat_feature_files(root)}
    ids.update(path.name for path in feature_roots(root))
    return ids


def validate_method_feature_ids(root: Path, findings: list[Finding]) -> None:
    for feature_id in sorted(feature_ids_from_shape(root)):
        is_method_id = feature_id in METHOD_FEATURE_IDS or feature_id.startswith(METHOD_FEATURE_PREFIXES)
        if not is_method_id:
            continue
        candidate_paths = [root / "docs" / "features" / f"{feature_id}.yaml", root / "docs" / "features" / feature_id]
        existing_path = next((path for path in candidate_paths if path.exists()), candidate_paths[0])
        add_error(
            findings,
            relpath(existing_path, root),
            f"Method-layer pseudo-feature `{feature_id}` is not allowed.",
            "Move repo-method content to docs/operating_system/ or operating-system specs/plans with targets.",
        )


def validate_feature_dependencies(root: Path, findings: list[Finding]) -> None:
    feature_ids = feature_ids_from_shape(root)
    for path in flat_feature_files(root) + managed_feature_contracts(root) + feature_source_files(root):
        try:
            payload = load_yaml(path)
        except yaml.YAMLError as exc:
            add_error(findings, relpath(path, root), f"Could not parse feature YAML: {exc}", "Fix YAML syntax.")
            continue
        if not isinstance(payload, dict):
            continue
        body = payload
        if len(payload) == 1:
            only_value = next(iter(payload.values()))
            if isinstance(only_value, dict):
                body = only_value
        depends_on = body.get("depends_on", [])
        if depends_on is None:
            continue
        if not isinstance(depends_on, list):
            add_error(
                findings,
                relpath(path, root),
                "depends_on must be a list of feature IDs.",
                "Change depends_on to a list or remove it.",
            )
            continue
        for dependency in depends_on:
            if not isinstance(dependency, str):
                add_error(
                    findings,
                    relpath(path, root),
                    "depends_on entries must be strings.",
                    "Use product feature IDs only.",
                )
                continue
            if dependency not in feature_ids:
                add_error(
                    findings,
                    relpath(path, root),
                    f"depends_on references unknown feature `{dependency}`.",
                    "Use an existing product feature ID or move method-layer relationships into spec/plan targets.",
                )


def is_id_like(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", value))


def validate_capability_ids(root: Path, findings: list[Finding]) -> None:
    paths = flat_feature_files(root) + managed_feature_contracts(root) + feature_source_files(root)
    for path in paths:
        try:
            payload = load_yaml(path)
        except yaml.YAMLError:
            continue
        if not isinstance(payload, dict):
            continue
        body = payload
        if len(payload) == 1:
            only_value = next(iter(payload.values()))
            if isinstance(only_value, dict):
                body = only_value
        capability_ids = body.get("capability_ids", [])
        if capability_ids is None:
            continue
        if not isinstance(capability_ids, list):
            add_error(
                findings,
                relpath(path, root),
                "capability_ids must be a list.",
                "Use stable kebab-case capability IDs.",
            )
            continue
        for capability_id in capability_ids:
            if not isinstance(capability_id, str) or not is_id_like(capability_id):
                add_error(
                    findings,
                    relpath(path, root),
                    f"Invalid capability ID: {capability_id!r}.",
                    "Use stable kebab-case IDs, not prose sentences.",
                )


def has_generated_header(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:300]
    except OSError:
        return False
    return "GENERATED FILE" in head or "Generated file" in head


def validate_generated_headers(root: Path, findings: list[Finding]) -> None:
    for path in feature_source_files(root):
        if has_generated_header(path):
            add_error(
                findings,
                relpath(path, root),
                "Human-owned feature.source.yaml appears to have a generated-file header.",
                "Regenerate into the feature contract path and keep feature.source.yaml human-owned.",
            )


def contains_feature_metadata_markers(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(pattern in text for pattern in FEATURE_METADATA_PATTERNS)


def metadata_marker_files(root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in METADATA_SCAN_SUFFIXES:
            continue
        relative_parts = path.relative_to(root).parts
        if relative_parts and relative_parts[0] in METADATA_SCAN_SKIP_DIRS:
            continue
        if contains_feature_metadata_markers(path):
            matches.append(path)
    return sorted(matches)


def validate_starter_method_only(root: Path, findings: list[Finding]) -> None:
    for path in feature_source_files(root):
        add_error(
            findings,
            relpath(path, root),
            "feature.source.yaml exists in starter_method_only mode.",
            "Switch to managed_architecture_metadata or remove feature metadata until adoption is chosen.",
        )
    for path in managed_feature_contracts(root):
        add_error(
            findings,
            relpath(path, root),
            "Managed feature contract exists in starter_method_only mode.",
            "Switch adoption mode or remove managed feature contracts.",
        )
    for path in generated_architecture_files(root):
        if is_empty_generated_scaffold(path):
            continue
        add_error(
            findings,
            relpath(path, root),
            "Non-empty generated architecture discovery exists in starter_method_only mode.",
            "Switch adoption mode or remove generated architecture indexes.",
        )
    for path in metadata_marker_files(root):
        add_error(
            findings,
            relpath(path, root),
            "Feature/capability metadata marker exists in starter_method_only mode.",
            "Switch adoption mode before adding feature/capability source metadata.",
        )

    features_root = root / "docs" / "features"
    if features_root.exists():
        for path in sorted(features_root.iterdir()):
            if path.name != "README.md":
                add_warning(
                    findings,
                    relpath(path, root),
                    "Non-README entry exists under docs/features in starter_method_only mode.",
                    "Confirm this is intentional prose, or switch adoption mode before adding feature metadata.",
                )
    stages_root = root / "docs" / "stages"
    if stages_root.exists():
        for path in sorted(stages_root.iterdir()):
            if path.name != "README.md":
                add_warning(
                    findings,
                    relpath(path, root),
                    "Non-README entry exists under docs/stages in starter_method_only mode.",
                    "Confirm this is intentional prose, or switch adoption mode before adding stage metadata.",
                )


def validate_managed_mode(config: AdoptionConfig, root: Path, findings: list[Finding]) -> None:
    for path in flat_feature_files(root):
        add_error(
            findings,
            relpath(path, root),
            "Flat authoritative feature YAML is not allowed in managed_architecture_metadata mode.",
            "Move semantic source into docs/features/<feature_id>/feature.source.yaml and regenerate the contract.",
        )
    for folder in feature_roots(root):
        source = folder / "feature.source.yaml"
        if not source.exists():
            add_error(
                findings,
                relpath(folder, root),
                "Managed feature folder is missing feature.source.yaml.",
                "Create the human-owned feature.source.yaml source file.",
            )
    if generated_architecture_files(root) and not feature_roots(root):
        add_error(
            findings,
            "docs/generated",
            "Generated architecture discovery exists but no managed feature folders were found.",
            "Create managed feature folders or remove stale generated discovery.",
        )
    if config.architecture_generator == "none":
        add_error(
            findings,
            "repo_config/adoption-mode.yaml",
            "managed_architecture_metadata mode requires an architecture_generator.",
            "Set architecture_generator to the sync/check script path.",
        )
    for folder in feature_roots(root):
        lineage = folder / "lineage.generated.yaml"
        if config.architecture_generator != "none" and not lineage.exists():
            add_warning(
                findings,
                relpath(folder, root),
                "Managed feature folder is missing lineage.generated.yaml.",
                "Run the architecture generator if lineage is adopted, or document why lineage is deferred.",
            )
    if not metadata_marker_files(root):
        add_warning(
            findings,
            ".",
            "No source metadata markers were found outside docs/config roots.",
            "Confirm source metadata is intentionally deferred, or add canonical feature/capability markers.",
        )


def validate_legacy_mode(config: AdoptionConfig, root: Path, findings: list[Finding]) -> None:
    for path in feature_source_files(root):
        add_error(
            findings,
            relpath(path, root),
            "feature.source.yaml exists in legacy_compatibility mode.",
            "Switch to managed_architecture_metadata or remove managed source files.",
        )
    flat_ids = {path.stem for path in flat_feature_files(root)}
    for contract in managed_feature_contracts(root):
        if contract.stem in flat_ids:
            add_error(
                findings,
                relpath(contract, root),
                "Managed feature-folder contract exists beside a flat authoritative contract.",
                "Choose legacy compatibility or managed mode; do not keep both authoritative shapes.",
            )
    follow_up = config.payload.get("migration_follow_up")
    if not isinstance(follow_up, dict) or not follow_up.get("required"):
        add_warning(
            findings,
            "repo_config/adoption-mode.yaml",
            "legacy_compatibility mode has no required migration_follow_up.",
            "Record the follow-up migration plan or document why legacy mode is long-lived.",
        )
    if generated_architecture_files(root) and config.architecture_generator == "none":
        add_warning(
            findings,
            "docs/generated",
            "Generated architecture discovery exists without a documented legacy generator.",
            "Document the legacy generator or remove stale generated discovery.",
        )


def validate_specs_and_plans(root: Path, findings: list[Finding]) -> None:
    for folder_name in ("specs", "plans"):
        folder = root / "docs" / "superpowers" / folder_name
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "candidate_type: operating_system" in text and "targets:" not in text:
                add_error(
                    findings,
                    relpath(path, root),
                    "Operating-system spec/plan candidate is missing targets.",
                    "Add targets for affected operating-system files/folders.",
                )
            if "candidate_type: operating_system" in text and "related_features: []" not in text:
                add_warning(
                    findings,
                    relpath(path, root),
                    "Operating-system spec/plan does not explicitly clear related_features.",
                    "Use related_features: [] unless product-feature impact is intentionally documented.",
                )


def run_validation(root: Path, adoption_mode_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    config = parse_adoption_config(adoption_mode_path, findings, root)

    validate_method_feature_ids(root, findings)
    validate_feature_dependencies(root, findings)
    validate_capability_ids(root, findings)
    validate_generated_headers(root, findings)
    validate_specs_and_plans(root, findings)

    if config is None:
        return findings

    if config.mode == "starter_method_only":
        validate_starter_method_only(root, findings)
    elif config.mode == "managed_architecture_metadata":
        validate_managed_mode(config, root, findings)
    elif config.mode == "legacy_compatibility":
        validate_legacy_mode(config, root, findings)

    return findings


def print_findings(findings: list[Finding]) -> None:
    if not findings:
        print("Adoption shape validation passed.")
        return

    for finding in findings:
        print(f"{finding.level}: {finding.path}: {finding.message}")
        print(f"  fix: {finding.fix}")


def main() -> int:
    args = build_parser().parse_args()
    root = args.repo_root.resolve()
    adoption_mode_path = (root / args.adoption_mode).resolve()
    findings = run_validation(root, adoption_mode_path)
    print_findings(findings)
    return 1 if any(finding.level == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
