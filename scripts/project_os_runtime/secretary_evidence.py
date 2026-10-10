from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


CURRENT = "CURRENT"
MISSING = "MISSING"
STALE = "STALE"


@dataclass(frozen=True)
class EvidenceSnapshot:
    status: str
    task_ref: str | None
    canonical_consequence_ref: str | None
    reconciled_result_ref: str | None
    blocking_refs: tuple[str, ...]
    project_consequence: str | None
    attention_delta: Mapping[str, Any] | None
    reasons: tuple[str, ...]
    sources: tuple[tuple[str, str], ...]
    reconciliation: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["blocking_refs"] = list(self.blocking_refs)
        value["reasons"] = list(self.reasons)
        value["sources"] = dict(self.sources)
        return value


def build_evidence_snapshot(
    *,
    task_ref: str | None,
    canonical_consequence_ref: str | None,
    reconciled_result_ref: str | None,
    blocking_refs: tuple[str, ...] | list[str] = (),
    project_consequence: str | None = None,
    attention_delta: Mapping[str, Any] | None = None,
    reconciled_result: Mapping[str, Any] | None = None,
) -> EvidenceSnapshot:
    references = {
        "task": task_ref,
        "canonical consequence": canonical_consequence_ref,
        "reconciled result": reconciled_result_ref,
    }
    reasons = [
        f"missing {name} reference"
        for name, value in references.items()
        if not isinstance(value, str) or not value.strip()
    ]
    normalized_blocking_refs = tuple(sorted({ref for ref in blocking_refs if isinstance(ref, str) and ref.strip()}))
    if normalized_blocking_refs:
        reasons.append("blocking references present")
    status = MISSING if any(reason.startswith("missing ") for reason in reasons) else STALE if normalized_blocking_refs else CURRENT
    sources = tuple(
        sorted(
            (name, value)
            for name, value in references.items()
            if isinstance(value, str) and value.strip()
        )
    )
    return EvidenceSnapshot(
        status=status,
        task_ref=task_ref if isinstance(task_ref, str) and task_ref.strip() else None,
        canonical_consequence_ref=(
            canonical_consequence_ref
            if isinstance(canonical_consequence_ref, str) and canonical_consequence_ref.strip()
            else None
        ),
        reconciled_result_ref=(
            reconciled_result_ref
            if isinstance(reconciled_result_ref, str) and reconciled_result_ref.strip()
            else None
        ),
        blocking_refs=normalized_blocking_refs,
        project_consequence=project_consequence if isinstance(project_consequence, str) and project_consequence.strip() else None,
        attention_delta=dict(attention_delta) if isinstance(attention_delta, Mapping) else None,
        reasons=tuple(dict.fromkeys(reasons)),
        sources=sources,
        reconciliation=dict(reconciled_result) if isinstance(reconciled_result, Mapping) else None,
    )


__all__ = ["CURRENT", "MISSING", "STALE", "EvidenceSnapshot", "build_evidence_snapshot"]
