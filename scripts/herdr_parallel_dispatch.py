"""Run a bounded, foreground wave of Herdr launcher attempts."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

try:
    from scripts.herdr_main_launcher import (
        _normalize_runtime_grant,
        _sha256_text,
    )
except ModuleNotFoundError:
    from herdr_main_launcher import (
        _normalize_runtime_grant,
        _sha256_text,
    )


MAX_CONCURRENCY = 2
_LOCAL_CAPABILITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._+-]*$")
TIMEOUT_OWNER = "dcode-project"
WHOLE_ATTEMPT_WALL_CLOCK_SECONDS = 1800
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
    "grant_turns",
    "grant_wall_clock_seconds",
    "grant_child_agents",
    "mcp_select",
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


def _canonical_mcp_selectors(values: object) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError("MCP selectors must be a list of strings")
    selectors = [selector.strip() for value in values for selector in value.split(",")]
    if any(not selector for selector in selectors):
        raise ValueError("MCP selectors cannot be empty")
    return sorted(set(selectors))


def _grant_digest(executor: str, runtime_grant: Mapping[str, Any]) -> str:
    return _sha256_text(
        json.dumps(
            {
                "executor": executor,
                "turns": runtime_grant["turns"]["requested"],
                "wall_clock_seconds": runtime_grant["wall_clock_seconds"]["requested"],
                "mcp_select": runtime_grant["mcp_select"],
                "delegation": runtime_grant["delegation"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _capability_digest(values: list[str]) -> str:
    return _sha256_text(json.dumps(values, separators=(",", ":")))


def _bind_requested_grant(lane: dict[str, Any]) -> None:
    selectors = _canonical_mcp_selectors(lane["mcp_select"])
    nested = lane.get("runtime_grant")
    if isinstance(nested, Mapping) and "mcp_select" in nested:
        if _canonical_mcp_selectors(nested["mcp_select"]) != selectors:
            raise ValueError("conflicting top-level and nested MCP selectors")
    runtime_grant = _normalize_runtime_grant(
        executor=str(lane["executor"]),
        grant_turns=lane["grant_turns"],
        grant_wall_clock_seconds=lane["grant_wall_clock_seconds"],
        mcp_select=selectors,
        grant_child_agents=lane["grant_child_agents"],
    )
    requested_value = lane.get("local_capabilities", [])
    requested = (
        requested_value.get("requested", [])
        if isinstance(requested_value, Mapping)
        else requested_value
    )
    effective = _verify_local_capabilities(_normalize_local_capabilities(requested))
    lane.update(
        {
            "mcp_select": selectors,
            "grant_turns": runtime_grant["turns"]["requested"],
            "grant_wall_clock_seconds": runtime_grant["wall_clock_seconds"]["requested"],
            "grant_child_agents": runtime_grant["delegation"]["child_agents"],
            "runtime_grant": runtime_grant,
            "grant_digest": _grant_digest(str(lane["executor"]), runtime_grant),
            "local_capabilities": {
                "requested": requested,
                "effective": effective,
                "verification_commands": list(effective),
                "source_task_sha256": _sha256_text(str(lane["task"])),
                "digest": _capability_digest(effective),
            },
        }
    )
    if not requested:
        lane.pop("local_capabilities", None)


def _normalize_local_capabilities(values: object) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError("local_capabilities must be a list of strings")
    normalized = [value.lower() for value in values]
    if any(not _LOCAL_CAPABILITY_PATTERN.fullmatch(value) or ".." in value for value in normalized):
        raise ValueError("local_capabilities must contain safe command basenames")
    if len(normalized) != len(set(normalized)):
        raise ValueError("local_capabilities cannot contain duplicates")
    return normalized


def _verify_local_capabilities(values: list[str]) -> list[str]:
    unavailable = [value for value in values if shutil.which(value) is None]
    if unavailable:
        raise ValueError("unavailable local capabilities: " + ", ".join(unavailable))
    return list(values)


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
        try:
            _bind_requested_grant(lane)
        except (TypeError, ValueError, RuntimeError) as exc:
            rejected.append(_reject(lane, str(exc)))
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
    grant = lane.get("runtime_grant")
    if not isinstance(grant, Mapping):
        bound_lane = dict(lane)
        _bind_requested_grant(bound_lane)
        grant = bound_lane["runtime_grant"]
    command.extend(
        [
            "--grant-turns",
            str(grant["turns"]["requested"]),
            "--grant-wall-clock-seconds",
            str(grant["wall_clock_seconds"]["requested"]),
            "--grant-child-agents",
            str(grant["delegation"]["child_agents"]),
        ]
    )
    for selection in grant.get("mcp_select", []):
        command.extend(["--mcp-select", str(selection)])
    capabilities = lane.get("local_capabilities", [])
    if isinstance(capabilities, Mapping):
        capabilities = capabilities.get("effective", [])
    for capability in capabilities:
        command.extend(["--local-capability", str(capability)])
    return command


def _tagged(lane_id: str, tag: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"tag": tag, "lane_id": lane_id, "payload": dict(payload)}


def parse_launcher_records(
    output: str | Iterable[str],
    *,
    lane_id: str | None = None,
) -> dict[str, Any]:
    """Parse launcher JSONL without treating preparation as final evidence."""

    if isinstance(output, bytes):
        output = output.decode("utf-8", errors="replace")
    lines = output.splitlines() if isinstance(output, str) else list(output)
    records: list[dict[str, Any]] = []
    malformed: list[str] = []
    preparation: dict[str, Any] | None = None
    candidate_assignment: dict[str, Any] | None = None
    for line in lines:
        if isinstance(line, bytes):
            line = line.decode("utf-8", errors="replace")
        text = str(line).strip()
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


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _merge_streams(first: object, second: object) -> str:
    left = _text(first)
    right = _text(second)
    if not left:
        return right
    if not right:
        return left
    if right == left or right.startswith(left):
        return right
    return left + right


def _finish_timed_out_process(process: Any, timeout_error: subprocess.TimeoutExpired) -> tuple[str, str, bool]:
    stdout = _text(timeout_error.output)
    stderr = _text(timeout_error.stderr)
    drained = False
    try:
        extra_stdout, extra_stderr = process.communicate(timeout=0)
        stdout = _merge_streams(stdout, extra_stdout)
        stderr = _merge_streams(stderr, extra_stderr)
        drained = True
    except (subprocess.TimeoutExpired, OSError, TypeError):
        pass
    reaped = getattr(process, "returncode", None) is not None
    wait = getattr(process, "wait", None)
    if not reaped and callable(wait):
        try:
            wait(timeout=0)
        except (subprocess.TimeoutExpired, OSError, TypeError):
            pass
        reaped = getattr(process, "returncode", None) is not None
    if reaped:
        for stream_name in ("stdout", "stderr"):
            stream = getattr(process, stream_name, None)
            close = getattr(stream, "close", None)
            if callable(close):
                close()
    return stdout, stderr, drained and reaped


def _process_identity(process: Any) -> dict[str, Any]:
    pid = getattr(process, "pid", None)
    return {"pid": pid} if isinstance(pid, int) else {}


def _grant_evidence_matches(lane: Mapping[str, Any], parsed: Mapping[str, Any]) -> bool:
    preparation = parsed.get("preparation")
    assignment = parsed.get("assignment")
    registry = preparation.get("registry_launcher") if isinstance(preparation, Mapping) else None
    prep_grant = registry.get("runtime_grant") if isinstance(registry, Mapping) else None
    prep_digest = registry.get("grant_digest") if isinstance(registry, Mapping) else None
    assignment_digest = assignment.get("grant_digest") if isinstance(assignment, Mapping) else None
    expected = lane.get("runtime_grant")
    expected_digest = lane.get("grant_digest")
    expected_capabilities = lane.get("local_capabilities")
    if not isinstance(expected, Mapping) or not expected_digest:
        return True
    grant_matches = (
        isinstance(registry, Mapping)
        and isinstance(assignment, Mapping)
        and prep_grant == expected
        and prep_digest == expected_digest
        and assignment_digest == expected_digest
    )
    if not isinstance(expected_capabilities, Mapping):
        return grant_matches
    prep_capabilities = registry.get("local_capabilities") if isinstance(registry, Mapping) else None
    assignment_capabilities = assignment.get("local_capabilities") if isinstance(assignment, Mapping) else None
    return grant_matches and prep_capabilities == expected_capabilities and assignment_capabilities == expected_capabilities


def runtime_completion_is_not_acceptance(record: Mapping[str, Any]) -> bool:
    return record.get("status") == "reported_completed" and record.get("accepted") is not True


def validate_acceptance(record: Mapping[str, Any]) -> str | None:
    if runtime_completion_is_not_acceptance(record):
        return "missing_grant_evidence" if not record.get("grant_evidence") else "acceptance_pending"
    return None


def dispatch_launcher_record(output: str) -> dict[str, Any]:
    record = json.loads(output)
    if not isinstance(record, Mapping):
        raise ValueError("launcher record must be an object")
    return dict(record)


def validate_local_capabilities(required: list[str], available: list[str]) -> bool:
    missing = set(required) - set(available)
    if missing:
        raise ValueError('unknown local capabilities: ' + ', '.join(sorted(missing)))
    return True


def validate_plan_authority(authority: Mapping[str, Any]) -> bool:
    return isinstance(authority.get("cumulative_wall_clock_seconds"), (int, float)) and authority["cumulative_wall_clock_seconds"] > 0


def validate_git_checkpoint(checkpoint: Mapping[str, Any]) -> bool:
    return bool(checkpoint.get("revision")) and checkpoint.get("verified") is True


def attempt_expired(started_at: float, now: float) -> bool:
    return now >= started_at


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
    if lane.get("executor") != "deepagents":
        return {
            "lane_id": lane_id,
            "command": [],
            "exit_code": None,
            "records": [],
            "stderr": "",
            "unresolved": False,
            "capacity": "retired",
            "failure_kind": "unsupported_executor",
        }
    bound_lane = dict(lane)
    try:
        _bind_requested_grant(bound_lane)
    except (TypeError, ValueError, RuntimeError) as exc:
        return {
            "lane_id": lane_id,
            "command": [],
            "exit_code": None,
            "records": [],
            "stderr": str(exc),
            "unresolved": True,
            "capacity": "occupied",
            "failure_kind": "grant_invalid",
        }
    command = _launcher_command(
        bound_lane,
        python_executable=python_executable,
        launcher_path=launcher_path,
    )
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
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, reaped = _finish_timed_out_process(process, exc)
            parsed = parse_launcher_records(stdout, lane_id=lane_id)
            records = list(parsed["records"])
            records.append(_tagged(lane_id, "child_exit", {"exit_code": process.returncode}))
            if stderr:
                records.append(_tagged(lane_id, "stderr", {"text": stderr}))
            attempt_id = None
            preparation = parsed.get("preparation")
            registry = preparation.get("registry_launcher") if isinstance(preparation, Mapping) else None
            if isinstance(registry, Mapping):
                attempt_id = registry.get("attempt_id")
            records.append(_tagged(lane_id, "capacity", {"state": "occupied"}))
            records.append(_tagged(lane_id, "unresolved", {"reason": "transport timeout"}))
            return {
                "lane_id": lane_id,
                "command": command,
                "exit_code": process.returncode,
                "records": records,
                "preparation": parsed["preparation"],
                "assignment": parsed["assignment"],
                "malformed": parsed["malformed"],
                "stdout": stdout,
                "stderr": stderr,
                "attempt_id": attempt_id,
                "process_identity": _process_identity(process),
                "ownership": "reconciliation_required",
                "reconciliation_required": True,
                "unresolved": True,
                "capacity": "occupied",
                "failure_kind": "transport_timeout",
                "reaped": reaped,
                "grant_verification": "unverified",
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

    stdout = _text(stdout)
    stderr = _text(stderr)
    parsed = parse_launcher_records(stdout, lane_id=lane_id)
    records = list(parsed["records"])
    records.append(_tagged(lane_id, "child_exit", {"exit_code": process.returncode}))
    if stderr:
        records.append(_tagged(lane_id, "stderr", {"text": stderr}))

    def classify(assignment: Mapping[str, Any] | None) -> tuple[str, bool, str, bool]:
        if not isinstance(assignment, Mapping):
            return "occupied", True, "missing final assignment", False
        execution = assignment.get("execution")
        cleanup = assignment.get("cleanup")
        descendant_state = execution.get("descendant_state") if isinstance(execution, Mapping) else None
        resource_settled = (
            isinstance(execution, Mapping)
            and execution.get("state") in {"exited", "completed", "failed", "start_failed"}
            and descendant_state in {"terminated", "not_started"}
            and isinstance(cleanup, Mapping)
            and cleanup.get("state") == "removed"
            and cleanup.get("recovery_required") is False
        )
        if not resource_settled:
            return "occupied", True, "execution or cleanup unsettled", False
        if assignment.get("reconciliation_required") is True:
            return "retired", True, "task result unresolved", False
        task_result = assignment.get("task_result")
        task_uncertain = not isinstance(task_result, Mapping) or (
            task_result.get("accepted") is None
            or task_result.get("state") in {"unknown", "running", "preserved", "unverified"}
            or task_result.get("status") in {"unknown", "running", "preserved", "unverified"}
        )
        if task_uncertain:
            if isinstance(task_result, Mapping) and task_result.get("state") == "reported_completed" and task_result.get("accepted") is None:
                return "retired", False, "acceptance pending", True
            return "retired", True, "task result unresolved", False
        return "retired", False, "settled", False

    grant_mismatch = not _grant_evidence_matches(bound_lane, parsed)
    if grant_mismatch:
        capacity, unresolved, unresolved_reason, acceptance_pending = "occupied", True, "grant mismatch", False
    elif parsed["malformed"]:
        capacity, unresolved, unresolved_reason, acceptance_pending = "occupied", True, "malformed launcher evidence", False
    else:
        capacity, unresolved, unresolved_reason, acceptance_pending = classify(parsed["assignment"])
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
        "stdout": stdout,
        "stderr": stderr or "",
        "process_identity": _process_identity(process),
        "unresolved": unresolved,
        "capacity": capacity,
        "grant_verification": "verified" if not grant_mismatch else "unverified",
        "acceptance_pending": acceptance_pending,
    }
    if process.returncode:
        result["failure_kind"] = "command_exit"
    elif unresolved_reason == "grant mismatch":
        result["failure_kind"] = "grant_mismatch"
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
