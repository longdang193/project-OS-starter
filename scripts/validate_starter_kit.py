"""
@meta
name: validate_starter_kit
type: script
domain: docs
responsibility:
  - Validate built starter-kit output against required and forbidden manifest paths.
inputs:
  - repo_config/starter-kit-manifest.json
  - Built starter-kit directory tree
outputs:
  - Exit status and human-readable starter-kit validation results.
tags:
  - docs
  - validation
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_starter_kit import load_manifest, repo_root

TEXT_FILE_SUFFIXES = {
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".py",
    ".ps1",
}

CONTENT_SCAN_ROOTS = (
    Path("AGENTS.md"),
    Path("GEMINI.md"),
    Path("CLAUDE.md"),
    Path(".agents/skills"),
    Path("docs/operating_system"),
)

FORBIDDEN_CONTENT_TOKENS = (
    ".codex/agents/",
    "scripts/build_starter_kit.py",
    "scripts/validate_starter_kit.py",
    "scripts/sync_agent_adapters.py",
    "scripts/deploy_agent_runtime.py",
    "generated_exports/project-OS-starter-kit",
    "repo_config/publication-config.json",
    "generated_agents/",
    "adapters/",
)

ALLOWED_CONDITIONAL_REFERENCES = {
    (
        Path("docs/operating_system/governance/repo-governance.md"),
        "repo_config/publication-config.json",
    ),
    (
        Path("docs/operating_system/governance/repo-governance.md"),
        "generated_agents/",
    ),
    (
        Path("docs/operating_system/governance/repo-governance.md"),
        "generated_exports/project-OS-starter-kit",
    ),
    (
        Path("docs/operating_system/governance/repo-governance.md"),
        "adapters/",
    ),
    (
        Path("docs/operating_system/governance/feature-routing-guide.md"),
        "repo_config/publication-config.json",
    ),
    (
        Path("docs/operating_system/governance/feature-routing-guide.md"),
        "adapters/",
    ),
    (
        Path("docs/operating_system/publication/public-repo-publication-policy.md"),
        "repo_config/publication-config.json",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate built project-OS-starter-kit output.")
    parser.add_argument(
        "--repo-root",
        default=str(repo_root()),
        help="Canonical source repo root.",
    )
    parser.add_argument(
        "--manifest",
        default="repo_config/starter-kit-manifest.json",
        help="Path to starter-kit manifest JSON.",
    )
    parser.add_argument(
        "--kit-root",
        required=False,
        help="Built starter-kit root. Defaults to <repo-root>/generated_exports/<outputRoot>.",
    )
    parser.add_argument(
        "--output-root",
        default="generated_exports",
        help="Parent directory of built starter-kit root when --kit-root is omitted.",
    )
    parser.add_argument(
        "--compare-kit-root",
        required=False,
        help="Optional second starter-kit tree to compare against the resolved --kit-root.",
    )
    return parser


def _iter_scannable_files(*, kit_root: Path):
    for relative_root in CONTENT_SCAN_ROOTS:
        absolute_root = kit_root / relative_root
        if absolute_root.is_file() and absolute_root.suffix.lower() in TEXT_FILE_SUFFIXES:
            yield absolute_root
            continue
        if not absolute_root.is_dir():
            continue
        for file_path in absolute_root.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in TEXT_FILE_SUFFIXES:
                yield file_path


def _scan_forbidden_content(*, kit_root: Path) -> list[str]:
    errors: list[str] = []
    for file_path in _iter_scannable_files(kit_root=kit_root):
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative_path = file_path.relative_to(kit_root)
        for token in FORBIDDEN_CONTENT_TOKENS:
            if token not in content:
                continue
            if (relative_path, token) in ALLOWED_CONDITIONAL_REFERENCES:
                continue
            errors.append(f"Forbidden content reference in {relative_path}: {token}")
    return errors


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_tree_paths(root: Path) -> set[Path]:
    paths: set[Path] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if relative_path.parts and relative_path.parts[0] == ".git":
            continue
        paths.add(relative_path)
    return paths


def compare_tree_parity(*, expected_root: Path, actual_root: Path) -> list[str]:
    errors: list[str] = []
    expected_paths = _iter_tree_paths(expected_root)
    actual_paths = _iter_tree_paths(actual_root)

    missing_paths = sorted(expected_paths - actual_paths)
    unexpected_paths = sorted(actual_paths - expected_paths)

    for relative_path in missing_paths:
        errors.append(f"Missing path in compared tree: {relative_path.as_posix()}")
    for relative_path in unexpected_paths:
        errors.append(f"Unexpected path present in compared tree: {relative_path.as_posix()}")

    for relative_path in sorted(expected_paths & actual_paths):
        expected_path = expected_root / relative_path
        actual_path = actual_root / relative_path
        if _file_digest(expected_path) != _file_digest(actual_path):
            errors.append(f"Content mismatch for path: {relative_path.as_posix()}")

    return errors


def validate_starter_kit(*, kit_root: Path, manifest_path: Path) -> list[str]:
    manifest = load_manifest(manifest_path)
    errors: list[str] = []

    for required_path in manifest.required_paths:
        if not (kit_root / required_path).exists():
            errors.append(f"Missing required path: {required_path}")

    for forbidden_path in manifest.forbidden_paths:
        if (kit_root / forbidden_path).exists():
            errors.append(f"Forbidden path present: {forbidden_path}")

    for omitted_path in manifest.omit_paths:
        if (kit_root / omitted_path).exists():
            errors.append(f"Omitted path still present: {omitted_path}")

    for empty_dir in manifest.create_empty_dirs:
        path = kit_root / empty_dir
        if not path.is_dir():
            errors.append(f"Required empty directory missing: {empty_dir}")

    errors.extend(_scan_forbidden_content(kit_root=kit_root))

    return errors


def main() -> int:
    args = build_parser().parse_args()
    source_root = Path(args.repo_root).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = source_root / manifest_path
    manifest = load_manifest(manifest_path.resolve())
    if args.kit_root:
        kit_root = Path(args.kit_root).resolve()
    else:
        output_root = Path(args.output_root)
        if not output_root.is_absolute():
            output_root = source_root / output_root
        kit_root = (output_root / manifest.output_root).resolve()

    errors = validate_starter_kit(kit_root=kit_root, manifest_path=manifest_path.resolve())
    if args.compare_kit_root:
        compare_root = Path(args.compare_kit_root).resolve()
        errors.extend(compare_tree_parity(expected_root=kit_root, actual_root=compare_root))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Starter kit validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
