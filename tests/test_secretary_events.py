import pytest

from scripts.project_os_runtime.secretary_events import (
    BLOCKED,
    DEPENDENCY_CHANGED,
    NO_ACTION,
    RECONCILE,
    ROUTINE_ACTIVITY,
    SECRETARY_ATTENTION,
    EventHint,
    ReconciliationEvidence,
    coalesce_event_hints,
    reconcile_event_hint,
)


def hint(
    event_type: str = DEPENDENCY_CHANGED,
    revision: int = 4,
    identity: str = "event-1",
) -> EventHint:
    return EventHint("fake", event_type, "runtime", identity, revision)


def evidence(revision: int = 4, stale: bool = False) -> ReconciliationEvidence:
    return ReconciliationEvidence("runtime", revision, controller_stale=stale)


def test_coalescer_keeps_newest_hint_for_same_identity() -> None:
    result = coalesce_event_hints([hint(revision=4), hint(revision=6)])

    assert len(result) == 1
    assert result[0].canonical_revision == 6


def test_coalescer_preserves_distinct_project_decisions() -> None:
    result = coalesce_event_hints(
        [hint(identity="event-1"), hint(identity="event-2")]
    )

    assert len(result) == 2


def test_routine_activity_stays_local() -> None:
    assert reconcile_event_hint(hint(ROUTINE_ACTIVITY), evidence()) == NO_ACTION


def test_current_project_event_requests_secretary_attention() -> None:
    assert reconcile_event_hint(hint(), evidence()) == SECRETARY_ATTENTION


def test_stale_or_newer_revision_reconciles_without_acceptance() -> None:
    assert reconcile_event_hint(hint(revision=3), evidence(revision=4)) == NO_ACTION
    assert reconcile_event_hint(hint(revision=5), evidence(revision=4)) == RECONCILE


def test_stale_controller_requires_reconciliation() -> None:
    assert reconcile_event_hint(hint(), evidence(stale=True)) == RECONCILE


def test_unknown_workstream_blocks_event_routing() -> None:
    result = reconcile_event_hint(
        hint(), ReconciliationEvidence("other", current_revision=4)
    )

    assert result == BLOCKED


def test_unknown_event_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported Secretary event type"):
        hint("idle")
