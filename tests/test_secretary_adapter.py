from scripts.project_os_runtime.secretary_adapter import (
    AttentionDelta,
    CommunicationEnvelope,
    ControllerBinding,
    ControllerRef,
    InMemoryControllerSessionAdapter,
    InMemoryControllerSessionJournal,
)


def binding(
    workstream: str = "runtime",
    *,
    repository_identity: str = "repo-a",
    canonical_work: str = "plan-a",
    expected_branch: str = "feature/runtime",
    expected_base: str = "base-a",
) -> ControllerBinding:
    return ControllerBinding(
        repository_identity=repository_identity,
        canonical_work=canonical_work,
        workstream=workstream,
        expected_branch=expected_branch,
        expected_base=expected_base,
    )


def envelope(current: ControllerBinding | None = None, *, reason: str = "reconcile") -> CommunicationEnvelope:
    return CommunicationEnvelope(
        binding=current or binding(),
        message_id="message-1",
        canonical_anchor="evidence-1",
        payload=AttentionDelta(reason=reason, evidence_refs=("evidence-1",)),
    )


def test_activation_is_idempotent_and_has_one_side_effect() -> None:
    adapter = InMemoryControllerSessionAdapter()

    first = adapter.activate(binding(), "activation-1")
    second = adapter.activate(binding(), "activation-1")

    assert first.created is True
    assert second.reused is True
    assert second.controller == first.controller
    assert adapter.activation_side_effects == 1


def test_activation_journal_reconciles_after_adapter_restart() -> None:
    journal = InMemoryControllerSessionJournal()
    first_adapter = InMemoryControllerSessionAdapter(journal)
    first = first_adapter.activate(binding(), "activation-1")

    restarted_adapter = InMemoryControllerSessionAdapter(journal)
    second = restarted_adapter.activate(binding(), "activation-1")

    assert second.reused is True
    assert second.controller == first.controller
    assert restarted_adapter.activation_side_effects == 0


def test_activation_mismatch_requires_recovery() -> None:
    adapter = InMemoryControllerSessionAdapter()
    adapter.activate(binding(), "activation-1")

    result = adapter.activate(binding("other"), "activation-1")

    assert result.recovery_required is True
    assert result.reason == "activation ID has a different binding"
    assert adapter.activation_side_effects == 1


def test_compaction_releases_session_but_keeps_replay_protection() -> None:
    adapter = InMemoryControllerSessionAdapter()
    activation = adapter.activate(binding(), "activation-1")
    controller = activation.controller
    assert controller is not None

    assert adapter.release_session(controller).released is True
    assert adapter.compact_released(controller) is True
    replay = adapter.activate(binding(), "activation-1")

    assert replay.recovery_required is True
    assert "compacted" in (replay.reason or "")


def test_binding_mismatch_requires_recovery_for_each_lifecycle_operation() -> None:
    adapter = InMemoryControllerSessionAdapter()
    current = adapter.activate(binding(), "activation-1").controller
    assert current is not None
    changed = binding(expected_base="other-base")

    resolve = adapter.resolve(changed)
    resume = adapter.resume(current, changed)
    delivery = adapter.deliver(current, envelope(changed))

    assert resolve.found is False
    assert resolve.recovery_required is True
    assert resume.recovery_required is True
    assert delivery.recovery_required is True
    assert adapter.delivery_side_effects == 0


def test_repository_work_canonical_workstream_branch_and_base_are_binding_fields() -> None:
    adapter = InMemoryControllerSessionAdapter()
    current = adapter.activate(binding(), "activation-1").controller
    assert current is not None

    for changed in (
        binding(repository_identity="repo-b"),
        binding(canonical_work="plan-b"),
        binding(workstream="other"),
        binding(expected_branch="other-branch"),
        binding(expected_base="other-base"),
    ):
        assert adapter.resume(current, changed).recovery_required is True


def test_observation_validates_identity_without_consuming_attention() -> None:
    adapter = InMemoryControllerSessionAdapter()
    unknown = ControllerRef(binding(), "missing")

    result = adapter.observe(unknown)

    assert result.state == "unknown"
    assert result.recovery_required is True
    assert result.deltas == ()


def test_release_session_is_distinct_from_lane_retirement() -> None:
    adapter = InMemoryControllerSessionAdapter()
    controller = adapter.activate(binding(), "activation-1").controller
    assert controller is not None

    result = adapter.release_session(controller)

    assert result.released is True
    assert adapter.resolve(binding()).found is False


def test_compact_released_does_not_remove_active_controller() -> None:
    adapter = InMemoryControllerSessionAdapter()
    controller = adapter.activate(binding(), "activation-1").controller
    assert controller is not None

    assert adapter.compact_released(controller) is False
    assert adapter.resolve(binding()).found is True


def test_compact_old_released_controller_preserves_replacement() -> None:
    adapter = InMemoryControllerSessionAdapter()
    old = adapter.activate(binding(), "activation-1").controller
    assert old is not None
    assert adapter.release_session(old).released is True
    replacement = adapter.activate(binding(), "activation-2").controller
    assert replacement is not None

    assert adapter.compact_released(old) is True
    assert adapter.resolve(binding()).controller == replacement


def test_release_unknown_session_requires_reconciliation() -> None:
    adapter = InMemoryControllerSessionAdapter()
    unknown = ControllerRef(binding(), "missing")

    result = adapter.release_session(unknown)

    assert result.released is False
    assert result.recovery_required is True


def test_activation_owner_is_bound_to_repository_and_canonical_work() -> None:
    adapter = InMemoryControllerSessionAdapter()
    first = adapter.activate(binding(), "activation-1").controller
    assert first is not None

    collision = adapter.activate(binding(canonical_work="plan-b"), "activation-2")

    assert collision.recovery_required is True
    assert adapter.activation_side_effects == 1


def test_same_workstream_name_can_activate_in_different_repositories() -> None:
    adapter = InMemoryControllerSessionAdapter()

    first = adapter.activate(binding(repository_identity="repo-a"), "activation-a")
    second = adapter.activate(binding(repository_identity="repo-b"), "activation-b")

    assert first.created is True
    assert second.created is True
    assert first.controller != second.controller
    assert adapter.activation_side_effects == 2


def test_delta_reference_fields_normalize_to_tuples() -> None:
    payload = AttentionDelta(
        "reconcile", ["constraint", "constraint"], ["evidence", "earlier"]
    )

    assert payload.constraint_refs == ("constraint",)
    assert payload.evidence_refs == ("earlier", "evidence")


def test_release_does_not_replay_active_ownership() -> None:
    adapter = InMemoryControllerSessionAdapter()
    controller = adapter.activate(binding(), "activation-1").controller
    assert controller is not None
    assert adapter.release_session(controller).released is True

    replay = adapter.activate(binding(), "activation-1")

    assert replay.recovery_required is True
    assert replay.reused is False
    assert adapter.resolve(binding()).found is False


def test_delivery_reuses_same_payload_and_rejects_changed_payload() -> None:
    adapter = InMemoryControllerSessionAdapter()
    controller = adapter.activate(binding(), "activation-1").controller
    assert controller is not None

    first = adapter.deliver(controller, envelope())
    second = adapter.deliver(controller, envelope())
    changed = adapter.deliver(controller, envelope(reason="changed payload"))

    assert first.delivered is True
    assert second.delivered is True
    assert second.recovery_required is False
    assert changed.recovery_required is True
    assert adapter.delivery_side_effects == 1


def test_delivery_reuse_survives_adapter_recreation_and_message_identity_is_separate() -> None:
    journal = InMemoryControllerSessionJournal()
    first_adapter = InMemoryControllerSessionAdapter(journal)
    controller = first_adapter.activate(binding(), "activation-1").controller
    assert controller is not None
    assert first_adapter.deliver(controller, envelope()).delivered is True

    restarted_adapter = InMemoryControllerSessionAdapter(journal)
    assert restarted_adapter.deliver(controller, envelope()).delivered is True
    assert restarted_adapter.delivery_side_effects == 0

    changed_message = CommunicationEnvelope(
        binding=binding(),
        message_id="message-2",
        canonical_anchor="evidence-1",
        payload=AttentionDelta(reason="reconcile", evidence_refs=("evidence-1",)),
    )
    assert restarted_adapter.deliver(controller, changed_message).delivered is True
    assert restarted_adapter.delivery_side_effects == 1
