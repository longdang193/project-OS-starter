"""Derive disposable task preparation data from a Git-tracked plan."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
from typing import Any

from .attempt import execution_binding_digest, normalize_runtime_grant
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
EXECUTION_ELIGIBLE_STATES = frozenset({"pending", "active"})
_SHARED_CONSTRAINT_LABELS = (
    "Required skills",
    "Preauthorized local actions",
    "User-approval actions",
    "Parallel ownership",
)
_REQUIRED_BINDING_FIELDS = frozenset(
    {
        "repository_identity",
        "worktree",
        "expected_base",
        "session",
        "pane",
        "runtime_grant",
        "allowed_write_set",
        "fixed_contracts",
        "mutable_resources",
        "local_capabilities",
        "remaining_authorized_task_allowance",
        "attempt_deadline",
        "accepted_prerequisites",
    }
)
_OPTIONAL_BINDING_FIELDS = frozenset({"prior_attempt_known", "codex_home", "target", "name"})
_BINDING_FIELDS = _REQUIRED_BINDING_FIELDS | _OPTIONAL_BINDING_FIELDS


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
    shared_constraints: tuple[tuple[str, str], ...]
    tasks: Mapping[str, PlanTask]


@dataclass(frozen=True, slots=True)
class PreparedTask:
    task_id: str
    execution_eligible: bool
    eligibility_reason: str | None
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
            "execution_eligible": self.execution_eligible,
            "eligibility_reason": self.eligibility_reason,
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


def _shared_constraints(text: str) -> tuple[tuple[str, str], ...]:
    constraints = []
    for label in _SHARED_CONSTRAINT_LABELS:
        prefix = f"- {label}:"
        value = next(
            (
                line.split(":", 1)[1].strip()
                for line in text.splitlines()
                if line.strip().casefold().startswith(prefix.casefold())
            ),
            "",
        )
        if value:
            constraints.append((label, value))
    return tuple(constraints)


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
    task_rows: list[tuple[str, PlanTask]] = []
    for line in lines[header_index + 2:]:
        if not line.strip():
            break
        cells = _split_row(line)
        if cells is None:
            break
        if len(cells) != len(_TASK_ROW_HEADER):
            raise ValueError("plan task ledger row has wrong column count")
        task_id = _canonical_task_id(cells[0])
        dependencies = _parse_dependencies(cells[4])
        title, profile, contract = contracts.get(task_id, (task_id, "unresolved", ""))
        task_rows.append((
            task_id,
            PlanTask(
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
            ),
        ))
    if not task_rows:
        raise ValueError("plan task ledger has no rows")

    try:
        validate_dependency_graph(
            [
                {"task": task_id, "dependencies": task.dependencies}
                for task_id, task in task_rows
            ]
        )
    except DependencyContractError as exc:
        raise ValueError(str(exc)) from exc
    tasks = {task_id: task for task_id, task in task_rows}

    return PlanGraph(
        plan_identity=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        goal=_section(text, "Goal"),
        shared_constraints=_shared_constraints(_section(text, "Execution Approach")),
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
    execution_eligible = task.state in EXECUTION_ELIGIBLE_STATES
    eligibility_reason = (
        None
        if execution_eligible
        else f"selected task is not execution-eligible: {task.state}"
    )
    brief_parts = [f"{canonical_id}: {task.title}"]
    if graph.goal:
        brief_parts.extend(("", "Plan goal:", graph.goal))
    if task.contract:
        brief_parts.extend(("", "Task contract:", task.contract))
    brief_parts.extend(("", f"Recorded prerequisites: {', '.join(task.dependencies) or 'none'}"))
    if unresolved:
        brief_parts.append(f"Unresolved prerequisites: {', '.join(unresolved)}")
    if graph.shared_constraints:
        brief_parts.extend(
            (
                "",
                "Plan-wide shared constraints:",
                "\n".join(f"- {label}: {value}" for label, value in graph.shared_constraints),
            )
        )
    return PreparedTask(
        task_id=canonical_id,
        execution_eligible=execution_eligible,
        eligibility_reason=eligibility_reason,
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
    bindings: dict[str, dict[str, Any]] = {}
    for selected_task_id in selected_task_ids:
        prepared = prepare_task(graph, selected_task_id)
        runtime = runtime_inputs_by_task.get(prepared.task_id)
        if not isinstance(runtime, Mapping):
            raise ValueError(f"resolved runtime inputs missing for {prepared.task_id}")
        for field in ("lane_id", "plan_identity", "task", "executor", "profile", "dependencies", "dependency_ready", "structurally_ready"):
            if field in runtime:
                if field == "plan_identity":
                    raise ValueError(f"runtime input conflicts with plan identity for {prepared.task_id}")
                raise ValueError(f"runtime input conflicts with plan-derived {field} for {prepared.task_id}")
        bindings[prepared.task_id] = _canonical_runtime_binding(runtime)
    text, graph, plan_identity, plan_source = _source_parts(source)
    status = _frontmatter_value(text, "status") if text is not None else None
    if status is not None and status.casefold() != "active":
        raise ValueError("plan must be active before dispatch")
    return _prepare_plan_lanes(text, graph, plan_identity, plan_source, tuple(selected_task_ids), bindings)


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


def _contract_section(body: str, heading: str) -> str:
    match = re.search(
        rf"(?ims)^\*\*{re.escape(heading)}:\*\*\s*$\n(.*?)(?=^\*\*[^*\n]+:\*\*\s*$|^##\s|\Z)",
        body,
    )
    return match.group(1).strip() if match else ""


def _worker_brief(
    text: str | None,
    task: PlanTask,
    prepared: PreparedTask,
    accepted: Mapping[str, Any],
    plan_goal: str,
    shared_constraints: Sequence[tuple[str, str]],
) -> str:
    selected = (
        _bounded_task_text(text, prepared.task_id, task.title)
        if text is not None
        else f"{prepared.task_id}: {task.title}\n\n{task.contract.strip()}".strip()
    )
    prerequisites = []
    for dependency in task.dependencies:
        binding = accepted[dependency]
        prerequisites.append(
            f"- {dependency}: accepted_revision={binding['accepted_revision']}"
            + (f"; artifact_ref={binding['artifact_ref']}" if binding.get("artifact_ref") else "")
        )
    parts = []
    if plan_goal and plan_goal.strip() not in selected:
        parts.extend(("Plan objective:", plan_goal.strip()))
    parts.extend(("Selected task contract:", selected))
    parts.extend(("Accepted prerequisites:", "\n".join(prerequisites) or "- none"))
    if task.required_proof.strip() and task.required_proof.strip() not in selected:
        parts.extend(("Required proof:", task.required_proof.strip()))
    rendered_constraints = "\n".join(
        f"- {label}: {value}" for label, value in shared_constraints
    )
    if rendered_constraints and rendered_constraints not in selected:
        parts.extend(("Applicable explicit shared constraints:", rendered_constraints))
    return "\n".join(parts).strip()


def _runtime_grant(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("runtime_grant must be a mapping")
    if not {"turns", "wall_clock_seconds", "delegation", "mcp_select"}.issubset(value):
        raise ValueError("runtime_grant must contain resolved turns, wall clock, delegation, and MCP fields")
    delegation = value.get("delegation")
    if not isinstance(delegation, Mapping) or "child_agents" not in delegation:
        raise ValueError("runtime_grant must contain resolved child-agent authority")
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
        artifact_ref = binding.get("artifact_ref")
        if artifact_ref is not None and (not isinstance(artifact_ref, str) or not artifact_ref.strip()):
            raise ValueError(f"invalid artifact reference: {dependency}")
        if "artifact_available" in binding:
            raise ValueError("artifact_available is not an accepted prerequisite input")
    return accepted


def _source_parts(source: str | os.PathLike[str] | PlanGraph) -> tuple[str | None, PlanGraph, str, str | None]:
    if isinstance(source, PlanGraph):
        return None, source, source.plan_identity, None
    if isinstance(source, str) and ("\n" in source or "\r" in source):
        return source, parse_plan(source), hashlib.sha256(source.encode("utf-8")).hexdigest(), None
    path = Path(source)
    text = path.read_text(encoding="utf-8")
    return text, parse_plan(text), _frontmatter_value(text, "name") or path.stem, str(path.resolve())


def _canonical_runtime_binding(runtime: Mapping[str, Any]) -> dict[str, Any]:
    binding = dict(runtime)
    if "runtime_grant" not in binding:
        grant_fields = {"grant_turns", "grant_wall_clock_seconds", "grant_child_agents", "mcp_select"}
        if grant_fields.issubset(binding):
            binding["runtime_grant"] = {
                "turns": binding.pop("grant_turns"),
                "wall_clock_seconds": binding.pop("grant_wall_clock_seconds"),
                "delegation": {"child_agents": binding.pop("grant_child_agents")},
                "mcp_select": binding.pop("mcp_select"),
            }
    else:
        for field in ("grant_turns", "grant_wall_clock_seconds", "grant_child_agents", "mcp_select"):
            binding.pop(field, None)
    return binding


def _prepare_plan_lanes(
    text: str | None,
    graph: PlanGraph,
    plan_identity: str,
    plan_source: str | None,
    task_ids: Sequence[str],
    runtime_bindings: Mapping[str, Any],
) -> list[dict[str, Any]]:
    selected = [_canonical_task_id(task_id) for task_id in task_ids]
    if not selected:
        raise ValueError("at least one task is required")
    if len(set(selected)) != len(selected):
        raise ValueError("duplicate selected task")
    unknown = sorted(set(selected) - set(graph.tasks))
    if unknown:
        raise ValueError(f"unknown selected task: {unknown[0]}")
    plan_revision = hashlib.sha256(text.encode("utf-8")).hexdigest() if text is not None else graph.plan_identity
    lanes: list[dict[str, Any]] = []
    for task_id in selected:
        task = graph.tasks[task_id]
        binding = runtime_bindings.get(task_id)
        if not isinstance(binding, Mapping):
            raise ValueError(f"missing runtime binding: {task_id}")
        extra = set(binding) - _BINDING_FIELDS
        missing = _REQUIRED_BINDING_FIELDS - set(binding)
        if extra:
            raise ValueError(f"runtime binding contains plan-owned fields: {sorted(extra)[0]}")
        if missing:
            raise ValueError(f"runtime binding missing field: {sorted(missing)[0]}")
        if task.executor.casefold() != "deepagents":
            raise ValueError(f"unsupported task executor: {task.executor}")
        if not task.profile or task.profile.casefold() in {"unresolved", "none", "none (lead controller)"}:
            raise ValueError(f"task profile unresolved: {task_id}")
        accepted = _accepted_prerequisites(task, binding["accepted_prerequisites"])
        grant = _runtime_grant(binding["runtime_grant"])
        prepared = prepare_task(graph, task_id)
        structurally_ready = prepared.structurally_ready
        if not prepared.execution_eligible:
            raise ValueError(prepared.eligibility_reason or "selected task is not execution-eligible")
        dependency_ready = prepared.execution_eligible and structurally_ready
        descriptor = {
            "lane_id": task_id.lower().replace(" ", "-"),
            "repository_identity": binding["repository_identity"],
            "plan_identity": plan_identity,
            "plan_revision": plan_revision,
            "plan_source": plan_source,
            "task": _worker_brief(text, task, prepared, accepted, graph.goal, graph.shared_constraints),
            "executor": task.executor.casefold(),
            "profile": task.profile,
            "worktree": binding["worktree"],
            "expected_base": binding["expected_base"],
            "session": binding["session"],
            "pane": binding["pane"],
            "allowed_write_set": binding["allowed_write_set"],
            "dependencies": list(task.dependencies),
            "dependency_ready": dependency_ready,
            "structurally_ready": structurally_ready,
            "accepted_prerequisites": accepted,
            "fixed_contracts": binding["fixed_contracts"],
            "mutable_resources": binding["mutable_resources"],
            "local_capabilities": binding["local_capabilities"],
            "remaining_authorized_task_allowance": binding["remaining_authorized_task_allowance"],
            "attempt_deadline": binding["attempt_deadline"],
            "runtime_grant": grant,
        }
        for field in _OPTIONAL_BINDING_FIELDS:
            if field in binding:
                descriptor[field] = binding[field]
        descriptor["grant_turns"] = grant["turns"]["requested"]
        descriptor["grant_wall_clock_seconds"] = grant["wall_clock_seconds"]["requested"]
        descriptor["grant_child_agents"] = grant["delegation"]["child_agents"]
        descriptor["mcp_select"] = grant["mcp_select"]
        descriptor["execution_binding_digest"] = execution_binding_digest(descriptor)
        descriptor["plan_preparation"] = prepared.to_dict()
        lanes.append(descriptor)
    return lanes


def prepare_plan_lanes(
    plan_file: str | Path | PlanGraph,
    task_ids: Sequence[str],
    runtime_bindings: Mapping[str, Any],
) -> list[dict[str, Any]]:
    text, graph, plan_identity, plan_source = _source_parts(plan_file)
    status = _frontmatter_value(text, "status") if text is not None else None
    if status is not None and status.casefold() != "active":
        raise ValueError("plan must be active before dispatch")
    if not isinstance(runtime_bindings, Mapping):
        raise ValueError("runtime bindings must be keyed by task ID")
    return _prepare_plan_lanes(text, graph, plan_identity, plan_source, task_ids, runtime_bindings)


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
