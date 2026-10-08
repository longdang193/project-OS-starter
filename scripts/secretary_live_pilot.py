from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from statistics import median
from typing import Any, Mapping

try:
    from scripts.project_os_runtime.secretary_receipts import (
        ReceiptValidationError,
        validate_live_receipt,
    )
except ModuleNotFoundError:
    from project_os_runtime.secretary_receipts import (
        ReceiptValidationError,
        validate_live_receipt,
    )


DEFAULT_MANIFEST = {
    "schema_version": "secretary-live-pilot-v1",
    "max_attempted_pairs": 5,
    "minimum_valid_pairs": 3,
    "max_arm_runs": 10,
    "max_total_wall_clock_minutes": 180,
    "primary_metric": "human_interventions_per_accepted_workstream",
    "benefit_min_intervention_reduction": 1,
    "max_candidate_completion_regression": 0.10,
}
REQUIRED_SOURCE_KEYS = ("launch", "task_result", "settlement", "acceptance")
SOURCE_BINDING_FIELDS = (
    "pair_id",
    "arm",
    "run_id",
    "assignment_id",
    "attempt_id",
    "task_id",
    "plan_identity",
    "plan_revision",
    "repository_identity",
    "workstream",
    "git_revision",
    "worktree",
    "controller_id",
    "session_id",
    "checkpoint",
)
REQUIRED_TIMESTAMP_KEYS = (
    "run_started",
    "first_useful_worker",
    "publication",
    "settlement",
    "acceptance",
    "run_finished",
)
PRODUCERS = {
    "launch": "herdr_main_launcher",
    "task_result": "dcode-project",
    "settlement": "project_os_runtime.attempt",
    "acceptance": "cos",
}


class PilotReceiptError(ValueError):
    pass


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PilotReceiptError(f"{label} must be non-empty text")
    return value.strip()


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotReceiptError(f"invalid evidence source: {path}") from exc
    if not isinstance(value, dict):
        raise PilotReceiptError(f"evidence source must be an object: {path}")
    return value


def _iso(value: Any, label: str) -> datetime:
    text = _text(value, label).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise PilotReceiptError(f"{label} must be ISO-8601") from exc


def _equal(left: Mapping[str, Any], right: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if left.get(field) != right.get(field):
            raise PilotReceiptError(f"{label} {field} mismatch")


def prepare_manifest(
    output: Path,
    *,
    repository_identity: str,
    plan_identity: str,
    plan_revision: str,
    task_id: str,
    workload_digest: str,
    workstream: str,
    git_revision: str,
) -> dict[str, Any]:
    manifest = {
        **DEFAULT_MANIFEST,
        "repository_identity": _text(repository_identity, "repository_identity"),
        "plan_identity": _text(plan_identity, "plan_identity"),
        "plan_revision": _text(plan_revision, "plan_revision"),
        "task_id": _text(task_id, "task_id"),
        "workload_digest": _text(workload_digest, "workload_digest"),
        "workstream": _text(workstream, "workstream"),
        "git_revision": _text(git_revision, "git_revision"),
        "checkpoint": f"{plan_revision}:{task_id}:{workload_digest}",
        "arms": ["baseline", "candidate"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _validate_source(
    source: Mapping[str, Any],
    *,
    kind: str,
    receipt: Mapping[str, Any],
    fields: tuple[str, ...],
) -> None:
    if source.get("producer") != PRODUCERS[kind]:
        raise PilotReceiptError(f"{kind} producer is not authoritative")
    for field in fields:
        _text(source.get(field), f"{kind}.{field}")
    _equal(source, receipt, fields, f"{kind} binding")


def validate_receipt(receipt: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "pair_id",
        "run_id",
        "arm",
        "assignment_id",
        "attempt_id",
        "task_id",
        "plan_identity",
        "plan_revision",
        "repository_identity",
        "workstream",
        "git_revision",
        "worktree",
        "checkpoint",
        "provider",
        "model",
        "controller_id",
        "session_id",
        "timestamps",
        "metrics",
        "source_refs",
    )
    for field in required:
        if field not in receipt:
            raise PilotReceiptError(f"receipt missing {field}")
    arm = _text(receipt.get("arm"), "arm")
    if arm not in {"baseline", "candidate"}:
        raise PilotReceiptError("arm must be baseline or candidate")
    for field in (
        "pair_id",
        "run_id",
        "assignment_id",
        "attempt_id",
        "task_id",
        "plan_identity",
        "plan_revision",
        "repository_identity",
        "worktree",
        "provider",
        "model",
        "controller_id",
        "session_id",
    ):
        _text(receipt.get(field), field)
    for field in (
        "repository_identity",
        "workstream",
        "git_revision",
        "plan_identity",
        "plan_revision",
        "task_id",
        "checkpoint",
    ):
        if receipt[field] != manifest.get(field):
            raise PilotReceiptError(f"receipt {field} does not match workload")

    live_receipt = receipt.get("live_receipt")
    if live_receipt is not None:
        try:
            normalized_live_receipt = validate_live_receipt(live_receipt)
        except ReceiptValidationError as exc:
            raise PilotReceiptError(f"live receipt invalid: {exc}") from exc
        for field in (
            "pair_id",
            "arm",
            "run_id",
            "attempt_id",
            "task_id",
            "plan_revision",
            "repository_identity",
            "plan_identity",
            "git_revision",
            "worktree",
            "workstream",
            "checkpoint",
            "model",
            "controller_id",
            "session_id",
            "provider",
        ):
            if normalized_live_receipt.get(field) != receipt.get(field):
                raise PilotReceiptError(f"live receipt {field} mismatch")
    else:
        normalized_live_receipt = None

    timestamps = receipt["timestamps"]
    if not isinstance(timestamps, Mapping):
        raise PilotReceiptError("timestamps must be an object")
    parsed_times = [_iso(timestamps.get(field), f"timestamps.{field}") for field in REQUIRED_TIMESTAMP_KEYS]
    if parsed_times != sorted(parsed_times):
        raise PilotReceiptError("timestamps are not monotonic")

    metrics = receipt["metrics"]
    if not isinstance(metrics, Mapping):
        raise PilotReceiptError("metrics must be an object")
    for field in ("human_interventions", "management_turns"):
        value = metrics.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise PilotReceiptError(f"metrics.{field} must be a non-negative integer")
    completion = metrics.get("accepted_completion_seconds")
    if not isinstance(completion, (int, float)) or isinstance(completion, bool) or completion <= 0:
        raise PilotReceiptError("metrics.accepted_completion_seconds must be positive")
    if metrics.get("correctness_gate") is not True:
        raise PilotReceiptError("correctness gate did not pass")
    if metrics.get("publication_success") is not True:
        raise PilotReceiptError("publication did not succeed")
    if metrics.get("duplicate_execution") is not False or metrics.get("unauthorized_writes") is not False:
        raise PilotReceiptError("correctness defect present")
    if not isinstance(metrics.get("token_usage", "unknown"), (int, float, str)):
        raise PilotReceiptError("token usage must be numeric or unknown")
    if not isinstance(metrics.get("cost", "unknown"), (int, float, str)):
        raise PilotReceiptError("cost must be numeric or unknown")
    relay_seconds = metrics.get("manual_relay_seconds", 0)
    if not isinstance(relay_seconds, (int, float)) or isinstance(relay_seconds, bool) or relay_seconds < 0:
        raise PilotReceiptError("manual relay time must be non-negative")

    refs = receipt["source_refs"]
    if not isinstance(refs, Mapping) or set(refs) != set(REQUIRED_SOURCE_KEYS):
        raise PilotReceiptError("source_refs must include launch, task_result, settlement, and acceptance")
    sources = {kind: _json(Path(_text(refs[kind], f"source_refs.{kind}"))) for kind in REQUIRED_SOURCE_KEYS}
    for kind in REQUIRED_SOURCE_KEYS:
        _validate_source(sources[kind], kind=kind, receipt=receipt, fields=SOURCE_BINDING_FIELDS)
    if sources["launch"].get("provider") != receipt["provider"] or sources["launch"].get("model") != receipt["model"]:
        raise PilotReceiptError("provider/model binding mismatch")
    if sources["launch"].get("timestamps") != receipt["timestamps"]:
        raise PilotReceiptError("launch timestamps are not producer-bound")
    if sources["launch"].get("metrics") != receipt["metrics"]:
        raise PilotReceiptError("metrics are not producer-bound")
    if sources["task_result"].get("publication_valid") is not True:
        raise PilotReceiptError("producer TaskResult is not valid")
    if sources["settlement"].get("settlement_proven") is not True or sources["settlement"].get("resource_settled") is not True:
        raise PilotReceiptError("producer settlement is not proven")
    if sources["acceptance"].get("decision") != "PASS":
        raise PilotReceiptError("producer acceptance did not pass")
    source_digests = {
        kind: hashlib.sha256(Path(_text(refs[kind], f"source_refs.{kind}")).read_bytes()).hexdigest()
        for kind in REQUIRED_SOURCE_KEYS
    }
    supplied_digests = receipt.get("source_digests")
    if supplied_digests is not None and supplied_digests != source_digests:
        raise PilotReceiptError("source digest mismatch")
    result = {
        **dict(receipt),
        "valid": True,
        "evidence_provenance": "live-attributed",
        "source_digests": source_digests,
    }
    if normalized_live_receipt is not None:
        result["live_receipt"] = normalized_live_receipt
    return result


def compare_records(
    records: list[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    *,
    capability_status: str = "AVAILABLE",
) -> dict[str, Any]:
    if capability_status == "BLOCKED_CAPABILITY":
        return {"classification": "BLOCKED_CAPABILITY", "valid_pairs": 0, "attempted_pairs": 0, "reason": "required runtime unavailable"}
    max_pairs = int(manifest.get("max_attempted_pairs", 5))
    min_pairs = int(manifest.get("minimum_valid_pairs", 3))
    if len(records) > max_pairs * 2:
        raise PilotReceiptError("record count exceeds maximum arm-run budget")
    grouped: dict[str, dict[str, Mapping[str, Any]]] = {}
    seen_run_ids: set[str] = set()
    seen_attempt_ids: set[str] = set()
    for record in records:
        validated = validate_receipt(record, manifest)
        pair = _text(validated.get("pair_id"), "pair_id")
        arm = _text(validated.get("arm"), "arm")
        run_id = _text(validated.get("run_id"), "run_id")
        attempt_id = _text(validated.get("attempt_id"), "attempt_id")
        if run_id in seen_run_ids:
            raise PilotReceiptError(f"duplicate run_id {run_id}")
        if attempt_id in seen_attempt_ids:
            raise PilotReceiptError(f"duplicate attempt_id {attempt_id}")
        seen_run_ids.add(run_id)
        seen_attempt_ids.add(attempt_id)
        if arm in grouped.setdefault(pair, {}):
            raise PilotReceiptError(f"duplicate arm for pair {pair}")
        grouped[pair][arm] = validated
    if len(grouped) > max_pairs:
        raise PilotReceiptError("pair count exceeds maximum attempted pair budget")
    valid_pairs = [pair for pair in grouped.values() if set(pair) == {"baseline", "candidate"}]
    if len(valid_pairs) < min_pairs:
        return {"classification": "INCONCLUSIVE", "valid_pairs": len(valid_pairs), "attempted_pairs": len(grouped)}
    baseline_interventions = median(pair["baseline"]["metrics"]["human_interventions"] for pair in valid_pairs[:min_pairs])
    candidate_interventions = median(pair["candidate"]["metrics"]["human_interventions"] for pair in valid_pairs[:min_pairs])
    baseline_completion = median(pair["baseline"]["metrics"]["accepted_completion_seconds"] for pair in valid_pairs[:min_pairs])
    candidate_completion = median(pair["candidate"]["metrics"]["accepted_completion_seconds"] for pair in valid_pairs[:min_pairs])
    intervention_reduction = baseline_interventions - candidate_interventions
    completion_regression = (candidate_completion / baseline_completion) - 1
    benefit = (
        intervention_reduction >= int(manifest.get("benefit_min_intervention_reduction", 1))
        and completion_regression <= float(manifest.get("max_candidate_completion_regression", 0.10))
    )
    return {
        "classification": "VERIFIED_BENEFIT" if benefit else "NO_MEASURED_BENEFIT",
        "valid_pairs": min_pairs,
        "attempted_pairs": len(grouped),
        "primary_metric": manifest.get("primary_metric"),
        "baseline_median_interventions": baseline_interventions,
        "candidate_median_interventions": candidate_interventions,
        "intervention_reduction": intervention_reduction,
        "baseline_median_completion_seconds": baseline_completion,
        "candidate_median_completion_seconds": candidate_completion,
        "completion_regression": completion_regression,
    }


def _report_markdown(result: Mapping[str, Any]) -> str:
    lines = ["# Secretary Live Pilot Comparison", "", f"- Classification: `{result['classification']}`"]
    for key, value in result.items():
        if key != "classification":
            lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--output", type=Path, required=True)
    for field in (
        "repository_identity",
        "plan_identity",
        "plan_revision",
        "task_id",
        "workload_digest",
        "workstream",
        "git_revision",
    ):
        prepare.add_argument(f"--{field.replace('_', '-')}", required=True)
    record = subparsers.add_parser("record")
    record.add_argument("--manifest", type=Path, required=True)
    record.add_argument("--receipt", type=Path, required=True)
    record.add_argument("--output", type=Path, required=True)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--manifest", type=Path, required=True)
    compare.add_argument("--records-dir", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    compare.add_argument("--capability-status", default="AVAILABLE")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        prepare_manifest(
            args.output,
            repository_identity=args.repository_identity,
            plan_identity=args.plan_identity,
            plan_revision=args.plan_revision,
            task_id=args.task_id,
            workload_digest=args.workload_digest,
            workstream=args.workstream,
            git_revision=args.git_revision,
        )
        return 0
    if args.command == "record":
        normalized = validate_receipt(_json(args.receipt), _json(args.manifest))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    result = compare_records(
        [_json(path) for path in sorted(args.records_dir.glob("*.json"))],
        _json(args.manifest),
        capability_status=args.capability_status,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_report_markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
