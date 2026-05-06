"""
Generate platform-specific agent runtime artifacts from canonical repo sources.

Usage:
  python scripts/sync_agent_adapters.py
  python scripts/sync_agent_adapters.py --check
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys

import yaml


@dataclass(frozen=True)
class Mapping:
    source: str
    destination: str
    mode: str
    comment_prefix: str
    include_glob: str | None


GENERATED_BY = "scripts/sync_agent_adapters.py"


def _render_json_from_yaml(text: str) -> str:
    payload = yaml.safe_load(text)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def _provider_settings_to_codex_hooks(payload: dict) -> dict:
    hooks_payload: dict[str, list[dict[str, object]]] = {}
    events = payload.get("hooks", {}).get("events", {})
    if not isinstance(events, dict):
        return {"hooks": {}}
    for event in events.values():
        if not isinstance(event, dict) or not event.get("enabled"):
            continue
        provider_event = event.get("provider_event")
        commands = event.get("commands")
        if not isinstance(provider_event, str) or not provider_event.strip():
            continue
        if not isinstance(commands, list) or not commands:
            continue
        mapped_hooks: list[dict[str, object]] = []
        timeout_seconds = int(event.get("timeout_seconds", 60))
        for command in commands:
            if not isinstance(command, str) or not command.strip():
                continue
            mapped_hooks.append(
                {
                    "type": "command",
                    "command": command,
                    "timeout": timeout_seconds,
                    "statusMessage": "Validating repo contracts",
                }
            )
        if not mapped_hooks:
            continue
        hooks_payload.setdefault(provider_event, []).append({"hooks": mapped_hooks})
    return {"hooks": hooks_payload}


def _provider_settings_to_claude_settings(payload: dict) -> dict:
    hooks_payload: dict[str, list[dict[str, object]]] = {}
    events = payload.get("hooks", {}).get("events", {})
    if not isinstance(events, dict):
        return {"hooks": {}}
    for event in events.values():
        if not isinstance(event, dict) or not event.get("enabled"):
            continue
        provider_event = event.get("provider_event")
        commands = event.get("commands")
        if not isinstance(provider_event, str) or not provider_event.strip():
            continue
        if not isinstance(commands, list) or not commands:
            continue
        mapped_hooks: list[dict[str, object]] = []
        timeout_seconds = int(event.get("timeout_seconds", 60))
        for command in commands:
            if not isinstance(command, str) or not command.strip():
                continue
            mapped_hooks.append(
                {
                    "type": "command",
                    "command": command,
                    "timeout": timeout_seconds,
                }
            )
        if not mapped_hooks:
            continue
        hooks_payload.setdefault(provider_event, []).append({"hooks": mapped_hooks})
    return {"hooks": hooks_payload}


def _provider_settings_to_antigravity_settings(payload: dict) -> dict:
    hooks = payload.get("hooks", {})
    events = hooks.get("events", {}) if isinstance(hooks, dict) else {}
    fallback_rule = ""
    if isinstance(events, dict):
        task_end = events.get("task_end")
        if isinstance(task_end, dict):
            value = task_end.get("fallback_rule")
            if isinstance(value, str):
                fallback_rule = value
    return {
        "provider": "antigravity",
        "lifecycle_hooks_supported": False,
        "fallback": {
            "mode": "rules_workflows",
            "task_end_rule": fallback_rule,
        },
    }


def _strip_markdown_frontmatter(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return normalized
    parts = normalized.split("---\n", 2)
    if len(parts) < 3:
        return normalized
    return parts[2].lstrip("\n")


def _codex_rules_filename(path: Path) -> str:
    name = path.name
    if name.endswith("-rule.md"):
        return f"{name[:-len('-rule.md')]}.rules"
    if name.endswith(".md"):
        return f"{name[:-3]}.rules"
    return f"{name}.rules"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync agent adapter outputs.")
    parser.add_argument("--check", action="store_true", help="Fail on drift without writing.")
    parser.add_argument(
        "--adapters-root",
        default="adapters",
        help="Adapters directory relative to repo root.",
    )
    return parser.parse_args()


def _load_mapping(path: Path) -> tuple[str, list[Mapping]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid mapping yaml: {path}")
    platform = str(payload.get("platform", path.parent.name))
    mapping_items = payload.get("mappings")
    if not isinstance(mapping_items, list):
        raise ValueError(f"`mappings` must be a list in {path}")
    mappings: list[Mapping] = []
    for raw in mapping_items:
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid mapping entry in {path}")
        mappings.append(
            Mapping(
                source=str(raw["source"]),
                destination=str(raw["destination"]),
                mode=str(raw.get("mode", "copy_file")),
                comment_prefix=str(raw.get("comment_prefix", "#")),
                include_glob=str(raw["include_glob"]) if "include_glob" in raw else None,
            )
        )
    return platform, mappings


def _render_generated_block(source_rel: str) -> str:
    return (
        "<!--\n"
        "GENERATED FILE - DO NOT EDIT\n\n"
        f"Source: {source_rel}\n"
        f"Generated by: {GENERATED_BY}\n"
        "To update: edit canonical source, then run sync.\n"
        "-->\n\n"
    )


def _strip_generated_block(raw: str) -> str:
    marker = "<!--\nGENERATED FILE - DO NOT EDIT\n"
    if not raw.startswith(marker):
        legacy_marker = "# GENERATED FILE - do not edit directly.\n"
        if raw.startswith(legacy_marker):
            rest = raw[len(legacy_marker) :]
            legacy_source = "# Source: `"
            if rest.startswith(legacy_source):
                line_end = rest.find("\n")
                if line_end != -1:
                    rest = rest[line_end + 1 :]
            return rest.lstrip("\n")
        return raw
    end = raw.find("-->\n")
    if end == -1:
        return raw
    return raw[end + len("-->\n") :].lstrip("\n")


def _render_with_header(text: str, *, source_rel: str, prefix: str) -> str:
    del prefix
    header = _render_generated_block(source_rel)
    normalized = _strip_generated_block(text.replace("\r\n", "\n"))
    if not normalized.startswith("---\n"):
        return header + normalized
    parts = normalized.split("---\n", 2)
    if len(parts) < 3:
        return header + normalized
    frontmatter = f"---\n{parts[1]}---\n"
    body = parts[2].lstrip("\n")
    return f"{frontmatter}\n{header}{body}"


def _inject_json_generated_metadata(payload: dict, *, source_rel: str) -> dict:
    clean_payload = dict(payload)
    clean_payload.pop("_generated", None)
    clean_payload.pop("_source", None)
    clean_payload.pop("_generated_by", None)
    clean_payload.pop("_do_not_edit", None)
    return {
        "_generated": True,
        "_source": source_rel,
        "_generated_by": GENERATED_BY,
        "_do_not_edit": "Edit canonical source and run sync.",
        **clean_payload,
    }


def _normalized(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip("\n")


def _sync_file(root: Path, mapping: Mapping, *, check: bool) -> list[str]:
    src = root / mapping.source
    dst = root / mapping.destination
    if not src.exists():
        return [f"Missing source: {src.as_posix()}"]
    src_text = src.read_text(encoding="utf-8")
    source_rel = src.relative_to(root).as_posix()
    if mapping.mode == "render_json_from_yaml":
        payload = _inject_json_generated_metadata(yaml.safe_load(src_text) or {}, source_rel=source_rel)
        rendered = json.dumps(payload, indent=2) + "\n"
    elif mapping.mode == "render_codex_hooks_from_yaml":
        payload = _inject_json_generated_metadata(
            _provider_settings_to_codex_hooks(yaml.safe_load(src_text) or {}),
            source_rel=source_rel,
        )
        rendered = json.dumps(payload, indent=2) + "\n"
    elif mapping.mode == "render_claude_settings_from_yaml":
        payload = _inject_json_generated_metadata(
            _provider_settings_to_claude_settings(yaml.safe_load(src_text) or {}),
            source_rel=source_rel,
        )
        rendered = json.dumps(payload, indent=2) + "\n"
    elif mapping.mode == "render_antigravity_settings_from_yaml":
        payload = _inject_json_generated_metadata(
            _provider_settings_to_antigravity_settings(yaml.safe_load(src_text) or {}),
            source_rel=source_rel,
        )
        rendered = json.dumps(payload, indent=2) + "\n"
    else:
        rendered = _render_with_header(
            src_text,
            source_rel=source_rel,
            prefix=mapping.comment_prefix,
        )
    if check:
        if not dst.exists():
            return [f"Missing generated file: {dst.as_posix()}"]
        actual = dst.read_text(encoding="utf-8")
        if _normalized(actual) != _normalized(rendered):
            return [f"Drift detected: {dst.as_posix()}"]
        return []
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(rendered, encoding="utf-8")
    return []


def _sync_tree(root: Path, mapping: Mapping, *, check: bool) -> list[str]:
    src_root = root / mapping.source
    dst_root = root / mapping.destination
    if not src_root.exists():
        return [f"Missing source directory: {src_root.as_posix()}"]
    pattern = mapping.include_glob or "**/*"
    issues: list[str] = []
    files = [p for p in src_root.glob(pattern) if p.is_file()]
    for src in files:
        rel = src.relative_to(src_root)
        dst = dst_root / rel
        rendered = _render_with_header(
            src.read_text(encoding="utf-8"),
            source_rel=src.relative_to(root).as_posix(),
            prefix=mapping.comment_prefix,
        )
        if check:
            if not dst.exists():
                issues.append(f"Missing generated file: {dst.as_posix()}")
                continue
            actual = dst.read_text(encoding="utf-8")
            if _normalized(actual) != _normalized(rendered):
                issues.append(f"Drift detected: {dst.as_posix()}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(rendered, encoding="utf-8")
    if not check and dst_root.exists():
        generated = {p.relative_to(dst_root) for p in dst_root.rglob("*") if p.is_file()}
        expected = {p.relative_to(src_root) for p in files}
        for stale in generated - expected:
            (dst_root / stale).unlink(missing_ok=True)
    return issues


def _sync_codex_rules_tree(root: Path, mapping: Mapping, *, check: bool) -> list[str]:
    src_root = root / mapping.source
    dst_root = root / mapping.destination
    if not src_root.exists():
        return [f"Missing source directory: {src_root.as_posix()}"]
    pattern = mapping.include_glob or "*.md"
    issues: list[str] = []
    files = [p for p in src_root.glob(pattern) if p.is_file()]
    expected_paths: set[Path] = set()
    for src in files:
        dst = dst_root / _codex_rules_filename(src)
        expected_paths.add(dst.relative_to(dst_root))
        body = _strip_markdown_frontmatter(src.read_text(encoding="utf-8"))
        rendered = _render_with_header(
            body,
            source_rel=src.relative_to(root).as_posix(),
            prefix=mapping.comment_prefix,
        )
        if check:
            if not dst.exists():
                issues.append(f"Missing generated file: {dst.as_posix()}")
                continue
            actual = dst.read_text(encoding="utf-8")
            if _normalized(actual) != _normalized(rendered):
                issues.append(f"Drift detected: {dst.as_posix()}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(rendered, encoding="utf-8")
    if not check and dst_root.exists():
        generated = {p.relative_to(dst_root) for p in dst_root.rglob("*") if p.is_file()}
        for stale in generated - expected_paths:
            (dst_root / stale).unlink(missing_ok=True)
    return issues


def run() -> int:
    args = parse_args()
    root = repo_root()
    adapters_root = root / args.adapters_root
    mapping_files = sorted(adapters_root.glob("*/mapping.yaml"))
    if not mapping_files:
        print("No adapter mappings found.")
        return 1
    issues: list[str] = []
    for mapping_file in mapping_files:
        platform, mappings = _load_mapping(mapping_file)
        for mapping in mappings:
            if mapping.mode == "copy_tree":
                issues.extend(_sync_tree(root, mapping, check=args.check))
            elif mapping.mode == "render_codex_rules_tree":
                issues.extend(_sync_codex_rules_tree(root, mapping, check=args.check))
            else:
                issues.extend(_sync_file(root, mapping, check=args.check))
        print(f"Processed adapter: {platform}")
    if issues:
        print("Agent adapter sync check failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    if args.check:
        print("Agent adapter outputs are up to date.")
    else:
        print("Agent adapter outputs synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
