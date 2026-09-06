"""
@meta
name: validate_repo_config
type: script
domain: config
distribution_tier: starter_kit
responsibility:
  - Validate repo-level config ownership surfaces for shape and path sanity.
inputs:
  - repo_config/publication-config.json
  - repo_config/starter-kit-manifest.json (optional; validated when present)
outputs:
  - Exit status and human-readable validation results.
tags:
  - config
  - validation
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

try:
    from project_root import resolve_repo_root
except ModuleNotFoundError:
    from scripts.project_root import resolve_repo_root


REQUIRED_PUBLICATION_KEYS = {
    "publicPaths",
    "forbiddenPaths",
    "requiredPaths",
    "allowedGeneratedPaths",
    "scrubPrivateReferencePaths",
    "forbiddenMetadataMarkers",
}
OPTIONAL_PUBLICATION_LIST_KEYS = {
    "forbiddenFilenameMarkers",
    "publicExcludeGlobs",
}
OPTIONAL_PUBLICATION_BOOL_KEYS = {
    "publicIncludeOverridesExcludes",
}
REQUIRED_STARTER_KIT_KEYS = {
    "outputRoot",
    "copyPaths",
    "requiredPaths",
    "forbiddenPaths",
    "sharedPaths",
}

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate repo config ownership surfaces, publication boundaries, "
            "starter-kit manifest and runtime config YAML shape."
        )
    )
    parser.add_argument(
        "--publication-config",
        default="repo_config/publication-config.json",
        help="Path to publication-config.json.",
    )
    parser.add_argument(
        "--starter-kit-manifest",
        default="repo_config/starter-kit-manifest.json",
        help=(
            "Path to starter-kit-manifest.json. Optional in consumer repos; "
            "validated when present."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional repo root override. Defaults to the current working directory.",
    )
    return parser


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def infer_repo_root(
    repo_root_arg: str | None,
    publication_config: Path,
    starter_kit_manifest: Path,
) -> Path:
    return resolve_repo_root(repo_root_arg)


def validate_publication_config(payload: Any, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append("Publication config must be a JSON object.")
        return

    missing = REQUIRED_PUBLICATION_KEYS - set(payload.keys())
    if missing:
        errors.append(
            "Publication config is missing required keys: "
            + ", ".join(sorted(missing))
        )

    for key in REQUIRED_PUBLICATION_KEYS & set(payload.keys()):
        value = payload[key]
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            errors.append(f"Publication config key `{key}` must be a list of strings.")

    for key in OPTIONAL_PUBLICATION_LIST_KEYS & set(payload.keys()):
        value = payload[key]
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            errors.append(f"Publication config key `{key}` must be a list of strings.")

    for key in OPTIONAL_PUBLICATION_BOOL_KEYS & set(payload.keys()):
        if not isinstance(payload[key], bool):
            errors.append(f"Publication config key `{key}` must be a boolean.")


def _paths_overlap(left: str, right: str) -> bool:
    left_path = Path(left.replace("\\", "/")).as_posix().rstrip("/")
    right_path = Path(right.replace("\\", "/")).as_posix().rstrip("/")
    return left_path == right_path or left_path.startswith(right_path + "/") or right_path.startswith(left_path + "/")


def _is_safe_relative_path(value: str) -> bool:
    path = PurePosixPath(value.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts


def validate_starter_kit_manifest(payload: Any, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append("Starter-kit manifest must be a JSON object.")
        return

    missing = REQUIRED_STARTER_KIT_KEYS - set(payload.keys())
    if missing:
        errors.append(
            "Starter-kit manifest is missing required keys: "
            + ", ".join(sorted(missing))
        )

    output_root = payload.get("outputRoot")
    if not isinstance(output_root, str) or not output_root.strip():
        errors.append("Starter-kit manifest key `outputRoot` must be a non-empty string.")

    for key in (REQUIRED_STARTER_KIT_KEYS - {"outputRoot"}) & set(payload.keys()):
        if key == "sharedPaths":
            value = payload[key]
            if not isinstance(value, dict) or set(value) != {"docs", "scripts", "skills"}:
                errors.append(
                    "Starter-kit manifest key `sharedPaths` must contain only `docs`, `scripts`, and `skills` lists."
                )
                continue
            for bundle_name in ("docs", "scripts", "skills"):
                bundle_paths = value[bundle_name]
                if not isinstance(bundle_paths, list) or not all(
                    isinstance(item, str) and item.strip() for item in bundle_paths
                ):
                    errors.append(
                        f"Starter-kit manifest key `sharedPaths.{bundle_name}` must be a list of strings."
                    )
            continue
        value = payload[key]
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            errors.append(f"Starter-kit manifest key `{key}` must be a list of strings.")

    shared_paths = payload.get("sharedPaths")
    if isinstance(shared_paths, dict) and all(
        isinstance(shared_paths.get(name), list) for name in ("docs", "scripts", "skills")
    ):
        other_paths = [
            item
            for key in ("copyPaths", "requiredPaths", "omitPaths", "createEmptyDirs")
            for item in payload.get(key, [])
            if isinstance(item, str)
        ]
        for bundle_name in ("docs", "scripts", "skills"):
            for shared_path in shared_paths[bundle_name]:
                if not isinstance(shared_path, str):
                    continue
                if not _is_safe_relative_path(shared_path):
                    errors.append(f"Starter-kit shared path must be relative and stay under repo root: {shared_path}")

        for bundle_paths in shared_paths.values():
            for shared_path in bundle_paths:
                for other_path in other_paths:
                    if _paths_overlap(shared_path, other_path):
                        errors.append(
                            f"Starter-kit shared path overlaps another manifest path: {shared_path} vs {other_path}"
                        )



def validate_runtime_configs(runtime_root: Path, errors: list[str]) -> None:
    yaml_paths = sorted(runtime_root.glob("*.yaml"))
    if not yaml_paths:
        errors.append(f"No runtime config YAML files found under: {runtime_root}")
        return

    for path in yaml_paths:
        try:
            payload = load_yaml(path)
        except yaml.YAMLError as exc:
            errors.append(f"Runtime config `{path}` could not be parsed: {exc}")
            continue

        if not isinstance(payload, dict):
            errors.append(
                f"Runtime config `{path}` must be a top-level mapping, not {type(payload).__name__}."
            )
            continue

        if not payload:
            errors.append(f"Runtime config `{path}` must not be empty.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        repo_root = infer_repo_root(args.repo_root, Path(args.publication_config), Path(args.starter_kit_manifest))
    except RuntimeError as exc:
        print(f"Repo config validation blocked: {exc}")
        return 2
    publication_config_path = Path(args.publication_config)
    if not publication_config_path.is_absolute():
        publication_config_path = repo_root / publication_config_path
    publication_config_path = publication_config_path.resolve()
    starter_kit_manifest_path = Path(args.starter_kit_manifest)
    if not starter_kit_manifest_path.is_absolute():
        starter_kit_manifest_path = repo_root / starter_kit_manifest_path
    starter_kit_manifest_path = starter_kit_manifest_path.resolve()

    errors: list[str] = []

    for path, label in ((publication_config_path, "Publication config"),):
        if not path.exists():
            errors.append(f"{label} path does not exist: {path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    try:
        publication_config = load_json(publication_config_path)
    except json.JSONDecodeError as exc:
        errors.append(f"Publication config could not be parsed: {exc}")
        publication_config = None


    starter_kit_manifest = None
    if starter_kit_manifest_path.exists():
        try:
            starter_kit_manifest = load_json(starter_kit_manifest_path)
        except json.JSONDecodeError as exc:
            errors.append(f"Starter-kit manifest could not be parsed: {exc}")

    if publication_config is not None:
        validate_publication_config(publication_config, errors)
    if starter_kit_manifest is not None:
        validate_starter_kit_manifest(starter_kit_manifest, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Repo config validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
