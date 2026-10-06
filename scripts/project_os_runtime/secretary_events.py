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
    canonical_revision: int
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.event_type not in PROJECT_EVENT_TYPES | {ROUTINE_ACTIVITY}:
            raise ValueError(f"unsupported Secretary event type: {self.event_type}")


@dataclass(frozen=True)
class ReconciliationEvidence:
    workstream: str
    current_revision: int
    workstream_exists: bool = True
    controller_stale: bool = False


def coalesce_event_hints(hints: list[EventHint]) -> tuple[EventHint, ...]:
    selected: dict[tuple[str, str, str], EventHint] = {}
    for hint in hints:
        key = (hint.workstream, hint.event_type, hint.observed_identity)
        current = selected.get(key)
        if current is None or hint.canonical_revision >= current.canonical_revision:
            selected[key] = hint
    return tuple(
        sorted(
            selected.values(),
            key=lambda item: (
                item.workstream,
                item.event_type,
                item.observed_identity,
                item.canonical_revision,
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
    if hint.canonical_revision < evidence.current_revision:
        return NO_ACTION
    if hint.canonical_revision > evidence.current_revision or evidence.controller_stale:
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
    "reconcile_event_hint",
]
