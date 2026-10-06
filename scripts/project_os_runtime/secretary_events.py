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
    resolved_event_ids: frozenset[str] = frozenset()
    superseded_event_ids: frozenset[str] = frozenset()


def event_identity(hint: EventHint) -> str:
    return f"{hint.source}:{hint.observed_identity}"


def _ordering(hint: EventHint) -> tuple[int, str]:
    return (hint.source_sequence if hint.source_sequence is not None else -1, hint.observed_anchor)


def coalesce_event_hints(hints: list[EventHint]) -> tuple[EventHint, ...]:
    selected: dict[tuple[str, str, str, str], EventHint] = {}
    for hint in hints:
        key = (hint.source, hint.workstream, hint.event_type, hint.observed_identity)
        current = selected.get(key)
        if current is None or _ordering(hint) >= _ordering(current):
            selected[key] = EventHint(
                source=hint.source,
                event_type=hint.event_type,
                workstream=hint.workstream,
                observed_identity=hint.observed_identity,
                observed_anchor=hint.observed_anchor,
                source_sequence=hint.source_sequence,
                evidence_refs=tuple(sorted(set(hint.evidence_refs) | set(current.evidence_refs)))
                if current is not None
                else tuple(sorted(set(hint.evidence_refs))),
            )
        elif current is not None:
            selected[key] = EventHint(
                source=current.source,
                event_type=current.event_type,
                workstream=current.workstream,
                observed_identity=current.observed_identity,
                observed_anchor=current.observed_anchor,
                source_sequence=current.source_sequence,
                evidence_refs=tuple(sorted(set(current.evidence_refs) | set(hint.evidence_refs))),
            )
    return tuple(
        sorted(
            selected.values(),
            key=lambda item: (
                item.workstream,
                item.event_type,
                item.observed_identity,
                item.source_sequence if item.source_sequence is not None else -1,
                item.observed_anchor,
            ),
        )
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
