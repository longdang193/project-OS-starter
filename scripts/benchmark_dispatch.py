"""Measure bounded dispatcher coordination with and without capacity refill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import time
from typing import Any

if __package__:
    from scripts import herdr_parallel_dispatch as dispatcher
else:
    import herdr_parallel_dispatch as dispatcher


def _lanes(root: Path, count: int) -> list[dict[str, Any]]:
    base = "0" * 40
    return [
        {
            "lane_id": f"benchmark-{index}",
            "repository_identity": "dispatcher-benchmark",
            "plan_identity": "dispatcher-benchmark",
            "task": f"benchmark task {index}",
            "executor": "deepagents",
            "profile": "normal",
            "worktree": str((root / f"lane-{index}").resolve()),
            "expected_base": base,
            "session": "benchmark",
            "pane": f"benchmark-{index}",
            "allowed_write_set": [f"benchmark/{index}.txt"],
            "dependencies": [],
            "dependency_ready": True,
            "fixed_contracts": ["parallel-dispatch-v1"],
            "mutable_resources": [f"benchmark:{index}"],
            "grant_turns": "native",
            "grant_wall_clock_seconds": "native",
            "grant_child_agents": "deny",
            "mcp_select": [],
            "remaining_authorized_task_allowance": 1800,
            "attempt_deadline": time.monotonic() + 1800,
        }
        for index in range(count)
    ]


def benchmark_dispatch(
    manifest_path: str | Path,
    *,
    repetitions: int = 30,
    max_concurrency: int = dispatcher.MAX_CONCURRENCY,
    mode: str = "baseline",
) -> dict[str, Any]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    if mode not in {"baseline", "refill", "four_lane"}:
        raise ValueError(f"unsupported benchmark mode: {mode}")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    count = int(manifest.get("lane_count", 8))
    sleep_seconds = float(manifest.get("workload_seconds", 0.01))
    root = Path(manifest_path).resolve().parent / ".runtime"
    root.mkdir(parents=True, exist_ok=True)
    lanes = _lanes(root, count)
    original_run_lane = dispatcher.run_lane

    def run_benchmark_lane(lane: dict[str, Any], **_: Any) -> dict[str, Any]:
        time.sleep(sleep_seconds)
        return {
            "lane_id": lane["lane_id"],
            "exit_code": 0,
            "records": [],
            "stderr": "",
            "unresolved": False,
            "capacity": "retired",
        }

    dispatcher.run_lane = run_benchmark_lane  # type: ignore[assignment]
    durations: list[float] = []
    completed_counts: list[int] = []
    try:
        for _ in range(repetitions):
            started = time.perf_counter()
            result = dispatcher.run_parallel(
                lanes,
                max_concurrency=max_concurrency,
                enable_refill=mode != "baseline",
            )
            durations.append(time.perf_counter() - started)
            completed_counts.append(len(result["results"]))
            if any(item.get("unresolved") for item in result["results"]):
                raise RuntimeError("benchmark produced unresolved lane evidence")
    finally:
        dispatcher.run_lane = original_run_lane  # type: ignore[assignment]
    mean_seconds = statistics.mean(durations)
    return {
        "mode": mode,
        "repetitions": repetitions,
        "lane_count": count,
        "max_concurrency": max_concurrency,
        "mean_seconds": mean_seconds,
        "p95_seconds": sorted(durations)[max(0, int(len(durations) * 0.95) - 1)],
        "throughput": statistics.mean(completed_counts) / mean_seconds,
        "completed_per_run": statistics.mean(completed_counts),
        "correctness": all(count == (count if mode == "baseline" else count) for count in completed_counts),
        "cleanup": "not_applicable_to_synthetic_worker",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--repetitions", type=int, default=30)
    run.add_argument("--max-concurrency", type=int, default=dispatcher.MAX_CONCURRENCY)
    run.add_argument("--mode", choices=("baseline", "refill", "four_lane"), default="baseline")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = benchmark_dispatch(
        args.manifest,
        repetitions=args.repetitions,
        max_concurrency=args.max_concurrency,
        mode=args.mode,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
