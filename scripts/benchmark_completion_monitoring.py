"""Run deterministic baseline/candidate completion-monitoring probes."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any


CASES: dict[str, dict[str, Any]] = {
    "process_info_stall_receipt": {"receipt_at": 0.25, "stall": "process-info", "expected": "completed"},
    "pane_read_stall_receipt": {"receipt_at": 0.25, "stall": "read", "expected": "completed"},
    "both_diagnostics_timeout_no_receipt": {"receipt_at": None, "stall": "both", "expected": "no-report"},
    "diagnostic_error_late_receipt": {"receipt_at": 0.25, "error": "process-info", "expected": "completed"},
    "normal_success": {"receipt_at": 0.2, "expected": "completed"},
    "terminal_process_without_receipt": {"receipt_at": None, "terminal": True, "expected": "completed"},
}


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += max(0.0, seconds)


class FakeHerdr:
    def __init__(self, module: Any, case: dict[str, Any], clock: Clock) -> None:
        self.module = module
        self.case = case
        self.clock = clock
        self.counts = {"wait-output": 0, "process-info": 0, "read": 0}
        self.timeout_count = 0

    def receipt(self) -> dict[str, Any]:
        receipt_at = self.case["receipt_at"]
        if receipt_at is None or self.clock.now < receipt_at:
            return {"state": "unknown", "detail": "harness-controlled unavailable"}
        return {
            "state": "confirmed",
            "worker_state": "exited",
            "worker_exit_code": 0,
            "descendant_state": "terminated",
            "cleanup_state": "removed",
            "role_views_state": "removed",
            "recovery_required": False,
        }

    def run(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        action = next((name for name in self.counts if name in command), "other")
        if action in self.counts:
            self.counts[action] += 1
        timeout = float(kwargs.get("timeout") or 0.0)
        if action == "wait-output":
            return subprocess.CompletedProcess(command, 1, "", "marker wait disabled")
        if action == "process-info" and self.case.get("error") == "process-info":
            self.clock.sleep(0.05)
            return subprocess.CompletedProcess(command, 1, "", "diagnostic error")
        if action == "process-info" and self.case.get("stall") in {"process-info", "both"}:
            self.timeout_count += 1
            self.clock.sleep(timeout)
            raise self.module.CommandTransportTimeout("deterministic diagnostic stall")
        if action == "read" and self.case.get("stall") in {"read", "both"}:
            self.timeout_count += 1
            self.clock.sleep(timeout)
            raise self.module.CommandTransportTimeout("deterministic diagnostic stall")
        self.clock.sleep(0.05)
        if action == "process-info":
            foreground = [] if self.case.get("terminal") else []
            payload = {"result": {"process_info": {"foreground_processes": foreground}}}
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        if action == "read":
            output = "Running task non-interactively...\nCOMPLETED\nMARKER"
            return subprocess.CompletedProcess(command, 0, json.dumps({"result": output}), "")
        return subprocess.CompletedProcess(command, 0, "", "")


def load_module(name: str, source: str, directory: Path) -> Any:
    path = directory / f"{name}.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_at_revision(revision: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{revision}:scripts/herdr_main_launcher.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def revision() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def run_case(module: Any, case: dict[str, Any]) -> dict[str, Any]:
    clock = Clock()
    fake = FakeHerdr(module, case, clock)
    original_time = module.time
    original_run = module._run
    original_receipt = module._read_deepagents_receipt
    try:
        module.time = clock
        module._run = fake.run
        module._read_deepagents_receipt = lambda *_args, **_kwargs: fake.receipt()
        result = module._deepagents_completion_evidence(
            "herdr.exe",
            "session",
            "pane",
            env={},
            expected_marker="MARKER",
            receipt_file=Path("harness-receipt.json"),
            attempt_id="harness-attempt",
            completion_wait_seconds=2.0,
            diagnostic_poll_seconds=2.0,
        )
    finally:
        module.time = original_time
        module._run = original_run
        module._read_deepagents_receipt = original_receipt
    monitoring = result.get("monitoring", {})
    receipt = result.get("lifecycle_receipt", {})
    observed_receipt = monitoring.get("receipt_observed_at")
    returned_at = monitoring.get("completion_returned_at")
    time_to_receipt = monitoring.get("time_to_receipt_ms", monitoring.get("detection_delay_ms"))
    receipt_to_return = monitoring.get("receipt_to_completion_return_ms")
    if receipt_to_return is None and observed_receipt is not None and returned_at is not None:
        receipt_to_return = round(max(0.0, returned_at - observed_receipt) * 1000, 3)
    cleanup = receipt.get("cleanup_state") if isinstance(receipt, dict) else None
    reconciliation = "not-required" if isinstance(receipt, dict) and receipt.get("recovery_required") is False else "receipt-fallback"
    if not isinstance(receipt, dict) or receipt.get("state") != "confirmed":
        cleanup = "missing-receipt-fallback"
    return {
        "subprocess_counts": fake.counts,
        "subprocess_total": sum(fake.counts.values()),
        "timeout_count": fake.timeout_count,
        "receipt_checks": monitoring.get("receipt_checks", 0),
        "diagnostic_probe_count": monitoring.get("diagnostic_probe_count", 0),
        "time_to_receipt_ms": time_to_receipt,
        "receipt_to_completion_return_ms": receipt_to_return,
        "lifecycle": result.get("state"),
        "expected_lifecycle": case["expected"],
        "outcome_match": result.get("state") == case["expected"],
        "cleanup": cleanup,
        "reconciliation": reconciliation,
        "elapsed_seconds": round(clock.now, 3),
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    return values[max(0, math.ceil(len(values) * fraction) - 1)]


def stats(rows: list[dict[str, Any]], field: str) -> dict[str, float | None]:
    values = sorted(float(row[field]) for row in rows if row.get(field) is not None)
    return {"median": median(values), "p95": percentile(values, 0.95)}


def median(values: list[float]) -> float:
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-revision", required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.repetitions < 1:
        raise SystemExit("--repetitions must be positive")
    candidate_source = (Path(__file__).resolve().parent / "herdr_main_launcher.py").read_text(encoding="utf-8")
    baseline_source = source_at_revision(args.baseline_revision)
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        baseline = load_module("completion_baseline", baseline_source, temporary_path)
        candidate = load_module("completion_candidate", candidate_source, temporary_path)
        rows: list[dict[str, Any]] = []
        for case_name, case in CASES.items():
            for repetition in range(1, args.repetitions + 1):
                baseline_result = run_case(baseline, case)
                candidate_result = run_case(candidate, case)
                for mode, result in (("baseline", baseline_result), ("candidate", candidate_result)):
                    rows.append({"mode": mode, "case": case_name, "repetition": repetition, **result})
    pairs = []
    for case_name in CASES:
        for repetition in range(1, args.repetitions + 1):
            pair = [row for row in rows if row["case"] == case_name and row["repetition"] == repetition]
            base, cand = next(row for row in pair if row["mode"] == "baseline"), next(row for row in pair if row["mode"] == "candidate")
            pairs.append({
                "case": case_name,
                "repetition": repetition,
                "lifecycle_match": base["lifecycle"] == cand["lifecycle"],
                "cleanup_match": base["cleanup"] == cand["cleanup"],
                "reconciliation_match": base["reconciliation"] == cand["reconciliation"],
            })
    harness_payload = {"cases": CASES, "budgets": {"diagnostic_timeout_seconds": 0.5, "receipt_poll_seconds": 0.1, "diagnostic_poll_seconds": 2.0}}
    harness_digest = hashlib.sha256(json.dumps(harness_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    summary = {}
    for mode in ("baseline", "candidate"):
        mode_rows = [row for row in rows if row["mode"] == mode]
        summary[mode] = {
            "subprocess_total": stats(mode_rows, "subprocess_total"),
            "time_to_receipt_ms": stats(mode_rows, "time_to_receipt_ms"),
            "receipt_to_completion_return_ms": stats(mode_rows, "receipt_to_completion_return_ms"),
            "timeout_count": sum(row["timeout_count"] for row in mode_rows),
            "lifecycle_mismatches": sum(not row["outcome_match"] for row in mode_rows),
            "max_elapsed_seconds": max(row["elapsed_seconds"] for row in mode_rows),
            "receipt_case_max_elapsed_seconds": max(
                row["elapsed_seconds"] for row in mode_rows if CASES[row["case"]]["receipt_at"] is not None
            ),
        }
    output = {
        "schema": "completion-monitoring-evidence/v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "os": platform.platform(),
        "baseline_revision": args.baseline_revision,
        "candidate_revision": revision(),
        "baseline_source_sha256": hashlib.sha256(baseline_source.encode()).hexdigest(),
        "candidate_source_sha256": hashlib.sha256(candidate_source.encode()).hexdigest(),
        "harness": "stdlib deterministic fake-Herdr command/receipt seam",
        "harness_digest": harness_digest,
        "fixed_budgets": harness_payload["budgets"],
        "cases": list(CASES),
        "repetitions_per_case_and_side": args.repetitions,
        "rows": rows,
        "pairs": pairs,
        "summary": summary,
        "correctness": {
            "lifecycle_mismatches": sum(not pair["lifecycle_match"] for pair in pairs),
            "cleanup_mismatches": sum(not pair["cleanup_match"] for pair in pairs),
            "reconciliation_mismatches": sum(not pair["reconciliation_match"] for pair in pairs),
            "all_outcomes_match": all(row["outcome_match"] for row in rows),
        },
        "receipt_availability": "harness control data; not production receipt-publication evidence",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
