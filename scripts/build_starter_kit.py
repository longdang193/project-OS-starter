"""
@meta
name: build_starter_kit
type: script
domain: docs
responsibility:
  - Build consume-only project-OS-starter-kit output from canonical project-OS-starter sources.
  - Copy only manifest-approved paths into kit output and exclude forbidden factory-only surfaces.
inputs:
  - repo_config/starter-kit-manifest.json
outputs:
  - Generated starter-kit directory tree under chosen output root.
tags:
  - docs
  - generation
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any


@dataclass(frozen=True)
class StarterKitManifest:
    output_root: str
    copy_paths: list[str]
    required_paths: list[str]
    forbidden_paths: list[str]
    omit_paths: list[str]
    create_empty_dirs: list[str]


REQUIRED_MANIFEST_KEYS = {
    "outputRoot",
    "copyPaths",
    "requiredPaths",
    "forbiddenPaths",
    "omitPaths",
    "createEmptyDirs",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build project-OS-starter-kit from manifest.")
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
        "--output-root",
        default="generated_exports",
        help="Directory where kit output root should be created.",
    )
    return parser


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_string_list(value: Any, *, key: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"Manifest key `{key}` must be a list of non-empty strings.")
    return [item.strip() for item in value]


def load_manifest(manifest_path: Path) -> StarterKitManifest:
    payload = _load_json(manifest_path)
    if not isinstance(payload, dict):
        raise ValueError("Starter-kit manifest must be a JSON object.")
    missing = REQUIRED_MANIFEST_KEYS - set(payload.keys())
    if missing:
        raise ValueError(
            "Starter-kit manifest is missing required keys: " + ", ".join(sorted(missing))
        )
    output_root = payload.get("outputRoot")
    if not isinstance(output_root, str) or not output_root.strip():
        raise ValueError("Manifest key `outputRoot` must be a non-empty string.")
    return StarterKitManifest(
        output_root=output_root.strip(),
        copy_paths=_validate_string_list(payload.get("copyPaths"), key="copyPaths"),
        required_paths=_validate_string_list(payload.get("requiredPaths"), key="requiredPaths"),
        forbidden_paths=_validate_string_list(payload.get("forbiddenPaths"), key="forbiddenPaths"),
        omit_paths=_validate_string_list(payload.get("omitPaths"), key="omitPaths"),
        create_empty_dirs=_validate_string_list(payload.get("createEmptyDirs"), key="createEmptyDirs"),
    )


def _resolve_under(root: Path, relative_path: str) -> Path:
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes repo root: {relative_path}") from exc
    return path


def _copy_path(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return
    shutil.copy2(source, destination)


def _remove_omitted_paths(*, kit_root: Path, omit_paths: list[str]) -> None:
    for relative_path in omit_paths:
        destination = kit_root / relative_path
        if destination.is_dir():
            shutil.rmtree(destination)
        elif destination.exists():
            destination.unlink()


def _create_empty_dirs(*, kit_root: Path, create_empty_dirs: list[str]) -> None:
    for relative_path in create_empty_dirs:
        (kit_root / relative_path).mkdir(parents=True, exist_ok=True)


def _destination_relative_path(relative_path: str) -> Path:
    if relative_path == "generated_agents/antigravity/GEMINI.md":
        return Path("GEMINI.md")
    if relative_path == "generated_agents/claude/CLAUDE.md":
        return Path("CLAUDE.md")
    return Path(relative_path)


def build_starter_kit(*, repo_root: Path, manifest_path: Path, output_root: Path) -> Path:
    manifest = load_manifest(manifest_path)
    kit_root = output_root / manifest.output_root
    if kit_root.exists():
        shutil.rmtree(kit_root)
    kit_root.mkdir(parents=True, exist_ok=True)

    for relative_path in manifest.copy_paths:
        source = _resolve_under(repo_root, relative_path)
        if not source.exists():
            raise FileNotFoundError(f"Missing copy path: {relative_path}")
        destination = kit_root / _destination_relative_path(relative_path)
        _copy_path(source, destination)

    _remove_omitted_paths(kit_root=kit_root, omit_paths=manifest.omit_paths)
    _create_empty_dirs(kit_root=kit_root, create_empty_dirs=manifest.create_empty_dirs)

    for forbidden_path in manifest.forbidden_paths:
        destination = kit_root / forbidden_path
        if destination.exists():
            raise ValueError(f"Forbidden path copied into starter kit: {forbidden_path}")

    for required_path in manifest.required_paths:
        destination = kit_root / required_path
        if not destination.exists():
            raise ValueError(f"Required path missing from starter kit: {required_path}")

    return kit_root


def main() -> int:
    args = build_parser().parse_args()
    source_root = Path(args.repo_root).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = source_root / manifest_path
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = source_root / output_root
    kit_root = build_starter_kit(
        repo_root=source_root,
        manifest_path=manifest_path.resolve(),
        output_root=output_root.resolve(),
    )
    print(f"Starter kit built at: {kit_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
