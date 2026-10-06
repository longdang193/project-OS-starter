from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol


@dataclass(frozen=True)
class ControllerRef:
    workstream: str
    controller_id: str
    branch: str
    base_commit: str


@dataclass(frozen=True)
class AttentionBrief:
    workstream: str
    objective: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoordinationDelta:
    kind: str
    summary: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolveReceipt:
    workstream: str
    controller: ControllerRef | None
    found: bool
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ActivationReceipt:
    activation_key: str
    workstream: str
    controller: ControllerRef | None
    created: bool
    reused: bool
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ResumeReceipt:
    controller: ControllerRef
    resumed: bool
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ObservationReceipt:
    controller: ControllerRef
    state: str
    deltas: tuple[CoordinationDelta, ...] = ()
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class DeliveryReceipt:
    controller: ControllerRef
    delivered: bool
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class SessionReleaseReceipt:
    controller: ControllerRef
    released: bool
    recovery_required: bool = False
    reason: str | None = None


class ActivationReceiptJournal(Protocol):
    def lookup_activation(self, activation_key: str) -> ActivationReceipt | None:
        ...

    def record_activation(self, receipt: ActivationReceipt) -> None:
        ...


class ControllerSessionAdapter(Protocol):
    def resolve(self, workstream: str) -> ResolveReceipt:
        ...

    def lookup_activation(self, activation_key: str) -> ActivationReceipt | None:
        ...

    def activate(
        self,
        workstream: str,
        activation_key: str,
        brief: AttentionBrief,
    ) -> ActivationReceipt:
        ...

    def resume(self, controller: ControllerRef, brief: AttentionBrief) -> ResumeReceipt:
        ...

    def observe(self, controller: ControllerRef) -> ObservationReceipt:
        ...

    def deliver(
        self,
        controller: ControllerRef,
        brief: AttentionBrief,
    ) -> DeliveryReceipt:
        ...

    def release_session(self, controller: ControllerRef) -> SessionReleaseReceipt:
        ...


class InMemoryActivationReceiptJournal:
    def __init__(self) -> None:
        self._receipts: dict[str, ActivationReceipt] = {}

    def lookup_activation(self, activation_key: str) -> ActivationReceipt | None:
        return self._receipts.get(activation_key)

    def record_activation(self, receipt: ActivationReceipt) -> None:
        current = self._receipts.get(receipt.activation_key)
        if current is not None and current != receipt:
            raise ValueError("activation key already has a different receipt")
        self._receipts[receipt.activation_key] = receipt


class InMemoryControllerSessionAdapter:
    def __init__(self, journal: ActivationReceiptJournal | None = None) -> None:
        self.journal = journal or InMemoryActivationReceiptJournal()
        self._controllers: dict[str, ControllerRef] = {}
        self._next_controller = 1
        self.activation_side_effects = 0
        self.delivery_side_effects = 0

    def resolve(self, workstream: str) -> ResolveReceipt:
        controller = self._controllers.get(workstream)
        if controller is None:
            return ResolveReceipt(workstream=workstream, controller=None, found=False)
        return ResolveReceipt(workstream=workstream, controller=controller, found=True)

    def lookup_activation(self, activation_key: str) -> ActivationReceipt | None:
        return self.journal.lookup_activation(activation_key)

    def activate(
        self,
        workstream: str,
        activation_key: str,
        brief: AttentionBrief,
    ) -> ActivationReceipt:
        if brief.workstream != workstream:
            return ActivationReceipt(
                activation_key=activation_key,
                workstream=workstream,
                controller=None,
                created=False,
                reused=False,
                recovery_required=True,
                reason="brief workstream does not match activation workstream",
            )

        existing = self.journal.lookup_activation(activation_key)
        if existing is not None:
            if existing.workstream != workstream:
                return replace(
                    existing,
                    recovery_required=True,
                    reason="activation key belongs to another workstream",
                )
            if existing.controller is not None:
                self._controllers[workstream] = existing.controller
            return replace(existing, created=False, reused=True)

        controller = ControllerRef(
            workstream=workstream,
            controller_id=f"controller-{self._next_controller}",
            branch="main",
            base_commit="test-base",
        )
        self._next_controller += 1
        receipt = ActivationReceipt(
            activation_key=activation_key,
            workstream=workstream,
            controller=controller,
            created=True,
            reused=False,
        )
        self.journal.record_activation(receipt)
        self._controllers[workstream] = controller
        self.activation_side_effects += 1
        return receipt

    def resume(self, controller: ControllerRef, brief: AttentionBrief) -> ResumeReceipt:
        current = self._controllers.get(controller.workstream)
        if brief.workstream != controller.workstream:
            return ResumeReceipt(
                controller=controller,
                resumed=False,
                recovery_required=True,
                reason="brief workstream does not match controller workstream",
            )
        if current != controller:
            return ResumeReceipt(
                controller=controller,
                resumed=False,
                recovery_required=True,
                reason="controller identity is stale or unknown",
            )
        return ResumeReceipt(controller=controller, resumed=True)

    def observe(self, controller: ControllerRef) -> ObservationReceipt:
        if self._controllers.get(controller.workstream) != controller:
            return ObservationReceipt(
                controller=controller,
                state="unknown",
                recovery_required=True,
                reason="controller identity is stale or unknown",
            )
        return ObservationReceipt(controller=controller, state="observed")

    def deliver(
        self,
        controller: ControllerRef,
        brief: AttentionBrief,
    ) -> DeliveryReceipt:
        if brief.workstream != controller.workstream:
            return DeliveryReceipt(
                controller=controller,
                delivered=False,
                recovery_required=True,
                reason="brief workstream does not match controller workstream",
            )
        if self._controllers.get(controller.workstream) != controller:
            return DeliveryReceipt(
                controller=controller,
                delivered=False,
                recovery_required=True,
                reason="controller identity is stale or unknown",
            )
        self.delivery_side_effects += 1
        return DeliveryReceipt(controller=controller, delivered=True)

    def release_session(self, controller: ControllerRef) -> SessionReleaseReceipt:
        if self._controllers.get(controller.workstream) != controller:
            return SessionReleaseReceipt(
                controller=controller,
                released=False,
                recovery_required=True,
                reason="session identity is stale or unknown",
            )
        del self._controllers[controller.workstream]
        return SessionReleaseReceipt(controller=controller, released=True)


__all__ = [
    "ActivationReceipt",
    "ActivationReceiptJournal",
    "AttentionBrief",
    "ControllerRef",
    "ControllerSessionAdapter",
    "CoordinationDelta",
    "DeliveryReceipt",
    "InMemoryActivationReceiptJournal",
    "InMemoryControllerSessionAdapter",
    "ObservationReceipt",
    "ResolveReceipt",
    "ResumeReceipt",
    "SessionReleaseReceipt",
]
