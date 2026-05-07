"""
Deploy generated agent runtime artifacts to user home runtime targets.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
import re
import shutil

import yaml

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


def _looks_like_repo_relative_path(value: str) -> bool:
    if not value or value.startswith(("http://", "https://")):
        return False
    if value.startswith("<") or value.startswith("%"):
        return False
    pure = PurePosixPath(value.replace("\\", "/"))
    if pure.is_absolute():
        return False
    if pure.parts and pure.parts[0] in {
        "docs",
        "scripts",
        "repo_config",
        ".agents",
        "generated_agents",
        "configs",
        "tests",
        "AGENTS.md",
        "README.md",
    }:
        return True
    return False


def _repo_absolute_string(root: Path, relative_path: str) -> str:
    normalized = relative_path.replace("/", "\\")
    return str((root / normalized).resolve())


def _rewrite_command_to_absolute_repo_path(command: str, root: Path) -> str:
    match = re.match(r'^(python|py)\s+([^"\s][^\s]*)$', command.strip())
    if not match:
        return command
    executable, target = match.groups()
    if not _looks_like_repo_relative_path(target):
        return command
    return f'{executable} "{_repo_absolute_string(root, target)}"'


def _rewrite_frontmatter_lists(meta: dict[str, object], root: Path) -> dict[str, object]:
    rewritten = dict(meta)
    for key in ("required_reads", "required_outputs"):
        value = rewritten.get(key)
        if not isinstance(value, list):
            continue
        rewritten[key] = [
            _repo_absolute_string(root, item) if isinstance(item, str) and _looks_like_repo_relative_path(item) else item
            for item in value
        ]
    hooks = rewritten.get("hooks")
    if isinstance(hooks, dict):
        rewritten_hooks = dict(hooks)
        for key in ("pre", "post"):
            value = rewritten_hooks.get(key)
            if not isinstance(value, list):
                continue
            rewritten_hooks[key] = [
                _rewrite_command_to_absolute_repo_path(item, root) if isinstance(item, str) else item
                for item in value
            ]
        rewritten["hooks"] = rewritten_hooks
    return rewritten


def _rewrite_text_runtime_paths(text: str, *, root: Path) -> str:
    normalized = text.replace("\r\n", "\n")
    if normalized.startswith("---\n"):
        parts = normalized.split("---\n", 2)
        if len(parts) >= 3:
            payload = yaml.safe_load(parts[1]) or {}
            if isinstance(payload, dict):
                rewritten_payload = _rewrite_frontmatter_lists(payload, root)
                frontmatter = yaml.safe_dump(rewritten_payload, sort_keys=False, allow_unicode=False).strip()
                normalized = f"---\n{frontmatter}\n---\n" + parts[2]
    lines: list[str] = []
    for line in normalized.splitlines():
        if line.startswith("Source: "):
            source_value = line[len("Source: ") :].strip()
            if source_value.startswith("`") and source_value.endswith("`"):
                raw = source_value[1:-1]
                if _looks_like_repo_relative_path(raw):
                    line = f'Source: `{_repo_absolute_string(root, raw)}`'
            elif _looks_like_repo_relative_path(source_value):
                line = f'Source: {_repo_absolute_string(root, source_value)}'
        elif "  - Source: `" in line and line.rstrip().endswith("`"):
            prefix, raw = line.split("`", 1)
            candidate, _ = raw.rsplit("`", 1)
            if _looks_like_repo_relative_path(candidate):
                line = f"{prefix}`{_repo_absolute_string(root, candidate)}`"
        lines.append(line)
    return "\n".join(lines)


def _render_runtime_text(src: Path, *, root: Path) -> str:
    return _rewrite_text_runtime_paths(src.read_text(encoding="utf-8"), root=root).rstrip("\n")


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


def _check_platform(generated_root: Path, target_root: Path, *, root: Path) -> list[str]:
    issues: list[str] = []
    generated_files = [p for p in generated_root.rglob("*") if p.is_file()]
    for src in generated_files:
        rel = src.relative_to(generated_root)
        dst = target_root / rel
        if not dst.exists():
            issues.append(f"Missing deployed file: {dst.as_posix()}")
            continue
        if _render_runtime_text(src, root=root) != _read_text(dst):
            issues.append(f"Deployed drift: {dst.as_posix()}")
    return issues


def _plan_deploy(generated_root: Path, target_root: Path, *, root: Path, force: bool) -> tuple[list[str], list[str], list[tuple[Path, Path, str]]]:
    changes: list[str] = []
    issues: list[str] = []
    pairs: list[tuple[Path, Path, str]] = []
    generated_files = [p for p in generated_root.rglob("*") if p.is_file()]
    for src in generated_files:
        rel = src.relative_to(generated_root)
        dst = target_root / rel
        rendered = _render_runtime_text(src, root=root)
        if dst.exists():
            if rendered == _read_text(dst):
                continue
            if not force and not _looks_generated(dst):
                issues.append(f"Refusing to overwrite non-generated runtime file without --force: {dst.as_posix()}")
                continue
            changes.append(f"update: {dst.as_posix()}")
        else:
            changes.append(f"create: {dst.as_posix()}")
        pairs.append((src, dst, rendered))
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
            issues.extend(_check_platform(generated_root, target_root, root=root))
            continue
        changes, plan_issues, pairs = _plan_deploy(generated_root, target_root, root=root, force=args.force)
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
        for _, dst, rendered in pairs:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if backup_root is not None and dst.exists():
                backup_path = backup_root / dst.relative_to(target_root)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup_path)
            dst.write_text(rendered + "\n", encoding="utf-8")
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
