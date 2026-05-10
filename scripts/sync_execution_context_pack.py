"""
@meta
name: sync_execution_context_pack
type: script
domain: docs
responsibility:
  - Sync execution context pack between worktree mirror and canonical repo storage.
  - Enforce Option B lane-id path safety and canonical path contract.
inputs:
  - artifacts/execution_context_pack.md
  - docs/superpowers/execution_context_packs/<lane-id>/latest.md
outputs:
  - Updated canonical context pack latest file.
  - Optional timestamped snapshot.
  - Optional updated worktree mirror.
tags:
  - docs
  - execution
  - handoff
  - sync
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import sys

LANE_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync execution context pack between mirror and canonical storage.")
    parser.add_argument("--repo-root", default=str(repo_root()), help="Repository root path.")
    parser.add_argument("--lane", required=True, help="Lane/workstream-safe id used under canonical storage.")
    parser.add_argument("--from-worktree", action="store_true", help="Copy mirror -> canonical latest.")
    parser.add_argument("--to-worktree", action="store_true", help="Copy canonical latest -> mirror.")
    parser.add_argument("--snapshot", action="store_true", help="Write timestamped snapshot after canonical update.")
    parser.add_argument(
        "--mirror-path",
        default="artifacts/execution_context_pack.md",
        help="Repo-relative mirror file path. Default: artifacts/execution_context_pack.md",
    )
    return parser


def validate_lane_id(lane: str) -> None:
    if not LANE_PATTERN.match(lane):
        raise ValueError(
            "Invalid --lane. Use only letters, numbers, dot, underscore, dash; must start with alphanumeric."
        )


def canonical_latest_path(root: Path, lane: str) -> Path:
    return root / "docs" / "superpowers" / "execution_context_packs" / lane / "latest.md"


def canonical_snapshot_path(root: Path, lane: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
    return root / "docs" / "superpowers" / "execution_context_packs" / lane / "snapshots" / f"{stamp}.md"


def sync_from_worktree(root: Path, lane: str, mirror_path: Path, snapshot: bool) -> None:
    if not mirror_path.exists():
        raise FileNotFoundError(f"Mirror file not found: {mirror_path.as_posix()}")
    latest = canonical_latest_path(root, lane)
    latest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(mirror_path, latest)
    print(f"Updated canonical latest: {latest.as_posix()}")
    if snapshot:
        snap = canonical_snapshot_path(root, lane)
        snap.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(latest, snap)
        print(f"Wrote snapshot: {snap.as_posix()}")


def sync_to_worktree(root: Path, lane: str, mirror_path: Path) -> None:
    latest = canonical_latest_path(root, lane)
    if not latest.exists():
        raise FileNotFoundError(f"Canonical latest not found: {latest.as_posix()}")
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(latest, mirror_path)
    print(f"Updated mirror: {mirror_path.as_posix()}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.from_worktree and not args.to_worktree:
        print("Error: select at least one mode: --from-worktree and/or --to-worktree", file=sys.stderr)
        return 2

    try:
        validate_lane_id(args.lane)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    root = Path(args.repo_root).resolve()
    mirror = (root / args.mirror_path).resolve()

    try:
        if args.from_worktree:
            sync_from_worktree(root, args.lane, mirror, args.snapshot)
        if args.to_worktree:
            sync_to_worktree(root, args.lane, mirror)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
