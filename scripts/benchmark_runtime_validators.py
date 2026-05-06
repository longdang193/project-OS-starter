"""
@meta
name: benchmark_runtime_validators
type: script
domain: docs
responsibility:
  - Benchmark runtime-governance validator commands with repeatable median/p95 timing.
  - Provide machine-readable and human-readable benchmark output for optimization tracking.
inputs:
  - scripts/validate_repo_contracts.py
  - scripts/sync_agent_adapters.py
  - scripts/validate_adoption_shape.py
  - scripts/validate_agent_runtime_drift.py
outputs:
  - Console benchmark report and optional JSON report file.
tags:
  - performance
  - benchmarking
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark runtime validator commands.")
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per command.")
    parser.add_argument("--json-out", default="", help="Optional JSON output path.")
    return parser


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    rank = (len(ordered) - 1) * p
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def run_once(command: list[str], cwd: Path) -> tuple[float, int]:
    start = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    return elapsed, completed.returncode


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve()
    py = sys.executable
    commands = [
        [py, "scripts/validate_repo_contracts.py", "--fast"],
        [py, "scripts/sync_agent_adapters.py", "--check"],
        [py, "scripts/validate_adoption_shape.py"],
        [py, "scripts/validate_agent_runtime_drift.py", "--skip-deploy-check"],
    ]

    results: list[dict[str, object]] = []
    overall_status = 0
    for cmd in commands:
        timings: list[float] = []
        return_codes: list[int] = []
        for _ in range(max(args.runs, 1)):
            elapsed, rc = run_once(cmd, root)
            timings.append(elapsed)
            return_codes.append(rc)
            if rc != 0:
                overall_status = rc

        record = {
            "command": " ".join(cmd),
            "runs": len(timings),
            "return_codes": return_codes,
            "mean_seconds": round(statistics.fmean(timings), 4),
            "median_seconds": round(statistics.median(timings), 4),
            "p95_seconds": round(percentile(timings, 0.95), 4),
            "min_seconds": round(min(timings), 4),
            "max_seconds": round(max(timings), 4),
        }
        results.append(record)

    print("Runtime validator benchmark:")
    for item in results:
        print(
            "- {command}\n"
            "  runs={runs} rc={return_codes} median={median_seconds}s p95={p95_seconds}s"
            .format(**item)
        )

    if args.json_out:
        out_path = (root / args.json_out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Wrote JSON report: {out_path.as_posix()}")

    return overall_status


if __name__ == "__main__":
    raise SystemExit(main())
