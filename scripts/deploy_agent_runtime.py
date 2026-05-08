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


def _runtime_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path.replace("\\", "/"))
    return str(normalized).replace("/", "\\")


def _runtime_absolute_string(target_root: Path, relative_path: str) -> str:
    return str((target_root / _runtime_relative_path(relative_path)).resolve())


def _rewrite_command_to_absolute_repo_path(command: str, root: Path) -> str:
    match = re.match(r'^(python|py)\s+([^"\s][^\s]*)$', command.strip())
    if not match:
        return command
    executable, target = match.groups()
    if not _looks_like_repo_relative_path(target):
        return command
    return f'{executable} "{_repo_absolute_string(root, target)}"'


def _rewrite_frontmatter_lists(meta: dict[str, object], target_root: Path) -> dict[str, object]:
    rewritten = dict(meta)
    for key in ("required_reads", "required_outputs"):
        value = rewritten.get(key)
        if not isinstance(value, list):
            continue
        rewritten[key] = [
            _runtime_absolute_string(target_root, item)
            if isinstance(item, str) and _looks_like_repo_relative_path(item)
            else item
            for item in value
        ]
    return rewritten


def _absolute_text_path(
    value: str,
    *,
    repo_root: Path,
    target_root: Path,
    current_runtime_dir: Path,
) -> str:
    raw_value = value.strip()
    normalized = PurePosixPath(raw_value.replace("\\", "/"))
    normalized_text = str(normalized)
    meaningful_parts = [part for part in normalized.parts if part not in {"."}]
    if meaningful_parts and meaningful_parts[0] == "scripts":
        return _repo_absolute_string(repo_root, "/".join(meaningful_parts))
    if meaningful_parts and meaningful_parts[0] == "docs":
        return _runtime_absolute_string(target_root, "/".join(meaningful_parts))
    if meaningful_parts and meaningful_parts[0] in {
        "skills",
        "references",
    }:
        return str((target_root / str(PurePosixPath(*meaningful_parts)).replace("/", "\\")).resolve())
    if raw_value.startswith("./") or raw_value.startswith("../"):
        return str((current_runtime_dir / Path(*normalized.parts)).resolve())
    if _looks_like_repo_relative_path(raw_value):
        return _runtime_absolute_string(target_root, raw_value)
    return value


def _rewrite_link_block_content(
    text: str,
    *,
    repo_root: Path,
    target_root: Path,
    current_runtime_dir: Path,
) -> str:
    markdown_link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    inline_code_pattern = re.compile(r"`([^`]+)`")

    def _rewrite_inline_value(raw: str) -> str:
        return _absolute_text_path(
            raw,
            repo_root=repo_root,
            target_root=target_root,
            current_runtime_dir=current_runtime_dir,
        )

    text = markdown_link_pattern.sub(
        lambda match: f"[{match.group(1)}]({_rewrite_inline_value(match.group(2))})",
        text,
    )
    text = inline_code_pattern.sub(
        lambda match: f"`{_rewrite_inline_value(match.group(1))}`",
        text,
    )
    return text


def _rewrite_must_read_block_content(
    text: str,
    *,
    repo_root: Path,
    target_root: Path,
    current_runtime_dir: Path,
) -> str:
    inline_code_pattern = re.compile(r"`([^`]+)`")
    return inline_code_pattern.sub(
        lambda match: f'`{_absolute_text_path(match.group(1), repo_root=repo_root, target_root=target_root, current_runtime_dir=current_runtime_dir)}`',
        text,
    )


def _rewrite_tagged_blocks(
    text: str,
    *,
    repo_root: Path,
    target_root: Path,
    current_runtime_dir: Path,
) -> str:
    block_handlers = {
        "LINK": _rewrite_link_block_content,
        "MUST-READ": _rewrite_must_read_block_content,
    }
    rewritten = text
    for tag_name, handler in block_handlers.items():
        pattern = re.compile(rf"<{tag_name}>(.*?)</{tag_name}>", re.DOTALL)
        rewritten = pattern.sub(
            lambda match: f"<{tag_name}>"
            + handler(
                match.group(1),
                repo_root=repo_root,
                target_root=target_root,
                current_runtime_dir=current_runtime_dir,
            )
            + f"</{tag_name}>",
            rewritten,
        )
    return rewritten


def _quote_runtime_path_list_entries(frontmatter: str) -> str:
    lines = frontmatter.splitlines()
    quoted_lines: list[str] = []
    in_runtime_path_list = False
    runtime_list_keys = {"required_reads:", "required_outputs:"}
    for line in lines:
        stripped = line.strip()
        if stripped in runtime_list_keys:
            in_runtime_path_list = True
            quoted_lines.append(line)
            continue
        if in_runtime_path_list:
            if line.startswith("-") or line.startswith("  -"):
                prefix, value = line.split("-", 1)
                item = value.strip()
                if item and not (item.startswith('"') and item.endswith('"')):
                    escaped = item.replace("\\", "\\\\")
                    line = f'{prefix}- "{escaped}"'
                quoted_lines.append(line)
                continue
            in_runtime_path_list = False
        quoted_lines.append(line)
    return "\n".join(quoted_lines)


def _rewrite_text_runtime_paths(
    text: str,
    *,
    repo_root: Path,
    target_root: Path,
    current_runtime_dir: Path,
) -> str:
    normalized = text.replace("\r\n", "\n")
    if normalized.startswith("---\n"):
        parts = normalized.split("---\n", 2)
        if len(parts) >= 3:
            payload = yaml.safe_load(parts[1]) or {}
            if isinstance(payload, dict):
                rewritten_payload = _rewrite_frontmatter_lists(payload, target_root)
                frontmatter = yaml.safe_dump(rewritten_payload, sort_keys=False, allow_unicode=False).strip()
                frontmatter = _quote_runtime_path_list_entries(frontmatter)
                normalized = f"---\n{frontmatter}\n---\n" + parts[2]
    normalized = _rewrite_tagged_blocks(
        normalized,
        repo_root=repo_root,
        target_root=target_root,
        current_runtime_dir=current_runtime_dir,
    )
    lines: list[str] = []
    for line in normalized.splitlines():
        if line.startswith("Source: "):
            source_value = line[len("Source: ") :].strip()
            if source_value.startswith("`") and source_value.endswith("`"):
                raw = source_value[1:-1]
                if _looks_like_repo_relative_path(raw):
                    line = f'Source: `{_repo_absolute_string(repo_root, raw)}`'
            elif _looks_like_repo_relative_path(source_value):
                line = f'Source: {_repo_absolute_string(repo_root, source_value)}'
        elif "  - Source: `" in line and line.rstrip().endswith("`"):
            prefix, raw = line.split("`", 1)
            candidate, _ = raw.rsplit("`", 1)
            if _looks_like_repo_relative_path(candidate):
                line = (
                    f"{prefix}`"
                    f"{_absolute_text_path(candidate, repo_root=repo_root, target_root=target_root, current_runtime_dir=current_runtime_dir)}`"
                )
        lines.append(line)
    return "\n".join(lines)


def _render_runtime_text(
    src: Path,
    *,
    repo_root: Path,
    target_root: Path,
    generated_root: Path,
) -> str:
    runtime_path = target_root / src.relative_to(generated_root)
    return _rewrite_text_runtime_paths(
        src.read_text(encoding="utf-8"),
        repo_root=repo_root,
        target_root=target_root,
        current_runtime_dir=runtime_path.parent,
    ).rstrip("\n")


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


def _check_platform(generated_root: Path, target_root: Path, *, repo_root: Path) -> list[str]:
    issues: list[str] = []
    generated_files = [p for p in generated_root.rglob("*") if p.is_file()]
    for src in generated_files:
        rel = src.relative_to(generated_root)
        dst = target_root / rel
        if not dst.exists():
            issues.append(f"Missing deployed file: {dst.as_posix()}")
            continue
        if _render_runtime_text(
            src,
            repo_root=repo_root,
            target_root=target_root,
            generated_root=generated_root,
        ) != _read_text(dst):
            issues.append(f"Deployed drift: {dst.as_posix()}")
    return issues


def _plan_deploy(
    generated_root: Path,
    target_root: Path,
    *,
    repo_root: Path,
    force: bool,
) -> tuple[list[str], list[str], list[tuple[Path, Path, str]]]:
    changes: list[str] = []
    issues: list[str] = []
    pairs: list[tuple[Path, Path, str]] = []
    generated_files = [p for p in generated_root.rglob("*") if p.is_file()]
    for src in generated_files:
        rel = src.relative_to(generated_root)
        dst = target_root / rel
        rendered = _render_runtime_text(
            src,
            repo_root=repo_root,
            target_root=target_root,
            generated_root=generated_root,
        )
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
            issues.extend(_check_platform(generated_root, target_root, repo_root=root))
            continue
        changes, plan_issues, pairs = _plan_deploy(
            generated_root,
            target_root,
            repo_root=root,
            force=args.force,
        )
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
