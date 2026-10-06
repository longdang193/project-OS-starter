from scripts.project_os_runtime.secretary_adapter import (
    AttentionBrief,
    ControllerRef,
    InMemoryActivationReceiptJournal,
    InMemoryControllerSessionAdapter,
)


def brief(
    workstream: str = "runtime",
    *,
    repository_identity: str = "repo-a",
    canonical_work: str = "plan-a",
    expected_branch: str = "feature/runtime",
    expected_base: str = "base-a",
    evidence_refs: tuple[str, ...] = (),
) -> AttentionBrief:
    return AttentionBrief(
        workstream=workstream,
        objective="reconcile attention",
        evidence_refs=evidence_refs,
        repository_identity=repository_identity,
        canonical_work=canonical_work,
        expected_branch=expected_branch,
        expected_base=expected_base,
    )


def test_activation_is_idempotent_and_has_one_side_effect() -> None:
    adapter = InMemoryControllerSessionAdapter()

    first = adapter.activate("runtime", "activation-1", brief())
    second = adapter.activate("runtime", "activation-1", brief())

    assert first.created is True
    assert second.reused is True
    assert second.controller == first.controller
    assert adapter.activation_side_effects == 1


def test_activation_journal_reconciles_after_adapter_restart() -> None:
    journal = InMemoryActivationReceiptJournal()
    first_adapter = InMemoryControllerSessionAdapter(journal)
    first = first_adapter.activate("runtime", "activation-1", brief())

    restarted_adapter = InMemoryControllerSessionAdapter(journal)
    second = restarted_adapter.activate("runtime", "activation-1", brief())

    assert second.reused is True
    assert second.controller == first.controller
    assert restarted_adapter.activation_side_effects == 0


def test_activation_mismatch_requires_recovery() -> None:
    adapter = InMemoryControllerSessionAdapter()
    adapter.activate("runtime", "activation-1", brief())

    result = adapter.activate("other", "activation-1", brief("other"))

    assert result.recovery_required is True
    assert result.reason == "activation key belongs to another workstream"
    assert adapter.activation_side_effects == 1


def test_resume_and_delivery_reject_stale_controller() -> None:
    adapter = InMemoryControllerSessionAdapter()
    current = adapter.activate("runtime", "activation-1", brief()).controller
    assert current is not None
    stale = ControllerRef("runtime", current.controller_id, "feature", "other-base")

    resume = adapter.resume(stale, brief())
    delivery = adapter.deliver(stale, brief())

    assert resume.recovery_required is True
    assert delivery.recovery_required is True
    assert adapter.delivery_side_effects == 0


def test_observation_never_turns_unknown_into_success() -> None:
    adapter = InMemoryControllerSessionAdapter()
    unknown = ControllerRef("runtime", "missing", "main", "test-base")

    result = adapter.observe(unknown)

    assert result.state == "unknown"
    assert result.recovery_required is True


def test_release_session_is_distinct_from_lane_retirement() -> None:
    adapter = InMemoryControllerSessionAdapter()
    controller = adapter.activate("runtime", "activation-1", brief()).controller
    assert controller is not None

    result = adapter.release_session(controller)

    assert result.released is True
    assert adapter.resolve("runtime").found is False


def test_release_unknown_session_requires_reconciliation() -> None:
    adapter = InMemoryControllerSessionAdapter()
    unknown = ControllerRef("runtime", "missing", "main", "test-base")

    result = adapter.release_session(unknown)

    assert result.released is False
    assert result.recovery_required is True


def test_activation_owner_is_bound_to_repository_and_canonical_work() -> None:
    adapter = InMemoryControllerSessionAdapter()
    first = adapter.activate("runtime", "activation-1", brief()).controller
    assert first is not None

    collision = adapter.activate(
        "runtime",
        "activation-2",
        brief(canonical_work="plan-b"),
    )

    assert collision.recovery_required is True
    assert adapter.activation_side_effects == 1


def test_activation_rejects_same_key_with_changed_git_binding() -> None:
    adapter = InMemoryControllerSessionAdapter()
    adapter.activate("runtime", "activation-1", brief())

    changed = adapter.activate(
        "runtime",
        "activation-1",
        brief(expected_branch="other-branch", expected_base="other-base"),
    )

    assert changed.recovery_required is True
    assert changed.reason == "activation key has a different request fingerprint"
    assert adapter.activation_side_effects == 1


def test_release_does_not_replay_active_ownership() -> None:
    adapter = InMemoryControllerSessionAdapter()
    controller = adapter.activate("runtime", "activation-1", brief()).controller
    assert controller is not None
    assert adapter.release_session(controller).released is True

    replay = adapter.activate("runtime", "activation-1", brief())

    assert replay.recovery_required is True
    assert replay.reused is False
    assert adapter.resolve("runtime", repository_identity="repo-a").found is False


def test_delivery_reuses_same_payload_and_rejects_changed_payload() -> None:
    adapter = InMemoryControllerSessionAdapter()
    controller = adapter.activate("runtime", "activation-1", brief()).controller
    assert controller is not None

    first = adapter.deliver(controller, brief(), delivery_identity="delivery-1")
    second = adapter.deliver(controller, brief(), delivery_identity="delivery-1")
    changed = adapter.deliver(
        controller,
        AttentionBrief(
            **{**brief().__dict__, "objective": "changed payload"}
        ),
        delivery_identity="delivery-1",
    )

    assert first.delivered is True
    assert second.delivered is True
    assert second.recovery_required is False
    assert changed.recovery_required is True
    assert adapter.delivery_side_effects == 1
