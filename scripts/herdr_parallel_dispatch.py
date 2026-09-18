"""Run a bounded, foreground wave of Herdr launcher attempts."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

try:
    from project_os_runtime.lane import PreparedLane, prepare_lane
except ModuleNotFoundError:
    from scripts.project_os_runtime.lane import PreparedLane, prepare_lane
try:
    from project_os_runtime.attempt import (
        NATIVE_GRANT_VALUE,
        WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
        assignment_id as _assignment_id,
        grant_digest as _contract_grant_digest,
        normalize_runtime_grant,
        resolve_attempt_budget,
        settlement_decision,
        terminal_settlement_proven,
    )
except ModuleNotFoundError:
    from scripts.project_os_runtime.attempt import (
        NATIVE_GRANT_VALUE,
        WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
        assignment_id as _assignment_id,
        grant_digest as _contract_grant_digest,
        normalize_runtime_grant,
        resolve_attempt_budget,
        settlement_decision,
        terminal_settlement_proven,
    )
try:
    from project_os_runtime.admission import (
        AdmissionBatch,
        AdmissionResult,
        canonical_token,
        classify_admission,
        legacy_admission_lists,
        resource_sets_conflict,
        validate_admission_results,
    )
except ModuleNotFoundError:
    from scripts.project_os_runtime.admission import (
        AdmissionBatch,
        AdmissionResult,
        canonical_token,
        classify_admission,
        legacy_admission_lists,
        resource_sets_conflict,
        validate_admission_results,
    )


MAX_CONCURRENCY = 2
_LOCAL_CAPABILITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._+-]*$")
TIMEOUT_OWNER = "dcode-project"
_REAPING_RESERVE_SECONDS = 30.0
_DISPATCH_DEADLINE_SECONDS = 5.0


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_descriptors(source: str | os.PathLike[str]) -> list[dict[str, Any]]:
    payload = json.loads(Path(source).read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        payload = payload.get("lanes")
    if not isinstance(payload, list) or not all(isinstance(item, Mapping) for item in payload):
        raise ValueError("lane descriptor file must contain a list of objects")
    return [dict(item) for item in payload]


def _canonical_path(value: object) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(value))))


def _grant_digest(executor: str, runtime_grant: Mapping[str, Any]) -> str:
    return _contract_grant_digest(executor, runtime_grant)


def _reject(lane: Mapping[str, Any], reason: str) -> dict[str, str]:
    return {"lane_id": str(lane.get("lane_id", "<missing>")), "reason": reason}


def _admit_lanes(
    lanes: Iterable[Mapping[str, Any]],
    *,
    max_concurrency: int = MAX_CONCURRENCY,
) -> dict[str, list[dict[str, Any]]]:
    raw_lanes = [dict(raw_lane) for raw_lane in lanes]
    batch = _prepare_admission(raw_lanes, max_concurrency=max_concurrency)
    lanes_by_id = {
        str(raw_lane.get("lane_id", f"<missing:{index}>")): raw_lane
        for index, raw_lane in enumerate(raw_lanes)
    }
    lanes_by_id.update({str(lane["lane_id"]): lane for lane in batch.prepared})
    return legacy_admission_lists(batch.results, lanes_by_id)


def _prepare_admission(
    lanes: Iterable[Mapping[str, Any]],
    *,
    max_concurrency: int = MAX_CONCURRENCY,
) -> AdmissionBatch:
    capacity = min(max_concurrency, MAX_CONCURRENCY)
    if capacity < 1:
        raise ValueError("max_concurrency must be positive")

    raw_lanes = [dict(raw_lane) for raw_lane in lanes]
    lane_ids = [
        str(lane["lane_id"]) if isinstance(lane.get("lane_id"), str) and lane["lane_id"].strip()
        else f"<missing:{index}>"
        for index, lane in enumerate(raw_lanes)
    ]
    duplicate_ids = {lane_id for lane_id in lane_ids if lane_ids.count(lane_id) > 1}
    lanes_by_id: dict[str, Mapping[str, Any]] = {}
    for lane_id, lane in zip(lane_ids, raw_lanes):
        lanes_by_id.setdefault(lane_id, lane)
    admission_results: list[AdmissionResult] = []
    recorded_ids: set[str] = set()

    def record(result: AdmissionResult) -> None:
        if result.lane_id not in recorded_ids:
            admission_results.append(result)
            recorded_ids.add(result.lane_id)

    admitted: list[PreparedLane] = []
    seen_worktrees: dict[str, str] = {}
    seen_panes: dict[str, str] = {}
    shared_contracts: tuple[str, ...] | None = None

    for raw_lane, lane_id in zip(raw_lanes, lane_ids):
        lane: Mapping[str, Any] = raw_lane
        if lane_id in duplicate_ids:
            record(classify_admission(lane_id, duplicate_id=True))
            continue
        if lane.get("executor") != "deepagents":
            record(classify_admission(lane_id, executor=lane.get("executor")))
            continue
        if lane.get("dependency_ready") is not True:
            record(classify_admission(lane_id, dependency_ready=False))
            continue
        preparation_error: str | None = None
        try:
            if not isinstance(lane, PreparedLane):
                lane = prepare_lane(lane)
            resolve_attempt_budget(
                lane["grant_wall_clock_seconds"],
                lane["remaining_authorized_task_allowance"],
                WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
            )
        except (TypeError, ValueError, RuntimeError) as exc:
            preparation_error = str(exc)
        if preparation_error is not None:
            record(classify_admission(lane_id, preparation_error=preparation_error))
            continue

        worktree = _canonical_path(lane["worktree"])
        pane = canonical_token(lane["pane"])
        conflict_reason: str | None = None
        if pane in seen_panes:
            conflict_reason = "pane conflicts with " + seen_panes[pane]
        contracts = tuple(sorted(map(str, lane["fixed_contracts"])))
        if shared_contracts is None:
            shared_contracts = contracts
            fixed_contracts_match = True
        elif contracts != shared_contracts:
            fixed_contracts_match = False
        else:
            fixed_contracts_match = True
        if conflict_reason is None and worktree in seen_worktrees:
            conflict_reason = "worktree conflicts with " + seen_worktrees[worktree]
        if conflict_reason is None and any(
            resource_sets_conflict(lane["allowed_write_set"], other["allowed_write_set"])
            or resource_sets_conflict(lane["mutable_resources"], other["mutable_resources"])
            for other in admitted
        ):
            conflict_reason = "write set or mutable resource conflicts"
        result = classify_admission(
            lane_id,
            conflict_reason=conflict_reason,
            fixed_contracts_match=fixed_contracts_match,
            capacity_available=len(admitted) < capacity,
            capacity_reason=f"capacity limit {capacity}",
        )
        record(result)
        if result.state == "ADMITTED":
            admitted.append(lane)
            seen_worktrees[worktree] = lane_id
            seen_panes[pane] = lane_id

    return AdmissionBatch(tuple(admitted), validate_admission_results(admission_results))


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
    assignment_value = lane.get("assignment_id") or _assignment_id(
        lane["repository_identity"], lane["plan_identity"], str(lane["lane_id"])
    )
    grant = lane.get("runtime_grant")
    if not isinstance(grant, Mapping):
        lane = prepare_lane(lane)
        grant = lane["runtime_grant"]
    grant_digest_value = lane.get("grant_digest") or _grant_digest(
        str(lane["executor"]), grant
    )
    prior_attempt_known = lane.get("prior_attempt_known", False)
    if not isinstance(prior_attempt_known, bool):
        raise ValueError("prior_attempt_known must be boolean")
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
        "--assignment-id",
        str(assignment_value),
        "--repository-identity",
        str(lane["repository_identity"]),
        "--plan-identity",
        str(lane["plan_identity"]),
        "--task-sha256",
        _sha256_text(str(lane["task"])),
        "--grant-digest",
        str(grant_digest_value),
        "--executor",
        str(lane["executor"]),
        "--task",
        str(lane["task"]),
        "--prior-attempt-known",
        str(prior_attempt_known).lower(),
        "--remaining-authorized-task-allowance",
        str(lane["remaining_authorized_task_allowance"]),
    ]
    for name, flag in (("name", "--name"), ("codex_home", "--codex-home")):
        if lane.get(name):
            command.extend([flag, str(lane[name])])
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


def _read_capture(stream: Any) -> str:
    flush = getattr(stream, "flush", None)
    if callable(flush):
        flush()
    seek = getattr(stream, "seek", None)
    read = getattr(stream, "read", None)
    if not callable(seek) or not callable(read):
        return ""
    seek(0)
    return _text(read())


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


def _effective_budget_is_contained(
    requested: Mapping[str, Any],
    observed: Mapping[str, Any],
) -> bool:
    for name in ("turns", "wall_clock_seconds"):
        requested_budget = requested.get(name)
        observed_budget = observed.get(name)
        if not isinstance(requested_budget, Mapping) or not isinstance(observed_budget, Mapping):
            return False
        requested_value = requested_budget.get("requested")
        effective_value = observed_budget.get("effective")
        if observed_budget.get("requested") != requested_value:
            return False
        if effective_value == NATIVE_GRANT_VALUE:
            if requested_value != NATIVE_GRANT_VALUE:
                return False
            continue
        if (
            isinstance(effective_value, bool)
            or not isinstance(effective_value, int)
            or effective_value <= 0
        ):
            return False
        if requested_value != NATIVE_GRANT_VALUE and effective_value > requested_value:
            return False
    return True


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
    try:
        stable_digest = _contract_grant_digest(str(lane.get("executor", "deepagents")), prep_grant)
    except (TypeError, ValueError):
        return False
    grant_matches = (
        isinstance(registry, Mapping)
        and isinstance(assignment, Mapping)
        and isinstance(prep_grant, Mapping)
        and stable_digest == expected_digest
        and prep_digest == expected_digest
        and assignment_digest == expected_digest
        and _effective_budget_is_contained(expected, prep_grant)
    )
    if not isinstance(expected_capabilities, Mapping) or not expected_capabilities.get("requested"):
        return grant_matches
    prep_capabilities = registry.get("local_capabilities") if isinstance(registry, Mapping) else None
    assignment_capabilities = assignment if isinstance(assignment, Mapping) else None
    return (
        grant_matches
        and _capability_evidence_matches(expected_capabilities, prep_capabilities)
        and _worker_capability_evidence_matches(expected_capabilities, assignment_capabilities)
    )


def _capability_evidence_matches(
    expected: Mapping[str, Any], actual: object
) -> bool:
    if not isinstance(actual, Mapping):
        return False
    for key in ("requested", "effective", "verification_commands", "source_task_sha256", "digest"):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    for key in ("passed_to_worker", "validated_available"):
        if key in actual and actual.get(key) != expected.get("effective", []):
            return False
    return True


def _worker_capability_evidence_matches(
    expected: Mapping[str, Any], assignment: object
) -> bool:
    if not isinstance(assignment, Mapping) or assignment.get("capability_state") != "confirmed":
        return False
    actual = assignment.get("capabilities")
    if not isinstance(actual, Mapping):
        return False
    return (
        actual.get("requested") == expected.get("requested", [])
        and actual.get("passed_to_worker") == expected.get("effective", [])
        and actual.get("validated_available") == expected.get("effective", [])
        and actual.get("digest") == expected.get("digest")
        and actual.get("validation_error") is None
    )


def _receipt_correlation_matches(lane: Mapping[str, Any], parsed: Mapping[str, Any]) -> bool:
    preparation = parsed.get("preparation")
    assignment = parsed.get("assignment")
    registry = preparation.get("registry_launcher") if isinstance(preparation, Mapping) else None
    if not isinstance(registry, Mapping) or not isinstance(assignment, Mapping):
        return False
    expected_assignment = str(lane.get("assignment_id") or _assignment_id(
        lane["repository_identity"], lane["plan_identity"], str(lane["lane_id"])
    ))
    expected_task = _sha256_text(str(lane["task"]))
    attempt_id = registry.get("attempt_id")
    return all(
        value in (None, expected)
        for value, expected in (
            (registry.get("assignment_id"), expected_assignment),
            (assignment.get("assignment_id"), expected_assignment),
            (registry.get("assignment_task_sha256"), expected_task),
            (assignment.get("task_sha256"), expected_task),
            (assignment.get("attempt_id"), attempt_id),
        )
    )


def runtime_completion_is_not_acceptance(record: Mapping[str, Any]) -> bool:
    return record.get("status") == "reported_completed" and record.get("accepted") is not True


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
    if timeout_seconds is None:
        deadline = lane.get("attempt_deadline")
        if isinstance(deadline, bool) or not isinstance(deadline, (int, float)) or not math.isfinite(float(deadline)):
            return {
                "lane_id": lane_id,
                "command": [],
                "exit_code": None,
                "records": [],
                "stderr": "missing finite attempt deadline",
                "unresolved": False,
                "capacity": "retired",
                "failure_kind": "deadline_missing",
            }
        timeout_seconds = max(0.0, float(deadline) - time.monotonic()) + _REAPING_RESERVE_SECONDS
    dispatch_started = time.monotonic()
    attempt_deadline = lane.get("attempt_deadline")
    dispatch_deadline = dispatch_started + _DISPATCH_DEADLINE_SECONDS
    if isinstance(attempt_deadline, (int, float)) and not isinstance(attempt_deadline, bool):
        dispatch_deadline = min(dispatch_deadline, float(attempt_deadline))
    if not isinstance(lane, PreparedLane):
        try:
            lane = prepare_lane(lane)
        except (TypeError, ValueError, RuntimeError) as exc:
            return {
                "lane_id": lane_id,
                "command": [],
                "exit_code": None,
                "records": [],
                "stderr": str(exc),
                "unresolved": False,
                "capacity": "retired",
                "failure_kind": "grant_invalid",
            }
    try:
        command = _launcher_command(
            lane,
            python_executable=python_executable,
            launcher_path=launcher_path,
        )
    except (TypeError, ValueError, OSError, RuntimeError) as exc:
        return {
            "lane_id": lane_id,
            "command": [],
            "exit_code": None,
            "records": [],
            "stderr": str(exc),
            "unresolved": False,
            "capacity": "retired",
            "failure_kind": "launch_preparation_failed",
        }
    capture_dir = Path(tempfile.mkdtemp(prefix=f"herdr-timeout-{lane_id}-"))
    stdout_path = capture_dir / "stdout.log"
    stderr_path = capture_dir / "stderr.log"
    handoff_path = capture_dir / "handoff.json"
    try:
        with stdout_path.open("w+", encoding="utf-8") as stdout_file, stderr_path.open(
            "w+", encoding="utf-8"
        ) as stderr_file:
            if time.monotonic() >= dispatch_deadline:
                return {
                    "lane_id": lane_id,
                    "command": command,
                    "exit_code": None,
                    "records": [_tagged(lane_id, "capacity", {"state": "retired"})],
                    "stderr": "dispatch deadline exceeded before worker launch",
                    "unresolved": False,
                    "capacity": "retired",
                    "failure_kind": "dispatch_deadline_exceeded",
                }
            process = popen_factory(
                command,
                cwd=str(lane["worktree"]),
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                encoding="utf-8",
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
                stdout = _merge_streams(stdout, _read_capture(stdout_file))
                stderr = _merge_streams(stderr, _read_capture(stderr_file))
                if getattr(process, "returncode", None) is None:
                    raise subprocess.TimeoutExpired(
                        command,
                        timeout_seconds,
                        output=stdout,
                        stderr=stderr,
                    )
            except subprocess.TimeoutExpired as exc:
                stdout, stderr, reaped = _finish_timed_out_process(process, exc)
                stdout = _merge_streams(stdout, _read_capture(stdout_file))
                stderr = _merge_streams(stderr, _read_capture(stderr_file))
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
                timeout_evidence = {
                    "owner": TIMEOUT_OWNER,
                    "pid": _process_identity(process).get("pid"),
                    "attempt_id": attempt_id,
                    "capacity": "occupied",
                    "reaped": reaped,
                    "paths": {
                        "stdout": str(stdout_path),
                        "stderr": str(stderr_path),
                        "handoff": str(handoff_path),
                    },
                }
                handoff_path.write_text(json.dumps(timeout_evidence, sort_keys=True), encoding="utf-8")
                records.append(_tagged(lane_id, "capacity", {"state": "occupied"}))
                records.append(_tagged(lane_id, "unresolved", {"reason": "transport timeout"}))
                return {
                    "lane_id": lane_id,
                    "assignment_id": lane.get("assignment_id"),
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
                    "timeout_evidence": timeout_evidence,
                    "grant_verification": "unverified",
                }
    except OSError as exc:
        shutil.rmtree(capture_dir, ignore_errors=True)
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

    shutil.rmtree(capture_dir, ignore_errors=True)
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
        lifecycle_receipt = assignment.get("lifecycle_receipt")
        if not isinstance(lifecycle_receipt, Mapping):
            return "occupied", True, "lifecycle receipt unavailable", False
        if "state" not in lifecycle_receipt and "worker_state" in lifecycle_receipt:
            lifecycle_receipt = {"state": "confirmed", **lifecycle_receipt}
        settlement = settlement_decision(lifecycle_receipt)
        if not settlement["resource_settled"]:
            return "occupied", True, settlement["reason"], False
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

    grant_mismatch = not _grant_evidence_matches(lane, parsed)
    if not _receipt_correlation_matches(lane, parsed):
        capacity, unresolved, unresolved_reason, acceptance_pending = "occupied", True, "receipt correlation mismatch", False
    elif parsed["malformed"]:
        capacity, unresolved, unresolved_reason, acceptance_pending = "occupied", True, "malformed launcher evidence", False
    else:
        capacity, unresolved, unresolved_reason, acceptance_pending = classify(parsed["assignment"])
    records.append(_tagged(lane_id, "capacity", {"state": capacity}))
    if unresolved:
        records.append(_tagged(lane_id, "unresolved", {"reason": unresolved_reason}))
    result = {
        "lane_id": lane_id,
        "assignment_id": lane.get("assignment_id"),
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
        "verification_failure": "grant_mismatch" if grant_mismatch else None,
        "acceptance_pending": acceptance_pending,
    }
    if process.returncode:
        result["failure_kind"] = "command_exit"
    elif unresolved_reason == "receipt correlation mismatch":
        result["failure_kind"] = "receipt_correlation_mismatch"
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
    event_callback: Any | None = None,
    **run_kwargs: Any,
) -> dict[str, Any]:
    """Run admitted lanes concurrently; return derived evidence only."""

    supplied_categories: dict[str, list[Mapping[str, Any]]] = {}
    if isinstance(source, (str, os.PathLike)):
        raw_lanes = _read_descriptors(source)
    elif isinstance(source, Mapping) and "admitted" in source:
        admitted = source["admitted"]
        if not isinstance(admitted, list):
            raise ValueError("admitted lanes must be a list")
        raw_lanes = admitted
        for category in ("deferred", "blocked", "rejected"):
            supplied = source.get(category, [])
            if not isinstance(supplied, list):
                raise ValueError(f"{category} lanes must be a list")
            supplied_categories[category] = supplied
    else:
        raw_lanes = list(source)

    batch = _prepare_admission(raw_lanes, max_concurrency=max_concurrency)
    lanes_by_id = {str(lane["lane_id"]): lane for lane in batch.prepared}
    admission = legacy_admission_lists(batch.results, lanes_by_id)
    admission["admitted"] = list(batch.prepared)
    for category, supplied in supplied_categories.items():
        admission[category] = list(supplied) + admission.get(category, [])

    if not 1 <= max_concurrency <= MAX_CONCURRENCY:
        raise ValueError(f"max_concurrency must be between 1 and {MAX_CONCURRENCY}")

    callback_errors: list[dict[str, Any]] = []

    def emit(event: dict[str, Any]) -> None:
        if event_callback is None:
            return
        try:
            event_callback(event)
        except BaseException as exc:
            callback_errors.append({"event": event, "error": str(exc)})

    for category in ("admitted", "deferred", "blocked", "rejected"):
        for item in admission.get(category, []):
            lane_id = str(item.get("lane_id", "<missing>"))
            emit({
                "tag": "lane_admission",
                "category": category,
                "lane_id": lane_id,
                "lane": item.to_dict() if isinstance(item, PreparedLane) else item,
            })

    results: dict[str, dict[str, Any]] = {}
    completion_order: list[str] = []
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
                completion_order.append(lane_id)
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
                completion_order.append(lane_id)
            emit({"tag": "lane_result", **results[lane_id]})
    return {
        "admitted": admission["admitted"],
        "deferred": admission.get("deferred", []),
        "blocked": admission.get("blocked", []),
        "rejected": admission["rejected"],
        "interrupted": interrupted,
        "callback_errors": callback_errors,
        "results": [
            results[lane_id]
            for lane_id in completion_order
            if lane_id in results
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes-file", required=True, type=Path)
    parser.add_argument("--max-concurrency", type=int, default=MAX_CONCURRENCY)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_parallel(
        args.lanes_file,
        max_concurrency=args.max_concurrency,
        event_callback=lambda event: print(json.dumps(event, sort_keys=True), flush=True),
    )
    admission_failure = bool(result["rejected"] or result.get("blocked"))
    runtime_failure = any(item.get("unresolved") for item in result["results"])
    return 2 if admission_failure or runtime_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
