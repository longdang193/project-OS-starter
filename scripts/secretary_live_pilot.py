"""Bounded, supervised Secretary trial accounting."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

try:
    from scripts.project_os_runtime.secretary_receipts import validate_live_receipt
except ModuleNotFoundError:
    from project_os_runtime.secretary_receipts import validate_live_receipt


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepare_manifest(*, task_id: str, plan_revision: str, workload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "project-os.secretary-live-workload.v1",
        "task_id": task_id,
        "plan_revision": plan_revision,
        "workload": dict(workload),
        "workload_digest": _digest(workload),
    }


def validate_receipt(receipt: Mapping[str, Any], *, attempt_id: str | None = None) -> dict[str, Any]:
    expected = {"attempt_id": attempt_id} if attempt_id else None
    return validate_live_receipt(receipt, expected=expected)


def admit_pilot(smoke_receipt: Mapping[str, Any]) -> dict[str, Any]:
    receipt = validate_receipt(smoke_receipt)
    if receipt["status"] != "READY":
        return {"admitted": False, "status": "BLOCKED_CAPABILITY", "trials_started": 0}
    return {"admitted": True, "status": "READY", "trials_started": 0}


def account_interrupted(record: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(record)
    result.update(
        {
            "outcome": "interrupted",
            "settlement": result.get("settlement", "unresolved"),
            "accounted": bool(result.get("attempt_id")),
            "duplicate_launch": False,
        }
    )
    return result


def _arm_totals(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    accepted = sum(record.get("acceptance") == "accepted" for record in records)
    costs = [record.get("cost") for record in records]
    total_cost = "unknown" if any(cost is None for cost in costs) else float(sum(costs))
    per_outcome = None if accepted == 0 else ("unknown" if total_cost == "unknown" else total_cost / accepted)
    return {
        "attempted": len(records),
        "accepted": accepted,
        "total_cost": total_cost,
        "cost_per_accepted_outcome": per_outcome,
        "human_interventions": sum(int(record.get("human_interventions", 0)) for record in records),
        "coordination_turns": sum(int(record.get("coordination_turns", 0)) for record in records),
    }


def compare_records(records: list[Mapping[str, Any]], *, minimum_valid_pairs: int = 3) -> dict[str, Any]:
    arms = {"baseline": [], "candidate": []}
    for record in records:
        arm = record.get("arm")
        if arm in arms:
            arms[arm].append(record)
    pair_map: dict[str, dict[str, Mapping[str, Any]]] = {}
    for record in records:
        pair_id = record.get("pair_id")
        arm = record.get("arm")
        if isinstance(pair_id, str) and arm in arms:
            pair_map.setdefault(pair_id, {})[arm] = record
    eligible: list[tuple[str, Mapping[str, Any], Mapping[str, Any]]] = []
    for pair_id, pair in pair_map.items():
        baseline = pair.get("baseline")
        candidate = pair.get("candidate")
        if not baseline or not candidate or baseline.get("workload_digest") != candidate.get("workload_digest"):
            continue
        if baseline.get("correctness") is True and candidate.get("correctness") is True:
            if baseline.get("acceptance") == "accepted" and candidate.get("acceptance") == "accepted":
                eligible.append((pair_id, baseline, candidate))
    failure_seen = any(record.get("correctness") is not True for record in records)
    costs_complete = all(
        isinstance(item.get("cost"), (int, float)) and not isinstance(item.get("cost"), bool)
        for pair in eligible
        for item in pair[1:]
    )
    if not records:
        status = "NOT_RUN"
    elif len(eligible) < minimum_valid_pairs:
        status = "INCONCLUSIVE"
    elif not costs_complete:
        status = "INCONCLUSIVE"
    elif failure_seen:
        status = "NO_MEASURED_BENEFIT"
    else:
        baseline_mean = sum(float(item[1].get("cost", 0)) for item in eligible) / len(eligible)
        candidate_mean = sum(float(item[2].get("cost", 0)) for item in eligible) / len(eligible)
        status = "VERIFIED_BENEFIT" if candidate_mean < baseline_mean else "NO_MEASURED_BENEFIT"
    return {
        "status": status,
        "attempted": len(records),
        "eligible_pairs": len(eligible),
        "arms": {name: _arm_totals(values) for name, values in arms.items()},
        "paired_deltas": [
            {
                "pair_id": pair_id,
                "candidate_minus_baseline_cost": (
                    candidate["cost"] - baseline["cost"]
                    if isinstance(candidate.get("cost"), (int, float))
                    and isinstance(baseline.get("cost"), (int, float))
                    else "unknown"
                ),
            }
            for pair_id, baseline, candidate in eligible
        ],
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "compare", "pilot"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--records", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("pilot_artifacts"))
    args = parser.parse_args(argv)
    if args.command == "prepare":
        if args.manifest is None:
            parser.error("--manifest required")
        payload = json.loads(args.manifest.read_text(encoding="utf-8"))
        _write_json(args.output_dir / "workload-manifest.json", payload)
        return 0
    if args.records is None:
        parser.error("--records required")
    records = json.loads(args.records.read_text(encoding="utf-8"))
    if args.command == "compare":
        _write_json(args.output_dir / "comparison-report.json", compare_records(records))
        return 0
    smoke_path = args.output_dir / "smoke-receipt.json"
    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
    smoke = validate_receipt(smoke)
    if smoke["status"] != "READY":
        _write_json(args.output_dir / "comparison-report.json", {"status": "BLOCKED_CAPABILITY", "reason": "smoke not ready"})
        return 0
    _write_json(args.output_dir / "comparison-report.json", compare_records(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
