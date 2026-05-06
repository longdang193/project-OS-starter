"""
Deploy generated agent runtime artifacts to user home runtime targets.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import shutil

PLATFORM_TARGETS = {
    "codex": Path.home() / ".codex",
    "claude": Path.home() / ".claude",
    "antigravity": Path.home() / ".gemini",
}

TARGET_ALIASES = {
    "gemini": "antigravity",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy generated agent runtime artifacts.")
    parser.add_argument(
        "--target",
        choices=["all", "codex", "claude", "antigravity", "gemini"],
        default="all",
        help="Platform target to deploy.",
    )
    parser.add_argument("--check", action="store_true", help="Check drift only.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned deploy changes without writing.")
    parser.add_argument("--backup", action="store_true", help="Backup overwritten files before deploy.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting runtime files without generated headers.")
    return parser.parse_args()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")


def _looks_generated(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return '"_generated": true' in text.lower() and '"_source"' in text and '"_do_not_edit"' in text
    return "<!--" in text[:256] and "GENERATED FILE - DO NOT EDIT" in text[:512]


def _check_platform(generated_root: Path, target_root: Path) -> list[str]:
    issues: list[str] = []
    generated_files = [p for p in generated_root.rglob("*") if p.is_file()]
    for src in generated_files:
        rel = src.relative_to(generated_root)
        dst = target_root / rel
        if not dst.exists():
            issues.append(f"Missing deployed file: {dst.as_posix()}")
            continue
        if _read_text(src) != _read_text(dst):
            issues.append(f"Deployed drift: {dst.as_posix()}")
    return issues


def _plan_deploy(generated_root: Path, target_root: Path, *, force: bool) -> tuple[list[str], list[str], list[tuple[Path, Path]]]:
    changes: list[str] = []
    issues: list[str] = []
    pairs: list[tuple[Path, Path]] = []
    generated_files = [p for p in generated_root.rglob("*") if p.is_file()]
    for src in generated_files:
        rel = src.relative_to(generated_root)
        dst = target_root / rel
        if dst.exists():
            if _read_text(src) == _read_text(dst):
                continue
            if not force and not _looks_generated(dst):
                issues.append(f"Refusing to overwrite non-generated runtime file without --force: {dst.as_posix()}")
                continue
            changes.append(f"update: {dst.as_posix()}")
        else:
            changes.append(f"create: {dst.as_posix()}")
        pairs.append((src, dst))
    return changes, issues, pairs


def _resolved_targets(raw_target: str) -> list[str]:
    if raw_target == "all":
        return list(PLATFORM_TARGETS.keys())
    canonical = TARGET_ALIASES.get(raw_target, raw_target)
    return [canonical]


def run() -> int:
    args = parse_args()
    root = repo_root()
    targets = _resolved_targets(args.target)
    issues: list[str] = []
    for platform in targets:
        generated_root = root / "generated_agents" / platform
        if not generated_root.exists():
            issues.append(f"Missing generated platform directory: {generated_root.as_posix()}")
            continue
        target_root = PLATFORM_TARGETS[platform]
        if args.check:
            issues.extend(_check_platform(generated_root, target_root))
            continue
        changes, plan_issues, pairs = _plan_deploy(generated_root, target_root, force=args.force)
        issues.extend(plan_issues)
        if plan_issues:
            continue
        if args.dry_run:
            print(f"[dry-run] {platform} -> {target_root.as_posix()}")
            for change in changes:
                print(f"- {change}")
            continue
        backup_root: Path | None = None
        if args.backup:
            stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            backup_root = target_root / ".backups" / stamp
        for src, dst in pairs:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if backup_root is not None and dst.exists():
                backup_path = backup_root / dst.relative_to(target_root)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup_path)
            shutil.copy2(src, dst)
        print(f"Deployed {platform} -> {target_root.as_posix()} ({len(pairs)} changed)")
    if issues:
        print("Deploy check failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    if args.check:
        print("Deployed runtime targets are up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
