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
    anchor: str = "anchor-4",
    identity: str = "event-1",
    source: str = "fake",
    sequence: int | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> EventHint:
    return EventHint(source, event_type, "runtime", identity, anchor, sequence, evidence_refs)


def evidence(anchor: str = "anchor-4", stale: bool = False, resolved: frozenset[str] = frozenset()) -> ReconciliationEvidence:
    return ReconciliationEvidence("runtime", anchor, controller_stale=stale, resolved_event_ids=resolved)


def test_coalescer_uses_source_sequence_for_same_identity() -> None:
    result = coalesce_event_hints([hint(anchor="anchor-4", sequence=4), hint(anchor="anchor-6", sequence=6)])

    assert len(result) == 1
    assert result[0].observed_anchor == "anchor-6"


def test_coalescer_unions_evidence_references() -> None:
    result = coalesce_event_hints(
        [
            hint(sequence=4, evidence_refs=("old",)),
            hint(sequence=6, evidence_refs=("new",)),
        ]
    )

    assert result[0].evidence_refs == ("new", "old")


def test_coalescer_preserves_distinct_project_decisions() -> None:
    result = coalesce_event_hints(
        [hint(identity="event-1"), hint(identity="event-2")]
    )

    assert len(result) == 2


def test_coalescer_preserves_conflicting_anchors_without_sequence() -> None:
    result = coalesce_event_hints(
        [hint(anchor="zz-old"), hint(anchor="aa-new")]
    )

    assert [item.observed_anchor for item in result] == ["aa-new", "zz-old"]


def test_coalescer_preserves_equal_sequence_conflicts() -> None:
    result = coalesce_event_hints(
        [hint(anchor="anchor-a", sequence=4), hint(anchor="anchor-b", sequence=4)]
    )

    assert len(result) == 2


def test_coalescer_preserves_one_missing_sequence_conflict() -> None:
    result = coalesce_event_hints(
        [hint(anchor="anchor-a", sequence=4), hint(anchor="anchor-b")]
    )

    assert len(result) == 2


def test_coalescer_scopes_identity_by_source() -> None:
    result = coalesce_event_hints([hint(source="one"), hint(source="two")])

    assert len(result) == 2


def test_routine_activity_stays_local() -> None:
    assert reconcile_event_hint(hint(ROUTINE_ACTIVITY), evidence()) == NO_ACTION


def test_current_project_event_requests_secretary_attention() -> None:
    assert reconcile_event_hint(hint(), evidence()) == SECRETARY_ATTENTION


def test_older_or_newer_unresolved_anchor_reconciles() -> None:
    assert reconcile_event_hint(hint(anchor="anchor-3"), evidence(anchor="anchor-4")) == RECONCILE
    assert reconcile_event_hint(hint(anchor="anchor-5"), evidence(anchor="anchor-4")) == RECONCILE


def test_explicit_resolution_suppresses_old_event() -> None:
    current = hint(anchor="anchor-3")
    assert reconcile_event_hint(
        current,
        evidence(anchor="anchor-4", resolved=frozenset({current.source + ":" + current.observed_identity})),
    ) == NO_ACTION


def test_stale_controller_requires_reconciliation() -> None:
    assert reconcile_event_hint(hint(), evidence(stale=True)) == RECONCILE


def test_unknown_workstream_blocks_event_routing() -> None:
    result = reconcile_event_hint(
        hint(), ReconciliationEvidence("other", current_anchor="anchor-4")
    )

    assert result == BLOCKED


def test_unknown_event_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported Secretary event type"):
        hint("idle")
