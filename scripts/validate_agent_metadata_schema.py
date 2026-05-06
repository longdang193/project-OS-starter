"""
Validate canonical metadata schema for skills, rules, and workflows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate skills/rules/workflows metadata schema.")
    parser.add_argument("--repo-root", default=str(repo_root()))
    return parser.parse_args()


def _extract_frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    payload = yaml.safe_load(parts[1]) if parts[1].strip() else {}
    if not isinstance(payload, dict):
        return None
    return payload


def _require_list(meta: dict[str, Any], key: str, findings: list[Finding], rel: str) -> None:
    value = meta.get(key)
    if not isinstance(value, list):
        findings.append(Finding("agent_metadata_schema_error", rel, f"`{key}` must be a list."))


def _require_string(meta: dict[str, Any], key: str, findings: list[Finding], rel: str) -> None:
    value = meta.get(key)
    if not isinstance(value, str) or not value.strip():
        findings.append(Finding("agent_metadata_schema_error", rel, f"`{key}` must be a non-empty string."))


def validate(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    # Skills
    for path in sorted((root / ".agents" / "skills").glob("*/SKILL.md")):
        rel = path.relative_to(root).as_posix()
        meta = _extract_frontmatter(path)
        if meta is None:
            findings.append(Finding("agent_metadata_schema_error", rel, "missing YAML frontmatter."))
            continue
        for key in ("name", "description"):
            _require_string(meta, key, findings, rel)
        _require_list(meta, "allowed-tools", findings, rel)
        hooks = meta.get("hooks")
        if not isinstance(hooks, dict):
            findings.append(Finding("agent_metadata_schema_error", rel, "`hooks` must be an object with `pre` and `post` lists."))
        else:
            if not isinstance(hooks.get("pre"), list):
                findings.append(Finding("agent_metadata_schema_error", rel, "`hooks.pre` must be a list."))
            if not isinstance(hooks.get("post"), list):
                findings.append(Finding("agent_metadata_schema_error", rel, "`hooks.post` must be a list."))
        _require_list(meta, "required_reads", findings, rel)
        _require_list(meta, "tags", findings, rel)

    # Rules
    rules_root = root / "docs" / "operating_system" / "rules"
    for path in sorted(rules_root.glob("*.md")):
        rel = path.relative_to(root).as_posix()
        meta = _extract_frontmatter(path)
        if meta is None:
            findings.append(Finding("agent_metadata_schema_error", rel, "missing YAML frontmatter."))
            continue
        for key in ("name", "description"):
            _require_string(meta, key, findings, rel)
        if not isinstance(meta.get("alwaysApply"), bool):
            findings.append(Finding("agent_metadata_schema_error", rel, "`alwaysApply` must be boolean."))
        _require_list(meta, "required_reads", findings, rel)
        _require_list(meta, "tags", findings, rel)

    # Workflows
    workflows_root = root / "docs" / "operating_system" / "workflows"
    for path in sorted(workflows_root.glob("*.md")):
        rel = path.relative_to(root).as_posix()
        meta = _extract_frontmatter(path)
        if meta is None:
            findings.append(Finding("agent_metadata_schema_error", rel, "missing YAML frontmatter."))
            continue
        for key in ("name", "description"):
            _require_string(meta, key, findings, rel)
        _require_list(meta, "required_reads", findings, rel)
        _require_list(meta, "related_skills", findings, rel)
        _require_list(meta, "tags", findings, rel)

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).resolve()
    findings = validate(root)
    if findings:
        print("Agent metadata schema validation failed:")
        for finding in findings:
            print(f"- {finding.category}: {finding.path} - {finding.message}")
        return 1
    print("Agent metadata schema validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

