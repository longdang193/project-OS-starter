"""Run a bounded, foreground wave of Herdr launcher attempts."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


MAX_CONCURRENCY = 2
_REQUIRED_FIELDS = (
    "lane_id",
    "task",
    "executor",
    "profile",
    "worktree",
    "expected_base",
    "session",
    "pane",
    "allowed_write_set",
    "dependencies",
    "dependency_ready",
    "fixed_contracts",
    "mutable_resources",
)


def _read_descriptors(source: str | os.PathLike[str]) -> list[dict[str, Any]]:
    payload = json.loads(Path(source).read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        payload = payload.get("lanes")
    if not isinstance(payload, list) or not all(isinstance(item, Mapping) for item in payload):
        raise ValueError("lane descriptor file must contain a list of objects")
    return [dict(item) for item in payload]


def _canonical_path(value: object) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(value))))


def _canonical_token(value: object) -> str:
    return str(value).replace("\\", "/").strip("/").casefold()


def _path_conflicts(left: object, right: object) -> bool:
    left_value = _canonical_token(left)
    right_value = _canonical_token(right)
    return (
        left_value == right_value
        or left_value.startswith(f"{right_value}/")
        or right_value.startswith(f"{left_value}/")
    )


def _set_conflicts(left: Iterable[object], right: Iterable[object]) -> bool:
    return any(_path_conflicts(left_item, right_item) for left_item in left for right_item in right)


def _reject(lane: Mapping[str, Any], reason: str) -> dict[str, str]:
    return {"lane_id": str(lane.get("lane_id", "<missing>")), "reason": reason}


def _invalidate_wave(
    admitted: list[dict[str, Any]],
    rejected: list[dict[str, str]],
    lane: Mapping[str, Any],
    reason: str,
) -> None:
    rejected.extend(_reject(item, reason) for item in admitted)
    admitted.clear()
    rejected.append(_reject(lane, reason))


def _admit_lanes(
    lanes: Iterable[Mapping[str, Any]],
    *,
    max_concurrency: int = MAX_CONCURRENCY,
) -> dict[str, list[dict[str, Any]]]:
    capacity = min(max_concurrency, MAX_CONCURRENCY)
    if capacity < 1:
        raise ValueError("max_concurrency must be positive")

    admitted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_worktrees: dict[str, str] = {}
    seen_panes: dict[str, str] = {}
    shared_contracts: tuple[str, ...] | None = None

    for raw_lane in lanes:
        lane = dict(raw_lane)
        lane_id = str(lane.get("lane_id", "<missing>"))
        missing = [field for field in _REQUIRED_FIELDS if field not in lane]
        if missing:
            rejected.append(_reject(lane, f"missing fields: {', '.join(missing)}"))
            continue
        if lane["executor"] != "deepagents":
            rejected.append(_reject(lane, f"unsupported executor: {lane['executor']}"))
            continue
        if lane_id in seen_ids:
            rejected.append(_reject(lane, "duplicate lane ID"))
            continue
        seen_ids.add(lane_id)
        if lane.get("dependency_ready") is not True:
            rejected.append(_reject(lane, "dependency not ready"))
            continue
        if not isinstance(lane["allowed_write_set"], list) or not isinstance(
            lane["mutable_resources"], list
        ):
            rejected.append(_reject(lane, "resource sets must be lists"))
            continue

        worktree = _canonical_path(lane["worktree"])
        if worktree in seen_worktrees:
            _invalidate_wave(
                admitted,
                rejected,
                lane,
                "worktree conflicts with " + seen_worktrees[worktree],
            )
            continue
        pane = _canonical_token(lane["pane"])
        if pane in seen_panes:
            _invalidate_wave(
                admitted,
                rejected,
                lane,
                "pane conflicts with " + seen_panes[pane],
            )
            continue
        contracts = tuple(sorted(map(str, lane["fixed_contracts"])))
        if shared_contracts is None:
            shared_contracts = contracts
        elif contracts != shared_contracts:
            rejected.append(_reject(lane, "fixed contracts differ"))
            continue
        if any(
            _set_conflicts(lane["allowed_write_set"], other["allowed_write_set"])
            or _set_conflicts(lane["mutable_resources"], other["mutable_resources"])
            for other in admitted
        ):
            _invalidate_wave(
                admitted,
                rejected,
                lane,
                "write set or mutable resource conflicts",
            )
            continue
        if len(admitted) >= capacity:
            rejected.append(_reject(lane, f"capacity limit {capacity}"))
            continue

        admitted.append(lane)
        seen_worktrees[worktree] = lane_id
        seen_panes[pane] = lane_id

    return {"admitted": admitted, "rejected": rejected}


def load_lane_descriptors(
    source: str | os.PathLike[str],
    *,
    max_concurrency: int = MAX_CONCURRENCY,
) -> dict[str, list[dict[str, Any]]]:
    """Load and validate lane descriptors before any write-capable launch."""

    return _admit_lanes(_read_descriptors(source), max_concurrency=max_concurrency)


def _launcher_command(
    lane: Mapping[str, Any],
    *,
    python_executable: str,
    launcher_path: str | os.PathLike[str] | None,
) -> list[str]:
    script = Path(launcher_path) if launcher_path else Path(__file__).with_name("herdr_main_launcher.py")
    command = [
        python_executable,
        str(script),
        "--profile",
        str(lane["profile"]),
        "--session",
        str(lane["session"]),
        "--pane",
        str(lane["pane"]),
        "--cwd",
        str(lane["worktree"]),
        "--expected-base",
        str(lane["expected_base"]),
        "--executor",
        str(lane["executor"]),
        "--task",
        str(lane["task"]),
    ]
    for name, flag in (("name", "--name"), ("codex_home", "--codex-home")):
        if lane.get(name):
            command.extend([flag, str(lane[name])])
    for selection in lane.get("mcp_select", []):
        command.extend(["--mcp-select", str(selection)])
    return command


def _tagged(lane_id: str, tag: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"tag": tag, "lane_id": lane_id, "payload": dict(payload)}


def parse_launcher_records(
    output: str | Iterable[str],
    *,
    lane_id: str | None = None,
) -> dict[str, Any]:
    """Parse launcher JSONL without treating preparation as final evidence."""

    lines = output.splitlines() if isinstance(output, str) else list(output)
    records: list[dict[str, Any]] = []
    malformed: list[str] = []
    preparation: dict[str, Any] | None = None
    candidate_assignment: dict[str, Any] | None = None
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            record = json.loads(text)
        except json.JSONDecodeError:
            malformed.append(text)
            continue
        if not isinstance(record, Mapping):
            malformed.append(text)
            continue
        record = dict(record)
        record_lane_id = lane_id or str(record.get("lane_id", ""))
        if "assignment" in record and isinstance(record["assignment"], Mapping):
            candidate_assignment = dict(record["assignment"])
            records.append(_tagged(record_lane_id, "final_assignment", candidate_assignment))
        elif "registry_launcher" in record:
            preparation = record
            records.append(_tagged(record_lane_id, "preparation", record))
        else:
            records.append(_tagged(record_lane_id, "launcher_record", record))

    preparation_attempt_id = None
    if preparation is not None and isinstance(preparation.get("registry_launcher"), Mapping):
        preparation_attempt_id = preparation["registry_launcher"].get("attempt_id")
    assignment = None
    if (
        candidate_assignment is not None
        and preparation_attempt_id is not None
        and candidate_assignment.get("attempt_id") == preparation_attempt_id
    ):
        assignment = candidate_assignment
    return {
        "preparation": preparation,
        "assignment": assignment,
        "records": records,
        "malformed": malformed,
    }


def run_lane(
    lane: Mapping[str, Any],
    *,
    python_executable: str = sys.executable,
    launcher_path: str | os.PathLike[str] | None = None,
    timeout_seconds: float | None = None,
    popen_factory: Any = subprocess.Popen,
) -> dict[str, Any]:
    """Run one blocking launcher attempt and retain unresolved state on timeout."""

    lane_id = str(lane["lane_id"])
    command = _launcher_command(
        lane,
        python_executable=python_executable,
        launcher_path=launcher_path,
    )
    if lane.get("executor") != "deepagents":
        return {
            "lane_id": lane_id,
            "command": command,
            "exit_code": None,
            "records": [],
            "stderr": "",
            "unresolved": False,
            "capacity": "retired",
            "failure_kind": "unsupported_executor",
        }
    try:
        process = popen_factory(
            command,
            cwd=str(lane["worktree"]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            return {
                "lane_id": lane_id,
                "command": command,
                "exit_code": None,
                "records": [],
                "stderr": "",
                "unresolved": True,
                "capacity": "occupied",
                "failure_kind": "transport_timeout",
            }
    except OSError as exc:
        return {
            "lane_id": lane_id,
            "command": command,
            "exit_code": None,
            "records": [],
            "stderr": str(exc),
            "unresolved": False,
            "capacity": "retired",
            "failure_kind": "launch_failed",
        }

    parsed = parse_launcher_records(stdout or "", lane_id=lane_id)
    records = list(parsed["records"])
    records.append(_tagged(lane_id, "child_exit", {"exit_code": process.returncode}))
    if stderr:
        records.append(_tagged(lane_id, "stderr", {"text": stderr}))

    def classify(assignment: Mapping[str, Any] | None) -> tuple[str, bool, str]:
        if not isinstance(assignment, Mapping):
            return "occupied", True, "missing final assignment"
        execution = assignment.get("execution")
        cleanup = assignment.get("cleanup")
        descendant_state = execution.get("descendant_state") if isinstance(execution, Mapping) else None
        resource_settled = (
            isinstance(execution, Mapping)
            and execution.get("state") in {"exited", "completed", "failed", "start_failed"}
            and descendant_state in {None, "terminated", "not_started"}
            and isinstance(cleanup, Mapping)
            and cleanup.get("state") == "removed"
            and cleanup.get("recovery_required") is not True
        )
        if not resource_settled:
            return "occupied", True, "execution or cleanup unsettled"
        if assignment.get("reconciliation_required") is True:
            return "retired", True, "task result unresolved"
        task_result = assignment.get("task_result")
        task_uncertain = isinstance(task_result, Mapping) and (
            task_result.get("accepted") is None
            or task_result.get("state") in {"unknown", "running", "preserved", "unverified"}
            or task_result.get("status") in {"unknown", "running", "preserved", "unverified"}
        )
        if task_uncertain:
            return "retired", True, "task result unresolved"
        return "retired", False, "settled"

    if parsed["malformed"]:
        capacity, unresolved, unresolved_reason = "occupied", True, "malformed launcher evidence"
    else:
        capacity, unresolved, unresolved_reason = classify(parsed["assignment"])
    records.append(_tagged(lane_id, "capacity", {"state": capacity}))
    if unresolved:
        records.append(_tagged(lane_id, "unresolved", {"reason": unresolved_reason}))
    result = {
        "lane_id": lane_id,
        "command": command,
        "exit_code": process.returncode,
        "records": records,
        "preparation": parsed["preparation"],
        "assignment": parsed["assignment"],
        "malformed": parsed["malformed"],
        "stderr": stderr or "",
        "unresolved": unresolved,
        "capacity": capacity,
    }
    if process.returncode:
        result["failure_kind"] = "command_exit"
    elif unresolved and unresolved_reason == "task result unresolved":
        result["failure_kind"] = "task_result_unresolved"
    return result


def load_lane_descriptors_from_items(
    lanes: Iterable[Mapping[str, Any]],
    *,
    max_concurrency: int = MAX_CONCURRENCY,
) -> dict[str, list[dict[str, Any]]]:
    """Validate in-memory descriptors with the file-backed admission rules."""

    return _admit_lanes(lanes, max_concurrency=max_concurrency)


def run_parallel(
    source: str | os.PathLike[str] | Mapping[str, Any] | Iterable[Mapping[str, Any]],
    *,
    max_concurrency: int = MAX_CONCURRENCY,
    stop_event: Any | None = None,
    **run_kwargs: Any,
) -> dict[str, Any]:
    """Run admitted lanes concurrently; return derived evidence only."""

    if isinstance(source, (str, os.PathLike)):
        admission = load_lane_descriptors(source, max_concurrency=max_concurrency)
    elif isinstance(source, Mapping) and "admitted" in source:
        admitted = source["admitted"]
        if not isinstance(admitted, list):
            raise ValueError("admitted lanes must be a list")
        admission = _admit_lanes(admitted, max_concurrency=max_concurrency)
        admission["rejected"] = list(source.get("rejected", [])) + admission["rejected"]
    else:
        admission = load_lane_descriptors_from_items(source, max_concurrency=max_concurrency)

    if not 1 <= max_concurrency <= MAX_CONCURRENCY:
        raise ValueError(f"max_concurrency must be between 1 and {MAX_CONCURRENCY}")

    results: dict[str, dict[str, Any]] = {}
    interrupted = bool(stop_event is not None and stop_event.is_set())
    with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        futures = {}
        if not interrupted:
            for lane in admission["admitted"]:
                if stop_event is not None and stop_event.is_set():
                    interrupted = True
                    break
                futures[pool.submit(run_lane, lane, **run_kwargs)] = str(lane["lane_id"])
        for future in as_completed(futures):
            lane_id = futures[future]
            try:
                results[lane_id] = future.result()
            except BaseException as exc:  # preserve sibling evidence
                results[lane_id] = {
                    "lane_id": lane_id,
                    "exit_code": None,
                    "records": [],
                    "stderr": str(exc),
                    "unresolved": True,
                    "capacity": "occupied",
                    "failure_kind": "coordinator_error",
                }
    return {
        "admitted": admission["admitted"],
        "rejected": admission["rejected"],
        "interrupted": interrupted,
        "results": [
            results[lane["lane_id"]]
            for lane in admission["admitted"]
            if lane["lane_id"] in results
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes-file", required=True, type=Path)
    parser.add_argument("--max-concurrency", type=int, default=MAX_CONCURRENCY)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_parallel(args.lanes_file, max_concurrency=args.max_concurrency)
    for item in result["results"]:
        print(json.dumps({"tag": "lane_result", **item}, sort_keys=True))
    for item in result["rejected"]:
        print(json.dumps({"tag": "lane_rejected", **item}, sort_keys=True))
    return 0 if not result["rejected"] and all(not item.get("unresolved") for item in result["results"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
