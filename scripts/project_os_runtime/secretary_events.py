from __future__ import annotations

from dataclasses import dataclass


DEPENDENCY_CHANGED = "dependency_changed"
CROSS_WORKSTREAM_CONFLICT = "cross_workstream_conflict"
AUTHORITY_ISSUE = "authority_issue"
INTENT_CHANGED = "intent_changed"
MEANINGFUL_COMPLETION = "meaningful_completion"
EXTERNAL_UNBLOCK = "external_unblock"
ROUTINE_ACTIVITY = "routine_activity"

PROJECT_EVENT_TYPES = frozenset(
    {
        DEPENDENCY_CHANGED,
        CROSS_WORKSTREAM_CONFLICT,
        AUTHORITY_ISSUE,
        INTENT_CHANGED,
        MEANINGFUL_COMPLETION,
        EXTERNAL_UNBLOCK,
    }
)

EventIdentity = tuple[str, str, str, str]

NO_ACTION = "NO_ACTION"
SECRETARY_ATTENTION = "SECRETARY_ATTENTION"
RECONCILE = "RECONCILE"
BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class EventHint:
    source: str
    event_type: str
    workstream: str
    observed_identity: str
    observed_anchor: str
    source_sequence: int | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.event_type not in PROJECT_EVENT_TYPES | {ROUTINE_ACTIVITY}:
            raise ValueError(f"unsupported Secretary event type: {self.event_type}")


@dataclass(frozen=True)
class ReconciliationEvidence:
    workstream: str
    current_anchor: str
    workstream_exists: bool = True
    controller_stale: bool = False
    resolved_event_ids: frozenset[EventIdentity] = frozenset()
    superseded_event_ids: frozenset[EventIdentity] = frozenset()


def event_identity(hint: EventHint) -> EventIdentity:
    return (hint.source, hint.workstream, hint.event_type, hint.observed_identity)


def _ordering(hint: EventHint) -> int | None:
    return hint.source_sequence


def _merge_same_anchor(hints: list[EventHint]) -> EventHint:
    first = hints[0]
    sequences = [hint.source_sequence for hint in hints if hint.source_sequence is not None]
    return EventHint(
        source=first.source,
        event_type=first.event_type,
        workstream=first.workstream,
        observed_identity=first.observed_identity,
        observed_anchor=first.observed_anchor,
        source_sequence=max(sequences) if sequences else None,
        evidence_refs=tuple(sorted({ref for hint in hints for ref in hint.evidence_refs})),
    )


def coalesce_event_hints(hints: list[EventHint]) -> tuple[EventHint, ...]:
    grouped: dict[tuple[str, str, str, str], list[EventHint]] = {}
    for hint in hints:
        key = (hint.source, hint.workstream, hint.event_type, hint.observed_identity)
        grouped.setdefault(key, []).append(hint)

    selected: list[EventHint] = []
    for same_identity in grouped.values():
        by_anchor: dict[str, list[EventHint]] = {}
        for hint in same_identity:
            by_anchor.setdefault(hint.observed_anchor, []).append(hint)
        merged = [_merge_same_anchor(anchor_hints) for anchor_hints in by_anchor.values()]
        if len(merged) == 1:
            selected.extend(merged)
            continue

        sequences = [hint.source_sequence for hint in merged]
        comparable = all(sequence is not None for sequence in sequences)
        unique_max = comparable and sequences.count(max(sequences)) == 1
        if unique_max:
            winner = max(merged, key=lambda hint: hint.source_sequence or 0)
            selected.append(
                replace_event_evidence(
                    winner,
                    {ref for hint in merged for ref in hint.evidence_refs},
                )
            )
        else:
            selected.extend(merged)

    return tuple(
        sorted(
            selected,
            key=lambda item: (
                item.workstream,
                item.event_type,
                item.observed_identity,
                item.observed_anchor,
            ),
        )
    )


def replace_event_evidence(hint: EventHint, evidence_refs: set[str]) -> EventHint:
    return EventHint(
        source=hint.source,
        event_type=hint.event_type,
        workstream=hint.workstream,
        observed_identity=hint.observed_identity,
        observed_anchor=hint.observed_anchor,
        source_sequence=hint.source_sequence,
        evidence_refs=tuple(sorted(evidence_refs)),
    )


def reconcile_event_hint(
    hint: EventHint,
    evidence: ReconciliationEvidence,
) -> str:
    if hint.workstream != evidence.workstream or not evidence.workstream_exists:
        return BLOCKED
    if hint.event_type == ROUTINE_ACTIVITY:
        return NO_ACTION
    identity = event_identity(hint)
    if identity in evidence.resolved_event_ids or identity in evidence.superseded_event_ids:
        return NO_ACTION
    if hint.observed_anchor != evidence.current_anchor or evidence.controller_stale:
        return RECONCILE
    return SECRETARY_ATTENTION


__all__ = [
    "AUTHORITY_ISSUE",
    "BLOCKED",
    "CROSS_WORKSTREAM_CONFLICT",
    "DEPENDENCY_CHANGED",
    "EventIdentity",
    "EXTERNAL_UNBLOCK",
    "EventHint",
    "INTENT_CHANGED",
    "MEANINGFUL_COMPLETION",
    "NO_ACTION",
    "PROJECT_EVENT_TYPES",
    "RECONCILE",
    "ReconciliationEvidence",
    "ROUTINE_ACTIVITY",
    "SECRETARY_ATTENTION",
    "coalesce_event_hints",
    "event_identity",
    "reconcile_event_hint",
]
