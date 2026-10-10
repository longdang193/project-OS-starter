"""Derive disposable task preparation data from a Git-tracked plan."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

from .attempt import execution_binding_digest, normalize_runtime_grant, same_attempt_binding
from .acceptance import release_authorized_evidence
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


def _plan_revision(value: str | bytes) -> str:
    text = value.decode("utf-8") if isinstance(value, bytes) else value
    canonical = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    values: dict[str, str] = {}
    labels = {label.casefold(): label for label in _SHARED_CONSTRAINT_LABELS}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^\s*-\s+([^:]+):\s*(.*)$", lines[index])
        if match is None:
            index += 1
            continue
        label = labels.get(match.group(1).strip().casefold())
        if label is None or label.casefold() in values:
            index += 1
            continue
        parts = [match.group(2).strip()]
        index += 1
        while index < len(lines):
            line = lines[index]
            if not line.strip() or not line[:1].isspace():
                break
            if re.match(r"^\s*-\s+", line):
                break
            parts.append(line.strip())
            index += 1
        value = " ".join(part for part in parts if part)
        if value:
            values[label.casefold()] = value
    return tuple(
        (label, values[label.casefold()])
        for label in _SHARED_CONSTRAINT_LABELS
        if label.casefold() in values
    )


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
        plan_identity=_plan_revision(text),
        goal=_section(text, "Goal"),
        shared_constraints=_shared_constraints(_section(text, "Execution Approach")),
        tasks=tasks,
    )


def load_plan(source: str | os.PathLike[str]) -> PlanGraph:
    if isinstance(source, str) and ("\n" in source or "\r" in source):
        return parse_plan(source)
    path = Path(source)
    return parse_plan(path.read_text(encoding="utf-8"))


def _transitions_are_applied(
    source: str | os.PathLike[str],
    transitions: Sequence[Mapping[str, str]],
) -> bool:
    graph = load_plan(source)
    return bool(transitions) and all(
        graph.tasks.get(_canonical_task_id(str(transition.get("task_id", "")))) is not None
        and graph.tasks[_canonical_task_id(str(transition.get("task_id", "")))].state
        == _cell(str(transition.get("next_state", ""))).casefold()
        for transition in transitions
    )


@contextmanager
def _plan_write_lock(path: Path):
    lock_root = Path(tempfile.gettempdir()) / "project-os-plan-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_name = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()
    lock_path = lock_root / f"{lock_name}.lock"
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _verify_git_checkpoint(
    source: str | os.PathLike[str],
    consequence: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify that a Git checkpoint records the accepted Plan revision."""

    required = ("commit_sha", "coordination_ref", "plan_path", "expected_plan_revision")
    if any(not isinstance(consequence.get(field), str) or not consequence.get(field).strip() for field in required):
        return {"verified": False, "reason": "Git checkpoint metadata incomplete"}
    plan_path = Path(source).resolve()
    try:
        root = Path(
            subprocess.run(
                ["git", "-C", str(plan_path.parent), "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        relative_plan = plan_path.relative_to(root).as_posix()
        commit_sha = str(consequence["commit_sha"])
        coordination_ref = str(consequence["coordination_ref"])
        if str(consequence["plan_path"]).replace("\\", "/") != relative_plan:
            return {"verified": False, "reason": "Git checkpoint Plan path mismatch"}
        expected_revision = str(consequence["expected_plan_revision"])
        subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", f"{commit_sha}^{{commit}}"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", commit_sha, coordination_ref],
            check=True,
            capture_output=True,
            text=True,
        )
        committed_plan = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit_sha}:{relative_plan}"],
            check=True,
            capture_output=True,
        ).stdout
        actual_revision = _plan_revision(committed_plan)
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError) as exc:
        return {"verified": False, "reason": f"Git checkpoint verification failed: {exc}"}
    if actual_revision != expected_revision:
        return {
            "verified": False,
            "reason": "Git checkpoint Plan revision mismatch",
            "actual_plan_revision": actual_revision,
        }
    return {
        **dict(consequence),
        "verified": True,
        "owner": "git",
        "checkpoint_verified": True,
        "plan_path": relative_plan,
        "expected_plan_revision": expected_revision,
        "commit_sha": commit_sha,
        "coordination_ref": coordination_ref,
    }


def apply_accepted_plan_transitions(
    source: str | os.PathLike[str],
    decision: Mapping[str, Any],
    transitions: Sequence[Mapping[str, str]],
    *,
    dependent_transition: Mapping[str, Any] | None = None,
    evidence_release: Mapping[str, Any] | None = None,
    expected_revision: str,
) -> dict[str, Any]:
    """Apply Plan transitions only from complete CoS acceptance proof."""

    controller = decision.get("controller")
    task = decision.get("task")
    task_transition = decision.get("task_transition")
    proof = decision.get("acceptance_proof")
    if (
        decision.get("decision") != "PASS"
        or not all(isinstance(value, Mapping) for value in (controller, task, task_transition, proof))
        or not isinstance(controller.get("identity"), str)
        or not controller.get("identity").strip()
        or controller.get("authority") != "cos"
        or not isinstance(controller.get("plan_identity"), str)
        or not controller.get("plan_identity").strip()
        or not isinstance(controller.get("task_id"), str)
        or not controller.get("task_id").strip()
        or not isinstance(task.get("task_id"), str)
        or not task.get("task_id").strip()
        or not isinstance(task.get("plan_identity"), str)
        or not task.get("plan_identity").strip()
        or controller.get("plan_identity") != task.get("plan_identity")
        or controller.get("task_id") != task.get("task_id")
        or task_transition.get("authorized") is not True
        or task_transition.get("current_state") != "active"
        or task_transition.get("next_state") != "completed"
    ):
        return {"authorized": False, "reason": "acceptance decision incomplete"}
    required_conditions = proof.get("required_conditions")
    artifact_conditions = proof.get("artifact_conditions")
    freshness = proof.get("freshness")
    git_proof = proof.get("git")
    settlement = proof.get("settlement")
    if (
        not isinstance(required_conditions, Mapping)
        or not required_conditions
        or not isinstance(artifact_conditions, Mapping)
        or set(artifact_conditions) != set(required_conditions)
        or any(value is not True for value in artifact_conditions.values())
        or proof.get("task_id") != task.get("task_id")
        or proof.get("plan_identity") != task.get("plan_identity")
        or proof.get("task_state") != "active"
        or not isinstance(freshness, Mapping)
        or freshness.get("head_matches") is not True
        or freshness.get("write_scope_matches") is not True
        or not isinstance(git_proof, Mapping)
        or not isinstance(git_proof.get("repository_identity"), str)
        or not git_proof.get("repository_identity").strip()
        or git_proof.get("plan_identity") != task.get("plan_identity")
        or not isinstance(settlement, Mapping)
        or settlement.get("settlement_proven") is not True
        or settlement.get("resource_settled") is not True
    ):
        return {"authorized": False, "reason": "acceptance decision incomplete"}
    try:
        target_plan_identity = _source_parts(source)[2]
    except (OSError, ValueError):
        return {"authorized": False, "reason": "acceptance decision incomplete"}
    if target_plan_identity != task.get("plan_identity"):
        return {"authorized": False, "reason": "acceptance decision incomplete"}
    accepted_task_id = task.get("task_id")
    accepted_transition = {
        "task_id": accepted_task_id,
        "expected_state": "active",
        "next_state": "completed",
    }
    expected_transitions: list[Mapping[str, Any]] = [accepted_transition]
    if dependent_transition is not None:
        if (
            dependent_transition.get("authorized") is not True
            or dependent_transition.get("current_state") != "pending"
            or dependent_transition.get("next_state") != "active"
            or not isinstance(dependent_transition.get("task_id"), str)
            or not dependent_transition.get("task_id").strip()
            or dependent_transition.get("plan_identity") != task.get("plan_identity")
        ):
            return {"authorized": False, "reason": "acceptance transition mismatch"}
        expected_transitions.append(
            {
                "task_id": dependent_transition.get("task_id"),
                "expected_state": "pending",
                "next_state": "active",
            }
        )
    if not isinstance(accepted_task_id, str) or list(transitions) != expected_transitions:
        return {"authorized": False, "reason": "acceptance transition mismatch"}
    if evidence_release is not None and not isinstance(evidence_release, Mapping):
        return {"authorized": False, "reason": "invalid evidence release"}
    attempt_guard = evidence_release.get("attempt_guard") if isinstance(evidence_release, Mapping) else None
    persisted_release_record = evidence_release.get("release_record") if isinstance(evidence_release, Mapping) else None
    record_release_authorization = None
    if isinstance(attempt_guard, Mapping):
        try:
            from scripts.dcode_project import record_release_authorization as persist_release_authorization

            release_binding = dict(evidence_release.get("binding", {}))
            evidence_ref = release_binding.get("evidence_ref")
            if not isinstance(evidence_ref, str) or not evidence_ref.strip():
                raise ValueError("evidence release binding is missing evidence_ref")
            recorded_resources = persisted_release_record.get("resources") if isinstance(persisted_release_record, Mapping) else None
            recorded_resource = recorded_resources.get(evidence_ref) if isinstance(recorded_resources, Mapping) else None
            configured_resources = evidence_release.get("resources")
            configured_resource = configured_resources.get(evidence_ref) if isinstance(configured_resources, Mapping) else None
            pending_resource = dict(recorded_resource) if isinstance(recorded_resource, Mapping) else (
                dict(configured_resource) if isinstance(configured_resource, Mapping) else {}
            )
            if pending_resource.get("state") not in {"removed", "already_absent"}:
                pending_resource["state"] = "pending"
            pending_authorization = {
                **dict(attempt_guard.get("release_authorization", {})),
                "canonical_consequence": dict(evidence_release.get("canonical_consequence", {})),
                "resources": {evidence_ref: pending_resource},
            }
            persisted_guard = persist_release_authorization(
                assignment_id=str(attempt_guard["assignment_id"]),
                binding=dict(attempt_guard["binding"]),
                release_authorization=pending_authorization,
            )
            by_attempt = persisted_guard.get("released_resources_by_attempt")
            attempt_key = str(attempt_guard["binding"].get("attempt_id"))
            attempt_resources = by_attempt.get(attempt_key) if isinstance(by_attempt, Mapping) else None
            if isinstance(attempt_resources, Mapping):
                authoritative_resources = attempt_resources
            else:
                legacy_binding = persisted_guard.get("release_binding")
                legacy_resources = persisted_guard.get("released_resources")
                authoritative_resources = (
                    legacy_resources
                    if isinstance(legacy_resources, Mapping)
                    and isinstance(legacy_binding, Mapping)
                    and same_attempt_binding(legacy_binding, attempt_guard["binding"])
                    else pending_authorization["resources"]
                )
            persisted_release_record = {
                "authorized": True,
                "binding": release_binding,
                "resources": dict(authoritative_resources),
                "attempt_guard": persisted_guard,
            }
            record_release_authorization = persist_release_authorization
        except (KeyError, RuntimeError, TypeError, ValueError) as exc:
            return {
                "authorized": False,
                "reason": "release authorization persistence failed",
                "evidence_release": {
                    "authorized": False,
                    "payload_released": False,
                    "reasons": [f"release authorization persistence failed: {exc}"],
                },
            }
    result = apply_plan_transitions(source, transitions, expected_revision=expected_revision)
    if result.get("authorized") is not True:
        try:
            replayable = _transitions_are_applied(source, transitions)
        except (OSError, ValueError, KeyError):
            replayable = False
        if not replayable:
            return result
        result = {**result, "authorized": True, "replayed": True}
    if evidence_release is None:
        return result
    canonical_consequence = dict(evidence_release.get("canonical_consequence", {}))
    transition_revision = result.get("new_revision") or result.get("revision")
    if canonical_consequence.get("expected_plan_revision") != transition_revision:
        checkpoint = {
            "verified": False,
            "reason": "Git checkpoint expected Plan revision does not match transition",
        }
    else:
        checkpoint = _verify_git_checkpoint(source, canonical_consequence)
    if checkpoint.get("verified") is True:
        canonical_consequence = checkpoint
    else:
        canonical_consequence = {
            "authorized": False,
            "owner": "git",
            "checkpoint_verified": False,
            "reason": checkpoint.get("reason", "Git checkpoint verification failed"),
        }
    release_result = release_authorized_evidence(
        decision,
        binding=evidence_release.get("binding", {}),
        canonical_consequence=canonical_consequence,
        required_consumers=evidence_release.get("required_consumers", ()),
        consumer_releases=evidence_release.get("consumer_releases", {}),
        retention=evidence_release.get("retention", {}),
        evidence_paths=evidence_release.get("evidence_paths", {}),
        retirement_proof=evidence_release.get("retirement_proof"),
        recovery_required=evidence_release.get("recovery_required", False),
        release_record=persisted_release_record,
    )
    if release_result.get("payload_released") is True and isinstance(attempt_guard, Mapping):
        try:
            if record_release_authorization is None:
                from scripts.dcode_project import record_release_authorization as persist_release_authorization

                record_release_authorization = persist_release_authorization

            record_release_authorization(
                assignment_id=str(attempt_guard["assignment_id"]),
                binding=dict(attempt_guard["binding"]),
                release_authorization={
                    **dict(attempt_guard.get("release_authorization", {})),
                    "canonical_consequence": canonical_consequence,
                    "resources": release_result.get("resources")
                    or (
                        persisted_release_record.get("resources", {})
                        if isinstance(persisted_release_record, Mapping)
                        else {}
                    ),
                },
            )
        except (KeyError, RuntimeError, TypeError, ValueError) as exc:
            release_result = {
                **release_result,
                "authorized": False,
                "payload_released": False,
                "reasons": [f"release record persistence failed: {exc}"],
            }
    return {**result, "evidence_release": release_result}


def apply_plan_transitions(
    source: str | os.PathLike[str],
    transitions: Sequence[Mapping[str, str]],
    *,
    expected_revision: str,
) -> dict[str, Any]:
    path = Path(source)
    with _plan_write_lock(path):
        return _apply_plan_transitions_locked(path, transitions, expected_revision=expected_revision)


def _apply_plan_transitions_locked(
    source: str | os.PathLike[str],
    transitions: Sequence[Mapping[str, str]],
    *,
    expected_revision: str,
) -> dict[str, Any]:
    """Apply one guarded lead-controller transition batch to a plan ledger."""

    path = Path(source)
    text = path.read_text(encoding="utf-8")
    revision = _plan_revision(text)
    if revision != expected_revision:
        return {
            "authorized": False,
            "reason": "plan revision changed",
            "revision": revision,
        }
    if not transitions:
        return {"authorized": False, "reason": "no plan transitions", "revision": revision}

    graph = parse_plan(text)
    normalized: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for transition in transitions:
        task_id = _canonical_task_id(str(transition.get("task_id", "")))
        expected_state = _cell(str(transition.get("expected_state", ""))).casefold()
        next_state = _cell(str(transition.get("next_state", ""))).casefold()
        if task_id in seen:
            return {"authorized": False, "reason": "duplicate plan transition", "revision": revision}
        seen.add(task_id)
        task = graph.tasks.get(task_id)
        if task is None:
            return {"authorized": False, "reason": "unknown plan task", "revision": revision}
        if task.state != expected_state:
            return {"authorized": False, "reason": "task state changed", "revision": revision}
        if (expected_state, next_state) not in {("active", "completed"), ("pending", "active")}:
            return {"authorized": False, "reason": "unsupported plan transition", "revision": revision}
        normalized.append((task_id, expected_state, next_state))

    proposed_states = {task_id: task.state for task_id, task in graph.tasks.items()}
    proposed_states.update({task_id: next_state for task_id, _, next_state in normalized})
    for task_id, _, next_state in normalized:
        if next_state == "active" and any(
            proposed_states.get(dependency) != "completed"
            for dependency in graph.tasks[task_id].dependencies
        ):
            return {"authorized": False, "reason": "dependent prerequisites incomplete", "revision": revision}

    lines = text.splitlines(keepends=True)
    header_index = next(
        (
            index
            for index, line in enumerate(lines)
            if (cells := _split_row(line))
            and tuple(_cell(item).casefold() for item in cells) == _TASK_ROW_HEADER
        ),
        None,
    )
    if header_index is None:
        return {"authorized": False, "reason": "plan task ledger table not found", "revision": revision}
    row_end = header_index + 2
    while row_end < len(lines) and lines[row_end].lstrip().startswith("|"):
        row_end += 1

    for task_id, _, next_state in normalized:
        row_pattern = re.compile(rf"^(\|\s*{re.escape(task_id)}\s*\|\s*)[^|]+(\|.*)$", re.IGNORECASE)
        matches = [index for index in range(header_index + 2, row_end) if row_pattern.match(lines[index])]
        if len(matches) != 1:
            return {"authorized": False, "reason": "plan task row unavailable", "revision": revision}
        row_index = matches[0]
        lines[row_index] = row_pattern.sub(
            lambda match: f"{match.group(1)}`{next_state}`{match.group(2)}",
            lines[row_index],
            count=1,
        )

    updated = "".join(lines)
    latest_text = path.read_text(encoding="utf-8")
    latest_revision = _plan_revision(latest_text)
    if latest_revision != revision:
        return {
            "authorized": False,
            "reason": "plan revision changed",
            "revision": latest_revision,
        }
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = handle.name
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return {
        "authorized": True,
        "revision": revision,
        "new_revision": _plan_revision(updated),
        "transitions": [
            {"task_id": task_id, "next_state": next_state}
            for task_id, _, next_state in normalized
        ],
    }


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
    return PreparedTask(
        task_id=canonical_id,
        execution_eligible=execution_eligible,
        eligibility_reason=eligibility_reason,
        dependencies=task.dependencies,
        prerequisites=prerequisites,
        structurally_ready=not unresolved,
        unresolved_prerequisites=unresolved,
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
        return source, parse_plan(source), _plan_revision(source), None
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
    plan_revision = _plan_revision(text) if text is not None else graph.plan_identity
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
