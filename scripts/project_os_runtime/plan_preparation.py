"""Derive disposable task preparation data from a Git-tracked plan."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
from typing import Any


_TASK_ROW_HEADER = ("task", "state", "workspace", "executor", "depends on", "required proof", "evidence")
_TASK_HEADING = re.compile(r"(?m)^###\s+Task\s+(\d+):\s*(.+?)\s*$")
_TASK_ID = re.compile(r"^Task\s+(\d+)$", re.IGNORECASE)
_SINGLE_DEPENDENCY = re.compile(r"^Task\s+(\d+)$", re.IGNORECASE)
_NAMED_DEPENDENCIES = re.compile(r"^Task\s+\d+(?:\s*,\s*Task\s+\d+)+$", re.IGNORECASE)
_NUMBERED_DEPENDENCIES = re.compile(r"^Tasks?\s+\d+(?:\s*,\s*\d+)+$", re.IGNORECASE)
_RANGE_DEPENDENCY = re.compile(r"^Tasks?\s+(\d+)\s*-\s*(?:Task\s+)?(\d+)$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class PlanTask:
    task_id: str
    title: str
    state: str
    workspace: str
    executor: str
    profile: str
    dependencies: tuple[str, ...]
    required_proof: str
    evidence: str
    contract: str


@dataclass(frozen=True, slots=True)
class PlanGraph:
    plan_identity: str
    goal: str
    required_skills: str
    tasks: Mapping[str, PlanTask]


@dataclass(frozen=True, slots=True)
class PreparedTask:
    task_id: str
    dependencies: tuple[str, ...]
    prerequisites: tuple[Mapping[str, str | None], ...]
    structurally_ready: bool
    unresolved_prerequisites: tuple[str, ...]
    brief: str
    required_proof: str
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "dependencies": list(self.dependencies),
            "prerequisites": [dict(item) for item in self.prerequisites],
            "structurally_ready": self.structurally_ready,
            "unresolved_prerequisites": list(self.unresolved_prerequisites),
            "brief": self.brief,
            "required_proof": self.required_proof,
            "evidence": self.evidence,
        }


def _cell(value: str) -> str:
    return value.strip().strip("`").strip()


def _split_row(line: str) -> list[str] | None:
    if not line.lstrip().startswith("|"):
        return None
    return [item.strip() for item in line.strip().strip("|").split("|")]


def _canonical_task_id(value: str) -> str:
    match = _TASK_ID.fullmatch(_cell(value))
    if not match:
        raise ValueError(f"unsupported task ID: {value}")
    number = int(match.group(1))
    if number < 1:
        raise ValueError("task IDs must be positive")
    return f"Task {number}"


def _parse_dependencies(value: str) -> tuple[str, ...]:
    normalized = _cell(value)
    if not normalized or normalized.casefold() == "none":
        return ()
    match = _SINGLE_DEPENDENCY.fullmatch(normalized)
    if match:
        return (f"Task {int(match.group(1))}",)
    if _NAMED_DEPENDENCIES.fullmatch(normalized):
        return tuple(f"Task {int(number)}" for number in re.findall(r"\d+", normalized))
    if _NUMBERED_DEPENDENCIES.fullmatch(normalized):
        return tuple(f"Task {int(number)}" for number in re.findall(r"\d+", normalized))
    match = _RANGE_DEPENDENCY.fullmatch(normalized)
    if match:
        start, end = (int(item) for item in match.groups())
        if start > end:
            raise ValueError(f"dependency range is reversed: {value}")
        return tuple(f"Task {number}" for number in range(start, end + 1))
    raise ValueError(f"unsupported or partially parsed dependencies: {value}")


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
    )
    return match.group(1).strip() if match else ""


def _task_contracts(text: str) -> dict[str, tuple[str, str, str]]:
    matches = list(_TASK_HEADING.finditer(text))
    contracts: dict[str, tuple[str, str, str]] = {}
    for index, match in enumerate(matches):
        task_id = f"Task {int(match.group(1))}"
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        profile_match = re.search(
            r"(?im)^\*\*Template Profile:\*\*\s*$\n\s*-\s*Controller-selected:\s*`?([^`\r\n]+?)`?\s*$",
            body,
        )
        profile = profile_match.group(1).strip() if profile_match else "unresolved"
        contracts[task_id] = (match.group(2).strip(), profile, body)
    return contracts


def parse_plan(text: str) -> PlanGraph:
    lines = text.splitlines()
    header_index: int | None = None
    for index, line in enumerate(lines):
        cells = _split_row(line)
        if cells and tuple(_cell(item).casefold() for item in cells) == _TASK_ROW_HEADER:
            header_index = index
            break
    if header_index is None:
        raise ValueError("plan task ledger table not found")
    if header_index + 1 >= len(lines) or _split_row(lines[header_index + 1]) is None:
        raise ValueError("plan task ledger separator missing")

    contracts = _task_contracts(text)
    tasks: dict[str, PlanTask] = {}
    for line in lines[header_index + 2:]:
        if not line.strip():
            break
        cells = _split_row(line)
        if cells is None:
            break
        if len(cells) != len(_TASK_ROW_HEADER):
            raise ValueError("plan task ledger row has wrong column count")
        task_id = _canonical_task_id(cells[0])
        if task_id in tasks:
            raise ValueError(f"duplicate task ID: {task_id}")
        dependencies = _parse_dependencies(cells[4])
        title, profile, contract = contracts.get(task_id, (task_id, "unresolved", ""))
        tasks[task_id] = PlanTask(
            task_id=task_id,
            title=title,
            state=_cell(cells[1]).casefold(),
            workspace=_cell(cells[2]),
            executor=_cell(cells[3]),
            profile=profile,
            dependencies=dependencies,
            required_proof=_cell(cells[5]),
            evidence=_cell(cells[6]),
            contract=contract,
        )
    if not tasks:
        raise ValueError("plan task ledger has no rows")

    for task in tasks.values():
        for dependency in task.dependencies:
            if dependency not in tasks:
                raise ValueError(f"missing dependency reference: {task.task_id} -> {dependency}")
            if dependency == task.task_id:
                raise ValueError(f"self-dependency: {task.task_id}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise ValueError(f"dependency cycle includes {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in tasks[task_id].dependencies:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in tasks:
        visit(task_id)

    return PlanGraph(
        plan_identity=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        goal=_section(text, "Goal"),
        required_skills=next(
            (line.split(":", 1)[1].strip() for line in _section(text, "Execution Approach").splitlines() if line.strip().casefold().startswith("- required skills:")),
            "",
        ),
        tasks=tasks,
    )


def load_plan(source: str | os.PathLike[str]) -> PlanGraph:
    if isinstance(source, str) and ("\n" in source or "\r" in source):
        return parse_plan(source)
    path = Path(source)
    return parse_plan(path.read_text(encoding="utf-8"))


def prepare_task(graph: PlanGraph, task_id: str) -> PreparedTask:
    canonical_id = _canonical_task_id(task_id)
    try:
        task = graph.tasks[canonical_id]
    except KeyError as exc:
        raise ValueError(f"unknown selected task: {canonical_id}") from exc
    prerequisites = tuple(
        {
            "task": dependency,
            "recorded_state": graph.tasks[dependency].state,
            "evidence_ref": graph.tasks[dependency].evidence or None,
        }
        for dependency in task.dependencies
    )
    unresolved = tuple(
        item["task"]
        for item in prerequisites
        if item["recorded_state"] != "completed"
    )
    brief_parts = [f"{canonical_id}: {task.title}"]
    if graph.goal:
        brief_parts.extend(("", "Plan goal:", graph.goal))
    if task.contract:
        brief_parts.extend(("", "Task contract:", task.contract))
    brief_parts.extend(("", f"Recorded prerequisites: {', '.join(task.dependencies) or 'none'}"))
    if unresolved:
        brief_parts.append(f"Unresolved prerequisites: {', '.join(unresolved)}")
    if graph.required_skills:
        brief_parts.extend(("", f"Plan-wide requirements: {graph.required_skills}"))
    return PreparedTask(
        task_id=canonical_id,
        dependencies=task.dependencies,
        prerequisites=prerequisites,
        structurally_ready=not unresolved,
        unresolved_prerequisites=unresolved,
        brief="\n".join(brief_parts).strip(),
        required_proof=task.required_proof,
        evidence=task.evidence,
    )


def prepare_lane_inputs(
    source: str | os.PathLike[str] | PlanGraph,
    selected_task_ids: Sequence[str],
    runtime_inputs_by_task: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    graph = source if isinstance(source, PlanGraph) else load_plan(source)
    lanes: list[dict[str, Any]] = []
    for selected_task_id in selected_task_ids:
        prepared = prepare_task(graph, selected_task_id)
        task = graph.tasks[prepared.task_id]
        runtime = runtime_inputs_by_task.get(prepared.task_id)
        if not isinstance(runtime, Mapping):
            raise ValueError(f"resolved runtime inputs missing for {prepared.task_id}")
        lane = dict(runtime)
        supplied_plan_identity = lane.get("plan_identity")
        if supplied_plan_identity is not None and supplied_plan_identity != graph.plan_identity:
            raise ValueError(f"runtime input conflicts with plan identity for {prepared.task_id}")
        derived = {
            "lane_id": lane.get("lane_id", prepared.task_id),
            "plan_identity": graph.plan_identity,
            "task": prepared.brief,
            "executor": task.executor,
            "profile": task.profile,
            "dependencies": list(prepared.dependencies),
            "dependency_ready": prepared.structurally_ready,
        }
        for field in ("task", "executor", "profile", "dependencies", "dependency_ready"):
            if field in lane and lane[field] != derived[field]:
                raise ValueError(f"runtime input conflicts with plan-derived {field} for {prepared.task_id}")
        lane.update(derived)
        lane["plan_preparation"] = prepared.to_dict()
        lanes.append(lane)
    return lanes


__all__ = ["PlanGraph", "PlanTask", "PreparedTask", "load_plan", "parse_plan", "prepare_lane_inputs", "prepare_task"]
