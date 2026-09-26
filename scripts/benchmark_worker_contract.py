"""Measure worker-contract handoff size without changing dispatch runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from statistics import median
from typing import Any, Mapping

try:
    from scripts.herdr_main_launcher import _project_runtime_grant
    from scripts.project_os_runtime.attempt import WHOLE_ATTEMPT_WALL_CLOCK_SECONDS
    from scripts.project_os_runtime.plan_preparation import prepare_plan_lanes
except ModuleNotFoundError:
    from herdr_main_launcher import _project_runtime_grant
    from project_os_runtime.attempt import WHOLE_ATTEMPT_WALL_CLOCK_SECONDS
    from project_os_runtime.plan_preparation import prepare_plan_lanes


def _load_tokenizer(name: str):
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError("offline measurement requires installed tiktoken") from exc
    try:
        encoding = tiktoken.get_encoding(name)
    except ValueError as exc:
        raise ValueError(f"unknown tokenizer encoding: {name}") from exc
    return encoding, tiktoken.__version__


def _metrics(text: str, encoding: Any) -> dict[str, Any]:
    encoded = text.encode("utf-8")
    return {
        "text_sha256": hashlib.sha256(encoded).hexdigest(),
        "utf8_bytes": len(encoded),
        "characters": len(text),
        "estimated_tokens": len(encoding.encode(text, disallowed_special=())),
    }


def _normalized_plan(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _task_scoped_reconstructed_plan(text: str, task_id: str) -> str:
    prefix = text.split("## Coordination State", 1)[0]
    match = re.search(
        rf"^### {re.escape(task_id)}:.*?(?=^### |^## Verification|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    verification = re.search(r"^## Verification.*\Z", text, re.MULTILINE | re.DOTALL)
    if match is None or verification is None:
        raise ValueError(f"cannot reconstruct baseline for {task_id}")
    return _normalized_plan(f"{prefix}\n## Task Breakdown\n{match.group(0)}\n{verification.group(0)}")


def _binding(task: Mapping[str, Any], manifest: Mapping[str, Any], fixture_root: Path) -> dict[str, Any]:
    task_id = str(task["task_id"])
    source_revision = str(manifest["source_revision"])
    custom = task.get("runtime_binding")
    if not isinstance(custom, Mapping):
        raise ValueError(f"runtime_binding missing for {task_id}")
    return {
        "repository_identity": "worker-contract-benchmark",
        "worktree": str(fixture_root.resolve()),
        "expected_base": source_revision,
        "session": "benchmark",
        "pane": f"benchmark-{task_id.lower().replace(' ', '-')}",
        "allowed_write_set": ["tests/fixtures/worker_contract_benchmark"],
        "fixed_contracts": ["worker-contract-benchmark-v1"],
        "mutable_resources": [f"benchmark:{task_id}"],
        "local_capabilities": {"requested": []},
        "remaining_authorized_task_allowance": WHOLE_ATTEMPT_WALL_CLOCK_SECONDS,
        "attempt_deadline": 4102444800.0,
        "runtime_grant": {
            "turns": "native",
            "wall_clock_seconds": "native",
            "delegation": {"child_agents": "deny"},
            "mcp_select": [],
        },
        "accepted_prerequisites": dict(custom["accepted_prerequisites"]),
    }


def _row(
    *,
    task_id: str,
    mode: str,
    brief: str,
    handoff: str,
    encoding: Any,
    tokenizer_version: str,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    brief_metrics = _metrics(brief, encoding)
    handoff_metrics = _metrics(handoff, encoding)
    return {
        "task_id": task_id,
        "mode": mode,
        "run": 0,
        "model_profile": "normal",
        "starting_revision": manifest["source_revision"],
        "baseline_name": manifest["baseline"]["name"],
        "tokenizer": manifest["tokenizer"],
        "tokenizer_version": tokenizer_version,
        "task_brief_tokens": brief_metrics["estimated_tokens"],
        "task_brief_characters": brief_metrics["characters"],
        "task_brief_utf8_bytes": brief_metrics["utf8_bytes"],
        "task_brief_sha256": brief_metrics["text_sha256"],
        "delivered_handoff_tokens": handoff_metrics["estimated_tokens"],
        "delivered_handoff_characters": handoff_metrics["characters"],
        "delivered_handoff_utf8_bytes": handoff_metrics["utf8_bytes"],
        "delivered_handoff_sha256": handoff_metrics["text_sha256"],
        "estimated_tokens": handoff_metrics["estimated_tokens"],
        "utf8_bytes": handoff_metrics["utf8_bytes"],
        "characters": handoff_metrics["characters"],
        "text_sha256": handoff_metrics["text_sha256"],
        "first_attempt_verified": "unknown",
        "eventual_verified": "unknown",
        "missing_context": "unknown",
        "missing_context_detail": "offline measurement; worker execution not attempted",
        "attempt_count": 0,
        "missing_context_retry_count": 0,
        "verification_references": [],
    }


def measure_offline(manifest_path: str | Path, tokenizer_name: str | None = None) -> list[dict[str, Any]]:
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported benchmark manifest schema")
    tokenizer = tokenizer_name or manifest.get("tokenizer", "cl100k_base")
    encoding, tokenizer_version = _load_tokenizer(tokenizer)
    fixture_root = manifest_path.parent
    plan_path = fixture_root / str(manifest["baseline"]["source"])
    plan_text = plan_path.read_text(encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for task in manifest["tasks"]:
        task_id = str(task["task_id"])
        binding = _binding(task, manifest, fixture_root)
        lane = prepare_plan_lanes(plan_path, [task_id], {task_id: binding})[0]
        bounded_brief = str(lane["task"])
        bounded_handoff = _project_runtime_grant(bounded_brief, lane["runtime_grant"])
        baseline_brief = _task_scoped_reconstructed_plan(plan_text, task_id)
        baseline_handoff = _project_runtime_grant(baseline_brief, lane["runtime_grant"])
        rows.extend(
            (
                _row(
                    task_id=task_id,
                    mode="baseline",
                    brief=baseline_brief,
                    handoff=baseline_handoff,
                    encoding=encoding,
                    tokenizer_version=tokenizer_version,
                    manifest=manifest,
                ),
                _row(
                    task_id=task_id,
                    mode="bounded",
                    brief=bounded_brief,
                    handoff=bounded_handoff,
                    encoding=encoding,
                    tokenizer_version=tokenizer_version,
                    manifest=manifest,
                ),
            )
        )
    return rows


def _write_jsonl(rows: list[dict[str, Any]], output: Path) -> None:
    output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _reduction(rows: list[dict[str, Any]]) -> float:
    baseline = next(row for row in rows if row["mode"] == "baseline")
    bounded = next(row for row in rows if row["mode"] == "bounded")
    if baseline["delivered_handoff_tokens"] <= 0:
        raise ValueError("baseline delivered handoff token count must be positive")
    return 1 - bounded["delivered_handoff_tokens"] / baseline["delivered_handoff_tokens"]


def _write_report(rows: list[dict[str, Any]], output: Path) -> None:
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_task.setdefault(str(row["task_id"]), []).append(row)
    reductions = [_reduction(task_rows) for task_rows in by_task.values()]
    baseline_total = sum(row["delivered_handoff_tokens"] for row in rows if row["mode"] == "baseline")
    bounded_total = sum(row["delivered_handoff_tokens"] for row in rows if row["mode"] == "bounded")
    aggregate = 1 - bounded_total / baseline_total if baseline_total else 0.0
    lines = [
        "# Worker Contract Communication Benchmark",
        "",
        f"- Tasks: {len(by_task)}",
        f"- Median delivered-handoff reduction: {median(reductions):.2%}",
        f"- Aggregate delivered-handoff reduction: {aggregate:.2%}",
        "",
        "| Task | Baseline handoff tokens | Bounded handoff tokens | Reduction |",
        "| --- | ---: | ---: | ---: |",
    ]
    for task_id in sorted(by_task):
        task_rows = by_task[task_id]
        baseline = next(row for row in task_rows if row["mode"] == "baseline")
        bounded = next(row for row in task_rows if row["mode"] == "bounded")
        lines.append(
            f"| {task_id} | {baseline['delivered_handoff_tokens']} | "
            f"{bounded['delivered_handoff_tokens']} | {_reduction(task_rows):.2%} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    offline = subparsers.add_parser("offline")
    offline.add_argument("--fixtures", type=Path, required=True)
    offline.add_argument("--output", type=Path, required=True)
    offline.add_argument("--tokenizer", default="cl100k_base")
    report = subparsers.add_parser("report")
    report.add_argument("--input", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "offline":
        rows = measure_offline(args.fixtures, args.tokenizer)
        _write_jsonl(rows, args.output)
        return 0
    _write_report(_read_jsonl(args.input), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
