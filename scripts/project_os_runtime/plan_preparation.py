"""Derive disposable task preparation data from a Git-tracked plan."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import time
from typing import Any

from .attempt import WHOLE_ATTEMPT_WALL_CLOCK_SECONDS, execution_binding_digest, normalize_runtime_grant
from .capabilities import DEFAULT_LOCAL_CAPABILITIES
try:
    from ..planning_dependencies import (
        DependencyContractError,
        parse_dependency_field,
        parse_task_id,
        validate_dependency_graph,
    )
except ImportError:
    from planning_dependencies import (
        DependencyContractError,
        parse_dependency_field,
        parse_task_id,
        validate_dependency_graph,
    )


_TASK_ROW_HEADER = ("task", "state", "workspace", "executor", "depends on", "required proof", "evidence")
_TASK_HEADING = re.compile(r"(?m)^###\s+Task\s+(\d+):\s*(.+?)\s*$")
_TASK_ID = re.compile(r"^Task\s+(\d+)$", re.IGNORECASE)
_SINGLE_DEPENDENCY = re.compile(r"^Task\s+(\d+)$", re.IGNORECASE)
_NAMED_DEPENDENCIES = re.compile(r"^Task\s+\d+(?:\s*,\s*Task\s+\d+)+$", re.IGNORECASE)
_NUMBERED_DEPENDENCIES = re.compile(r"^Tasks?\s+\d+(?:\s*,\s*\d+)+$", re.IGNORECASE)
_RANGE_DEPENDENCY = re.compile(r"^Tasks?\s+(\d+)\s*-\s*(?:Task\s+)?(\d+)$", re.IGNORECASE)
_BINDING_FIELDS = frozenset(
    {
        "repository_identity",
        "worktree",
        "expected_base",
        "session",
        "pane",
        "runtime_grant",
        "accepted_prerequisites",
    }
)


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
    try:
        return tuple(parse_dependency_field(_cell(value)))
    except DependencyContractError as exc:
        raise ValueError(str(exc)) from exc


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

    try:
        validate_dependency_graph({task_id: task.dependencies for task_id, task in tasks.items()})
    except DependencyContractError as exc:
        raise ValueError(str(exc)) from exc

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


def _frontmatter_value(text: str, name: str) -> str | None:
    match = re.match(r"(?ms)^---\s*\n(.*?)\n---\s*\n", text)
    if match is None:
        return None
    value = re.search(rf"(?im)^{re.escape(name)}:\s*(.+?)\s*$", match.group(1))
    return value.group(1).strip().strip("'\"") if value else None


def _bounded_task_text(text: str, task_id: str, title: str) -> str:
    match = re.search(
        rf"(?ims)^###\s+{re.escape(task_id)}:\s*[^\n]*\n(.*?)(?=^###\s+Task\s+\d+:|^##\s|\Z)",
        text,
    )
    if match is None:
        raise ValueError(f"missing task section: {task_id}")
    return f"{task_id}: {title.strip()}\n\n{match.group(1).strip()}"


def _write_set(body: str) -> list[str]:
    values: list[str] = []
    section = re.search(r"(?ims)^\*\*Files And Symbols:\*\*\s*\n(.*?)(?=^\*\*[^*\n]+:\*\*\s*$|\Z)", body)
    for line in (section.group(1) if section else "").splitlines():
        if not re.match(r"\s*-\s*(?:Create|Modify|Add|Update|Delete)", line, re.IGNORECASE):
            continue
        values.extend(item.split(":", 1)[0] for item in re.findall(r"`([^`]+)`", line))
    return list(dict.fromkeys(values)) or ["docs/superpowers/plans"]


def _runtime_grant(value: object) -> dict[str, Any]:
    if value is None:
        return {"turns": "native", "wall_clock_seconds": "native", "child_agents": "deny", "mcp_select": []}
    if not isinstance(value, Mapping):
        raise ValueError("runtime_grant must be a mapping")
    return normalize_runtime_grant(dict(value), executor="deepagents")


def _accepted_prerequisites(task: PlanTask, value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("accepted_prerequisites must be a mapping")
    accepted = {str(key): item for key, item in value.items()}
    for dependency in task.dependencies:
        binding = accepted.get(dependency)
        if not isinstance(binding, Mapping):
            raise ValueError(f"missing accepted prerequisite binding: {dependency}")
        if not isinstance(binding.get("accepted_revision"), str) or not binding["accepted_revision"].strip():
            raise ValueError(f"missing accepted revision: {dependency}")
        if not isinstance(binding.get("artifact_ref"), str) or not binding["artifact_ref"].strip():
            raise ValueError(f"missing artifact reference: {dependency}")
        if "artifact_available" in binding:
            raise ValueError("artifact_available is not an accepted prerequisite input")
    return accepted


def prepare_plan_lanes(
    plan_file: str | Path,
    task_ids: Sequence[str],
    runtime_bindings: Mapping[str, Any],
) -> list[dict[str, Any]]:
    plan_path = Path(plan_file)
    text = plan_path.read_text(encoding="utf-8")
    if (_frontmatter_value(text, "status") or "").casefold() != "active":
        raise ValueError("plan must be active before dispatch")
    if not isinstance(runtime_bindings, Mapping):
        raise ValueError("runtime bindings must be keyed by task ID")
    graph = parse_plan(text)
    selected = [_canonical_task_id(task_id) for task_id in task_ids]
    if not selected:
        raise ValueError("at least one task is required")
    if len(set(selected)) != len(selected):
        raise ValueError("duplicate selected task")
    unknown = sorted(set(selected) - set(graph.tasks))
    if unknown:
        raise ValueError(f"unknown selected task: {unknown[0]}")
    plan_identity = _frontmatter_value(text, "name") or plan_path.stem
    plan_revision = hashlib.sha256(text.encode("utf-8")).hexdigest()
    lanes: list[dict[str, Any]] = []
    for task_id in selected:
        task = graph.tasks[task_id]
        binding = runtime_bindings.get(task_id)
        if not isinstance(binding, Mapping):
            raise ValueError(f"missing runtime binding: {task_id}")
        extra = set(binding) - _BINDING_FIELDS
        missing = _BINDING_FIELDS - set(binding)
        if extra:
            raise ValueError(f"runtime binding contains plan-owned fields: {sorted(extra)[0]}")
        if missing:
            raise ValueError(f"runtime binding missing field: {sorted(missing)[0]}")
        if task.executor.casefold() != "deepagents":
            raise ValueError(f"unsupported task executor: {task.executor}")
        if not task.profile or task.profile.casefold() in {"unresolved", "none", "none (lead controller)"}:
            raise ValueError(f"task profile unresolved: {task_id}")
        accepted = _accepted_prerequisites(task, binding["accepted_prerequisites"])
        structurally_ready = task.state in {"pending", "active"} and all(
            graph.tasks[dependency].state == "completed" for dependency in task.dependencies
        )
        grant = _runtime_grant(binding["runtime_grant"])
        task_text = _bounded_task_text(text, task_id, task.title)
        descriptor = {
            "lane_id": task_id.lower().replace(" ", "-"),
            "repository_identity": binding["repository_identity"],
            "plan_identity": plan_identity,
            "plan_revision": plan_revision,
            "task": task_text,
            "executor": task.executor.casefold(),
            "profile": task.profile,
            "worktree": binding["worktree"],
            "expected_base": binding["expected_base"],
            "session": binding["session"],
            "pane": binding["pane"],
            "allowed_write_set": _write_set(task_text),
            "dependencies": list(task.dependencies),
            "dependency_ready": structurally_ready,
            "structurally_ready": structurally_ready,
            "accepted_prerequisites": accepted,
            "fixed_contracts": ["plan-to-dispatch-v1"],
            "mutable_resources": [task_id],
            "grant_turns": grant["turns"],
            "grant_wall_clock_seconds": grant["wall_clock_seconds"],
            "grant_child_agents": grant["delegation"]["child_agents"],
            "mcp_select": grant["mcp_select"],
            "runtime_grant": grant,
            "local_capabilities": list(DEFAULT_LOCAL_CAPABILITIES),
            "remaining_authorized_task_allowance": WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
            "attempt_deadline": time.monotonic() + WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
            "target": task_id,
            "name": task.title,
        }
        descriptor["execution_binding_digest"] = execution_binding_digest(descriptor)
        lanes.append(descriptor)
    return lanes


__all__ = [
    "PlanGraph",
    "PlanTask",
    "PreparedTask",
    "load_plan",
    "parse_plan",
    "prepare_lane_inputs",
    "prepare_plan_lanes",
    "prepare_task",
]
