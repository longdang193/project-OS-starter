"""
Deploy generated agent runtime artifacts to user home runtime targets.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path, PurePosixPath
import re
import shutil

import yaml

PLATFORM_TARGETS = {
    "codex": Path.home() / ".codex",
    "claude": Path.home() / ".claude",
    "antigravity": Path.home() / ".gemini" / "antigravity",
}

SHARED_SKILLS_TARGET = Path.home() / ".agents" / "skills"
SHARED_SKILL_MARKER = ".project-os-managed"

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
    parser.add_argument(
        "--adopt-shared-skill",
        metavar="NAME",
        help="Explicitly adopt one differing unmarked shared skill.",
    )
    parser.add_argument(
        "--rewrite-mode",
        choices=["relative", "hardcode"],
        default="relative",
        help="Whether repo-relative runtime paths stay relative or are rewritten to absolute hardcoded paths.",
    )
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


def _rewrite_frontmatter_lists(
    meta: dict[str, object],
    target_root: Path,
    *,
    rewrite_mode: str,
) -> dict[str, object]:
    rewritten = dict(meta)
    if rewrite_mode != "hardcode":
        return rewritten
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
    rewrite_mode: str,
) -> str:
    if rewrite_mode != "hardcode":
        return text
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
    rewrite_mode: str = "relative",
) -> str:
    normalized = text.replace("\r\n", "\n")
    if normalized.startswith("---\n"):
        parts = normalized.split("---\n", 2)
        if len(parts) >= 3:
            payload = yaml.safe_load(parts[1]) or {}
            if isinstance(payload, dict):
                rewritten_payload = _rewrite_frontmatter_lists(
                    payload,
                    target_root,
                    rewrite_mode=rewrite_mode,
                )
                frontmatter = yaml.safe_dump(rewritten_payload, sort_keys=False, allow_unicode=False).strip()
                frontmatter = _quote_runtime_path_list_entries(frontmatter)
                normalized = f"---\n{frontmatter}\n---\n" + parts[2]
    normalized = _rewrite_tagged_blocks(
        normalized,
        repo_root=repo_root,
        target_root=target_root,
        current_runtime_dir=current_runtime_dir,
        rewrite_mode=rewrite_mode,
    )
    if rewrite_mode != "hardcode":
        return normalized
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
    rewrite_mode: str,
) -> str:
    runtime_path = target_root / src.relative_to(generated_root)
    return _rewrite_text_runtime_paths(
        src.read_text(encoding="utf-8"),
        repo_root=repo_root,
        target_root=target_root,
        current_runtime_dir=runtime_path.parent,
        rewrite_mode=rewrite_mode,
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
    return "<!--" in text and "GENERATED FILE - DO NOT EDIT" in text


RUNTIME_DEPLOY_EXCLUDE_PREFIXES = {
    "codex": ("skills/",),
}


def _runtime_deploy_exclude_prefixes(platform: str) -> tuple[str, ...]:
    return RUNTIME_DEPLOY_EXCLUDE_PREFIXES.get(platform, ())


def _runtime_path_is_excluded(platform: str, relative_path: PurePosixPath) -> bool:
    relative_text = relative_path.as_posix()
    for prefix in _runtime_deploy_exclude_prefixes(platform):
        normalized_prefix = prefix.rstrip("/")
        if relative_text == normalized_prefix or relative_text.startswith(f"{normalized_prefix}/"):
            return True
    return False


def _iter_generated_runtime_files(platform: str, generated_root: Path) -> list[Path]:
    return [
        src
        for src in generated_root.rglob("*")
        if src.is_file()
        and not _runtime_path_is_excluded(
            platform,
            PurePosixPath(src.relative_to(generated_root).as_posix()),
        )
    ]


def _runtime_owned_files(
    generated_root: Path,
    target_root: Path,
    platform: str = "",
) -> set[Path]:
    return {
        target_root / src.relative_to(generated_root)
        for src in _iter_generated_runtime_files(platform, generated_root)
    }


def _runtime_excluded_managed_files(
    generated_root: Path,
    target_root: Path,
    platform: str = "",
) -> set[Path]:
    return {
        target_root / src.relative_to(generated_root)
        for src in generated_root.rglob("*")
        if src.is_file()
        and _runtime_path_is_excluded(
            platform,
            PurePosixPath(src.relative_to(generated_root).as_posix()),
        )
    }


def _runtime_managed_roots(generated_root: Path, target_root: Path) -> set[Path]:
    roots: set[Path] = set()
    for src in generated_root.rglob("*"):
        if not src.is_file():
            continue
        relative = src.relative_to(generated_root)
        if relative.parts[0] == "skills" and len(relative.parts) > 1:
            roots.add(target_root / relative.parts[0] / relative.parts[1])
            continue
        roots.add(target_root / relative.parts[0])
    return roots


def _runtime_should_ignore_existing_path(platform: str, target_root: Path, candidate: Path) -> bool:
    relative = candidate.relative_to(target_root).as_posix()
    if platform == "codex":
        if relative == "rules/default.rules":
            return True
        if relative.startswith("skills/.system/"):
            return True
    return False


def _runtime_stale_generated_files(
    generated_root: Path,
    target_root: Path,
    platform: str = "",
) -> list[Path]:
    owned_files = _runtime_owned_files(generated_root, target_root, platform=platform)
    excluded_managed_files = _runtime_excluded_managed_files(
        generated_root,
        target_root,
        platform=platform,
    )
    stale: list[Path] = []
    for managed_root in _runtime_managed_roots(generated_root, target_root):
        if managed_root.is_file():
            candidates = [managed_root]
        elif managed_root.is_dir():
            candidates = [path for path in managed_root.rglob("*") if path.is_file()]
        else:
            continue
        for candidate in candidates:
            if candidate in owned_files:
                continue
            try:
                candidate.relative_to(target_root / ".backups")
                continue
            except ValueError:
                pass
            if candidate in excluded_managed_files:
                stale.append(candidate)
                continue
            if _runtime_should_ignore_existing_path(platform, target_root, candidate):
                continue
            if not _looks_generated(candidate):
                stale.append(candidate)
    return stale
def _check_platform(
    generated_root: Path,
    target_root: Path,
    *,
    repo_root: Path,
    rewrite_mode: str,
    platform: str = "",
) -> list[str]:
    issues: list[str] = []
    generated_files = _iter_generated_runtime_files(platform, generated_root)
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
            rewrite_mode=rewrite_mode,
        ) != _read_text(dst):
            issues.append(f"Deployed drift: {dst.as_posix()}")
    for stale in _runtime_stale_generated_files(generated_root, target_root, platform=platform):
        issues.append(f"Stale deployed file: {stale.as_posix()}")
    return issues


def _plan_deploy(
    generated_root: Path,
    target_root: Path,
    *,
    repo_root: Path,
    force: bool,
    rewrite_mode: str,
    platform: str = "",
) -> tuple[list[str], list[str], list[tuple[Path | None, Path, str | None]]]:
    changes: list[str] = []
    issues: list[str] = []
    pairs: list[tuple[Path | None, Path, str | None]] = []
    generated_files = _iter_generated_runtime_files(platform, generated_root)
    for src in generated_files:
        rel = src.relative_to(generated_root)
        dst = target_root / rel
        rendered = _render_runtime_text(
            src,
            repo_root=repo_root,
            target_root=target_root,
            generated_root=generated_root,
            rewrite_mode=rewrite_mode,
        )
        if dst.exists():
            if rendered == _read_text(dst):
                continue
            if not force and not _looks_generated(dst):
                issues.append(
                    f"Refusing to overwrite non-generated runtime file without --force: {dst.as_posix()}"
                )
                continue
            changes.append(f"update: {dst.as_posix()}")
        else:
            changes.append(f"create: {dst.as_posix()}")
        pairs.append((src, dst, rendered))
    for stale in _runtime_stale_generated_files(generated_root, target_root, platform=platform):
        changes.append(f"remove: {stale.as_posix()}")
        pairs.append((None, stale, None))
    return changes, issues, pairs


def _resolved_targets(raw_target: str) -> list[str]:
    if raw_target == "all":
        return list(PLATFORM_TARGETS.keys())
    canonical = TARGET_ALIASES.get(raw_target, raw_target)
    return [canonical]


def _repo_skill_names(skills_root: Path) -> set[str]:
    return {
        path.name
        for path in skills_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    }


def _shared_skill_marker(skills_root: Path, skill_name: str) -> dict[str, object]:
    return {
        "schema": 1,
        "source_root": str(skills_root.parent.parent.resolve()),
        "source_rel": f".agents/skills/{skill_name}",
    }


def _shared_skill_marker_path(target_root: Path, skill_name: str) -> Path:
    return target_root / skill_name / SHARED_SKILL_MARKER


def _read_shared_skill_marker(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _shared_skill_is_owned(skills_root: Path, target_root: Path, skill_name: str) -> bool:
    return _read_shared_skill_marker(_shared_skill_marker_path(target_root, skill_name)) == _shared_skill_marker(
        skills_root,
        skill_name,
    )


def _shared_skill_source_files(skills_root: Path, skill_name: str) -> list[Path]:
    return [
        src
        for src in (skills_root / skill_name).rglob("*")
        if src.is_file() and src.relative_to(skills_root / skill_name).as_posix() != SHARED_SKILL_MARKER
    ]


def _shared_skill_marker_text(skills_root: Path, skill_name: str) -> str:
    return json.dumps(_shared_skill_marker(skills_root, skill_name), indent=2, sort_keys=True)


def _shared_skill_expected_files(skills_root: Path, target_root: Path, skill_name: str) -> set[Path]:
    expected = {
        target_root / skill_name / src.relative_to(skills_root / skill_name)
        for src in _shared_skill_source_files(skills_root, skill_name)
    }
    expected.add(_shared_skill_marker_path(target_root, skill_name))
    return expected


def _shared_skill_owned_files(skills_root: Path, target_root: Path) -> set[Path]:
    owned: set[Path] = set()
    for skill_name in _repo_skill_names(skills_root):
        if _shared_skill_is_owned(skills_root, target_root, skill_name):
            owned.update(_shared_skill_expected_files(skills_root, target_root, skill_name))
    return owned


def _shared_skill_stale_files(skills_root: Path, target_root: Path) -> list[Path]:
    stale: list[Path] = []
    if not target_root.is_dir():
        return stale
    source_names = _repo_skill_names(skills_root)
    for deployed_root in target_root.iterdir():
        if not deployed_root.is_dir():
            continue
        skill_name = deployed_root.name
        marker = _read_shared_skill_marker(deployed_root / SHARED_SKILL_MARKER)
        if marker is None:
            continue
        if marker != _shared_skill_marker(skills_root, skill_name):
            continue
        owned_files = (
            _shared_skill_expected_files(skills_root, target_root, skill_name)
            if skill_name in source_names
            else set()
        )
        for candidate in deployed_root.rglob("*"):
            if candidate.is_file() and candidate not in owned_files:
                stale.append(candidate)
    return stale


def _check_shared_skills(skills_root: Path, target_root: Path) -> list[str]:
    issues: list[str] = []
    for skill_name in sorted(_repo_skill_names(skills_root)):
        deployed_root = target_root / skill_name
        if deployed_root.exists() and not _shared_skill_is_owned(skills_root, target_root, skill_name):
            source_files = _shared_skill_source_files(skills_root, skill_name)
            if all(
                (deployed_root / src.relative_to(skills_root / skill_name)).is_file()
                and _read_text(deployed_root / src.relative_to(skills_root / skill_name)) == _read_text(src)
                for src in source_files
            ) and {path.relative_to(deployed_root).as_posix() for path in deployed_root.rglob("*") if path.is_file()} == {
                src.relative_to(skills_root / skill_name).as_posix() for src in source_files
            }:
                continue
            issues.append(f"Unowned shared skill collision: {deployed_root.as_posix()}")
            continue
        for src in (skills_root / skill_name).rglob("*"):
            if not src.is_file() or src.name == SHARED_SKILL_MARKER:
                continue
            dst = target_root / skill_name / src.relative_to(skills_root / skill_name)
            if not dst.exists():
                issues.append(f"Missing deployed shared skill file: {dst.as_posix()}")
                continue
            if _read_text(src) != _read_text(dst):
                issues.append(f"Deployed shared skill drift: {dst.as_posix()}")
    for stale in _shared_skill_stale_files(skills_root, target_root):
        issues.append(f"Stale deployed shared skill file: {stale.as_posix()}")
    return issues


def _plan_shared_skill_deploy(
    skills_root: Path,
    target_root: Path,
    *,
    force: bool,
    adopt_shared_skill: str | None = None,
) -> tuple[list[str], list[str], list[tuple[Path | None, Path, str | None]]]:
    changes: list[str] = []
    issues: list[str] = []
    pairs: list[tuple[Path | None, Path, str | None]] = []
    source_names = _repo_skill_names(skills_root)
    if adopt_shared_skill is not None and adopt_shared_skill not in source_names:
        issues.append(f"Unknown shared skill for adoption: {adopt_shared_skill}")
    for skill_name in sorted(source_names):
        source_files = _shared_skill_source_files(skills_root, skill_name)
        deployed_root = target_root / skill_name
        owned = _shared_skill_is_owned(skills_root, target_root, skill_name)
        unmarked_identical = False
        if deployed_root.exists() and not owned:
            deployed_files = {
                path.relative_to(deployed_root).as_posix(): path
                for path in deployed_root.rglob("*")
                if path.is_file() and path.name != SHARED_SKILL_MARKER
            }
            source_by_relative = {
                src.relative_to(skills_root / skill_name).as_posix(): src for src in source_files
            }
            unmarked_identical = set(deployed_files) == set(source_by_relative) and all(
                _read_text(deployed_files[relative]) == _read_text(source_by_relative[relative])
                for relative in source_by_relative
            )
            if not unmarked_identical and adopt_shared_skill != skill_name:
                issues.append(
                    f"Refusing unowned shared skill collision without --adopt-shared-skill {skill_name}: {deployed_root.as_posix()}"
                )
                continue
        for src in source_files:
            dst = target_root / skill_name / src.relative_to(skills_root / skill_name)
            rendered = _read_text(src)
            if dst.exists():
                if rendered == _read_text(dst):
                    continue
                changes.append(f"update: {dst.as_posix()}")
            else:
                changes.append(f"create: {dst.as_posix()}")
            pairs.append((src, dst, rendered))
        marker_path = _shared_skill_marker_path(target_root, skill_name)
        marker_text = _shared_skill_marker_text(skills_root, skill_name)
        if not owned or not marker_path.exists():
            changes.append(f"{'update' if marker_path.exists() else 'create'}: {marker_path.as_posix()}")
            pairs.append((None, marker_path, marker_text))
    for stale in _shared_skill_stale_files(skills_root, target_root):
        changes.append(f"remove: {stale.as_posix()}")
        pairs.append((None, stale, None))
    return changes, issues, pairs


def run() -> int:
    args = parse_args()
    root = repo_root()
    targets = _resolved_targets(args.target)
    issues: list[str] = []
    shared_skills_root = root / ".agents" / "skills"
    if args.check:
        issues.extend(_check_shared_skills(shared_skills_root, SHARED_SKILLS_TARGET))
    else:
        changes, plan_issues, pairs = _plan_shared_skill_deploy(
            shared_skills_root,
            SHARED_SKILLS_TARGET,
            force=args.force,
            adopt_shared_skill=args.adopt_shared_skill,
        )
        issues.extend(plan_issues)
        if not plan_issues:
            if args.dry_run:
                print(f"[dry-run] shared skills -> {SHARED_SKILLS_TARGET.as_posix()}")
                for change in changes:
                    print(f"- {change}")
            else:
                backup_root: Path | None = None
                if args.backup:
                    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
                    backup_root = SHARED_SKILLS_TARGET / ".backups" / stamp
                for src, dst, rendered in pairs:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if backup_root is not None and dst.exists():
                        backup_path = backup_root / dst.relative_to(SHARED_SKILLS_TARGET)
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(dst, backup_path)
                    if src is None:
                        if rendered is None:
                            dst.unlink(missing_ok=True)
                        else:
                            dst.write_text(rendered + "\n", encoding="utf-8")
                        continue
                    dst.write_text(rendered + "\n", encoding="utf-8")
                print(
                    f"Deployed shared skills -> {SHARED_SKILLS_TARGET.as_posix()} ({len(pairs)} changed)"
                )
    for platform in targets:
        generated_root = root / "generated_agents" / platform
        if not generated_root.exists():
            issues.append(f"Missing generated platform directory: {generated_root.as_posix()}")
            continue
        target_root = PLATFORM_TARGETS[platform]
        if args.check:
            issues.extend(
                _check_platform(
                    generated_root,
                    target_root,
                    repo_root=root,
                    rewrite_mode=args.rewrite_mode,
                    platform=platform,
                )
            )
            continue
        changes, plan_issues, pairs = _plan_deploy(
            generated_root,
            target_root,
            repo_root=root,
            force=args.force,
            rewrite_mode=args.rewrite_mode,
            platform=platform,
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
        for src, dst, rendered in pairs:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if backup_root is not None and dst.exists():
                backup_path = backup_root / dst.relative_to(target_root)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup_path)
            if src is None:
                dst.unlink(missing_ok=True)
                continue
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
