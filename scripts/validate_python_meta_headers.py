"""
@meta
name: validate_python_meta_headers
type: script
domain: validation
responsibility:
  - Validate module-level Python @meta docstring blocks for governed source folders.
  - Enforce required metadata keys and basic shape constraints.
inputs:
  - Python files under configured scan roots
outputs:
  - Exit status and validation report
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

REQUIRED_KEYS = {
    "name",
    "type",
    "domain",
    "responsibility",
    "inputs",
    "outputs",
    "lifecycle",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Python @meta docstring headers.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--paths",
        nargs="*",
        default=["src"],
        help="Relative directories to scan for Python files.",
    )
    return parser


def _extract_module_docstring(path: Path) -> str | None:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return ast.get_docstring(module, clean=False)


def _parse_meta_lines(docstring: str) -> dict[str, object]:
    result: dict[str, object] = {}
    lines = [line.rstrip() for line in docstring.splitlines()]
    if not lines or lines[0].strip() != "@meta":
        return result

    current_key: str | None = None
    for raw in lines[1:]:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("- ") and current_key:
            result.setdefault(current_key, [])
            if isinstance(result[current_key], list):
                result[current_key].append(line[2:].strip())
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value:
                result[current_key] = value
            else:
                result[current_key] = []
    return result


def validate_python_meta_headers(root: Path, relative_paths: list[str]) -> list[str]:
    issues: list[str] = []
    targets: list[Path] = []
    for rel in relative_paths:
        base = root / rel
        if base.exists():
            targets.extend(sorted(base.rglob("*.py")))

    for path in targets:
        doc = _extract_module_docstring(path)
        rel = path.relative_to(root).as_posix()
        if not doc:
            issues.append(f"{rel}: missing module docstring with @meta block")
            continue
        parsed = _parse_meta_lines(doc)
        if not parsed:
            issues.append(f"{rel}: missing or malformed @meta block")
            continue
        for key in REQUIRED_KEYS:
            if key not in parsed:
                issues.append(f"{rel}: missing @meta required key `{key}`")
        lifecycle = parsed.get("lifecycle")
        if isinstance(lifecycle, list) and not lifecycle:
            issues.append(f"{rel}: `lifecycle` must include `status`")
    return issues


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve()
    issues = validate_python_meta_headers(root, args.paths)
    if issues:
        print("Python @meta header validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Python @meta header validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
