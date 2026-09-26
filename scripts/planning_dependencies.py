"""Strict dependency parsing and graph validation for planning ledgers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import re
from typing import Any


class DependencyContractError(ValueError):
    """Raised when dependency syntax or graph structure is invalid."""


_TASK_ID = re.compile(r"Task\s+(\d+)", re.IGNORECASE)
_TASK_RANGE = re.compile(r"Tasks\s+(\d+)\s*[-–]\s*(\d+)", re.IGNORECASE)
_TASK_LIST = re.compile(r"Tasks?\s+\d+(?:\s*,\s*(?:Task\s+)?\d+)+", re.IGNORECASE)


def parse_task_id(value: str) -> str:
    if not isinstance(value, str):
        raise DependencyContractError("task ID must be a string")
    match = _TASK_ID.fullmatch(value.strip())
    if match is None:
        raise DependencyContractError(f"unsupported task ID: {value!r}")
    return f"Task {int(match.group(1))}"


def parse_dependency_field(value: str | None) -> list[str]:
    if value is None or not value.strip() or value.strip().casefold() in {"none", "n/a"}:
        return []

    if _TASK_LIST.fullmatch(value.strip()):
        return [f"Task {number}" for number in re.findall(r"\d+", value)]

    dependencies: list[str] = []
    for token in value.split(","):
        token = token.strip()
        task_match = _TASK_ID.fullmatch(token)
        if task_match is not None:
            dependencies.append(f"Task {int(task_match.group(1))}")
            continue
        range_match = _TASK_RANGE.fullmatch(token)
        if range_match is None:
            raise DependencyContractError(f"unsupported dependency syntax: {value!r}")
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        if end < start:
            raise DependencyContractError(f"descending dependency range: {token!r}")
        dependencies.extend(f"Task {number}" for number in range(start, end + 1))
    return dependencies


def validate_dependency_graph(
    tasks: Mapping[str, Iterable[str]] | Iterable[Mapping[str, Any]],
) -> None:
    if isinstance(tasks, Mapping):
        entries = list(tasks.items())
    else:
        entries = []
        for item in tasks:
            if not isinstance(item, Mapping):
                raise DependencyContractError("task record must be a mapping")
            task_id = item.get("task") or item.get("task_id")
            if not isinstance(task_id, str):
                raise DependencyContractError("task record requires task ID")
            dependencies = item.get("dependencies", [])
            entries.append((task_id, dependencies))

    graph: dict[str, tuple[str, ...]] = {}
    for raw_task_id, raw_dependencies in entries:
        task_id = parse_task_id(str(raw_task_id))
        if task_id in graph:
            raise DependencyContractError(f"duplicate task ID: {task_id}")
        if isinstance(raw_dependencies, str):
            dependencies = tuple(parse_dependency_field(raw_dependencies))
        else:
            dependencies = tuple(parse_task_id(str(item)) for item in raw_dependencies)
        if len(set(dependencies)) != len(dependencies):
            raise DependencyContractError(f"duplicate dependency: {task_id}")
        if task_id in dependencies:
            raise DependencyContractError(f"self-dependency: {task_id}")
        graph[task_id] = dependencies

    missing = sorted({dependency for dependencies in graph.values() for dependency in dependencies if dependency not in graph})
    if missing:
        raise DependencyContractError(f"missing task reference: {missing[0]}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise DependencyContractError(f"dependency cycle at: {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in graph[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        visit(task_id)


__all__ = [
    "DependencyContractError",
    "parse_dependency_field",
    "parse_task_id",
    "validate_dependency_graph",
]
