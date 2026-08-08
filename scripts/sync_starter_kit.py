"""
@meta
name: sync_starter_kit
type: script
domain: docs
responsibility:
  - Rebuild generated starter-kit export and deployed sibling from canonical sources.
  - Validate both outputs and prove byte-for-byte tree parity.
inputs:
  - repo_config/starter-kit-manifest.json
  - Optional export and deployment parent directories.
outputs:
  - Generated starter-kit export and deployed sibling starter kit.
tags:
  - docs
  - generation
  - local-only
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from pathlib import Path

from build_starter_kit import build_starter_kit, repo_root
from validate_starter_kit import compare_tree_parity, validate_starter_kit


def sync_starter_kit(
    *,
    repo_root: Path,
    manifest_path: Path,
    export_root: Path,
    deploy_root: Path,
) -> Path:
    if export_root.resolve() == deploy_root.resolve():
        raise ValueError("starter-kit export and deploy roots must differ")
    exported_root = build_starter_kit(
        repo_root=repo_root,
        manifest_path=manifest_path,
        output_root=export_root,
    )
    deployed_root = build_starter_kit(
        repo_root=repo_root,
        manifest_path=manifest_path,
        output_root=deploy_root,
    )
    errors = validate_starter_kit(kit_root=exported_root, manifest_path=manifest_path)
    errors.extend(validate_starter_kit(kit_root=deployed_root, manifest_path=manifest_path))
    errors.extend(compare_tree_parity(expected_root=exported_root, actual_root=deployed_root))
    if errors:
        raise ValueError("starter-kit sync failed:\n" + "\n".join(errors))
    return deployed_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync generated and deployed project-OS-starter-kit outputs.")
    parser.add_argument("--repo-root", default=str(repo_root()), help="Canonical source repo root.")
    parser.add_argument("--manifest", default="repo_config/starter-kit-manifest.json", help="Starter-kit manifest path.")
    parser.add_argument("--export-root", default="generated_exports", help="Generated export parent directory.")
    parser.add_argument("--deploy-root", help="Deployed kit parent directory. Defaults to source repo parent.")
    return parser


def _resolve_path(value: str, *, source_root: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (source_root / path).resolve()


def main() -> int:
    args = build_parser().parse_args()
    source_root = Path(args.repo_root).resolve()
    manifest_path = _resolve_path(args.manifest, source_root=source_root)
    export_root = _resolve_path(args.export_root, source_root=source_root)
    deploy_root = Path(args.deploy_root).resolve() if args.deploy_root else source_root.parent
    deployed_root = sync_starter_kit(
        repo_root=source_root,
        manifest_path=manifest_path,
        export_root=export_root,
        deploy_root=deploy_root,
    )
    print(f"Starter kit synced at: {deployed_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
